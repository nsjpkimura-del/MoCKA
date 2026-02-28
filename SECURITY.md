# SECURITY POLICY

## Reporting a Vulnerability

MoCKA is an experimental cryptographic audit framework.

If you discover a security issue, please open a GitHub Issue including:

- Clear reproduction steps  
- Affected component  
- Expected vs actual behavior  
- Potential impact assessment  

For sensitive disclosures, contact via GitHub direct message before public disclosure.

## Supported Scope

In scope:
- Hash chain tampering  
- Key rotation bypass  
- Signature forgery  
- Observer compromise assumptions  
- Timestamp anchoring weaknesses  

Out of scope:
- General dependency vulnerabilities  
- Local environment misconfiguration  

## Philosophy

Security is not assumed.  
It is continuously tested.  

Independent adversarial review is explicitly welcome.

---

# セキュリティポリシー（日本語）

## 脆弱性の報告方法

MoCKA は実験的な暗号監査フレームワークです。

脆弱性を発見した場合は、GitHub Issue に以下を記載してください：

- 再現手順  
- 影響を受けるコンポーネント  
- 期待される動作と実際の動作  
- 想定される影響範囲  

機密性の高い内容については、公開前にGitHub経由でご連絡ください。

## 対象範囲

対象：
- ハッシュ連鎖の改ざん  
- 鍵ローテーション回避  
- 署名偽造  
- 観測者前提の破綻  
- タイムスタンプ固定の弱点  

対象外：
- 一般的な依存ライブラリ脆弱性  
- ローカル環境の設定不備  

## 基本理念

セキュリティは前提ではない。  
検証され続けるものである。  

独立した批判的検証を歓迎する。
