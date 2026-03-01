# AI_SAVE_SPEC_v0.1
Core Rule: 1 save = 1 index row + 1 body file
ID Rule: AS-YYYYMMDD_HHMMSS-hash8
Index Header: ts_iso,item_id,title,summary,tags,source,actor,body_path,body_sha256,ext_ref
Decision Log Header: ts_iso,dec_id,scope,decision,reason,change_summary,actor,refs
Integrity: sha256, append-only

NOTE: Git commit署名の検証（機械可読, 文字化け回避）
cmd:
  git --no-pager log --format=""%H%nG=%G?%nFPR=%GF%nSIGNER=%GS%nDATE=%cd%nSUBJ=%s%n"" -1
meaning:
  G=valid signature, N=no signature, B=bad signature, U=unknown trust

