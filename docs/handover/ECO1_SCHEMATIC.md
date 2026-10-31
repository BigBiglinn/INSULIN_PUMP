# ECO1: schematic changes before Rev B layout completion

Bench-only prototype: water or 0.9 % saline, never on a person or animal, never with insulin.

**Status:** schematic changed at tag `sch-eco1-done`. **PCB copper not changed:** `pump_v2.kicad_pcb` is identical to `route-stage5a-done`, so schematic parity now reports the expected differences (below). Electrically untested, incomplete, not fabrication-ready. Calculations and simulations here are not hardware evidence.

## 1. Verification verdicts

| # | Item | Verdict | Result |
|---|---|---|---|
| 1 | WBA55 power (E1–E6) | **VERIFIED** after corrections | Matches DS14127 Fig. 15 and AN6373; no source conflicts |
| 2 | LM51551 soft start (E7) | **VERIFIED by simulation; REQUIRES HARDWARE TEST** | 47 nF fails; 1 µF passes every corner |
| 3 | HPH6-0090L (E8) | **REQUIRES HARDWARE TEST** (leakage) | All published limits pass; leakage is unpublished |
| 4 | RF (E9) | **NEEDS CORRECTION** (widths), now corrected | 63 Ω: 0.20 mm; 50 Ω: 0.32 mm; both 0.25 mm gap, bare copper |
| 5 | READY/FAULT (E10/E17) | **NEEDS CORRECTION**, now corrected | BSS138 level shifters replace the pin moves |
| 6 | Clocks (E13/E14) | HSE **VERIFIED**; LSI2 **NEEDS CORRECTION** | LSE crystal stays fitted |
| 7 | 48 V protection (E15/E16) | **NEEDS CORRECTION**, now corrected; **REQUIRES HARDWARE TEST** | Bleeder 10 k, not 12 k; TVS SMBJ48A, not 51 V standoff |
| — | E11 FLY_PGOOD to PA15 | **WITHDRAWN** | Pin 25 also has no route with today's copper (scratch test). No MCU pin changes |

## 2. Evidence

**Item 1.** VDDRF on VDD; VDDANA on VDD11; VDDRFPA on VDD11 (limits TX to about +3 dBm, AN6373 §7); VDDHPA capacitor only (DS14127 §3.12, Fig. 15). AN6373: 2.2 µH ±20 %, RDC < 500 mΩ, Iop > 200 mA, Isat > 800 mA; COUT 4.7 µF ±20 %; CIN 10 µF. The 10 nH coil and VDDSMPS bead are AN6373 recommendations, and the VDDRFPA bead is conditional ("may be necessary"). All three are fitted as used on MB1803. ST's VDDA bead is omitted: DS14127 requires only 100 nF + 1 µF, and VDDA serves only the VBAT ADC.

**Item 2.** `validation/sim/lm51551_startup.py`: cycle-by-cycle model with the datasheet hiccup rule (not a vendor model). Corners: VIN 3.0/4.2 V, COUT 150/181 µF, VCLTH 93/107 mV, ISS 9/11 µA, with 6 mA PMD401 idle and the bleeder.

| CSS | Result |
|---|---|
| 47 nF | Fails every corner: repeated hiccup, stuck below 11 V |
| 220 nF | Fails every corner |
| 470 nF | Mixed, not robust |
| **1 µF** | **Passes every corner: 91–111 ms, 0 hiccups, peak 3.09 A against the 4.2 A minimum limit** |

With a full 100 mA load during start, 1 µF still fails at 3.0 and 3.4 V, so **the PMD401 must stay parked until FLY_PGOOD**. Load-step response and loop stability need a hardware test.

**Item 3.** Coilcraft Doc 613 (Rev 11/23/21) against this design:

| Check | Requirement | HPH6-0090L | Result |
|---|---|---|---|
| Lp | 5–10 µH (7.3 calc) | 7.29 µH ±5 % | Pass |
| Turns ratio | 5 | 1 primary, 5 series windings | Pass |
| Saturation | ≥ 5 A | 4.60 × 6 ÷ 1 = 27.6 A | Pass |
| Volt-time | 9.9 V·µs at 4.2 V | 131.9 V·µs | Pass |
| Primary RMS | ≥ 2.5 A required (about 2.3 A) | 2.90 A | Pass, 0.16 W copper loss |
| Secondary RMS | ≥ 0.3 A | 2.90 A, 0.15 Ω | Pass |
| Isolation | About 100 V peak | 500 Vrms per winding | Pass |
| Frequency | 298 kHz | Up to 1 MHz | Pass |
| Temperature | Max part +125 °C; Irms limits apply to −40 to +85 °C ambient | 40 °C rise at rated current, all windings | Pass on paper |
| **Leakage** | **≤ 2 % assumed by clamp design** | **Not published** | **Unknown** |
| Size | 12 × 12 mm placeholder | 32.65 × 26.75 × 13.6 mm | **48 V block re-placement** |

Connections: primary 3 (dot) to VBAT, 10 to FLY_SW. Secondary from GND: 1 (dot)–12, 2–11, 4–9, 5–8, 6–7 to FLY_SEC, dots aiding. Doc 613 restricts medical or high-risk use without Coilcraft's approval; this is a bench prototype. Stock not checked.

LTspice sweep (`validation/sim/hph6_leakage.cir`, `.log`), fixed duty, generic device models. Vout had not fully settled in the low-k runs, so read these as indicative; efficiency is not meaningful.

| k (leakage ≈ 1−k²) | Vds at 3.0 V | Vds at 4.2 V | Clamp power (max) | D301 reverse (max) |
|---|---|---|---|---|
| 0.99 (2 %) | 18.2 V | 19.4 V | 0.40 W | 96 V |
| 0.98 (4 %) | 20.0 V | 21.7 V | 0.53 W | 99 V |
| 0.97 (6 %) | 20.2 V | 23.0 V | 0.62 W | 102 V |
| 0.95 (10 %) | 20.7 V | 24.2 V | 0.70 W | 104 V |

Q301 is rated 25 V (80 % rule: 20 V), R306 is 1 W, D301 is 200 V. **Action:** buy samples and measure primary inductance with all secondaries shorted **before PCB release**. Pass: ≤ 2 %. 2–4 %: lower R306 (bench tune). Above 4 %: choose another primary winding or re-select.

**Item 4.** `validation/sim/rf_line_solver.py`: 2-D finite-difference solver. It gives 60.6 Ω for ST's own 0.30/0.15 mm example, which ST specifies as 63 Ω (4 % low). ST's 0.45/0.13 mm line gives 55.7 Ω over Layer 3 but 22.5 Ω over In1, consistent with ST's Layer 3 reference: do not copy that width onto a solid In1 plane. Stack assumed: JLC04161H-7628, 0.2104 mm prepreg, εr 4.4, 35 µm copper (secondary source; confirm in JLCPCB's calculator before ordering).

| Line | Width | Gap | Z0 bare | Sensitivity |
|---|---|---|---|---|
| U501.37 to FL501 | 0.20 mm | 0.25 mm | 62.9 Ω | ±3 Ω for εr ±0.2, h ±0.02 mm |
| FL501 to J501 | 0.32 mm | 0.25 mm | 50.5 Ω | Same |

Solder mask lowers Z0 by about 8 %, so open the mask over the RF lines (also AN5948 §7.6). Earlier estimates of 0.25 and 0.36 mm were wrong. Reference: solid In1 GND under the whole path, no vias. Manufacturable per JLCPCB's published limits: 0.09 mm track/space; 0.32 mm pads above the 0.2 mm BGA minimum; 0.28 mm mask dam above 0.10 mm. Put GND vias beside the bumps, not in the pads. MLPF placement is by machine only (DS14446 §3.4). The U.FL pad and QFN pin transitions are not modelled. FL501 pads: A1 IN, A3 OUT, A2/B1/B2/B3 GND.

**Item 5.** Earlier moves to FT pins were not enough: with VDD = 0 (master switch off) the FT limit falls to 4 V while the PMD401 can stay alive on the discharging rail, and PB4 has a reset pull-up (RM0493 §14.4.2). PB15 is `TT`. Fix: non-inverting BSS138 shifters with gate on +3V3 and 100 k to +3V3. The pin never sees above 3.3 V, at any PMD401 rail, in reset or unpowered. No PMD401 rail answer is needed for READY or FAULT. Firmware: both read LOW when the PMD401 is unpowered, so trust them only after FLY_PGOOD.

**Residual risk, outside this item:** PMD_SS, SCLK and MOSI (`FT_a`) have PMD401 pull-ups of 10–20 k to an unknown rail. If that rail is 5 V, those pins can exceed 4 V during the seconds after master-switch-off. Measure the rail before PCB release; if 5 V, add the same shifters to those three lines.

**Item 6.** HSE: NX1612SA, 8 pF load (AN5948 Table 5), inside DS14127's 8–18 pF; internal trim, no external capacitors. Firmware centres it with HSETRIM. LSE: ST documents LSI2 as usable for the radio sleep timer, but it needs periodic calibration, and field reports conflict. ST's wiki pages timed out, so this rests on search excerpts. The crystal costs three small parts and is ST's validated configuration, so **Y502 is fitted** (NX1610SE, 6 pF per MB1803). Requires moving it beside pins 16/17 and re-routing HB_S2M. Leave PC13 unused (ES0592 §2.2.10).

**Item 7.** Worst-case COUT 182 µF. 12 k gives 5.04 s, which misses the 5 s limit. **10 k gives 4.21 s** (3.47 s at 150 µF), 0.25 W at 50.4 V, 0.29 W at 54.2 V: 2512 1 W is adequate; confirm element voltage ≥ 100 V. It adds about 0.1 A at the 3.0 V input while the rail is on (worsens U-24).

A 51 V standoff TVS can reach 62.7 V breakdown, above the 60 V ceiling. **SMBJ48A:** VR 48 V, VBR 53.3–58.9 V at 1 mA, VC 77.4 V at 7.8 A (distributor data; Littelfuse datasheet not retrieved). Fault current here is at most about 0.2 A, so the clamp should sit near VBR: an estimate. About 12 W sustained exceeds its rating, so it is expected to fail short, then the converter hiccups. Sacrificial, and needs replacing after a fault. LM51551 OVP remains primary at 51.4–54.2 V; that top end still exceeds the PMD401's 50.4 V, in a fault only. Setpoint 47.43–48.58 V with 0.1 % resistors. Slightly above VR at the very top: confirm leakage on the bench.

## 3. Change list

| Ref | Old | New | Consequence |
|---|---|---|---|
| U501.2 | +3V3 | WBA_VDDSMPS | Filtered through FB501 |
| U501.39 | WBA_VDDANA | WBA_VDD11 | Powered from SMPS output |
| U501.40 | WBA_VDDRF | +3V3 | Powered |
| U501.43 | Unpowered unless R513 fitted | WBA_VDDRFPA via FB502 | TX about +3 dBm |
| L501 | L_SMPS_TBD, VLX to VDD11 | 2.2 µH LQM21PN2R2MGH, WBA_VLX_L to VDD11 | Stable SMPS |
| L503 | — | **New** 10 nH LQG15HS10NJ02D | RF noise reduction |
| FB501, FB502 | — | **New** 47 Ω LSMGA160808T470RG | SMPS and PA filtering |
| C506 | 100 nF, +3V3 | 10 µF/10 V GRM188C81A106MA73, VDDSMPS | SMPS input cap |
| C507 | 4.7 µF 0603 | 10 µF/10 V 0805 | VDD bulk |
| C509 | TBD | 4.7 µF GRM155R60J475ME47D | SMPS output cap |
| C510 | TBD | 470 nF | VDDHPA |
| C511, C512, C513 | TBD | 100 nF | Decoupling; C511 on VDD11, C512 on +3V3 |
| C520, C521 | — | **New** 1 µF | VDDA; FB501 supply side |
| R510, R511, R512 | DNP 0R | **Deleted** | Prevents wrong supply links |
| R513 | DNP 0R_VERIFY | DNP 0R, +10 dBm option | Never with FB502 |
| C514, C515, L502 | RF placeholders | **Deleted** | Replaced by FL501 |
| FL501 | — | **New** MLPF-WB-04D3 | RF filter; new footprint |
| Y501 | 2016 placeholder | NX1612SA, new footprint | Closer to pins |
| C516, C517 | DNP TBD | **Deleted** | Internal load trim |
| Y502 | DNP 3215 | **Fitted** NX1610SE, new footprint | LSE available |
| C518, C519 | DNP TBD | **Fitted** 6 pF C0G | LSE load |
| Q701, Q702 | — | **New** BSS138 | READY and FAULT shifters |
| R715, R716 | — | **New** 100 k | Shifter pull-ups |
| R706, R707 pin 1 | PMD_READY_M, PMD_FAULT_M | PMD_READY_D, PMD_FAULT_D | Now on shifter drains |
| T301 | 4-pin placeholder | HPH6-0090L, 12 pins, nets FLY_SEC_A–D | **48 V block re-placement** |
| C305 | 47 nF | 1 µF/10 V X7R | Rail rise about 100 ms |
| R307, R308 | 470 k, 10 k 1 % | 470 k, 10 k 0.1 % | Tighter setpoint |
| R312 | DNP TBD | **Fitted** 10 k 1 % 2512 | E-11 discharge |
| D303 | — | **New** SMBJ48A | 60 V clamp |
| Q302, Q303, R309, R310 | DNP | **Deleted** | K-12 switched output dropped; SW48 nets gone |
| L201 | 0603 footprint | DFE201612E-2R2M, Murata 2016 footprint | Part now fits |
| R107, R108 | 1 M 1 % | 200 k 1 % | 30 mV max leakage error at VBAT; 10.5 µA drain |

**No MCU pin assignments changed.** Project net classes gain FLY_SEC_A–D in HV48.

## 4. Check results at this checkpoint

| Check | Result |
|---|---|
| Netlist against this plan | 32 nets checked, 0 failures; deleted parts and SW48 nets absent |
| Pin map (CubeMX) | 0 failing assignments |
| ERC | 5 `power_pin_not_driven`, 1 cosmetic U701 warning (6 errors before) |
| Parity on a scratch copy | 98 issues, **expected until the PCB is updated**: 11 missing and 12 extra footprints, 21 net conflicts, 29 symbol and 25 field mismatches |
| PCB file | Identical to `route-stage5a-done` |

**The 5 ERC errors are left visible, not masked.** U501 pins 3, 38, 39, 43 and 2 are declared power inputs but are fed by the SMPS output, an internal regulator or a bead, which ERC can't recognise. No PWR_FLAGs were added.

## 5. Still open

- PMD_SS, SCLK and MOSI residual risk (§2, item 5).
- T301 sample measurement; stock for T301, MLPF and crystals.
- D701–D709 TVS parts, F101 part, U101 land drawing.
- U501 fan-out, including FLY_PGOOD at pin 28: no route exists on today's copper. If the fan-out redo cannot escape it, a pin-change ECO returns as a fallback.

**Firmware obligations:** PMD401 parked until FLY_PGOOD; READY and FAULT valid only after FLY_PGOOD; SMPS and TX power configured for VDDRFPA on VDD11; HSETRIM centring; PC13 unused.
