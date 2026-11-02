#!/usr/bin/env python3
"""Inspect the public LumASe L3 label masks, WITHOUT downloading CT images.
Small ranged downloads of 108 individual L3 *_seg.nii.gz entries from Zenodo
record 7181338; aggregate outputs and anonymous selection-index hashes only.
This neither validates original anatomical completeness nor verifies label names.
"""
import argparse,collections,hashlib,io,json,re
import numpy as np
import nibabel as nib
import requests
from remotezip import RemoteZip

ZENODO_RECORD=7181338
ARCHIVE_KEY='L1-L5FineSegMix-663case.zip'
ARCHIVE_MD5='baf6374a927e9591dbae3314570bdb1e'

def audit_one(data,index):
    img=nib.load(io.BytesIO(data)) if False else None
    import tempfile,pathlib
    with tempfile.TemporaryDirectory() as td:
        p=pathlib.Path(td)/'L3_seg.nii.gz'
        p.write_bytes(data)
        img=nib.load(str(p))
        a=np.asarray(img.dataobj)
        if not np.all(np.isfinite(a)):raise ValueError('non-finite mask')
        if not np.array_equal(a,np.round(a)):raise ValueError('non-integer mask')
        a=a.astype(np.uint8)
    m=a>0
    if m.sum()<500:raise ValueError('near-empty label')
    labels,counts=np.unique(a,return_counts=True)
    occupied=np.where(m)
    faces={ 'x0':int(m[0,:,:].sum()),'x1':int(m[-1,:,:].sum()),
            'y0':int(m[:,0,:].sum()),'y1':int(m[:,-1,:].sum()),
            'z0':int(m[:,:,0].sum()),'z1':int(m[:,:,-1].sum()) }
    border=sum(faces.values())
    distinct=[int(x) for x in labels if x!=0]
    spacing=np.linalg.norm(img.affine[:3,:3],axis=0)
    return {'index':index,'sha256':hashlib.sha256(data).hexdigest(),
      'bytes':len(data),'shape':list(a.shape),
      'nonzero_labels':distinct,
      'class_counts':{str(int(k)):int(v) for k,v in zip(labels,counts) if k>0},
      'voxel_spacing_mm':spacing.round(4).tolist(),
      'total_occupied_voxels':int(m.sum()),
      'border_voxels_six_faces':faces,
      'border_face_count':sum(v>0 for v in faces.values()),
      'border_voxel_fraction':round(border/int(m.sum()),6),
      'zero_border_voxels':border==0,
      'low_boundary_contact_fraction':border/max(1,int(m.sum()))<.005,
      'complete_anatomical_geometry_verified':False}

def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('--limit',type=int,default=108)
    args.add_argument('--selection',type=int,default=12)
    a=args.parse_args()
    resp=requests.get(f'https://zenodo.org/api/records/{ZENODO_RECORD}',timeout=35)
    resp.raise_for_status()
    record=resp.json()
    archive=next(x for x in record['files'] if x['key']==ARCHIVE_KEY)
    if archive['checksum']!=f'md5:{ARCHIVE_MD5}':raise ValueError('Archive checksum metadata changed')
    archive_url=archive['links'].get('self') or archive['links'].get('content')
    with RemoteZip(archive_url) as z:
        files=sorted((x for x in z.infolist()
          if re.search(r'_L3_seg[.]nii[.]gz$',x.filename,re.I)
          and not x.filename.startswith('__MACOSX/')),
          key=lambda i:(i.file_size,i.filename))
        if len(files)!=108:raise ValueError(f'Unexpected L3 mask count: {len(files)}')
        records=[]
        for j,f in enumerate(files[:a.limit]):
            if f.file_size>40_000_000:raise ValueError('L3 mask file unusually large')
            data=z.read(f)
            records.append(audit_one(data,j))
    label_sets=collections.Counter(tuple(x['nonzero_labels']) for x in records)
    face_counts=collections.Counter(x['border_face_count'] for x in records)
    no_touch=[r for r in records if r['zero_border_voxels']]
    low_touch=sorted(records,key=lambda r:(r['border_voxel_fraction'],r['border_face_count']))
    chosen=low_touch[:a.selection]
    output={'source':'LumASe 2022 / Zenodo 7181338',
      'archive_checksum_md5':ARCHIVE_MD5,
      'audited_l3_masks':len(records),
      'all_l3_files_in_archive':len(files),
      'numeric_label_sets':{','.join(map(str,k)):v for k,v in label_sets.items()},
      'number_without_crop_boundary_contact':len(no_touch),
      'number_with_less_than_0_5pct_boundary_contact':sum(r['low_boundary_contact_fraction'] for r in records),
      'crop_face_touch_histogram':{str(k):v for k,v in sorted(face_counts.items())},
      'ordered_low-contact_candidates':[{'index':r['index'],'sha256':r['sha256'],
         'boundary_fraction':r['border_voxel_fraction'],
         'border_face_count':r['border_face_count'],
         'spacing_mm':r['voxel_spacing_mm'],
         'classes':r['nonzero_labels']} for r in chosen],
      'warning':'Zero crop-border voxels does NOT imply anatomically complete L3; no subregion name-map verified.',
      'no_ct_image_downloaded':True,
      'no_original_label_mask_saved':True,
      'anatomy_approved':False}
    print('L3_CROP_CENSUS '+json.dumps(output,ensure_ascii=False))

if __name__=='__main__':
    main()
