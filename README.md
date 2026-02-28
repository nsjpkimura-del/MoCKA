[Whitepaper v0.1](https://github.com/nsjpkimura-del/mocka-civilization/blob/main/WHITEPAPER_v0.1.md)

## Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Threat Model](AI_ORCHESTRATION_THREAT_MODEL.md)
- [Programs Reference](PROGRAMS.md)
- [Security Policy](SECURITY.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## ドキュメント一覧（日本語）

- [アーキテクチャ概要](ARCHITECTURE.md)
- [脅威モデル](AI_ORCHESTRATION_THREAT_MODEL.md)
- [プログラム一覧](PROGRAMS.md)
- [セキュリティポリシー](SECURITY.md)
- [貢献ガイドライン](CONTRIBUTING.md)

---# mocka-transparency

Public verification layer for the MoCKA architecture.

This repository contains reproducible proof artifacts for:

- Deterministic SHA256 audit chains  
- Ed25519 signature validation  
- RFC3161 timestamp anchoring  
- Multi-observer integrity model  

## Verification

Clone and validate:

```bash
git clone https://github.com/nsjpkimura-del/mocka-transparency
python verify_chain.py observer_audit_chain.csv
```

Independent cryptographic scrutiny is encouraged.

---

# mocka-transparency（日本語）

MoCKA アーキテクチャの公開検証レイヤーです。

本リポジトリには以下の再現可能な検証資産が含まれます：

- SHA256 決定論的監査連鎖  
- Ed25519 署名検証  
- RFC3161 外部タイムスタンプ固定  
- マルチ観測者整合モデル  

独立した暗号学的検証を歓迎します。

---
Part of the MoCKA Deterministic Governance Architecture.
See Civilization layer for full structural doctrine.


