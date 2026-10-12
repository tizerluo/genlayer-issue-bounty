# PRD acceptance status — 2026-10-12

This audit includes the owner's Review rounds 1 and 3 security amendments, recorded in [PRD deviations](PRD_DEVIATIONS.md). FR-07 is updated; older PRD snippets are superseded by those amendments.

- [x] New independent public repository; not a fork or HelloCounter/template reuse.
- [x] One production gl.Contract subclass; pinned Depends header; original MUST interface plus five public additions (21 methods); fresh deployment required for revised constructor/storage.
- [x] ND-1 identity/proof split into two canonical callbacks for nonce capture; ND-2/3 canonical facts; ND-4 independent rerun and hash/decision/score/Hamming comparison.
- [x] Bounded/escaped prompts, numeric GitHub identity, custom User-Agent and conservative normalization.
- [x] Terminal states, authorized refunds, awarded_at and seven-day hold on both withdrawal methods, recipient selection, synchronous error propagation for host rollback, fixed-treasury surplus sweep, zero-before-send and independent modeled native-balance assertions.
- [x] Six SDK-supported events; Chinese code/test comments; English README.
- [x] Official lint, semantic validation and typecheck pass; 214 direct/unit/probe tests pass in source and package modes, with negative controls for the review findings.
- [x] Sanitized public diff, explicitly synthetic security fixture metadata, current ABI, and obsolete sandbox/gist evidence identified.
- [x] Strong dedicated encrypted CLI keystore outside repo, mode-0600 password, no old key variables read, testnet guards.
- [x] Public source committed frequently and pushed; architecture, consensus, threat model, usage, deployment scripts and final report included.
- [ ] Studio I-1–I-4 pass: Docker and Studio unavailable; tests skipped.
- [ ] Real OpenRouter smoke and score distribution: key absent; skipped.
- [ ] Reviewed ZIP deployed on Bradbury with matching code hash: package not deployed; legacy minified deployment is superseded.
- [ ] Fresh funded ZIP bounty, final external payment and protocol fee allocation: revised deployment and live execution remain unverified; legacy demo bounty is historical.
- [ ] GitHub Actions installed and green: workflow permission unavailable; updated source/package job definition delivered only at docs/ci.yml; preexisting workflow untouched.
- [ ] Owner portal submission/form verification: explicitly reserved to owner, no submission performed.
- [ ] Fresh eligible sandbox PRs: create bounty first, then independent default-branch merges with immutable closing evidence; replace old gist with nonce-scoped proof.
- [ ] Bradbury appeal rollback, irreversible message timing and deliberate failed-child experiment: delay/recipient selection do not establish recovery.

M0–M4 have local evidence. M5 is blocked; M6 is partially delivered. Runtime/security limitations are stated in THREAT_MODEL.md; all verification findings and exact blockers are in progress.md.
