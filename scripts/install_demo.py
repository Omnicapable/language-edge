"""Install the bundled, precomputed demo without downloading model weights."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from language_edge.core import default_data_dir

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',default=str(default_data_dir()));a=p.parse_args()
    archive=Path(__file__).resolve().parents[1]/'examples'/'demo-sdxl.zip'
    root=Path(a.data).expanduser()
    root.mkdir(parents=True,exist_ok=True)
    # Windows packaged apps may redirect AppData only once the directory exists.
    root=root.resolve();target=(root/'demo-sdxl').resolve()
    if not target.is_relative_to(root):
        raise ValueError('Demo must remain inside the data directory')
    if target.exists():
        print('Demo workspace already exists; leaving it unchanged.');return
    if not archive.exists():
        print('Demo archive is not included in this checkout.');return
    manifest=json.loads((archive.parent/'demo-manifest.json').read_text())
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=manifest['sha256']:
        raise ValueError('Demo checksum mismatch. Obtain a fresh trusted release.')
    root.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        if sum(i.file_size for i in z.infolist())>250_000_000 or len(z.infolist())>1000:
            raise ValueError('Demo archive exceeds extraction limits')
        if any(not n.startswith('demo-sdxl/') or not (root/n).resolve().is_relative_to(target) for n in z.namelist()):
            raise ValueError('Unsafe archive path')
        z.extractall(root)
    print('Installed precomputed demo:',target)

if __name__=='__main__':main()
