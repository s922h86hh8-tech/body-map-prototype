#!/usr/bin/env python3
"""Read official BodyParts3D v4.0 anatomy index and individual L3 OBJ in temporary memory.
Official source 20130619, license currently CC BY 4.0 (publisher license update 2025-02-27).
Never write third-party mesh to the GitHub repository. Quality is UNVALIDATED.
"""
import csv,io,json,os,hashlib,re
from pathlib import Path
import numpy as np,requests,trimesh
from remotezip import RemoteZip

ROOT='https://dbarchive.biosciencedbc.jp/data/bodyparts3d/20130619/'
idx_url=ROOT+'isa_parts_list_e.txt'
zip_url=ROOT+'isa_BP3D_4.0_obj_99.zip'
r=requests.get(idx_url,timeout=50);r.raise_for_status()
print('INDEX_STATUS',r.status_code,'BYTES',len(r.content),'SHA256',hashlib.sha256(r.content).hexdigest())
lines=r.text.splitlines()
rows=list(csv.reader(lines,delimiter='\t'))
print('COLUMNS',rows[:3])
found=[x for x in rows if any(('third lumbar' in k.lower() or 'l3 vertebra' in k.lower() or 'lumbar vertebra l3' in k.lower()) for k in x)]
print('L3_SOURCE_ROWS',json.dumps(found[:15],ensure_ascii=False))
# Official mapping: the table lists representation BP8227, while ZIP is atomic ELEMENT ID.
# Resolve via isa_element_parts, NOT guessed ID conversion.
ele=requests.get(ROOT+'isa_element_parts.txt',timeout=50);ele.raise_for_status()
el_rows=list(csv.reader(ele.text.splitlines(),delimiter='\t'))
concepts={row[0] for row in found if row and row[0]=='FMA13074'}
ids={row[2] for row in el_rows if len(row)>=3 and row[0] in concepts}
if not ids:
    raise ValueError('No official FMA13074 -> FJ mesh mapping; cannot identify L3')
print('L3_ATOMIC_ELEMENT_IDS',json.dumps(sorted(ids),ensure_ascii=False))
source_reps=ids
with RemoteZip(zip_url) as z:
    all_members=z.infolist()
    matches=[x for x in all_members if any(x.filename.lower().endswith('/'+element_id.lower()+'.obj') for element_id in ids)]
    print('ARCHIVE_INDEX',json.dumps({'file_entries':len(all_members),
      'candidate_entries':[{'name':x.filename,'size_bytes':x.file_size} for x in matches[:30]],
      'matched_official_index':any(any(id+'.obj' in x.filename for id in source_reps) for x in matches),
      'source_version':'BodyParts3D 4.0 99-percent-polygon-reduced OBJ',
      'source_license_page':'https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html',
      'reference_geometry_not_original_CT':True,'anatomy_approved':False}))
    selected=[x for x in matches if any(x.filename.lower().endswith('/'+id.lower()+'.obj') for id in source_reps)]
    if not selected:
       print('MODEL_NOT_IDENTIFIED_OR_ARCHIVE_ENTRY_MISSING; do not invent identifier')
       raise SystemExit(0)
    chosen=min(selected,key=lambda x:x.file_size)
    if chosen.file_size>6000000:
       print('SOURCE_MESH_TOO_LARGE_FOR_PROBE',chosen.file_size)
       raise SystemExit(0)
    raw=z.read(chosen)
mesh=trimesh.load(io.BytesIO(raw),file_type='obj',process=False,force='mesh')
if not isinstance(mesh,trimesh.Trimesh):raise RuntimeError('Could not parse one L3 mesh')
print('L3_MESH_DIAGNOSTICS',json.dumps({
    'representation_id':chosen.filename,
    'obj_sha256':hashlib.sha256(raw).hexdigest(),
    'mesh_vertices':len(mesh.vertices),'mesh_faces':len(mesh.faces),
    'bbox_units_unverified':mesh.bounds.round(3).tolist(),
    'extents_units_unverified':mesh.extents.round(3).tolist(),
    'watertight':bool(mesh.is_watertight),
    'winding_consistent':bool(mesh.is_winding_consistent),
    'connected_parts':len(mesh.split(only_watertight=False)),
    'unit_and_coordinate_conversion_required':True,
    'independent_anatomic_validation':False,
    'third_party_source_mesh_not_committed':True,
    'anatomy_approved':False},ensure_ascii=False))
,x.filename,re.I) for id in ids)]
    print('ARCHIVE_INDEX',json.dumps({'file_entries':len(all_members),
      'candidate_entries':[{'name':x.filename,'size_bytes':x.file_size} for x in matches[:30]],
      'matched_official_index':any(any(id in x.filename for id in source_reps) for x in matches),
      'source_version':'BodyParts3D 4.0 99-percent-polygon-reduced OBJ',
      'source_license_page':'https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html',
      'reference_geometry_not_original_CT':True,'anatomy_approved':False}))
    selected=[x for x in matches if any(id in x.filename for id in source_reps) and x.filename.lower().endswith('.obj')]
    if not selected:
       print('MODEL_NOT_IDENTIFIED_OR_ARCHIVE_ENTRY_MISSING; do not invent identifier')
       raise SystemExit(0)
    chosen=min(selected,key=lambda x:x.file_size)
    if chosen.file_size>6000000:
       print('SOURCE_MESH_TOO_LARGE_FOR_PROBE',chosen.file_size)
       raise SystemExit(0)
    raw=z.read(chosen)
mesh=trimesh.load(io.BytesIO(raw),file_type='obj',process=False,force='mesh')
if not isinstance(mesh,trimesh.Trimesh):raise RuntimeError('Could not parse one L3 mesh')
print('L3_MESH_DIAGNOSTICS',json.dumps({
    'representation_id':chosen.filename,
    'obj_sha256':hashlib.sha256(raw).hexdigest(),
    'mesh_vertices':len(mesh.vertices),'mesh_faces':len(mesh.faces),
    'bbox_units_unverified':mesh.bounds.round(3).tolist(),
    'extents_units_unverified':mesh.extents.round(3).tolist(),
    'watertight':bool(mesh.is_watertight),
    'winding_consistent':bool(mesh.is_winding_consistent),
    'connected_parts':len(mesh.split(only_watertight=False)),
    'unit_and_coordinate_conversion_required':True,
    'independent_anatomic_validation':False,
    'third_party_source_mesh_not_committed':True,
    'anatomy_approved':False},ensure_ascii=False))
