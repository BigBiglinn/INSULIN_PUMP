"""Closed-loop BEHAVIOURAL simulation of the 48 V flyback (LM51551 peak-current-mode control) in ngspice.

Purpose: startup, load transient, open-feedback-resistor fault (with and without the PROPOSED independent
OVP of FINAL_ENGINEERING_REVIEW_2026-11-01 §2.3), output short, and stresses. This is NOT the TI model and
NOT a verified design: it is a behavioural model built only from SNVSB75E (docs/datasheets/lm51551.pdf)
numbers plus the assumptions listed below, around the same power stage as sim_flyback_ngspice.py.

Controller elements and their source
  fsw 298 kHz (RT 73.2 k, SNVSB75E Eq.5)                         [DS/CALC]
  fixed slope 40 mV per period added to CS for PWM (Eq.7)        [DS]
  PWM comparator gain GCOMP = 0.142 (Fig. 9-17)                   [DS]
  COMP-to-PWM offset 1.0 V (taken = COMP min clamp)               [ASSUMPTION - not in datasheet]
  cycle-by-cycle limit VCLTH 100 mV (93-107) on CS, no slope       [DS 9.3.7]
  tON(min) ~140 ns (Eq.12 at RT 73.2 k), also used as blanking    [DS/CALC]
  DMAX 90 % (DMAX1 85 %, DMAX2 93 % at other RT)                   [ASSUMPTION within DS range]
  error amp Gm 2 mA/V, RO 10 MOhm, +-180 uA, COMP clamp 1.0..2.8 V [DS]
  VREF 1.00 V, soft start 10 uA into C305 47 nF, ref = min(SS,VREF)[DS]
  internal OVP: FB > 110 % stops switching, < 105 % resumes        [DS 9.3.13]
  UVLO/EN: switching only while FLY_EN > 1.5 V (UVLO rising typ)   [DS]
  hiccup (64 CL cycles -> 32768 cycles off) NOT modelled           [handled by calculation]
  gate drive = VBAT (BIAS = VCC = VBAT in this design)             [design.py]
Compensation R303 3.01 k, C306 180 nF, C307 3.3 nF are the PRELIMINARY schematic values; transformer is the
SPECIFICATION (n 5, Lp 7.3 uH, k 0.99) because T301 is still a placeholder. Results therefore show
behaviour of the proposed design, not of hardware, and must be re-run with the TI model and the real T301.

Usage: python3 scripts/sim_flyback_closedloop.py [case ...]   (ngspice 42, numpy, matplotlib)
Outputs: validation/sim/ngspice_closedloop/*.cir/*.log, results.md; docs/report/figures/sim_cl_*.png
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "validation", "sim", "ngspice_closedloop")
FIG = os.path.join(ROOT, "docs", "report", "figures")

# Each case: vin, tstop, load (ohm expression), C305, R307 open time, independent OVP (trip V, delay s),
# short time, and optional initial state (ic: +48V rail, COMP, SS) for windows that start in regulation.
# COMP initial values are the steady-state values of scripts/sim_flyback_cycle.py.
CASES = {
    # 10 Oct soft start (47 nF): current limit within the first ms -> hiccup trigger (post-processed)
    "startup_3v0_100mA_css47n": dict(vin=3.0, tstop=2e-3, load="480", css="47n"),
    # corrected soft start (2.2 uF): full start-up, switching level (long run)
    # adopted C305 4.7 uF, full start-up at minimum battery with the motor parked (FW-R2), lean storage
    "startup_3v0_6mA_css4u7": dict(vin=3.0, tstop=0.55, load="8000", css="4.7u", long=True),
    "startup_3v0_100mA_css2u2": dict(vin=3.0, tstop=0.26, load="480", css="2.2u", long=True),
    # load steps from regulation
    "loadstep_3v0": dict(vin=3.0, tstop=11e-3, load="(time<3m || time>7m) ? 8000 : 480", css="2.2u",
                         ic=(48.0, 1.186, 2.0)),
    "loadstep_3v4": dict(vin=3.4, tstop=11e-3, load="(time<3m || time>7m) ? 8000 : 480", css="2.2u",
                         ic=(48.0, 1.17, 2.0)),
    # end of the soft-start ramp under full load at minimum battery, started on the ramp at 44 V (SS = 0.917 V):
    # does the soft-start charge current on top of 100 mA trip hiccup? (hiccup counted from 2 ms to skip the IC)
    "ssend_3v0_100mA_css2u2": dict(vin=3.0, tstop=30e-3, load="480", css="2.2u", ic=(44.0, 1.65, 0.9167)),
    "ssend_3v0_100mA_css3u3": dict(vin=3.0, tstop=40e-3, load="480", css="3.3u", ic=(44.0, 1.65, 0.9167)),
    "ssend_3v0_100mA_css4u7": dict(vin=3.0, tstop=55e-3, load="480", css="4.7u", ic=(44.0, 1.65, 0.9167)),
    # worst case for hiccup: VCLTH minimum 93 mV [DS]
    "ssend_3v0_100mA_css3u3_vclth93": dict(vin=3.0, tstop=40e-3, load="480", css="3.3u", ic=(44.0, 1.65, 0.9167),
                                           vclth=0.093),
    # same, but current-limit events inside the 140 ns minimum on-time (leading-edge spike) not counted for hiccup
    # (0.0417 of the period = 140 ns): bounds the effect of an internal or external leading-edge blanking
    "ssend_3v0_100mA_css2u2_vclth93_blank": dict(vin=3.0, tstop=30e-3, load="480", css="2.2u",
                                                 ic=(44.0, 1.65, 0.9167), vclth=0.093, cl_blank=0.0417),
    "ssend_3v0_100mA_css3u3_vclth93_blank": dict(vin=3.0, tstop=40e-3, load="480", css="3.3u",
                                                 ic=(44.0, 1.65, 0.9167), vclth=0.093, cl_blank=0.0417),
    # same, with the TI-recommended CS RC filter 100 ohm / 470 pF (proposal)
    "ssend_3v0_100mA_css2u2_vclth93_csf": dict(vin=3.0, tstop=30e-3, load="480", css="2.2u",
                                               ic=(44.0, 1.65, 0.9167), vclth=0.093, csfilter=("100", "470p")),
    "ssend_3v0_100mA_css3u3_vclth93_csf": dict(vin=3.0, tstop=40e-3, load="480", css="3.3u",
                                               ic=(44.0, 1.65, 0.9167), vclth=0.093, csfilter=("100", "470p")),
    # steady 100 mA at minimum battery and minimum VCLTH, without and with the CS filter
    "steady_3v0_100mA_vclth93": dict(vin=3.0, tstop=15e-3, load="480", css="2.2u", ic=(48.0, 1.63, 2.0), vclth=0.093),
    "steady_3v0_100mA_vclth93_csf": dict(vin=3.0, tstop=15e-3, load="480", css="2.2u", ic=(48.0, 1.63, 2.0),
                                         vclth=0.093, csfilter=("100", "470p")),
    # parked-motor load during start-up (FW-R2), minimum VCLTH, present circuit
    "ssend_3v0_6mA_css2u2_vclth93": dict(vin=3.0, tstop=30e-3, load="8000", css="2.2u", ic=(44.0, 1.25, 0.9167),
                                         vclth=0.093),
    # load steps with the CS filter (and at minimum VCLTH)
    "loadstep_3v0_csf": dict(vin=3.0, tstop=11e-3, load="(time<3m || time>7m) ? 8000 : 480", css="2.2u",
                             ic=(48.0, 1.186, 2.0), csfilter=("100", "470p")),
    "loadstep_3v0_vclth93_csf": dict(vin=3.0, tstop=11e-3, load="(time<3m || time>7m) ? 8000 : 480", css="2.2u",
                                     ic=(48.0, 1.186, 2.0), vclth=0.093, csfilter=("100", "470p")),
    "loadstep_3v4_csf": dict(vin=3.4, tstop=11e-3, load="(time<3m || time>7m) ? 8000 : 480", css="2.2u",
                             ic=(48.0, 1.17, 2.0), csfilter=("100", "470p")),
    "loadramp_3v0_20ms_vclth93": dict(vin=3.0, tstop=30e-3, css="2.2u", ic=(48.0, 1.186, 2.0), vclth=0.093,
                                      load="v(mot)/(6m + 94m*min(1, max(0, (time-3m)/20m)))"),
    "loadramp_3v0_20ms_vclth93_csf": dict(vin=3.0, tstop=30e-3, css="2.2u", ic=(48.0, 1.186, 2.0), vclth=0.093,
                                          load="v(mot)/(6m + 94m*min(1, max(0, (time-3m)/20m)))",
                                          csfilter=("100", "470p")),
    # tolerance corner: 2.2 uF -20 % and ISS +10 % (11 uA) -> equivalent 1.6 uF at 10 uA
    "ssend_3v0_100mA_css1u6_vclth93_csf": dict(vin=3.0, tstop=25e-3, load="480", css="1.6u",
                                               ic=(44.0, 1.65, 0.9167), vclth=0.093, csfilter=("100", "470p")),
    # 3.3 uF -20 % with ISS +10 % -> 2.4 uF equivalent
    "ssend_3v0_100mA_css2u4_vclth93_csf": dict(vin=3.0, tstop=30e-3, load="480", css="2.4u",
                                               ic=(44.0, 1.65, 0.9167), vclth=0.093, csfilter=("100", "470p")),
    # 4.7 uF -20 % with ISS +10 % -> 3.4 uF equivalent
    "ssend_3v0_100mA_css3u4_vclth93_csf": dict(vin=3.0, tstop=40e-3, load="480", css="3.4u",
                                               ic=(44.0, 1.65, 0.9167), vclth=0.093, csfilter=("100", "470p")),
    "ssend_3v0_6mA_css1u6_vclth93": dict(vin=3.0, tstop=25e-3, load="8000", css="1.6u", ic=(44.0, 1.25, 0.9167),
                                         vclth=0.093),
    "ssend_3v0_100mA_css4u7_vclth93": dict(vin=3.0, tstop=55e-3, load="480", css="4.7u", ic=(44.0, 1.65, 0.9167),
                                           vclth=0.093),
    # same 100 mA demand reached by a 20 ms ramp (firmware acceleration limit) instead of a step
    "loadramp_3v0_20ms": dict(vin=3.0, tstop=30e-3, css="2.2u", ic=(48.0, 1.186, 2.0),
                              load="v(mot)/(6m + 94m*min(1, max(0, (time-3m)/20m)))"),
    "loadstep_4v2": dict(vin=4.2, tstop=11e-3, load="(time<3m || time>7m) ? 8000 : 480", css="2.2u",
                         ic=(48.0, 1.156, 2.0)),
    # R307 opens at 1 ms in regulation (hiccup trigger expected within ~0.3 ms)
    "openfb_4v2_idle": dict(vin=4.2, tstop=2e-3, load="8000", css="2.2u", fb_open=1e-3, ic=(48.0, 1.156, 2.0)),
    # proposed independent OVP: R307 already open, rail starts just below the trip point
    "ovptrip_4v2_52v5_10us": dict(vin=4.2, tstop=1.5e-3, load="10e6", css="2.2u", fb_open=0.0, ovp=(52.5, 10e-6),
                                  ic=(52.0, 2.79, 2.0)),
    "ovptrip_4v2_53v1_50us": dict(vin=4.2, tstop=1.5e-3, load="10e6", css="2.2u", fb_open=0.0, ovp=(53.1, 50e-6),
                                  ic=(52.6, 2.79, 2.0)),
    # output short at 1 ms from regulation
    "short_3v0": dict(vin=3.0, tstop=1.6e-3, load="480", css="2.2u", short=1e-3, ic=(48.0, 1.628, 2.0)),
}
DEFAULTS = dict(css="2.2u", fb_open=None, ovp=None, short=None, ic=None, long=False, r306="220", c308="470n",
                vclth=0.100, cl_blank=0.0, csfilter=None)

NET = """* Piezo Insulin Pump v2 - 48 V flyback, CLOSED-LOOP BEHAVIOURAL LM51551 model ({name})
* see scripts/sim_flyback_closedloop.py header for every parameter source and assumption
.param vin={vin} tsw={{1/298k}}
V1 vsrc 0 {vin}
R1s vsrc vin 20m
C1 vin c1n 220u
R1c c1n 0 80m
C2 vin c2n 20u
R2c c2n 0 3m
* ---- transformer specification (T301 placeholder) ----
Lp vin lpn 7.3u
Rlp lpn sw 15m
Ls 0 lsn 182.5u
Rls lsn sec 0.35
K1 Lp Ls 0.99
M1 sw g cs cs QCSD
Rs cs 0 22m
* CS pin node (optional RC filter)
{cs_filter}Dc sw clamp DSCH
* RCD clamp: R306/C308 as in design.py (re-tuned 1 Nov from 390 ohm / 22 nF; cases marked 'oldclamp' keep those)
Rc clamp vin {r306}
Cc clamp vin {c308}
D1 sec out DHF
Rsn sec snb 220
Csn snb out 100p
* ---- +48V_RAW (C309, C310, C311) -> R311 0R -> +48V_MOT (C702) ----
C3 out c3n 1.8u
R3c c3n 0 5m
C3b out c3bn 1.8u
R3bc c3bn 0 5m
C4 out c4n 47u
R4c c4n 0 0.3
R311 out mot 1m
C702 mot c7n 100u
R7c c7n 0 0.2
Bload mot 0 I=v(mot)/({load_expr})
* ---- feedback divider R307/R308 (R307 may open) ----
Bfb out fb I=(v(out)-v(fb))/({r307_expr})
R308 fb 0 10k
* ---- LM51551 behavioural controller ----
Vramp ramp 0 PULSE(0 1 0 {{tsw-10n}} 10n 0 {{tsw}})
* UVLO/EN = FLY_EN: R402 1k from main MCU (3.3 V), R401 4.7k pull-down
Vmcu mcu 0 3.3
R402 mcu en 1k
R401 en 0 4.7k
Benok enok 0 V=v(en) > 1.5 ? 1 : 0
* soft start: 10 uA into C305 47 nF, 55 ohm discharge when disabled
Bss 0 ss I=v(enok) > 0.5 ? 10u : -v(ss)/55
C305 ss 0 {css}
* internal OVP with hysteresis (110 % / 105 %)
Bov ov 0 V=v(fb) > 1.10 ? 1 : (v(fb) < 1.05 ? 0 : (v(ovd) > 0.5 ? 1 : 0))
Rov ov ovd 1k
Cov ovd 0 1p
* error amplifier: Gm 2 mA/V, +-180 uA (40 uA during OVP), RO 10 Mohm, clamp 1.0..2.8 V
Bea 0 comp I=max(min(2m*(min(v(ss),1.0)-v(fb)), v(ovd) > 0.5 ? 40u : 180u), v(ovd) > 0.5 ? -40u : -180u)
Ro comp 0 10meg
R303 comp crc 3.01k
C306 crc 0 180n
C307 comp 0 3.3n
* COMP clamps 1.0 / 2.8 V as a stiff piecewise-linear conductance (100 ohm beyond the clamp)
Bclamp comp 0 I=v(comp) > 2.8 ? (v(comp)-2.8)/100 : (v(comp) < 1.0 ? (v(comp)-1.0)/100 : 0)
* PWM latch: set at period start (tON(min)/blanking 140 ns = ramp < 0.0417), reset by PWM compare, CL or DMAX
Bset set 0 V=v(ramp) < 0.0417 ? 1 : 0
Brst rst 0 V=((v(csp) + 0.04*v(ramp) > 0.142*(v(comp)-1.0)) || (v(csp) > {vclth}) || (v(ramp) > 0.9)) ? 1 : 0
Bq q 0 V=(v(enok) < 0.5 || v(ovd) > 0.5) ? 0 : ((v(set) > 0.5) ? 1 : ((v(rst) > 0.5) ? 0 : (v(qd) > 0.5 ? 1 : 0)))
Rq q qd 100
Cq qd 0 10p
Bcl cl 0 V=(v(csp) > {vclth}) ? 1 : 0
* per-period current-limit flag (set by CL, cleared at period start) for the hiccup post-processor
Bclf clf 0 V=(v(cl) > 0.5 && v(ramp) > {cl_blank}) ? 1 : ((v(ramp) < 0.01) ? 0 : (v(clfd) > 0.5 ? 1 : 0))
Rclf clf clfd 100
Cclf clfd 0 10p
Bg gd 0 V=v(qd) > 0.5 ? {vin} : 0
Rg gd g 2
{ovp_block}
.model QCSD VDMOS(Vto=1.1 Kp=40 Rd=2.5m Rs=1m Rg=1 Cgs=0.9n Cgdmax=0.6n Cgdmin=0.08n Cjo=0.6n Is=1e-12 BV=25)
.model DSCH D(Is=2u Rs=40m N=1.15 Cjo=60p BV=100)
.model DHF D(Is=5n Rs=60m N=1.6 Cjo=15p Tt=15n BV=200)
.model DCL D(Is=1e-12 N=0.2)
.options method=gear reltol=1e-3 itl4=50
{long_opts}
.tran {tstep} {tstop} 0 10n {uic}
{ic_line}
{meas}
.control
run
set wr_singlescale
set wr_vecnames
linearize v(out) v(comp) v(ss) v(clfd) i(Lp)
wrdata {wave} v(out) v(comp) v(ss) v(clfd) i(Lp)
.endc
.end
"""

OVP_BLOCK = """* PROPOSED independent OVP (FINAL_ENGINEERING_REVIEW §2.3): own sense of +48V_RAW, latch, open-drain on FLY_EN
* trip {trip} V, total detection+propagation delay {td} s modelled as RC to 50 % (ASSUMPTION)
Bovp op 0 V=(v(out) > {trip} || v(opd) > 0.5) ? 1 : 0
Ropd op opd 1k
Copd opd 0 {cdel}
Bpd en 0 I=v(opd) > 0.5 ? v(en)/10 : 0
"""


def meas_lines(c):
    te = c["tstop"]
    t0 = max(0.0, te - 1e-3)
    L = [f".meas tran vout_end AVG v(mot) FROM={t0} TO={te}",
         ".meas tran vout_max MAX v(out)",
         ".meas tran ipri_max MAX i(Lp)",
         ".meas tran vds_max MAX v(sw)",
         ".meas tran vd1_max MAX par('v(out)-v(sec)')",
         f".meas tran iin_end AVG i(V1) FROM={t0} TO={te}"]
    if c["ic"] is None:
        L.append(".meas tran t_reg WHEN v(mot)=47.5 RISE=1")
    if c["name"].startswith("loadramp"):
        L += [".meas tran vmin_ramp MIN v(mot) FROM=3m TO=30m", ".meas tran vpre AVG v(mot) FROM=2m TO=3m",
              ".meas tran vend_100mA AVG v(mot) FROM=28m TO=30m", ".meas tran iin_100mA AVG i(V1) FROM=28m TO=30m"]
    if c["name"].startswith("loadstep"):
        L += [".meas tran vpre AVG v(mot) FROM=2m TO=3m", ".meas tran vmin_step MIN v(mot) FROM=3m TO=7m",
              ".meas tran vmax_unload MAX v(mot) FROM=7m TO=11m", ".meas tran vpp_100mA PP v(mot) FROM=6m TO=7m",
              ".meas tran iin_100mA AVG i(V1) FROM=6m TO=7m", ".meas tran pout_100mA AVG par('v(mot)*v(mot)/480') FROM=6m TO=7m"]
    if c["name"].startswith("ssend"):
        L += [f".meas tran vpp_end PP v(mot) FROM={t0} TO={te}", ".meas tran t_reg47 WHEN v(mot)=47.5 RISE=1"]
    if c["name"].startswith("startup") and te > 0.1:
        L += [f".meas tran vpp_end PP v(mot) FROM={t0} TO={te}",
              f".meas tran pout_end AVG par('v(mot)*v(mot)/480') FROM={t0} TO={te}"]
    if c["fb_open"] is not None:
        L.append(f".meas tran vds_max_fault MAX v(sw) FROM={c['fb_open']} TO={te}")
        L.append(f".meas tran vd1_max_fault MAX par('v(out)-v(sec)') FROM={c['fb_open']} TO={te}")
    if c["short"] is not None:
        L += [f".meas tran ipri_max_short MAX i(Lp) FROM={c['short']} TO={te}",
              f".meas tran vds_max_short MAX v(sw) FROM={c['short']} TO={te}",
              f".meas tran vd1_max_short MAX par('v(out)-v(sec)') FROM={c['short']} TO={te}"]
    if c["ovp"] is not None:
        L += [".meas tran t_trip WHEN v(opd)=0.5 RISE=1", ".meas tran t_en_low WHEN v(en)=1.45 FALL=1",
              ".meas tran vout_max_after MAX v(out)"]
    return "\n".join(L)


def build(name, c):
    c = dict(DEFAULTS, **c, name=name)
    load = c["load"]
    if c["short"] is not None:
        load = f"(time < {c['short']}) ? ({load}) : 0.1"
    c["load_expr"] = load
    r307 = "470k" if c["fb_open"] is None else f"(time < {c['fb_open']}) ? 470k : 1e9"
    ovp = ""
    if c["ovp"]:
        trip, td = c["ovp"]
        ovp = OVP_BLOCK.format(trip=trip, td=td, cdel=f"{td / 0.693 / 1e3:.4g}")
    wave = os.path.join(OUT, f"wave_{name}.txt")
    uic, ic_line = "", ""
    if c["ic"] is not None:
        v0, comp0, ss0 = c["ic"]
        vin = c["vin"]
        uic = "uic"
        ic_line = (f".ic v(out)={v0} v(mot)={v0} v(snb)={v0} v(fb)={v0 * 10 / 480:.4f} v(comp)={comp0} v(crc)={comp0} "
                   f"v(ss)={ss0} v(vin)={vin} v(vsrc)={vin} v(clamp)={vin + 15} v(en)=2.72 v(mcu)=3.3")
    # long runs: store only the needed vectors, interpolated to a 50 ns grid (a 260 ms run otherwise exhausts
    # memory); peak measurements of such a run are therefore on the 50 ns grid
    if c["csfilter"]:
        # TI-recommended CS RC filter (SNVSB75E 9.3.7: RF 10-200 ohm, CF 100 pF-2 nF; 3 RF CF < (1-D)/fsw)
        rf, cf = c["csfilter"]
        net_cs = f"Rcsf cs csp {rf}\nCcsf csp 0 {cf}\n"
    else:
        net_cs = "Rcsf cs csp 1m\n"
    long_opts = (".options interp\n.save v(out) v(mot) v(comp) v(ss) v(clfd) v(sw) v(sec) v(cl) i(Lp) i(V1) v(en)"
                 if c["long"] else "")
    tstep = "50n" if c["long"] else "100n"
    return c, NET.format(cs_filter=net_cs, cl_blank=c["cl_blank"], r306=c["r306"], c308=c["c308"], vclth=c["vclth"], long_opts=long_opts, tstep=tstep, uic=uic, ic_line=ic_line, name=name, vin=c["vin"], load_expr=load, r307_expr=r307, ovp_block=ovp,
                         tstop=c["tstop"], meas=meas_lines(c), wave=wave,
                         css=c["css"])


def run_case(name):
    c, net = build(name, CASES[name])
    cir = os.path.join(OUT, f"cl_{name}.cir")
    log = os.path.join(OUT, f"cl_{name}.log")
    open(cir, "w").write(net)
    p = subprocess.run(["ngspice", "-b", "-o", log, cir], capture_output=True, text=True, timeout=7200)
    txt = open(log).read() if os.path.exists(log) else p.stdout + p.stderr
    meas = {}
    for m in re.finditer(r"^(\w+)\s*=\s*([-+0-9.eE]+)", txt, re.M):
        meas[m.group(1).lower()] = float(m.group(2))
    for m in re.finditer(r"^(\w+)\s*=\s*failed", txt, re.M):
        meas[m.group(1).lower()] = None
    ok = "simulation(s) aborted" not in txt and "Timestep too small" not in txt
    return name, c, meas, ok


def plot(results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def load(name):
        f = os.path.join(OUT, f"wave_{name}.txt")
        if not os.path.exists(f):
            return None
        a = np.loadtxt(f, skiprows=1)
        return a  # columns: t, v(out), v(comp), v(ss), clf, i(Lp)

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    a = load("startup_3v0_6mA_css4u7")
    if a is not None:
        ax[0, 0].plot(a[:, 0] * 1e3, a[:, 1], label="C305 4.7 uF (adopted), 6 mA (motor parked)")
    a = load("startup_3v0_100mA_css2u2")
    if a is not None:
        ax[0, 0].plot(a[:, 0] * 1e3, a[:, 1], label="C305 2.2 uF, 100 mA (hiccup at 214 ms*)")
    a = load("startup_3v0_100mA_css47n")
    if a is not None:
        ax[0, 0].plot(a[:, 0] * 1e3, a[:, 1], label="C305 47 nF (hiccup triggers <1 ms)")
    ax[0, 0].set_xlabel("time (ms)"); ax[0, 0].set_ylabel("+48V_RAW (V)"); ax[0, 0].legend(fontsize=8)
    ax[0, 0].set_title("Start-up, Vin 3.0 V (*trace invalid after hiccup time)", fontsize=9); ax[0, 0].grid(alpha=.3)
    for name, lab in (("loadstep_3v0", "step, Vin 3.0 V (hiccup at 6.1 ms*)"), ("loadstep_3v4", "step, Vin 3.4 V (hiccup*)"),
                      ("loadstep_4v2", "step, Vin 4.2 V"), ("loadramp_3v0_20ms", "20 ms ramp, Vin 3.0 V")):
        a = load(name)
        if a is not None:
            m = a[:, 0] < 11e-3
            ax[0, 1].plot(a[m, 0] * 1e3, a[m, 1], label=lab)
    ax[0, 1].set_xlabel("time (ms)"); ax[0, 1].set_ylabel("+48V_RAW (V)"); ax[0, 1].legend(fontsize=7)
    ax[0, 1].set_title("6 mA -> 100 mA at 3 ms (step back at 7 ms)\n*hiccup not modelled: trace invalid after it",
                       fontsize=9)
    ax[0, 1].grid(alpha=.3)
    a = load("openfb_4v2_idle")
    if a is not None:
        ax[1, 0].plot(a[:, 0] * 1e3, a[:, 1])
    ax[1, 0].set_xlabel("time (ms)"); ax[1, 0].set_ylabel("+48V_RAW (V)"); ax[1, 0].grid(alpha=.3)
    ax[1, 0].set_title("R307 opens at 1 ms, Vin 4.2 V, 6 mA (valid until hiccup trigger)")
    for name, lab in (("ovptrip_4v2_52v5_10us", "trip 52.5 V, 10 us"), ("ovptrip_4v2_53v1_50us", "trip 53.1 V, 50 us")):
        a = load(name)
        if a is not None:
            ax[1, 1].plot(a[:, 0] * 1e3, a[:, 1], label=lab)
    ax[1, 1].axhline(55.9, ls="--", c="r", lw=.8)
    ax[1, 1].set_xlabel("time (ms)"); ax[1, 1].set_ylabel("+48V_RAW (V)"); ax[1, 1].legend(fontsize=8)
    ax[1, 1].set_title("Proposed independent OVP, R307 open, no load"); ax[1, 1].grid(alpha=.3)
    fig.suptitle("Behavioural closed-loop switching model (not TI model, T301 = specification) - simulation, "
                 "not measurement", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "sim_cl_flyback.png"), dpi=110)

    a = load("short_3v0")
    if a is not None:
        fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
        m = (a[:, 0] > 0.95e-3)
        ax[0].plot(a[m, 0] * 1e3, a[m, 1]); ax[0].set_ylabel("+48V_RAW (V)"); ax[0].grid(alpha=.3)
        ax[1].plot(a[m, 0] * 1e3, a[m, 5]); ax[1].set_ylabel("primary current (A)")
        ax[1].axhline(0.1 / 0.022, ls="--", c="r", lw=0.8); ax[1].set_xlabel("time (ms)"); ax[1].grid(alpha=.3)
        ax[0].set_title("Output short (0.1 ohm) at 1 ms, Vin 3.0 V: cycle-by-cycle limit (hiccup not modelled)")
        fig.tight_layout(); fig.savefig(os.path.join(FIG, "sim_cl_short.png"), dpi=110)


def hiccup_trigger(name, t_from=0.0):
    """Apply the SNVSB75E 9.3.10 hiccup rule (64 current-limit cycles; counter reset by 8 consecutive clean
    cycles) to the per-period CL flag exported by the simulation. Returns the first trigger time or None."""
    f = os.path.join(OUT, f"wave_{name}.txt")
    a = np.loadtxt(f, skiprows=1)
    t, flag = a[:, 0], a[:, 4]
    tsw = 1 / 298e3
    k = np.floor(t / tsw).astype(int)
    ph = t / tsw - k
    sel = (ph > 0.05) & (t >= t_from)
    nper = k.max() + 1
    fl = np.zeros(nper, bool)
    np.maximum.at(fl, k[sel], flag[sel] > 0.5)
    seen = np.zeros(nper, bool)
    seen[k[sel]] = True
    cnt = good = 0
    for i in np.nonzero(seen)[0]:
        if fl[i]:
            cnt += 1
            good = 0
        else:
            good += 1
            if good >= 8:
                cnt = 0
        if cnt >= 64:
            return (i + 1) * tsw
    return None


def fmt(v, nd=3):
    if v is None:
        return "not reached"
    return f"{v:.{nd}g}"


def report(results):
    L = ["# Closed-loop behavioural flyback simulation (ngspice)", "",
         "Generated by `scripts/sim_flyback_closedloop.py`. **Simulation of a behavioural model, not a measurement and",
         "not the TI model.** Controller parameters from SNVSB75E; COMP offset 1.0 V and DMAX 90 % are assumptions;",
         "T301 is the specification (n 5, Lp 7.3 uH, k 0.99); compensation is the PRELIMINARY schematic value.",
         "The proposed independent OVP is modelled as an ideal latch with the stated trip and delay.", "",
         f"ngspice: `{subprocess.run(['ngspice', '-v'], capture_output=True, text=True).stdout.strip().splitlines()[1].strip() if True else ''}`", "",
         "| Case | Converged | Result |", "|---|---|---|"]
    for name, c, m, ok in results:
        try:
            m["hiccup_trigger_t"] = hiccup_trigger(name, 2e-3 if name.startswith("ssend") else 0.0) if ok else None
        except Exception:
            m["hiccup_trigger_t"] = None
        bits = [f"C305={c['css']}"]
        for k in sorted(m):
            v = m[k]
            if k == "stack":
                continue
            unit = "s" if (k.startswith("t_") or k.endswith("_t")) and v is not None else ""
            bits.append(f"{k}={fmt(v, 4)}{unit}")
        state = "yes" if ok else ("NO RESULT (run incomplete)" if ok is None else "NO (do not use)")
        L.append(f"| {name} | {state} | {'; '.join(bits)} |")
    L += ["", "Keys: vout_* = +48V_MOT/+48V_RAW (V); ipri = primary current (A); vds = Q301 drain (V); vd1 = D301 reverse",
          "(V); iin = battery current (A, negative = drawn); t_reg = time to reach 47.5 V; t_50v4 etc = time the rail first",
          "crosses that voltage; cl_frac = fraction of time CS is above VCLTH; t_trip = independent-OVP latch time;",
          "hiccup_trigger_t = time at which the LM51551 hiccup counter (64 CL cycles, reset by 8 clean cycles, SNVSB75E",
          "9.3.10) would first stop the converter. Hiccup itself is not modelled, so **every waveform after",
          "hiccup_trigger_t is not valid** (the real device would stop switching for 32 768 cycles = 110 ms).", ""]
    open(os.path.join(OUT, "results.md"), "w").write("\n".join(L))


def parse_case(name):
    """Re-read an existing log (used by --report so the long cases need not be re-run)."""
    c, _ = build(name, CASES[name])
    txt = open(os.path.join(OUT, f"cl_{name}.log")).read()
    meas = {}
    for m in re.finditer(r"^(\w+)\s*=\s*([-+0-9.eE]+)", txt, re.M):
        meas[m.group(1).lower()] = float(m.group(2))
    ok = "simulation(s) aborted" not in txt and "Timestep too small" not in txt
    if "Total elapsed time" not in txt and not meas:
        ok = None                                  # run still in progress or killed: no result
    return name, c, meas, ok


def main():
    """python3 sim_flyback_closedloop.py            run every case, then write results.md and figures
       python3 sim_flyback_closedloop.py a b        run only cases a, b
       python3 sim_flyback_closedloop.py --report   rebuild results.md and figures from existing logs"""
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[1:]
    if args == ["--report"]:
        results = [parse_case(n) for n in CASES]
    else:
        names = args or list(CASES)
        with ThreadPoolExecutor(max_workers=min(len(names), os.cpu_count() or 2)) as ex:
            results = list(ex.map(run_case, names))
    for name, c, m, ok in results:
        print(name, "OK" if ok else "FAILED", m)
    if not args or args == ["--report"]:
        report(results)
        plot(results)


if __name__ == "__main__":
    main()
