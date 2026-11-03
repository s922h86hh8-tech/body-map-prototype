#!/usr/bin/env python3
"""LumASe L3 108-mask original 3D crop census, numeric classes only.

Reads public, checksum-known ZIP member masks by byte range, in a temporary
working directory, without obtaining original grayscale CT image. Candidate
indices/SHAs are anonymous but source-derived. No L3 anatomy/level or numeric
class mapping is independently expert-verified. Does not upload source masks.
"""
import argparse,collections,hashlib,json,re,tempfile
from pathlib import Path
import numpy as np
import nibabel as nib
import requests
from remotezip import RemoteZip

SOURCE='https://zenodo.org/api/records/7181338'
ZIP_KEY='L1-L5FineSegMix-663case.zip'
ZIP_MD5='baf6374a927e9591dbae3314570bdb1e'
def source_archive():
    request=requests.get(SOURCE,timeout=35)
    request.raise_for_status()
    record=request.json()
    entry=next(x for x in record['files'] if x['key']==ZIP_KEY)
    if entry.get('checksum')!='md5:'+ZIP_MD5:raise ValueError('Source archive metadata checksum changed')
    return entry['links'].get('self') or entry['links'].get('content')
def get_rec(member,index,zipfile):
    if member.file_size>40000000:raise ValueError('Unexpectedly large L3 label volume')
    contents=zipfile.read(member)
    with tempfile.TemporaryDirectory() as directory:
        p=Path(directory)/'source_mask.nii.gz'
        p.write_bytes(contents)
        img=nib.load(str(p))
        arr=np.asarray(img.dataobj)
        if arr.ndim!=3 or not np.isfinite(arr).all() or not np.array_equal(arr,np.rint(arr)):
            raise ValueError('Invalid L3 numeric volume')
        arr=arr.astype(np.uint8)
        if not np.array_equal(np.unique(arr),np.arange(8)):raise ValueError('Unexpected numeric labels; do not guess')
        touches={}
        counts={}
        for k in range(1,8):
            m=arr==k
            touches[k]=bool(m[0,:,:].any() or m[-1,:,:].any() or m[:,0,:].any() or
                            m[:,-1,:].any() or m[:,:,0].any() or m[:,:,-1].any())
            counts[k]=int(m.sum())
    return {'index':index,'SHA256':hashlib.sha256(contents).hexdigest(),
            'voxel_shape':list(arr.shape),'array_axes':list(nib.aff2axcodes(img.affine)),
            'crop_by_numeric_id':{str(i):touches[i] for i in range(1,8)},
            'class_voxels':{str(i):counts[i] for i in range(1,8)},
            'all_numeric_classes_without_original_crop_contact':not any(touches.values()),
            'numeric_label_to_anatomy_mapping_known':False,
            'shape_anatomically_complete_proven':False}
def run(start,limit):
    with RemoteZip(source_archive()) as z:
        entries=sorted([x for x in z.infolist() if re.search(r'_L3_seg[.]nii[.]gz$',x.filename,re.I)
           and not x.filename.startswith('__MACOSX/')],
           key=lambda f:(f.file_size,f.filename))
        if len(entries)!=108:raise ValueError('108 original L3-named masks expected')
        if start<0 or start+limit>108:raise ValueError('Invalid index range')
        records=[get_rec(entries[i],i,z) for i in range(start,start+limit)]
    counts={str(k):sum(not r['crop_by_numeric_id'][str(k)] for r in records) for k in range(1,8)}
    candidates=[{'index':r['index'],'mask_SHA256':r['SHA256'],
       'original_image_shape':r['voxel_shape'],
       'numeric_class_7_not_on_crop_faces':True,
       'other_classes_touched':[int(k) for k,v in r['crop_by_numeric_id'].items() if v]}
       for r in records if not r['crop_by_numeric_id']['7']]
    return {'status':'SOURCE_ONLY_L3_NUMERIC_CROP_AUDIT',
            'source_Zenodo_record':7181338,
            'selection_index_type':'ascending uncompressed ZIP member size, then filename',
            'range':[start,start+limit-1],
            'inspected':len(records),
            'number_free_of_original_crop_by_numeric_class':counts,
            'all_7_classes_crop_free':sum(r['all_numeric_classes_without_original_crop_contact'] for r in records),
            'numeric_class_7_crop_free_candidates':candidates,
            'source_label_name_mapping_verified':False,
            'complete_anatomy_of_candidates_verified':False,
            'anatomy_approved':False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start',type=int,required=True)
    p.add_argument('--limit',type=int,default=27)
    a=p.parse_args()
    print('L3_V64_SOURCE108_CENSUS '+json.dumps(run(a.start,a.limit),ensure_ascii=False))
if __name__=='__main__':main()
