"""Saved-state equality must distinguish bytes that numeric equality merges."""
import unittest
import numpy as np
from sss_integration.registered_lora_model import same_tensors


class SavedTensorEquality(unittest.TestCase):
    def test_signed_zero_is_not_bit_identical(self):
        positive=np.array([0.],dtype='<f4');negative=np.array([-0.],dtype='<f4')
        self.assertTrue(np.array_equal(positive,negative))
        self.assertFalse(same_tensors({'moment':positive},{'moment':negative}))
        self.assertTrue(same_tensors({'moment':positive},{'moment':positive.copy()}))

    def test_finite_matching_layout_and_exact_values_required(self):
        value=np.array([1.,2.],dtype='<f4');changed=value.copy()
        changed[0]=np.nextafter(changed[0],np.float32(2.))
        for other in [changed,value.astype('<f8'),value.reshape(1,2),
                      np.array([np.nan,2.],dtype='<f4'),np.array([np.inf,2.],dtype='<f4')]:
            with self.subTest(other=other):
                self.assertFalse(same_tensors({'weight':value},{'weight':other}))
        self.assertFalse(same_tensors({'weight':value},{'other':value}))
        self.assertFalse(same_tensors({'weight':np.array([np.nan])},{'weight':np.array([np.nan])}))


if __name__=='__main__':unittest.main()
