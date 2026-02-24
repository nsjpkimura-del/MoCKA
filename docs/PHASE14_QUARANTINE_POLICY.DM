MoCKA Phase14 Quarantine Policy
Version: 1.0
Purpose: 危険枝の隔離制度を確立し、運用系から排除する

1. 概要
quarantined は「危険性があるため運用系から隔離する」分類である。
隔離は削除ではない。証跡保持を前提とする。

2. 隔離対象
以下のいずれかに該当する孤児を隔離する。
- 出所不明の枝
- 運用事故が疑われる枝
- 監査整合性に影響する可能性がある枝

3. 隔離の実施方法
- branch_registry.classification を quarantined に更新
- 隔離理由を note に追記
- 当該イベントのDB行をスナップショットとしてファイル保存する

4. 禁止事項
- quarantine の代替として削除すること
- 手動でDBを書き換えること

Status: ESTABLISHED
