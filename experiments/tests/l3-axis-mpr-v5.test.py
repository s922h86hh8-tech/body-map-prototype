#!/usr/bin/env python3
"""Technical regression for the provisional L3 pedicle-axis MPR tool.
Synthetic anatomy is NOT a vertebra and tests do not approve real anatomy.
"""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import numpy as np
import nibabel as nib
from PIL import Image
import base64,io

SRC=Path(__file__).resolve().parents[1]/'tools'/'build-l3-axis-orthogonal-mpr-v5.py'
spec=importlib.util.spec_from_file_location('mpr',SRC)
mpr=importlib.util.module_from_spec(spec);spec.loader.exec_module(mpr)

def save_landmarks(ct_path,seg_path,path,affine,body,posterior,side):
    rows=[]
    for kind,voxel in zip(mpr.PAIR_KINDS[side],[body,posterior]):
        rows.append({'kind':kind,'voxel_ijk':list(voxel),'world_ras_mm':
           nib.affines.apply_affine(affine,np.asarray(voxel)).tolist(),
           'reviewer_confirmation':'unverified_candidate',
           'authority':'unreviewed_manual_click'})
    value={'schema':'L3_LOCAL_LANDMARK_REVIEW_V1',
      'ready_for_anatomical_approval':False,
      'source_CT_sha256':hashlib.sha256(ct_path.read_bytes()).hexdigest(),
      'source_mask_sha256':hashlib.sha256(seg_path.read_bytes()).hexdigest(),
      'synthetic_technical_demo_not_anatomy':True,'items':rows}
    path.write_text(json.dumps(value),encoding='utf8')

def case(tmp,affine,side):
    shape=(80,82,60)
    axis=np.indices(shape)
    seg=np.zeros(shape,dtype=np.uint8)
    radius=np.sqrt((axis[0]-39)**2+(axis[1]-42)**2+(axis[2]-28)**2)
    seg[(radius<21)&(radius>2)]=np.minimum(7,1+(axis[0][(radius<21)&(radius>2)]//12)).astype(np.uint8)
    ct=(axis[0]*5+axis[1]*2+axis[2]*4+700* (seg>0)).astype(np.float32)
    cp=tmp/'ct.nii.gz';mp=tmp/'mask.nii.gz';lp=tmp/'review.json';out=tmp/'mpr.json'
    nib.save(nib.Nifti1Image(ct,affine),str(cp))
    nib.save(nib.Nifti1Image(seg,affine),str(mp))
    first=(35,34,27);second=(35,57,30)
    save_landmarks(cp,mp,lp,affine,first,second,side)
    result=mpr.generate(cp,mp,lp,side,out,fraction=.5,pixels=101,spacing_mm=.35)
    d=json.loads(out.read_text())
    assert d['medical_anatomy_approved'] is False
    assert d['plane_is_pedicle_isthmus_verified'] is False
    assert d['input_demo_points'] is True
    assert d['not_a_pedicle_width_or_height_measurement'] is True
    assert d['source_intensity_units']=='not independently confirmed as HU'
    assert d['CT_mask_were_in_exact_same_grid'] is True
    n=np.asarray(d['plane_normal_world_ras'])
    u=np.asarray(d['plane_horizontal_world_ras'])
    v=np.asarray(d['plane_vertical_world_ras'])
    assert abs(np.dot(n,u))<1e-7 and abs(np.dot(n,v))<1e-7 and abs(np.dot(u,v))<1e-7
    assert abs(np.linalg.norm(n)-1)<1e-6 and abs(np.linalg.norm(u)-1)<1e-6
    expected=(nib.affines.apply_affine(affine,first)+nib.affines.apply_affine(affine,second))/2
    assert np.allclose(d['plane_center_world_ras_mm'],expected,atol=.00001)
    for k in ('image_ct_base64_png','image_overlay_base64_png'):
        p=Image.open(io.BytesIO(base64.b64decode(d[k])))
        assert p.size==(101,101) and p.mode=='RGB'
    assert result['plane_orthogonality_max_error']<1e-6
    assert result['inside_fraction']>0.95
    # Source tampering and invalid landmarks must be detected.
    bad=json.loads(lp.read_text());bad['source_CT_sha256']='0'*64
    wrong=tmp/'wrong.json';wrong.write_text(json.dumps(bad))
    try:mpr.generate(cp,mp,wrong,side,out)
    except ValueError as e:assert 'CT does not match' in str(e)
    else:raise AssertionError('Mismatch source SHA not detected')
    deg=json.loads(lp.read_text());deg['items'][1]['world_ras_mm']=deg['items'][0]['world_ras_mm']
    deg['items'][1]['voxel_ijk']=deg['items'][0]['voxel_ijk']
    degen=tmp/'deg.json';degen.write_text(json.dumps(deg))
    try:mpr.generate(cp,mp,degen,side,out)
    except ValueError as e:assert 'degenerate' in str(e)
    else:raise AssertionError('degenerate axis not rejected')
    return {'source_axes':nib.aff2axcodes(affine),'side':side,'pass':True,
            'points':101,'technical_only':True}
def main():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        a=case(root,np.diag([.6,.7,1.,1.]),'right')
        b=case(root,np.array([[-.6,0,0,90],[0,-.7,0,95],[0,0,1,2],[0,0,0,1.]],float),'left')
    print('L3_MPR_SYNTHETIC_TECHNICAL_PASS '+json.dumps({'tested':[a,b],'source_hash_guard':True,'anatomy_approved':False}))
if __name__=='__main__':main()
