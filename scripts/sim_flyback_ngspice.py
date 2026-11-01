"""Re-run the 10 Oct open-loop flyback power-stage simulation (validation/sim/flyback_openloop.cir,
LTspice 26.1.1) in ngspice, as an independent cross-check, and plot waveforms for the report.

Same circuit and values as the LTspice netlist; only LTspice-specific syntax is translated
(.step -> one run per case, Rser= -> explicit series resistors, if() -> ternary, extra diode
parameters dropped). It is still an OPEN-LOOP POWER-STAGE model: ideal fixed-duty gate drive,
transformer = specification (n = 5, Lp = 7.3 uH, k = 0.99), generic FET/diode models.
It does not model the LM51551 control loop.

Usage: python3 scripts/sim_flyback_ngspice.py  (needs ngspice on PATH, numpy, matplotlib)
Outputs: validation/sim/ngspice/*.cir, *.log, results.md; docs/report/figures/sim_*.png
"""
import os
import re
import subprocess

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "validation", "sim", "ngspice")
FIG = os.path.join(ROOT, "docs", "report", "figures")

CASES = [  # same order as the LTspice .step list: (case, snub)
    ("vin3v0_nosnub", 3.0, 0.785, 0),
    ("vin4v2_nosnub", 4.2, 0.715, 0),
    ("vin3v0_snub", 3.0, 0.785, 1),
    ("vin4v2_snub", 4.2, 0.715, 1),
]

NET = """* Piezo Insulin Pump v2 - 48 V flyback power stage, OPEN LOOP (ngspice translation of flyback_openloop.cir)
* case {name}: Vin={vin} V, D={d}, snubber={snub}
.param fs=300k
.param vin={vin}
.param duty={d}
V1 vsrc 0 {{vin}}
R1s vsrc vin 20m
C1 vin c1n 220u
R1c c1n 0 80m
C2 vin c2n 20u
R2c c2n 0 3m
Lp vin lpn 7.3u
Rlp lpn sw 15m
Ls 0 lsn 182.5u
Rls lsn sec 0.35
K1 Lp Ls 0.99
M1 sw g cs cs QCSD
Rs cs 0 22m
Vg gd 0 PULSE(0 {{vin}} 0 15n 15n {{duty/fs-15n}} {{1/fs}})
Rg gd g 2
Dc sw clamp DSCH
Rc clamp vin 390
Cc clamp vin 22n
D1 sec out DHF
Rsn sec snb 220
Csn snb out {csn}
C3 out c3n 1.8u
R3c c3n 0 5m
C4 out c4n 47u
R4c c4n 0 0.3
Rload out 0 480
.model QCSD VDMOS(Vto=1.1 Kp=40 Rd=2.5m Rs=1m Rg=1 Cgs=0.9n Cgdmax=0.6n Cgdmin=0.08n Cjo=0.6n Is=1e-12 BV=25)
.model DSCH D(Is=2u Rs=40m N=1.15 Cjo=60p BV=100)
.model DHF D(Is=5n Rs=60m N=1.6 Cjo=15p Tt=15n BV=200)
.ic V(out)=48 V(clamp)=15
.options method=gear reltol=1e-3
.tran 5n 6m 5m uic
.meas tran vout_avg AVG v(out) FROM=5m TO=6m
.meas tran vout_pp PP v(out) FROM=5m TO=6m
.meas tran ipri_pk MAX i(Lp) FROM=5m TO=6m
.meas tran vds_max MAX v(sw) FROM=5m TO=6m
.meas tran vd1_rev_max MAX par('v(out)-v(sec)') FROM=5m TO=6m
.meas tran iin_avg AVG i(V1) FROM=5m TO=6m
.meas tran pout AVG par('v(out)*v(out)/480') FROM=5m TO=6m
.meas tran pclamp AVG par('(v(clamp)-v(vin))*(v(clamp)-v(vin))/390') FROM=5m TO=6m
.control
run
wrdata {wave} v(sw) i(Lp) v(out) v(out)-v(sec) v(clamp)
.endc
.end
"""


def run():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(FIG, exist_ok=True)
    rows = []
    for name, vin, d, snub in CASES:
        cir = os.path.join(OUT, f"flyback_{name}.cir")
        wave = os.path.join(OUT, f"wave_{name}.txt")
        open(cir, "w").write(NET.format(name=name, vin=vin, d=d, snub=snub,
                                        csn="100p" if snub else "1f", wave=wave))
        p = subprocess.run(["ngspice", "-b", cir], capture_output=True, text=True, timeout=3000)
        log = p.stdout + p.stderr
        open(os.path.join(OUT, f"flyback_{name}.log"), "w").write(log)
        m = {k: float(v) for k, v in re.findall(r"^(\w+)\s+=\s+([-+0-9.eE]+)", log, re.M)}
        iin = -m.get("iin_avg", float("nan"))
        pin = vin * iin
        rows.append((name, vin, snub, m.get("vout_avg"), m.get("vout_pp"), m.get("ipri_pk"), m.get("vds_max"),
                     m.get("vd1_rev_max"), iin, m.get("pout"), m.get("pout", 0) / pin if pin else float("nan"),
                     m.get("pclamp")))
        print(name, {k: round(v, 3) for k, v in m.items()})
    with open(os.path.join(OUT, "results.md"), "w") as f:
        f.write("| Case | Vin (V) | Snubber | Vout avg (V) | Vout p-p (V) | Ipri pk (A) | VDS max (V) | "
                "D301 reverse max (V) | Iin avg (A) | Pout (W) | Efficiency | P clamp (W) |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            if r[10] == r[10] and r[10] > 1.0:      # Pout > Pin: not a valid steady state
                f.write(f"| {r[0]} | {r[1]} | {r[2]} | INVALID: output power exceeds input power "
                        f"(efficiency {r[10]:.2f}); run did not converge to a physical steady state |"
                        + " |" * 8 + "\n")
                continue
            f.write("| " + " | ".join(str(r[0]) if i == 0 else (f"{x:.3g}" if isinstance(x, float) else str(x))
                                      for i, x in enumerate(r)) + " |\n")
    plot()


def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    name = "vin3v0_snub"
    d = np.loadtxt(os.path.join(OUT, f"wave_{name}.txt"))
    t = d[:, 0]
    sel = t >= t[-1] - 13.4e-6           # last four switching periods
    t = (t[sel] - t[sel][0]) * 1e6
    cols = {"v(sw) - FET drain (V)": d[sel, 1], "i(Lp) - primary current (A)": d[sel, 3],
            "v(out) - 48 V rail (V)": d[sel, 5], "D301 reverse voltage (V)": d[sel, 7]}
    fig, ax = plt.subplots(4, 1, figsize=(9, 9), sharex=True)
    for a, (lab, y) in zip(ax, cols.items()):
        a.plot(t, y, lw=1.0, color="#2a6fb0")
        a.set_ylabel(lab, fontsize=8)
        a.grid(True, lw=0.3)
    ax[-1].set_xlabel("time (us), last 4 switching periods, Vin = 3.0 V, 100 mA load, snubber fitted")
    fig.suptitle("ngspice open-loop power-stage simulation (transformer = specification, not a real part)", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "sim_flyback_waveforms_3v0.png"), dpi=110)


if __name__ == "__main__":
    import sys
    if "--only" in sys.argv:
        CASES[:] = [c for c in CASES if c[0] == sys.argv[sys.argv.index("--only") + 1]]
    run()
