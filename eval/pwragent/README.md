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

The separately approved harder cohort is `preregistered-hard-httpx.json`: only
four HTTPX multipart task cells, both exact models OFF/ON,2million inclusive
tokens, cumulative$500 ceiling including all earlier charges/holds. Its protocol
hash alone is authorized through the review gate; the original stage remains
paused. The runner always stops after those four cells and restores the pause.
Reports filter by cohort, so this amendment is not silently pooled with stage1.

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

Review found the original6062 Playwright launch silently added `--no-sandbox`.
The prior sandbox claim was incorrect and is retained as a stage1 limitation.
The harder cohort pins driver2c7d84b with explicit `chromiumSandbox:true` and
uses the [official Playwright1.63 seccomp profile](https://github.com/microsoft/playwright/blob/v1.63.0/utils/docker/seccomp_profile.json)
for scoped clone/setns/unshare namespace permissions. It uses no SYS_ADMIN,
unconfined policy or root Electron. Actual native HTTPX zero-turn preflights
passed; driver DEBUG argv and live process UID/seccomp evidence are retained.

Admission is subscription-only: the approved auth must be ChatGPT account auth
with no API-key value, and the container rejects API-key or endpoint override
environment variables before launching the agent. Actual account/read receipts
identified ChatGPT Pro for every prior task. Managed provider source selects
chatgpt.com/backend-api/codex in this mode; parent App Server replies resolve
default tier, helper usage resolves standard, and fast mode is disabled.
These prove runtime route/settings, not an upstream billing invoice.

Run from this checkout after preparing pinned payloads/task packages:

```sh
python3 -m unittest discover -s eval/pwragent -p 'test_*.py'
python3 eval/pwragent/run_stage.py
python3 eval/pwragent/reconcile_records.py  # offline, after dispatch process stops
python3 eval/pwragent/report.py --paused
# The exact separately approved protocol; the gate rejects any other hash:
python3 eval/pwragent/run_stage.py --protocol eval/pwragent/preregistered-hard-httpx.json
python3 eval/pwragent/report.py --protocol eval/pwragent/preregistered-hard-httpx.json --paused
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
There is $65 held orchestration allowance, serial concurrency, conservative
next-call reservations and per-task observed stops. Stops are post-request,
not provider billing caps; reservations cover in-flight uncertainty. Final stage
completion pauses further paid/subscription eval work for explicit user review.

Report paired pass@1, exact McNemar, task bootstrap cost intervals and cost per
resolved task. With zero discordant outcomes the empirical bootstrap can be
zero-width; the report also gives the finite-sample upper bound on discordance.
Financial pairs retain infrastructure-invalid grades, with separate counts from
valid score pairs. Reported cancellation costs are partial snapshots; their
full reservations remain charged. `.eval/PAUSED_FOR_REVIEW.json` blocks every
dispatch before ledger admission, and requires explicit user review approval
before an operator clears it. The current stage also reserves $8.605102 for
separately audited Jarvis eval-only overhead; unrelated root history is excluded.
Root verifiers trust Git repositories only inside their isolated task container.
Small samples cannot establish population-level effects. An enabled flag with
zero interceptions is smoke evidence, not evidence of compression efficacy.
See `PROVENANCE.md` for instruction-protection fixes and historical auxiliary
work; standalone Codex Token Miser provenance remains unconfirmed.

Validation on the current checkout and untouched base e837a70: existing Node
suite33/40 passes in both, with the same seven historical report/skill failures.
The separate evaluator suite passes10/10. Protected instruction cases pass7/7.
