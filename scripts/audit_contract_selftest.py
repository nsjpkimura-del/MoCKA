from __future__ import annotations

from datetime import datetime, timezone

from src.mocka_audit.contract_v1 import (
    AuditEventInput,
    ContractError,
    compute_chain_hash,
    compute_event_id,
    derive_event,
    normalize_event_content,
    validate_derived,
)


def _h64(ch: str) -> str:
    return ch * 64


def main() -> int:
    try:
        inp = AuditEventInput(
            ts_local=datetime(2026, 2, 20, 12, 34, 56, tzinfo=timezone.utc),
            event_kind="ingest",
            target_path=r"outbox\example.json",
            sha256_source=_h64("a"),
            sha256_after=_h64("b"),
            contract_version="mocka.audit.v1",
        )

        content = normalize_event_content(inp)
        eid = compute_event_id(content)
        ch0 = compute_chain_hash("GENESIS", eid)

        d = derive_event(inp, previous_event_id="GENESIS")
        validate_derived(d)

        assert d.event_content == content
        assert d.event_id == eid
        assert d.chain_hash == ch0

        # Determinism check: same input -> same output
        d2 = derive_event(inp, previous_event_id="GENESIS")
        assert d2 == d

        # Mutation check: change one field -> different event_id
        inp3 = AuditEventInput(
            ts_local=inp.ts_local,
            event_kind="ingest",
            target_path=r"outbox\example2.json",
            sha256_source=inp.sha256_source,
            sha256_after=inp.sha256_after,
            contract_version=inp.contract_version,
        )
        d3 = derive_event(inp3, previous_event_id="GENESIS")
        assert d3.event_id != d.event_id

        print("OK")
        print("event_content:", d.event_content)
        print("event_id:", d.event_id)
        print("chain_hash:", d.chain_hash)
        return 0

    except ContractError as e:
        print("CONTRACT_ERROR:", str(e))
        return 2
    except Exception as e:
        print("ERROR:", repr(e))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())