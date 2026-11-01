# Engineering blocker review: Piezo Insulin Pump v2 Rev B

1 Nov 2026. Covers the nine open critical items named by the owner on 1 Nov 2026. Board state: commit `ef091c3` (kicad-cli 10.0.4 in CI: ERC 6 intentional errors + 1 cosmetic warning; DRC 0 copper errors, 24 unconnected, silkscreen warnings only).

> **Superseded in part by `FINAL_ENGINEERING_REVIEW_2026-11-01.md`** (same day). Corrections from that review: LM51551 OVP worst case is **49.9–55.9 V** (52.8 V typical), not 51.4–54.2 V; bleeder C<sub>max</sub> 180.8 µF (10 kΩ still meets E-11: 4.4 s worst case); the detailed decision proposals there replace the recommendations here.
>
> Bench-only prototype: water or 0.9 % saline, never on a person or an animal, no real insulin. Nothing below is a validation result. **No electrical or safety decision has been made in this review.** Every recommendation is a proposal for the owner.

## How to read the evidence labels

| Label | Meaning |
| --- | --- |
| **[REPO-DS]** | Read from a datasheet or manual stored in `docs/datasheets/` (text extracted and quoted) |
| **[REPO]** | Stated in a project document (requirements, decision log, design notes) |
| **[CALC]** | Calculated here from [REPO]/[REPO-DS] numbers; the inputs are listed |
| **[SIM]** | Simulation in `validation/sim/` (LTspice 10 Oct, ngspice 1 Nov): open-loop, transformer = specification |
| **[WEB-2ND]** | From a web search summary or a distributor/forum page, **not** from the manufacturer's document. The session's network policy blocked st.com, ti.com, jst-mfg.com and coilcraft.com, so the primary documents could not be read. **Must be confirmed before use.** |
| **[OWNER]** | Decision that belongs to the owner |

---

## 1. STM32WBA55: power supply, clock and RF implementation (U-05)

**Already established**

- Pin functions: all 41 assigned functions verified against the STM32CubeMX 6.18.1 database, with 0 failures [REPO] (`validation/logs/pinmap_check.md`).
- Six supply pins are deliberately left on placeholder nets: VLXSMPS, VDD11, VDDANA, VDDHPA, VDDRF and VDDRFPA. These are the 6 ERC errors, which CI confirmed on 1 Nov.
- The RF output is a U.FL connector (J501) behind a 3-element pi placeholder: C514, L502, C515 (owner decision, 10 Oct) [REPO].
- The HSE crystal is Y501 32 MHz, with load capacitors C516/C517 DNP (A-8) [REPO].

**Missing**

ST DS (STM32WBA5x datasheet), RM0493, errata, the NUCLEO-WBA55CG (MB1803) schematic and board files, and the RF hardware application note. None of these is in the repository [REPO].

**Research findings, all [WEB-2ND]; none applied to the design:**

- **The relevant ST documents are identified:**
  - **AN5948**, *How to develop RF hardware using STM32WBA MCUs*.
  - **AN6373**, *Guidelines to enable the embedded SMPS of STM32WBA series*.
  - The STM32WBA5xxx datasheet, served by st.com as `stm32wba52ce.pdf`.
- The embedded SMPS is described as a step-down converter whose output feedback is tied internally to VDD11. It runs at 3 MHz and needs an input capacitor, an inductor and an output capacitor, with an optional ~10 nH noise-blocking inductor.
- **Capacitor values quoted in the summaries:** about 4.7 µF on VDD11 and about 470 nF on VDDHPA. The summaries also describe a 100 nF VDDRFPA capacitor in one AN5948 configuration.
- **LDO-only mode:** VDDSMPS and VLXSMPS are to be grounded when the SMPS inductor is not fitted.

**Recommendation**

1. Obtain DS, AN5948, AN6373 and the MB1803 schematic. Either allow st.com in the session network policy or have the owner supply the PDFs.
2. Copy ST's MB1803 values for L501, C509–C515 and L502, and for the HSE/LSE parts, unchanged (P-06, L-6).
3. Decide between SMPS mode and LDO mode. The LDO option, with VDDSMPS and VLXSMPS grounded, needs no inductor and frees board area, at the cost of higher current. That is a battery-life trade-off: see §9.
4. Then re-place Y501 next to pins 41/42 and route the 12 group-A nets. Route the RF trace as 50 Ω on the chosen stack-up (U-20).

**Owner decisions:**

- SMPS or LDO mode [OWNER].
- Whether to keep the U.FL connector or add an on-board antenna. An antenna changes certification scope and needs ST reference geometry [OWNER].

---

## 2. Flyback transformer selection (U-04)

**Already established**

- Specification in `FLYBACK_DESIGN.md` §4 [REPO] [CALC]:
  - n = Ns/Np = 5 (±3 %);
  - Lp 7.3 µH nominal (5–10 µH acceptable);
  - primary Isat ≥ 5 A, Irms ≥ 2.5 A; secondary Irms ≥ 0.3 A;
  - leakage ≤ 2 % of Lp;
  - ≥ 100 V working between windings (non-isolated topology);
  - 300 kHz.
- The 5 A saturation requirement comes from R305 = 22 mΩ and the LM51551 current-limit threshold of 93–107 mV [REPO-DS SNVSB75E]: 107 mV / 22 mΩ = 4.86 A.
- The power stage works with this specification in simulation [SIM]. At 3.0 V in, 100 mA out (snubber fitted):

  | Quantity | LTspice | ngspice |
  | --- | --- | --- |
  | Primary peak (A) | 3.39 | 3.45 |
  | VDS max (V) | 18.5 | 18.7 |
  | Efficiency | 82 % | 80 % |

- **Peak-current note from the ngspice waveforms** (`docs/report/figures/sim_flyback_waveforms_3v0.png`):
  - The primary peak occurs at switch-**on**: it is the D301 reverse-recovery current reflected to the primary, not the end-of-ramp current (about 3.1 A).
  - The LM51551's leading-edge blanking must cover it. Re-check this once real transformer and diode parasitics are known.

**Missing:** a real part, with its datasheet, footprint and measured leakage.

**Research findings [WEB-2ND]**

- **Coilcraft Hexa-Path (HP/HPH):**
  - Six identical 1:1 windings that can be connected in series or parallel, intended as inductors or flyback transformers in the 5–50 W range. HPH variants have higher inductance than HP.
  - One forum thread describes an HPH1-1400L wired as a 1:5 step-up, but gives no ratings.
  - The electrical tables are in Coilcraft documents 613-1 and 613-2, which could not be opened.
- **The 1+5 problem:** a 1+5 connection puts the full primary current through **one** 1:1 winding. Whether any Hexa-Path size has a single-winding Isat ≥ 5 A at Lp ≈ 7 µH is unverified.

**Recommendation**

1. Read Coilcraft 613-1/613-2. Check a 1 (primary) + 5 (series secondary) connection against §4: Lp of one winding, Isat of one winding ≥ 5 A, and leakage.
2. If no catalogue part fits, request a custom-wound quote against the §4 table. The owner has said this is a funded project with lab access [REPO]. The specification is complete enough to send to a magnetics vendor.
3. Replace `XFMR_PLACEHOLDER_4P` with the real footprint. Re-run the open-loop simulation (`scripts/sim_flyback_ngspice.py`) with the real Lp, leakage and winding resistance. Then re-tune the clamp and snubber (§3).

**Owner decision:** catalogue part or custom winding, cost and lead time [OWNER].

---

## 3. Flyback compensation and snubber (part of U-04, A-23, A-25)

**Already established [REPO] [CALC] [SIM]**

| Part | Value | Basis |
| --- | --- | --- |
| Clamp (D302 PMEG10020ELR, R306, C308) | 390 Ω / 22 nF | Simulated; D302 rated 100 V, 2 A [REPO-DS] |
| Clamp loss | 0.35–0.43 W in R306 | R306 = 390 Ω 1 W in 2512 (about 43 % of rating) |
| D301 snubber (R313, C312) | 220 Ω / 100 pF | Without it, D301 reverse ringing reached its 200 V breakdown in LTspice |
| Snubber loss | 0.14–0.17 W in R313 | R313 is a **1206**; its power rating is not recorded, because the part is TBD |
| FET drain peak | 18.5–18.7 V | 74–75 % of the CSD16340Q3's 25 V V<sub>DS</sub> [REPO-DS]; meets the proposed 80 % rule with little margin |
| Compensation | R303 3.01 kΩ, C306 180 nF, C307 3.3 nF | Crossover about 3 kHz, from a hand calculation with assumed 50 µF effective output capacitance (A-25) |
| Right-half-plane zero | About 30 kHz at 3.0 V / 100 mA | Hand calculation |

**Missing**

- A control-loop model.
- Real leakage inductance.
- The PMD401's input capacitance and cable.

There is no LM51551 model in LTspice or ngspice [REPO].

**Research findings [WEB-2ND]**

- A TI E2E answer says the LM5155 product folder carries an *unencrypted PSpice model (transient and average)* for the LM5155-Q1. Users report problems importing it into TINA; TI suggests *PSpice for TI*.
- The LM51551 shares the LM5155 control architecture (SNVSB75E covers both [REPO-DS]). Whether the model also covers the LM51551's hiccup option is not stated.

**Recommendation**

1. After §2, run the LM5155 PSpice model in PSpice for TI with the real transformer. Target a crossover of at most one fifth of the worst-case right-half-plane zero (≤ 6 kHz), with phase margin ≥ 45° over 3.0–4.2 V and 6–100 mA.
2. Measure on the bench with a Bode injection resistor in the FB divider. This is check PW-03/PW-04 in `VALIDATION_PLAN.md`.
3. Re-tune R306/C308 for VDS ≤ 20 V at the real leakage. Specify R313 with ≥ 0.5 W rating (about 3× the simulated loss): a 2010 or 2512 package if the 1206 part cannot meet it.
4. Size the snubber and clamp from measured leakage, not from the 2 % assumption.

**Owner decision:** none until §2 is closed. The R313 package change needs approval because it alters the footprint.

---

## 4. 48 V output switch and bleeder (U-06, E-04, E-11)

**Already established**

- K-12 asks for a "switched output". The owner (10 Oct) placed Q302/Q303/R309/R310 as DNP placeholders and bridged the switch with R311 = 0 Ω. R312 is a DNP bleeder placeholder in a 2512 footprint [REPO].
- The decision log notes: *"A flyback has no DC input-to-output path, so EN low de-energises the rail."* With the LM51551 disabled, no DC path exists from VBAT to the output (transformer plus D301).
- **Requirements:**
  - E-04 (DECIDED): rail on only while dosing; the off state truly disconnects the load.
  - E-11 (PROPOSED): rail below 60 V in every fault; below 5 V within 5 s of switch-off.
- **Capacitance on the rail [REPO]:**
  - C309 and C310: 2.2 µF / 100 V X7R each, with DC-bias derating at 48 V unknown (≤ nominal).
  - C311: 47 µF / 100 V.
  - C702: 100 µF / 100 V.
  - Total C<sub>nom</sub> = 151.4 µF.

**Calculation [CALC]: bleeder for E-11**

Assumption: +20 % tolerance on the electrolytic capacitors, a typical figure that is not from their datasheets because the capacitor series is TBD. That gives C<sub>max</sub> ≈ 180.8 µF.

| Start voltage | Condition | R for < 5 V in 5 s |
| --- | --- | --- |
| 50.4 V | normal maximum | R ≤ 5 s / (180.8 µF × ln(50.4/5)) = **12.0 kΩ** |
| 55.9 V | LM51551 OVP worst case (corrected) | R ≤ 5 s / (180.8 µF × ln(55.9/5)) = **11.5 kΩ** |

With **R312 = 10 kΩ**:

| Check | Result |
| --- | --- |
| Discharge time, worst case (180.8 µF, from 55.9 V to 5 V) | 4.4 s |
| Discharge time, nominal (151.4 µF, from 50.4 V) | 3.5 s |
| Dissipation while the rail is on | 0.25 W at 50.4 V; 0.31 W at 55.9 V |
| Added load on the flyback | about 5 mA (design load 100 mA) |

Because E-04 keeps the rail on only while dosing, the energy cost is roughly 0.25 W × motor-on time. That is about 0.03 Wh/day at a 50 U/day profile (assumed; see §9).

**Recommendation**

- **Option A (recommended):**
  - Delete the Q302, Q303, R309 and R310 placeholders and keep R311.
  - Fit R312 = 10 kΩ, rated **≥ 0.5 W and ≥ 100 V working**: 2512 thick film, or 2 × 20 kΩ. The voltage rating must be read from the chosen resistor's datasheet.
  - This meets E-04 through the flyback's disable and E-11's discharge clause with fewer parts and one fewer series element in the motor path.
  - It also removes the SW48_GATE group-B unconnected item.
- **Option B:** design the K-12 high-side switch. It needs a P-MOSFET of at least the 100 V class with a level-shifted gate and its own fault analysis. Only necessary if the owner reads E-04 as requiring a semiconductor disconnect in addition to the converter disable.

**Owner decisions:**

- Option A or B.
- Accept E-11 as a requirement (it is PROPOSED).
- The R312 value and part [OWNER].

---

## 5. Independent 48 V over-voltage protection (U-23, E-03, E-11)

**Already established**

- The LM51551 over-voltage threshold is **107 / 110 / 113 % of VREF, sensed on FB** [REPO-DS SNVSB75E, electrical characteristics]. With VREF 0.99–1.01 V and R307/R308 = 470 kΩ/10 kΩ, the output stops at about 52.8 V typical, 49.9–55.9 V worst case [CALC, corrected in the final review] while the divider is intact.
- **An open R307/R308 or a lifted FB pin removes all regulation and over-voltage protection.** The converter then runs at current limit (93–107 mV / 22 mΩ ≈ 4.2–4.9 A primary [REPO-DS]). The output can rise past the 100 V capacitor rating; nothing else limits it. This is an uncovered single fault.
- **Setpoint tolerance [CALC]:** VREF ±1 % and 1 % resistors give 46.6–49.4 V static. That is inside E-03's 45.6–50.4 V, with about 1 V margin at the top (ripple 0.13–0.16 V p-p [SIM]).
- The OVP ceiling (up to 55.9 V worst case) is above the PMD401's 50.4 V upper limit (48 V ±5 %, PMD401 manual 150025-01 §3.2 [REPO-DS]). The LM51551's OVP protects touch voltage, not the driver.

**Options**

| Option | Description | Independent of | Limitation |
| --- | --- | --- | --- |
| A | Hardware comparator or voltage supervisor on a **separate** divider from +48V_RAW, open-drain output wired to FLY_EN (the existing kill node, which already pulls the LM51551 UVLO/EN low) | FB divider, both MCUs and firmware | Part TBD. A 50.4 V trip point inside the 49.4 V worst-case setpoint needs tight tolerance; a trip near 52 V protects E-11 but not the PMD401 maximum |
| B | Second divider into a spare STM32C031 ADC pin; supervisor firmware asserts the veto | FB divider and main MCU | Firmware-dependent; ms response |
| C | TVS clamp on the rail | Everything | A clamp cannot sit between 50.4 V and 60 V with practical tolerance, and the flyback can feed it watts continuously. Not recommended |

**Recommendation:** Option A for the fault ceiling (trip around 52–55 V, below 60 V), plus Option B as a monitor of the 45.6–50.4 V window. Use 0.1 % divider resistors on both dividers (also on R307/R308) to win back the setpoint margin. Select parts from manufacturer datasheets; none is chosen here.

**Owner decisions:** approve a schematic change; trip voltages; whether E-11 becomes DECIDED [OWNER].

---

## 6. Motor speed limiting and independent supervision (S-06, S-07, OPEN item 2)

**Already established**

| Fact | Source |
| --- | --- |
| Speed cap 15 steps/s (D-08, DECIDED), enforced only in main-MCU firmware | [REPO] |
| LL06 top speed about 15 mm/s (about 25 U/s) | [REPO] |
| PMD401 maximum waveform cycle rate 1500 Hz, about 5 µm per cycle | PMD401 manual [REPO-DS] |
| PMD401 servo mode: 16-bit signed speed over SPI; the motor stops if no SPI data arrives for about 10 ms; AEN low parks the motor in about 250 ms | PMD401 manual §5 [REPO-DS] |
| No stored maximum-speed parameter for servo mode found in manual 150025-01 | [REPO-DS] |
| Encoder A/B routed to supervisor TIM3 (ENC_A_S routed 31 Oct, ENC_B_S earlier); S-07 hardware complete | [REPO] |
| Veto (R403 pull-up, BSS138 on FLY_EN) and open-drain park (Q402) are in place | [REPO] |

**Calculation [CALC]: how fast must a runaway be stopped?** S-06 limits a single fault to 0.5 U extra.

- 0.5 U = 5 µL ÷ 16.69 nL/µm = **300 µm** of plunger travel.

| Speed | Time to deliver 0.5 U |
| --- | --- |
| Speed cap (15 steps/s × 4.5 µm = 67.5 µm/s) | 4.4 s |
| PMD401 maximum (1500 Hz × about 5 µm ≈ 7.5 mm/s) | **40 ms** |
| LL06 top speed 15 mm/s | **20 ms** |

**Stop paths available to the supervisor**

| Path | Time to stop | Can it meet 20–40 ms? |
| --- | --- | --- |
| AEN park | about 250 ms [REPO-DS] | **No** |
| 48 V veto (LM51551 off) | The rail decays through the PMD401's own load from 151 µF. At 100 mA that is about 0.66 V/ms. The PMD401's behaviour below 45.6 V is unknown | Unproven |
| **Stop SPI data** (PMD401 stops after about 10 ms without SPI) | ≈ 10 ms + supervisor detection (≈ 1 ms at full speed: more than 100 encoder counts per ms) | **Yes:** about 11 ms × 15 mm/s ≈ 165 µm ≈ 0.28 U. The supervisor cannot do this today because the main MCU drives the SPI bus directly |

**Recommendation**

1. **Hardware:** add a supervisor-controlled gate (single AND gate or tri-state buffer) in PMD_SCLK or PMD_MOSI, defaulting to blocked when the supervisor is in reset. This uses the PMD401's own SPI timeout as a fast, independent stop path. Keep the veto and park as the slower backups.
2. **Supervisor firmware:** a TIM3 encoder rate check against the cap, run every 1 ms, with a hard limit at about 1.5× the cap. On a trip: gate SPI, then veto, then park.
3. Ask PiezoMotor in writing whether the PMD401 can hold a maximum servo speed internally (OPEN item 2).

**Owner decisions:** approve the SPI gate (a schematic change); accept S-06/S-07 (PROPOSED) [OWNER].

---

## 7. J703 connector voltage rating (U-17)

**Already established**

- J703 is a JST SM02B-SRSS-TB (SH series, 1.0 mm pitch). This is the connector family PiezoMotor uses on the PMD401 itself [REPO-DS PMD401 manual §3.4; `pump_v2.kicad_dru` note].
- Its 0.4 mm pad-to-pad gap needs a scoped DRC exception against the 0.6 mm HV48 class.

**Research finding [WEB-2ND]**

| Source | Rating |
| --- | --- |
| Distributor listing | **50 V AC/DC**, 1.0 A (AWG #28) |
| Another listing | 50 V AC, 0.7 A |
| JST datasheet | Not read (jst-mfg.com outside the allowed network) |

**Comparison [CALC]**

| Voltage at J703 | Value | Against a 50 V rating |
| --- | --- | --- |
| Nominal | 48 V | 96 % |
| E-03 maximum | 50.4 V | **exceeds** |
| LM51551 OVP window | 52.8 V typical, 49.9–55.9 V worst case (corrected) | **exceeds** |
| E-11 fault ceiling | 60 V | **exceeds** |
| E-06 80 % rule (PROPOSED) | would need a rating ≥ 63 V | **fails** |

**Recommendation**

1. Confirm the rating in JST's own SH datasheet.
2. If it is 50 V, use a board-side connector with a manufacturer rating ≥ 100 V DC and ≥ 0.6 mm pad spacing for J703. Make up a cable with an SH housing at the PMD401 end, since the PMD401 side is the vendor's choice.
3. This also removes the `J703_vendor_connector_pitch` DRC exception.

**Owner decision:** connector change and cable assembly [OWNER].

---

## 8. High-voltage clearance requirements (P-03, CF-6, A-20, U-16)

**Already established**

- Net class HV48 (+48V_RAW, +48V_MOT, FLY_SEC) uses 0.6 mm on **all** layers [REPO]. CI DRC on 1 Nov: 0 clearance errors.
- Exceptions:
  - J703's own pads (0.35 mm rule).
  - Q301's own pads (0.127 mm), which are not an HV net.
- P-03 (PROPOSED): 0.6 mm outer, 0.1 mm inner, citing IPC-2221C.
- CF-6: an older note used 0.2 mm inner.

**Research finding [WEB-2ND]**

- Secondary sources quote IPC-2221B Table 6-1 for both 31–50 V and 51–100 V as **0.1 mm internal (B1)** and **0.6 mm external uncoated (B2)**.
- The coated-external values differ between sources.
- One vendor blog gives a conflicting table. The IPC-2221C text was not available.

**Relevant voltages [REPO] [SIM]**

| Node | Voltage |
| --- | --- |
| 48 V rail, normal | ≤ 50.4 V |
| 48 V rail, OVP ceiling | 55.9 V worst case |
| 48 V rail, E-11 fault limit | 60 V |
| FLY_SEC / D301 reverse | 88–97 V peaks in simulation (snubbed) |

These fall in the 51–100 V row.

**Recommendation**

- Keep the conservative 0.6 mm on every layer for HV48. If the quoted B1/B2 values are confirmed, this satisfies both, and costs little on this board.
- Purchase or borrow IPC-2221C to confirm and close CF-6.
- Resolve the J703 exception through §7.
- Keep FLY_SEC in HV48 because of the 97 V ringing.

**Owner decision:** sign off P-03 with the confirmed table [OWNER].

---

## 9. Battery and current-budget decisions (E-01, E-05, E-09, E-10, U-18, U-24)

**Already established**

- Cell: Molicel INR18650-P28A (Rev A item 11) [REPO]. Protection, a 5 A fuse and a master switch are required (E-01).
- **BQ25188** [REPO-DS SLUSFJ3]:
  - 5 mA–1 A configurable fast charge.
  - Battery regulation 3.6–4.65 V.
  - Linear charger.
  - Default ICHG 10 mA; firmware must set it [REPO].
- **TPS62840** [REPO-DS SLVSEC6D]: 1.8–6.5 V input, up to 750 mA.
- **Flyback input current at full PMD401 speed (100 mA at 48 V)** [SIM], at 3.0 V:

  | Simulator | Input current |
  | --- | --- |
  | LTspice | 2.0 A |
  | ngspice | 2.07 A |

  E-05's 2.1 A budget is reached.

**Research finding [WEB-2ND]:** Molicel P28A distributor data:

| Parameter | Value |
| --- | --- |
| Capacity | 2800 mAh typical (minimum quoted as 2600–2700 mAh, depending on the source) |
| Charge cut-off | 4.2 V |
| Maximum continuous discharge | 35 A |
| Discharge cut-off | 2.5 V (one source) |

**Calculations [CALC]**

- **Motor load at dosing speed** (inputs: LL06 "5 mW per Hz of step rate" [REPO], PMD401 6 mA idle at 48 V [REPO-DS], the 15 steps/s cap):

  | Load | Power |
  | --- | --- |
  | PMD401 idle | 0.29 W |
  | Motor at the cap | 0.075 W |
  | Total at 48 V | about 0.37 W |
  | Battery side (at 80 % efficiency) | about **0.46 W ≈ 0.15 A at 3.0 V** |

  Caveat: the PMD401's own drive losses at 15 Hz are unknown; MT-07 must measure them. The 2.1 A case only occurs at full speed, which means a runaway or a deliberate fast move.
- **Energy budget (illustrative):** the cell is 2.8 Ah × 3.6 V ≈ 10 Wh (distributor nominal).
  - At an *assumed* 50 U/day, motor-on time is 50 U ÷ 0.11 U/s ≈ 455 s. That costs about 0.06 Wh (at 0.46 W) plus 0.03 Wh (bleeder, §4).
  - **The idle power dominates.** Meeting E-10 (3 days, PROPOSED) needs average idle ≤ about 0.13 W, with 10 % reserve.
  - The Rev A figure is 0.11 W (unmeasured; it includes Nucleo boards). The Rev B idle figure, including BLE, must be measured (BT-01).
- **Charge current:** the BQ25188 is linear, so P ≈ (V<sub>BUS</sub> − V<sub>BAT</sub>) × I<sub>CHG</sub>. From 5 V USB:

  | Charge current | Dissipation at 3.0 V cell | Dissipation at 4.2 V cell |
  | --- | --- | --- |
  | 1 A | 2.0 W | 0.8 W |
  | 0.5 A | 1.0 W | 0.4 W |

  The package is a 1.1 × 1.6 mm WCSP (A-12).

**Recommendation**

1. Set the charge current to about 0.5 A (about 0.18C) until the BQ25188 thermal data (θ<sub>JA</sub>, thermal regulation) and Molicel's standard-charge current have been read. Record it as a firmware constant.
2. Keep E-05 at 2.1 A for normal operation. Size every part in the battery path (F101, J101, J102 and its switch, VBAT tracks, Q301, T301, R305) for the **current-limit** case, ≥ 5 A peak. F101 (5 A, 2920 footprint) and the protection board (5 A) already assume this.
3. Measure PMD401 current at dosing speed (MT-07) and Rev B idle power (BT-01) before fixing the cell size.

**Owner decisions:**

- The cell for Rev B (keep the P28A or not).
- Battery connector, fuse part and master switch (B.19, B.20).
- Charge current.
- Whether E-10 stays at 3 days [OWNER].

---

## Summary of owner decisions

| # | Decision | Blocks |
| --- | --- | --- |
| 1 | Supply ST documents, or allow st.com; SMPS vs LDO; U.FL vs antenna | 12 unconnected group-A items, 6 ERC errors, RF |
| 2 | Transformer: Coilcraft Hexa-Path check or custom winding | Flyback, compensation, layout around T301 |
| 3 | R313 package (≥ 0.5 W) | Snubber reliability |
| 4 | 48 V output: Option A (delete switch placeholders, fit R312 10 kΩ ≥ 0.5 W ≥ 100 V) or B; E-11 status | SW48_GATE item, E-04/E-11 |
| 5 | Secondary OVP (hardware comparator + supervisor ADC), trip points, 0.1 % dividers | Uncovered single fault |
| 6 | Supervisor-controlled SPI gate; S-06/S-07 sign-off; PiezoMotor question | Runaway containment |
| 7 | J703: confirm the JST rating; ≥ 100 V board connector + cable | 50 V rating vs 50.4–60 V |
| 8 | Sign off HV clearance (P-03) after reading IPC-2221C | CF-6 |
| 9 | Cell, connector, fuse, switch, charge current, E-10 | BOM, battery life |

## Sources (web; secondary, to be confirmed against the manufacturer documents)

- ST application notes and datasheet located by search: [AN5948](https://www.st.com/resource/en/application_note/an5948-how-to-develop-rf-hardware-using-stm32wba-mcus-stmicroelectronics.pdf), [AN6373](https://www.st.com/resource/en/application_note/an6373-guidelines-to-enable-the-embedded-smps-of-stm32wba-series-microcontroller-stmicroelectronics.pdf), [STM32WBA5xxx datasheet](https://www.st.com/resource/en/datasheet/stm32wba52ce.pdf), [AN5948 mirror](https://manuals.plus/m/71bbef8705ea623bf6a68e14dbfec25d111c954e33241d0dbfeafd524bf0efd3.pdf)
- TI LM5155 models: [TI E2E: unencrypted PSpice model for LM5155](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1109410/lm5155-unencrypted-spice-model-for-lm5155), [TI E2E: TINA import](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/780617/tina-spice-lm5155-lm5155-q1-pspice-cannot-import-into-tina)
- Coilcraft Hexa-Path: [configurable transformers](https://www.coilcraft.com/en-us/products/transformers/power-transformers/configurable-transformers/), [Hexa-Path brochure](https://www.coilcraft.com/getmedia/936400ae-3cbc-4381-aed1-ae101ef7a35e/hexa-path.pdf), [ADI forum: HPH1-1400L as 1:5](https://ez.analog.com/adiacademy/university-program/f/q-a/603661/figure-8-transformer-dc-dc-booster-delivers-1-ma-at-15-v/598488)
- JST SM02B-SRSS-TB ratings (distributors): [Derf](https://derf.com/product/sm02b-srss-tblfsn), [Datasheets.com](https://www.datasheets.com/jst/sm02b-srss-tb-lf-sn-), [LCSC](https://www.lcsc.com/product-detail/C160402.html)
- IPC-2221 Table 6-1 (secondary): [Sierra Circuits](https://www.protoexpress.com/?p=848), [Sierra Circuits blog](https://protoexpress.com/blog/ipc-2221-circuit-board-design), [Altium](https://resources.altium.com/p/using-an-ipc-2221-calculator-for-high-voltage-design), [Siemens](https://blogs.sw.siemens.com/electronic-systems-design/2025/04/29/pcb-high-voltage-spacing-what-every-engineer-should-know/)
- Molicel P28A (distributors): [IMR Batteries PDF](https://www.imrbatteries.com/content/molicel_p28a.pdf), [Compel](https://www.compel.ru/infosheet/MOLICEL/INR-18650-P28A), [akkuteile.de](https://www.akkuteile.de/en/lithium-ionen-battery/size-18650/molicel/molicel-inr18650-p28a-2800mah-35a-lithium-ion-battery-3-6v-3-7v_100662_3013)
