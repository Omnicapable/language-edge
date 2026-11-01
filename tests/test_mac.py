import contextlib
import sys
from types import SimpleNamespace
import numpy as np
import pytest
from PIL import Image
from language_edge import models
from language_edge.core import Run
from language_edge.platform_support import assess_mac

def profile(**changes):
    return {'system':'Darwin','process_arch':'arm64','python':[3,11,15],
        'macos':'14.0','apple_silicon':True,'rosetta':False,'memory_gib':16,**changes}

def test_native_mac_generation_and_low_ram_note():
    r=assess_mac(profile(memory_gib=8))
    assert r['install_mode']=='full' and not r['errors']
    assert any('Limited unified' in note for note in r['notes'])
    assert not r['hardware_verified']

def test_intel_has_viewer_route_without_insecure_downgrade():
    p=profile(process_arch='x86_64',apple_silicon=False)
    assert assess_mac(p)['install_mode']=='viewer'
    assert assess_mac(p,'full')['errors']
    assert not assess_mac(p,'viewer')['errors']

def test_rosetta_stops_full_install_but_allows_explicit_viewer():
    p=profile(process_arch='x86_64',rosetta=True)
    assert assess_mac(p)['errors']
    assert assess_mac(p,'full')['errors']
    assert not assess_mac(p,'viewer')['errors']

def test_old_macos_and_wrong_python_are_explained():
    assert assess_mac(profile(macos='13.6'))['install_mode']=='viewer'
    assert assess_mac(profile(macos='13.6'),'full')['errors']
    assert assess_mac(profile(python=[3,10,15]))['errors']

def test_low_memory_affects_mps_generation_only():
    c=models.new_config('sd15',memory_mode='low-memory')
    assert models.generation_precision(c,'mps')=='float16'
    assert models.generation_precision(c,'cpu')=='float32'
    assert models.generation_precision(models.new_config('sd15'),'mps')=='float32'
    assert c['representation']==models.new_config('sd15')['representation']

def fake_torch(monkeypatch,available=True):
    calls=[]
    class Generator:
        def __init__(self,**kwargs):pass
        def manual_seed(self,seed):return self
    t=SimpleNamespace(float16='fp16',float32='fp32',Generator=Generator,
        inference_mode=contextlib.nullcontext,cuda=SimpleNamespace(is_available=lambda:False),
        backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda:available)),
        mps=SimpleNamespace(synchronize=lambda:calls.append('sync'),empty_cache=lambda:calls.append('empty')))
    monkeypatch.setitem(sys.modules,'torch',t)
    return t,calls

def test_mps_cache_release_and_unavailable_device(monkeypatch):
    _,calls=fake_torch(monkeypatch)
    models.release_device_cache('mps')
    assert calls==['sync','empty']
    fake_torch(monkeypatch,False)
    with pytest.raises(ValueError,match='Apple GPU is unavailable'):models.device_name('mps')
    assert models.device_name('auto')=='cpu'

def test_vae_stays_float32_in_lower_memory_mode(tmp_path,monkeypatch):
    t,calls=fake_torch(monkeypatch)
    captured={}
    class Vae:
        @classmethod
        def from_pretrained(cls,source,**kwargs):captured.update(kwargs);return cls()
        def eval(self):return self
        def to(self,device):captured['device']=device;return self
        def enable_slicing(self):captured['slicing']=True
    monkeypatch.setitem(sys.modules,'diffusers',SimpleNamespace(AutoencoderKL=Vae))
    monkeypatch.setattr(models,'weight_identity',lambda vae:'test-hash')
    c=models.new_config('sd15',device='mps',memory_mode='low-memory')
    models.load_vae(c)
    assert captured['torch_dtype']==t.float32
    assert captured['device']=='mps'

def test_generation_failure_cleans_cache_and_preserves_actionable_error(tmp_path,monkeypatch):
    t,calls=fake_torch(monkeypatch)
    class Broken:
        @classmethod
        def from_pretrained(cls,*args,**kwargs):raise RuntimeError('out of memory')
    monkeypatch.setitem(sys.modules,'diffusers',SimpleNamespace(AutoPipelineForText2Image=Broken))
    run=Run.create(tmp_path/'test',models.new_config('sd15',device='mps'))
    with pytest.raises(ValueError,match='Completed files are saved'):
        models._generate_pending(run,[{}],lambda message:None,lambda:False)
    assert calls==['sync','empty','sync','empty']

def test_lower_memory_generation_records_execution_and_cleans_cache(tmp_path,monkeypatch):
    t,calls=fake_torch(monkeypatch)
    captured={}
    class Pipeline:
        scheduler=SimpleNamespace(config={})
        @classmethod
        def from_pretrained(cls,*args,**kwargs):captured.update(kwargs);return cls()
        def set_progress_bar_config(self,**kwargs):pass
        def to(self,device):captured['device']=device
        def enable_attention_slicing(self):captured['sliced']=True
        def __call__(self,*args,**kwargs):return SimpleNamespace(images=[Image.new('RGB',(8,8))],nsfw_content_detected=None)
    monkeypatch.setitem(sys.modules,'diffusers',SimpleNamespace(AutoPipelineForText2Image=Pipeline))
    run=Run.create(tmp_path/'test',models.new_config('sd15',device='mps',memory_mode='low-memory'))
    (run.path/'staging').mkdir()
    meta={'id':'test','prompt':'A bowl','seed':42,'generation':run.config['generation']}
    models._generate_pending(run,[meta],lambda message:None,lambda:False)
    import json
    saved=json.loads((run.path/'staging/test.json').read_text())
    assert saved['execution']=={'device':'mps','generation_precision':'float16'}
    assert captured['torch_dtype']==t.float16 and captured['variant']=='fp16'
    assert captured['device']=='mps' and captured['sliced']
    assert calls==['sync','empty','sync','empty']

def test_encoding_failure_cleans_cache(tmp_path,monkeypatch):
    fake_torch(monkeypatch)
    run=Run.create(tmp_path/'test',models.new_config('sd15',device='mps'))
    (run.path/'staging').mkdir()
    Image.new('RGB',(8,8)).save(run.path/'staging'/'test.png')
    monkeypatch.setattr(models,'establish_encoder',lambda run:(object(),'mps'))
    def broken(*args):raise RuntimeError('MPS operation unsupported')
    monkeypatch.setattr(models,'encode_image',broken)
    clean=[];monkeypatch.setattr(models,'release_device_cache',clean.append)
    with pytest.raises(ValueError,match='Apple GPU operation failed'):
        models._encode_staged(run,[{'id':'test'}],lambda message:None,lambda:False)
    assert clean==['mps']
