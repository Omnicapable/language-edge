import base64
import importlib.util
import io
import json
import socket
import threading
import urllib.error
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer
import pytest
from PIL import Image,PngImagePlugin
from language_edge.core import Run,clean_image
from language_edge.models import new_config
from language_edge.server import Jobs,handler_class

@pytest.fixture
def local(tmp_path):
    server=ThreadingHTTPServer(('127.0.0.1',0),handler_class(tmp_path,Jobs()))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    state=json.load(opener.open(base+'/api/state'))
    yield base,opener,state['token']
    server.shutdown();server.server_close()

@pytest.mark.parametrize('path',['/api/state','/api/map/test','/image/test/test.png'])
def test_cross_origin_get_denied(local,path):
    base,opener,token=local
    req=urllib.request.Request(base+path,headers={'Origin':'https://attacker.example'})
    with pytest.raises(urllib.error.HTTPError) as e:opener.open(req)
    assert e.value.code==403

def test_host_and_fetch_site_denied(local):
    base,opener,token=local
    for headers in ({'Host':'attacker.example'},{'Sec-Fetch-Site':'cross-site'}):
        with pytest.raises(urllib.error.HTTPError) as e:opener.open(urllib.request.Request(base+'/api/state',headers=headers))
        assert e.value.code==403

def test_privacy_headers(local):
    base,opener,token=local
    response=opener.open(base+'/')
    assert response.headers['Cross-Origin-Resource-Policy']=='same-origin'
    assert response.headers['Referrer-Policy']=='no-referrer'
    assert response.headers['X-Frame-Options']=='DENY'
    assert response.headers['X-Content-Type-Options']=='nosniff'
    assert 'no-store' in response.headers['Cache-Control']

def test_wrong_content_type_and_large_requests(local):
    base,opener,token=local
    for headers in ({'Content-Type':'text/plain'},{'Content-Type':'application/json','Content-Length':'32000001'}):
        req=urllib.request.Request(base+'/api/create',data=b'{}',headers={'X-LE-Token':token,**headers})
        with pytest.raises(urllib.error.HTTPError) as e:opener.open(req)
        assert e.value.code==400

@pytest.mark.parametrize('path',['/../config.json','/%2e%2e/config.json','/image/test/%2e%2e.png','/api/map/../outside'])
def test_traversal_denied(local,path):
    base,opener,token=local
    with pytest.raises(urllib.error.HTTPError) as e:opener.open(base+path)
    assert e.value.code==404

def test_stored_image_strips_metadata(tmp_path):
    original=Image.new('RGB',(12,12),'red')
    info=PngImagePlugin.PngInfo();info.add_text('private-comment','not for distribution')
    exif=Image.Exif();exif[270]='Private location description'
    raw=io.BytesIO();original.save(raw,'PNG',pnginfo=info,exif=exif)
    with Image.open(io.BytesIO(raw.getvalue())) as image:
        cleaned=clean_image(image)
        assert not cleaned.info and not cleaned.getexif()
        run=Run.create(tmp_path/'test',new_config('sd15'))
        run.add(image,[1,2],{'id':'test','role':'query'})
    with Image.open(run.path/'images/test.png') as saved:
        assert not saved.info and not saved.getexif()

def test_image_size_and_format_are_validated():
    image=Image.new('RGB',(1,1));image.format='TIFF'
    with pytest.raises(ValueError,match='real PNG'):clean_image(image)
    class Huge:
        width=10000;height=10000
    with pytest.raises(ValueError,match='40 megapixels'):clean_image(Huge())

def test_release_allowlist_excludes_secrets_and_live_runs(tmp_path):
    script=Path(__file__).resolve().parents[1]/'scripts/package_release.py'
    spec=importlib.util.spec_from_file_location('release',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for path in ['README.md','.env','.env.production','credentials.json','private/photo.json',
        'runs/demo-sdxl/map.json','examples/personal-prompts.csv','scripts/.env.local','scripts/secrets.json',
        'language_edge/core.py','examples/demo-sdxl.zip']:
        file=tmp_path/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_text('test')
    accepted={str(r).replace('\\','/') for _,r in module.release_files(tmp_path)}
    assert accepted=={'README.md','language_edge/core.py','examples/demo-sdxl.zip'}

def test_upload_rejects_renamed_non_image(local,tmp_path):
    base,opener,token=local
    run=Run.create(tmp_path/'test',new_config('sd15'));(run.path/'reference.npz').write_bytes(b'test')
    payload={'name':'test','files':[{'name':'fake.png','data':base64.b64encode(b'<html>not an image</html>').decode()}]}
    req=urllib.request.Request(base+'/api/import',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-LE-Token':token})
    with pytest.raises(urllib.error.HTTPError) as e:opener.open(req)
    assert e.value.code==400
    assert not list((run.path/'uploads').iterdir())

def test_upload_sanitizes_before_worker(local,tmp_path,monkeypatch):
    from language_edge import models
    finished=threading.Event();received=[]
    def fake_import(run,paths,*args):received.extend(paths);finished.set()
    monkeypatch.setattr(models,'import_images',fake_import)
    base,opener,token=local
    run=Run.create(tmp_path/'test',new_config('sd15'));(run.path/'reference.npz').write_bytes(b'test')
    info=PngImagePlugin.PngInfo();info.add_text('private','metadata')
    raw=io.BytesIO();Image.new('RGB',(8,8)).save(raw,'PNG',pnginfo=info)
    payload={'name':'test','files':[{'name':'private-name.png','data':base64.b64encode(raw.getvalue()).decode()}]}
    req=urllib.request.Request(base+'/api/import',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-LE-Token':token})
    assert json.load(opener.open(req))['ok'] and finished.wait(5)
    assert received and 'private-name' not in received[0].name
    with Image.open(received[0]) as im:assert not im.info

def test_data_directory_can_be_explicitly_overridden(tmp_path,monkeypatch):
    from language_edge.core import default_data_dir
    monkeypatch.setenv('LANGUAGE_EDGE_DATA',str(tmp_path/'local-data'))
    assert default_data_dir()==(tmp_path/'local-data').resolve()
