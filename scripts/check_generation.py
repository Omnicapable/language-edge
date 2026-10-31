"""Real GPU integration: stop/resume, query placement, import, frozen reference."""
import argparse
import hashlib
import time
from pathlib import Path
from language_edge.core import Run,parse_prompts,atomic_json
from language_edge.models import generate,import_images

def main():
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);a=p.parse_args()
    run=Run(a.run);reference=(run.path/'reference.npz').read_bytes()
    prompts=parse_prompts('prompt\nA luminous garden of glass flowers at night\nA red ceramic bowl on a plain white table\nA white horse standing in a green meadow\nA tiny city carved inside a seashell\n')
    # Cancel after the first generation completes, then resume the exact same inputs.
    stop=[False]
    def progress(message):
        print(message,flush=True)
        if message.startswith('Generating 1/'):
            stop[0]=True
    start=time.perf_counter()
    generate(run,prompts,[43],True,progress,lambda:stop[0])
    staged=len(list((run.path/'staging').glob('*.json')))
    generate(run,prompts,[43],True)
    count=len(run.records())
    generate(run,prompts,[43],True)
    assert len(run.records())==count,'Resume duplicated records'
    candidate=run.records()[0]
    import_images(run,[run.path/candidate['image']])
    assert reference==(run.path/'reference.npz').read_bytes(),'Query or import changed frozen reference'
    payload=run.export()
    matched=[]
    records=run.records()
    import numpy as np
    from language_edge.core import unit_vectors
    for q in records:
        if q.get('seed')==43:
            same=[r for r in records if r.get('seed')==42 and r['prompt']==q['prompt']]
            if same:
                x=unit_vectors(run.vectors([q,same[0]]))
                matched.append({'prompt':q['prompt'],'seed42_to_seed43_cosine_distance':float(1-x[0]@x[1])})
    atomic_json(a.out,{'run':run.path.name,'query_seed':43,'reference_sha256':hashlib.sha256(reference).hexdigest(),
        'frozen_reference_unchanged':True,'resume_without_duplicate_records':True,
        'staged_records_after_stop':staged,'new_generation_and_import_seconds':time.perf_counter()-start,
        'total_images':len(payload['points']),'matched_seed_pairs':matched})

if __name__=='__main__':main()
