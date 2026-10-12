"""Describe the preregistered baseline-cost band without discarding other pairs."""
import argparse
import json
from pathlib import Path
import statistics

from report import interval
from runtime import LOCAL


def summarize(records, models, minimum=3, maximum=15):
    output = {}
    for model in models:
        tasks = {}
        for record in records:
            if record['cell']['model'] == model:
                pair = tasks.setdefault(record['cell']['task'], {})
                arm = record['cell']['token_miser']
                if arm in pair:
                    raise ValueError('Duplicate task/model/arm; define repeats before pooling')
                pair[arm] = record
        pairs = []
        for task, arms in tasks.items():
            off, on = arms.get(False), arms.get(True)
            complete = all(r and r.get('accounting', {}).get('usage_complete')
                           and r.get('success') is not None for r in (off, on))
            baseline = (off or {}).get('accounting', {})
            cost = baseline.get('estimated_cost_usd')
            eligible = (minimum <= cost <= maximum
                        if baseline.get('usage_complete') and cost is not None else None)
            row = dict(task=task, paired_complete=complete, baseline_in_band=eligible)
            for label, record in [('off', off), ('on', on)]:
                row[label] = None if not record else {
                    'run_id': record['run_id'], 'success': record.get('success'),
                    'agent_status': record.get('agent_status'),
                    'cost_usd': record.get('accounting', {}).get('estimated_cost_usd'),
                    'usage_complete': record.get('accounting', {}).get('usage_complete', False),
                    'grade': record.get('grade'),
                }
            pairs.append(row)
        selected = [p for p in pairs if p['baseline_in_band'] and p['paired_complete']]
        totals = {label: sum(p[label]['cost_usd'] for p in selected) for label in ['off', 'on']}
        diffs = [p['on']['cost_usd'] - p['off']['cost_usd'] for p in selected]
        output[model] = dict(all_task_pairs=pairs, band_complete_pairs=len(selected),
                            band_off_passes=sum(p['off']['success'] for p in selected),
                            band_on_passes=sum(p['on']['success'] for p in selected),
                            band_total_cost_usd=totals,
                            band_cost_change_fraction=totals['on']/totals['off']-1 if totals['off'] else None,
                            band_mean_cost_delta_usd=statistics.mean(diffs) if diffs else None,
                            band_cost_delta_empirical_bootstrap_95=interval(diffs),
                            limitation='A conditional description of this small selected sample, not an unbiased population estimate. A zero-width bootstrap at n=1 says nothing about uncertainty across tasks.')
    return output


def build(protocol):
    pr = json.loads(Path(protocol).read_text())
    records = [json.loads(p.read_text()) for p in sorted((LOCAL/'records').glob('*.json'))]
    records = [r for r in records if r.get('cohort_id') == pr['cohort_id']]
    result = dict(schema_version=1, cohort_id=pr['cohort_id'], minimum_usd=3, maximum_usd=15,
                  selection='Complete OFF baseline cost in [3,15], without inspecting ON cost or either correctness outcome. All fixed task pairs remain listed; no outcomes are dropped from the primary report.',
                  billing='Common dated API-equivalent estimates for Codex Pro execution, not API charges.',
                  models=summarize(records, pr['models']))
    dest = LOCAL/('report-'+pr['cohort_id']); dest.mkdir(exist_ok=True)
    (dest/'cost-band.json').write_text(json.dumps(result, indent=2)+'\n')
    lines = ['# Requested $3–15 baseline band', '', result['selection'], '', result['billing'], '',
             '| Model | Task | OFF $ | ON $ | OFF pass | ON pass | OFF in band |',
             '|---|---|---:|---:|---|---|---|']
    for model, data in result['models'].items():
        for pair in data['all_task_pairs']:
            off, on = pair['off'] or {}, pair['on'] or {}
            fmt = lambda value: 'pending/unknown' if value is None else f'{value:.4f}'
            lines.append(f"| {model} | {pair['task']} | {fmt(off.get('cost_usd'))} | {fmt(on.get('cost_usd'))} | {off.get('success')} | {on.get('success')} | {pair['baseline_in_band']} |")
    lines += ['', 'Reasoning tokens are a subset of output. Summary-model usage is included in total cost and separately itemized in token-breakdown.csv. Missing usage is unknown, never zero.', '',
              'Small samples do not establish equality or a population cost effect. The statistical unit is the task pair, not individual verifier checks. The primary report retains the entire fixed cohort.']
    (dest/'cost-band.md').write_text('\n'.join(lines)+'\n')
    return dest/'cost-band.json'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--protocol', required=True, type=Path)
    print(build(parser.parse_args().protocol))
