"""Original event fixtures only; no helper, SDK, process census or payload."""
import copy
import unittest
from intervals import overlap, IncompleteEvidence

class Intervals(unittest.TestCase):
    def setUp(self):
        self.expected=[dict(pid=10,candidate_id='left',threads=1),dict(pid=20,candidate_id='right',threads=1)]
        self.events=[self.event('start',10,100),self.event('start',20,150),
                     self.event('end',10,200),self.event('end',20,250)]
    def event(self,kind,pid,tick):
        return dict(kind=kind,pid=pid,candidate_id={10:'left',20:'right'}[pid],clock_id='same-clock',tick_ns=tick)
    def run_events(self,events):
        return overlap(events,expected=self.expected,clock_id='same-clock')
    def test_overlap(self):
        value=self.run_events(self.events)
        self.assertEqual(value['overlap_ns'],50)
        self.assertTrue(value['overlap_observed'])
        self.assertFalse(value['settlement_proved'])
        self.assertFalse(value['timestamp_producer_qualified'])
    def test_serial_and_touching_are_functional_but_no_overlap(self):
        for start in (200,201):
            value=self.run_events([self.event('start',10,100),self.event('end',10,200),
                self.event('start',20,start),self.event('end',20,300)])
            self.assertFalse(value['overlap_observed'])
    def test_incomplete_or_extra_census(self):
        for events in (self.events[:3],self.events+self.events[:1],[]):
            with self.assertRaises(IncompleteEvidence):self.run_events(events)
    def test_clock_candidate_and_pid_binding(self):
        for key,value in [('clock_id','other'),('candidate_id','wrong'),('pid',30),('pid',True)]:
            events=copy.deepcopy(self.events);events[1][key]=value
            with self.assertRaises(IncompleteEvidence):self.run_events(events)
    def test_timestamp_types_and_range(self):
        for tick in (True,1.5,float('nan'),float('inf'),-1,2**63):
            events=copy.deepcopy(self.events);events[1]['tick_ns']=tick
            with self.assertRaises(IncompleteEvidence):self.run_events(events)
    def test_out_of_order_duplicate_and_end_before_start(self):
        for events in ([self.events[1],self.events[0],*self.events[2:]],
                       [self.events[0],self.events[0],*self.events[2:]],
                       [self.event('end',10,100),*self.events[1:]]):
            with self.assertRaises(IncompleteEvidence):self.run_events(events)
    def test_binding_census_and_weights(self):
        for key,value in [('pid',10),('candidate_id','left'),('threads',2),('threads',True)]:
            expected=copy.deepcopy(self.expected);expected[1][key]=value
            with self.assertRaises(IncompleteEvidence):overlap(self.events,expected=expected,clock_id='same-clock')
    def test_zero_duration_and_unknown_fields(self):
        with self.assertRaises(IncompleteEvidence):
            self.run_events([self.event('start',10,100),self.event('end',10,100),
                self.event('start',20,150),self.event('end',20,200)])
        for key,value in [('kind','finish'),('extra',0)]:
            events=copy.deepcopy(self.events);events[2][key]=value
            with self.assertRaises(IncompleteEvidence):self.run_events(events)

if __name__=='__main__':unittest.main()
