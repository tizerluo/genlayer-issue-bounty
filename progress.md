# Implementation progress

Owner approved `docs-PRD.md` on 2026-10-12. The explicit session decisions override its draft status: IssueBountyEscrow, public `tizerluo/genlayer-issue-bounty`, English README, OpenRouter, Bradbury only, a small test-GEN demo. No builder portal submission is authorized.

## Milestones

| Milestone | Status | Evidence |
| --- | --- | --- |
| M0 | Complete within available environment | Pinned SDK, probe, tools and section 11 register |
| M1 | Complete | Skeleton/views; lint and direct tests |
| M2 | Complete | GitHub binding and payable creation tests |
| M3 | Complete | Claims, independent judge, T-N1–N14 |
| M4 | Complete | Refund/withdraw/events and accounting tests |
| M5 | Attempted; blocked | 10 Studio/live cases skipped, no Docker/Studio/key |
| M6 | Partial delivery; blocked live steps | Public source and evidence published; CI permission, faucet and fee policy unresolved |

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
| 1 | owner to verify at submission | Portal form must confirm group AND / member OR. No submission performed. |
| 2 | owner to verify at submission | Exact meaning of escalation threshold requires portal confirmation. |
| 3 | Partially verified; fees/version unresolved | Bradbury chain 4221 confirmed by network info and eth_chainId. Stable estimator missing; RC quoteGasPrice reverts. RPC probe: FeeManager code 1159 bytes, GENPerTimeUnit/storageUnitPrice both zero; this does not establish gasless deployment or protocol version. artifacts/network-probe.json. |
| 4 | Verified official source + SDK | PRD Depends hash still in official boilerplate; pinned GenVM v0.2.12 probe passes lint/validation. |
| 5 | Verified SDK/direct | Response.status is the actual field; compatibility fallback status_code retained. |
| 6 | Verified lint/direct emission | gl.Event supported; non-indexed fields require **blob. Six events pass lint/typecheck and emitted request inspection. Live receipt remains unverified. |
| 7 | Partially verified | list[str] roundtrips through actual calldata in direct mode and ABI. CLI help supports JSON arrays; live CLI/GenVM decoding remains blocked. |
| 8 | Verified with documented harness limits | direct_vm.value carries payable value. Native strict_eq Sandbox replay is incomplete; test-only original-callback adapter verifies positive/negative votes. |
| 9 | Host verified; GenVM/quota unverified | Sandbox PR 3 .diff returns 302 to patch-diff; final URL 200 text/plain. SHA-256 matches captured fixture. GenVM redirect following and API quota exemption remain unverified; final URL avoids redirects. |
| 10 | SDK wire verified; live header receipt unverified | M0 probe intercepts WebRequest and asserts User-Agent bytes. SDK serializes custom headers. |
| 11 | Verified | gltest 0.29.2 built-in testnet_bradbury appears at startup; RPC and chain also in SDK. |
| 12 | Unverified on Bradbury | SDK EthSend transfer request, zero-before-send and accounting verified directly. RC fee estimation currently incompatible; messageAllocations and failed-child behavior require network test. No automatic restoration exists in this contract. |
| 13 | Verified CLI help | Stable 0.39.2 and RC 0.40.0-rc.3 write expose fee-value but no bounty value option; Python SDK has value. |
| 14 | Verified official configuration; execution blocked | Settings → Inference Providers; openrouter/openai-compatible plugin, api_key_env_var OPENROUTERAPIKEY, api_url https://openrouter.ai/api. Bridge owner OPENROUTER_API_KEY into backend process environment; key absent and Studio unavailable. docs/STUDIO.md. |
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

### M1 — 2026-10-12

- Implemented typed storage/dataclasses, constructor, all 11 read methods, criteria validation, conservative schema normalization and shared deterministic decision function.
- `python scripts/check.py check contracts/issue_bounty_escrow.py --json`: lint and SDK semantic validation pass (11 views). `pytest tests/direct tests/experiments -q`: recorded below.
- Workspace `.git` is mounted read-only (`index.lock: Read-only file system`). To honor frequent commits, separate durable git metadata is `/home/box/.genlayer/issue-bounty-git`, with worktree unchanged at `/workspace/genlayer-issue-bounty`. Use `GIT_DIR=/home/box/.genlayer/issue-bounty-git GIT_WORK_TREE=/workspace/genlayer-issue-bounty` for git/gh commands. No permission escalation needed.
- M1 initial suite exposed cache-dependent SDK cleanup in gltest 0.29.2: the cache path must include `gltest-direct`. Fixed the cache path without changing SDK behavior. Final M1 suite: 13 passed (12 direct + 1 probe).

### M2 — 2026-10-12

- ND-1 verifies an exact gist marker and implements latest-proof identity migration in both directions. ND-2 freezes bounded normalized issue fields, validates all inputs before any HTTP call, and stores payable reward.
- `python scripts/check.py check contracts/issue_bounty_escrow.py --json`: pass, 13 public methods.
- `pytest tests/direct -q`: **36 passed**. T-B1–B6 and T-C1–C6 covered, including HTTP failures, identity migration, reward 0/123, snapshot bounds, invalid arguments and exact deadline boundary.

### M3 — 2026-10-12

- Implemented ND-3 ordered fact gate and ND-4 independent LLM judge/validator. Diff SHA-256 is over the raw bytes both times. All captures are plain values; strict pickling checks are enabled. Missing/truncated evidence is conservative, closing tags escaped, schema rejects duplicate ids, boolean scores and ambiguous results.
- Objective failures produce REJECTED claims without LLM use. Transient/schema failures occur before any claim/counter/accounting mutation.
- `python scripts/check.py check contracts/issue_bounty_escrow.py --json`: pass (14 methods). `pytest tests/direct -q`: **80 passed**.
- T-N1–N14 exercised, including forged ACCEPT, threshold disagreement, score tolerance, reject Hamming tolerance, changed diff, transient/external/LLM error voting and strict_eq disagreement. Error replay uses an Exception with the exact wire message because native `run_validator(leader_error=UserError(...))` wraps its repr instead of `.message` in 0.29.2.

### M4 — 2026-10-12

- Implemented creator-only refund strictly after deadline + grace, single-use credit withdrawal, and six events using supported `**blob` constructors.
- Direct payout tests inspect the actual SDK `EthSend` request (recipient, 123 wei, empty calldata) and assert credit is already zero and withdrawn total updated at emission. Event requests are observed through the harness hook.
- `python scripts/check.py check contracts/issue_bounty_escrow.py --json`: pass, 16 public methods. `pytest tests/direct -q`: **86 passed**. Accounting sequence conserves 579 wei through rejection/award/refund/withdraw.
- Item 6 verified at SDK/lint/direct request level; Bradbury event receipt still blocked. Direct mode does not move native balances or execute emitted transfers. `total_withdrawn` measures requested transfers; confirmed EOA delivery remains a finalization check.

### M5 — 2026-10-12

- Added manual Studio tests I-1 payment flow, I-2 fact rejection, I-3 refund, I-4 split committee, plus complete/partial real LLM smoke repeated three times. Results require both accepted/finalized status and successful execution; a negative-case timeout is not counted as success.
- `command -v docker`, Docker socket paths: absent. `curl --max-time 3 http://127.0.0.1:4000/api`: connection refused. Studio cannot start in this environment; no Docker daemon installed or privileged escalation attempted.
- `ISSUE_BOUNTY_STUDIO_TESTS=1 .venv/bin/gltest tests/integration -v --network localnet`: **10 skipped**, with explicit missing-Studio prerequisite. Real smoke also lacks OPENROUTER_API_KEY. This is blocked execution, not a passed M5.
- Removed unbound private-key interpolation from shared gltest config: 0.29.2 eagerly resolves all networks and otherwise blocks even direct/local tests. Deployment scripts will decrypt only the dedicated keystore in memory.
- `docs/CONSENSUS.md` records mocked consensus observations and explicitly leaves live-model distributions unmeasured.
- Item 14: official Studio Providers docs (https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/providers) specify Settings → Inference Providers → New Config → provider/model/plugin/default validator config. CLI 0.39.2 `init --help` provides `--headless --numValidators --localnet-version`, but no OpenRouter key flag. Verify exact OpenRouter plugin fields from Studio source in M6; do not write secrets into repo/env.

M5 attempted; runtime and real LLM validation remain blocked. Proceeding to M6 independent deliverables.

### M6 — 2026-10-12

- Added English README, MIT license, architecture/consensus/threat/Studio docs, ABI, isolated network SDK dependencies and resumable deploy/demo scripts. Demo amount is 0.0001 test GEN, capped at 0.001; chain identity and funding checked before decrypting/signing. Tests cover wrong chain, zero balance and reward caps.
- Stable CLI 0.39.2 estimate failed due to missing SDK function. Explicitly installed CLI 0.40.0-rc.3 and isolated genlayer-py 0.19.0rc2, per official v0.6 release-family documentation. RC `estimate-fees --json` fails at `quoteGasPrice()` for FeeManager 0xF205868bf5db79d2162843742D18D0900A9E462a. Read-only RPC observations stored in artifacts/network-probe.json: code 1159 bytes, GENPerTimeUnit and storageUnitPrice zero, quoteGasPrice/messageFeeParamsBudgetFloor reverted. Current consensus version and usable fee policy remain unresolved.
- Default Python requests UA received RPC HTTP 403 Cloudflare HTML. Curl requests succeeded; the deployment preflight uses curl for public RPC. No faucet challenge was bypassed.
- `bash scripts/deploy_bradbury.sh --preflight`: Bradbury address `0x8f374a83965b2143bea962a48c8dacaf0db62d16`, balance 0 wei; no signing/deployment transaction. deployments/bradbury.json explicitly records status blocked, address null, no demo_txs.
- Created independent PUBLIC evidence sandbox https://github.com/tizerluo/bounty-sandbox. Issue #1 is OPEN; partial PR #2 and complete PR #3 merged. Reopened issue after fixture merges. Created exact public deployer gist https://gist.github.com/tizerluo/e6b1878333f2612ef1a822edbd1590b1. deployments/sandbox.json records public selectors.
- `python scripts/make_fixtures.py`: fetched public user/issue/merged PR/diff and saved sanitized fixtures used by tests. Normalized account/repo/numbers/time documented in provenance.json; raw diff retained. `curl` of github.com/tizerluo/bounty-sandbox/pull/3.diff returns 302 to patch-diff, final URL returns 200 text/plain. Both retrieved and fixture hashes: b54015422fd6089164383ba0efa5b8043067ab08986aa2375e07b2a9fce3de79.
- Workflow ready at .github/workflows/ci.yml locally, but first push was rejected by GitHub because CLI OAuth token lacks workflow scope. Read-only connected-app login confirmed tizerluo; its create-file write was blocked with `MCP tool call requires approval, but approval policy is never`. Did not retry that restricted write through another surface. Published source with identical prepared workflow at docs/ci.yml. Owner must grant workflow permission/install it; no workflow run or green CI is claimed.
- `gh repo create tizerluo/genlayer-issue-bounty --public --source . --push` was attempted in workspace; gh does not recognize separate GIT_DIR. Retried from a clean temporary clone of the same local commits. Repo creation succeeded; after the workflow-bearing push rejection, replaced only the unpublished last commit with a source-only version. Public push then succeeded. Separate workspace metadata now follows public main; local ci-ready branch preserves the full workflow snapshot. Workspace source and ready local workflow remain in the requested directory.
- `gh repo view ... --json url,isFork,visibility,defaultBranchRef`: PUBLIC, isFork false, main. `gh run list`: empty (blocked workflow publication).
- Final local verification: `pytest tests/direct tests/experiments -q`: **92 passed** (91 direct/unit + 1 probe); `python scripts/check.py check ... --json`: lint and semantic validation pass, 16 public methods; `PATH=<venv>/bin:$PATH python scripts/check.py typecheck ...`: **no type errors**. Integration suite: **10 skipped**, no real LLM or committee result.
- Re-fetched official portal contribution-types/52 API (read-only): multiplier 50.0, weekly limit 2, AI review true, escalation threshold 400, evidence groups [[studio-contract,github-repo],[genlayer-explorer-contract]]. Items 1/2 still owner to verify at submission. No submission made.
- Security review of tracked files: no env/password/keystore/private-key file paths staged. Dependencies/tools/caches and encrypted keystore stay outside the public tracked tree. Final report states absent address/demo evidence and remaining blockers explicitly.
- Final targeted consensus additions isolate the security boundary: score 7 vs 6 must disagree despite difference 1; score 9 vs 7 may agree at tolerance 2 when both ACCEPT. Final suite: **94 passed**; lint/semantic validation and typecheck remain passed. Integration rerun: **10 skipped** with missing Studio prerequisite. No broader live results claimed.
- Raw unified diff contains a required space-only context line. `.gitattributes` exempts raw diff fixtures from whitespace checking rather than changing their hash-anchored bytes. Conventional key/env formats additionally ignored. Credential pattern scan covered 54 tracked files before final documentation update, with zero candidate files; no secret values emitted by the scan.

## Review round 1

2026-10-12: owner requested all findings 1–13 from `/workspace/genlayer-ic/review.md` (Cursor Agent / claude-opus-5-5-high). This section supersedes earlier implementation statements about wallet-keyed limits, editable references, address-only proofs, immediate withdrawal and eligible sandbox evidence. [PRD deviation notes](docs/PRD_DEVIATIONS.md) record each changed requirement; FR-07 is amended in the PRD. No workflow publication, portal submission, mainnet action or inspection of old wallet variables is performed.

| Finding | Fix | Negative test / evidence |
| --- | --- | --- |
| 1 HIGH: pre-bounty merge | Gate requires created_at ≤ merged_at ≤ deadline. Old sandbox PRs are marked obsolete; demo creates a bounty before accepting fresh independent merge evidence. | `test_gate[MERGED_BEFORE_BOUNTY]` rejects precreation timestamp without LLM; `test_merge_at_creation_boundary` preserves the inclusive boundary. |
| 2 HIGH: editable PR reference/injection | Issue association uses the merge commit message fetched by immutable SHA and verified against the response SHA. PR title/body are absent from facts/prompt. | `test_mutable_reference_cannot_replace_commit_evidence`, `test_pr_text_excluded_from_judgment`, `test_merge_commit_hash_mismatch`. |
| 3 HIGH: self/side-branch merge | Extract base.ref, default_branch, merged_by.id. Reject non-default branch, missing/invalid merger and merger equal to author. | `test_gate` includes NOT_DEFAULT_BRANCH, SELF_MERGED and MERGER_NOT_VERIFIED; strict mocks prove no LLM use. |
| 4 HIGH: wallet migration/resampling | Attempts keyed by bounty/GitHub id; completed bounty/PR/diff judgments persisted. Duplicate rejected diff reverts ALREADY_JUDGED before another LLM call or count/claim update. | `test_wallet_migration_preserves_limit`, `test_rejected_diff_cannot_be_rejudged_after_migration`; `test_changed_diff_and_other_bounty_are_distinct` checks key scope. |
| 5 MEDIUM: prompt escaping | Remove Unicode controls/format characters; escape ampersands and all angle brackets; JSON encode data so forged rules/JSON cannot form new template lines. | `test_prompt_injection_stays_encoded_data` covers spaced/hyphenated/zero-width closing tags, bidi/control characters, forged SECURITY RULES and JSON; `test_truncated_and_escaped` exercises the claim path. |
| 6 MEDIUM: replayable gist | Marker includes contract, wallet and current per-id nonce; every successful bind increments nonce. Identity consensus precedes deterministic nonce capture and independent proof consensus. | `test_old_gist_cannot_reclaim_migrated_identity`, `test_proof_is_bound_to_contract`; failed proofs do not advance nonce. |
| 7 MEDIUM: negation/bare link | Only standalone affirmative closing-keyword lines in immutable merge commits count. Editable PR text is never reference evidence. | `test_mutable_reference_cannot_replace_commit_evidence` rejects Doesn't fix, does not resolve, bare URL, wrong number and wrong repository. |
| 8 MEDIUM: finality/recipient/failure | Bounty awarded_at and seven-day FINALITY_DELAY; aggregate per-wallet credit hold shared by withdraw/withdraw_to; caller-selected destination; restore synchronous emission failure. Document actual appeals, dependent rollback and deferred child failure as unverified; no recovery claim. | `test_award_cannot_withdraw_before_finality` covers both methods at delay−1; `test_withdraw_to_uses_callers_credit` rejects credit theft and inspects destination; invalid recipient tests; `test_new_award_cannot_shorten_existing_credit_hold`; `test_synchronous_emit_error_rolls_back_credit`; simulated stranded-transfer negative control. |
| 9 MEDIUM: missing attack/accounting tests | Add regressions for every finding. Model native deposits from input values and outgoing balances from actual EthSend amounts, independently of the contract ledger; assert contract_balance as well as totals throughout payout sequence. | Claim/binding/prompt attacks above; `test_sequence_accounting` and `test_accounting_detects_simulated_stranded_transfer` fail on native balance/accounting discrepancy. The model is disclosed, not presented as real transfer execution. |
| 10 LOW: criteria treated as untrusted instructions | Sponsor inspection targets are JSON data under acceptance_criteria; instructions state their evaluation role and prohibit overriding security/schema. | `test_criteria_are_inspection_targets` rejects the old untrusted_criteria block and verifies numbered targets; injected closing-target tags are covered by finding 5. |
| 11 LOW: gist owner | Require owner numeric id exactly equal to user id, with integer type validation. | `test_gist_owner_must_match_user` rejects wrong, boolean and string ids; leaves binding/nonce unchanged. |
| 12 LOW: custom Sandbox adapter | README explicitly names T-N9–T-N12, same-process replay, non-equivalent exception conversion/isolation and weaker evidence. Add real Studio I-4 immutable-reference disagreement alongside decision split. | `test_validator_vm_error_cannot_approve` rejects a callback VM failure but does not claim native GenVM equivalence. `test_I4_reference_disagreement` is added; Studio execution remains skipped/blocked. |
| 13 LOW: tooling/key handling | Strip only trailing password newlines; private owner/mode/symlink-checked caches; SDK explicitly pinned; bounty id decoded from recorded creation receipt, including resumption; live/mock suites guard loopback localnet before writes. Keep docs/ci.yml aligned with lint/tests/typecheck. | `test_signer_trims_only_trailing_newlines`, `test_password_permissions_rejected_before_decryption`, cache attack tests, `test_missing_or_non_integer_creation_id_is_not_guessed`, `test_concurrent_demo_uses_creation_receipt_and_repairs_stale_id`, `test_live_smoke_guard_refuses_network_before_deploy`. |

Implementation and verification notes:

- ND-1 now has two sequential strict calls, allowing storage nonce selection only after numeric-id consensus. All callback captures remain plain values; closure pickling checks pass. ND-3 adds one GitHub request for immutable merge commit evidence; ND-4 consumes no editable PR title/body.
- The helper's duplicate web registrations previously retained the first response. Replaced matching URL mocks rather than appending, so hash-mismatch/truncation/changed-diff tests use the intended response. SDK release v0.2.12 is explicitly selected, avoiding unreliable latest resolution when moving away from old shared caches. Downloaded the pinned release fresh from its official URL into a new owner-only cache; no old shared cached code was copied.
- Seven days is a conservative application hold, not a measured Bradbury appeal window. Positive awards extend the hold for aggregate wallet credit, including existing refunds/mature awards. Refund-only credit is available immediately. Synchronous emission restoration is unit tested; async failed-child recovery and award/withdrawal rollback after appeal require a Bradbury experiment and remain unverified.
- Native balance assertions use a disclosed independent test model because direct mode does not execute native transfers. A simulated deferred failure preserves native value after bookkeeping says withdrawn, and the strengthened conservation check correctly fails. No live successful/failed transfer is claimed.
- Historical sandbox PRs #2/#3 and the old gist cannot satisfy revised eligibility. Manifest explicitly invalidates them. The demo persists the creation transaction and decodes its returned id, pauses for fresh postcreation independent default-branch PRs, and waits for actual credit maturity. If a v0.6 receipt omits execution bytes, it retains the hash and stops for a full receipt instead of guessing. Funding/fee/deployment blockers prevent a new valid network demo here.
- Live smoke now requires six distinct precreated bounties and fresh complete/partial PRs; it cannot use historical merges or resample one rejected diff. Tests only allow localnet/loopback; Bradbury is exercised exclusively through its guarded deployment/demo tooling when prerequisites are met.
- Final validation: `ISSUE_BOUNTY_CACHE_DIR=/home/box/.genlayer/issue-bounty-cache .venv/bin/pytest tests/direct tests/experiments -q`: **147 passed**. Official `check ... --json`: **passed**, 20 public methods (14 views, 6 writes), six events. `typecheck`: **no type errors**. Regenerated `artifacts/abi.json` with the official schema command.
- `ISSUE_BOUNTY_STUDIO_TESTS=1 .venv/bin/gltest tests/integration -q --network localnet`: **11 skipped**, local Studio unavailable. No native sandbox/committee, real-model or protocol-finality validation is claimed. Existing README limitation expanded as specifically requested for finding 12.
- CI definition updated only at `docs/ci.yml` with pinned GenVM and typecheck. The preexisting untracked `.github/` is excluded from the commit; no workflow-scope write is attempted. Review source/docs use external Git metadata and are committed/pushed to main after final checks.
