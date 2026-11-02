"""Package approved source and the audited public demo; never read live user runs."""
from pathlib import Path
import hashlib
import json
import zipfile
from language_edge import __version__

ROOT=Path(__file__).resolve().parents[1]
ROOT_FILES={'.gitattributes','.gitignore','pyproject.toml','README.md','QUICKSTART.md',
    'LICENSE','THIRD_PARTY_NOTICES.md','SECURITY.md','PRIVACY.md','CHANGELOG.md',
    'constraints-tested.txt','Setup Windows.cmd','Start Windows.cmd','Setup Mac.command','Start Mac.command'}
SOURCE_DIRS={'language_edge','docs','scripts','tests','.github'}
TEXT_SUFFIXES={'.py','.md','.json','.csv','.cjs','.html','.css','.yml','.toml','.txt'}
PUBLIC_REPORTS={'AUDIT.md','REPRESENTATION_REVIEW.md','SECURITY_REVIEW.md','sd15-integration.json',
    'sd15-pilot.json','sdxl-integration.json','sdxl-pilot.json','verification-summary.json',
    'dependency-audit-direct.json','dependency-audit-runtime.json','release-privacy-scan.json','current-stack-smoke.json','MAC_COMPATIBILITY.md','mac-compatibility-checks.json'}
EXAMPLES={'demo-sdxl.zip','demo-manifest.json','sd15-smoke.csv'}

def sensitive_path(path):
    return any(p.startswith('.env') or p.lower().startswith(('credentials','secrets'))
        or p.lower() in {'.aws','.ssh','.git','__pycache__','.pytest_cache'}
        for p in path.parts) or path.suffix.lower() in {'.pem','.key','.p12','.pfx'}

def release_files(root=ROOT):
    candidates=[root/name for name in ROOT_FILES]
    for directory in SOURCE_DIRS:
        folder=root/directory
        if folder.is_dir() and not folder.is_symlink():
            candidates.extend(folder.rglob('*'))
    candidates.extend(root/'reports'/name for name in PUBLIC_REPORTS)
    candidates.extend(root/'examples'/name for name in EXAMPLES)
    for file in sorted(set(candidates)):
        relative=file.relative_to(root)
        if not file.is_file() or file.is_symlink() or sensitive_path(relative):continue
        if not file.resolve().is_relative_to(root.resolve()):continue
        if len(relative.parts)==1:
            approved=file.name in ROOT_FILES
        elif relative.parts[0] in SOURCE_DIRS:
            approved=file.suffix in TEXT_SUFFIXES or relative.as_posix()=='docs/images/language-edge-cover.png'
        elif relative.parts[0]=='reports':
            approved=len(relative.parts)==2 and file.name in PUBLIC_REPORTS
        elif relative.parts[0]=='examples':
            approved=len(relative.parts)==2 and file.name in EXAMPLES
        else:approved=False
        if approved:yield file,relative

def main():
    demo=ROOT/'examples'/'demo-sdxl.zip'
    manifest=json.loads((ROOT/'examples'/'demo-manifest.json').read_text())
    if hashlib.sha256(demo.read_bytes()).hexdigest()!=manifest['sha256']:
        raise ValueError('Public demo changed. Review its content and update the approved manifest explicitly.')
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    target=dist/f'language-edge-{__version__}-source.zip'
    temporary=dist/f'language-edge-{__version__}-source.zip.tmp'
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as z:
        for file,relative in release_files():
            info=zipfile.ZipInfo('language-edge/'+relative.as_posix(),(2026,11,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if file.suffix=='.command' else 0o100644)<<16
            z.writestr(info,file.read_bytes())
    from check_release_privacy import inspect_bytes
    findings=[]
    inspect_bytes(target.name,temporary.read_bytes(),findings)
    if findings:
        temporary.unlink()
        raise ValueError('Release pattern scan found potentially private content; review before packaging.')
    temporary.replace(target)
    print('Release archive',target)
    print('Only approved source and the frozen public demo were included. No live runs were read.')

if __name__=='__main__':main()
