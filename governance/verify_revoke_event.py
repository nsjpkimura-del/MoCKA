from pathlib import Path
import json,base64
from cryptography.hazmat.primitives.asymmetric import ed25519

def b64u_decode(s:str)->bytes:
    pad="="*((4-len(s)%4)%4)
    return base64.urlsafe_b64decode(s+pad)

ROOT=Path(__file__).resolve().parents[1]
EV=ROOT/"governance"/"revoke_event.json"
PUB=ROOT/"governance"/"keys"/"root_key_v2.ed25519.public.b64u"

if not EV.exists():
    print("INFO: revoke_event.json not present")
    raise SystemExit(0)

ev=json.loads(EV.read_text(encoding="utf-8-sig"))
sig=b64u_decode(ev["signature"])
ev_copy=dict(ev); ev_copy["signature"]=""

msg=json.dumps(ev_copy,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()
pub_raw=b64u_decode(PUB.read_text(encoding="utf-8-sig"))
pub=ed25519.Ed25519PublicKey.from_public_bytes(pub_raw)

try:
    pub.verify(sig,msg)
    print("PASS: revoke_event signature valid")
except Exception as e:
    print("FAIL: revoke_event signature invalid",e)
    raise SystemExit(2)
