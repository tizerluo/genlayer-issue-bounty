# Contract source and deployment notes

`contracts/issue_bounty_escrow.py` is the readable review source. The redeploy
candidate is `artifacts/issue_bounty_escrow.zip`, built from those exact UTF-8 bytes. Semantic checks support different zlib
implementations; the deployment manifest separately pins the exact shipped ZIP hash. Its manifest records both SHA-256 hashes and byte counts.
This is a fresh-deployment candidate; renamed storage fields do not migrate the
existing minified deployment.

## Packaging research

| Option | Finding | Decision |
| --- | --- | --- |
| Multi-file ZIP / runner | GenVM supports ZIP files, `runner.json`, `MapFile`, `Seq`, and pinned `Depends` actions. ZIP entries must use `stored` compression. | Use a stored ZIP with a compressed **inner data file** and a small Python loader. |
| ZIP entry compression | The pinned executor explicitly rejects compressed entries. Splitting readable files into a stored ZIP alone increases code bytes. | Every outer ZIP entry is stored, with a fixed timestamp and permissions. |
| Installed libraries / `Depends` | v0.2.12 resolves dependencies against the node's installed runner registry. Its internal `on_chain:` id does not expose arbitrary contract-source imports through `Depends`. | Keep the original pinned Python runner; no operator-installed custom dependency. |
| On-chain code runners | The newer specification documents `chain:` references to other contracts' code slots. That is not a feature to infer from the older pinned Python dependency hash. | Not needed for this candidate. |
| Separate library contract | Ordinary contract view calls exist; calls from within nondeterministic callbacks are forbidden. Moving judging into a separate child contract introduces another address and execution boundary. | The package saves gas while preserving one contract, its ABI and its consensus boundaries. |
| Python payload decompression | The pinned CPython build includes zlib. Loading a local compressed payload is deterministic and does not require an external service. | Verified with the actual v0.2.12 CPython/Wasm executor, not just host Python. |

Primary references:

- [GenLayer CLI deployment](https://docs.genlayer.com/developers/intelligent-contracts/deploying/cli-deployment)
  describes single-file CLI deployment; binary packages need a bytes-capable SDK.
- [GenVM runner specification](https://sdk.genlayer.com/v0.2.5/spec/02-execution-environment/04-runners.html)
  documents multi-file ZIPs, stored entries, mappings and initialization actions.
- [Pinned ZIP parser](https://github.com/genlayerlabs/genvm/blob/v0.2.12/executor/src/runners/ustar.rs)
  rejects compression methods other than `Stored`.
- [Pinned dependency resolver](https://github.com/genlayerlabs/genvm/blob/v0.2.12/executor/src/rt/supervisor/actions.rs)
  requires registered external runners; `<contract>` refers to the current package.
- [Pinned CPython dependencies](https://github.com/genlayerlabs/genvm/blob/v0.2.12/runners/cpython/deps/default.nix)
  includes zlib, with [its build](https://github.com/genlayerlabs/genvm/blob/v0.2.12/runners/cpython/default.nix).
- [Pinned contract-call implementation](https://github.com/genlayerlabs/genvm/blob/v0.2.12/executor/src/wasi/genlayer_sdk.rs)
  checks deterministic context for `CallContract`.
- [Current runner specification](https://sdk.genlayer.com/main/spec/02-execution-environment/04-runners.html)
  separately documents newer `chain:` and custom runners.
- [genlayer-py deployment implementation](https://github.com/genlayerlabs/genlayer-py/blob/main/genlayer_py/contracts/actions.py)
  accepts `str | bytes` and serializes the supplied code into the deployment payload.
  The installed 0.19.0rc2 implementation was also inspected locally.

## What is deployed

The stored ZIP contains three files:

1. `runner.json` maps `source.zlib` to the GenVM VFS and loads the same pinned
   `py-genlayer` runner used by the original contract.
2. `file` becomes `/contract.py`. Its readable loader decompresses the local
   payload, checks its exact length and SHA-256, then compiles and executes it
   in that module's globals.
3. `source.zlib` contains the complete readable source, compressed by zlib.

The standard SDK runner discovers the same `IssueBountyEscrow` class. Sandbox
and nondeterministic replay can import the same `contract` module again. The
loader reads only its mapped local file; it fetches no code from the network.
All bytes, including the loader and the checksum, are stored in the same
immutable deployment input. That bundled checksum only detects corruption; it
does not prove what a deployer sent. The external manifest and read-only RPC
code hash verification establish the link to the reviewed artifact. ZIP entry compression and Python decompression
are different stages: GenVM parses stored entries, then CPython reads the inner
payload after startup.

The loader uses `exec` solely to load the checksum-verified source bundled by
our build. It never executes GitHub text, model outputs, or user-supplied code.
The linter/typechecker validate the restored readable contract; the actual
GenVM probe validates the separate loader and package execution path.

Raw `.py` upload still exceeds the cap. Use the package bytes for redeployment.
`scripts/deploy_bradbury.py` reads `artifacts/issue_bounty_escrow.zip` verbatim,
checks its recorded hash and source semantics, checks resumed transaction code,
and hashes `gen_getContractCode` bytes after deployment before recording success.
Legacy deployment fields are never used for package resumption. Do not pass the ZIP through a CLI path
that decodes it as UTF-8 text. Source/explorer tools that assume UTF-8 contract
code need to extract `source.zlib`; the readable repository file and manifest
provide the review source directly. Portal acceptance of a binary deployment
was not tested and no portal submission was made.

## Review round 3 behavior

This is a fresh deployment with constructor `(claim_grace_seconds,
max_claims_per_claimant, treasury)`. The recorded candidate uses
`[259200, 3, "0x8f374a83965b2143bea962a48c8dacaf0db62d16"]`. The ABI now
has 21 methods (14 views, 7 writes), including `sweep_surplus`; six events remain.

- Identity proof requires the gist owner, contract, caller and per-GitHub-id nonce.
  Migration preserves numeric-id attempt limits and invalidates old proofs.
- Eligibility uses affirmative merge-commit lines (bullets, CRLF, comma lists)
  or issue closure events tied to the same merge SHA, the default branch,
  an independent merger, the author and the creation-to-deadline merge window.
  A sponsor's optional trusted merger list adds a membership check; empty
  means trusting any independent repository merger ID.
- The raw diff hash anchors independent leader/validator fetches and judgments.
  Threshold disagreement cannot be excused by score tolerance.
- Named prompt placeholders preserve sponsor-target boundaries and JSON data
  encoding. Controls and Unicode line/paragraph separators are filtered;
  potentially forged delimiter openings are escaped while code `<` survives.
  Summaries strip HTTP(S) URLs and still require frontend HTML escaping.
- Withdrawal clears credit before emission and preserves the seven-day hold.
  Synchronous errors propagate for whole-transaction rollback by the host;
  deferred child errors cannot be caught in the contract. The fixed treasury
  can sweep only positive native surplus above escrow plus outstanding credits.
  Sweeping does not recreate claimant credit or prove delivery. Confirm failed
  child receipts before treasury reconciliation or another sweep request.
- HTTP 406 for a diff is `[EXTERNAL] DIFF_TOO_LARGE`. The 12,000-character
  judgment bound still applies; completed judgments cannot be resampled.
  Repository dot segments and `.git` suffixes are rejected.

## Reproduce the candidate

```bash
.venv/bin/python scripts/build_contract_package.py
node scripts/estimate_deploy_gas.mjs
ISSUE_BOUNTY_TEST_PACKAGE=1 pytest tests/direct tests/experiments -q -W error::RuntimeWarning
```

The estimate script uses public addresses, SDK calldata/RLP/EVM encoding, and
curl. Its RPC allowlist contains only `eth_chainId` and `eth_estimateGas`; it has
no account creation, signing, key access or submission path. The measured gas
is EVM submission/storage gas, not a quote for future GenVM execution or LLM fees.

For actual Wasm verification, extract the official v0.2.12
`genvm-linux-amd64.tar.xz`, `genvm-linux-amd64-executor.tar.xz` and
`genvm-universal.tar.xz` into one runtime directory. Its layout must contain
`lib/libc.so`, `executor/v0.2.12/`, and `runners/`. Then run:

```bash
.network-venv/bin/python scripts/verify_contract_package.py --genvm-root /path/to/runtime
```

The probe executes the exact shipped ZIP for construction and SDK schema.
It separately checks source loading in real nondeterministic and sandbox child VMs
using a modified temporary package with an added test method. Its temporary callback probe is not in
the deployment package or public ABI. The local host stores no chain state and
uses no live provider. [Runtime evidence](../artifacts/package-runtime-validation.json)
records both shipped and modified probe hashes, and which checks use each.

See the package manifest, gas evidence, runtime probe evidence, and
[Review round 3](../progress.md#review-round-3) for
exact counts and checks. For preserved security rationale and remaining live
limitations, see [review round 1](../progress.md#review-round-1),
[consensus](CONSENSUS.md), and [threat model](THREAT_MODEL.md).
