"""Recompute every calculated figure in docs/report/PROJECT_ENGINEERING_REPORT.md from its stated inputs
(final engineering review, 1 Nov 2026). Prints input -> result with the source of each input.

Usage: python3 scripts/audit_calcs.py > validation/logs/report_audit_calcs.txt
No external data: every input below is quoted from a repository document or datasheet (source given).
"""
import math

rows = []


def row(name, value, unit, how, src):
    rows.append((name, value, unit, how, src))


# --- syringe / dose (DESIGN_REQUIREMENTS §2) -------------------------------------------------
bore = 4.61                                            # mm, Hamilton 81320 [REPO]
area = math.pi * (bore / 2) ** 2
row("Plunger area", area, "mm^2", "pi*(4.61/2)^2", "DESIGN_REQUIREMENTS §2")
nl_per_um = area                                       # 1 mm^2 x 1 um = 1 nL
um_per_U = 10_000 / nl_per_um                          # 1 U = 10 uL = 10 000 nL
row("Travel per 1 U", um_per_U, "um", "10 uL / area", "D-03")
row("Counts per 1 U (80 nm)", um_per_U / 0.08, "counts", "travel / 0.08 um", "LL06 E2 encoder")
row("0.05 U travel", 0.05 * um_per_U, "um", "", "D-05")
row("Volume per count", 0.08 * nl_per_um, "nL", "0.08 um x area", "")
row("Full 60 mm stroke", 60_000 * nl_per_um / 1e6, "mL", "", "D-04")
row("Speed cap 15 steps/s x 4.5 um", 15 * 4.5, "um/s", "", "D-08, LL06 no-load step")
row("Speed cap in U/s", 15 * 4.5 / um_per_U, "U/s", "", "")
row("Force at 1 bar", 0.1 * area, "N", "0.1 N/mm^2 x area", "")
row("Pressure at 6.5 N stall", 6.5 / area * 10, "bar", "", "LL06 6.5 N")

# --- flyback (FLYBACK_DESIGN, SNVSB75E) ------------------------------------------------------
n, vout, vf = 5, 48.0, 0.85                            # vf: PNE20010ER ~0.85 V at 1 A [DS typ 845 mV]
for vin in (3.0, 4.2):
    k = (vout + vf) / (n * vin)
    row(f"Duty D at Vin={vin} V (CCM)", k / (1 + k), "-", "(Vout+Vf)/(n Vin) = D/(1-D)", "FLYBACK_DESIGN §2")
row("Plain-boost duty 3.0->48 V", 1 - 3.0 / 48, "-", "1 - Vin/Vout (lossless)", "")
row("RT for 298 kHz", 2.21e10 / 298e3 - 955, "ohm", "2.21e10/fsw - 955", "SNVSB75E Eq. 5")
pin = 4.8 / 0.8
iin = pin / 3.0
d3 = ((vout + vf) / 15) / (1 + (vout + vf) / 15)
ipri = iin / d3
row("Primary avg during on-time (3.0 V)", ipri, "A", "Iin / D", "")
row("Lp for 40 % ripple", 3.0 * d3 / (0.4 * ipri * 298e3) * 1e6, "uH", "Vin D / (dI fsw)", "")
row("Primary peak (calc)", ipri * 1.2, "A", "Iavg + dI/2", "")
row("Current limit min", 0.093 / 0.022, "A", "93 mV / 22 mohm", "SNVSB75E VCLTH")
row("Current limit max", 0.107 / 0.022, "A", "107 mV / 22 mohm", "SNVSB75E VCLTH")
row("Soft-start time, 10 Oct C305 47 nF", 47e-9 * 1.0 / 10e-6 * 1e3, "ms", "C VREF / ISS (ISS typ 10 uA)", "SNVSB75E")
c_out = 1.8e-6 * 2 + 47e-6 + 100e-6
row("  charge current that 4.7 ms demands", c_out * 48 / 4.7e-3, "A", "C_out x 48 V / tSS", "-> current limit + hiccup")
row("Soft-start time, C305 2.2 uF (1 Nov, superseded)", 2.2e-6 * 1.0 / 10e-6 * 1e3, "ms", "", "SNVSB75E")
row("  charge current at 2.2 uF", c_out * 48 / 0.22, "A", "", "")
row("Soft-start time, C305 4.7 uF (adopted)", 4.7e-6 * 1.0 / 10e-6 * 1e3, "ms", "", "SNVSB75E")
row("  range incl. C +-20 %, ISS 9..11 uA, VREF 0.99..1.01", 4.7e-6 * 0.8 * 0.99 / 11e-6 * 1e3, "ms (min)", "", "")
row("  ...max", 4.7e-6 * 1.2 * 1.01 / 9e-6 * 1e3, "ms", "", "")
row("  charge current at 4.7 uF", c_out * 48 / 0.47, "A", "", "")
row("  worst-case equivalent C (C -20 %, ISS +10 %)", 4.7 * 0.8 / 1.1, "uF", "", "sim ssend_*_css3u4_vclth93_csf")
row("  SS discharge 5 tau through 55 ohm switch", 5 * 55 * 4.7e-6 * 1e3, "ms", "", "SNVSB75E SS pull-down 55 ohm")
row("CS RC filter 100 ohm / 470 pF: tau", 100 * 470e-12 * 1e9, "ns", "", "SNVSB75E 9.3.7")
row("  3 RF CF vs (1-D)/fsw at 3.0 V", 3 * 100 * 470e-12 / ((1 - d3) / 298e3), "-", "must be < 1", "Eq. 13")
row("  2 RF CF (current limit invalid below this on-time)", 2 * 100 * 470e-12 * 1e9, "ns", "", "vs tON(min) 140 ns")
# VBAT_FUSED charge track (layout_fixes_4.py): IPC-2221 external-layer equation I = 0.048 dT^0.44 A^0.725 (A in mil^2)
a_mil2 = (0.2 / 0.0254) * 1.378
row("VBAT_FUSED 0.2 mm x 35 um cross-section", a_mil2, "mil^2", "", "1 oz assumed")
row("  current for 10 C rise", 0.048 * 10 ** 0.44 * a_mil2 ** 0.725, "A", "IPC-2221 equation", "standard not in repo")
row("  rise at 0.5 A", (0.5 / (0.048 * a_mil2 ** 0.725)) ** (1 / 0.44), "C", "", "")
row("  rise at 1.0 A", (1.0 / (0.048 * a_mil2 ** 0.725)) ** (1 / 0.44), "C", "", "")
row("  resistance (8.9 mm)", 1.72e-8 * 8.9e-3 / (35e-6 * 0.2e-3) * 1e3, "mohm", "", "")
ratio_nom = 1 + 470 / 10
ratio_lo = 1 + 470 * 0.99 / (10 * 1.01)
ratio_hi = 1 + 470 * 1.01 / (10 * 0.99)
row("Vout nominal", 1.0 * ratio_nom, "V", "VREF (1+470k/10k)", "")
row("Vout min (VREF 0.99, 1 % R)", 0.99 * ratio_lo, "V", "", "SNVSB75E VREF 0.99-1.01")
row("Vout max (VREF 1.01, 1 % R)", 1.01 * ratio_hi, "V", "", "")
row("OVP trip, nominal parts, typ 110 %", 1.10 * ratio_nom, "V", "", "SNVSB75E VOVTH 107/110/113 %")
row("OVP trip, nominal divider & VREF, min 107 %", 1.07 * ratio_nom, "V", "the '51.4' in earlier docs", "")
row("OVP trip, nominal divider & VREF, max 113 %", 1.13 * ratio_nom, "V", "the '54.2' in earlier docs", "")
row("OVP trip worst low (107 %, VREF 0.99, divider low)", 1.07 * 0.99 * ratio_lo, "V", "CORRECTED worst case", "")
row("OVP trip worst high (113 %, VREF 1.01, divider high)", 1.13 * 1.01 * ratio_hi, "V", "CORRECTED worst case", "")
row("Ripple cap needed for 0.24 V", 0.1 * d3 / (298e3 * 0.24) * 1e6, "uF", "I D / (f dV)", "")
D = d3
row("RHP zero (3.0 V, 100 mA)", (1 - D) ** 2 * vout / (2 * math.pi * D * 0.1 * n ** 2 * 7.3e-6) / 1e3, "kHz",
    "(1-D)^2 Vout / (2 pi D Iout n^2 Lp)", "")
row("Off-state drain plateau", 3.0 + (48.8 + vf) / n, "V", "Vin + (Vout+Vf)/n", "")
row("D301 steady reverse (3.0 V)", 48.8 + n * 3.0, "V", "Vout + n Vin", "")
row("D301 steady reverse (4.2 V)", 49.9 + n * 4.2, "V", "", "")
row("Leakage fraction for k=0.99", (1 - 0.99 ** 2) * 100, "% of Lp", "1-k^2", "sim netlist")
row("FET margin", 18.7 / 25 * 100, "% of VDS", "", "CSD16340Q3 25 V")
row("Rectifier margin", 97.1 / 200 * 100, "% of VR", "", "PNE20010ER 200 V")
row("Clamp diode margin", 18.7 / 100 * 100, "% of VR", "", "PMEG10020ELR 100 V")
row("R306 loss vs 1 W rating", 0.425 / 1.0 * 100, "%", "", "sim")
row("C309/C310 at worst OVP 55.9 V", 55.9 / 100 * 100, "% of 100 V", "", "E-06 80 % rule")

# --- bleeder (E-11) ---------------------------------------------------------------------------
c_nom = 2.2 + 2.2 + 47 + 100
c_max = 2.2 + 2.2 + 1.2 * (47 + 100)                   # +20 % on the electrolytics (ASSUMED typical)
row("Rail capacitance nominal", c_nom, "uF", "C309+C310+C311+C702", "design.py")
row("Rail capacitance assumed max", c_max, "uF", "+20 % electrolytics", "ASSUMPTION")
for v0 in (50.4, 54.2, 55.9):
    row(f"Max bleeder R for <5 V in 5 s from {v0} V", 5 / (c_max * 1e-6 * math.log(v0 / 5)) / 1e3, "kohm", "", "E-11")
    row(f"  t with 10 kohm from {v0} V (Cmax)", 10e3 * c_max * 1e-6 * math.log(v0 / 5), "s", "", "")
row("10 kohm loss at 50.4 V", 50.4 ** 2 / 10e3, "W", "", "")
row("10 kohm loss at 55.9 V", 55.9 ** 2 / 10e3, "W", "", "")

# --- kill path --------------------------------------------------------------------------------
row("FLY_EN with MCU high", 3.3 * 4.7 / (4.7 + 1.0), "V", "3.3 x 4.7k/(4.7k+1k)", "K-10")
for ron in (5, 20):
    row(f"FLY_EN with veto ON, MCU high, Rds(on)={ron} ohm", 3.3 * ron / (1000 + ron) * 1000, "mV",
        "3.3 V x Ron/(1k+Ron) (4.7k in parallel neglected)", "vs VEN(FALLING) min 0.33 V")

# --- runaway (S-06) ---------------------------------------------------------------------------
um_half_U = 0.5 * um_per_U
row("0.5 U travel", um_half_U, "um", "", "S-06")
for v in (15.0, 7.5):
    row(f"Time to 0.5 U at {v} mm/s", um_half_U / (v * 1000) * 1000, "ms", "", "LL06 top / PMD401 1500 Hz x 5 um")
row("Overrun with 11 ms stop at 15 mm/s", 0.011 * 15000 / um_per_U, "U", "", "SPI-gate proposal (1 ms detect)")
row("Overrun with 12 ms stop at 15 mm/s", 0.012 * 15000 / um_per_U, "U", "", "2 ms worst-case detect + 10 ms")
row("Max PMD401 SPI timeout for S-06 at 15 mm/s", (um_half_U / 15000 - 0.002) * 1e3, "ms", "", "runaway_timing.py")
row("Max PMD401 SPI timeout for S-06 at 7.5 mm/s", (um_half_U / 7500 - 0.002) * 1e3, "ms", "", "")
row("Rail decay rate at 100 mA from 151.4 uF", 0.1 / 151.4e-6 / 1000, "V/ms", "", "")

# --- power / battery ----------------------------------------------------------------------------
p48 = 48 * 0.006 + 0.005 * 15
row("48 V load at dosing speed", p48, "W", "48 V x 6 mA + 5 mW/Hz x 15 Hz", "PMD401 manual, LL06")
row("Battery current at dosing speed (3.0 V, 80 %)", p48 / 0.8 / 3.0, "A", "", "")
e_cell = 2.8 * 3.6
row("Cell energy (2.8 Ah x 3.6 V)", e_cell, "Wh", "", "distributor data [WEB-2ND]")
row("Idle limit for 3 days, 10 % reserve", e_cell * 0.9 / 72, "W", "", "E-10 (proposed)")
row("Motor-on time for 50 U/day (ASSUMED profile)", 50 / (15 * 4.5 / um_per_U), "s", "", "")
row("Charger loss 1 A, 3.0 V cell, 5 V in", (5 - 3.0) * 1.0, "W", "", "linear charger")
row("Charger loss 0.5 A, 3.0 V cell", (5 - 3.0) * 0.5, "W", "", "")
row("Unload overshoot + 1 % setpoint corner", 49.4 + 1.3, "V", "49.4 V + 1.3 V (sim)", "vs PMD401 50.4 V")
row("Unload overshoot + 0.1 % setpoint corner", 1.01 * (1 + 470 * 1.001 / (10 * 0.999)) + 1.3, "V", "", "")
row("Current limit with R305 18 mohm (proposal)", 0.093 / 0.018, "A (min)", "", "decision 8")
row("  ...max", 0.107 / 0.018, "A", "", "-> T301 Isat >= 6.5 A")
row("Stored rail energy at 48 V", 0.5 * 151.4e-6 * 48 ** 2 * 1e3, "mJ", "", "")
row("VBAT divider current at 4.2 V", 4.2 / 2e6 * 1e6, "uA", "", "")
row("VBAT divider time constant", 0.5e6 * 100e-9 * 1e3, "ms", "500 k x 100 nF", "")

print(f"{'Quantity':55s} {'Value':>12s}  Unit       How / source")
for name, v, u, how, src in rows:
    print(f"{name:55s} {v:12.4g}  {u:10s} {how} {('[' + src + ']') if src else ''}")
