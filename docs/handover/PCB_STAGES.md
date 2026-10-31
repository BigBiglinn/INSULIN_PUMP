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
