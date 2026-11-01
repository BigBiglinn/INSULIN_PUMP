"""Reviewer's independent design calculations. Datasheet values cited inline (docs/datasheets)."""
import math
rho, t1oz = 1.72e-8, 35e-6
def trace_R(L_mm, w_mm, t=t1oz): return rho * (L_mm * 1e-3) / (w_mm * 1e-3 * t)
print("== 1. LM51551 slope compensation (SNVSB75E eq.8/9/10)")
fsw = 2.21e10 / (73.2e3 + 955)                  # eq.5
print(f"fsw = {fsw/1e3:.1f} kHz")
n, Lp, Vout, Vf = 5.0, 7.3e-6, 48.0, 0.9
for Rs in (22e-3, 18e-3, 15e-3):
    fall = (Vout + Vf) / n / Lp                      # primary-referred falling slope A/s
    need = 0.5 * fall * Rs * 1.2                     # eq.8 LHS, V/s
    have = 40e-3 * fsw                               # fixed slope V/s
    RSL_min = max(0.0, (need / fsw - 40e-3) / 30e-6)
    RSL_opt = max(0.0, (0.82 * fall * Rs / fsw - 40e-3) / 30e-6)
    print(f" Rs={Rs*1e3:.0f} mohm: needed {need/1e3:.1f} kV/s vs fixed {have/1e3:.1f} kV/s -> "
          f"{'OK' if have > need else 'SUBHARMONIC RISK'}; RSL min {RSL_min:.0f} ohm, RSL(82%) {RSL_opt:.0f} ohm")
    for D in (0.785, 0.715):
        for V, lab in ((93e-3, 'min'), (107e-3, 'max')):
            Ipk = (V - 30e-6 * RSL_opt * D) / Rs
            print(f"    with RSL={RSL_opt:.0f}: Ipk-CL({lab}, D={D}) = {Ipk:.2f} A")
print("  Required peak at 3.0 V / 100 mA (FLYBACK_DESIGN.md): ~3.1 A")

print("\n== 2. Current-sense error from the 0.2 mm FLY_CS track (Q301 source -> R305, ~6.1 mm)")
Rt = trace_R(6.1, 0.2)
for Rs in (22e-3,):
    print(f" track R = {Rt*1e3:.1f} mohm (1 oz, 25 C; +~30 % hot). Effective sense = {(Rs+Rt)*1e3:.1f} mohm")
    print(f" Ilim(min) = 93 mV/{(Rs+Rt)*1e3:.1f} mohm = {0.093/(Rs+Rt):.2f} A  (design intent 4.2-4.9 A; needed ~3.1 A)")

print("\n== 3. Battery-path track VBAT_FUSED (F101 -> J102), 0.2 mm, ~25 mm")
L = math.hypot(123 - 112.383, 156.612 - 145.995) + (145.995 - 140.545) + (112.383 - 105.955)
R = trace_R(L, 0.2)
print(f" length {L:.1f} mm, R = {R*1e3:.0f} mohm; at 2.1 A: drop {2.1*R*1e3:.0f} mV, loss {2.1**2*R:.2f} W")
# IPC-2152 rough (external, 1 oz, 10 K rise) charts: ~0.75 A for 0.2 mm; ~2.1 A needs about 0.9-1.0 mm
print(" IPC-2152 (1 oz external, 10 K): 0.2 mm carries roughly 0.7-0.8 A; 2.1 A needs ~0.9-1.0 mm (verify with chart)")

print("\n== 4. 48 V set point tolerance (VREF 0.99-1.01 V, R307 470k 1 %, R308 10k 1 %)")
hi = 1.01 * (1 + 470e3 * 1.01 / (10e3 * 0.99)); lo = 0.99 * (1 + 470e3 * 0.99 / (10e3 * 1.01))
print(f" Vout DC range {lo:.2f} .. {hi:.2f} V (limit 45.6-50.4 V); margin {lo-45.6:.2f} V low / {50.4-hi:.2f} V high for ripple+step")
print(f" OVP (FB 107-113 % of VREF): {1.07*0.99*48:.1f}..{1.13*1.01*48:.1f} V -> above 50.4 V PMD401 limit; protects only E-11 (60 V)")
print(f" R307 sees {48*470/480:.1f} V across one 0603 (typ. 50 V rated, some 75 V) -> {48*470/480/50*100:.0f} % of 50 V: fails the E-06 80 % rule")

print("\n== 5. Kill path (SNVSB75E: EN 0.4-0.7 V rising / 0.33-0.63 falling; UVLO 1.425-1.575 V rising)")
for v3 in (3.0, 3.3, 3.37):
    print(f" 3V3={v3}: MCU high -> FLY_EN = {v3*4.7/5.7:.2f} V (needs > 1.575 V to run) ")
print(" Pull-down only -> 0 V (shutdown); veto BSS138 on: I = 3.3 V/1k = 3.3 mA, Vds ~ few mV -> shutdown")
print(f" UVLO hysteresis current 5 uA x (1k||4.7k = {1e3*4.7e3/5.7e3:.0f} ohm) = {5e-6*824*1e3:.1f} mV (negligible)")

print("\n== 6. E-11 discharge (proposed): <5 V within 5 s after switch-off")
C = 2 * 2.2e-6 * 0.5 + 47e-6 + 100e-6     # ceramics derated 50 %
Rbleed_now = 480e3
print(f" C ~ {C*1e6:.0f} uF; with only R307+R308 (480k): tau = {Rbleed_now*C:.0f} s -> t(5 V) = {Rbleed_now*C*math.log(48/5):.0f} s (FAIL)")
Rmax = 5 / math.log(48 / 5) / C
print(f" R312 needed <= {Rmax/1e3:.1f} kohm; e.g. 12k: t(5 V) = {12e3*C*math.log(48/5):.1f} s, P = {48**2/12e3:.2f} W while 48 V on, I = {48/12e3*1e3:.1f} mA")

print("\n== 7. Cell -> VBAT drop at the 3.4 V dosing cut-off, 2 A flyback draw (estimates, not measured)")
parts = {"cell ESR (18650, est.)": 0.035, "protection PCB (est.)": 0.04, "fuse 5 A (est.)": 0.015, "XT30 + wiring (est.)": 0.01,
         "VBAT_FUSED 0.2 mm track": R, "master switch + leads (est.)": 0.02}
tot = sum(parts.values())
for k, v in parts.items(): print(f"  {k:30s} {v*1e3:5.0f} mohm")
print(f" total {tot*1e3:.0f} mohm -> drop {2*tot:.2f} V; VBAT at IC = {3.4-2*tot:.2f} V; 3V3 in 100 % mode ~ VBAT - ~0.02 V")
print(" LM51551: VCC UVLO rising 2.75-2.95 V, BIAS=VCC min 2.97 V. E-02 needs 3V3 >= 3.0 V while dosing.")

print("\n== 8. Encoder edge timing (if LL06 outputs need the pull-ups the PMD401 normally supplies)")
cps = 15e-3 / 80e-9
print(f" max count rate {cps/1e3:.0f} k counts/s -> per-channel {cps/4/1e3:.1f} kHz, min edge spacing {1/cps*1e6:.2f} us")
for Rpu in (40e3, 10e3):
    for Cl in (100e-12, 200e-12):
        print(f"  pull-up {Rpu/1e3:.0f}k, C {Cl*1e12:.0f} pF: 10-90 % rise {2.2*Rpu*Cl*1e6:.2f} us")
