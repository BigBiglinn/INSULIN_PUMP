"""Q301 (CSD16340Q3, VDS 25 V abs max [DS]) drain-voltage stress investigation.

Uses the closed-loop behavioural netlist of sim_flyback_closedloop.py and modifies it per case:
  - QCSD model breakdown raised from 25 V to 60 V so that the model's avalanche clamp cannot hide the true peak
    (with BV = 25 V a result 'at 25.7 V' only means 'the model avalanched');
  - operating point forced into cycle-by-cycle current limit (R307 open = the fault case, or startup/overload),
    starting from a given rail voltage (initial condition) so the worst case is reached in one window;
  - sweeps: Vin, Vout (rail), VCLTH (93/100/107 mV), coupling k (leakage 2 %/3 %), drain-loop parasitic
    inductance, RCD clamp R306/C308, and a numerical-accuracy check (reltol, max step).
The window is 0.25 ms, i.e. before the LM51551 hiccup counter (64 current-limit cycles = 215 us) would stop
switching; all cycles in it are current-limit cycles, which is the worst case the FET sees.

Usage: python3 scripts/sim_q301_stress.py   -> validation/sim/q301_stress/results.md, docs/report/figures/sim_q301_*.png
SIMULATION OF A MODEL - transformer = specification (T301 is a placeholder), generic FET/diode models.
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_flyback_closedloop as CL  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "validation", "sim", "q301_stress")
FIG = os.path.join(ROOT, "docs", "report", "figures")


def netlist(name, vin=4.2, vrail=52.0, vclth=0.100, k=0.99, r306="390", c308="22n", ldrain=0.0, bv=60,
            maxstep="2n", reltol="1e-3", tstop=0.25e-3, regulate=False, wave=True, load="8000", comp=None,
            rg="2", snub=None):
    """regulate=False: R307 open from t=0 -> current-limit operation (fault/overload worst case).
       regulate=True : normal regulation at vrail (6 mA load) for comparison."""
    base = dict(vin=vin, tstop=tstop, load=load, css="2.2u", fb_open=None if regulate else 0.0,
                ic=(vrail, comp if comp else (1.16 if regulate else 2.79), 2.0), r306=r306, c308=c308, vclth=vclth)
    c, net = CL.build(name, base)
    net = net.replace("BV=25)", f"BV={bv})")
    net = net.replace("K1 Lp Ls 0.99", f"K1 Lp Ls {k}")
    if ldrain:
        # parasitic inductance of the drain loop (PCB trace + package) between the winding and the FET drain;
        # the clamp diode connects at the winding side, so this inductance is NOT clamped
        net = net.replace("M1 sw g cs cs QCSD", f"Ld sw drn {ldrain}\nM1 drn g cs cs QCSD")
    net = net.replace("Rg gd g 2", f"Rg gd g {rg}")
    if snub:
        rs_, cs_ = snub                    # drain-source RC snubber at the FET pins
        d = "drn" if ldrain else "sw"
        net = net.replace("Rs cs 0 22m", f"Rs cs 0 22m\nRsd {d} sdn {rs_}\nCsd sdn 0 {cs_}")
    net = net.replace(".options method=gear reltol=1e-3 itl4=50", f".options method=gear reltol={reltol} itl4=50")
    net = re.sub(r"\.tran \S+ \S+ 0 10n", f".tran 2n {tstop} 0 {maxstep}", net)
    vds = "v(drn)" if ldrain else "v(sw)"
    meas = (f".meas tran vds_max MAX {vds} FROM=50u TO={tstop}\n"
            f".meas tran vclamp_avg AVG par('v(clamp)-v(vin)') FROM=100u TO={tstop}\n"
            f".meas tran ipk MAX i(Lp) FROM=50u TO={tstop}\n"
            f".meas tran p_r306 AVG par('(v(clamp)-v(vin))*(v(clamp)-v(vin))/{r306}') FROM=100u TO={tstop}\n"
            f".meas tran vout_end AVG v(out) FROM={tstop - 20e-6} TO={tstop}\n"
            f".meas tran iin_avg AVG i(V1) FROM={tstop * 0.6} TO={tstop}\n"
            f".meas tran pout_avg AVG par('v(mot)*v(mot)/({load})') FROM={tstop * 0.6} TO={tstop}\n")
    net = re.sub(r"\.meas tran [^\n]*\n", "", net)
    net = net.replace(".control", meas + ".control", 1)
    wf = os.path.join(OUT, f"wave_{name}.txt")
    ctl = (f".control\nrun\nset wr_singlescale\nset wr_vecnames\n"
           + (f"wrdata {wf} {vds} v(clamp) i(Lp)\n" if wave else "") + ".endc\n.end\n")
    net = re.sub(r"\.control.*", ctl, net, flags=re.S)
    return net


def run(case):
    name, kw = case
    net = netlist(name, **kw)
    cir = os.path.join(OUT, f"{name}.cir")
    log = os.path.join(OUT, f"{name}.log")
    open(cir, "w").write(net)
    subprocess.run(["ngspice", "-b", "-o", log, cir], capture_output=True, timeout=3600)
    txt = open(log).read()
    m = {k.lower(): float(v) for k, v in re.findall(r"^(\w+)\s*=\s*([-+0-9.eE]+)", txt, re.M)}
    ok = "aborted" not in txt and "Timestep too small" not in txt and "vds_max" in m
    return name, kw, m, ok


CASES = [
    # 1. reproduce the 25.7 V result and remove the model clamp
    ("A1_bv25_52V", dict(bv=25)),
    ("A2_bv60_52V", dict(bv=60)),
    # 2. numerical check
    ("A3_bv60_52V_fine", dict(bv=60, maxstep="0.5n", reltol="1e-4")),
    # 3. normal regulation (not current limit) for comparison
    ("B1_regulating_48V_4v2", dict(vrail=48.0, regulate=True)),
    ("B2_regulating_48V_3v0", dict(vrail=48.0, regulate=True, vin=3.0)),
    # 4. worst-case corners at current limit
    ("C1_cl_48V_4v2", dict(vrail=48.0)),
    ("C2_cl_53v1_4v2", dict(vrail=53.1)),
    ("C3_cl_55v9_4v2", dict(vrail=55.9)),
    ("C4_cl_55v9_4v2_vclth107", dict(vrail=55.9, vclth=0.107)),
    ("C5_cl_55v9_4v2_vclth107_k985", dict(vrail=55.9, vclth=0.107, k=0.985)),
    ("C6_cl_55v9_3v0", dict(vrail=55.9, vin=3.0)),
    # 5. parasitic drain inductance (not clamped)
    ("D1_cl_55v9_ld5n", dict(vrail=55.9, vclth=0.107, ldrain="5n")),
    ("D2_cl_55v9_ld10n", dict(vrail=55.9, vclth=0.107, ldrain="10n")),
    # 6. clamp re-tune at the worst corner (VCLTH 107 mV, 3 % leakage, 55.9 V, 4.2 V)
    ("E1_r270", dict(vrail=55.9, vclth=0.107, k=0.985, r306="270")),
    ("E2_r220", dict(vrail=55.9, vclth=0.107, k=0.985, r306="220")),
    ("E3_r180", dict(vrail=55.9, vclth=0.107, k=0.985, r306="180")),
    ("E4_r150", dict(vrail=55.9, vclth=0.107, k=0.985, r306="150")),
    ("E5_r150_ld5n", dict(vrail=55.9, vclth=0.107, k=0.985, r306="150", ldrain="5n")),
    # 7. clamp capacitor (ripple) at the worst corner
    ("G1_c100n", dict(vrail=55.9, vclth=0.107, k=0.985, c308="100n")),
    ("G2_c220n", dict(vrail=55.9, vclth=0.107, k=0.985, c308="220n")),
    ("G3_c470n", dict(vrail=55.9, vclth=0.107, k=0.985, c308="470n")),
    ("G4_c1u", dict(vrail=55.9, vclth=0.107, k=0.985, c308="1u")),
    ("G5_c470n_r220", dict(vrail=55.9, vclth=0.107, k=0.985, c308="470n", r306="220")),
    ("G6_c470n_r150", dict(vrail=55.9, vclth=0.107, k=0.985, c308="470n", r306="150")),
    # 8. layout parasitic + mitigations (gate turn-off resistor, drain RC snubber)
    ("H1_c470n_r220_ld5n", dict(vrail=55.9, vclth=0.107, k=0.985, c308="470n", r306="220", ldrain="5n")),
    ("H2_c470n_r220_ld5n_rg10", dict(vrail=55.9, vclth=0.107, k=0.985, c308="470n", r306="220", ldrain="5n",
                                     rg="10")),
    ("H3_c470n_r220_ld5n_snub", dict(vrail=55.9, vclth=0.107, k=0.985, c308="470n", r306="220", ldrain="5n",
                                     snub=("4.7", "1n"))),
    ("H4_c470n_r150_ld5n_rg10_snub", dict(vrail=55.9, vclth=0.107, k=0.985, c308="470n", r306="150",
                                          ldrain="5n", rg="10", snub=("4.7", "1n"))),
    # 9. adopted interim clamp (R306 220 ohm, C308 470 nF) at other corners
    ("I1_new_clamp_cl_48V_3v0", dict(vrail=48.0, vin=3.0, r306="220", c308="470n")),
    ("I2_new_clamp_cl_48V_4v2", dict(vrail=48.0, r306="220", c308="470n")),
    ("I3_new_clamp_worst_ld2n", dict(vrail=55.9, vclth=0.107, k=0.985, c308="470n", r306="220", ldrain="2n")),
    ("I5_r220_c220n_worst_derated", dict(vrail=55.9, vclth=0.107, k=0.985, c308="220n", r306="220")),
    ("I4_new_clamp_worst_ld2n_rg10", dict(vrail=55.9, vclth=0.107, k=0.985, c308="470n", r306="220", ldrain="2n",
                                          rg="10")),
    # 10. re-tuned clamp in normal regulation (efficiency / clamp loss penalty)
    ("F3_c470n_r220_regulating_3v0_100mA", dict(vrail=48.0, regulate=True, vin=3.0, r306="220", c308="470n",
                                                load="480", comp=1.63, tstop=1.5e-3)),
    ("F4_c470n_r220_regulating_4v2_100mA", dict(vrail=48.0, regulate=True, vin=4.2, r306="220", c308="470n",
                                                load="480", comp=1.56, tstop=1.5e-3)),
    ("F1_r150_regulating_3v0_100mA", dict(vrail=48.0, regulate=True, vin=3.0, r306="150", load="480", comp=1.63,
                                          tstop=1.5e-3)),
    ("F2_r390_regulating_3v0_100mA", dict(vrail=48.0, regulate=True, vin=3.0, r306="390", load="480", comp=1.63,
                                          tstop=1.5e-3)),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    cases = [c for c in CASES if not only or c[0] in only]
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        res = list(ex.map(run, cases))
    L = ["# Q301 drain-voltage stress investigation (simulation)", "",
         "Generated by `scripts/sim_q301_stress.py`. Behavioural LM51551 + switching power stage (ngspice 42), T301 =",
         "specification (n 5, Lp 7.3 uH), generic FET/diode models. **QCSD breakdown raised to 60 V** except case A1, so",
         "peaks are not hidden by the model's avalanche. 'cl' = R307 open, current-limit operation (fault/overload);",
         "'regulating' = normal operation. CSD16340Q3 V<sub>DS</sub> abs max = 25 V [DS]; 80 % design limit = 20 V.", "",
         "| Case | Vin | Rail start | VCLTH | k | R306 | C308 | L drain | Rg | drain RC | VDS max (V) | % of 25 V | clamp avg above Vin (V) | Ipk (A) | P(R306) (W) | eff. | Valid |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, kw, m, ok in res:
        L.append(f"| {name} | {kw.get('vin', 4.2)} | {kw.get('vrail', 52.0)} | {kw.get('vclth', 0.1)*1e3:.0f} mV | "
                 f"{kw.get('k', 0.99)} | {kw.get('r306', '390')} | {kw.get('c308', '22n')} | {kw.get('ldrain', 0) or '-'} | "
                 f"{kw.get('rg', '2')} | {'/'.join(kw['snub']) if kw.get('snub') else '-'} | "
                 f"{m.get('vds_max', float('nan')):.2f} | {m.get('vds_max', 0)/25*100:.0f} % | "
                 f"{m.get('vclamp_avg', float('nan')):.2f} | {m.get('ipk', float('nan')):.2f} | "
                 f"{m.get('p_r306', float('nan')):.3f} | "
                 f"{(m['pout_avg'] / (-m['iin_avg'] * kw.get('vin', 4.2))) if kw.get('regulate') and m.get('iin_avg') else float('nan'):.3f} | "
                 f"{'yes' if ok else 'NO'} |")
    open(os.path.join(OUT, "results.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    plot()


def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for name, lab in (("A1_bv25_52V", "model BV 25 V (as before): clipped"), ("A2_bv60_52V", "model BV 60 V: true peak"),
                      ("C5_cl_55v9_4v2_vclth107_k985", "worst corner, 390 ohm / 22 nF"),
                      ("G5_c470n_r220", "worst corner, 220 ohm / 470 nF")):
        f = os.path.join(OUT, f"wave_{name}.txt")
        if not os.path.exists(f):
            continue
        a = np.loadtxt(f, skiprows=1)
        t0 = 0.2e-3
        m = (a[:, 0] > t0) & (a[:, 0] < t0 + 3 * 3.356e-6)
        ax[0].plot((a[m, 0] - t0) * 1e6, a[m, 1], label=lab)
        ax[1].plot((a[m, 0] - t0) * 1e6, a[m, 3], label=lab)
    ax[0].axhline(25, c="r", ls="--", lw=.8); ax[0].axhline(20, c="orange", ls="--", lw=.8)
    ax[0].set_ylabel("Q301 drain (V)"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    ax[1].set_ylabel("primary current (A)"); ax[1].set_xlabel("time (us)"); ax[1].grid(alpha=.3)
    ax[0].set_title("Q301 drain at current limit (R307 open), Vin 4.2 V - simulation, not measurement", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "sim_q301_drain.png"), dpi=110)


if __name__ == "__main__":
    main()
