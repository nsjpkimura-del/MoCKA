# C:\Users\sirok\MoCKA\governance\outfield\push_export_A_to_sheets.py
# Target Spreadsheet:
# https://docs.google.com/spreadsheets/d/1qwTXWG95pYyOOHCcL57UFI0bu33UZKErtSDQSwMawew/edit#gid=0

import csv
from pathlib import Path
from typing import List

import gspread
from google.oauth2.service_account import Credentials

CSV_PATH = Path(r"C:\Users\sirok\MoCKA\governance\outfield\phase24_export_A.csv")
CREDS_JSON = Path(r"C:\Users\sirok\MoCKA\secrets\gcp_service_account.json")

SPREADSHEET_ID = "1qwTXWG95pYyOOHCcL57UFI0bu33UZKErtSDQSwMawew"
TARGET_SHEET_NAME = "outfield_export_A"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def read_csv_rows(path: Path) -> List[List[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [row for row in csv.reader(f)]

def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit("ERROR: CSV not found")

    if not CREDS_JSON.exists():
        raise SystemExit("ERROR: creds json not found")

    rows = read_csv_rows(CSV_PATH)
    if not rows:
        raise SystemExit("ERROR: CSV empty")

    creds = Credentials.from_service_account_file(str(CREDS_JSON), scopes=SCOPES)
    gc = gspread.authorize(creds)

    sh = gc.open_by_key(SPREADSHEET_ID)

    try:
        ws = sh.worksheet(TARGET_SHEET_NAME)
    except Exception:
        ws = sh.add_worksheet(
            title=TARGET_SHEET_NAME,
            rows=max(200, len(rows) + 10),
            cols=max(10, len(rows[0]) if rows else 10),
        )

    ws.clear()
    ws.update(range_name="A1", values=rows)

    print("書き込み完了")
    print("ROWS:", max(0, len(rows) - 1))

if __name__ == "__main__":
    main()
