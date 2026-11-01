# 48 V flyback design (LM51551): calculations and simulation

Prepared 10 Oct 2026. Bench-only prototype (water or saline, never on a person or an animal).

The power stage is now dimensioned. **Two things remain unverified:** the transformer has no off-the-shelf part, and the control loop has not been simulated, because LTspice has no LM51551 model.

Sources:

- TI SNVSB75E (LM5155/LM51551): `docs/datasheets/lm51551.pdf`
- TI CSD16340Q3: `docs/datasheets/csd16340q3.pdf`
- Nexperia PNE20010ER and PMEG10020ELR: `docs/datasheets/`

## 1. Requirements used

| Item | Value | Source |
| --- | --- | --- |
| Input | 3.0–4.2 V (1S Li-ion); dosing stops at 3.4 V | E-01, S-13 |
| Output | 48 V; 45.6–50.4 V at the PMD401 including ripple and a 0 → 100 mA step | E-03 |
| Load | ≤ 100 mA (PMD401 at full speed; current at dosing speed has not been measured) | PMD401 manual / MT-07 |
| Capacitor rating | ≥ 100 V on the 48 V rail; nothing above 80 % of its voltage rating | E-06 (80 % rule PROPOSED) |
| Controller | LM51551, BIAS = VCC = VBAT (works from 2.97 V) | K-12, SNVSB75E §1 |

## 2. Hand calculations (CALC)

| Quantity | Equation / basis | Result |
| --- | --- | --- |
| Switching frequency | R<sub>T</sub> = 2.21×10¹⁰ / f<sub>SW</sub> − 955 (Eq. 5) | R301 = 73.2 kΩ → 298 kHz (±15 %) |
| Turns ratio n = N<sub>s</sub>/N<sub>p</sub> | CCM: V<sub>out</sub> + V<sub>F</sub> = n·V<sub>in</sub>·D/(1−D); a common configurable-transformer ratio | n = 5 → D = 0.765 at 3.0 V, 0.70 at 4.2 V (D<sub>MAX</sub> ≥ 90 % at 300 kHz) |
| Input current | P<sub>in</sub> = 4.8 W / 0.8 at 3.0 V | ≈ 2.0 A average (sim: 2.0–2.3 A). **This touches the E-05 2.1 A budget at full PMD401 speed** |
| Primary inductance | ΔI = 40 % of I<sub>pri,avg</sub> = 2.61 A at 3.0 V; L<sub>p</sub> = V<sub>in</sub>·D/(ΔI·f<sub>SW</sub>) | 7.3 µH (specify 5–10 µH) |
| Primary peak current | I<sub>pri,avg</sub> + ΔI/2 | 3.1 A (sim: 3.4 A with snubber) |
| Sense resistor | I<sub>lim</sub> = V<sub>CLTH</sub>/R<sub>s</sub>, V<sub>CLTH</sub> = 93–107 mV | R305 = 22 mΩ → 4.2–4.9 A; P ≈ 0.12 W |
| Soft start | t<sub>SS</sub> = C<sub>SS</sub>·V<sub>REF</sub>/I<sub>SS</sub> (10 µA, 1 V) | C305 = 47 nF → 4.7 ms |
| VCC/BIAS capacitor | Datasheet: 1–4.7 µF | C304 = 2.2 µF |
| Output divider | V<sub>out</sub> = 1 V × (1 + 470k/10k) | 48.0 V nominal (±1 % reference + resistor tolerance; full tolerance stack not done) |
| Output ripple | ΔV = I<sub>out</sub>·D/(f<sub>SW</sub>·C) | ≥ 1.1 µF effective at 48 V for 0.24 V → 2 × 2.2 µF/100 V X7R (C309, C310) plus C311 |
| FET voltage | V<sub>in,max</sub> + (V<sub>out</sub>+V<sub>F</sub>)/n + leakage spike | 13.9 V + spike; clamp must hold ≤ 20 V for a 25 V FET |
| Rectifier voltage | V<sub>out</sub> + n·V<sub>in,max</sub> + ringing | 69 V steady state; ringing per §3 |
| RHP zero (CCM) | (1−D)²·V<sub>out</sub> / (2π·D·I<sub>out</sub>·n²·L<sub>p</sub>) | ≈ 30 kHz at 3.0 V / 100 mA |
| Compensation (PRELIMINARY) | Current-mode gain with R<sub>i</sub> = R<sub>s</sub>/0.142 (SNVSB75E Fig. 9-17), f<sub>c</sub> ≈ 3 kHz, g<sub>m</sub> = 2 mA/V | R303 = 3.01 kΩ, C306 = 180 nF, C307 = 3.3 nF. **Depends on T301 L<sub>p</sub> and the PMD401 cable and bulk capacitance; must be verified** |

## 3. Open-loop power-stage simulation (LTspice 26.1.1)

File: `validation/sim/flyback_openloop.cir`; log: `validation/sim/flyback_openloop.log`.

**Scope:**

- The gate is driven by an ideal fixed-duty PWM. There is **no LM51551 model**, so neither regulation nor the control loop was simulated.
- The transformer is the specification below with k = 0.99 (about 2 % leakage, assumed).
- The FET and diode are generic models approximating the datasheet figures.
- The load is 480 Ω (100 mA).

| Run | Change | Result | Decision |
| --- | --- | --- | --- |
| 1 | 100 V Schottky output diode, 560 Ω / 10 nF clamp | V<sub>DS</sub> 22.6 V (90 % of 25 V); diode reverse ringing reached its 100 V breakdown | Rejected |
| 2 | + 100 Ω / 470 pF snubber, 270–390 Ω / 22 nF clamp | V<sub>DS</sub> 16.7 V, diode 81–91 V; but 0.5–0.63 W snubber loss and I<sub>pk</sub> 4.25 A at the current limit | Rejected |
| 3 | **200 V PNE20010ER + 220 Ω / 100 pF snubber, 390 Ω / 22 nF clamp** | V<sub>out</sub> 48.5–49.9 V (open loop); I<sub>pk</sub> 3.39 A (3.0 V), 2.74 A (4.2 V); V<sub>DS</sub> 18.5 V (74 %); D301 reverse 88–97 V (49 %); clamp 0.35–0.42 W; snubber 0.14–0.17 W; efficiency 82–85 % | **Adopted** |

Without the snubber in run 3, the 200 V diode still rang to its 200 V breakdown in the model, so the snubber is required.

## 4. Transformer specification (T301 remains a PLACEHOLDER)

| Parameter | Requirement |
| --- | --- |
| Turns ratio N<sub>s</sub>/N<sub>p</sub> | 5 (± 3 %) |
| Primary inductance | 7.3 µH nominal, 5–10 µH acceptable (re-check ripple and compensation) |
| Primary saturation current | ≥ 5 A (above the maximum current limit of 4.9 A) |
| Primary RMS current | ≥ 2.5 A |
| Secondary RMS current | ≥ 0.3 A |
| Leakage inductance | ≤ 2 % of L<sub>p</sub>. **Clamp and snubber values were tuned for 2 %** |
| Insulation | Functional; secondary ≥ 100 V working (non-isolated topology) |
| Frequency | 300 kHz |

Candidates screened without success:

- Coilcraft LPR6235-253LMR (1:10): about 1.3 A saturation, too small.
- Würth LT3748-family flyback transformers: step-down ratios.
- Coilcraft Hexa-Path HP/HPH (six-winding configurable, 5–50 W): plausible family, but Coilcraft's product tables returned HTTP 403 and could not be verified.

**Next step:** obtain the HP/HPH datasheet (or a custom-wound quote), check a 1+5 or 2+4 winding configuration against this table, then replace the `XFMR_PLACEHOLDER_4P` footprint.

## 5. What is still required before this stage can be trusted

1. A real transformer that meets §4, its footprint, and re-tuned clamp and snubber values.
2. Loop compensation verified: TI's LM5155 PSpice/TINA model or bench Bode measurement. Load-step check against E-03 ±5 %.
3. Tolerance stack of the 48 V setpoint (V<sub>REF</sub> ±1 % plus 1 % resistors) against 45.6–50.4 V; consider 0.1 % resistors.
4. Thermal check: R306 at 0.4 W, R305, Q301, D301.
5. The input current at full PMD401 speed (about 2.0–2.3 A at 3.0 V) is at or above the E-05 2.1 A budget. Measure the PMD401 current at dosing speed (MT-07).
6. 60 V fault ceiling (E-11, PROPOSED):
   - The LM51551 OVP trips at 107–113 % of V<sub>REF</sub> on FB (SNVSB75E electrical characteristics). The output is therefore stopped at about 51.4–54.2 V with nominal divider and V<sub>REF</sub>; including V<sub>REF</sub> ±1 % and 1 % resistors the worst case is **49.9–55.9 V** (52.8 V typical; corrected 1 Nov 2026, `scripts/audit_calcs.py`) while the FB divider is intact.
   - **An open R307/R308 or a lifted FB pin removes this protection.** That single fault is not covered: no secondary OVP or clamp is fitted.
   - Note also that 54.2 V exceeds the PMD401's 50.4 V maximum (E-03). OVP protects against touch voltage, not against overvoltage at the driver.
