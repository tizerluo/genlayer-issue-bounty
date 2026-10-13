# Threat model

| Threat | Control | Remaining limitation |
| --- | --- | --- |
| GitHub login rename/reuse | Bind and verify numeric user id | GitHub account compromise transfers proof authority |
| Binding another wallet / stale proof | Exact contract/wallet/nonce marker, matching gist owner, nonce advances after every successful binding | Latest 100 public gists scanned; GitHub compromise permits fresh proofs |
| False PR claims | Default branch, independent merger, bound author, creation-to-deadline merge window and closing reference in merge commit message/PR title/PR body or SHA-matched closed event before LLM; optional trusted merger list | PR title/body are editable and fetched at claim time; empty list trusts any independent merger ID; allowed IDs can still collude; current default branch can change |
| Negated closing references | GitHub-compatible keyword matching links even `does not fix #1`; acceptance and payout require diff-only AI judgment and all other claim gates | Linking does not interpret negation or prove implementation; AI judgment remains fallible |
| Mutable external evidence | Creation snapshot, strict fact consensus, raw diff SHA-256 across blocks | GitHub edits may prevent consensus; patch-diff stability is not guaranteed |
| Prompt injection / PR edits | Exclude PR title/body from judgment; strip controls and Unicode separators, escape delimiter openings, JSON encode data; sponsor criteria remain inspection targets | Title/body closing references establish linking only; models may still be manipulated; consensus is not a security proof |
| Truncated diff | Only first 12,000 chars considered, flag truncation and treat missing evidence as unmet | Use small focused PRs; full downloads have no contract-side byte cap |
| Schema manipulation | Require complete unique ids, actual booleans after normalization, bounded integer score | LLM quality and scoring calibration require live measurement |
| Incorrect validator vote | Rerun LLM/diff, compare decision, scores ±2 and reject Hamming distance ≤1 | Test-only Sandbox adapter has different error conversion and lacks isolation; real committee tests remain unexecuted |
| Duplicate payout / premature withdrawal | Terminal bounty, awarded_at, seven-day aggregate credit hold, clear credit before transfer | Delay is local policy; appeal/reversal semantics remain unverified |
| External transfer failure | Caller-selected EOA via withdraw_to; synchronous errors trigger host transaction rollback; empty calldata; constructor-fixed treasury sweeps only balance above escrow+credits | Deferred child failures do not recreate claimant credits. Treasury reconciliation is manual; sweeps also emit asynchronous transfers. Verify failure, delivery, fees and appeal rollback on Bradbury before production funding |
| GitHub rate limit/outage | Minimal requests, User-Agent, fixed transient errors | Shared validator IP may exhaust unauthenticated 60/hour limits |
| Attempt bypass / LLM resampling | Counter per GitHub id/bounty across migration; persisted judged bounty/PR/diff keys | Multiple GitHub accounts remain possible; infrastructure/schema failures intentionally remain retriable |
| Invalid network, keys or cache poisoning | Chain 4221 before dedicated-keystore decryption; smoke/mock suites guard loopback localnet; user-owned private mode-0700 caches | Protect the keystore; never use mainnet or real funds |

Protocol fees are separate from the bounty value. Fee budgets must include external-message allocations when required. Depositing fees is not adding bounty funds. Do not mark settlement delivered from ACCEPTED status alone: check successful execution, finalization and the recipient's balance.

This is a testnet demonstration. Missing Studio, live LLM and Bradbury evidence are enumerated in progress.md and FINAL_REPORT.md. No portal scoring outcome is claimed.

Deployment identity uses separate package transaction/address/hash fields. The deployment tool submits the committed ZIP verbatim, rejects resumed transactions for other code, and verifies the raw on-chain code hash before marking success. The old minified deployment is superseded; the ZIP is not deployed. Semantic package verification checks runner, loader, stored entries and restored source without comparing compressor bytes.
