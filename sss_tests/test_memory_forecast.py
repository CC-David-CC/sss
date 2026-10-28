import copy
import unittest
from sss.records import digest
from sss.studies.memory_forecast import observed_memory_forecast,placement_candidates


class MemoryForecastTests(unittest.TestCase):
    def setUp(self):
        self.descriptor=dict(phase='cow-inference',runtime_id='a'*64,evaluation_id='b'*64,
            layout_id='c'*64,device_class='Controlled A100 class',format='F32',
            context_tokens=512,batch_tokens=512,maximum_tokens=64)
        self.process=dict(pid=123,start_ticks=456,boot_id='00000000-0000-0000-0000-000000000000')
        self.samples=[dict(process=copy.deepcopy(self.process),used_bytes=n) for n in (80,100,90)]
        self.forecast=self.build()
    def build(self):return observed_memory_forecast(self.descriptor,self.process,self.samples,evidence_sha256='d'*64)
    def row(self,identity,free,util=100,device=None):
        return dict(gpu_uuid='GPU-'+identity,device_class=device or self.descriptor['device_class'],free_bytes=free,utilization_percent=util)
    def test_peak_is_explicitly_a_forecast_without_execution_authority(self):
        self.assertEqual(self.forecast['peak_observed_bytes'],100)
        self.assertFalse(self.forecast['guaranteed_upper_bound']);self.assertTrue(self.forecast['native_admission_required'])
        self.assertFalse(self.forecast['work_authorized'])
    def test_busy_card_remains_eligible_and_smaller_idle_window_is_preferred(self):
        cards=[self.row('busy',100,100),self.row('large',1000,0),self.row('small',110,0),self.row('short',99,0)]
        selected=placement_candidates(self.forecast,self.descriptor,cards)
        self.assertEqual([r['gpu_uuid'] for r in selected],['GPU-small','GPU-large','GPU-busy'])
    def test_every_workload_dimension_is_bound(self):
        for key in self.descriptor:
            changed=copy.deepcopy(self.descriptor)
            changed[key]=1024 if type(changed[key]) is int else 'different'
            with self.subTest(key=key),self.assertRaises(ValueError):placement_candidates(self.forecast,changed,[])
    def test_training_cannot_reuse_inference_memory_observations(self):
        self.descriptor['phase']='backprop'
        with self.assertRaises(ValueError):self.build()
    def test_process_reuse_or_foreign_sample_is_refused(self):
        for key,new in [('pid',124),('start_ticks',457),('boot_id','11111111-1111-1111-1111-111111111111')]:
            changed=copy.deepcopy(self.samples);changed[1]['process'][key]=new
            with self.subTest(key=key),self.assertRaises(ValueError):observed_memory_forecast(self.descriptor,self.process,changed,evidence_sha256='d'*64)
    def test_missing_and_nonpositive_memory_cannot_authorize_a_window(self):
        for values in ([],[0],[-1],[True],[1.5]):
            samples=[dict(process=self.process,used_bytes=n) for n in values]
            with self.subTest(values=values),self.assertRaises(ValueError):observed_memory_forecast(self.descriptor,self.process,samples,evidence_sha256='d'*64)
    def test_foreign_hardware_is_not_a_measured_match(self):
        self.assertEqual(placement_candidates(self.forecast,self.descriptor,[self.row('other',1000,0,'Other GPU class')]),[])
    def test_mutated_or_relabelled_forecast_is_refused(self):
        for key,value in [('peak_observed_bytes',1),('work_authorized',True),('guaranteed_upper_bound',True),('schema',True)]:
            changed=copy.deepcopy(self.forecast);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):placement_candidates(changed,self.descriptor,[])
    def test_bad_inventory_is_not_silently_filtered(self):
        good=self.row('same',101)
        for rows in ([good,good],[dict(good,free_bytes=True)],[dict(good,utilization_percent=101)],[dict(good,free_bytes=-1)]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):placement_candidates(self.forecast,self.descriptor,rows)
    def test_empty_windows_do_not_create_a_fallback_or_change_inputs(self):
        original=copy.deepcopy(self.forecast)
        self.assertEqual(placement_candidates(self.forecast,self.descriptor,[self.row('small',99)]),[])
        self.assertEqual(self.forecast,original)
    def test_boolean_process_numbers_cannot_alias_an_integer_identity(self):
        owner=dict(self.process,pid=1)
        samples=[dict(process=dict(owner,pid=True),used_bytes=100)]
        with self.assertRaises(ValueError):observed_memory_forecast(self.descriptor,owner,samples,evidence_sha256='d'*64)
