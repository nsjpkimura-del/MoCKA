# C:\Users\sirok\MoCKA\governance\outfield\run_outfield_export_A.ps1
# One-shot: generate export_A.csv then diff-push to Google Sheets
# Target Spreadsheet:
# https://docs.google.com/spreadsheets/d/1qwTXWG95pYyOOHCcL57UFI0bu33UZKErtSDQSwMawew/edit#gid=0

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$py = "C:\Users\sirok\MoCKA\.venv\Scripts\python.exe"
$repo = "C:\Users\sirok\MoCKA"

Set-Location $repo

# 1) Generate export CSV (importance A only, exclude test ids)
& $py -c "
import csv, os
base = r'C:\Users\sirok\MoCKA\governance\infield\index'
out  = r'C:\Users\sirok\MoCKA\governance\outfield\phase24_export_A.csv'
files = [('seeds_index.csv','seeds'),('docs_index.csv','docs'),('calc_index.csv','calc')]
deny_prefix = ('seed_test_','seed_watch_','seed_poll_')
rows = []
for fname, typ in files:
    p = os.path.join(base, fname)
    if not os.path.exists(p):
        continue
    with open(p, encoding='utf-8-sig', newline='') as rf:
        r = csv.DictReader(rf)
        for row in r:
            if row.get('importance') != 'A':
                continue
            rid = (row.get('id') or '').strip()
            if rid.startswith(deny_prefix):
                continue
            rows.append({
                'id': rid,
                'type': typ,
                'title20': (row.get('title20') or '').strip(),
                'summary100': (row.get('summary100') or '').strip(),
                'link_target': (row.get('link_target') or '').strip(),
            })

with open(out, 'w', encoding='utf-8', newline='\n') as wf:
    w = csv.DictWriter(wf, fieldnames=['id','type','title20','summary100','link_target'])
    w.writeheader()
    w.writerows(rows)

print('EXPORT_OK:', out)
print('ROWS:', len(rows))
"

# 2) Diff push to Sheets + audit
& $py C:\Users\sirok\MoCKA\governance\outfield\push_export_A_to_sheets_diff.py
