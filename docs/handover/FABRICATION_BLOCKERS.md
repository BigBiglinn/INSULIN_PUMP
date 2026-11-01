# What still prevents fabrication of Rev B

Status at commit `a768755` plus the documentation commit that follows it (1 Nov 2026). The design is **not ready for fabrication**. Every item below must be closed, re-verified and recorded before Gerbers are generated (CLAUDE.md Phase 6). The decision numbers refer to `OWNER_APPROVAL_SHEET.md`.

## 1. Blocked by owner decisions

| Blocker | Decision | Affects |
| --- | --- | --- |
| No overvoltage protection independent of the R307/R308 feedback divider | 1 | Schematic, PCB, safety case S-04 |
| No hardware runaway stop fast enough for S-06; PMD401 SPI timeout not guaranteed | 2 | Schematic, PCB, firmware, SG-06 |
| 48 V output switch placeholders versus bleeder | 3 | Schematic, PCB (SW48_GATE unconnected), E-11 |
| J703 voltage rating unverified (distributor listing 50 V) | 4 | Footprint, routing |
| HV clearance rule not signed off | 5 | DRC rules |
| Feedback divider 1 % versus 0.1 %; R307 working voltage (U-38) | 6 | BOM |
| Transformer T301 not selected (placeholder footprint) | 7 | Footprint, clamp/snubber, compensation, flyback layout |
| Current-limit headroom: hiccup on 100 mA load **steps** at 3.0 V (also at 3.4 V without the CS filter); a 20 ms speed ramp avoids it at V<sub>CLTH</sub> 93 mV in simulation (FW-R1) | 8 | Firmware requirement; optionally R305 / T301 I<sub>sat</sub> |
| No CS-pin RC filter: the leading-edge spike trips hiccup on full-load start-up at minimum V<sub>CLTH</sub> | 19 | Schematic (2 parts), PCB |
| **Q301 (25 V) exceeds its absolute maximum at fault current limit**: 22.1 V on an ideal layout after the 1 Nov clamp re-tune, but 28–33 V with 2–5 nH drain-loop inductance (`validation/sim/q301_stress/results.md`) | 9 | ≥ 40 V FET (gate-drive constraint), gate-resistor footprint, layout |
| R313 rating | 11 | Footprint |
| Battery cell, fuse, connector, charge current | 13 | BOM, firmware |
| Supervisor cannot read the battery voltage | 14 | Schematic |
| Fab house and stack-up not chosen; RF trace not impedance-controlled | 15 | DRC rules, RF layout |

## 2. Blocked by missing manufacturer documents

| Missing document | Blocks |
| --- | --- |
| ST DS14127, AN5948, AN6373, MB1803 schematic (decision 12) | STM32WBA55 SMPS inductor, VDD11/VDDRF/VDDRFPA/VDDANA decoupling, HSE/LSE load capacitors, RF match, exposed-pad layout. **12 unconnected items, 6 ERC errors**, plus 6 nets boxed in by the U501 fan-out that must be redone (I2C_SDA→U501.6, PMD_SCLK_M, PMD_MOSI_M, PMD_READY_M, MAIN_SWCLK, FLY_PGOOD) |
| ST STM32C031 datasheet | Supervisor decoupling values, boot pins (A-7) |
| ~~TI BQ25188 YBG package drawing~~ | **Closed 1 Nov:** found in the repo PDF; footprint corrected; 3 items routed |
| JST SH, MAX3485, LL06, Molicel, fuse, TVS (D701–D709), crystal datasheets | Footprint and rating verification (U-12, U-15, U-17, U-34) |

## 3. Engineering work that remains after the decisions

1. Implement approved decisions in `scripts/design.py`, the schematic and the PCB.
2. Re-lay the STM32WBA55 area per ST, then route the remaining **19** unconnected items. Each is listed in `validation/drc/pump_v2-drc.rpt`.
3. Flyback loop compaction around the real T301 (FL-1 to FL-4).
4. Loop simulation with the TI LM5155/LM51551 model and the real T301, followed by a bench Bode measurement. The present compensation (R303/C306/C307) is **preliminary**.
5. Footprint verification against drawings for every part (PB-03). Done for CSD16340Q3 (to be replaced) and BQ25188 (corrected).
6. IPC-2152 width check on the battery path and the flyback primary.
7. Silkscreen clean-up: 69 overlap, 52 over copper and 1 edge warning (kicad-cli).
8. Refill zones in pcbnew (press **B**) and save. The stored fills were re-clipped by script.
9. Independent design review by a qualified engineer (none has taken place).
10. Rev A bench results (DV-1): the owner's gate before any Rev B fabrication.

## 4. Already verified (no blocker)

| Item | Evidence |
| --- | --- |
| Copper DRC | **0** errors (kicad-cli 10.0.4; latest run in `validation/KICAD_CI_PROVENANCE.md`) |
| Schematic–PCB parity | **0** issues (same run) |
| ERC | 6 intentional `power_pin_not_driven` errors (U-05) + 1 cosmetic warning; no other violations |
| BOM | Matches the schematic: 133 references in the kicad-cli export; `gen_bom_full.py` reports an identical reference set |
| Pin map | 41/41 functions against the STM32CubeMX database (10 Oct) |
| Soft-start lock-out | Fixed: C305 = 4.7 µF (worst-case simulated, not measured); full-load start also needs decision 19 |
| BQ25188 land pattern | Verified against TI YBG0008-C01 and corrected |
