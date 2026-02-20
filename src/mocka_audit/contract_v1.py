from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone


CONTRACT_VERSION_DEFAULT = "mocka.audit.v1"
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    pass


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_str_nonempty(name: str, value: str) -> str:
    if value is None:
        raise ContractError(f"{name} must not be None")
    if not isinstance(value, str):
        raise ContractError(f"{name} must be str")
    if value == "":
        raise ContractError(f"{name} must not be empty")
    if "\n" in value or "\r" in value:
        raise ContractError(f"{name} must not contain newlines")
    return value


def _require_hash64(name: str, value: str) -> str:
    v = _require_str_nonempty(name, value).strip().lower()
    if not _HEX64_RE.match(v):
        raise ContractError(f"{name} must be 64 lowercase hex chars")
    return v


def _format_ts_iso8601_utc(ts: datetime) -> str:
    if not isinstance(ts, datetime):
        raise ContractError("ts_local must be datetime")
    if ts.tzinfo is None:
        raise ContractError("ts_local must be timezone-aware")
    ts_utc = ts.astimezone(timezone.utc).replace(microsecond=0)
    return ts_utc.isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class AuditEventInput:
    ts_local: datetime
    event_kind: str
    target_path: str
    sha256_source: str
    sha256_after: str
    contract_version: str = CONTRACT_VERSION_DEFAULT


@dataclass(frozen=True)
class AuditEventDerived:
    event_content: str
    event_id: str
    chain_hash: str


def normalize_event_content(inp: AuditEventInput) -> str:
    ts_s = _format_ts_iso8601_utc(inp.ts_local)
    kind_s = _require_str_nonempty("event_kind", inp.event_kind).strip()
    path_s = _require_str_nonempty("target_path", inp.target_path).strip()

    src_s = _require_hash64("sha256_source", inp.sha256_source)
    aft_s = _require_hash64("sha256_after", inp.sha256_after)
    ver_s = _require_str_nonempty("contract_version", inp.contract_version).strip()

    content = "|".join([ts_s, kind_s, path_s, src_s, aft_s, ver_s])

    if "\n" in content or "\r" in content:
        raise ContractError("event_content must not contain newlines")

    return content


def compute_event_id(event_content: str) -> str:
    c = _require_str_nonempty("event_content", event_content)
    return _sha256_hex(c.encode("utf-8"))


def compute_chain_hash(previous_event_id: str, current_event_id: str) -> str:
    prev = _require_str_nonempty("previous_event_id", previous_event_id).strip()
    cur = _require_str_nonempty("current_event_id", current_event_id).strip()
    return _sha256_hex((prev + cur).encode("utf-8"))


def derive_event(inp: AuditEventInput, previous_event_id: str = "GENESIS") -> AuditEventDerived:
    content = normalize_event_content(inp)
    eid = compute_event_id(content)
    ch = compute_chain_hash(previous_event_id, eid)
    return AuditEventDerived(event_content=content, event_id=eid, chain_hash=ch)


def validate_derived(d: AuditEventDerived) -> None:
    _require_str_nonempty("event_content", d.event_content)
    _require_hash64("event_id", d.event_id)
    _require_hash64("chain_hash", d.chain_hash)