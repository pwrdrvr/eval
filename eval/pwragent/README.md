# Bounded real PwrAgent paired evaluation

This evaluator runs the actual PwrAgent Electron application and its managed
Codex App Server inside each task's isolated native arm64 container. It compares
exact `gpt-6.1-sol` and `gpt-6-astra`, high reasoning/default service, with Token
Miser OFF/ON. It does not emulate compression or compare against a published
leaderboard as a causal baseline.

The stage is preregistered in `preregistered-stage.json`: ten pinned public
Terminal-Bench 2.0/DeepSWE tasks, one replicate per model/flag, randomized within
task. This is a resource-feasible subset, not SWE-bench Verified. Original task
verifiers stay absent during agent execution. DeepSWE grades exported patches
in pristine containers. Every admitted attempt, including infrastructure and
model failures, is retained. No benchmark solution or task patch is published.

## Execution and evidence

`runtime-pins.json` records the production application source, eval driver PR,
managed release and exact hashes. The additive headless driver is PwrAgent
PR2707 at6062dd7. Build its production image following that PR's
`apps/desktop/eval/HEADLESS.md`, then overlay the pinned eval directory. Current
pilot payload is `fh-pwragent:8655446`. Source packages live under `.eval/cache`;
each task file is checked against the preregistration before dispatch. Local
paths in the preregistration identify this execution workspace and must be
relocated explicitly for reproduction; retain all content hashes and disclose
the resulting configuration hash.

The managed Linux release requires glibc2.39. Main tasks keep their original
base image and mount a separate readonly Ubuntu2.39 glibc tree. `patchelf0.18.0`
relocates only the managed siblings' ELF interpreter/RPATH; application code is
unchanged. Original release hashes and relocated hashes are both recorded.
The pilot used unrelocated binaries on Ubuntu24; each ON/OFF pair shares its
runtime. Readonly original Codex auth is mounted as uid501, with no copy or image
layer credential. The local Docker socket is never mounted into a task.

Run from this checkout after preparing pinned payloads/task packages:

```sh
python3 -m unittest discover -s eval/pwragent -p 'test_*.py'
python3 eval/pwragent/run_stage.py
python3 eval/pwragent/report.py --paused
```

`--limit N` admits only the first N preregistered cells. `--retry-infra N` is an
explicit, evidence-checked replacement of a settled zero-dispatch infrastructure
attempt; it creates a distinct ID and retains the original. It never retries a
model result. Completed records resume without dispatch. Ambiguous state fails
closed. The audited ledger includes all overhead and conservative reservations.

Outputs are local/ignored: `.eval/records/*.json`, `.eval/stage-ledger.sqlite`,
`.eval/stage-ledger.json`, `.eval/runs/*/output/{result,ready,thread}.json`, sanitized
`rollout.jsonl`/`protocol.jsonl`, original verifier records, and
`.eval/report/{interim.json,interim.md,records.jsonl}`. Costs distinguish the app's
historical pricing from a common dated official card and conservative admission
projection. Reasoning is an output subset; cache writes are an input subset.
Helpers and retrieval calls remain separate. A pending parent price row is only
reconciled with the matching completed event and exact provider counters.

## Budget and interpretation

The inclusive current stage ceiling is **$250**, including orchestration,
subscription API-equivalent usage, helper calls and retries. API credit billing
is not verified; subscription execution is not assigned zero economic cost.
There is $50 held orchestration allowance, serial concurrency, conservative
next-call reservations and per-task observed stops. Stops are post-request,
not provider billing caps; reservations cover in-flight uncertainty. Final stage
completion pauses further paid/subscription eval work for explicit user review.

Report paired pass@1, exact McNemar, task bootstrap cost intervals and cost per
resolved task. With zero discordant outcomes the empirical bootstrap can be
zero-width; the report also gives the finite-sample upper bound on discordance.
Small samples cannot establish population-level effects. An enabled flag with
zero interceptions is smoke evidence, not evidence of compression efficacy.
See `PROVENANCE.md` for instruction-protection fixes and historical auxiliary
work; standalone Codex Token Miser provenance remains unconfirmed.
