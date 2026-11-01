"""Third Q301 run: AONR34332C at 4.2 V, 4.9 A. Settling check (later window), 3-5 nH loop range, 2 % and 10 % leakage."""

base = open("short_aonr_4p2.cir", encoding="latin1").read()
for lst in ("3n", "5n"):
    for leak in ("0.02", "0.10"):
        s = base
        s = s.replace(".step param Ipk list 3.4 4.9", ".param Ipk=4.9")
        s = s.replace(".param leak=0.10", f".param leak={leak}")
        s = s.replace("Lstray sw swl 4n", f"Lstray sw swl {lst}")
        s = s.replace(".tran 0 230u 200u 0 uic", ".tran 0 430u 400u 0 uic")
        # Ptv in the earlier decks is the loss in Rtv only; this is the power in the TVS junction
        s = s.replace(".end", ".meas tran Pdtv AVG (V(vin)-V(tv))*I(Dtv)\n.end")
        open(f"check_aonr_4p2_{lst}_leak{leak.replace('0.', '')}.cir", "w", encoding="latin1", newline="\n").write(s)
        # Drain-source capacitance read from datasheet Fig. 8: Coss-Crss about 2.7 nF at 0 V, 1.25 nF at 15 V
        s = s.replace("Cjo=5n M=0.4", "Cjo=2.7n M=0.28")
        open(f"check_aonr_coss_4p2_{lst}_leak{leak.replace('0.', '')}.cir", "w", encoding="latin1", newline="\n").write(s)
