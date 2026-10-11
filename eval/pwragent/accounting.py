"""Reprice immutable PwrAgent usage rows; reasoning is an output subset."""
import json
from pathlib import Path

CARD=json.loads((Path(__file__).with_name('pricing-2026-10-11.json')).read_text())


def account(result):
    pricing=result.get('pricing') or {}
    lines=pricing.get('lines',[])
    rows=[]
    unknown=[]
    seen=set()
    for line in lines:
        identity=line.get('usageLineId')
        if not identity or identity in seen:
            raise ValueError('missing/duplicate usage identity')
        seen.add(identity)
        if line.get('status')=='superseded':
            continue
        model=line.get('model')
        rates=CARD['models'].get(model)
        if not rates:
            unknown.append(model);continue
        inp=line.get('inputTokens')
        out=line.get('outputTokens')
        cache=line.get('cachedInputTokens')
        write=line.get('cacheWriteInputTokens',0)
        if not all(isinstance(v,int) and v>=0 for v in [inp,out,cache,write]) or cache>inp or write>inp-cache:
            raise ValueError('inconsistent measured tokens')
        context=line.get('peakContextTokens')
        # A turn ledger can span short/long requests. Protocol request records
        # are needed for exact tier splits; report a bounded projection here.
        short,long=rates['short'],rates['long']
        def cost(r):
            return ((inp-cache-write)*r[0]+cache*r[1]+write*r[2]+out*r[3])/1e6
        lower,upper=cost(short),cost(long)
        conservative=((inp-cache)*max(long[0],long[2])+cache*long[1]+out*long[3])/1e6
        rows.append(dict(usage_line_id=identity,model=model,scope=line.get('scope'),status=line.get('status'),service_tier=line.get('serviceTier'),input_tokens=inp,uncached_input_tokens=inp-cache,cached_input_tokens=cache,cache_write_tokens=write,output_tokens=out,reasoning_tokens=line.get('reasoningOutputTokens'),peak_context_tokens=context,provider_equivalent_cost_usd=line.get('totalCostMicros',0)/1e6,projected_short_usd=lower,projected_long_usd=upper,conservative_budget_usd=conservative,turn_usage_attributed=line.get('turnUsageAttributed')))
    missing=result.get('dispatchIntentAt') and not rows
    return dict(rows=rows,unpriced_models=unknown,usage_complete=bool(rows) and not unknown and not missing and all(r['status']=='finalized' for r in rows),provider_equivalent_cost_usd=sum(r['provider_equivalent_cost_usd'] for r in rows),projected_cost_lower_usd=sum(r['projected_short_usd'] for r in rows),projected_cost_upper_usd=sum(r['projected_long_usd'] for r in rows),conservative_budget_usd=sum(r['conservative_budget_usd'] for r in rows),billing_basis='Codex subscription usage; not API credit billing')
