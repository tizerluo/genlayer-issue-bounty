# Threat model

| Threat | Control | Remaining limitation |
| --- | --- | --- |
| GitHub login rename/reuse | Bind and verify numeric user id | GitHub account compromise transfers proof authority |
| Binding another wallet | Exact gist marker from user's own public gist list | Latest proof wins; only latest 100 public gists scanned |
| False PR claims | Check merged status, base repo, author id, merge deadline and issue reference before LLM | Maintainer merge is a trusted human gate, not proof of correctness |
| Mutable external evidence | Creation snapshot, strict fact consensus, raw diff SHA-256 across blocks | GitHub edits may prevent consensus; patch-diff stability is not guaranteed |
| Prompt injection | Bound inputs, escape closing tags (case-insensitive), explicit untrusted data, independent judge | Models may still be manipulated; consensus is not a security proof |
| Truncated diff | Only first 12,000 chars considered, flag truncation and treat missing evidence as unmet | Use small focused PRs; full downloads have no contract-side byte cap |
| Schema manipulation | Require complete unique ids, actual booleans after normalization, bounded integer score | LLM quality and scoring calibration require live measurement |
| Incorrect validator vote | Rerun LLM and diff, compare decision, scores ±2 and reject Hamming distance ≤1 | Direct tests replay callbacks without full VM isolation |
| Duplicate payout | Terminal bounty state, clear credit before external message | Finality/appeals and external-message execution are protocol dependencies |
| External transfer failure | Pull payment separated from judge, empty EOA transfer calldata | No automatic restoration or recovery method; a failed finalized child transfer can strand value. Verify fees and delivery on Bradbury before funding use |
| GitHub rate limit/outage | Minimal requests, User-Agent, fixed transient errors | Shared validator IP may exhaust unauthenticated 60/hour limits |
| Attempt-limit bypass | Limit per wallet/bounty | Github identity can migrate between wallets; not a Sybil prevention mechanism |
| Invalid network or key exposure | Deployment script verifies chain 4221 before decrypting dedicated keystore; passwords outside git | Build environment must protect its keystore; never use mainnet or real funds |

Protocol fees are separate from the bounty value. Fee budgets must include external-message allocations when required. Depositing fees is not adding bounty funds. Do not mark settlement delivered from ACCEPTED status alone: check successful execution, finalization and the recipient's balance.

This is a testnet demonstration. Missing Studio, live LLM and Bradbury evidence are enumerated in progress.md and FINAL_REPORT.md. No portal scoring outcome is claimed.
