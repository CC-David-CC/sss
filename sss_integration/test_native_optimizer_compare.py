"""Optional NumPy checks for the completed-state mechanics comparator."""
import unittest
import numpy as np
from sss_integration.native_optimizer_compare import compare_arrays

class ContinuationComparisonTests(unittest.TestCase):
 def test_nonfinite_and_layout_mismatches_refuse_comparison(self):
  for a,b in [(np.array([1],dtype="float32"),np.array([1,2],dtype="float32")),(np.array([float("nan")],dtype="float32"),np.array([1],dtype="float32"))]:
   with self.assertRaises(ValueError):compare_arrays(a,b,atol=2e-7,rtol=2e-6)
 def test_checks_all_chunks_and_signed_zero_bits(self):
  a=np.zeros((1<<20)+1,dtype="float32");b=a.copy();b[0]=-0.;b[-1]=1e-3
  result=compare_arrays(a,b,atol=2e-7,rtol=2e-6)
  self.assertEqual(result["elements"],len(a));self.assertEqual(result["bitwise_differences"],2);self.assertEqual(result["outside_tolerance"],1)
 def test_tolerance_is_symmetric_and_does_not_imply_bitwise_identity(self):
  a=np.array([1.,1e-9],dtype="float32");b=np.nextafter(a,np.float32(2.))
  forward=compare_arrays(a,b,atol=2e-7,rtol=2e-6);reverse=compare_arrays(b,a,atol=2e-7,rtol=2e-6)
  self.assertEqual(forward,reverse);self.assertEqual(forward["outside_tolerance"],0);self.assertEqual(forward["bitwise_differences"],2)

if __name__=="__main__":unittest.main()
