#!/usr/bin/env python3
"""Synthetic-only numeric guards; no test subject data and no anatomical claims."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

SRC=Path(__file__).resolve().parents[1]/'tools'/'audit-verse-l3-pair-v7.py'
spec=importlib.util.spec_from_file_location('verse_v7',SRC)
v7=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v7)

class PairIntegrity(unittest.TestCase):
    def setUp(self):
        self.ct=np.zeros((32,34,36),dtype=np.float32)
        self.seg=np.zeros_like(self.ct,dtype=np.uint8)
        self.seg[8:18,10:22,9:24]=22
        self.aff=np.diag([0.7,0.9,1.4,1.0])
    def test_safe_synthetic_shape(self):
        r=v7.inspect_arrays(self.ct,self.seg,self.aff,self.aff)
        self.assertTrue(r['technical_geometry_screen_pass'])
        self.assertEqual(r['label22_connected_components_26'],1)
        self.assertFalse(r['anatomy_approved'])
        self.assertFalse(r['correct_l3_identity_expert_verified'])
    def test_boundary_contact_rejected(self):
        self.seg[0,12,12]=22
        r=v7.inspect_arrays(self.ct,self.seg,self.aff,self.aff)
        self.assertIn('i_min',r['label22_touching_volume_faces'])
        self.assertFalse(r['technical_geometry_screen_pass'])
    def test_disconnected_rejected(self):
        self.seg[26:28,27:29,25:27]=22
        r=v7.inspect_arrays(self.ct,self.seg,self.aff,self.aff)
        self.assertEqual(r['label22_connected_components_26'],2)
        self.assertFalse(r['technical_geometry_screen_pass'])
    def test_mismatch_rejected(self):
        shifted=self.aff.copy();shifted[0,3]=0.15
        with self.assertRaisesRegex(ValueError,'affine mismatch'):
            v7.inspect_arrays(self.ct,self.seg,self.aff,shifted)
    def test_absent_l3_is_not_candidate(self):
        self.seg[:]=21
        r=v7.inspect_arrays(self.ct,self.seg,self.aff,self.aff)
        self.assertFalse(r['label22_present'])
        self.assertFalse(r['technical_geometry_screen_pass'])
    def test_no_fake_fractional_labels(self):
        bad=self.seg.astype(np.float32)
        bad[9,10,10]=22.3
        with self.assertRaisesRegex(ValueError,'integer-valued'):
            v7.inspect_arrays(self.ct,bad,self.aff,self.aff)

if __name__=='__main__':unittest.main()
