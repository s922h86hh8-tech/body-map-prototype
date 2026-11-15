#!/usr/bin/env python3
"""Synthetic-only technical tests for L3 VerSe v7.3 RAS image orientation."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import nibabel as nib
import numpy as np

SCRIPT=Path(__file__).resolve().parents[1]/'tools'/'build-verse-l3-orientation-review-v7.3.py'
spec=importlib.util.spec_from_file_location('l3v73',SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class OrientationTests(unittest.TestCase):
    def setUp(self):
        self.center=[20.,33.,45.]
        self.n=51
        self.pitch=.65
    def test_center_stays_center_in_three_views(self):
        for p in ('axial','coronal','sagittal'):
            np.testing.assert_allclose(m.pixel_world(self.center,p,25,25,self.n,self.pitch),self.center)
    def test_screen_right_and_top_are_declared_RAS(self):
        for p in ('axial','coronal','sagittal'):
            a=m.AXES[p]
            cr=m.pixel_world(self.center,p,26,25,self.n,self.pitch)
            ct=m.pixel_world(self.center,p,25,24,self.n,self.pitch)
            np.testing.assert_allclose(np.array(cr)-self.center,np.array(a['right'])*self.pitch,atol=1e-9)
            np.testing.assert_allclose(np.array(ct)-self.center,np.array(a['up'])*self.pitch,atol=1e-9)
    def test_sagittal_posterior_is_left(self):
        point=m.pixel_world(self.center,'sagittal',24,25,self.n,self.pitch)
        self.assertAlmostEqual(point[1],self.center[1]-self.pitch)
        self.assertAlmostEqual(point[0],self.center[0])
    def test_bad_point_rejected(self):
        with self.assertRaisesRegex(ValueError,'Invalid pixel'):
            m.pixel_world(self.center,'axial',-1,25,self.n,self.pitch)
        with self.assertRaisesRegex(ValueError,'Unknown plane'):
            m.pixel_world(self.center,'wrong',25,25,self.n,self.pitch)
    def test_resampled_slices_obey_world_directions(self):
        ijk=np.mgrid[:72,:74,:68].astype(float)
        # Image intensity deliberately increases from posterior toward anterior,
        # and from inferior toward superior. Synthetic image, not real anatomy.
        ct=(ijk[0]+2*ijk[1]+3*ijk[2]).astype(np.float32)
        label=np.zeros(ct.shape,dtype=np.uint8)
        label[31:40,31:42,29:40]=22
        aff=np.diag([1.,1.,1.,1.])
        for p in m.AXES:
            data=m.slice_images(ct,label,aff,[35.,36.,34.],p,45,.9)
            self.assertGreater(data['l3_pixels_in_plane'],0)
            self.assertGreater(data['source_CT_plane_inside_fraction'],.99)
            self.assertTrue(data['ct_png_base64'])
            self.assertTrue(data['ct_l3_overlay_png_base64'])
    def test_source_grid_can_have_negative_voxel_axis(self):
        ijk=np.mgrid[:64,:64,:64]
        ct=(ijk[0]+2*ijk[1]+3*ijk[2]).astype(np.float32)
        label=np.zeros(ct.shape,dtype=np.uint8);label[27:37,27:37,27:37]=22
        affine=np.diag([-1.,-1.,1.,1.])
        affine[:3,3]=[63.,63.,0.]
        sample=m.slice_images(ct,label,affine,[31.5,31.5,31.5],'sagittal',41,.65)
        self.assertGreater(sample['l3_pixels_in_plane'],0)
    def test_reject_mismatched_ct_mask_grids(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);ct=root/'ct.nii.gz';seg=root/'seg.nii.gz';out=root/'private.json'
            arr=np.zeros((48,48,48),np.float32);masks=np.zeros(arr.shape,np.uint8)
            masks[18:31,18:31,18:31]=22
            a=np.eye(4); b=np.eye(4); b[1,3]=.2
            nib.save(nib.Nifti1Image(arr,a),str(ct))
            nib.save(nib.Nifti1Image(masks,b),str(seg))
            with self.assertRaisesRegex(ValueError,'affines differ'):
                m.build(ct,seg,'fake',out,41,.65)
    def test_full_builder_local_only_flags(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);ct=root/'ct.nii.gz';seg=root/'seg.nii.gz';out=root/'PRIVATE.json'
            ijk=np.mgrid[:64,:64,:64]
            arr=(ijk[0]+ijk[1]*2+ijk[2]*3).astype(np.float32)
            masks=np.zeros(arr.shape,np.uint8);masks[24:41,23:42,22:43]=22
            a=np.eye(4)
            nib.save(nib.Nifti1Image(arr,a),str(ct))
            nib.save(nib.Nifti1Image(masks,a),str(seg))
            log=m.build(ct,seg,'SYNTHETIC_NOT_ANATOMY',out,41,.65)
            d=json.loads(out.read_text())
            self.assertEqual(set(d['screens']),{'axial','coronal','sagittal'})
            self.assertEqual(log['ras_direction_labels']['sagittal'],['A','S'])
            self.assertTrue(d['images_are_sensitive_do_not_upload'])
            self.assertFalse(d['front_back_anatomical_direction_verified'])
            self.assertFalse(d['anatomy_approved'])
            self.assertEqual(len(d['source_CT_sha256']),64)

if __name__=='__main__':
    unittest.main()
