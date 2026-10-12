# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
import typing

PROMPT_VERSION = "BOUNTY_JUDGE_V1"
GITHUB_UA = "genlayer-issue-bounty-escrow"
BIND_PREFIX = "genlayer-bounty-bind:"
MAX_CRITERIA = 5
MAX_CRITERION_CHARS = 200
MAX_ISSUE_TITLE_CHARS = 200
MAX_ISSUE_SNAPSHOT_CHARS = 2000
MAX_PR_TITLE_CHARS = 200
MAX_PR_BODY_CHARS = 3000
MAX_DIFF_CHARS_FOR_LLM = 12000
MAX_SUMMARY_CHARS = 400
SCORE_MIN, SCORE_MAX = 0, 10
SCORE_TOLERANCE = 2
REJECT_HAMMING_TOLERANCE = 1
MIN_DEADLINE_DELAY = 3600
MAX_DEADLINE_WINDOW = 180 * 24 * 3600
MAX_PAGE_SIZE = 50
ZERO_ADDRESS = "0x" + "0" * 40
U64_MAX = (1 << 64) - 1


def _error(code: str, prefix: str = "EXPECTED") -> typing.NoReturn:
    raise gl.vm.UserError(f"[{prefix}] {code}")


def _now() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _canonical(obj: typing.Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def _positive_id(value: int, code: str) -> None:
    if type(value) is not int or not 0 < value <= U64_MAX:
        _error(code)


def _criteria(values: list[str]) -> list[str]:
    if not isinstance(values, list) or not 1 <= len(values) <= MAX_CRITERIA:
        _error("INVALID_CRITERIA")
    if any(not isinstance(v, str) for v in values):
        _error("INVALID_CRITERIA")
    clean = [v.strip() for v in values]
    if any(not v or len(v) > MAX_CRITERION_CHARS for v in clean) or len(set(clean)) != len(clean):
        _error("INVALID_CRITERIA")
    return clean


def _decide(verdict: dict, min_score: int) -> str:
    return "ACCEPT" if all(verdict["criteria_met"]) and verdict["score"] >= min_score else "REJECT"


def _normalize_verdict(raw: typing.Any, n: int) -> dict:
    # 拒绝重复或越界 id，避免同一条标准覆盖另一条。
    if not isinstance(raw, dict) or not isinstance(raw.get("criteria"), list):
        _error("BAD_SCHEMA", "LLM_ERROR")
    rows = raw["criteria"]
    if len(rows) != n:
        _error("BAD_SCHEMA", "LLM_ERROR")
    met_by_id = {}
    for row in rows:
        if not isinstance(row, dict):
            _error("BAD_SCHEMA", "LLM_ERROR")
        idx = row.get("id")
        if type(idx) is not int or not 1 <= idx <= n or idx in met_by_id:
            _error("BAD_SCHEMA", "LLM_ERROR")
        met = row.get("met", row.get("satisfied", row.get("passed")))
        if isinstance(met, str):
            word = met.strip().lower()
            if word in {"true", "yes", "met", "pass"}:
                met = True
            elif word in {"false", "no", "not_met", "fail", "unclear"}:
                met = False
        if type(met) is not bool:
            _error("BAD_SCHEMA", "LLM_ERROR")
        met_by_id[idx] = met
    score = raw.get("score")
    if isinstance(score, str) and re.fullmatch(r"[+-]?\d+", score.strip()):
        score = int(score)
    elif type(score) is float:
        # 允许 JSON 小数；不调用 float，NaN/Infinity 回滚。
        try:
            score = int(score + 0.5) if score >= 0 else int(score - 0.5)
        except (ValueError, OverflowError):
            _error("BAD_SCHEMA", "LLM_ERROR")
    if type(score) is not int:
        _error("BAD_SCHEMA", "LLM_ERROR")
    return {"criteria_met": [met_by_id[i] for i in range(1, n + 1)],
            "score": max(SCORE_MIN, min(SCORE_MAX, score)),
            "summary": re.sub(r"\s+", " ", str(raw.get("summary", ""))).strip()[:MAX_SUMMARY_CHARS]}


@allow_storage
@dataclass
class Bounty:
    id: u64
    creator: Address
    repo: str
    issue_number: u64
    issue_title: str
    issue_snapshot: str
    criteria_json: str
    min_score: u8
    reward: u256
    deadline: u64
    created_at: u64
    status: str
    winner: Address
    winning_claim_id: i64


@allow_storage
@dataclass
class Claim:
    id: u64
    bounty_id: u64
    claimant: Address
    github_id: u64
    pr_number: u64
    status: str
    reason: str
    merged_at: str
    diff_sha256: str
    criteria_met_json: str
    score: u8
    summary: str
    created_at: u64


class IssueBountyEscrow(gl.Contract):
    claim_grace_seconds: u64
    max_claims_per_claimant: u8
    bounties: DynArray[Bounty]
    claims: DynArray[Claim]
    claim_ids_by_bounty: TreeMap[str, DynArray[u64]]
    claim_count_by_key: TreeMap[str, u8]
    wallet_to_github_id: TreeMap[Address, u64]
    wallet_to_github_login: TreeMap[Address, str]
    github_id_to_wallet: TreeMap[str, Address]
    credits: TreeMap[Address, u256]
    total_escrowed: u256
    total_credits: u256
    total_withdrawn: u256

    def __init__(self, claim_grace_seconds: int, max_claims_per_claimant: int):
        if type(claim_grace_seconds) is not int or not 0 < claim_grace_seconds <= 30 * 86400:
            _error("INVALID_GRACE")
        if type(max_claims_per_claimant) is not int or not 1 <= max_claims_per_claimant <= 10:
            _error("INVALID_MAX_CLAIMS")
        self.claim_grace_seconds = u64(claim_grace_seconds)
        self.max_claims_per_claimant = u8(max_claims_per_claimant)
        self.total_escrowed = u256(0)
        self.total_credits = u256(0)
        self.total_withdrawn = u256(0)

    def _bounty(self, bounty_id: int) -> Bounty:
        if type(bounty_id) is not int or not 0 <= bounty_id < len(self.bounties):
            _error("BOUNTY_NOT_FOUND")
        return self.bounties[bounty_id]

    @gl.public.view
    def get_config(self) -> dict:
        return {"claim_grace_seconds": int(self.claim_grace_seconds),
                "max_claims_per_claimant": int(self.max_claims_per_claimant),
                "prompt_version": PROMPT_VERSION, "score_tolerance": SCORE_TOLERANCE,
                "max_criteria": MAX_CRITERIA}

    @gl.public.view
    def get_bounty(self, bounty_id: int) -> dict:
        b = self._bounty(bounty_id)
        return {"id": int(b.id), "creator": b.creator.as_hex, "repo": b.repo,
                "issue_number": int(b.issue_number), "issue_title": b.issue_title,
                "issue_snapshot": b.issue_snapshot, "criteria": json.loads(b.criteria_json),
                "min_score": int(b.min_score), "reward": int(b.reward),
                "deadline": int(b.deadline), "created_at": int(b.created_at),
                "status": b.status, "winner": b.winner.as_hex,
                "winning_claim_id": int(b.winning_claim_id)}

    @gl.public.view
    def get_bounties(self, offset: int, limit: int) -> list:
        if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= MAX_PAGE_SIZE:
            _error("INVALID_PAGE")
        return [self.get_bounty(i) for i in range(offset, min(offset + limit, len(self.bounties)))]

    @gl.public.view
    def get_bounty_count(self) -> int:
        return len(self.bounties)

    @gl.public.view
    def get_claim(self, claim_id: int) -> dict:
        if type(claim_id) is not int or not 0 <= claim_id < len(self.claims):
            _error("CLAIM_NOT_FOUND")
        c = self.claims[claim_id]
        return {"id": int(c.id), "bounty_id": int(c.bounty_id), "claimant": c.claimant.as_hex,
                "github_id": int(c.github_id), "pr_number": int(c.pr_number),
                "status": c.status, "reason": c.reason, "merged_at": c.merged_at,
                "diff_sha256": c.diff_sha256, "criteria_met": json.loads(c.criteria_met_json),
                "score": int(c.score), "summary": c.summary, "created_at": int(c.created_at)}

    @gl.public.view
    def get_claims_for_bounty(self, bounty_id: int) -> list:
        self._bounty(bounty_id)
        return [self.get_claim(int(i)) for i in self.claim_ids_by_bounty.get(str(bounty_id), [])]

    @gl.public.view
    def get_github_binding(self, wallet: str) -> dict:
        address = Address(wallet)
        return {"github_id": int(self.wallet_to_github_id.get(address, u64(0))),
                "login": self.wallet_to_github_login.get(address, "")}

    @gl.public.view
    def get_wallet_for_github_id(self, github_id: int) -> str:
        return self.github_id_to_wallet.get(str(github_id), Address(ZERO_ADDRESS)).as_hex

    @gl.public.view
    def get_credit(self, wallet: str) -> int:
        return int(self.credits.get(Address(wallet), u256(0)))

    @gl.public.view
    def get_accounting(self) -> dict:
        return {"total_escrowed": int(self.total_escrowed), "total_credits": int(self.total_credits),
                "total_withdrawn": int(self.total_withdrawn), "contract_balance": int(self.balance)}

    @gl.public.view
    def get_claim_count(self, bounty_id: int, wallet: str) -> int:
        self._bounty(bounty_id)
        key = f"{bounty_id}:{Address(wallet).as_hex.lower()}"
        return int(self.claim_count_by_key.get(key, u8(0)))
