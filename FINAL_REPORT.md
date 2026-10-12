# Final report — IssueBountyEscrow

Date: 2026-10-12. Testnet only. No builder portal submission.

| Deliverable | Result |
| --- | --- |
| Public repository | https://github.com/tizerluo/genlayer-issue-bounty — published, PUBLIC, `isFork: false` |
| Contract | `contracts/issue_bounty_escrow.py`, complete PRD MUST interface |
| Bradbury contract address | **Not deployed — blocked** |
| Bradbury contract explorer URL | **Unavailable until deployment**; expected `https://explorer-bradbury.genlayer.com/address/<verified contract address>` |
| Demo bounty id / transaction hash | **None — funded network demo blocked** |
| Dedicated public deployer | `0x8f374a83965b2143bea962a48c8dacaf0db62d16`; zero test GEN |
| Direct/unit/probe tests | **94 passed** |
| Lint / SDK validation | **Passed**; 16 public methods, six events |
| Pyright | **Passed — no type errors** |
| Studio / real LLM | **10 skipped**, prerequisite blockers below |
| GitHub Actions | **Publication blocked** — workflow prepared locally and in `docs/ci.yml`; CLI token lacks `workflow` scope, app write requires unavailable approval |

M0–M4 are implemented and verified locally. M5 was attempted and remains blocked. M6's public source, documentation, deployment scripts and evidence fixtures are delivered; CI publication, live deployment and payout are blocked. No address, receipt, real-model result or on-chain payment is fabricated.

Remaining blockers:

1. Official [GenLayer faucet](https://testnet-faucet.genlayer.foundation) requires GitHub sign-in and Cloudflare Turnstile. Owner must fund the public deployer with test GEN; the agent stopped this step as instructed.
2. Docker binary/socket and Studio RPC at localhost:4000 are absent. I-1–I-4 are implemented but unexecuted.
3. `OPENROUTER_API_KEY` is absent, so complete/partial real LLM smoke and consensus score distributions are unmeasured.
4. Stable CLI 0.39.2 lacks the estimator method; RC CLI 0.40.0-rc.3 reaches Bradbury FeeManager but `quoteGasPrice()` reverts. Compatible fee policy, measured profiles, external-message allocation and actual EOA delivery remain unverified.
5. PRD section 11 items 1 and 2 are **owner to verify at submission**. GenVM redirect behavior, on-network headers/array decoding, and failure recovery also remain live checks; the register in progress.md distinguishes verified facts from open items.
6. GitHub refused workflow-bearing pushes with the CLI OAuth token because it lacks `workflow` scope. The connected GitHub app is authenticated as `tizerluo`, but its create-file action was blocked: `MCP tool call requires approval, but approval policy is never`. Source was published with the ready CI definition at `docs/ci.yml`; no green CI result is claimed. Owner can grant workflow permission and install that definition as described in README.

Public demo evidence prepared:

- Sandbox: https://github.com/tizerluo/bounty-sandbox (independent public repo).
- Open issue: https://github.com/tizerluo/bounty-sandbox/issues/1.
- Complete merged PR: https://github.com/tizerluo/bounty-sandbox/pull/3.
- Partial merged PR: https://github.com/tizerluo/bounty-sandbox/pull/2.
- Deployer identity proof: https://gist.github.com/tizerluo/e6b1878333f2612ef1a822edbd1590b1.

New encrypted CLI keystore and mode-0600 password are outside the repo under `/home/box/.genlayer`. No secrets/private keys were printed, logged or committed; old wallet key variables were not inspected. Source uses separate git metadata at `/home/box/.genlayer/issue-bounty-git` because workspace `.git` is read-only. See progress.md for dated commands and milestones, and deployments/bradbury.json for the explicit blocked record.
