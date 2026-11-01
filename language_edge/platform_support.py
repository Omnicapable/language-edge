"""Standard-library-only preflight, usable before installing model dependencies."""
from __future__ import annotations
import argparse
import importlib.util
import json
import platform
import subprocess
import sys

MIN_MAC_GENERATION=(14,0)  # Published macosx_14_0_arm64 wheel for pinned torch 2.15.

def _sysctl(name):
    try:
        result=subprocess.run(['/usr/sbin/sysctl','-n',name],capture_output=True,text=True,timeout=3,check=False)
        return result.stdout.strip() if result.returncode==0 else None
    except (OSError,subprocess.TimeoutExpired):
        return None

def machine_profile():
    system=platform.system()
    arch=platform.machine().lower()
    is_mac=system=='Darwin'
    memory=_sysctl('hw.memsize') if is_mac else None
    return {'system':system,'process_arch':arch,'python':list(sys.version_info[:3]),
        'macos':platform.mac_ver()[0] if is_mac else '',
        'apple_silicon':is_mac and (arch in ('arm64','aarch64') or _sysctl('hw.optional.arm64')=='1'),
        'rosetta':is_mac and _sysctl('sysctl.proc_translated')=='1',
        'memory_gib':round(int(memory)/2**30,1) if memory and memory.isdigit() else None}

def assess_mac(profile,mode='auto'):
    errors=[];notes=[]
    if mode not in ('auto','full','viewer'):
        raise ValueError('Installation mode must be auto, full or viewer.')
    if profile['system']!='Darwin':errors.append('This launcher is for macOS.')
    if tuple(profile['python'][:2]) not in ((3,11),(3,12)):
        errors.append('Use Python 3.11 or 3.12.')
    parts=[int(p) for p in (profile.get('macos') or '0').split('.')[:2]]
    version=tuple((parts+[0,0])[:2])
    native=profile['process_arch'] in ('arm64','aarch64')
    translated=profile.get('rosetta') or (profile.get('apple_silicon') and not native)
    compatible=bool(profile.get('apple_silicon') and native and not translated and version>=MIN_MAC_GENERATION)
    if translated and mode!='viewer':
        errors.append('Python is running through Rosetta. Run native arm64 Python, or explicitly choose viewer mode.')
    if mode=='full' and not compatible and not translated:
        errors.append('The pinned generation stack requires Apple Silicon, native arm64 Python and macOS 14 or later. Use viewer mode on this Mac.')
    selected='full' if compatible and mode!='viewer' else 'viewer'
    if selected=='viewer':notes.append('Viewer only: explore saved maps. Local generation and image encoding are not installed by this mode.')
    else:
        notes.append('Apple Silicon generation candidate detected; actual MPS runtime still needs checking.')
        if profile.get('memory_gib') is not None and profile['memory_gib']<16:
            notes.append('Limited unified memory: start with one SD 1.5 image and consider the experimental lower-memory mode.')
    return {'profile':profile,'install_mode':selected,'errors':errors,'notes':notes,
        'hardware_verified':False}

def runtime_status():
    report={'profile':machine_profile(),'models_installed':False,'mps_available':False,'cuda_available':False,'notes':[]}
    if not all(importlib.util.find_spec(m) for m in ('torch','diffusers','transformers','accelerate')):
        report['notes'].append('Model packages missing; viewer-only operation is available.')
        return report
    report['models_installed']=True
    try:
        import torch
        report['torch']=torch.__version__
        report['cuda_available']=torch.cuda.is_available()
        report['mps_available']=bool(getattr(torch.backends,'mps',None) and torch.backends.mps.is_available())
        if report['mps_available']:
            torch.ones(1,device='mps').sum().item()
            torch.mps.empty_cache()
        elif report['profile']['system']=='Darwin':
            report['notes'].append('Apple GPU unavailable. CPU can be selected explicitly, but it will be slower.')
    except Exception as exc:
        report['mps_available']=False
        report['runtime_error']=f'{type(exc).__name__}: {exc}'
        report['notes'].append(f'Model runtime check failed: {type(exc).__name__}: {exc}')
    return report

def main():
    parser=argparse.ArgumentParser(description='Mac installation preflight and model-runtime check')
    parser.add_argument('--install-mode',choices=['auto','full','viewer'])
    parser.add_argument('--print-install',action='store_true')
    parser.add_argument('--check-runtime',action='store_true')
    parser.add_argument('--require-models',action='store_true')
    args=parser.parse_args()
    if args.check_runtime:
        result=runtime_status()
        print(json.dumps(result,indent=2))
        return 2 if args.require_models and (not result['models_installed'] or result.get('runtime_error')) else 0
    result=assess_mac(machine_profile(),args.install_mode or 'auto')
    for line in result['notes']:print(line,file=sys.stderr)
    for line in result['errors']:print('Error: '+line,file=sys.stderr)
    if result['errors']:return 2
    print(result['install_mode'] if args.print_install else json.dumps(result,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
