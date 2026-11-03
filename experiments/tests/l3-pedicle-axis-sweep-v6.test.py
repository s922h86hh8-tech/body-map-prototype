#!/usr/bin/env python3
"""Deterministic NON-ANATOMICAL test for CT cross-section sweep and proxy guards.

Synthetic pipe with a designed numerical constriction. A synthetic pipe is
NOT a pedicle; passing test proves only basic math and source integrity.
"""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import numpy as np,nibabel as nib

SOURCE=Path(__file__).resolve().parents[1]/'tools'/'l3-pedicle-axis-sweep-v6.py'
spec=importlib.util.spec_from_file_location('v6axis',SOURCE)
sw=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sw)
def make(root,affine):
    shape=(74,84,68)
    xx,yy,zz=np.ogrid[:shape[0],:shape[1],:shape[2]]
    # Explicitly artificial tube along voxel Y, narrowing at y=43.
    r=(4.8+0.012*(yy-43)**2).astype(float)
    section=((xx-35)**2+(zz-34)**2<r*r)
    seg=np.where(section,3,0).astype(np.uint8)
    ct=(seg*620+np.broadcast_to((xx*2+yy+zz),shape)).astype(np.float32)
    cp=root/'ct.nii.gz';mp=root/'mask.nii.gz';lp=root/'landmarks.json';op=root/'result.json'
    nib.save(nib.Nifti1Image(ct,affine),str(cp))
    nib.save(nib.Nifti1Image(seg,affine),str(mp))
    v1=[35,16,34];v2=[35,69,34]
    kinds=sw.base.PAIR_KINDS['right']
    items=[{'kind':kind,'voxel_ijk':ijk,
            'world_ras_mm':nib.affines.apply_affine(affine,ijk).tolist(),
            'reviewer_confirmation':'unverified_candidate',
            'authority':'unreviewed_manual_click'}
           for kind,ijk in zip(kinds,[v1,v2])]
    report={'schema':'L3_LOCAL_LANDMARK_REVIEW_V1',
            'ready_for_anatomical_approval':False,
            'source_CT_sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),
            'source_mask_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),
            'synthetic_technical_demo_not_anatomy':True,
            'items':items}
    lp.write_text(json.dumps(report),encoding='utf8')
    return cp,mp,lp,op
def check(root,affine,expected_axis):
    cp,mp,lp,out=make(root,affine)
    result=sw.sweep(cp,mp,lp,'right',3,out,step_mm=.5,margin_mm=1,
                    pixels=101,spacing_mm=.35)
    report=json.loads(out.read_text())
    assert result['planes']>=50
    assert report['schema']=='L3_PEDICLE_AXIS_MULTI_MPR_V6_RESEARCH_ONLY'
    assert report['source_CT_sha256']==hashlib.sha256(cp.read_bytes()).hexdigest()
    assert report['input_uses_fictitious_demo_points'] is True
    assert report['anatomic_label_mapping_confirmed'] is False
    assert report['minimum_proxy_is_anatomical_pedicle_isthmus'] is False
    assert report['expert_anatomy_approved'] is False
    assert report['n_valid_numeric_roi_planes']>15
    assert report['sampling_step_mm']==.5
    assert len(report['previews'])>=3
    normal=np.asarray(report['normal_RAS'])
    assert np.allclose(normal,expected_axis,atol=1e-7)
    # The central constriction is purposely not reported as an anatomy location:
    # it can only produce a synthetic numerical best-proxy candidate.
    candidate=report['minimum_proxy_plane_index_if_any']
    assert candidate is not None
    best=report['planes'][candidate]['center_world_ras_mm']
    expected=nib.affines.apply_affine(affine,[35,43,34])
    assert abs(best[1]-expected[1])<=6,(best,expected)
    # Missing numeric label must not be conflated with valid numeric ROI.
    absent=sw.sweep(cp,mp,lp,'right',7,root/'absent.json',step_mm=1.,
                    margin_mm=1.,pixels=101,spacing_mm=.35)
    assert absent['valid_numeric_ROI_planes']==0
    assert absent['smallest_numeric_ellipse_proxy_plane_index'] is None
    # No source identity substitution can be accepted.
    bad=json.loads(lp.read_text());bad['source_mask_sha256']='f'*64
    wrong=root/'bad.json';wrong.write_text(json.dumps(bad))
    try:sw.sweep(cp,mp,wrong,'right',3,root/'unsafe.json')
    except ValueError as exc:assert 'Source segmentation' in str(exc)
    else:raise AssertionError('mismatched SHA unexpectedly accepted')
    return {'axes':nib.aff2axcodes(affine),'valid_numeric_proxy_planes':report['n_valid_numeric_roi_planes'],
            'synthetic_constriction_world_y_mm':round(float(expected[1]),3),
            'numeric_candidate_world_y_mm':round(float(best[1]),3),
            'anatomy_approved':False}
def main():
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory);axis_a=np.diag([1.,1.,1.,1.])
        a=check(root,axis_a,[0,1,0])
        axis_b=np.array([[-.9,0,0,70],[0,-.8,0,65],[0,0,1.25,0],[0,0,0,1]],float)
        b=check(root,axis_b,[0,-1,0])
    print('L3_V6_SYNTHETIC_SWEEP_PASS '+json.dumps({
        'synthetic_tube_not_lumbar_anatomy':True,
        'test_cases':[a,b],
        'source_integrity_rejection':True,
        'unmapped_label_rejection':True,
        'anatomy_approved':False},ensure_ascii=False))
if __name__=='__main__':main()
