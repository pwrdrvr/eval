import unittest
from accounting import account


def line(**kw):
    return dict(usageLineId='a',model='gpt-6.1-sol',status='finalized',inputTokens=1000,cachedInputTokens=600,cacheWriteInputTokens=100,outputTokens=200,reasoningOutputTokens=150,**kw)


class AccountingTests(unittest.TestCase):
    def test_reasoning_and_cache_writes_are_subsets_not_double_counted(self):
        a=account({'dispatchIntentAt':'x','pricing':{'lines':[line()]}})
        self.assertTrue(a['usage_complete'])
        self.assertAlmostEqual(a['projected_cost_lower_usd'],(300*2+600*.1+100*2.5+200*10)/1e6)

    def test_duplicate_cumulative_rows_and_unpriced_helpers_fail_closed(self):
        with self.assertRaises(ValueError):account({'pricing':{'lines':[line(),line()]}})
        x=line();x['model']='unknown-helper'
        self.assertFalse(account({'dispatchIntentAt':'x','pricing':{'lines':[x]}})['usage_complete'])

    def test_missing_usage_after_dispatch_cannot_be_zero_cost(self):
        self.assertFalse(account({'dispatchIntentAt':'x','pricing':{'lines':[]}})['usage_complete'])

    def test_pending_label_needs_matching_terminal_and_provider_counters(self):
        x=line();x.update(status='pending',scope='turn',threadId='thread',turnId='turn',turnUsageAttributed=True)
        result={'dispatchIntentAt':'x','threadId':'thread','turnId':'turn','status':'completed','pricing':{'lines':[x]}}
        events=[{'notification':{'method':'thread/tokenUsage/updated','params':{'threadId':'thread','turnId':'turn','tokenUsage':{'total':{k:x[k] for k in ['inputTokens','cachedInputTokens','outputTokens','reasoningOutputTokens']}}}}},{'notification':{'method':'turn/completed','params':{'threadId':'thread','turnId':'turn','turn':{'status':'completed'}}}}]
        self.assertFalse(account(result)['usage_complete'])
        self.assertTrue(account(result,events)['usage_complete'])
        events[0]['notification']['params']['tokenUsage']['total']['outputTokens']+=1
        self.assertFalse(account(result,events)['usage_complete'])


if __name__=='__main__':unittest.main()
