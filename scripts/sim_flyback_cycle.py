"""Cycle-by-cycle model of the 48 V flyback with LM51551 control, for LONG-HORIZON behaviour that a switching
SPICE run cannot reach in reasonable time: soft start versus hiccup, the open-R307 fault over seconds (hiccup
ratchet), the proposed independent OVP, output short in hiccup, and soft-start capacitor sizing.

Model (each switching period solved exactly for an ideal, piecewise-linear flyback):
  on-time: magnetizing current rises Vin/Lp; it ends at the first of PWM compare
           Rs*i + 40 mV*(t/Tsw) >= GCOMP*(VCOMP - VOFF), current limit Rs*i >= VCLTH, or DMAX; never < tON(min)
  off-time: secondary current i/n falls at (Vout + Vf + i_s*Rsec)/Ls (CCM or DCM solved exactly)
  output: C_out with exact exponential discharge into the load resistance
  error amplifier: Gm into the Type-II network R303/C306/C307 + RO, COMP clamps, 8 Euler sub-steps per period
  soft start, internal OVP (110 %/105 %), UVLO/EN, hiccup (64 CL cycles, reset by 8 clean cycles, 32 768 off)
  PGOOD (FB > 95 % rising)
Sources: SNVSB75E for every controller number except VOFF = 1.0 V and DMAX = 90 % (ASSUMPTIONS, as in
sim_flyback_closedloop.py); transformer = specification (n 5, Lp 7.3 uH); leakage, clamp and switching losses
are NOT included (optimistic on delivered power, i.e. pessimistic for over-voltage faults).
Cross-check against the switching ngspice model: see validation/sim/cycle_model/results.md.

Usage: python3 scripts/sim_flyback_cycle.py      -> validation/sim/cycle_model/results.md, figures
"""
import math
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "validation", "sim", "cycle_model")
FIG = os.path.join(ROOT, "docs", "report", "figures")

FSW = 298e3
T = 1 / FSW
LP, N, VF, RSEC = 7.3e-6, 5.0, 0.85, 0.35
LS = N * N * LP
RS = 0.022
COUT = 1.8e-6 * 2 + 47e-6 + 100e-6          # C309, C310 (DC-bias derated as in the SPICE runs), C311, C702
R307, R308 = 470e3, 10e3
CSS_NEW = 2.2e-6                              # corrected C305 (section 1 of results.md)
TF = 0.5                                      # fault time, after PGOOD with CSS_NEW


def simulate(vin=3.0, t_end=0.5, load=lambda t, v: 8000.0, css=47e-9, iss=10e-6, vref=1.0, vclth=0.100,
             gcomp=0.142, voff=1.0, dmax=0.90, ton_min=140e-9, fb_open_at=None, ovp=None, sample=20,
             v0=0.0, enable_hiccup=True):
    """ovp = (trip_V, delay_s) for the proposed independent latched OVP on FLY_EN, or None."""
    gm, ro, isrc = 2e-3, 10e6, 180e-6
    r303, c306, c307 = 3.01e3, 180e-9, 3.3e-9
    vout, im, vss, vcomp, vcrc = v0, 0.0, 0.0, 1.0, 1.0
    cnt = good = 0
    hic_left = 0
    ov = False
    ovp_lat = False
    ovp_pending = None
    pgood_t = None
    hiccups = []
    ts, vs, cs, ss = [], [], [], []
    ncyc = int(t_end / T)
    vmax = vout
    first = {}
    ein = 0.0
    sub = 8
    dt = T / sub
    for k in range(ncyc):
        t = k * T
        fb = 0.0 if (fb_open_at is not None and t >= fb_open_at) else vout * R308 / (R307 + R308)
        # independent OVP (latched): pulls FLY_EN to ~0 V -> UVLO/EN low -> standby, SS discharged
        if ovp is not None and not ovp_lat:
            if vout > ovp[0] and ovp_pending is None:
                ovp_pending = t + ovp[1]
            if ovp_pending is not None and t >= ovp_pending:
                ovp_lat = True
                first.setdefault("ovp_trip", t)
        # internal OVP on FB
        if fb > 1.10 * vref:
            ov = True
        elif fb < 1.05 * vref:
            ov = False
        enabled = (not ovp_lat) and hic_left == 0
        ton = 0.0
        cl = False
        if enabled and not ov:
            slope_i = vin / LP
            denom = RS * slope_i + 0.04 / T
            t_pwm = (gcomp * (vcomp - voff) - RS * im) / denom
            t_cl = (vclth / RS - im) / slope_i
            ton = min(t_pwm, t_cl, dmax * T)
            ton = max(ton, ton_min)
            cl = t_cl <= ton + 1e-12
        ip = im + vin / LP * ton
        ein += vin * 0.5 * (im + ip) * ton
        # off phase on the secondary
        toff = T - ton
        isec = ip / N
        q = 0.0
        if isec > 0:
            vsec = vout + VF + 0.5 * isec * RSEC
            tz = isec * LS / max(vsec, 1e-3)
            if tz <= toff:
                q = 0.5 * isec * tz
                im = 0.0
            else:
                iend = isec - vsec / LS * toff
                q = 0.5 * (isec + iend) * toff
                im = iend * N
        # output capacitor with exact discharge into the load
        r = load(t, vout)
        vout = (vout + q / COUT) * math.exp(-T / (r * COUT))
        vmax = max(vmax, vout)
        for lv in (47.5, 50.4, 55.9, 60.0, 80.0, 100.0):
            if vout >= lv and lv not in first:
                first[lv] = t
        # PGOOD
        if pgood_t is None and fb > 0.95 * vref and enabled:
            pgood_t = t
        # hiccup counter (SNVSB75E 9.3.10)
        if enable_hiccup and enabled:
            if cl:
                cnt += 1
                good = 0
            elif ton > 0:
                good += 1
                if good >= 8:
                    cnt = 0
            if cnt >= 64:
                hic_left = 32768
                hiccups.append(t)
                cnt = good = 0
        elif hic_left > 0:
            hic_left -= 1
        # soft start and error amplifier
        if enabled and not ovp_lat:
            vss += iss * T / css
        else:
            vss = 0.0
        lim = 40e-6 if ov else isrc
        for _ in range(sub):
            i = max(-lim, min(lim, gm * (min(vss, vref) - fb)))
            i_r = (vcomp - vcrc) / r303
            vcomp += (i - i_r - vcomp / ro) / c307 * dt
            vcrc += i_r / c306 * dt
            vcomp = min(2.8, max(1.0, vcomp))
        if k % sample == 0:
            ts.append(t); vs.append(vout); cs.append(vcomp); ss.append(vss)
    return dict(t=np.array(ts), v=np.array(vs), comp=np.array(cs), ss=np.array(ss), vmax=vmax, vend=vout,
                pgood_t=pgood_t, hiccups=hiccups, first=first, ein=ein)


def run_all():
    os.makedirs(OUT, exist_ok=True)
    L = ["# Cycle-by-cycle flyback model results", "",
         "Generated by `scripts/sim_flyback_cycle.py`. **Model results, not measurements.** Ideal piecewise-linear",
         "flyback (no leakage, clamp or switching loss), LM51551 control per SNVSB75E, VOFF 1.0 V and DMAX 90 %",
         "assumed, T301 = specification. Load 8 kOhm = PMD401 idle ~6 mA; 480 Ohm = 100 mA.", ""]
    res = {}

    # ---- 1. soft-start capacitor vs hiccup (worst case: VCLTH 93 mV, ISS 11 uA, Vin 3.0 V) ----
    L += ["## 1. Soft start versus hiccup (C305 sweep)", "",
          "Worst case for hiccup: Vin 3.0 V, VCLTH min 93 mV, ISS max 11 uA, VREF 1.01 V. Pass = reaches PGOOD",
          "with no hiccup event.", "",
          "| C305 | tSS = C*VREF/ISS (typ) | load | hiccup events | first hiccup (ms) | PGOOD at (ms) | Vmax (V) |",
          "|---|---|---|---|---|---|---|"]
    sweep = []
    for css in (47e-9, 100e-9, 220e-9, 470e-9, 680e-9, 1e-6, 1.5e-6, 2.2e-6):
        for rl, lab in ((8000.0, "6 mA"), (480.0, "100 mA")):
            r = simulate(vin=3.0, t_end=0.6, load=lambda t, v, rl=rl: rl, css=css, iss=11e-6, vref=1.01,
                         vclth=0.093, sample=200)
            sweep.append((css, lab, r))
            L.append(f"| {css*1e9:.0f} nF | {css/10e-6*1e3:.1f} ms | {lab} | {len(r['hiccups'])} | "
                     f"{(r['hiccups'][0]*1e3) if r['hiccups'] else '-'} | "
                     f"{(r['pgood_t']*1e3) if r['pgood_t'] is not None else 'not reached'} | {r['vmax']:.2f} |")
    res["sweep"] = sweep
    L.append("")

    # ---- 2. nominal startup with present 47 nF and with the corrected value ----
    L += ["## 2. Startup, nominal parameters", "", "| Case | hiccups | PGOOD (ms) | Vmax (V) | Vend (V) |",
          "|---|---|---|---|---|"]
    for name, kw in (("47 nF, 3.0 V, 6 mA", dict(css=47e-9, vin=3.0, load=lambda t, v: 8000.0)),
                     ("47 nF, 3.0 V, 100 mA", dict(css=47e-9, vin=3.0, load=lambda t, v: 480.0)),
                     ("47 nF, 4.2 V, 6 mA", dict(css=47e-9, vin=4.2, load=lambda t, v: 8000.0)),
                     ("2.2 uF, 3.0 V, 100 mA", dict(css=CSS_NEW, vin=3.0, load=lambda t, v: 480.0)),
                     ("2.2 uF, 4.2 V, 6 mA", dict(css=CSS_NEW, vin=4.2, load=lambda t, v: 8000.0)),
                     ("2.2 uF, 4.2 V, 0 to 100 mA step at 0.4 s", dict(css=CSS_NEW, vin=4.2,
                      load=lambda t, v: 8000.0 if t < 0.4 else 480.0))):
        r = simulate(t_end=0.6, sample=100, **kw)
        if "step" in name:
            sel = r["t"] > 0.4
            name += f" (min after step {r['v'][sel].min():.2f} V)"
        res["start:" + name] = r
        L.append(f"| {name} | {len(r['hiccups'])} | {(r['pgood_t']*1e3) if r['pgood_t'] is not None else 'not reached'}"
                 f" | {r['vmax']:.2f} | {r['vend']:.2f} |")
    L.append("")

    # ---- 3. open R307 (single fault), from regulated state ----
    L += ["## 3. Single fault: R307 (FB top resistor) opens at t = 0.5 s (after PGOOD, C305 = 2.2 uF), Vin 4.2 V", "",
          "FB is pulled to 0 V by R308, so the LM51551 internal OVP (sensed on FB) cannot act. Hiccup is the only",
          "on-chip limit. 'no load' = PMD401 unpowered/disconnected and no bleeder (C leakage only, 10 MOhm).", "",
          "| Load | Independent OVP | Vmax (V) | time >50.4 V after fault (ms) | >55.9 V | >60 V | >100 V | hiccups | OVP trip (ms after fault) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for rl, lab in ((10e6, "no load"), (10e3, "bleeder R312 10k only"), (8000.0, "PMD401 idle 6 mA"),
                    (480.0, "100 mA")):
        for ovp in (None, (52.5, 10e-6), (53.1, 50e-6)):
            r = simulate(vin=4.2, t_end=TF + 3.0, load=lambda t, v, rl=rl: rl, css=CSS_NEW, fb_open_at=TF, ovp=ovp,
                         sample=200)
            res[f"openfb:{lab}:{ovp}"] = r
            f = r["first"]

            def since(x):
                return f"{(f[x]-TF)*1e3:.2f}" if x in f and f[x] >= TF else "-"
            nh = len([h for h in r["hiccups"] if h >= TF])
            trip = f"{(f['ovp_trip'] - TF) * 1e3:.3f}" if "ovp_trip" in f else "-"
            ovl = "none" if ovp is None else f"{ovp[0]} V / {ovp[1] * 1e6:.0f} us"
            L.append(f"| {lab} | {ovl} | {r['vmax']:.1f} | {since(50.4)} | {since(55.9)} | {since(60.0)} | "
                     f"{since(100.0)} | {nh} | {trip} |")
    L += ["", "Over 3 s after the fault. A rail that keeps rising in hiccup steps (no load) will exceed any rating",
          "given enough time: the hiccup ratchet only slows the runaway.", ""]

    # ---- 4. output short ----
    r = simulate(vin=3.0, t_end=TF + 0.5, load=lambda t, v: 480.0 if t < TF else 0.1, css=CSS_NEW, sample=50)
    res["short"] = r
    hs = [h for h in r["hiccups"] if h >= TF]
    L += [f"## 4. Output short (0.1 Ohm) at {TF} s, Vin 3.0 V, C305 = 2.2 uF", "",
          f"- hiccup events after the short in 0.5 s: {len(hs)}; first at {((hs[0]-TF)*1e3):.3f} ms after the short."
          if hs else "- no hiccup event after the short (unexpected - check)",
          f"- on-time per hiccup burst is 64 CL cycles = {64*T*1e6:.0f} us out of {(64+32768)*T*1e3:.1f} ms "
          f"(burst duty {64/(64+32768)*100:.2f} %), so average input current in a sustained short is far below the",
          "  2 A dosing level; peak primary current is held at VCLTH/RS = 4.2-4.9 A by the cycle-by-cycle limit.", ""]
    open(os.path.join(OUT, "results.md"), "w").write("\n".join(L))
    return res


def plots(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(9, 8))
    for key, lab in (("start:47 nF, 3.0 V, 100 mA", "C305 47 nF (10 Oct value), 100 mA"),
                     ("start:47 nF, 3.0 V, 6 mA", "C305 47 nF (10 Oct value), 6 mA"),
                     ("start:2.2 uF, 3.0 V, 100 mA", "C305 2.2 uF (corrected), 100 mA")):
        r = res[key]
        ax[0].plot(r["t"] * 1e3, r["v"], label=lab)
    ax[0].set_xlim(0, 600)
    ax[0].set_xlabel("time (ms)"); ax[0].set_ylabel("+48V_RAW (V)"); ax[0].grid(alpha=.3); ax[0].legend(fontsize=8)
    ax[0].set_title("Startup at Vin 3.0 V: hiccup lock-out with 47 nF, clean start with 2.2 uF (cycle model)")
    for key, lab in (("openfb:no load:None", "no load, no independent OVP"),
                     ("openfb:PMD401 idle 6 mA:None", "6 mA, no independent OVP"),
                     ("openfb:no load:(52.5, 1e-05)", "no load, proposed OVP 52.5 V")):
        r = res[key]
        ax[1].plot(r["t"], r["v"], label=lab)
    ax[1].set_xlim(0, TF + 3.0)
    ax[1].axhline(50.4, ls="--", c="r", lw=.8); ax[1].axhline(100, ls="--", c="r", lw=.8)
    ax[1].set_xlabel("time (s)"); ax[1].set_ylabel("+48V_RAW (V)"); ax[1].grid(alpha=.3); ax[1].legend(fontsize=8)
    ax[1].set_title(f"R307 opens at {TF} s, Vin 4.2 V, C305 2.2 uF (hiccup ratchet; cycle model)")
    fig.suptitle("Cycle-by-cycle model - simulation, not measurement", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "sim_cycle_flyback.png"), dpi=110)


if __name__ == "__main__":
    plots(run_all())
    print(open(os.path.join(OUT, "results.md")).read())
