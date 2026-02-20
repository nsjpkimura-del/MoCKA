Week3 Ed25519 daily signature minimal drop.

1) Install:
   pip install cryptography

2) Generate keys (once):
   python -c "from key_manager import generate_keys; generate_keys()"

3) Sign:
   python -c "import datetime; from daily_signature import sign_daily; d=datetime.date.today().isoformat(); print(sign_daily(d,'FINAL_CHAIN_HASH',6,2))"

4) Verify:
   python -c "import datetime; from daily_signature import sign_daily, verify_daily; d=datetime.date.today().isoformat(); s=sign_daily(d,'FINAL_CHAIN_HASH',6,2); print(verify_daily(s,d,'FINAL_CHAIN_HASH',6,2))"

5) Save to sqlite:
   python -c "import datetime; from daily_signature import sign_daily; from daily_sig_db_sqlite import save_daily_signature; d=datetime.date.today().isoformat(); sig=sign_daily(d,'FINAL_CHAIN_HASH',6,2); save_daily_signature('audit.db',d,'FINAL_CHAIN_HASH',6,2,sig)"