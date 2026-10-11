"""Produce an interim paired report without silently dropping failed cells."""
import json
import math
from pathlib import Path
import random
import statistics
from runtime import LOCAL,ROOT


def interval(values,seed=20261011):
    if not values:return None
    rng=random.Random(seed)
    samples=sorted(statistics.mean(rng.choices(values,k=len(values))) for _ in range(10000))
    return [samples[249],samples[9749]]


def build():
    records=[json.loads(f.read_text()) for f in sorted((LOCAL/'records').glob('*.json'))]
    summary={'schema_version':1,'stage':'interim: pause all further eval/model work for user review','preregistration':json.loads((ROOT/'eval/pwragent/preregistered-stage.json').read_text()),'ledger':json.loads((LOCAL/'stage-ledger.json').read_text()),'models':{},'records':records}
    for model in summary['preregistration']['models']:
        rows=[r for r in records if r['cell']['model']==model]
        arms={}
        for arm,label in [(False,'off'),(True,'on')]:
            a=[r for r in rows if r['cell']['token_miser']==arm]
            valid=[r for r in a if r.get('success') is not None]
            costs=[r['accounting']['estimated_cost_usd'] for r in a if r.get('accounting',{}).get('usage_complete') and r['accounting'].get('estimated_cost_usd') is not None]
            total=sum(costs)
            passed=sum(r.get('success') is True for r in valid)
            arms[label]=dict(attempted=len(a),graded_valid=len(valid),infra_invalid=len(a)-len(valid),passes=passed,pass_at_1=passed/len(valid) if valid else None,costed_runs=len(costs),api_equivalent_cost_usd=total,mean_cost_per_attempt_usd=statistics.mean(costs) if costs else None,cost_per_resolved_task_usd=total/passed if passed and len(costs)==len(a) else None)
        by_task={}
        for r in rows:by_task.setdefault(r['cell']['task'],{})[r['cell']['token_miser']]=r
        pairs=[(t,p[False],p[True]) for t,p in by_task.items() if set(p)=={False,True} and all(r.get('success') is not None for r in p.values())]
        diffs=[int(on['success'])-int(off['success']) for _,off,on in pairs]
        wins=sum(x==1 for x in diffs);losses=sum(x==-1 for x in diffs);discord=wins+losses
        pvalue=min(1,2*sum(math.comb(discord,k) for k in range(min(wins,losses)+1))/2**discord) if discord else 1
        cost_pairs=[(off['accounting']['estimated_cost_usd'],on['accounting']['estimated_cost_usd']) for _,off,on in pairs if off.get('accounting',{}).get('usage_complete') and on.get('accounting',{}).get('usage_complete') and all(r['accounting'].get('estimated_cost_usd') is not None for r in [off,on])]
        cost_diffs=[on-off for off,on in cost_pairs]
        paired=dict(n=len(pairs),score_delta_on_minus_off=statistics.mean(diffs) if diffs else None,score_delta_bootstrap_95_ci=interval(diffs),on_only_pass=wins,off_only_pass=losses,exact_mcnemar_p=pvalue,cost_pairs=len(cost_pairs),mean_cost_delta_on_minus_off_usd=statistics.mean(cost_diffs) if cost_diffs else None,cost_delta_bootstrap_95_ci_usd=interval(cost_diffs),aggregate_cost_change_fraction=(sum(b for a,b in cost_pairs)/sum(a for a,b in cost_pairs)-1) if cost_pairs and sum(a for a,b in cost_pairs)>0 else None)
        summary['models'][model]={'arms':arms,'paired':paired}
    dest=LOCAL/'report';dest.mkdir(exist_ok=True)
    (dest/'interim.json').write_text(json.dumps(summary,indent=2)+'\n')
    (dest/'records.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in records))
    md=['# PwrAgent Token Miser interim evaluation','', 'Further paid/subscription eval model work is paused pending explicit user review approval.','', '| Model | OFF passes | ON passes | Paired tasks | ON−OFF score | ON−OFF mean cost |', '|---|---:|---:|---:|---:|---:|']
    for model,s in summary['models'].items():
        a=s['arms'];p=s['paired'];delta=p['score_delta_on_minus_off'];cost=p['mean_cost_delta_on_minus_off_usd']
        md.append(f"| {model} | {a['off']['passes']}/{a['off']['graded_valid']} | {a['on']['passes']}/{a['on']['graded_valid']} | {p['n']} | {delta*100:.1f} pp | ${cost:.4f} |" if delta is not None and cost is not None else f"| {model} | {a['off']['passes']}/{a['off']['graded_valid']} | {a['on']['passes']}/{a['on']['graded_valid']} | {p['n']} | unresolved | unresolved |")
    md.extend(['','Costs are API-equivalent estimates for Codex subscription execution, not verified API-credit invoices. The ledger uses a higher conservative projection for admission and keeps unknown spend reserved. Reasoning is included in output; native helper and retrieval rows are retained.','', 'This uses own matched pairs on available Terminal-Bench 2.0 and DeepSWE packages in native Linux arm64 containers, not SWE-bench Verified or the published Kimi/amd64 FrontierHarness leaderboard configuration. Sample selection, order, hashes, exact commits, pricing snapshot, failures and confidence intervals are in interim.json. A small sample does not establish population-level improvement.','', 'Historical GPT-5.6-Sol host pilots are auxiliary, non-efficacy-grade evidence. They are not pooled with these requested-model results.','', 'Budget ledger: '+json.dumps({k:v for k,v in summary['ledger'].items() if k!='entries'})])
    (dest/'interim.md').write_text('\n'.join(md)+'\n')
    print(json.dumps({'report':str(dest/'interim.json'),'models':summary['models'],'ledger':{k:v for k,v in summary['ledger'].items() if k!='entries'}},indent=2))


if __name__=='__main__':build()
