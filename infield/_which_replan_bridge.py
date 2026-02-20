import hashlib
import mocka.replan_bridge_auto as m
p = m.__file__
h = hashlib.sha256(open(p,"rb").read()).hexdigest()
print("FILE =", p)
print("SHA256 =", h)
