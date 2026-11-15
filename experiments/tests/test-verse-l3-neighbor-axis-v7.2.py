#!/usr/bin/env python3
"""Synthetic numeric axis/label guards only, never anatomical image validation."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

SRC=Path(__file__).resolve().parents[1]/'tools'/'audit-verse-l3-neighbor-axis-v7.2.py'
spec=importlib.util.spec_from_file_location('neighbor_v72',SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class NeighborAxis(unittest.TestCase):
    def setUp(self):
        self.arr=np.zeros((14,14,24),dtype=np.uint8)
        self.arr[5:9,5:9,16:20]=21
        self.arr[5:9,5:9,10:14]=22
        self.arr[5:9,5:9,4:8]=23
        self.aff=np.diag([1.2,0.8,2.0,1.0])
    def test_up_down_label_order(self):
        r=m.audit_neighbor_geometry(self.arr,self.aff)
        self.assertTrue(r['neighbor_z_order_expected_in_affine_RAS'])
        self.assertEqual(r['label_offsets_from_L3_RAS_mm']['21']['offset_from_22_RAS_mm'][2],12.0)
        self.assertEqual(r['label_offsets_from_L3_RAS_mm']['23']['offset_from_22_RAS_mm'][2],-12.0)
        self.assertFalse(r['anterior_posterior_independent_landmarks_verified'])
        self.assertFalse(r['expert_anatomy_approved'])
    def test_global_translation_not_in_relative_offsets(self):
        a=self.aff.copy()
        a[:3,3]=[125,-76,210]
        r=m.audit_neighbor_geometry(self.arr,a)
        self.assertEqual(r['label_offsets_from_L3_RAS_mm']['21']['offset_from_22_RAS_mm'][2],12.0)
    def test_reversed_superior_world_axis_does_not_pass(self):
        a=self.aff.copy()
        a[2,2]=-2.
        r=m.audit_neighbor_geometry(self.arr,a)
        self.assertFalse(r['neighbor_z_order_expected_in_affine_RAS'])
        self.assertEqual(r['neighbor_z_order_checks']['L2_number_above_L3_in_RAS_S'],False)
    def test_absent_neighbour_is_not_pass(self):
        a=self.arr.copy();a[a==21]=0
        r=m.audit_neighbor_geometry(a,self.aff)
        self.assertIsNone(r['neighbor_z_order_checks']['L2_number_above_L3_in_RAS_S'])
        self.assertFalse(r['neighbor_z_order_expected_in_affine_RAS'])
    def test_missing_l3_rejected(self):
        a=self.arr.copy();a[a==22]=0
        with self.assertRaisesRegex(ValueError,'No VerSe L3'):
            m.audit_neighbor_geometry(a,self.aff)
    def test_fractional_rejected(self):
        a=self.arr.astype(float)
        a[5,5,12]=22.5
        with self.assertRaisesRegex(ValueError,'finite integers'):
            m.audit_neighbor_geometry(a,self.aff)
    def test_noninvertible_affine_rejected(self):
        a=self.aff.copy();a[2,2]=0
        with self.assertRaisesRegex(ValueError,'Singular'):
            m.audit_neighbor_geometry(self.arr,a)
    def test_not_AP_independent_even_when_S_order_pass(self):
        a=self.aff.copy(); a[0,0]=-1.2; a[1,1]=-0.8
        r=m.audit_neighbor_geometry(self.arr,a)
        self.assertTrue(r['neighbor_z_order_expected_in_affine_RAS'])
        self.assertFalse(r['anterior_posterior_independent_landmarks_verified'])

if __name__=='__main__':
    unittest.main()
