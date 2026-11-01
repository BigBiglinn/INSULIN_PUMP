"""Fault-response timing model for motor runaway (S-06: overrun after a fault must stay < 0.5 U), covering the
PROPOSED supervisor-controlled SPI gate (FINAL_ENGINEERING_REVIEW_2026-11-01 §2.4), the existing 48 V veto
(kill path), supervisor failure and power loss. CALCULATION, not a demonstration: no circuit, firmware or
hardware exists for the SPI gate or the rate check, and several inputs are not guaranteed by any datasheet.

Usage: python3 scripts/runaway_timing.py > validation/logs/runaway_timing.txt
"""
import math

# ---- inputs (source) -----------------------------------------------------------------------------------------
BORE = 4.61                       # mm, Hamilton 81320 bore [REPO DESIGN_REQUIREMENTS §2]
AREA = math.pi * (BORE / 2) ** 2  # mm^2 -> 1 mm^2 x 1 um = 1 nL
UM_PER_U = 10_000 / AREA          # 1 U = 10 uL
BUDGET_UM = 0.5 * UM_PER_U        # S-06
ENC_UM = 0.080                    # LL06 E2 encoder 80 nm/count [DS LL06]
V_TOP = 15.0                      # mm/s, LL06 no-load top speed [DS LL06]
V_PMD = 7.5                       # mm/s, PMD401 1500 Hz x 5 um [DS PMD401 manual]
V_CAP = 15 * 4.5e-3               # mm/s, firmware speed cap 15 steps/s x 4.5 um (D-08)
T_SPI_TIMEOUT = (10e-3, 5e-3, 20e-3)  # s, PMD401 "about 10 ms" [DS] - not a guaranteed max: 5-20 ms band ASSUMED
T_FAST, N_FAST = 1e-3, 10         # proposed fast tier: every 1 ms, block if > 10 counts/ms [PROPOSAL]
T_SLOW, K_SLOW = 100e-3, 1.5      # proposed slow tier: every 100 ms, block above 1.5 x cap [PROPOSAL]
T_GATE = 1e-6                     # OR-gate + GPIO latency, negligible [ASSUMPTION]
T_IWDG = (10e-3, 100e-3)          # supervisor IWDG timeout range to be configured [ASSUMPTION, firmware]
C_RAIL = 151.4e-6                 # F, +48 V rail nominal [design.py]
E_RAIL = 0.5 * C_RAIL * 48.0 ** 2  # J, stored energy at 48 V
P_MOTOR = (2.0, 7.5)              # W drawn by PMD401+LL06 while running fast [ASSUMPTION: converter max ~7.5 W]
D_DECEL_UM = "unknown"            # deceleration distance after the PMD401 stops: measure on bench (SG-06)

rows = []


def add(scn, speed, t_detect, t_stop, note):
    d = speed * 1e3 * (t_detect + t_stop)          # um
    rows.append((scn, speed, t_detect * 1e3, t_stop * 1e3, d, d / UM_PER_U, d < BUDGET_UM, note))


def fast_detect(v):
    """worst-case detection latency of the 1 ms tier: one full window plus the window in which the rate rises"""
    counts_per_ms = v * 1e3 / ENC_UM / 1e3        # v mm/s -> counts/ms
    if counts_per_ms > N_FAST:
        return 2 * T_FAST
    return None


def slow_detect(v):
    if v > K_SLOW * V_CAP:
        return 2 * T_SLOW
    return None


for v in (V_TOP, V_PMD, 0.8, 0.79, 0.2, K_SLOW * V_CAP * 1.01):
    td = fast_detect(v)
    tier = "fast"
    if td is None:
        td = slow_detect(v)
        tier = "slow"
    if td is None:
        add(f"main-MCU runaway at {v:.3g} mm/s", v, float("nan"), 0, "below both thresholds: not detected (<= 1.5x cap)")
        continue
    for to, lab in zip(T_SPI_TIMEOUT, ("timeout 10 ms (typ)", "timeout 5 ms", "timeout 20 ms (assumed max)")):
        add(f"main-MCU runaway at {v:.3g} mm/s, {tier} tier", v, td + T_GATE, to, f"SPI gate; {lab}")

# supervisor hangs with gate released, then the main MCU runs away (DOUBLE fault)
for iw in T_IWDG:
    add(f"supervisor hang + runaway (double fault), IWDG {iw*1e3:.0f} ms", V_TOP, iw, T_SPI_TIMEOUT[2],
        "IWDG reset -> GPIO hi-Z -> pull-up blocks SS")
# supervisor in reset / unpowered at the start: gate blocked by pull-up -> no motion possible
add("supervisor in reset or unpowered", V_TOP, 0.0, 0.0, "pull-up keeps SS high: no SPI frame reaches PMD401")
# power loss: 3V3 collapses, SS floats high via PMD401 internal ~20 k pull-up; motor runs at most until timeout
add("battery disconnect / 3V3 loss during normal dosing (at cap)", V_CAP, 0.0, T_SPI_TIMEOUT[2],
    "SS high via PMD401 pull-up -> timeout; also 48 V collapses")
add("3V3 loss during a runaway (double fault)", V_TOP, 0.0, T_SPI_TIMEOUT[2], "as above")
# PMD401 internal fault (drives without SPI): only the 48 V veto + stored energy limit it
for p in P_MOTOR:
    t_e = E_RAIL / p
    add(f"PMD401 drives without SPI (veto only), P={p} W", V_TOP, 2 * T_FAST, t_e,
        f"stored rail energy {E_RAIL*1e3:.0f} mJ / P (upper bound, PMD401 min supply unknown)")
# proposed combination: SPI block AND 48 V veto together (both outputs on one trip)
for p in P_MOTOR:
    add(f"SPI gate + veto together, runaway 15 mm/s, P={p} W", V_TOP, 2 * T_FAST,
        min(T_SPI_TIMEOUT[2], E_RAIL / p), "stop = earlier of SPI timeout (20 ms max assumed) and rail exhaustion")
# park-only (existing Rev A behaviour, no SPI gate)
add("no SPI gate: park command only (250 ms)", V_TOP, 2 * T_FAST, 0.250, "fails S-06 above ~1.2 mm/s")

print("Runaway fault-response timing (CALCULATED - no hardware, gate or firmware exists)")
print(f"1 U = {UM_PER_U:.1f} um travel; S-06 budget 0.5 U = {BUDGET_UM:.1f} um; encoder 80 nm/count; "
      f"deceleration distance after stop: {D_DECEL_UM} (not included)")
print(f"{'scenario':62s} {'v mm/s':>7s} {'detect ms':>9s} {'stop ms':>8s} {'overrun um':>10s} {'U':>6s} {'<0.5U':>6s}  note")
for scn, v, td, ts, d, u, ok, note in rows:
    tds = "  n/a" if math.isnan(td) else f"{td:9.2f}"
    ds = "   n/a" if math.isnan(d) else f"{d:10.1f}"
    us = "  n/a" if math.isnan(u) else f"{u:6.3f}"
    oks = "  -" if math.isnan(d) else ("  yes" if ok else "   NO")
    print(f"{scn:62s} {v:7.3g} {tds:>9s} {ts:8.2f} {ds:>10s} {us:>6s} {oks:>6s}  {note}")
