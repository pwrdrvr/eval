"""Report the preregistered long-thread metric without pooling components as trials."""
import argparse
import json
from pathlib import Path
from runtime import LOCAL
from usage_report import build as usage_report
from cost_band_report import build as band_report


def build(protocol):
    pr=json.loads(Path(protocol).read_text())
    rows=[json.loads(p.read_text()) for p in sorted((LOCAL/'records').glob('*.json'))]
    rows=[r for r in rows if r.get('cohort_id')==pr['cohort_id']]
    arms={}
    for row in rows:
        label='on' if row['cell']['token_miser'] else 'off'
        if label in arms:raise ValueError('Duplicate workflow arm; repeats must be specified separately')
        grade=row.get('grade') or {};details=grade.get('details') or {};account=row.get('accounting') or {}
        arms[label]=dict(run_id=row['run_id'],agent_status=row.get('agent_status'),
                         component_passes=details.get('component_passed'),
                         component_count=details.get('component_total'),
                         primary_score=details.get('component_fraction'),
                         whole_thread_success=row.get('success'),
                         complete_usage=account.get('usage_complete',False),
                         reported_cost_usd=account.get('estimated_cost_usd'),
                         cost_upper_usd=account.get('estimated_cost_usd') if account.get('usage_complete') else row['reservation_usd'],
                         components=grade.get('components',[]))
        passed=details.get('component_passed')
        arms[label]['cost_per_verified_feature_usd']=(account['estimated_cost_usd']/passed
            if passed and account.get('usage_complete') and account.get('estimated_cost_usd') is not None else None)
    paired={}
    if set(arms)=={'off','on'}:
        off,on=arms['off'],arms['on'];scores=[off['primary_score'],on['primary_score']]
        paired['thread_pairs_with_valid_score']=int(all(x is not None for x in scores))
        paired['score_delta_on_minus_off']=scores[1]-scores[0] if all(x is not None for x in scores) else None
        if off['complete_usage'] and on['complete_usage']:
            paired['cost_delta_on_minus_off_usd']=on['reported_cost_usd']-off['reported_cost_usd']
            paired['cost_change_fraction']=on['reported_cost_usd']/off['reported_cost_usd']-1
    result=dict(schema_version=1,cohort_id=pr['cohort_id'],primary_metric=pr['analysis']['primary_correctness'],
                uncertainty='One paired workflow. Six components are correlated within each shared model thread and are not six independent experiments. This is a descriptive result; no population-effect confidence interval is justified.',
                comparability='New six-feature workflow, separate from the fixed single-task cohort and published leaderboard. Original component verifiers are unchanged.',
                billing='Codex Pro usage, priced at the frozen standard API card for comparison. Not API-key charges or billing invoices. Reasoning is included in output.',
                arms=arms,paired=paired,protocol=pr)
    dest=LOCAL/('report-'+pr['cohort_id']);dest.mkdir(exist_ok=True)
    (dest/'workflow.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Longer Sol workflow: Token Miser OFF/ON','',result['comparability'],'',result['billing'],'',
           '| Arm | Features passed | Primary score | All six passed and completed | Estimated cost | Cost per verified feature |',
           '|---|---:|---:|---|---:|---:|']
    for label in ['off','on']:
        arm=arms.get(label,{})
        score=arm.get('primary_score');cost=arm.get('reported_cost_usd');per=arm.get('cost_per_verified_feature_usd')
        lines.append('| '+label.upper()+' | '+str(arm.get('component_passes','pending'))+'/'+str(arm.get('component_count',6))+' | '+(f'{score:.1%}' if score is not None else 'pending')+' | '+str(arm.get('whole_thread_success','pending'))+' | '+(f'${cost:.4f}' if cost is not None else 'unknown/pending')+' | '+(f'${per:.4f}' if per is not None else 'undefined/pending')+' |')
    lines+=['',result['uncertainty'],'','The token-breakdown and paired-token-deltas files contain cached input, uncached input, output, reasoning, and separate summary-model rows. Missing usage remains unknown with its reservation retained.']
    (dest/'workflow.md').write_text('\n'.join(lines)+'\n')
    usage_report(protocol);band_report(protocol)
    return dest/'workflow.json'


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--protocol',required=True,type=Path)
    print(build(parser.parse_args().protocol))
