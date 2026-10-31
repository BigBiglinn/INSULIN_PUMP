import re
base = open("../flyback_clamp_final.cir", encoding="latin1").read()
MODELS = {
 "aonr": ".model QF VDMOS(Vto=0.85 Kp=300 Rd=1m Rs=0.3m Rg=1 Cgs=3n Cgdmax=0.6n Cgdmin=0.15n Cjo=5n M=0.4 Is=1e-12 BV=60 mfg=AONR34332C_fit)",
 "buk_typ": ".model QF VDMOS(Vto=2.21 Kp=43 Rd=7m Rs=3m Rg=0.8 Cgs=520p Cgdmax=100p Cgdmin=22p Cjo=900p M=0.4 Is=1e-12 BV=60 mfg=BUK9M20_fit_typ)",
 "buk_maxvth": ".model QF VDMOS(Vto=2.56 Kp=43 Rd=7m Rs=3m Rg=0.8 Cgs=520p Cgdmax=100p Cgdmin=22p Cjo=900p M=0.4 Is=1e-12 BV=60 mfg=BUK9M20_fit_vth_plus_0p35)",
}
for rcl in (330,):
  for name, model in MODELS.items():
    for vin in ("3.0", "3.4", "4.2"):
        s = base
        s = s.replace("RCLVAL", str(rcl))
        s = re.sub(r"\.model QF VDMOS.*", model, s)
        s = s.replace(".param Vin=4.2", f".param Vin={vin}")
        s = s.replace(".step param leak list 0.01 0.02 0.04 0.06 0.10", ".step param leak list 0.06 0.10")
        s = s.replace(".step param tvs list 0 1\n", ".param tvs=1\n").replace(".step param tvs list 0 1\r\n", ".param tvs=1\r\n")
        # 4 nH commutation-loop estimate from PCB_STAGES.md, in series with the clamp path
        s = s.replace("Dc sw clamp DSCH", "Lstray sw swl 4n\nDc swl clamp DSCH")
        s = s.replace(".end", ".meas tran Von_max MAX V(sw) TRIG V(q)=0.5 RISE=last\n.end") if False else s
        open(f"{name}_{vin.replace('.','p')}.cir", "w", encoding="latin1", newline="\n").write(s)
