"""Run after a demo reference is built. Writes measured results, never claims semantic validation."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
from PIL import Image,ImageChops,ImageEnhance
from language_edge.core import Run,nearest,unit_vectors,atomic_json
from language_edge.models import establish_encoder,encode_image

def main():
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);a=p.parse_args()
    run=Run(a.run);records=run.records();vectors=run.vectors(records)
    vae,dev=establish_encoder(run);size=run.config['representation']['size']
    chosen=records[:min(6,len(records))]
    metrics=[]
    def distance(a,b):return float(np.clip(1-unit_vectors(a[None])@unit_vectors(b[None]).T,0,2)[0,0])
    start=time.perf_counter()
    for r in chosen:
        with Image.open(run.path/r['image']) as image:
            original=encode_image(image,vae,dev,size)
            repeated=encode_image(image,vae,dev,size)
            shifted=encode_image(ImageChops.offset(image,8,0),vae,dev,size)
            brighter=encode_image(ImageEnhance.Brightness(image).enhance(1.1),vae,dev,size)
        metrics.append({'id':r['id'],'repeat_max_absolute_error':float(np.max(np.abs(original-repeated))),
            'shift_8px_cosine_distance':distance(original,shifted),'brightness_10pct_cosine_distance':distance(original,brighter)})
    payload=run.export();points=payload['points']
    refs=[r for r in records if r['role']=='reference'];rx=run.vectors(refs)
    matrix=unit_vectors(rx)@unit_vectors(rx).T
    baseline=float(np.median(1-matrix[np.triu_indices(len(rx),1)]))
    coords=np.array([p['position'] for p in points]);ref_indices=[i for i,p in enumerate(points) if p['role']=='reference']
    overlap=[]
    for i,p in enumerate(points):
        candidates=[j for j in ref_indices if points[j]['id']!=p['id']]
        closest=sorted(candidates,key=lambda j:np.linalg.norm(coords[i]-coords[j]))[:payload['k']]
        original={n['id'] for n in p['neighbors']}
        overlap.append(len(original&{points[j]['id'] for j in closest})/len(original))
    size_sweep=[]
    held=[r for r in records if r['role']=='evaluation']
    if held:
        for n in sorted(set([max(4,len(rx)//3),max(4,2*len(rx)//3),len(rx)])):
            d,_=nearest(run.vectors(held),rx[:n],min(5,n))
            size_sweep.append({'reference_count':n,'evaluation_mean_novelty':float(d.mean())})
    result={'run':run.path.name,'model':run.config['model'],'device':dev,'image_count':len(records),
        'representation':run.config['representation'],'vae_sha256':run.config['vae_sha256'],
        'repeatability_and_perturbations':metrics,'median_between_reference_distance':baseline,
        'mean_full_space_to_3d_neighbor_recall':float(np.mean(overlap)),
        'retained_reference_variance':float(sum(payload['variance'])),
        'reference_size_sweep':size_sweep,'encoding_checks_seconds':time.perf_counter()-start,
        'conclusion':'Engineering pilot only. VAE cosine distance is spatially sensitive and not a validated semantic or language-reach metric.',
        'not_verified':['Mac hardware','10000 prompt performance','large held-out calibration','semantic validity']}
    atomic_json(a.out,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
