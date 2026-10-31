"""Create a portable demo and source archive, excluding models, private runs and environments."""
from pathlib import Path
import io
import json
import zipfile
import numpy as np
from language_edge.core import digest

ROOT=Path(__file__).resolve().parents[1]

def main():
    run=ROOT/'runs'/'demo-sdxl'
    examples=ROOT/'examples';examples.mkdir(exist_ok=True)
    config=json.loads((run/'config.json').read_text())
    config['source']='stabilityai/sdxl-turbo';config['device']='auto'
    with np.load(run/'reference.npz',allow_pickle=False) as original:
        bundle={k:original[k] for k in original.files}
    bundle['config_digest']=np.array(digest(config))
    stream=io.BytesIO();np.savez_compressed(stream,**bundle)
    with zipfile.ZipFile(examples/'demo-sdxl.zip','w',zipfile.ZIP_DEFLATED) as z:
        prefix='demo-sdxl/'
        z.writestr(prefix+'config.json',json.dumps(config,indent=2))
        z.writestr(prefix+'reference.npz',stream.getvalue())
        z.write(run/'map.json',prefix+'map.json')
        for folder in ('images','records','vectors'):
            for file in sorted((run/folder).iterdir()):
                if file.is_file():z.write(file,prefix+folder+'/'+file.name)
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    excludes={'.venv','.git','runs','models','private','dist','build','__pycache__','.pytest_cache'}
    with zipfile.ZipFile(dist/'language-edge-0.1.0-source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(ROOT.rglob('*')):
            relative=file.relative_to(ROOT)
            if not file.is_file() or any(p in excludes or p.endswith('.egg-info') for p in relative.parts):continue
            if relative.parts[0]=='project_admin':continue
            if file.suffix in ('.log','.pyc'):continue
            z.write(file,'language-edge/'+relative.as_posix())
    print('Demo archive',examples/'demo-sdxl.zip')
    print('Release archive',dist/'language-edge-0.1.0-source.zip')

if __name__=='__main__':main()
