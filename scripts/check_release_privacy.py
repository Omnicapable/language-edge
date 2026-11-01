"""Scan tracked files and nested distribution metadata without printing secrets."""
import argparse
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
    'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'github_token':rb'gh[pousr]_[A-Za-z0-9]{30,}',
    'huggingface_token':rb'hf_[A-Za-z0-9]{30,}',
    'openai_token':rb'sk-(?:proj-)?[A-Za-z0-9_-]{35,}',
    'aws_access_key':rb'(?:AKIA|ASIA)[A-Z0-9]{16}',
    'user_directory':rb'[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9_. -]+[\\/]',
}
TEXT_SUFFIXES={'.json','.xml','.py','.md','.txt','.html','.js','.css','.cjs','.yml','.toml','.csv','.cmd','.command'}

def inspect_bytes(name,data,hits,depth=0):
    if depth>3:
        raise ValueError('Unexpected archive nesting')
    if name.endswith(('.zip','.docx','.npz')):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if sum(n.file_size for n in z.infolist())>250_000_000:
                raise ValueError('Archive exceeds scan budget')
            for info in z.infolist():
                inspect_bytes(name+'!'+info.filename,z.read(info),hits,depth+1)
    elif Path(name).suffix.lower() in TEXT_SUFFIXES:
        for kind,pattern in PATTERNS.items():
            count=len(re.findall(pattern,data))
            if count:hits.append({'file':name,'kind':kind,'count':count})

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='reports/release-privacy-scan.json');p.add_argument('--archive');p.add_argument('--history',action='store_true');a=p.parse_args()
    hits=[]
    if a.archive:
        file=Path(a.archive);inspect_bytes(file.name,file.read_bytes(),hits);files=[file.name]
    elif a.history:
        objects=subprocess.check_output(['git','rev-list','--objects','--all'],cwd=ROOT).decode().splitlines()
        ids=[line.split(' ',1)[0] for line in objects]
        details=subprocess.check_output(['git','cat-file','--batch-check'],input=('\n'.join(ids)+'\n').encode(),cwd=ROOT).decode().splitlines()
        names={line.split(' ',1)[0]:line.split(' ',1)[1] for line in objects if ' ' in line}
        files=[]
        for line in details:
            object_id,kind,size=line.split()
            if kind!='blob':continue
            if int(size)>250_000_000:raise ValueError('Historical object exceeds scan budget')
            name=names.get(object_id,object_id);files.append(name)
            data=subprocess.check_output(['git','cat-file','blob',object_id],cwd=ROOT)
            inspect_bytes(name,data,hits)
    else:
        files=[f for f in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0') if f]
        for name in files:inspect_bytes(name,(ROOT/name).read_bytes(),hits)
    result={'scope':'release archive' if a.archive else 'Git history blobs' if a.history else 'tracked working tree','files_checked':len(files),
        'findings':hits,'note':'Pattern scan, not proof of absence of secrets. Personal author names, filenames and intentional demo prompts require human review.'}
    target=ROOT/a.output;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return 1 if hits else 0

if __name__=='__main__':raise SystemExit(main())
