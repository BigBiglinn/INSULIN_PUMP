# Placement-only proposal: removing routing bottlenecks (pump_v2 Rev B)

10 Oct 2026, branch `placement-opt`. **Proposal only. The project PCB has not been changed.** It is still identical to the baseline (md5 `eb5b4bcd…`).

- **Recovery point:** tag `baseline-routing-e8d141c` (on commit `b0e5473`; the PCB is the same as at `e8d141c`).
- **Status:** awaiting owner approval before anything is applied.

> Bench-only prototype for water or 0.9 % saline. Never connect it to a person or an animal, and never use real insulin. Not fabrication-ready.

## 0. Scope limits respected

This proposal does **not** change any of the following:

- The schematic, BOM, netlist, values or part choices.
- The WBA55 supply, clock or RF wiring, or the placement of its placeholders (L501, C509–C519, R510–R513, Y501, Y502, L502, J501). Those wait for the ST documents (§1).
- The transformer choice. T301 stays the 12 × 12 mm placeholder; only its position shifts.
- The 48 V protection (U-06 switch, U-23 secondary OVP). Placeholders are only relocated, not designed.
- The 6 intentional ERC errors. They stay visible.

## 1. ST documents: identification status

Downloading from st.com, st.com.cn and wiki.st.com failed again on 10 Oct 2026, both from this machine and through the WebFetch service (timeouts). **No ST document content has been read.** The table records only what web-search index entries say about each document, pointing at st.com URLs. Every number and revision must be confirmed against the PDF itself before use.

| Role | Document | Revision seen in the search index | Confirmed by reading? |
| --- | --- | --- | --- |
| Datasheet | **DS14127**, "STM32WBA5xxx" (covers WBA54xx/55xx) | Rev 10, May 2026 (st.com URL title); older copies Rev 6/7 at distributors | **No** |
| Reference manual | **RM0493**, STM32WBA5x | Rev 5, Sep 2024 is the newest seen; an ST PCN mentions Feb 2026 RM updates for STM32WBAx, revision not named | **No** |
| Errata | **ES0592**, "STM32WBA5xxx device errata" (lists WBA54/55, silicon revisions A and B) | Rev 7, Feb 2026 (per search summary) | **No** |
| RF hardware guide | **AN5948**, "How to develop RF hardware using STM32WBA (5xxx) MCUs" | Revision not seen | **No** |
| HSE trimming | **AN5042**, HSE calibration for STM32 wireless MCUs (WL/WB/WBA, RCC_ECSCR1) | Rev 16, Jul 2024 | **No** |
| Oscillator design | **AN2867**, oscillator design guide for STM32 | Rev 24, Feb 2026 | **No** |
| Reference board | **UM3301** (NUCLEO-WBA55CG, MB1803) and MB1803 schematics; **UM3255** (STM32WBA55G-DK1) | Revision not seen | **No** |
| Possible extra reference | ST STDES-WBA5xxx reference designs (product pages exist) | — | **No** |

There is no dedicated "hardware getting started" application note for the WBA. The search found AN5928 and AN5929, but both cover software.

**What is needed from you:** the PDFs for DS14127, RM0493, ES0592, AN5948 and UM3301, plus the MB1803 schematic, placed in `docs/datasheets/`. Until then, U-05 stays open and no WBA wiring is changed.

## 2. Method

[`scripts/eval_placement.py`](../../scripts/eval_placement.py) applies a move set to a **scratch copy** of the board with all tracks deleted. It then reports:

- per-net airwire length: the minimum spanning tree over pad centres;
- straight-line pad-to-pad loop metrics for the flyback.

`kicad-cli pcb drc` is then run on that copy with the project's rules (`.kicad_pro` and `.kicad_dru`), with zones refilled.

Outputs are in `validation/placement/`:

- move sets: `moves_v1.json`, `moves_v2.json`, `moves_v3.json`
- results: `eval_v1.txt`, `eval_v2.txt`, `eval_v3.txt`

**Result for every variant:** 0 `courtyards_overlap`, 0 `clearance` (pad to pad, including the HV48 0.6 mm class), 0 shorting, and 0 copper-to-edge violations. These are **placement-level checks only**. They do not prove the moved parts can be routed within the HV48 clearance; that is shown only by routing.

Three variants were evaluated:

- **v1:** every move requested, including R711/R712 next to U601.
- **v2 (recommended core):** v1 without the R711/R712 move. §4 explains why.
- **v3 (core plus option):** v2 with the supervisor cluster moved up 16.5 mm (U601, C601–C604, D601, R601, J601) and J503 next to it.

## 3. Results against the baseline (airwire MST, mm; indicative, not routed lengths)

| Item | Baseline | v2 | v3 |
| --- | --- | --- | --- |
| **Clamp loop** Q301.D→D302→C308→T301.1 (pad-to-pad path) | 59.7 | **13.9** | 13.9 |
| **Secondary loop** T301.4→D301→C309→T301.3 | 73.1 | **18.8** | 18.8 |
| Gate U301.GATE→Q301.G | 11.0 | **3.4** | 3.4 |
| Current sense U301.CS→R305 | 12.9 | 6.5 | 6.5 |
| VCC capacitor U301.VBAT→C304 | 6.6 | 3.2 | 3.2 |
| FLY_SW node Q301.D→T301.2 | 3.9 | 7.4 (worse, see M2) | 7.4 |
| +48V_MOT (net) | 96.2 | **44.2** | 44.2 |
| +48V_MOT R311→J703.2 / C702→J703.2 | 13.3 / 18.3 | 4.0 / 11.2 | 4.0 / 11.2 |
| +48V_RAW (net) | 98.6 | 72.0 | 72.0 |
| FLY_FB / FLY_SS / FLY_PGOOD | 26.2 / 6.1 / 73.5 | 6.4 / 3.5 / 47.9 | same |
| CON_SUP_TX / CON_SUP_RX | 57.2 / 56.2 | 15.9 / 13.4 | **4.6 / 3.4** |
| CON_MAIN_TX | 21.7 | 29.3 (+7.6) | 24.5 (+2.8) |
| ENC_A_S / ENC_B_S | 60.9 / 62.6 | unchanged | 46.8 / 48.9 |
| HB_M2S / HB_S2M / SUP_VETO / SUP_PARK | 41.8 / 42.5 / 47.9 / 45.3 | unchanged | 25.3 / 26.1 / 36.5 / 31.3 |
| ENC_VCC / PMD_5V | 54.6 / 41.8 | 9.9 / 22.5 | same |
| SW48_GATE (DNP-only net) | 55.5 | 12.0 | 12.0 |
| **Total over 35 tracked nets** | 1323.9 | **927.7 (−30 %)** | **815.4 (−38 %)** |
| Signal nets ripped up and re-routed | — | 22 nets, 248 segments (710 mm), 24 vias | 33 nets, 375 segments (1081 mm), 32 vias |

## 4. Proposed moves

All parts stay on F.Cu. Positions are in board millimetres, with the rotation in degrees.

### Group F: flyback switching and clamp loop (FL-1, FL-9)

| # | Part(s) | From → to | Expected benefit | Affected nets | Clearance and constraints | Implications |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | T301 (placeholder) | (180, 156) → (183.5, 156) | Opens a 4 mm column between Q301/C302 and the T301 primary pins for the clamp | VBAT, FLY_SW, GND, FLY_SEC | Courtyard 177.2–189.8. All neighbours are clear | **Not final:** the real transformer footprint (U-04) may be a different size or pinout, and then this block must be redone. Keep the 12.6 mm square reserved |
| M2 | D302 clamp diode (rotated 270°), C308 clamp capacitor (rotated 90°) | (196.3, 142.1) → (175.2, 157.4); (190.2, 145.0) → (175.2, 153.3) | Clamp loop goes from ~60 mm to ~14 mm (pad-to-pad), which reduces leakage-spike overshoot on Q301 and EMI. Follows the SNVSB75E §10.5.1 loop rule | FLY_SW, FLY_CLAMP, VBAT | D302 anode next to the Q301 drain/T301.2; C308 VBAT pad next to T301.1. FLY_SW is PWR class (0.8 mm track, 0.2 mm clearance) | FLY_SW grows from 3.9 to 7.4 mm because T301 moved. This is a deliberate trade for the much smaller clamp loop. The C308 VBAT pad is inside the In2 VBAT polygon (48 V block). The clamp/snubber values stay provisional (A-23) |
| M3 | R306 clamp resistor (2512) | (175.4, 143) → (182, 147) | Frees the old area; R306 carries the averaged clamp current, so the fast edge stays in C308 | FLY_CLAMP, VBAT | 2 mm above the T301 courtyard | FLY_CLAMP needs a short B.Cu hop from the D302/C308 node. About 0.4 W dissipation (U-19); keep copper around it |
| M4 | U301 LM51551 (rotated 180°), C304 | (164, 152) → (165.6, 159); (158.8, 146.5) → (165.6, 162.9) | GATE, CS and PGND pins now face Q301/R305. Gate loop 11 → 3.4 mm, CS 12.9 → 6.5 mm, VCC capacitor right at pins 1/2. Follows SNVSB75E §10.5.1 (gate loop, CVCC, device near RS) | FLY_GATE, FLY_CS, VBAT, GND, all FLY_* control nets | U301 courtyard 164.1–167.1 × 157.2–160.8. Q301 is 2 mm east | **FLY_EN (safety enable node) is re-routed.** It must be checked after routing (SG tests on hardware later). The exposed pad needs the same GND via pattern as now |
| M5 | Control parts R307, R308, C305, R301, R302, TP302 (column at x = 162); R303, C306, C307 (above U301) | From scattered spots (153–169, 141–162) | Small-signal parts sit on the quiet (west) side next to their pins: FB, SS, RT, PGOOD, EN. Closes the FLY_SS blocker (6.1 → 3.5 mm) and puts TP302 next to the PGOOD node | FLY_FB, FLY_SS, FLY_RT, FLY_PGOOD, FLY_COMP, FLY_COMP_RC, +3V3, GND, +48V_RAW (R307 top) | Rows at 1.8 mm pitch. The R307 +48V_RAW pad meets 0.6 mm HV clearance at the pad level (DRC: 0 clearance violations) | **The FB sense becomes a long +48V_RAW (HV48) trace, about 30 mm** from the output capacitors to R307. The FB node itself stays short. That is the correct trade (high-impedance node short, low-impedance sense long), but the sense trace must hold 0.6 mm clearance along its route. AGND parts are grouped, so a later FL-3 decision (local AGND island) stays possible |

### Group O: output capacitors and the 48 V output path (FL-2, +48V_MOT blocker)

| # | Part(s) | From → to | Expected benefit | Affected nets | Clearance and constraints | Implications |
| --- | --- | --- | --- | --- | --- | --- |
| M6 | D301 rectifier, C309/C310 ceramic output capacitors (rotated 180°), R313/C312 snubber (vertical) | D301 (190.5, 159.5) → (192.6, 159.5); C309/C310 (159.8 and 165.3, 142.6) → (192.3, 152.5 and 156.0); R313/C312 (190.5, 155.5 / 152.5) → (191.2 / 194.0, 163.1) | Secondary loop goes from ~73 mm to ~19 mm. COUT sits between the D301 cathode and the T301.3 return (SNVSB75E: smallest COUT loop, small ceramic COUT). The snubber sits directly across D301 | FLY_SEC, FLY_SNUB, +48V_RAW, GND | All HV48 pads clear at the pad level | Less room for **D301 thermal copper (FL-5)**. Sizing waits on U-19. C311 (47 µF bulk) stays at (180.5, 171) |
| M7 | R311 0 Ω bypass, TP301, R312 (DNP bleeder), C702 100 µF bulk | R311 (190.8, 142.2) → (199.5, 149.5); TP301 (169.5, 142) → (201.5, 145); R312 (183.9, 143) → (195.5, 145.8); C702 (196.5, 164) → (200.5, 158) | **Removes the +48V_MOT blocker geometry:** R311 → J703.2 is 4 mm, C702 → J703.2 is 11 mm, the net is 96 → 44 mm, and the route no longer crosses D302/TP302/FLY_SW | +48V_RAW, +48V_MOT, GND | The C702 courtyard reaches x = 209.5 (0.5 mm inside the edge). The pad still meets the 0.3 mm copper-to-edge rule (DRC: 0) | **Mechanical:** the tall 12.5 mm can now sits 4 mm from J703, so check the PMD401 cable entry and the enclosure. The J703 pad-entry clearance (1.0 mm pitch vs HV48 0.6 mm) is unchanged and still needs FL-6/U-17 |
| M8 | Q302 (DNP high-side switch placeholder), R309, R310 | Q302 (160.4, 179.6) → (193.5, 171.5); R309/R310 → (191.0 / 195.0, 177.2) | Q302 sits next to the output path, so HV copper no longer runs about 30 mm across the bottom band to a DNP part. SW48_GATE becomes local (55 → 12 mm) | +48V_RAW, +48V_MOT, SW48_GATE, SW48_DRV | Clear | **Not a design of U-06.** Q303 is left at (169.9, 179.6) near FLY_EN, so the DNP-only SW48_DRV stays long (29 mm). That is reported, not hidden. Alternative: leave the whole switch group where it is (your choice) |

### Group S: long signal routes

| # | Part(s) | From → to | Expected benefit | Affected nets | Implications |
| --- | --- | --- | --- | --- | --- |
| M9 | J503 console header | (159.2, 104.5) → v2: (141, 147), horizontal; v3: (157.5, 136), vertical | CON_SUP_TX/RX 56 → 14 mm (v2) or 4 mm (v3) | CON_SUP_TX, CON_SUP_RX, CON_MAIN_TX, GND | CON_MAIN_TX gets longer: +7.6 mm (v2) or +2.8 mm (v3). The header moves from the top edge to mid-board: still reachable for a bench cable, ≥ 9 mm from HV48 copper |
| M10 | JP701 encoder-supply selector, C701 encoder decoupling | (171.8, 102.8) → (199.5, 134.5); (188.5, 104.8) → (199.5, 138.5) | ENC_VCC 55 → 10 mm, PMD_5V 42 → 23 mm. The decoupling capacitor is now next to J705 pin 3 | ENC_VCC, PMD_5V, +3V3, GND | Both are ≥ 6 mm from the nearest HV48 pad (TP301) |
| — | **R711/R712 (not recommended as a stand-alone move)** | Evaluated in v1 at (152, 167.5 / 169.3) | ENC_A_S/ENC_B_S drop by 57 mm, but **ENC_A/ENC_B rise by 57/60 mm**, so the net gain is zero | — | The length is set by the distance from U601 to J705, not by where the resistor sits. Electrically, the resistor at the MCU pin is the usual place for injection limiting, while the resistor at the branch point isolates a fault on the supervisor branch better (S-07 intent). Recommend leaving R711/R712 at the branch point, unless v3 is chosen, which shortens the run anyway |
| M11 (v3 option) | U601 supervisor plus C601–C604, D601, R601 (−16.5 mm in y), J601 → (136.4, 150) | (150, 160) → (150, 143.5) | Moves the supervisor out of the flyback's neighbourhood. CON 4 mm; HB, SUP_VETO and SUP_PARK 11–16 mm shorter; ENC_A_S/B_S 14 mm shorter. Total −38 % against −30 % for v2 | 33 nets re-routed, including **SUP_VETO, SUP_PARK, HB_*, SUP_NRST and SWD** | **RF/WBA reserve:** C601/C603 then sit at y ≈ 134.6, close to the WBA placeholder row (y ≤ 133). That eats into the space the ST-guided VDDRF/VDDRFPA decoupling and the pi network may need. **Safety:** the kill-path nets are re-routed, so SG checks are needed later. Under v3, J601 is on the opposite side to the U601 SWD pins (short detour) |

**Not proposed now:**

- The WBA55 area (waits on ST documents).
- The U101 BQ25188 escape (YBG footprint pitch unverified, U-12).
- The VBAT_SENSE divider relocation. It is a marginal gain: the high-impedance trace goes 28 → ~11 mm, but a 20 mm VBAT trace is added. It is best decided together with the ADC leakage data from DS14127.

## 5. Power, ground-return, RF and mechanical summary

- **Power:** no net, value or rail changes. All moved VBAT pads stay inside the In2 VBAT polygon (x > 155, y > 140.5). JP701/C701 and J503 (v2) sit over the +3V3 region, and the In2 planes are not reshaped.
- **Ground returns:**
  - The primary loop (C302/C303 → T301.1 … Q301 → R305 → GND) is unchanged.
  - The clamp and secondary loops shrink by about a factor of 4.
  - Flyback pulsed currents stay in the 48 V block over the solid In1 GND.
  - v3 moves U601 about 6 mm further from U301 than it is today.
- **RF:** no part in the WBA/RF area moves, and the U.FL and pi network are untouched. v3 reduces the free reserve below U501 (see M11).
- **Mechanical:** the C702 can moves near J703 at the right edge, and J503 moves from the top edge to mid-board. T301's final footprint is unknown. Mounting holes, edge connectors (J1xx, J70x) and U.FL are not moved.

## 6. What happens once a variant is approved

Nothing below is done until you approve.

1. Encode the approved moves in `scripts/gen_pcb.py` as a `move` sub-command that edits the existing board. It will **not** re-run `place`, so all other routing is kept.
2. Rip up the tracks and vias of the affected signal nets only, as listed in §3. For GND/+3V3/VBAT, remove only the fan-out stubs on moved pads, then re-run the plane fan-out for those pads.
3. Refill zones. Run ERC, then DRC with `--schematic-parity --refill-zones`, the unconnected classification and the BOM export. Report against the baseline:
   - ERC: 6 errors, 1 warning
   - DRC: 0 copper violations, 0 parity issues, 35 unconnected (12 placeholder / 1 DNP-only / 22 genuine)
4. **Expect the unconnected count to rise after step 2.** Ripped nets are unrouted until the re-route stage. Re-routing (a staged Freerouting/hand pass with checks after each batch) is a **separate step**, and I will ask before it.
5. Commit on `placement-opt`. Merge to `master` only with your approval. The baseline tag stays as the recovery point.

## 7. Decisions requested

1. **Variant:**
   - v2 (core: M1–M10), or
   - v3 (core plus the supervisor relocation M11), or
   - a subset.
2. **M8:** relocate Q302/R309/R310 next to the output, or leave the switch placeholders where they are.
3. **R711/R712:** leave them at the branch point (recommended), or move them to U601 anyway.
4. **After placement:** apply and stop for review, or apply and continue to the staged re-route.
