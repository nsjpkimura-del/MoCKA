# AI Orchestration Threat Model

## Scope
This document defines the threat model for MoCKA’s multi-agent orchestration and governance layer.
Objective: auditable resilience, not perfect security.

## System Model
MoCKA combines:
- Deterministic append-only audit chain (SHA256)
- Signature-based governance (Ed25519)
- Key retirement / succession (valid_to)
- Multi-observer verification model
- Optional external time anchoring (RFC3161)
- Dual-layer memory concept (INFIELD source / OUTFIELD sync)

## Trust Assumptions
- Cryptographic primitives remain secure
- At least one observer remains uncompromised
- Governance key material is not fully compromised simultaneously
- Deterministic generation and verification rules are followed

## Adversary Model
Adversaries may attempt:
- Log tampering / insertion / deletion
- Rollback attacks (reverting to an older state)
- Time spoofing and re-ordering
- Key theft or unauthorized signing
- Poisoning of outfield summaries or indices
- Orchestration misrouting (wrong agent, wrong authority)
- Partial host compromise

## Failure Modes (Explicit Limits)
MoCKA can fail if:
- Governance keys are fully compromised
- Multiple observers are compromised
- Deterministic gates are bypassed
- External timestamp services are unavailable when required
- Replicated memory diverges silently without detection

## Mitigations
- Append-only deterministic hashing (tamper evidence)
- Signature governance with enforced retirement (authority tracking)
- Multi-observer separation (assumption diversification)
- External timestamp anchoring (anti-rollback time witness)
- Documented delegation and phase reconstruction rules

## Non-Goals
- Distributed consensus or blockchain design
- Economic attack resistance (token incentives)
- Global real-time replication guarantees
- Strong Byzantine fault tolerance

## Open Review
Independent scrutiny is welcome:
- Threat model criticism
- Attack surface enumeration
- Adversarial test plans
- Suggestions for formal verification or proofs

---

# AIオーケストレーション脅威モデル（日本語）

## 適用範囲
本書は、MoCKAのマルチエージェント・オーケストレーションおよびガバナンス層に対する脅威モデルを定義する。
目的は完全無欠な安全性ではなく、監査可能な耐性である。

## システムモデル
MoCKAは以下を組み合わせる：
- SHA256による追記専用の決定論的監査連鎖
- Ed25519署名によるガバナンス
- valid_to による鍵退位と継承
- マルチ観測者検証モデル
- 必要に応じたRFC3161外部時刻固定
- 二層記憶（INFIELD原本／OUTFIELD同期）

## 信頼前提
- 暗号原語が破綻していない
- 少なくとも一つの観測者が健全である
- ガバナンス鍵が同時に全面侵害されていない
- 決定論的生成・検証ルールが守られている

## 攻撃者モデル
攻撃者は以下を試み得る：
- ログの改ざん、挿入、削除
- ロールバック攻撃（過去状態への巻き戻し）
- 時刻偽装や順序の攪乱
- 鍵の窃取や不正署名
- アウトフィールド要約やインデックスの汚染
- オーケストレーション誤誘導（誤った権限・誤った委任）
- ホストの部分侵害

## 失敗条件（設計限界）
以下では破綻し得る：
- ガバナンス鍵の全面侵害
- 複数観測者の同時侵害
- 決定論的ゲートの回避
- 必要時の外部タイムスタンプ不在
- 複製記憶の無検知乖離

## 緩和策
- 追記専用決定論的ハッシュ（改ざん検知）
- 署名ガバナンスと退位強制（権限追跡）
- 観測者分離（前提の分散）
- 外部時刻固定（反ロールバックの外部証言）
- 委任とフェーズ再構築の公式ルール化

## 非目標
- 分散合意やブロックチェーン
- トークン設計など経済的耐性
- グローバル即時同期の保証
- 強いビザンチン耐性

## 公開レビュー
以下を歓迎する：
- 脅威モデルへの批判
- 攻撃面の列挙
- 攻撃計画の提案
- 形式検証や証明の提案
