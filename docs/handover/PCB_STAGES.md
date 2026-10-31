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
| Q301 margin | 24.4 V simulated peak + 2.5-4.9 V estimated parasitic spike + about 1 V TVS heating = 27.9-30.3 V at the worst corner | **Margin not established.** Measure before continuous running; P3 proposes a gate resistor and a DNP drain snubber. |

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
