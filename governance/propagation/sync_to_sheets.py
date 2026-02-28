# NOTE: file=C:\Users\sirok\MoCKA\governance\propagation\sync_to_sheets.py
# NOTE: Phase23-C Google Sheets sync with approval gate
# NOTE: approval flag must exist and contain exact string "APPROVED" (BOM tolerant)
# NOTE: reads governance/propagation/public_index_v1.json (dict with items OR list)
# NOTE: writes header + rows to target sheet range

import os
import json
from datetime import datetime, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SECRETS_PATH = os.path.join(BASE_DIR, "governance", "secrets", "mocka-sheets-key.json")
APPROVAL_FLAG = os.path.join(BASE_DIR, "governance", "propagation", "APPROVED_TO_SYNC.flag")
PUBLIC_JSON = os.path.join(BASE_DIR, "governance", "propagation", "public_index_v1.json")
AUDIT_LOG = os.path.join(BASE_DIR, "governance", "propagation", "sync_audit.log")

SPREADSHEET_ID = "1qwTXWG95pYyOOHCcL57UFI0bu33UZKErtSDQSwMawew"
RANGE_NAME = "シート1!A1"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(f"{ts} {msg}\n")


def check_approval() -> bool:
    if not os.path.exists(APPROVAL_FLAG):
        log("DENY: approval flag missing")
        return False
    with open(APPROVAL_FLAG, "r", encoding="utf-8-sig") as f:
        content = f.read().strip()
    if content != "APPROVED":
        log("DENY: approval content invalid")
        return False
    return True


def load_public_items():
    if not os.path.exists(PUBLIC_JSON):
        log("HALT: public index missing")
        raise FileNotFoundError(PUBLIC_JSON)

    with open(PUBLIC_JSON, "r", encoding="utf-8-sig") as f:
        obj = json.load(f)

    if isinstance(obj, dict):
        items = obj.get("items", [])
        if not isinstance(items, list):
            log("HALT: public index items not list")
            raise ValueError("public_index_v1.json: items must be a list")
        return items

    if isinstance(obj, list):
        return obj

    log("HALT: public index root not dict/list")
    raise ValueError("public_index_v1.json must be dict(with items) or list")


def build_service():
    if not os.path.exists(SECRETS_PATH):
        log("HALT: secrets json missing")
        raise FileNotFoundError(SECRETS_PATH)

    creds = service_account.Credentials.from_service_account_file(
        SECRETS_PATH,
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=creds)


def write_sheet(values):
    svc = build_service()
    body = {"values": values}
    svc.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption="RAW",
        body=body,
    ).execute()


def main():
    if not check_approval():
        print("DENY")
        return

    items = load_public_items()

    values = [["event_id", "importance", "hash"]]
    for item in items:
        if isinstance(item, dict):
            values.append([item.get("event_id"), item.get("importance"), item.get("hash")])

    write_sheet(values)
    log(f"SYNC_OK count={len(items)}")
    print("SYNC_OK")


if __name__ == "__main__":
    main()