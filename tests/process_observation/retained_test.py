import threading
import unittest
from retained import RetainedSamples


class Owner:
    pid = 123
    reaped = False
    ended = False
    def terminal(self): return self.ended


class Samples(unittest.TestCase):
    def test_missing_is_preserved_and_bounded(self):
        calls=[]; s=RetainedSamples(Owner(), lambda pid: calls.append(pid) or dict(pid=pid,available=False),limit=2)
        self.assertTrue(s.sample()); self.assertTrue(s.sample()); self.assertFalse(s.sample())
        self.assertEqual(calls,[123,123]); self.assertEqual(s.samples[0]['observation'],dict(pid=123,available=False))
        self.assertFalse(s.report()['resource_release_authorized'])

    def test_reaped_or_terminal_never_queries_reusable_pid(self):
        owner=Owner(); s=RetainedSamples(owner,lambda _:self.fail('query forbidden'))
        owner.ended=True; self.assertFalse(s.sample())
        owner.reaped=True
        with self.assertRaises(RuntimeError): s.sample()

    def test_query_ownership_failure_is_not_missing(self):
        error=RuntimeError('retained probe ownership')
        def query(_): raise error
        s=RetainedSamples(Owner(),query)
        with self.assertRaises(RuntimeError) as caught: s.sample()
        self.assertIs(caught.exception,error); self.assertEqual(s.samples,[])

    def test_wrong_pid_and_bool_counters_refuse(self):
        for value in [dict(pid=124,available=False), dict(pid=123,available=True,resident_bytes=True)]:
            with self.assertRaises(ValueError): RetainedSamples(Owner(),lambda _,v=value:v).sample()

    def test_counter_observation_has_query_bracket(self):
        v=dict(pid=123,available=True,resident_bytes=5,virtual_bytes=10,threads=2,running_threads=1,total_user_native_units=8,total_system_native_units=9)
        ticks=iter([10,20]); s=RetainedSamples(Owner(),lambda _:v,clock=lambda:next(ticks))
        self.assertTrue(s.sample()); self.assertEqual(s.samples[0]['before_monotonic_ns'],10)
        self.assertEqual(s.samples[0]['after_monotonic_ns'],20)

    def test_cross_thread_refuses_without_query(self):
        s=RetainedSamples(Owner(),lambda _:self.fail('wrong thread query')); errors=[]
        def run():
            try: s.sample()
            except RuntimeError as e: errors.append(e)
        thread=threading.Thread(target=run); thread.start(); thread.join()
        self.assertEqual(len(errors),1)


if __name__=='__main__': unittest.main()
