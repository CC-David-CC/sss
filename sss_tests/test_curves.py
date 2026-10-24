import copy,unittest
from sss.curves import measured_curves
from sss.records import digest
class MeasuredCurves(unittest.TestCase):
 def setUp(self):
  self.p=dict(cases_per_evaluation=4,batch_size=2,checkpoint_updates=[0,1,2],arms=[dict(id='owned')],reference=dict(unchanged_original_F32_sha256='a'*64))
  self.p['protocol_id']=digest(self.p)
  def point(update,gain,loss):return dict(arm='owned',update=update,presentations=update*2,original_answers_gained=gain,original_answers_lost=loss,passed=2+gain-loss,finished=4,model_sha256='a'*64 if update==0 else 'b'*64)
  self.d=dict(protocol_id=self.p['protocol_id'],reference_passed=2,reference_finished=4,status='COMPLETE',points=[point(0,0,0),point(1,2,2),point(2,2,1)])
 def test_net_score_does_not_hide_lost_original_answers(self):
  rows=measured_curves(self.p,self.d)['owned'];self.assertEqual(rows[1]['passed'],2);self.assertEqual(rows[1]['original_answers_lost'],2);self.assertEqual(rows[2]['passed'],3)
 def test_missing_measurement_cannot_be_interpolated(self):
  self.d['points'].pop(1)
  with self.assertRaises(ValueError):measured_curves(self.p,self.d)
 def test_changed_exposure_and_net_totals_are_rejected(self):
  for change in [dict(presentations=999),dict(passed=4),dict(original_answers_lost=-1),dict(update=True)]:
   value=copy.deepcopy(self.d);value['points'][1].update(change)
   with self.assertRaises(ValueError):measured_curves(self.p,value)
 def test_altered_protocol_and_false_completion_are_rejected(self):
  value=copy.deepcopy(self.p);value['batch_size']=3
  with self.assertRaises(ValueError):measured_curves(value,self.d)
  self.d['points'].pop()
  with self.assertRaises(ValueError):measured_curves(self.p,self.d)
if __name__=='__main__':unittest.main()
