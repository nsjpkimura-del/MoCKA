# AI_SAVE_SPEC_v0.1
Core Rule: 1 save = 1 index row + 1 body file
ID Rule: AS-YYYYMMDD_HHMMSS-hash8
Index Header: ts_iso,item_id,title,summary,tags,source,actor,body_path,body_sha256,ext_ref
Decision Log Header: ts_iso,dec_id,scope,decision,reason,change_summary,actor,refs
Integrity: sha256, append-only
