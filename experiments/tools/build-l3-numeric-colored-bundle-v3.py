#!/usr/bin/env python3
"""Add numeric label-specific 3D colors to validated CT+mask L3 bundle.

Source label IDs 1..7 are not assigned anatomical structure names. This is
visual, private, research-only CT-derived geometry. No original CT or colored
3D data are committed by this script.
"""
import argparse,base64,hashlib,importlib.util,io,json
from pathlib import Path
import nibabel as nib
import numpy as np
from skimage.measure import marching_cubes
import trimesh

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('l3_source_v1',HERE/'build-l3-local-review-bundle-v1.py')
v1=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)
spec2=importlib.util.spec_from_file_location('l3_pair_v2',HERE/'build-l3-ct-overlay-bundle-v2.py')
v2=importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(v2)

def class_at_surface(vertices,mask,spacing):
    lower=np.floor(vertices).astype(np.int32)
    upper=np.ceil(vertices).astype(np.int32)
    best=np.full(len(vertices),np.inf,dtype=np.float32)
    assigned=np.zeros(len(vertices),dtype=np.uint8)
    shape=np.asarray(mask.shape)-1
    for bit in range(8):
        choices=[upper[:,axis] if ((bit>>axis)&1) else lower[:,axis] for axis in range(3)]
        xyz=np.column_stack(choices)
        xyz=np.maximum(0,np.minimum(xyz,shape))
        labels=mask[tuple(xyz.T)]
        distance=np.sum(((vertices-xyz)*spacing)**2,axis=1)
        selected=(labels>0)&(distance<best)
        best[selected]=distance[selected]
        assigned[selected]=labels[selected]
    if np.any(assigned==0) or np.max(assigned)>7:
        raise ValueError('Source surface vertices cannot be assigned source mask classes')
    return assigned

def convert(mask_file,ct_file,out_file):
    original=v2.build_pair(mask_file,ct_file,out_file)
    bundle=json.loads(out_file.read_text())
    canonical=nib.as_closest_canonical(nib.load(str(mask_file)))
    labels=np.asarray(canonical.dataobj,dtype=np.uint8)
    vertices,faces,_,_=marching_cubes((labels>0).astype(np.float32),level=.5)
    spacing=np.linalg.norm(canonical.affine[:3,:3],axis=0)
    classes=class_at_surface(vertices,labels,spacing)
    xyz=nib.affines.apply_affine(canonical.affine,vertices)
    mesh=trimesh.Trimesh(vertices=xyz,faces=faces,process=False)
    mesh.visual.vertex_colors=v1.COLORS[classes]
    exported=trimesh.exchange.gltf.export_glb(mesh)
    back=trimesh.load(io.BytesIO(exported),file_type='glb',process=False,force='mesh')
    if len(back.faces)!=len(mesh.faces):
        raise ValueError('GLB color conversion changed face count')
    drift=float(np.max(np.abs(back.extents-mesh.extents)))
    if drift>1e-3:raise ValueError('Colored GLB extent drift')
    # Read back actual converted vertex colors, not just input assumptions.
    vertex_colors=np.asarray(back.visual.vertex_colors)
    if vertex_colors.ndim!=2 or vertex_colors.shape[0]!=len(mesh.vertices) or vertex_colors.shape[1]<3:
        raise ValueError('GLB lost numeric surface vertex colors')
    actual=np.asarray(mesh.visual.vertex_colors)
    delta=int(np.max(np.abs(vertex_colors[:,:3].astype(int)-actual[:,:3].astype(int))))
    if delta>1:raise ValueError('GLB vertex colors are not preserved')
    bundle['schema']='L3_REVIEW_BUNDLE_V3_NUMERIC_COLORED_CT'
    bundle['surface']['glb_base64']=base64.b64encode(exported).decode('ascii')
    bundle['surface']['glb_sha256']=hashlib.sha256(exported).hexdigest()
    bundle['surface']['vertex_numeric_labels_colorized']=True
    bundle['surface']['color_error_max_8bit']=delta
    bundle['surface']['numeric_class_vertex_counts']={str(i):int(np.count_nonzero(classes==i)) for i in range(1,8)}
    bundle['surface']['class_color_RGBA']={str(i):v1.COLORS[i].tolist() for i in range(1,8)}
    bundle['anatomy_approved']=False
    bundle['source_label_to_anatomical_name_verified']=False
    out_file.write_text(json.dumps(bundle,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    return {'status':'3D_NUMERIC_LABEL_COLORS_TECHNICALLY_PRESERVED',
      'source_ct_sha256':original['source_ct_sha256'],
      'mask_sha256':original['source_mask_sha256'],
      'triangles':len(mesh.faces),'mesh_colors_preserved':True,
      'max_8bit_color_error':delta,'per_numeric_class_vertices':bundle['surface']['numeric_class_vertex_counts'],
      '3D_labels_are_anatomic_names':False,'anatomy_approved':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('mask','ct','out'):
        p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    print('L3_V3_COLORED_SOURCE '+json.dumps(convert(a.mask,a.ct,a.out),ensure_ascii=False))
if __name__=='__main__':main()
