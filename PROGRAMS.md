# MoCKA Programs Reference

This document explains the major programs and scripts in MoCKA.
It is intended for engineers who want to reproduce, audit, or attack-test the system.

---

## 1. Chain Verification

### verify_chain.py
EN
Verifies the deterministic SHA256 append-only chain for structural integrity.
Typical checks include:
- Entry ordering and linkage (prev hash relation)
- Deterministic hashing rules
- Optional timestamp/monotonic constraints (if enabled)

JP
決定論的なSHA256追記連鎖を検証する。
主な検証項目：
- 連鎖構造（prev hash）の整合
- 決定論的ハッシュ規則の確認
- 必要に応じて時刻単調性などの制約

Example
python verify_chain.py path\to\chain.csv

---

## 2. Key Governance and Rotation

### transition_verify.py
EN
Validates key transition events (key_id introduction, valid_to retirement, and transition logs).
Focus:
- Correct succession ordering
- Retirement enforcement (valid_to model)
- Multi-step transition validation

JP
鍵の遷移イベントを検証する（key_id導入、valid_to退位、遷移ログ）。
注目点：
- 継承順序の正しさ
- valid_toによる退位の強制
- 多段遷移の整合性検証

Example
python transition_verify.py governance\transition_log.csv

---

### transition_log.csv
EN
Append-only governance record of key succession.
This is a primary artifact for auditability of authority changes.

JP
鍵継承の追記専用ガバナンス記録。
権限継承の監査可能性を担保する一次資料。

---

## 3. Observer System

### observer_run.py
EN
Runs observer routines that verify latest chain states under a strict-latest policy.
Designed for continuous validation (for example, on a dedicated drive or node).

JP
strict-latest方針で最新チェーン状態を検証する観測ルーチンを実行。
常時検証ノードでの継続監査を想定。

---

### observer_seal.py
EN
Produces an observer seal artifact (a cryptographic snapshot of observer state).
Used to freeze an audit state for later comparison.

JP
観測者封印（オブザーバーシール）を生成する。
監査状態をスナップショットとして固定し、後日の比較に使う。

---

### observer_seal_verify.py
EN
Verifies an observer seal artifact and checks consistency against chain states.

JP
観測者封印を検証し、チェーン状態との整合を確認する。

---

### observer_audit.log / observer_audit_chain.csv
EN
Operational logs and chain artifacts produced by the observer system.

JP
観測者システムが生成する運用ログおよび連鎖資料。

---

## 4. External Time Anchoring

### rfc3161_stamp.py
EN
Obtains an RFC3161 timestamp token for a given hash.
Provides an external time anchor for anti-rollback and ordering guarantees.

JP
指定ハッシュに対するRFC3161タイムスタンプトークンを取得する。
ロールバック耐性と順序保証の外部アンカーとして使う。

Inputs / Outputs
- Input: hash value (SHA256)
- Output: .tsr timestamp response

---

## 5. Public Transparency Indexing

### tools/build_public_index.py
EN
Builds a sanitized public index for transparency publication.
Typically used to generate:
- public_index_v1.json
- references to proof packages
- stable identifiers for external review

JP
透明性公開用のサニタイズされたインデックスを生成する。
主に以下を作る：
- public_index_v1.json
- proofパッケージ参照
- 外部レビュー向けの安定ID

---

### governance/propagation/public_index_v1.json
EN
A generated public index intended for external reviewers.
This file should be reproducible from source.

JP
外部レビュー向けの公開インデックス（生成物）。
生成元から再現可能であるべき。

---

## 6. Outfield Synchronization

### governance/propagation/sync_to_sheets.py
EN
Synchronizes selected summaries or indices to an outfield store (for example, Google Sheets).
Purpose:
- cross-device portability
- cross-agent shared reference layer
- lightweight summary protocol for constrained environments

Security Notes
- Do not commit secrets (API keys, credentials).
- Prefer environment variables and local secret stores.

JP
選別された要約やインデックスをアウトフィールド（例：Google Sheets）へ同期する。
目的：
- 端末間での可搬性
- エージェント間の共有参照層
- 制約環境向け軽量サマリプロトコル

セキュリティ注意
- APIキー等の秘密はコミットしない。
- 環境変数とローカル秘密管理を優先する。

---

## 7. Recommended Reading Order (for Reviewers)

EN
1) ARCHITECTURE.md
2) AI_ORCHESTRATION_THREAT_MODEL.md
3) PROGRAMS.md (this file)
4) governance/history (REC documents)
5) mocka-transparency proof package and verification scripts

JP
1) ARCHITECTURE.md
2) AI_ORCHESTRATION_THREAT_MODEL.md
3) PROGRAMS.md（本書）
4) governance/history（REC文書）
5) mocka-transparency の検証資産

---

## 8. Notes on Reproducibility

EN
MoCKA is designed as a reproducible integrity experiment.
If a script output is intended for publication, it should be reproducible from source with documented inputs.

JP
MoCKAは再現可能な整合性実験として設計されている。
公開対象の出力は、入力を明示し、生成元から再現できることが望ましい。
