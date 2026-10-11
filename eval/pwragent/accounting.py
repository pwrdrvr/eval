"""Reprice immutable PwrAgent usage rows; reasoning is an output subset."""
import json
from pathlib import Path

CARD=json.loads((Path(__file__).with_name('pricing-2026-10-11.json')).read_text())


def parent_protocol_proof(result,events):
    """Require durable matching terminal and final provider counters."""
    terminal=False
    final=None
    for event in events:
        n=event.get('notification',{})
        p=n.get('params',{})
        if p.get('threadId')!=result.get('threadId') or p.get('turnId')!=result.get('turnId'):
            continue
        if n.get('method')=='turn/completed' and p.get('turn',{}).get('status')=='completed':terminal=True
        if n.get('method')=='thread/tokenUsage/updated':final=p.get('tokenUsage',{}).get('total')
    return final if terminal and result.get('status')=='completed' else None


def account(result,events=()):
    pricing=result.get('pricing') or {}
    lines=pricing.get('lines',[])
    rows=[]
    unknown=[]
    seen=set()
    proof=parent_protocol_proof(result,events)
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
        reconciled=bool(proof and line.get('scope')=='turn' and line.get('threadId')==result.get('threadId') and line.get('turnId')==result.get('turnId') and line.get('turnUsageAttributed') is True and all(proof.get(k)==line.get(k) for k in ['inputTokens','cachedInputTokens','outputTokens','reasoningOutputTokens']))
        # Total input < threshold proves every component short even if peak
        # metadata is absent. Mixed/unknown requests retain the price interval.
        exact_short=inp<=CARD['long_context_threshold_input_tokens'] or (isinstance(context,int) and context<=CARD['long_context_threshold_input_tokens'])
        rows.append(dict(usage_line_id=identity,model=model,scope=line.get('scope'),status=line.get('status'),protocol_reconciled=reconciled,service_tier=line.get('serviceTier'),input_tokens=inp,uncached_input_tokens=inp-cache,cached_input_tokens=cache,cache_write_tokens=write,output_tokens=out,reasoning_tokens=line.get('reasoningOutputTokens'),peak_context_tokens=context,provider_equivalent_cost_usd=line.get('totalCostMicros',0)/1e6,estimated_cost_usd=lower if exact_short else None,projected_short_usd=lower,projected_long_usd=upper,conservative_budget_usd=conservative,turn_usage_attributed=line.get('turnUsageAttributed')))
    missing=result.get('dispatchIntentAt') and not rows
    return dict(rows=rows,unpriced_models=unknown,usage_complete=bool(rows) and not unknown and not missing and all(r['status']=='finalized' or r['protocol_reconciled'] for r in rows),provider_equivalent_cost_usd=sum(r['provider_equivalent_cost_usd'] for r in rows),estimated_cost_usd=sum(r['estimated_cost_usd'] for r in rows) if rows and all(r['estimated_cost_usd'] is not None for r in rows) else None,projected_cost_lower_usd=sum(r['projected_short_usd'] for r in rows),projected_cost_upper_usd=sum(r['projected_long_usd'] for r in rows),conservative_budget_usd=sum(r['conservative_budget_usd'] for r in rows),billing_basis='Codex subscription usage; not API credit billing; estimated_cost_usd uses common 2026-10-11 card, provider_equivalent_cost_usd preserves app historical catalog')
