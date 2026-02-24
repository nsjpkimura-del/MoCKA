MoCKA Phase14 Orphan Classification Policy
Version: 1.0
Purpose: 孤児イベントの制度的分類規則を固定する

1. 分類語定義

orphan_detected
  検出直後の未分類状態

historical_test
  意図的テストにより生成された枝
  条件:
    - prev_id = GENESIS である
    - 主要チェーン長に影響しない

operational_accident
  運用中の誤操作・途中失敗により発生
  条件:
    - 正統TIP系から途中分岐
    - 明示的テスト記録が存在しない

quarantined
  危険性を伴う枝
  隔離対象として扱う

reintegrated
  再接続が制度的に許可された枝

2. 分類変更規則

- 初期状態は orphan_detected
- 分類変更は専用スクリプトでのみ実施
- 変更理由は必ずnoteに残す
- 変更行為自体を audit_event として記録する

3. 禁止事項

- 直接DB更新禁止
- branch_registryの削除禁止

Status: ESTABLISHED
