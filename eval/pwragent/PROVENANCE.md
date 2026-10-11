This evaluation runs real PwrAgent Electron plus the managed Codex App Server
inside each isolated Linux task container. Both requested models use high
reasoning, default service tier, and fast mode off. Within a pair only the
explicit Token Miser flag changes. Raw credentials are excluded from build
contexts, logs, task trees, artifacts, and Git. The host auth file is mounted
read only, individually, into fresh Codex state; an expired login fails closed.

The historical FrontierHarness v1.0 results used Kimi K3, Terminal-Bench 2.1 and
DeepSWE. The Terminal-Bench 2.1 repository/registry could not be resolved on
2026-10-11. This study uses verified available Terminal-Bench 2.0 sources at
69671fbaac6d67a7ef0dfec016cc38a64ef7a77c plus pinned public DeepSWE task packages.
This is an explicitly different task/runtime/model configuration, with no
leaderboard comparability claimed. Correctness uses the original task verifier
after the agent ends; verifier/solution packages are hidden during the turn.
Native Linux arm64 execution on Apple Silicon differs from the historical
Linux amd64 runtime. Own matched on/off pairs are the causal comparison.

Recovered auxiliary repository: https://github.com/pwrdrvr/token-miser-evals
at e5b7d8f019df6b7dc35827aaad6b6c3f0e1dc5d1. It contains a historical M4 host
pilot, three controls and two Miser runs, on GPT-5.6-Sol/high. Its README reports
38.9% higher raw median cost with Miser and every cost cell disqualified by
degenerate tool output or missing interception telemetry. Tokens are absent
from that legacy cost cohort, so it cannot be repriced reliably. Twelve host
control calibrations have no paired treatment. These are historical auxiliary
evidence, not new Sol/Astra efficacy results. The current repo's documented
adapter drives PwrAgent; standalone Codex implementation provenance remains
under investigation and must not be inferred from this repo's name.

The user superseded the earlier $2500 authorization with a current-stage $250
ceiling and mandatory review pause. That cap applies to conservative
API-equivalent cost on the existing Codex subscription, including parent,
helper, retry and orchestration reserves. No new cloud compute is provisioned.
Outstanding/unknown dispatch usage retains its full reservation. Runs are
serial. No automatic paid retry or batch beyond this stage is authorized.
