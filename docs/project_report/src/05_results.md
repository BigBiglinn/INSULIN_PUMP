# Results and Discussion {#ch:results}

!box Read this first. | Every result in this chapter is a software check, a hand calculation or a simulation. No board was fabricated and no measurement was made. "Pass" below means "passes the stated software check", never "works on the bench".

## Validation status overview {#sec:valstatus}

{tab:valstatus} gives the evidence level reached by each part of the design. The remaining sections give the numbers.

!table tab:valstatus | Evidence level reached by each subsystem (final state, tag pcb-p6-final) | 2.2,1,1,1,1,1
| Subsystem | Designed | Calculated | Simulated | KiCad-checked | Bench-tested |
| Battery path, fuse, switch | Yes (fuse part TBD) | Yes (IR drop) | – | Yes | No |
| BQ25188 charger | Yes | – | – | Yes | No |
| TPS62840 3.3 V buck | Yes | Yes (VSET) | – | Yes | No |
| LM51551 48 V flyback | Yes (T301 leakage unknown) | Yes | Yes (open loop, start-up model, Q301 stress) | Yes | No |
| 48 V over-voltage trip and bleeder | Yes (ECO2) | Yes | – | Yes | No |
| Kill path (enable, veto, park) | Yes | Yes (thresholds) | – | Yes | No |
| Runaway (speed) protection | Encoder to supervisor only | – | – | Yes | No |
| STM32WBA55 supplies, clocks, RF | Yes (ECO1, from ST documents) | Yes (RF line impedance) | Field solver | Yes | No |
| STM32C031 supervisor | Yes (decoupling values assumed) | – | – | Yes | No |
| PMD401, encoder, RS-485 interfaces | Yes | Yes (levels) | – | Yes | No |
| PCB layout | Yes, fully routed | Partly (widths) | Layout sensitivity | Yes: 0 ERC, 0 DRC | No |
| Firmware | Design and reference code only | – | Reference code on a simulated plant | n/a | No |

## Electrical rules check and design rules check {#sec:ercdrc}

### Final reports

The archived final reports were produced by kicad-cli 10.0.3 on 1 November 2026 at 12:18 and are reproduced in {app:reports}. **ERC: 0 errors, 0 warnings. DRC: 0 violations, 0 unconnected pads, 0 footprint errors**, with schematic parity checked and zones refilled. The netlist audit `validation/logs/p6_netlist_audit.txt` compared 493 pads against the netlist with 0 mismatches.

Clean reports can hide suppressed checks, so the ignored checks were examined explicitly ({tab:ignored}). With every ignored ERC check enabled on a scratch copy (`validation/logs/p6_strict_erc.rpt`), the only findings are six footprint-filter warnings on deliberate footprint assignments.

!table tab:ignored | Checks switched off in the project settings, and why that is acceptable | 2.5,4
| Ignored check | Assessment |
| ERC: global label appears only once | Label-style generated schematic; connectivity verified independently (451/451 pins) |
| ERC: four connection points joined | Cosmetic for a label-style schematic |
| ERC: SPICE model issue | No SPICE models attached to symbols; simulation is done in separate decks |
| ERC: footprint does not match filters | Strict run shows 6 deliberate cases: J102, FB501, FB502, D301, D302, D303 |
| DRC: footprint has no courtyard | Library footprints without courtyards (test points, jumpers) |
| DRC: track not centred on via | Cosmetic geometry from scripted routing |
| DRC: tuning profile, footprint filters, component type | Not relevant to this board |

### How the reports evolved

The final zero was reached by fixing the causes, not by suppressing warnings ({fig:erchist}). The six ERC `power_pin_not_driven` errors of 10 October were left visible on purpose for three weeks, because the WBA55 supply wiring could not be designed without the ST documents. ECO1 wired the supplies from DS14127 and removed one error. The last five were cleared in P6 by adding PWR_FLAG markers to the five WBA55 rails that are fed through a bead, an inductor or the chip's own SMPS: no pin on those nets is a KiCad power output, so ERC cannot see a source. The U701 `lib_symbol_mismatch` warning was cleared by flattening the MAX3485 symbol into the project library. DRC fell from 305 violations of all severities before P6, most of them silkscreen, to 0.

!fig fig:erchist | docs/project_report/figures/fig_erc_history.png | ERC errors at the recorded checkpoints. | 5.5

### KiCad could not be re-run for this report

The container used to prepare this report has only Ubuntu's KiCad 7.0.11, which cannot open KiCad 10 files. ERC and DRC were therefore **not** re-run here. The figures above are read from the archived report files, whose timestamps match the final commit `945ce5f`. The independent checks below were re-run instead.

## Independent connectivity and netlist checks (re-run) {#sec:rerun}

The independent review of 1 November added reviewer-written Python checkers that read the KiCad files directly, without KiCad. They were re-run for this report on the final board, with outputs saved in `docs/project_report/evidence/` ({tab:rerun}).

!table tab:rerun | Independent checks re-run on the final design (20 Nov 2026) | 2.5,2.5,3
| Check | Tool | Result |
| Schematic pins vs `design.py` | `scripts/review/sch_netlist_check.py` | 451 pins compared, **0 mismatches**; 0 pins with neither a connection nor a no-connect flag |
| Copper connectivity per net | `scripts/review/pcb_check.py` | **0 nets** with more than one copper island (was 28 nets / 35 connections at the review) |
| Shorts (different-net copper overlap) | same | **0** |
| Clearance against net classes | same | 2 flags, both on FL501 bump pairs at 0.18 mm. These are covered by the scoped 0.15 mm FL501 rule, which this script does not read; KiCad DRC with the rule reports 0 |
| Inner-layer fills | same | In1 GND: one 8882 mm² fill (plus two 0.4 mm² slivers); In2: +3V3 4870 mm² and VBAT 3875 mm² |
| Flyback layout sensitivity | `scripts/review/run_flyback_sens.sh`, ngspice 42 | identical to the archived output ({sec:laysens}) |
| LM51551 start-up model | `validation/sim/lm51551_startup.py` | identical conclusions to ECO1 ({sec:softstart}) |
| RF line field solver | `validation/sim/rf_line_solver.py` | 62.9 Ω at 0.20 mm and 50.5 Ω at 0.32 mm reproduced |

The same script reports track widths on the current-carrying nets ({tab:widths}). The routing is complete, but several power nets still run in narrow tracks. That is the subject of review findings F-M1, F-M2 and F-C4 ({sec:review}).

!table tab:widths | Track widths on current-carrying nets at pcb-p6-final (pcb_check.py) | 1.6,1,1,1.2,1.6
| Net | Min (mm) | Max (mm) | Length (mm) | Of which < 0.5 mm |
| VBAT_FUSED | 0.15 | 0.30 | 68.5 | 68.5 |
| VBAT | 0.20 | 0.30 | 50.1 | 50.1 (plus the In2 VBAT plane) |
| VBAT_RAW | 0.80 | 0.80 | 15.6 | 0 |
| FLY_SW | 0.30 | 1.00 | 15.6 | 1.0 |
| FLY_CLAMP | 0.50 | 1.00 | 21.0 | 0 |
| FLY_CS | 0.20 | 0.50 | 13.0 | 6.8 |
| FLY_GATE / FLY_GATE_Q | 0.20 | 0.30 | 4.9 / 4.9 | all |
| FLY_SEC / FLY_SEC_A–D | 0.40 | 0.60 | 8.3 / 31–32 each | mostly |
| +48V_RAW | 0.20 | 0.80 | 64.8 | 45.3 |
| +48V_MOT | 0.30 | 0.50 | 23.5 | 3.6 |
| +3V3 | 0.20 | 0.30 | 71.1 | all (plus the In2 3V3 plane) |

## Pin-map verification {#sec:pinres}

`scripts/verify_pinmap.py` checked every assigned function of both MCUs against the STM32CubeMX 6.18.1 database: **41 functions, 0 failures**. It also confirmed three assumptions from the CubeMX pin names: C031 NRST on PF2 (`PF2-NRST`), C031 BOOT0 shared with SWCLK (`PA14-BOOT0`), and WBA55 BOOT0 on pin 34 (`PH3-BOOT0`). Two things remain unchecked: the WBA55 TIM2 counter width (CF-21, FW-08), which RM0493 must confirm, and the electrical pin properties.

## Design calculations {#sec:calcs}

`scripts/review/design_calcs.py` recomputes the key design equations from the datasheets. The re-run output is identical to the archived one. Its inputs are the values at the time of the review (1 % feedback resistors, the old track lengths), so items 2, 3 and 4 below describe the earlier board and are updated in the text.

!table tab:calcs | Key design calculations (CALC) | 2.4,3,2.6
| Quantity | Result | Assessment |
| Kill path, MCU high (3V3 = 3.0–3.37 V) | FLY_EN = 2.47–2.78 V | above the 1.575 V UVLO maximum: runs |
| Kill path, pull-down only / veto on | 0 V / a few mV | below the 0.33 V EN falling minimum: off |
| UVLO hysteresis-current error | 5 µA × 825 Ω = 4 mV | negligible |
| 48 V set point (0.1 % resistors, ECO1) | 47.43–48.58 V | inside 45.6–50.4 V |
| LM51551 internal OVP (107–113 % of VREF) | 50.8–54.8 V | above the PMD401's 50.4 V; independent trip added in ECO2 |
| E-11 discharge with R312 = 10 kΩ | 4.21 s from 50.4 V to 5 V | meets < 5 s |
| Slope compensation, RS = 22 mΩ | needs 17.7 kV/s; fixed ramp gives 11.9 kV/s | **subharmonic risk at D ≈ 0.71–0.79: open (F-C5)** |
| Slope compensation option | RS = 18 mΩ with RSL ≈ 880 Ω: ILIM 4.0–4.9 A | recommended by the review; not applied |
| Encoder edge rate at 15 mm/s | 188 k counts/s; 5.33 µs between edges | with 40 kΩ internal pull-ups, rise 8.8–17.6 µs: too slow if the LL06 outputs are open-collector (F-M7) |
| Cell → VBAT drop at 2 A (estimated resistances) | 186 mΩ → VBAT 3.03 V at the 3.4 V cut-off | close to the 2.97 V LM51551 BIAS minimum (F-M1) |

## Simulation results {#sec:sims}

Four kinds of model were used. Each has stated limits:

- **LTspice 26.1.1 open-loop power stage** with ideal fixed-duty gate drive. There is no LM51551 model, so neither regulation nor loop stability is simulated. Transformer per specification; generic FET and diode models.
- **ngspice 42 decks** (independent review) for layout sensitivity.
- **A cycle-by-cycle Python model** of LM51551 start-up and hiccup logic built from datasheet values. Not a vendor model.
- **A 2-D finite-difference field solver** for the RF line.

### Open-loop flyback power stage and efficiency {#sec:openloop}

{tab:openloop} gives the four runs of `validation/sim/flyback_openloop.cir` (load 480 Ω = 100 mA, the PMD401 maximum). Without the snubber, the 200 V rectifier rang to its breakdown voltage, so those runs are invalid as operating points, and the snubber is required. With the snubber, the stage delivers 4.90 W at 3.0 V input and 5.19 W at 4.2 V input. **Efficiency is 81.7 % at 3.0 V and 84.5 % at 4.2 V** ({fig:openloop}), close to the 80 % assumed in the hand calculation. The output is above 48 V because the duty cycle was fixed (open loop).

!table tab:openloop | Open-loop flyback simulation (LTspice, flyback_openloop.log) | 1.5,1,1,1,1,1,1,1,1
| Case | Vout avg (V) | Vout p-p (V) | Ipk (A) | Vds max (V) | D301 rev. (V) | Iin (A) | Pin / Pout (W) | η |
| 3.0 V, no snubber | 48.44 | 0.142 | 3.32 | 20.0 | 200.5 | 2.01 | 5.93 / 4.89 | (82.4 %) invalid |
| 4.2 V, no snubber | 49.37 | 0.105 | 2.72 | 20.0 | 200.5 | 1.41 | 5.86 / 5.08 | (86.6 %) invalid |
| 3.0 V, snubber | 48.48 | 0.138 | 3.39 | 18.5 | 88.5 | 2.03 | 5.99 / 4.90 | **81.7 %** |
| 4.2 V, snubber | 49.93 | 0.144 | 2.74 | 18.5 | 97.1 | 1.47 | 6.14 / 5.19 | **84.5 %** |

!fig fig:openloop | docs/project_report/figures/fig_openloop.png | Open-loop flyback simulation at 100 mA: efficiency (left) and input/output power (right). Grey: runs without the rectifier snubber, rejected because D301 rings to its 200 V breakdown. | 6.27

In the adopted run, the clamp dissipates 0.35–0.42 W and the snubber 0.14–0.17 W. Together they are about half of the roughly 1 W total loss. The simulated input current (2.0–2.3 A at 3.0 V in the different runs) reaches or exceeds the E-05 battery-path budget of 2.1 A at full PMD401 load (U-24). The PMD401 current at actual dosing speed has not been measured (MT-07). The parallel line ({sec:pr3}) found a light-load efficiency of only 37 % at the 6 mA PMD401 idle load in its switching model, because clamp and switching losses dominate when the output power is small.

### Transformer leakage and the clamp {#sec:clamp}

The HPH6-0090L datasheet does not publish leakage inductance, and the clamp absorbs the leakage energy at every switch turn-off. A sweep therefore bracketed it from 2 % to 10 % ({tab:leak}, {fig:leak}).

!table tab:leak | Peak switch voltage against transformer leakage (LTspice, no loop inductance) | 1,1.5,1.5,1.5,1.6
| Leakage | ECO1 clamp, Vds at 3.0 V | ECO1 clamp, Vds at 4.2 V | ECO1 clamp power | ECO2 clamp + SMAJ15A, Vds at 4.9 A, 4.2 V |
| 2 % | 18.2 V | 19.4 V | 0.40 W | 22.8 V |
| 4 % | 20.0 V | 21.7 V | 0.53 W | 23.9 V |
| 6 % | 20.2 V | 23.0 V | 0.62 W | 24.1 V (TVS conducting) |
| 10 % | 20.7 V | 24.2 V | 0.70 W | 24.4 V (TVS conducting) |

!fig fig:leak | docs/project_report/figures/fig_leakage.png | Simulated peak drain voltage against leakage for the ECO1 clamp at nominal peak current and the ECO2 clamp with the SMAJ15A ceiling at the 4.9 A current limit. | 5.6

The ECO1 sweep was run at the nominal 3.1–3.4 A peak current. Re-running at the 4.9 A current-limit peak (`flyback_clamp_worstcase.cir`) showed that the old 390 Ω/22 nF clamp would reach 26.3 V at 2 %, 32.6 V at 4 % and 45.2 V at 10 % leakage, far above the 25 V rating of the original CSD16340Q3. That finding drove the ECO2 change to a 30 V FET, a larger clamp capacitor and the SMAJ15A ceiling. The bench action is fixed in advance: measure the primary inductance with all secondaries shorted. At ≤ 2 % leakage the design is acceptable; at 2–4 %, lower R306; above 4 %, choose another winding or another part.

### Switch voltage margin, Q301 {#sec:q301}

The clamp results above exclude the stray inductance of the commutation loop. `validation/sim/q301/` added 3–5 nH, the loop estimate from the P1b placement review ({tab:q301}, {fig:q301}).

!table tab:q301 | Q301 AONR34332C peak drain voltage at the 4.9 A limit (LTspice, validation/sim/q301/RESULTS.md) | 1,1,1,1,1,1,1
| VBAT | Leakage | Loop L | Vds peak | % of 30 V | TVS power | R306 power |
| 4.2 V | 2 % | 3 nH | 25.8 V | 86 % | 0 | 0.87 W |
| 4.2 V | 2 % | 5 nH | 27.2 V | 91 % | 0 | 0.87 W |
| 4.2 V | 10 % | 3 nH | 27.1 V | 90 % | 3.03 W | 0.98 W |
| 4.2 V | 10 % | 4 nH | 28.0 V | 93 % | – | 0.98 W |
| 4.2 V | 10 % | 5 nH | 28.9 V | 96 % | 3.03 W | 0.98 W |
| 3.4 V | 10 % | 4 nH | 27.2 V | 91 % | – | 0.98 W |

!fig fig:q301 | docs/project_report/figures/fig_q301.png | Simulated Q301 peak drain voltage at the current limit, against the 30 V rating and the 80 % derating line. | 5.6

No corner exceeds 30 V, but the worst is 28.9 V, and about 29.9 V with the estimated 1 V TVS heating. **The 80 % derating line (24 V) is exceeded at every corner, so the voltage margin is not established** (open item). The search for a part above 30 V that is fully enhanced at the 3.0–4.2 V gate drive (the LM51551 drives the gate from VBAT) found no verified candidate. TI CSD18543Q3A and AOS AON2240 need about 4.5 V of gate drive. Diodes DMN4020LFDE has only advance data. Nexperia BUK9M20-40H is the only candidate worth checking, but its datasheet could not be retrieved, and the LTspice decks built from guessed parameters are explicitly marked "not evidence". Two simulated mitigations exist: a 10 Ω gate resistor plus a drain RC snubber, and the SMAJ13A/24 mΩ stress-reduction option (21.7 V at 10 % leakage, about 25–27 V with parasitics). The footprints for the first are on the board but unfitted (ECO3).

### Soft start and hiccup lock-out {#sec:softstart}

The LM51551 counts current-limit cycles and enters hiccup mode after 64 consecutive ones. Charging about 150–182 µF to 48 V through a short soft-start ramp holds the converter in current limit long enough to trip it. The cycle-by-cycle model `validation/sim/lm51551_startup.py` was re-run for this report over 12 corners per capacitor value (VIN 3.0/4.2 V, C_{OUT} 150/181 µF, V_{CLTH} 93/107 mV, I_{SS} 9/11 µA) with the 6 mA PMD401 idle load and the bleeder ({fig:softstart}).

!fig fig:softstart | docs/project_report/figures/fig_softstart.png | Soft-start study, re-run of the cycle-by-cycle model. 47 nF and 220 nF lock out in every corner; 470 nF is not robust; 1 µF starts cleanly in 91–111 ms in all 12 corners, with a peak current of 2.2–3.1 A. | 5.6

With 47 nF (the original value) the rail stalls between 7 V and 11 V after six hiccups at every corner. With 1 µF the rail reaches regulation in 91–111 ms with no hiccup, and the peak primary current is 2.19–3.09 A, below the 4.2 A minimum current limit. With the full 100 mA load present during start-up, even 1 µF fails at 3.0 V and 3.4 V input (the rail stalls near 19 V). This is why the **PMD401 must stay parked until FLY_PGOOD**. The obligation is enforced in hardware by the default park (Q402/R405) and in firmware.

### RF line impedance {#sec:rf}

The field solver was validated against ST's own example: it gives 60.6 Ω for a line that ST specifies as 63 Ω, 4 % low. It then confirmed that ST's reference width must not be copied onto this stack-up. Over a solid In1 plane, ST's 0.45 mm line gives 22.5 Ω, against 55.7 Ω over ST's Layer-3 reference. {fig:rf} shows the impedance against width for the assumed JLC 7628 stack-up. Both chosen widths land on target bare: 0.20 mm gives 62.9 Ω and 0.32 mm gives 50.5 Ω. A solder mask over them would pull them down to 57.3 Ω and 46.9 Ω, which is why the mask is opened. Sensitivity is about ±3 Ω for εr ±0.2 or a prepreg thickness change of ±0.02 mm. The slight non-monotonic step between 0.32 and 0.33 mm in the figure is the 0.01 mm grid resolution of the solver.

!fig fig:rf | docs/project_report/figures/fig_rf_line.png | Grounded-coplanar line impedance against width (0.25 mm gap, 0.2104 mm prepreg, εr 4.4), bare and under solder mask. The grey bars mark the two chosen widths. | 5.6

### Layout sensitivity of the clamp path {#sec:laysens}

The independent review's ngspice deck (earlier clamp values, 25 V FET model) showed how much the clamp-path inductance matters. With a tight layout the peak V_{DS} is 17.7 V (3.0 V input) and 17.9 V (4.2 V input). With about 25 nH in the clamp path and 30 nH in the secondary path it rises to 28.2 V and 26.2 V ({fig:laysens}). The re-run reproduced these numbers exactly. The result led the P1b placement to pull D302, C308 and D304 next to the Q301 drain. On the final board D302 is about 3.6 mm and C308 about 6.5 mm from Q301, against about 25 mm at the review. The loop inductance of the routed copper has not been extracted.

!fig fig:laysens | docs/project_report/figures/fig_layout_sens.png | Peak drain voltage with a tight clamp loop (blue) and with about 25 nH of clamp-path inductance (orange); ngspice re-run of the review deck. | 5.6

## Efficiency and energy budget {#sec:energy}

There is no measured power budget: PW-09, MT-07 and BT-01 are all open. To show which terms matter, an illustrative estimate was computed by `scripts/report_energy_estimate.py` from recorded datasheet figures. Its output is saved as `evidence/energy_estimate.txt`. The profile is that of check BT-01: 1 U/h basal delivered as 0.05 U pulses, plus three 5 U boluses a day (39 U/day). The cell energy assumes the Rev A Molicel P28A (2.8 Ah × 3.6 V ≈ 10.1 Wh), because the Rev B cell is not chosen. Conversion uses the simulated 81.7 % flyback efficiency.

!table tab:energy | Illustrative daily energy budget (estimate, not measured) | 3,2,3
| Term | Value | Basis |
| Time per unit at the speed cap | 8.9 s/U (0.113 U/s) | 599 µm/U ÷ 4.5 µm/step ÷ 15 steps/s |
| 48 V load, rail on, motor still | 0.518 W | PMD401 idle 0.288 W + bleeder 0.230 W |
| 48 V load while moving | 0.59 W (low) … 5.03 W (high) | LL06 5 mW/Hz figure … PMD401 100 mA maximum |
| Per rail on/off cycle | 0.54 J (441 ms overhead) | charging 182 µF to 48 V, soft start, unpark 80 ms, park 250 ms; PMD401 boot time unknown |
| Motion energy | 0.07 … 0.59 Wh/day | 39 U/day |
| Rail cycles | 0.07 Wh/day | 483 cycles/day |
| Idle with 48 V off | 2.64 Wh/day | 0.11 W Rev A budget (not measured; Rev B value unknown) |
| **Total and run time** | **2.78 … 3.30 Wh/day → 3.6 … 3.1 days** | E-10 target (proposed): ≥ 3 days |

Three conclusions follow, and they hold whatever the exact numbers turn out to be:

1. **Idle power dominates.** Even at the pessimistic motion figure, dosing uses less than a quarter of the energy. Run time is about 11 days at 10 mW idle, 5.4 days at 50 mW and 1.8 days at 200 mW. Measuring the Rev B idle current (encoder, MAX3485, LEDs, BLE duty, regulator quiescent current; review finding F-m3) is therefore the most important power measurement.
2. **Switching the 48 V rail off between doses (K-11) is essential.** The PMD401 idle alone would cost 6.9 Wh/day at the rail, plus 5.5 Wh/day in the bleeder, more than half the cell every day before conversion loss.
3. The bleeder R312 costs 0.23 W while the rail is on. That is acceptable at the short duty cycle of this profile, but it lowers the flyback's headroom at low battery (U-24).

## v1 simulator results {#sec:v1res}

!box Pending source files. | As explained in {sec:v1}, the v1 code and CSV results are not yet in the repository. The two recorded results are about 89 % time in range for PID control, and about 93 % time in range with 0 % hypoglycaemia for the predictive controller with the safety supervisor. They will be expanded here with the glucose traces, the per-scenario table and the fault-injection results once the files are committed. Until then they are reported only as figures recorded in the decision log, not as results regenerated for this report.

## Independent design review: findings and their status {#sec:review}

An independent review on 1 November 2026 (`docs/review/INDEPENDENT_DESIGN_REVIEW.md` [25]) examined the design as it stood at commit `976a17b`, the 10 October state. It used only its own scripts and calculations. It was merged into the main branch after stage P6, so some of its findings had already been fixed by ECO1–ECO3 and P1–P6 and others had not. {tab:review} gives the status of every critical and major finding against the final design, determined for this report from `design.py`, the project file and the re-run of `pcb_check.py`.

!table tab:review | Independent-review findings against the final design | 0.7,3.3,1.2,3
| ID | Finding (at 976a17b) | Status at P6 | Evidence |
| F-C1 | 35 missing connections on 28 nets | **Closed** | 0 unconnected (KiCad); 0 islands (re-run) |
| F-C2 | WBA55 supply pins not supplied | **Closed** | ECO1 supply network from DS14127/AN6373 |
| F-C3 | Clamp ~25 mm from the switch; 25 V FET overstressed | **Partly closed** | Clamp beside the drain (D302 3.6 mm); 30 V FET; margin still open ({sec:q301}) |
| F-C4 | FLY_CS 0.2 mm track inside the sense path; ILIM could fall to 2.5 A | **Open, not re-assessed** | R305 now about 5 mm from Q301; 6.8 mm of FLY_CS still < 0.5 mm |
| F-C5 | No slope compensation at D ≈ 0.71–0.79 | **Open** | R305 still 22 mΩ, no RSL in `design.py` |
| F-M1 | Battery path VBAT_FUSED 0.2 mm at 2.1 A | **Open** | still 0.15–0.30 mm, 68.5 mm |
| F-M2 | Narrow VBAT feed to the primary | **Open (partly mitigated)** | VBAT tracks 0.2–0.3 mm; In2 VBAT plane under the 48 V block |
| F-M3 | Secondary loop large (C309/C310 33 mm from D301) | **Closed** | C309/C310 now 5.5–10.5 mm from D301 |
| F-M4 | R307 (470 k) 0603 at 47 V: 94 % of a 50 V rating | **Open** | still the 0603 footprint |
| F-M5 | L201 0603 cannot hold the 2016 inductor | **Closed** | ECO1: DFE201612E on a 2016 footprint |
| F-M6 | RF chain long, with vias, no stack-up | **Closed in layout**; stack-up open | P2: 2.5 + 8.5 mm, no vias; widths from the field solver |
| F-M7 | No pull-ups on ENC_A/B/I | **Open** | no pull-up footprints in `design.py` |
| F-M8 | READY/FAULT fail unsafe when unplugged | **Partly closed** | level shifters (ECO1); firmware must ignore both until FLY_PGOOD |
| F-M9 | No TVS or series resistor on RS-485 | **Open** | J704 lines unprotected |
| F-M10 | Charging with the switch off runs at the 10 mA default | **Open (owner decision)** | assumption A-14 to be corrected |
| F-M11 | Net-class gaps (FLY_SNUB, VBAT, GND in Default) | **Open** | net-class patterns unchanged |
| F-M12 | E-11 bleeder missing | **Closed** | R312 10 kΩ 1 W fitted |
| F-M13 | Zones connect SMD pads by track only | **Open** | all five zones `thru_hole_only` |
| F-M14 | BOMs stale | **Closed** | BOMs re-exported at P6 (144 references) |
| F-M15 | FLY_GATE 14 mm with a layer change | **Improved** | FLY_GATE 4.9 mm |

The minor findings are also open: decoupling distance, an RS-485 RO pull-up, the battery-life calculation (now estimated in {sec:energy}), a common-cause over-voltage on the shared 3V3, missing test points on several rails and safety signals, no reverse-polarity protection, no USB ESD protection, the JST SH 48 V rating, and the missing deliverable file names. **The finding that matters most is F-C5.** Without slope compensation, subharmonic oscillation is expected at heavy load. The fix is a two-part change (R305 → 18 mΩ, RSL ≈ 887 Ω) that also requires re-checking the current limit and the start-up model.

## Parallel development line (pull request #3, not merged) {#sec:pr3}

A second, independent design session worked from the 10 October state in parallel (branch `claude/friendly-keller-9gz8a8`, pull request #3). The owner merged pull requests #1 (the independent review) and #2 (the placement and routing line described in this report), but not #3. Its board is a different design and **is not the design of record**. Its simulation work is still useful as independent corroboration, because it used different models (an ngspice translation of the open-loop deck, a level-2 switching model and a level-3 cycle model) and reached compatible conclusions:

- **Open-loop agreement between simulators.** ngspice reproduced the LTspice open-loop results within 0.1–0.7 % on output voltage, 0.7–1.8 % on peak current and 0.4–1.1 % on V_{DS}. Efficiency was 80 % at 3.0 V and 85 % at 4.2 V in ngspice, against 82 % and 85 % in LTspice. Output ripple differed by −12 % to +17 %.
- **Soft start.** Its cycle model also found that 47 nF to 680 nF lock out. It found 1 µF marginal with 100 mA during start-up, and ≥ 1.5 µF clean. That line adopted 4.7 µF, and a full 0.55 s switching run reached 47.5 V at 465 ms with no hiccup and the motor parked. This report's line keeps 1 µF with the motor parked until PGOOD. Both conclude that the PMD401 must be parked during start-up.
- **Load steps.** A 6 → 100 mA step at 3.0 V and 3.4 V dipped to 47.0 V and then triggered hiccup about 3 ms after the step. A 20 ms ramp did not: it dipped by only 0.19 V, at about 83 % efficiency. This suggests that firmware should ramp the PMD401 step rate rather than step it. That has not been checked on this design.
- **Faults.** With R307 open and no load, the level-3 model showed the rail ratcheting above 100 V within 2–3 s through repeated soft-start restarts. That confirms the need for the independent OVP that ECO2 added to this design. An output short was held at a 4.95 A primary peak, with hiccup after 0.235 ms.
- **Q301 stress.** In current-limit operation a 25 V FET reached 26.2 V with no layout inductance and 33.7 V with 5 nH. That line therefore rejected the CSD16340Q3 and asked for a ≥ 40 V part. ECO2 in this report's line reached the same rejection independently.

## Problems found and how they were diagnosed {#sec:problems}

Failures and corrections are part of the engineering record. {tab:problems} lists every significant one. Most were caught by simulation or by checking a datasheet before any hardware existed, which is the main return on the verification effort.

!table tab:problems | Problems found during the design, how they were found, and the fix | 2.2,2.2,3
| Problem | How it was found | Fix |
| Rev A kill switch was fail-on: the Pololu EN has a 100 kΩ pull-up to VIN | Reading the module schematic (30 Sep) | 4.7 kΩ pull-down, 1 kΩ from the MCU, BSS138 veto |
| DC2628A output capacitor at 96 % of its rating | Voltage-rating check | 47 µF/100 V replacement |
| Supervisor gate pull-down gave no veto when the supervisor was dead (SG-03 would fail) | Single-fault reasoning in the requirements report | R403 pull-up: veto on by default (owner, 10 Oct) |
| 100 V Schottky rectifier rang to breakdown | Open-loop LTspice run 1 | 200 V PNE20010ER plus RC snubber |
| 47 nF soft start locks out in hiccup | Cycle-by-cycle start-up model | 1 µF; PMD401 parked until PGOOD |
| 25 V switch exceeds its rating at the current limit | Worst-case clamp simulation at 4.9 A | 30 V AONR34332C, bigger clamp capacitor, SMAJ15A ceiling; margin still open |
| SMBJ48A clamp only 0.6 V below the 60 V ceiling | Clamp-voltage calculation from Rd | Independent zener/BSS138 OVP trip |
| R312 specified with its dissipation (0.25 W) instead of its rating | ECO2 review | 1 W 2512 |
| TPS62840 inductor on a 0603 footprint | Review against TI SLVSEC6D Table 4 | DFE201612E on a 2016 footprint |
| READY/FAULT could exceed the pin rating with the MCU unpowered (FT limit falls to 4 V at VDD = 0) | DS14127 pin-tolerance check (ECO1) | BSS138 level shifters |
| RF line widths copied from ST's reference were wrong for this stack-up | 2-D field solver | 0.20 / 0.32 mm lines, mask opened |
| ST datasheets unreachable (st.com blocked) for three weeks | Download failures | Six ERC errors left visible instead of masked; resolved in ECO1 |
| FLY_PGOOD could not escape U501 pin 28 | Stage 5a, D7 scratch investigation | Coordinated pin 24–38 fan-out in P2 |
| Freerouting plateaued at about 63 unrouted; telemetry was on by default | Router logs | Staged, specification-driven hand routing; telemetry off |
| BOMs went stale against the schematic twice | BOM re-export comparison | Re-exported with every difference documented; BOM export added to the checks |

## Unresolved issues and risks {#sec:open}

The design is digitally complete but **not fabrication-ready**. {tab:open} lists the open items that matter most. Every item is also in `docs/handover/UNRESOLVED_ISSUES.md` or in the review.

!table tab:open | Principal unresolved issues | 0.8,3.2,1,2.4
| ID | Issue | Severity | Needed to close |
| Q301 | Switch voltage margin: 28.9 V simulated (about 29.9 V with heating) on a 30 V part; derating exceeded | Critical | Measure Vds on the bench; or a verified ≥ 40 V logic-level FET |
| T301 | Transformer leakage unpublished; clamp and snubber values provisional | Critical | Measure leakage on samples; re-tune R306/C308/R313/C312 |
| F-C5 | No slope compensation; subharmonic risk | Critical | RS 18 mΩ + RSL 887 Ω; re-simulate; bench check |
| PMD401 | Absolute maximum on the 48 V input unknown; the OVP trip (50.5–53.9 V) can exceed 50.4 V | Critical | Vendor question (drafted, not sent) |
| U-03 / S-06 | Speed cap only in main-MCU firmware; FT-02 cannot pass | Critical | Supervisor rate check in firmware |
| Loop | LM51551 control loop not modelled; compensation preliminary | Major | TI model or bench Bode measurement |
| F-C4 / F-M1 / F-M2 / F-M13 | Narrow power tracks, SMD pads not flooded | Major | Pour-based re-work of the power stage and battery path |
| F-M7 / F-M9 | Encoder pull-ups; RS-485 protection | Major | Footprints (fit after IF-02) |
| U-12 / U-17 | BQ25188 YBG footprint pitch inferred; connector orientation; J703 0.40 mm gap at 48 V | Major | TI and JST drawings |
| U-16 / U-20 | No fab house or stack-up; RF impedance estimated | Major | Fab selection |
| U-24 | Input current 2.0–2.3 A at 3.0 V vs the 2.1 A budget | Major | MT-07 measurement |
| F101, R316, R317, C314 | No 5 A fuse part found in the 2920 footprint; tuning parts TBD | Minor | Part selection |
| Firmware | Not written; obligations listed in {sec:fw} | Major | Owner |

## Assumptions the design rests on {#sec:assumptions}

The full assumptions register (A-1 to A-30) is in `docs/handover/ASSUMPTIONS_AND_DEVIATIONS.md`. The most consequential assumptions are these:

- **Step length falls smoothly and repeatably with load,** so it can serve as the occlusion sensor. This is the project's main technical bet, unproven on hardware (MT-05).
- The PMD401 behaves as its manual describes in servo mode with this motor and encoder, and its unstated pull-up rail is no higher than 5 V.
- The LL06 encoder is powered correctly from 3.3 V (JP701), and its outputs need no external pull-ups. Otherwise F-M7 applies.
- The transformer leakage is at most 2–4 %.
- The STM32C031 package is LQFP48 and its decoupling values follow common practice (ST datasheet not read).
- The JLC04161H-7628 stack-up holds for the RF line widths.

{fig:bomstatus} summarises the evidence status of the 144 BOM references. 110 of them (DECIDED, DS, CALC) rest on a recorded decision, a datasheet or a calculation. 30 are labelled assumptions, mostly connectors, test points, LEDs and decoupling. Only 4 remain TBD or PLACEHOLDER: F101 and the unfitted bench-tuning parts R316, R317 and C314. Five references are DNP.

!fig fig:bomstatus | docs/project_report/figures/fig_bom_status.png | Evidence status of the 144 BOM references (docs/bom_detailed.csv at pcb-p6-final). | 5.6
