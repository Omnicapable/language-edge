"""Install the bundled, precomputed demo without downloading model weights."""
import argparse
import zipfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',default='runs');a=p.parse_args()
    archive=Path(__file__).resolve().parents[1]/'examples'/'demo-sdxl.zip'
    root=Path(a.data).resolve();target=root/'demo-sdxl'
    if target.exists():
        print('Demo workspace already exists; leaving it unchanged.');return
    if not archive.exists():
        print('Demo archive is not included in this checkout.');return
    root.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        if any(not (root/n).resolve().is_relative_to(root) for n in z.namelist()):
            raise ValueError('Unsafe archive path')
        z.extractall(root)
    print('Installed precomputed demo:',target)

if __name__=='__main__':main()
