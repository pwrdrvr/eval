import unittest
from report import verifier_scores


class VerifierScoreTests(unittest.TestCase):
    def test_task_weighting_preserves_partial_failures_and_excludes_invalid_infra(self):
        rows=[
            {'success':False,'agent_status':'completed','grade':{'details':{'f2p':0.5,'p2p':1.0,'partial':0.99,'f2p_total':2,'p2p_total':100}}},
            {'success':True,'agent_status':'completed','grade':{'details':{'f2p':1.0,'p2p':1.0,'partial':1.0,'f2p_total':200,'p2p_total':10000}}},
            {'success':None,'agent_status':'completed','grade':{'details':{'f2p':0.0,'p2p':0.0,'partial':0.0}}},
        ]
        scores=verifier_scores(rows)
        self.assertEqual(scores['f2p'],{'task_attempts_with_score':2,'mean':0.75})
        self.assertEqual(scores['partial']['mean'],0.995)
        self.assertEqual(scores['p2p']['mean'],1.0)
        self.assertFalse(rows[0]['success'])

    def test_budget_stop_keeps_raw_verifier_fraction_without_turning_it_into_success(self):
        row={'success':False,'agent_status':'budget_exceeded','grade':{'details':{'f2p':1.0,'p2p':1.0,'partial':1.0}}}
        scores=verifier_scores([row])
        self.assertEqual(scores['partial']['mean'],1.0)
        self.assertEqual(scores['noncompleted_agent_attempts'],1)
        self.assertFalse(row['success'])


if __name__=='__main__':unittest.main()
