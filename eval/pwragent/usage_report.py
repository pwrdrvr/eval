"""Auditable token and cost decomposition, including every helper row."""
import argparse
import csv
import json
from pathlib import Path
from runtime import LOCAL

TOKEN_KEYS = ('input_tokens','cached_input_tokens','uncached_input_tokens',
              'cache_write_tokens','output_tokens','reasoning_tokens','nonreasoning_output_tokens')
COST_KEYS = ('uncached_input_excluding_writes','cached_input','cache_writes',
             'output_including_reasoning','reasoning_subset')


def breakdown(records):
    groups=[]
    for record in records:
        accounting=record.get('accounting',{})
        buckets={}
        for row in accounting.get('rows',[]):
            key=(row['model'],row.get('usage_role','unclassified'))
            buckets.setdefault(key,[]).append(row)
        for (model,role),rows in buckets.items():
            result=dict(run_id=record['run_id'],task=record['cell']['task'],
                        requested_model=record['cell']['model'],token_miser=record['cell']['token_miser'],
                        usage_model=model,usage_role=role,usage_rows=len(rows),
                        agent_status=record.get('agent_status'),success=record.get('success'),
                        usage_complete=accounting.get('usage_complete',False))
            for key in TOKEN_KEYS:
                values=[r.get(key) for r in rows]
                result[key]=sum(values) if all(isinstance(v,int) for v in values) else None
            costs=[r.get('estimated_cost_usd') for r in rows]
            result['estimated_cost_usd']=sum(costs) if all(v is not None for v in costs) else None
            for key in COST_KEYS:
                values=[(r.get('estimated_cost_components_usd') or {}).get(key) for r in rows]
                result[key+'_usd']=sum(values) if all(v is not None for v in values) else None
            result['usage_line_ids']=[r['usage_line_id'] for r in rows]
            groups.append(result)
    return groups


def build(protocol):
    pr=json.loads(Path(protocol).read_text())
    records=[json.loads(p.read_text()) for p in sorted((LOCAL/'records').glob('*.json'))]
    records=[r for r in records if r.get('cohort_id')==pr['cohort_id']]
    groups=breakdown(records)
    dest=LOCAL/('report-'+pr['cohort_id']);dest.mkdir(exist_ok=True)
    note=('API-equivalent estimates for Pro subscription execution, not API bills. '
          'Input = cached + uncached. Cache writes are a subset of uncached input. '
          'Reasoning is a subset of output; never add it again. Costs sum uncached input excluding writes, '
          'cached input, writes, and output including reasoning. Summary-model and other helpers are separate. '
          'Incomplete rows are reported snapshots, not final usage. Account-wide quota changes are excluded.')
    (dest/'token-breakdown.json').write_text(json.dumps({'notes':note,'groups':groups},indent=2)+'\n')
    if groups:
        with (dest/'token-breakdown.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=[k for k in groups[0] if k!='usage_line_ids'])
            writer.writeheader();writer.writerows({k:v for k,v in g.items() if k!='usage_line_ids'} for g in groups)
    md=['# Measured token breakdown','',note,'',
        '| Run | Usage model / role | Cached input | Uncached input | Output (includes reasoning) | Reasoning subset | Estimated $ |',
        '|---|---|---:|---:|---:|---:|---:|']
    for g in groups:
        count=lambda key: f"{g[key]:,}" if g[key] is not None else 'unknown'
        cost=f"{g['estimated_cost_usd']:.6f}" if g['estimated_cost_usd'] is not None else 'unknown'
        md.append(f"| {g['run_id']} | {g['usage_model']} / {g['usage_role']} | {count('cached_input_tokens')} | {count('uncached_input_tokens')} | {count('output_tokens')} | {count('reasoning_tokens')} | {cost} |")
    (dest/'token-breakdown.md').write_text('\n'.join(md)+'\n')
    return dest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--protocol',type=Path,required=True)
    print(build(p.parse_args().protocol))
