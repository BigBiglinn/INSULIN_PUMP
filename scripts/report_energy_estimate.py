"""Illustrative energy and battery-life estimate for the report (NOT a measurement, NOT a power budget).

Every input is either recorded in the requirements/handover documents (source given) or a labelled
assumption. The purpose is to show which terms dominate, so that the bench checks (PW-09, MT-07, BT-01)
know what to measure. Output: docs/project_report/evidence/energy_estimate.txt
"""
import math, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "docs", "project_report", "evidence", "energy_estimate.txt")
L = []
p = L.append

# --- recorded inputs
U_UL = 10.0                 # 1 U = 10 uL (D-03)
AREA = math.pi * 4.61 ** 2 / 4   # mm^2, Hamilton 81320 bore 4.61 mm (D-04)
STEP_UM = 4.5               # no-load full step, LL06 datasheet (COMPONENTS_AND_BOM sec.4)
CAP_STEPS = 15.0            # speed cap, steps/s (K-15)
P_PMD_IDLE = 48 * 0.006     # W, PMD401 idle 6 mA at 48 V (manual, DESIGN_REQUIREMENTS sec.2)
P_PMD_MAX = 48 * 0.100      # W, PMD401 peak 100 mA (manual)
P_LL06_PER_HZ = 0.005       # W per Hz of step rate (LL06 data, COMPONENTS_AND_BOM sec.4)
ETA = 0.817                 # flyback efficiency, LTspice open-loop run 3 at 3.0 V (flyback_openloop.log step 3)
C_OUT = 182e-6              # worst-case 48 V capacitance (ECO2 item 2)
R_BLEED = 10e3              # R312
T_UNPARK, T_PARK = 0.080, 0.250   # s, PMD401 manual (unpark >= 80 ms, park about 250 ms)
T_SS = 0.111                # s, soft start with C305 = 1 uF at 9 uA (ECO1)
P_IDLE_REVA = 0.11          # W, Rev A idle budget with 48 V off (DESIGN_REQUIREMENTS sec.2; not measured)
# --- assumptions (labelled)
CELL_WH = 2.8 * 3.6         # ASSUMED: Molicel INR18650-P28A 2800 mAh x 3.6 V nominal (Rev B cell is OPEN B.20)
PROFILE_U = 24 * 1.0 + 3 * 5.0   # BT-01 profile: 1 U/h basal + three 5 U boluses per day
PULSES = 24 * 20 + 3        # basal delivered as 0.05 U pulses (D-07 proposed) + 3 boluses

um_per_U = U_UL * 1000 / AREA          # uL -> mm^3 ; /mm^2 -> mm ; *1000 -> um
s_per_U = um_per_U / STEP_UM / CAP_STEPS
p(f"Syringe area {AREA:.2f} mm^2; travel per U {um_per_U:.0f} um; steps per U {um_per_U/STEP_UM:.0f} (no-load step)")
p(f"Time per U at the {CAP_STEPS:.0f} steps/s cap: {s_per_U:.1f} s  ({1/s_per_U:.3f} U/s)")

p_rail_on = P_PMD_IDLE + 48.0 ** 2 / R_BLEED      # load on the 48 V rail whenever it is on, motor still
p_move_lo = p_rail_on + P_LL06_PER_HZ * CAP_STEPS   # LL06 5 mW/Hz figure
p_move_hi = P_PMD_MAX + 48.0 ** 2 / R_BLEED         # PMD401 maximum current
p(f"48 V load, rail on, motor still: {p_rail_on:.3f} W (PMD401 idle {P_PMD_IDLE:.3f} W + bleeder {48**2/R_BLEED:.3f} W)")
p(f"48 V load while moving: low {p_move_lo:.3f} W (LL06 5 mW/Hz) ... high {p_move_hi:.3f} W (PMD401 100 mA)")

e_charge = 0.5 * C_OUT * 48.0 ** 2 / ETA
t_overhead = T_SS + T_UNPARK + T_PARK
e_overhead = e_charge + p_rail_on / ETA * t_overhead
p(f"Per rail cycle: charge 182 uF to 48 V {e_charge:.3f} J; overhead time {t_overhead*1000:.0f} ms "
  f"(soft start + unpark + park, PMD401 boot time unknown, MT-07); overhead energy {e_overhead:.3f} J")

move_s = PROFILE_U * s_per_U
for name, pm in (("low", p_move_lo), ("high", p_move_hi)):
    e_move = pm / ETA * move_s
    e_ovh = PULSES * e_overhead
    wh_dose = (e_move + e_ovh) / 3600
    wh_idle = P_IDLE_REVA * 24
    days = CELL_WH / (wh_dose + wh_idle)
    p(f"[{name}] motion {e_move/3600:.3f} Wh/day + rail cycles {e_ovh/3600:.3f} Wh/day + idle {wh_idle:.2f} Wh/day "
      f"= {wh_dose + wh_idle:.2f} Wh/day -> {days:.1f} days on {CELL_WH:.1f} Wh")

p("Sensitivity to idle power (48 V off), high motion case:")
for pi in (0.01, 0.02, 0.05, 0.11, 0.2):
    e_move = p_move_hi / ETA * move_s
    wh = (e_move + PULSES * e_overhead) / 3600 + pi * 24
    p(f"  idle {pi*1000:5.0f} mW -> {wh:.2f} Wh/day -> {CELL_WH/wh:.1f} days")
p(f"If the 48 V rail were left on all day: PMD401 idle alone {P_PMD_IDLE*24:.1f} Wh/day "
  f"(+ bleeder {48**2/R_BLEED*24:.1f} Wh/day) at the rail, before conversion loss")
p("All values are estimates from recorded datasheet figures and assumptions; none is measured (PW-09, MT-07, BT-01 open).")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write("\n".join(L) + "\n")
print("\n".join(L))
