"""Second Q301 run: shorter window, worst corners only, from the decks written by make.py."""
import re

KEEP = ["aonr_3p4", "aonr_4p2", "buk_typ_3p4", "buk_typ_4p2", "buk_maxvth_3p4", "buk_maxvth_4p2"]
for name in KEEP:
    s = open(f"{name}.cir", encoding="latin1").read()
    s = s.replace(".tran 0 700u 600u 0 uic", ".tran 0 230u 200u 0 uic")
    s = s.replace(".step param leak list 0.06 0.10", ".param leak=0.10")
    s = re.sub(r"\.param Vin=([0-9.]+)", r".param Vin=\1", s)
    open(f"short_{name}.cir", "w", encoding="latin1", newline="\n").write(s)
