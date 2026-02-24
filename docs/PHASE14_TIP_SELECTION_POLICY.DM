MoCKA Phase14 TIP Selection Policy
Version: 1.0
Purpose: 分岐発生時の正統TIP決定規則を制度化する

1. 基本原則
TIPは決定論的規則により自動選択される。
人間の感覚判断は禁止。

2. 優先順位規則

Rule-1: 最長チェーン優先
到達長（reachable length）が最大のチェーンを正統とする。

Rule-2: 同長時の決定規則
event_id の辞書順で最小値を正統とする。
（完全決定論のため）

Rule-3: 明示再選択儀式
例外的変更は専用再選択スクリプトでのみ可能。
その場合は audit_event として記録する。

3. 禁止事項
- 手動で last_event_id.txt を直接編集すること
- DBを直接改変すること

4. 適用条件
ORPHAN_COUNT > 0 の場合に本規則を発動する。

Status: ESTABLISHED
Record Timestamp (UTC):
02/24/2026 10:55:47.ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss")

Execution Evidence
- tool: tools\phase14_reselect_tip.py
- db: audit\ed25519\audit.db
- ledger_table_detected: audit_ledger_event
- new_tip_selected: 33cedbb94b557e08c1babf10006f288c112e26b2ecd4cb563458ff632f3b07d9
- chain_length: 30
- note: deterministic selection executed successfully

Evidence Timestamp (UTC): 2026-02-24 01:58:30
