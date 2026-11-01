# Rev B PCB update stages (after ECO1 and ECO2)

Bench-only prototype: water or 0.9 % saline, never on a person or animal, never with insulin. Incomplete, electrically untested, not fabrication-ready. Passing DRC does not show the circuit works.

| Tag | State |
|---|---|
| `route-stage5a-done` | Last routing checkpoint before the schematic changes (preserved) |
| `sch-eco1-done`, `sch-eco2-done` | Schematic changes; PCB unchanged (preserved) |
| `pcb-eco-before` | = `sch-eco2-done`, the restore point for this work |
| `pcb-p1-placement` | Stage P1 below |

## Stage P1: footprints and placement (no new signal routing)

**Method:** `scripts/pcb_eco.py` with `validation/routing/pcb_p1_plan.json`. The board was updated in place, not regenerated. Full itemised record: `validation/routing/pcb_p1_log.txt`. Per-net copper summary: `validation/routing/pcb_p1_copper_changes.txt`. Picture: `validation/routing/pcb_p1_placement.png`.

**Results (kicad-cli 10.0.3, on the project files):**

| Check | Before | After P1 |
|---|---|---|
| ERC | 5 `power_pin_not_driven` + 1 cosmetic | Same, no new types |
| DRC errors other than unconnected | 0 | **0** |
| Parity | 123 (schematic ahead of PCB) | **0** |
| Unconnected pairs | 48 | **81** (expected: new parts and removed copper) |
| Footprints | 147 | 154; 28 moved |
| Track length | 2474 mm | 2163 mm; 62 routed nets unchanged |
| Warnings | 83 / 71 silk, 6 / 1 dangling | 199 / 88 silk, 4 / 8 dangling |

**Copper removed on purpose:** RF_ANT, RF_MCU, SW48_GATE, SW48_DRV, WBA_VDDANA, WBA_VDDHPA, WBA_VDDRF, WBA_VDDRFPA, WBA_VLXSMPS, LSE_OUT, BUCK_SW (L201 footprint changed).

**Routed copper cut because a new part sits on it:** MAIN_NRST and MAIN_SWO, both part of the planned U501 fan-out redo. PMD_FAULT_M lost its last 13.7 mm when R707 moved to the shifter drain. GND, +3V3 and VBAT fan-out stubs on moved parts were replaced where room allowed.

**Not fanned out yet (no room with auto fan-out):** C313.2, C501.1, C501.2, C506.2, C512.1, Q304.2, R716.2.

**Other project-file changes:** FL501 scoped DRC rule (bump pad gap 0.18 mm, DS14446); FLY_SEC_A–D in HV48.

### Placement points for review

1. **T301** at (192.8, 164.5), rotated 180°, body 26.75 mm tall between J703 and H904 with about 0.1 mm courtyard margin each side. Its pads are 0.4 mm from the board edge.
2. **Primary loop.** Pin 10 (FLY_SW) faces Q301 about 8 mm away. Pin 3 (VBAT) is across the part, about 31 mm from pin 10, and is fed through the In2/In1 plane pair. This is inherent to the HPH6 pinout. Scope for ringing on the bench.
3. **Secondary.** D301, R313, C312, C309 and C310 sit along the top edge of T301, next to pin 7. The four series links cross the part: F.Cu is blocked by the body, so plan B.Cu under it at HV48 clearance.
4. **RF.** FL501 directly above pin 37, J501 moved so its signal pad lines up, 7.5 mm straight run planned.
5. **WBA55 supplies and crystals.** Decoupling, Y501 and Y502 moved to the pins. Y501 is about 3 mm from the HSE pins and about 5 mm from L501.
6. **R312** moved to +48V_RAW beside C311. **D304** is about 6 mm from C308 because of space: keep that loop wide and short.
7. **Q701, Q702** beside R706 and R707; **OVP group** (D303, R314, R315, C313, Q304) near the kill-path parts.

## Remaining stages

| Stage | Work | Gate |
|---|---|---|
| P2 | RF line, supplies and crystals, then U501 pins 24–40 fan-out including FLY_PGOOD, SWO, NRST, SWCLK, READY | Owner review of the fan-out |
| P3 | Flyback, secondary links, 48 V rail, OVP group | Owner review, T301 leakage result |
| P4 | Remaining signals and U101 (needs the TI land drawing) | 0 unconnected, DRC errors 0, parity 0 |
| P5 | Silkscreen, footprint checks, fab rules, manufacturing outputs | K-7 waiver, owner release |

## Placement review before P2 (tag `pcb-p1b-placement`)

Estimates below are hand calculations, not measurements. Nothing here proves the circuit works.

| Item | Result | Action |
|---|---|---|
| T301 edge | 0.4 mm pad to edge was not acceptable for a 22 g, 13.6 mm tall part | Right board edge moved out 1.5 mm (now 111.5 x 85 mm); pads 2.1 mm from edge. Connectors J701-J705 now sit 1.5 mm back from the edge: check plug access. |
| T301 courtyard | 0.1 mm each side | J703 moved 0.8 mm up, T301 re-centred: about 0.47 mm to J703, 0.48 mm to H904. M3 head clearance about 0.5 mm with washer radius 3.5 mm. |
| Clamp loop | C308 had been placed about 7 mm from D302 | C308 and D304 moved beside D302 (D304 now about 5 mm); R306 moved away because it carries only DC. |
| Primary loop | Input caps at Q301, pin 3 about 31 mm away, planes continuous (same island, checked) | Estimate 8-9 nH extrinsic including about 2.3 nH for the In2/In1 pair. Commutation loop (Q301, D302, C308, VBAT via, C303) about 3-5 nH sets the fast spike. |
| 48 V clearance | HV48 rule 0.6 mm on all layers; lowest pad gaps 0.72-0.85 mm. J703 0.40 mm is below the rule (vendor connector, FL-6 open). 105 V peak across D301 and snubber. | P3 checks routed copper. IPC-2221 values not confirmed from a source copy. |
| PMD401 voltage | Neither PMD401 document gives an absolute maximum. Manual: 48 V error limit +/-5 %, motor stops on voltage error. | **NOT VERIFIED.** Trip at 50.5-53.9 V can exceed 50.4 V. See P3 decision. |
| Q301 margin | 24.4 V simulated peak + 2.5-4.9 V estimated parasitic spike + about 1 V TVS heating = 27.9-30.3 V at the worst corner | **Margin not established.** Measure before continuous running; P3 proposes a gate resistor and a DNP drain snubber. 1 Nov update: simulated with loop inductance, 28.9 V at the worst corner (about 29.9 V with TVS heating), see `validation/sim/q301/RESULTS.md`. |

## Stage P2: RF, WBA55 supplies, crystals, U501 pins 24-40, FLY_PGOOD (tag `pcb-p2-done`)

Route specifications: `validation/routing/p2/`. Measurements: `p2_measurements.txt`, `p2_clearance.txt`. Pictures: `p2_board_fcu.png`, `p2_u501_fcu.png`, `p2_u501_bcu.png`.

| Check | P1 | P2 |
|---|---|---|
| DRC errors other than unconnected | 0 | **0** |
| Parity | 0 | **0** |
| ERC | 5 + 1 cosmetic | Same |
| Unconnected pairs | 81 | **50** |

**RF:** 2.5 mm RF_MCU (0.20 mm) and 8.5 mm RF_ANT (0.32 mm, first 0.5 mm at 0.20 mm beside the filter), no vias, **0 crossings on any layer**, was 50.9 mm with 2 vias and 10 crossings. Solder mask opened over the lines. GND stitching vias both sides. A 0.4 mm jog at the pin moves the line clear of pin 38.

**Fan-out:** every pin 24-40 connected, including FLY_PGOOD (53.4 mm, 2 vias), MAIN_SWCLK and PMD_READY_M. Duplicate LED_MAIN and zero-length RS485_RO segments removed. 9 GND vias under the exposed pad.

**Trade-offs for review:**
- MAIN_NRST is 62.5 mm with 6 vias, to avoid crossing the RF line. It has 100 nF at C508. A single crossing under the RF line would be much shorter; the owner asked not to assume that is acceptable.
- C501 (VDD decoupling) is about 7 mm from pin 44 through the +3V3 plane. C512 is about 3 mm from pin 40, also through vias.
- VDD11 branch: L501 to pin 45 about 12 mm with 2 vias; pin 39 reaches the same node through about 15 mm and vias. VDDANA decoupling C511 is about 4 mm from pin 39.
- FLY_PGOOD crosses FLY_EN once, on different layers. No check of coupling into the UVLO/SYNC pin.
- Y501 has 0.87 mm from pad centre to VDD11 track. MCU_48V_EN and VBAT_SENSE remain beside Y502.

**Still unconnected (50), by stage:** flyback and 48 V rail, including T301 series links and the OVP group (P3); PMD_FAULT, SPI, CON_MAIN_TX, ENC_I_M, I2C_SDA, VBAT_SENSE, R716, L201, RS485_B, charger pins (P4); 3 small GND pour islands (P4).

## ECO3 and Stage P4 (tags `sch-eco3-done`, `pcb-p4-done`)

**Status: P3 flyback routing on hold. Q301 margin, T301 leakage and PMD401 voltage protection are all OPEN.** Incomplete, electrically untested, not fabrication-ready.

### ECO3 optional parts

| Ref | Part | State | Note |
|---|---|---|---|
| JP301 | Copper bridge, B.Cu | Bridged | Needed because an unfitted series resistor would leave the gate open. No component. Cut it to use R316 |
| R316 | Gate resistor, B.Cu 0603 | Unfitted, value TBD | Hand-fit on the bench only |
| R317, C314 | Drain RC snubber, 0402 | Unfitted, values TBD, not routed yet (P3) | FLY_SW to GND beside Q301 |

### Q301: higher-voltage search (not resolved)

Requirement: full enhancement at 3.0-4.2 V gate, because the LM51551 gate drive equals VBAT here. At about 2.3 A RMS, 20 mOhm costs about 0.1 W.

| Part | VDS | Gate-drive evidence | Result |
|---|---|---|---|
| AOS AONR34332C (fitted in schematic) | 30 V | Under 2.9 mOhm at 2.5 V (datasheet) | Gate fine, voltage margin not established |
| TI CSD18543Q3A | 60 V | Rated at 4.5 V; RDS(on) curve rises steeply below about 3.5 V (datasheet Fig. 7) | Rejected at VBAT 3.0-3.5 V |
| AOS AON2240 | 40 V | Rated at 4.5 V (29 mOhm); VGS(th) up to 2.4 V | Rejected: threshold too high |
| Diodes DMN4020LFDE | 40 V | Rated at 4.5 V (28 mOhm); advance information | Not usable without low-gate data |
| Nexperia BUK9M20-40H | 40 V | Logic level, 20 mOhm; datasheet could not be retrieved | **Only candidate worth checking** |
| Toshiba SSM3K339R | 40 V | 180 mOhm at 2.5 V | Too lossy |

No part above 30 V has been verified. Parts searches are not exhaustive.

**Stress-reduction option, not applied:** SMAJ13A clamp ceiling and R305 24 mOhm (limit 3.9-4.5 A). Simulated Vds at most 21.7 V at 10 % leakage (`flyback_clamp_smaj13.log`), about 25-27 V with the same parasitic and heating estimates, or 83-91 % of 30 V. It leaves less overload headroom (3.4 A needed at 3.0 V, 100 mA). Hardware measurement still decides.

### PMD401 question for PiezoMotor/Acuvi (not yet sent)

> For the PMD401 (manual 150025-01, data sheet PMD401-2504-01): (1) What is the absolute maximum voltage on the 48 V input, and for how long? (2) What happens at 50.4-54 V, beyond the voltage error flag? (3) What are the Ready, Fault, SPI and AEN input and output levels, and which rail do their pull-ups use? (4) What is the input capacitance on the 48 V rail?

**The PMD401 must not be described as protected until this is answered.**

### P2 concerns (reviewed)

| Concern | Finding | Action |
|---|---|---|
| Decoupling distance (straight line) | C510 2.0, C506 2.8, C511 4.2, C503 4.5, C512 5.0, C513 5.0, C505 7.2, C501 7.8 mm; several through vias | Not fatal; RF test decides. No change: caps cannot get closer without a tighter layout around the crystal |
| VDD11 | **Corrected:** L501 now beside C509; VLX path 7 mm, no vias. Net still 28 mm and 6 vias overall; pin 39 and pin 45 reach the node by separate branches | Measure ripple and TX spurs on the bench |
| FLY_PGOOD to FLY_EN | One crossing at 72 degrees, F.Cu over B.Cu with two planes between; 2.5 mm within 1 mm. Estimated coupling about 1 fF | Acceptable on paper. Check for false sync on the bench (SG-03) |
| MAIN_NRST | **Corrected:** 49 mm and 2 vias (was 62.5 mm and 6 vias), still no RF crossing | Done |
| J703 | 0.40 mm pad gap, below the 0.6 mm rule. JST SH rating at 48-54 V not confirmed. About 0.5 mm from T301 body, set back 1.5 mm from the edge | **Open:** check with the real plug and JST data |

### P4 results

| Check | P2 | P4 |
|---|---|---|
| DRC errors other than unconnected | 0 | **0** |
| Parity | 0 | **0** |
| ERC | 5 + 1 cosmetic | Same |
| Unconnected pairs | 50 | **37** |

**Routed in P4:** PMD_FAULT_M and _D, PMD_SS_M, PMD_SCLK_M, PMD_MOSI_M, I2C_SDA (MCU to R105), VBAT_SENSE, CON_MAIN_TX, BUCK_SW, +3V3 at L201 and R716, gate path through JP301 and R316.

**Unrouted, by reason:**
- **P3 hold:** +48V_RAW, +48V_MOT, FLY_SW, FLY_SEC, FLY_SEC_A to _D, FLY_CLAMP, FLY_SNUB, FLY_DSNB, FLY_EN to Q304, OVP_G, OVP_K.
- **U101 land drawing:** CHG_INT_N, I2C_SDA (U101 to R105), VBAT_FUSED.
- **Owner decision:** ENC_I_M (below) and RS485_B to R714 (D3).

**ENC_I_M (pin 48):** no route exists without crossing the RF line or a pin change. Rows on B.Cu box it in, and every route east must pass the RF path. Options: one B.Cu crossing under the RF line with In1 GND between, or move the index to another pin. PA15 (pin 25) also had no route in a quick scratch test.

Moved beyond the approved routing nets to clear the left side: L501, L503, L201, FB501, C509 and the NRST, SWO and VDD11 paths around them.

## Stage P6: digital completion, 1 Nov 2026 (tags `pcb-p6-before`, `pcb-p6-routed`, `pcb-p6-clean`, `pcb-p6-final`)

Replaces stages P3 and P5 for a digital-only objective. **Software validation only. Nothing has been built or measured, and a clean report does not show the circuit works.** Route specs: `validation/routing/p6_flyback.json`, `p6_enc_a.json`, `p6_enc_routes.json`. Silkscreen: `scripts/pcb_silk.py`.

| Check (kicad-cli 10.0.3) | Before P6 | After P6 |
|---|---|---|
| ERC errors / warnings | 5 / 1 | **0 / 0** |
| DRC violations, all severities | 305 | **0** |
| Unconnected pads | 34 | **0** |
| Schematic parity | 0 | **0** |
| Pad nets against netlist (`validation/logs/p6_netlist_audit.txt`) | not run | 493 compared, **0 mismatches** |
| MCU pin map (`verify_pinmap.py`) | 0 failing | **0 failing** |

Project DRC checks that are off: missing courtyard, track not centred on via, tuning geometry, footprint filters, footprint type. With all of them and the ignored ERC checks enabled on a scratch copy, the only findings are 6 footprint-filter notes on deliberate assignments (J102, FB501, FB502, D301, D302, D303; `validation/logs/p6_strict_erc.rpt`). The 3 scoped clearance exceptions in `pump_v2.kicad_dru` (J703, Q301, FL501) remain.

**Layout choices to review:**
- FLY_SW runs from Q301 to T301 pin 10 on B.Cu at 1.0 mm through 2 + 2 vias. F.Cu is blocked by the T301 pin 9 HV clearance beside R305. This adds loop inductance. R305's GND via moved to two vias below the part.
- T301 series links run on B.Cu under the transformer at 0.4 mm, HV48 rule met. Their vias sit under the body.
- FLY_CLAMP uses one via pair to D304. +48V_RAW reaches C311 and R307 through B.Cu.
- OVP group: fed from C311, FLY_EN joins by B.Cu at the existing via. R315 and C313 are new bottom-side parts.
- ENC_I_M is 32 mm with one crossing under RF_MCU; RF_ANT still has none. Coupling not analysed.
- U101: I2C_SCL escape re-routed to free pin C1. Vias beside the balls, 0.15 mm necks, VBAT_FUSED 0.25-0.3 mm.
- Reference text: 6 parts moved to the fab layer (D704, D709, R705, R706, TP701, Y501). Some labels sit several mm from their part.
