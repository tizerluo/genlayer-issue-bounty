# Consensus design and measurements

The contract makes settlement decisions in two stages. GitHub facts are deterministic after extraction; an LLM assessment requires independent judgment. The SDK dependency is pinned in the contract header.

| Block | Operations per node | Consensus payload | Principle |
| --- | --- | --- | --- |
| ND-1 binding | user + public gist list | numeric id, normalized login, exact marker found | canonical JSON strict equality |
| ND-2 creation | issue metadata | existence, issue kind, state, bounded title/body snapshot | canonical JSON strict equality |
| ND-3 claim facts | PR metadata + merged PR diff | author id, base repo, merge facts, reference, SHA-256 and character count | canonical JSON strict equality |
| ND-4 judge | same diff + LLM | criterion booleans, score, summary, SHA-256 | independent rerun with explicit comparison |

The ND-4 validator validates the leader schema, independently reads the diff, verifies its hash against ND-3, and calls the LLM. ACCEPT/REJECT must match exactly. Scores may differ by at most 2. When both reject, criterion booleans may differ at at most one position. ACCEPT implies every criterion is true on both sides. Summary wording is ignored. A score difference across the minimum threshold always causes disagreement even if within tolerance.

Business/external errors agree only if independently reproduced with the same message. Transient errors agree if the rerun also produces a transient error, ending the transaction without a claim or accounting mutation. LLM schema errors, VM errors and unknown errors always disagree. Successful reruns disagree with an errored leader.

`prompt_non_comparative` does not independently answer the settlement question. `prompt_comparative` would require another model judgment to compare results. Here code directly compares bounded decision fields. `strict_eq` is used only for processed GitHub facts, never raw LLM answers.

## Measured results — 2026-10-12

M3 direct tests: 80 passed; M4: 86 passed. The consensus matrix covers T-N1–N14: identical decisions, score tolerance, threshold crossings, criterion disagreements, reject Hamming bounds, hash mismatch, transient/LLM error votes, malformed and forged leader results, and strict fact disagreement. These are mocked callback measurements; there are no real-model score distributions yet.

Final M6 local suite: **94 passed**, including five deployment safety guards, a threshold-crossing score difference of only 1 (reject), the exact score tolerance boundary of 2 (agree), and the SDK probe's exact User-Agent wire assertion. Actual public sandbox diff is used with recorded SHA-256; account/repo/time fields are normalized for fixed direct-mode transaction time. GitHub Actions publication was blocked by unavailable workflow permission, so this result is local execution.

gltest 0.29.2's native Sandbox replay is incomplete. A test-only adapter executes the original sandbox callback and returns its SDK result. It does not provide VM isolation. Strict mocks and callback pickling checks remain enabled; the contract and its validator are not patched. Direct mode does not simulate committee finality, native transfers, or protocol fees.

Studio I-1–I-4 are implemented but blocked: Docker binary/socket absent and localhost:4000 unavailable. Real OpenRouter smoke (complete and partial PR, 3 runs each) is blocked because OPENROUTER_API_KEY is absent. No consensus rate or live result is claimed. Run the manual commands in README after providing those prerequisites; append actual receipts, outcomes and per-node scores here.
