# Final report — IssueBountyEscrow

Date: 2026-10-12. Review round 1. Testnet only. No builder portal submission.

All review findings **1–13** are addressed, with negative regression evidence mapped in [progress.md](progress.md#review-round-1) and specification changes in [PRD deviation notes](docs/PRD_DEVIATIONS.md).

| Deliverable | Result |
| --- | --- |
| Public repository | https://github.com/tizerluo/genlayer-issue-bounty — main, independent public repository |
| Claim eligibility | Creation-to-deadline merge window, default branch, independent merger and immutable merge-commit issue reference; editable PR title/body excluded |
| Retry protection | Attempts per bounty/GitHub id across wallet migration; repeated judged PR/diff rejected before another LLM call |
| Identity proof | Contract/wallet/nonce-scoped gist, verified owner, nonce advanced after successful binding |
| Prompt | Escaped angles, controls removed, JSON encoded data, sponsor acceptance targets restored |
| Payout | awarded_at, seven-day hold, withdraw_to, caller-owned credit, synchronous emission restoration; deferred failures remain unverified |
| Direct/unit/probe tests | **147 passed**, including negative cases for every finding and native-balance mismatch detection |
| Lint / SDK validation | **Passed**; 20 public methods, six events; ABI regenerated |
| Typecheck | **Passed — no type errors** |
| Studio / real LLM | **11 skipped**; local runtime unavailable; I-4 reference disagreement added |
| Tooling | Private checked caches, password newline handling, receipt-derived demo id, localnet-only smoke guards |
| GitHub Actions | docs/ci.yml updated with SDK pin, lint, tests and typecheck; no .github/workflows addition, no hosted run claimed |
| Bradbury address / explorer / funded demo | **Not deployed — no address, demo id or network transactions** |
| Dedicated public deployer | `0x8f374a83965b2143bea962a48c8dacaf0db62d16`; prior preflight found zero test GEN |

M0–M4 have local implementation evidence. M5 and live M6 remain blocked. Review fixes do not establish real committee behavior, protocol finality or successful native transfer delivery.

Remaining blockers and limits:

1. Official faucet GitHub sign-in / Turnstile and zero deployer funding block deployment. Docker/Studio are unavailable; OpenRouter smoke prerequisites remain absent.
2. Existing fee tooling is incompatible with the observed Bradbury FeeManager. Measured fee profiles, external-message allocation and final delivery still require live verification.
3. The seven-day delay is a local contract policy, **not a verified Bradbury appeal window**. Award reversal, rollback of dependent withdrawals and irreversible message timing are unverified. A later failed child transfer cannot be caught or recovered by this contract; withdraw_to helps choose a compatible EOA but cannot recover an already emitted transfer. Before production funding, run a deliberate failed-child transfer and appeal/reversal experiment on Bradbury and inspect receipts/balances.
4. T-N9–T-N12 and other direct replay tests use a custom same-process spawn_sandbox adapter. Its exception conversion and isolation differ from GenVM. Payout balances are independently modeled in tests, not moved by an actual child transfer. README documents both limitations; Studio I-4 must supplement callback-level evidence.
5. Historical sandbox PRs #2/#3 predate any new bounty and are obsolete evidence. The address-only gist is also obsolete. A valid demo creates its bounty first, publishes a fresh contract/wallet/current-nonce proof and uses new PRs independently merged into the default branch with immutable closing lines before the deadline. The manifest records this requirement; no replacement eligible network demo is claimed.
6. The demo derives its bounty id from the recorded creation execution receipt and repairs stale guessed ids. If v0.6 omits execution bytes, it retains the transaction hash and stops until a full verifiable receipt is available. It never chooses an id from the global bounty count.
7. Hosted CI remains unavailable because the token lacks workflow scope. Only docs/ci.yml is updated; the preexisting untracked workflow is excluded. PRD portal-form items remain reserved to the owner; no submission was performed.

All review work uses `/home/box/.genlayer/issue-bounty-git` as GIT_DIR because workspace .git is read-only. Dedicated encrypted keystore/password stay outside the repository. No secrets were printed or committed, no OLD_WALLET variables were read, and no mainnet or portal action was taken.
