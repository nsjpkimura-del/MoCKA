# mocka-transparency

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
