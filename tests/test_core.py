import hashlib
import json
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
import numpy as np
import pytest
from PIL import Image
from language_edge.core import Run,parse_prompts,nearest,fit_reference,project,mesh,atomic_json
from language_edge.models import new_config
from language_edge.server import handler_class,Jobs

def test_dedup_and_seed_grouping():
    rows=parse_prompts('prompt\n"A cat"\n" a   CAT "\nA dog\nA tree\nA car\nA bird\n')
    assert len(rows)==5
    assert {r['role'] for r in rows}>={'reference','calibration'}

def test_nearest_self_exclusion_and_batching():
    x=np.eye(70,dtype=np.float32)
    d,i=nearest(x,x,1,list(range(70)))
    assert np.allclose(d,1)
    assert np.all(i[:,0]!=np.arange(70))

def test_frozen_projection_and_original_space_novelty():
    rng=np.random.default_rng(8)
    x=rng.normal(size=(12,20)); c=rng.normal(size=(4,20))
    b,_=fit_reference(x,c)
    old=project(x,b).copy()
    project(rng.normal(size=(3,20)),b)
    assert np.array_equal(old,project(x,b))
    assert np.isfinite(b['threshold'])

def populated(tmp_path):
    r=Run.create(tmp_path/'test',new_config('sdxl-turbo'))
    rng=np.random.default_rng(1)
    for i in range(10):
        r.add(Image.new('RGB',(8,8)),rng.normal(size=20),{'id':str(i),'group':str(i),
            'role':'reference' if i<6 else 'calibration' if i<8 else 'evaluation','prompt':str(i),'seed':42})
    return r

def test_resume_freeze_and_query_cannot_move_map(tmp_path):
    r=populated(tmp_path);r.freeze()
    before=(r.path/'reference.npz').read_bytes()
    old={p['id']:p['position'] for p in r.export()['points']}
    assert not r.add(Image.new('RGB',(8,8)),np.ones(20),{'id':'0'})
    r.add(Image.new('RGB',(8,8)),np.ones(20),{'id':'query','role':'query','group':'new','prompt':'new','seed':1})
    after=r.export()
    assert before==(r.path/'reference.npz').read_bytes()
    for p in after['points']:
        if p['id'] in old: assert np.allclose(p['position'],old[p['id']],atol=1e-6)
        if p['role']=='reference':assert p['id'] not in [n['id'] for n in p['neighbors']]
    with pytest.raises(ValueError,match='already frozen'):r.freeze()
    r.config['representation']['size']=256
    with pytest.raises(ValueError,match='Configuration changed'):r.export()

def test_reject_split_leakage(tmp_path):
    r=populated(tmp_path)
    marker=r.path/'records'/'6.json'; row=json.loads(marker.read_text());row['group']='0';atomic_json(marker,row)
    with pytest.raises(ValueError,match='leak'):r.freeze()

def test_degenerate_mesh_and_bad_vectors():
    assert mesh(np.zeros((5,3)))['faces']==[]
    with pytest.raises(ValueError):nearest(np.zeros((1,5)),np.ones((4,5)))

def test_server_local_security(tmp_path):
    server=ThreadingHTTPServer(('127.0.0.1',0),handler_class(tmp_path,Jobs()))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        state=json.load(urllib.request.urlopen(base+'/api/state'))
        data=json.dumps({'name':'hello','model':'sd15'}).encode()
        req=urllib.request.Request(base+'/api/create',data=data,headers={'Content-Type':'application/json'})
        with pytest.raises(urllib.error.HTTPError) as err:urllib.request.urlopen(req)
        assert err.value.code==403
        req.add_header('X-LE-Token',state['token']);req.add_header('Origin',base)
        assert json.load(urllib.request.urlopen(req))['ok']
        req.add_header('Origin','https://example.com')
        with pytest.raises(urllib.error.HTTPError):urllib.request.urlopen(req)
        with pytest.raises(urllib.error.HTTPError):urllib.request.urlopen(base+'/image/../config.json')
    finally:server.shutdown();server.server_close()
