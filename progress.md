# Implementation progress

Owner approved `docs-PRD.md` on 2026-10-12. The explicit session decisions override its draft status: IssueBountyEscrow, public `tizerluo/genlayer-issue-bounty`, English README, OpenRouter, Bradbury only, a small test-GEN demo. No builder portal submission is authorized.

## Milestones

| Milestone | Status | Evidence |
| --- | --- | --- |
| M0 | In progress | Toolchain and SDK verification |
| M1–M6 | Pending | Execute in order |

## Session evidence — 2026-10-12

- Read approved PRD sections 3–12. Workspace starts with no commits and no implementation.
- `gh auth status`: authenticated as `tizerluo`; no credentials captured in artifacts.
- Python 3.13.5, Node v22.23.3, npm 10.9.9, uv available. `genlayer`, `gltest`, `docker` are not on PATH.
- Checked only presence of `OPENROUTER_API_KEY`: absent. Real LLM smoke will be skipped and reported as blocked; no key value was read or logged.
- Default npm cache is read-only. Tool installs will use `/tmp` caches and a repository-ignored tool prefix.
- Existing `/home/box/.genlayer/keystores/genlayer-testnet.json` will not be used. A new dedicated encrypted deployer will be created through the CLI.

## Section 11 verification register

| Item | Finding | Evidence / next action |
| --- | --- | --- |
| 1 | Owner to verify at submission | Portal form must confirm group AND / member OR. No submission performed. |
| 2 | Owner to verify at submission | Exact meaning of escalation threshold requires portal confirmation. |
| 3–14 | Pending | Toolchain, direct experiments, official source, network checks |
| 15 | Not applicable | Statuspage candidate C was not selected. |

## Safety constraints

Never inspect `OLD_WALLET_*_PK`. No mainnet or real-money actions. New encrypted keystore and password stay under `/home/box/.genlayer`, outside git; no private key export to logs. Faucet login/captcha stops that step. Public address and blockers may be recorded.

### M0 findings — 2026-10-12

- Installed CLI 0.39.2 in ignored `.tools`, genlayer-test 0.29.2, genvm-linter 0.11.0, genlayer-py 0.16.3 (0.29.2 pins `<0.17`), Python 3.12.15. Added missing cloudpickle dependency and froze all dependencies. SDK fetched from official GenVM v0.2.12 release.
- Item 4: official boilerplate still uses PRD hash `1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`. `python scripts/check.py check experiments/sdk_probe.py`: lint and semantic validation pass.
- Item 5: downloaded SDK `genlayer/gl/nondet/web.py` declares `Response.status`, `headers`, `body`. Contract will also accept `status_code` for compatibility.
- Item 6: SDK has `gl.Event.emit`; its constructor requires indexed positional arguments followed by `**blob`, rather than PRD's named non-indexed arguments. Verify production event emission in M4.
- Item 7: probe accepts `list[str]`; CLI `deploy --help` documents JSON array conversion. Calldata schema check passes. Actual CLI/RPC array decoding remains an integration check.
- Item 8: probe verifies `direct_vm.value = 123` reaches `gl.message.value`. `run_validator` captures strict_eq, but native 0.29.2 Sandbox handler returns an invalid result (`unknown type 14`). `tests/conftest.py` provides a narrowly scoped, non-isolated replay adapter; it executes the original callback and tests identical/different normalized facts. This is not full GenVM sandbox validation.
- Item 9: host HTTP observations confirm GitHub `.diff` redirects to patch-diff. GenVM redirect following cannot be verified without Studio/network execution; contract requests final patch-diff URL directly. Claims that patch-diff is exempt from API limits or permanently stable remain unverified.
- Item 10: SDK accepts and serializes custom `headers`; probe exercises custom User-Agent. Receipt on the actual GenVM network remains unverified.
- Item 11: gltest 0.29.2 startup lists built-in `testnet_bradbury`.
- Item 13: CLI 0.39.2 `write --help` has `--fee-value`, but no bounty `--value` option. Demo will use Python SDK.
- Item 3: `network info` confirms Bradbury RPC, chain 4221; `eth_chainId` returns `0x107d`. `estimate-fees --json` fails with `TypeError: client.estimateTransactionFees is not a function` in stable CLI. Protocol fee status is not inferred from this failure; investigate RC tooling in M6.
- Dedicated CLI-created encrypted keystore is `/home/box/.genlayer/keystores/issue-bounty-deployer.json`. Strong random password at `/home/box/.genlayer/deployer.pass`, mode 0600. Public address: `0x8f374a83965b2143bea962a48c8dacaf0db62d16`. `account show`: locked, active, Bradbury, balance 0 GEN.
- Official faucet https://testnet-faucet.genlayer.foundation frontend requires GitHub sign-in and Cloudflare Turnstile; stopped funding step. Owner must fund the address above with test GEN. No faucet bypass attempted.
- Commands: `.venv/bin/pytest tests/experiments -q`: **1 passed**. `python scripts/check.py` changes only cache paths under `/tmp`, because HOME is read-only; it runs the official linter.

M0 verification complete within available environment. M1 begins next; unresolved live checks remain explicitly listed.
