import csv
import hashlib
import os

EXPORT = r"C:\Users\sirok\MoCKA\governance\outfield\phase24_export_A.csv"
SIG    = r"C:\Users\sirok\MoCKA\governance\infield\calc\index_signature.sha256"

with open(SIG, "r", encoding="utf-8") as f:
    index_sig = f.read().strip()

with open(EXPORT, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["INDEX_SIGNATURE", index_sig])

print("SHEETS_EXPORT_WITH_SIGNATURE_READY")
