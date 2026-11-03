#!/usr/bin/env python3
"""Diagnostic: distinguish limited MPR field-of-view from absent label/crop.
Uses SOURCE-NUMERIC CLASS (no anatomical label map) and deliberately fictional
class-centered axis; no CT image or full report is published. Generated reports
are written locally only; cleanup is the caller's responsibility.
"""
import argparse,collections,importlib.util,json,tempfile
from pathlib import Path
HERE=Path(__file__).parent
src=HERE/'l3-pedicle-axis-sweep-v6.py'
spec=importlib.util.spec_from_file_location('numerical_sweep_v6',src)
v6=importlib.util.module_from_spec(spec);spec.loader.exec_module(v6)

def test(ct,mask,axis_dir,out_dir,classes=(2,7)):
    scans=[]
    for numeric_id in classes:
        axis=axis_dir/f'demo-numeric-{numeric_id}.json'
        if not axis.exists():raise ValueError('Missing source centered non-anatomic axis '+str(numeric_id))
        # Grow from 35.35mm to 70.35mm then 100.5mm.
        for n,spacing in [(101,.35),(201,.35),(201,.5)]:
            out=out_dir/f'class-{numeric_id}-grid-{n}-spacing-{str(spacing).replace(".","p")}.json'
            x=v6.sweep(ct,mask,axis,'right',numeric_id,out,step_mm=.5,
                       margin_mm=1.,pixels=n,spacing_mm=spacing)
            report=json.loads(out.read_text(encoding='utf8'))
            rejected=collections.Counter(row['invalid_reason'] or 'accepted'
                                         for row in report['planes'])
            scans.append({
              'numeric_id_not_anatomic_name':numeric_id,
              'plane_width_mm':round(n*spacing,2),
              'pixels':n,'pixel_size_mm':spacing,
              'tested_planes':report['n_planes'],
              'accepted_numeric_proxy_planes':report['n_valid_numeric_roi_planes'],
              'reasons':dict(rejected),
              'pedicle_axis_independently_verified':False,
              'source_numeric_id_named_from_primary_document':False})
    return {'status':'FOV_CAUSE_DIAGNOSTIC',
       'results':scans,'all_axes_are_explicitly_fake_numeric_centroid_demos':True,
       'source_numeric_label_7_anatomic_identity_known':False,
       'not_a_valid_pedicle_width_measurement':True,
       'anatomy_approved':False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ct',type=Path,required=True)
    p.add_argument('--mask',type=Path,required=True)
    p.add_argument('--axis-dir',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    result=test(args.ct,args.mask,args.axis_dir,args.output_dir)
    print('L3_V62_FOV_SENSITIVITY '+json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
