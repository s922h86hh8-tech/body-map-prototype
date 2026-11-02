#!/usr/bin/env python3
"""Controlled L3 v5.0 trial vs v3.5 with unchanged baseline v2.4 CT pose.
Translates v4.7's second/third model slots explicitly; never implies approval.
"""
import argparse,importlib.util,json
from pathlib import Path
import nibabel as nib
import trimesh
base=Path(__file__).with_name('compare-l3-bidirectional-holdout-v4.7.py')
spec=importlib.util.spec_from_file_location('v47',base)
v47=importlib.util.module_from_spec(spec);spec.loader.exec_module(v47)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('mask','v24','v35','v50','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--samples',type=int,default=5000)
    a=p.parse_args()
    models={k:trimesh.load(str(getattr(a,k)),force='mesh',process=False)
            for k in ('v24','v35','v50')}
    # v4.7 function uses historical parameter labels v33 and v35.
    # INPUT positional mapping is explicit: first=v24, second=v35, third=v50.
    raw=v47.compare(models['v24'],models['v35'],models['v50'],
                    nib.load(str(a.mask)),samples=a.samples)
    if 'metrics' not in raw:
        raise ValueError('No accepted pose under research-only axis prior')
    actual={'v24':raw['metrics']['v24'],
            'v35':raw['metrics']['v33'],
            'v50':raw['metrics']['v35']}
    def delta(shape,way):
        return round(actual[shape][way]['p95_mm']-actual['v35'][way]['p95_mm'],3)
    comparison={shape:{k:delta(shape,k) for k in ('ct_to_model','model_to_ct','bidirectional')}
                for shape in ('v24','v50')}
    out={'status':'EXPERIMENTAL_V50_COMPARISON_NO_ANATOMICAL_APPROVAL',
         'original_baseline':'v24',
         'fixed_registration_from':'v24',
         'v35_candidate_posterior_extension_model_units':17.2,
         'v50_candidate_posterior_extension_model_units':15.05,
         'pose':raw['pose'],
         'source_array_axes':raw['header']['voxel_array_axis_codes'],
         'crop':raw['crop'],
         'surface_distances_mm':{shape:{way:values[way] for way in
           ('ct_to_model','model_to_ct','bidirectional')} for shape,values in actual.items()},
         'delta_p95_relative_to_v35_mm':comparison,
         'numeric_classes_not_anatomy_names':True,
         'no_expert_anatomical_pose_or_surface_approval':True,
         'anatomy_approved':False}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'written':str(a.out),'anatomy_approved':False}))

if __name__=='__main__':main()
