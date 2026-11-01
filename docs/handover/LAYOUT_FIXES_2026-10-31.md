# Layout-only fixes, 31 Oct 2026: engineering report

> **Correction, 1 Nov 2026.** This report's "0 dangling" result was wrong. kicad-cli 10.0.4, run in GitHub Actions on 1 Nov, found **3 dangling track ends** on this board, which the Python checker had missed. They were removed the next day. All other predictions here matched KiCad: 28 unconnected, 0 copper errors, 0 unmirrored back text, D704 edge warning. See `LAYOUT_FIXES_2026-11-01.md`. KiCad verification is now available through CI, so the "not verified by KiCad" warnings below are superseded.

Piezo Insulin Pump v2, Rev B digital handover. This continues from `976a17b`, which is tagged `checkpoint/pre-layout-fixes-2026-10-31`.

> **Bench-only prototype.** Use water or 0.9 % saline only. Never connect it to a person or an animal, and never use real insulin. This is a digital handover design. It is not authorised for fabrication or for any clinical use.
>
> **KiCad DRC and ERC have NOT been run on the modified board.** Every result below comes from a pure-Python checker written in this session (`scripts/pcbcheck.py`). The checker was calibrated against the last real kicad-cli 10.0.3 run, but it is an approximation. Before anything else, open the board in KiCad 10, refill the zones (**B**), and run `bash scripts/run_checks.sh` (section 8).

## 1. Scope

The owner asked for:

- The PCB layout fixes that need no new datasheet and no owner-level electrical decision.
- No change to electrical decisions, part choices, schematic connectivity or open assumptions.
- A recoverable checkpoint first.
- No claim of ERC/DRC verification unless the checks were actually run.

**What was changed:**

- Only `hardware/kicad/pump_v2.kicad_pcb`, as copper, component positions, silkscreen and stored zone fills.
- The schematic, the netlist, `scripts/design.py`, the footprints, part values and DRC rules were not touched.
- Every pad keeps its net (checked: 460 pads, 0 net changes). The footprint blocks are byte-identical except for their position and rotation fields.

## 2. Environment, method and how far the results can be trusted

- **KiCad was not available.** The cloud container offered only Ubuntu's KiCad 7, which cannot read KiCad 10 files. Running the official KiCad 10 container image was refused by the session's permission policy. So `kicad-cli` and `pcbnew` could not be used, and `gen_pcb.py`, `hand_route.py` and `run_checks.sh` could not be run.
- **Edits were made as scripted text edits** of the S-expression board file:
  - `scripts/pcbedit.py` (move, add, delete, re-clip zone fills, preserving the file's CRLF line endings);
  - `scripts/pcbroute.py` (grid A* router);
  - `scripts/layout_fixes.py` (the whole procedure, reproducible from the checkpoint tag).
- **Checker (`scripts/pcbcheck.py`):**
  - It re-implements copper clearance by net class (`pump_v2.kicad_pro`), the two scoped rules in `pump_v2.kicad_dru`, the 0.3 mm zone clearance, copper-to-edge 0.3 mm, hole clearance 0.25 mm, connectivity through pads/tracks/vias/stored zone fills, dangling vias and tracks, and courtyard overlap.
  - **Calibration on the unmodified board.** It reproduced the 10 Oct kicad-cli report exactly:

    | Check | Result on the unmodified board |
    | --- | --- |
    | Unconnected pairs | 35, on the same 28 nets |
    | Copper violations | 0 |
    | Dangling items | 8 vias + 1 track, at the same coordinates |
    | Courtyard overlaps | 0 |

  - **What it does not do:** it does not model KiCad's zone refill, thermal-spoke rules (`starved_thermal`), solder-mask or silkscreen rules, or text geometry. It can miss things KiCad would report.
- **Zone fills.** Stored fills were only *cut back* around new or moved copper (with the clearance, and 0.3 mm thermal reliefs with 0.35 mm spokes for the moved J503 GND pin). No copper was ever added. Areas vacated by moved parts and removed tracks stay empty until KiCad refills the zones. **Refill before trusting DRC or using any output.**
- **Silkscreen.** Positions were chosen with a conservative text-box estimate (`scripts/pcbsilk.py`). Only KiCad can give the real counts.

## 3. Before and after routing status (pcbcheck.py)

| Item | Before (976a17b; same as kicad-cli 10 Oct) | After (this commit, pcbcheck.py) |
| --- | --- | --- |
| Unconnected pairs, total | 35 (28 nets) | **28** (23 nets) |
| Group A: WBA55 placeholders (ST documents needed) | 12 | 12 (unchanged, deliberately) |
| Group B: DNP 48 V switch only | 1 | 1 (unchanged, U-06) |
| Group C: genuine functional connections | 22 | **15** |
| Copper clearance / edge / hole violations | 0 | **0** (with re-clipped fills) |
| Dangling vias / dangling tracks | 8 / 1 | **0 / 0** |
| Courtyard overlaps | 0 | 0 |
| Track segments / vias | 1081 / 229 | 1095 / 234 |
| Silkscreen (pcbsilk.py estimate only, not comparable with KiCad's 75/55/3) | 78 overlaps, 16 over pads, 5 at edge | 74 overlaps, 15 over pads, 3 at edge |
| Back-side unmirrored text (KiCad: 2) | 2 | 0 (both mirrored) |

Full lists: `validation/logs/pcbcheck_2026-10-31.txt` (before and after), `validation/logs/unrouted_nets_2026-10-31.txt`, and the step-by-step log `validation/logs/layout_fixes_2026-10-31.log`.

## 4. Nets connected in this session

| Net | Was | Now | Route |
| --- | --- | --- | --- |
| **+48V_MOT** | 3 islands; J703.2 (PMD401 48 V input) not fed | **1 island** | F.Cu 0.4 mm from R311.2, north of D302, down the free x = 200 mm corridor, entering J703.2 from above. B.Cu 0.4 mm from the C702.1 through-hole pad to one via on that route. Smallest gap to other copper is **0.75 mm** (to J703.1 GND); the HV48 rule is 0.6 mm. No DRC rule relaxed. |
| **FLY_SS** | C305 on the far side of U301 | **connected** | U301.9 → 0.7 mm F.Cu stub → via (0.5/0.3 mm) → B.Cu → via (0.5/0.3 mm) → C305.1, about 4 mm in total. C305.2 → GND via to the In1 plane. |
| **FLY_PGOOD** (part) | 3 groups (U301/R302, TP302, U501.28) | 2 groups | TP302 now sits on the trace beside U301/R302. **U501.28 (PA12) is still unconnected** (section 6). |
| **CON_SUP_RX** | J503.4 ↔ U601.32, 56 mm gap | **connected** | 20.9 mm, 1 via (the via sits under the LQFP48 body of U601, which has no exposed pad) |
| **CON_SUP_TX** | J503.3 ↔ U601.29, 56 mm gap | **connected** | 30.7 mm, 1 via |
| **CON_MAIN_TX** | connected to J503 at its old position | **connected to J503 at its new position** | U501-side escape and via kept; 45.3 mm, 4 vias |
| **ENC_A_S** | R711.1 ↔ U601.17, 61 mm gap | **connected** | 65.1 mm, 6 vias. Runs alongside the existing ENC_B_S route. |

Re-routed without changing their connectivity (they stay fully connected):

- FLY_FB, FLY_RT and the U301 side of FLY_PGOOD (the U301 east-side escapes).
- U301 AGND pin 7, now tied directly to the exposed pad.

## 5. PCB changes and component moves

| Part | From (x, y, rot) | To | Why |
| --- | --- | --- | --- |
| C305 (CSS 47 nF, FLY_SS) | 163.805, 146.505, 0° | **164.75, 149.40, 180°** | Next to U301 in the free strip north of the IC, so FLY_SS is about 4 mm instead of an unroutable 6 mm crossing |
| TP302 (FLY_PGOOD test point) | 197.548, 145.046, 0° (beside J703) | **165.75, 155.75, 0°** | On the PGOOD trace at U301/R302, and out of the 48 V corridor |
| J503 (console header) | pin 1 at 159.19, 104.50, 90° (top edge) | **pin 1 at 133.50, 147.50, 90°** | Free area between the MCUs: both supervisor console nets are now about 20–30 mm, and CON_MAIN_TX about 45 mm |
| R711, R712 | not moved | — | R712 → U601 (ENC_B_S) was already routed. Moving the 100 Ω parts to U601 would only move the 60 mm run onto ENC_A/ENC_B and break a finished route. ENC_A_S was routed instead |

**Details of the U301 rework.** Datasheet basis: TI SNVSB75E pin table and §10.5.1, both in `docs/datasheets/lm51551.pdf`.

- **Constraint:** pin 9 (SS) sits between FLY_RT (pin 10) and FLY_FB (pin 8), and FLY_EN wraps around the east side. No one-layer FLY_SS route to any C305 position was possible without moving FLY_EN. A limited automated search (C305 positions south and east of U301, with every routing order of the neighbours) found none that kept FLY_FB, FLY_RT and FLY_PGOOD routable on one layer.
- **Solution:**
  - A 0.5 mm via just east of pin 9.
  - FLY_FB, FLY_RT and FLY_PGOOD re-routed down a four-track channel between the pins and the FLY_EN track.
  - AGND pin 7 tied to the exposed pad, as the datasheet asks ("Connect the exposed pad to the AGND and PGND pins under the device"). This replaced its own via.
- **Clearance margin:** several gaps in this channel are exactly at the 0.15 mm Default rule. They are legal under the board rules, with no margin.
- **CSS ground:** returns through a GND via to the solid In1 plane. The single-net AGND/PGND strategy is still FL-3 [APPROVAL].

**Silkscreen:**

- The two B.SilkS disclaimer texts are mirrored and centred at x = 155 mm. Their wording is unchanged.
- References repositioned: J501 and J102 (were clipped by the board edge), C305, TP302 and J503 (moved parts), and U301 and R302 (now covered by the moved parts).
- The D704 reference stayed where it was: no clear position was found (KiCad flags it at the edge).

**Dead-end autorouter stubs removed** (8 dangling vias, 1 dangling track, and the stub tracks that led only to them; 31 items):

- MAIN_SWCLK (J502 side)
- VBAT_SENSE (U501 side)
- ENC_VCC via
- WBA_VDDRFPA (3 vias and stubs)
- CON_SUP_TX (an old stub, then re-routed)
- PMD_MOSI_M (U501 side)
- ENC_I_M (R710 side)

Every one was on a net that was already unconnected. The unconnected count did not change, and no pad lost a connection.

**Script record.** The placements were also recorded in `scripts/gen_pcb.py` `ANCHORS`, so a future `gen_pcb.py place` keeps them. Regenerating still discards all routing.

## 6. Remaining unconnected items: 28 (pcbcheck.py)

**Group A (12): need the ST documents (U-05). Deliberately not routed.**

- HSE_IN ×2, HSE_OUT ×2, LSE_IN ×2
- RF_MCU
- WBA_VDD11 ×2, WBA_VDDANA, WBA_VDDRF, WBA_VDDRFPA

**Group B (1):** SW48_GATE, between DNP placeholders. Needs the owner decision U-06.

**Group C (15): genuine connections still to route.**

| Net | Gap | Blocker / next step |
| --- | --- | --- |
| FLY_PGOOD: U501.28 (PA12) | 33 mm | Pin 28 is enclosed by the pin 27/29 escapes inside the WBA55 fan-out. Route after the ST-guided U501 re-layout |
| VBAT_FUSED (U101.C2), CHG_INT_N (U101.A1), I2C_SDA (U101.C1 → R105) | 6–12 mm | BQ25188 WCSP ball escape; the footprint pitch is unverified (U-12). Do not route until the TI drawing has been read |
| I2C_SDA (R105 → U501.6), MAIN_SWCLK, PMD_MOSI_M, PMD_SCLK_M, PMD_READY_M, ENC_I_M, VBAT_SENSE | 9–36 mm | U501 fan-out congestion. Re-route together with the WBA re-layout (the blocker report's sequencing) |
| ENC_I, ENC_VCC, RS485_B | 15–41 mm | PMD401 / encoder connector row; routable, not attempted in this session |
| +3V3 (R302.2 group to the main +3V3 group) | 17 mm | R302.2's +3V3 via sits in the In2 **VBAT** region of the 48 V block, so it reaches no +3V3 plane. This was already the case before this session. It needs a short +3V3 track to the 3V3 region (x < 155 mm) or a decision on the In2 split |

## 7. ERC/DRC status

- **ERC:** the schematic was not modified. The last real ERC (10 Oct, `validation/erc/pump_v2-erc.rpt`) found **6 errors** (`power_pin_not_driven` on U501 pins 3, 38, 39, 40, 43 and 45, intentional, U-05) and **1 warning** (U701 `lib_symbol_mismatch`). It has **not been re-run** on 31 Oct.
- **DRC:** `validation/drc/pump_v2-drc.rpt` and `.json` are the **10 Oct reports of the previous board**. They are kept unchanged as the baseline and **do not describe the current board**. KiCad DRC has **not** been run on the modified board.
- **Expected when KiCad DRC is run** (not verified):
  - copper violations 0;
  - unconnected 28;
  - `via_dangling` / `track_dangling` 0;
  - `nonmirrored_text_on_back_layer` 0;
  - `silk_edge_clearance` probably 1 (D704);
  - other silkscreen warnings similar to before;
  - possibly `starved_thermal` items (KiCad reported 3 before; the thermal around the moved J503 GND pin is re-made at refill).
- Any difference between these expectations and the real KiCad result means my checker missed something: report the real numbers.

## 8. Verify in KiCad 10 (required next step)

1. Open `hardware/kicad/pump_v2.kicad_pro` in KiCad 10.0.x and press **B** (refill all zones). Save.
2. Run `bash scripts/run_checks.sh`. It runs ERC, then DRC with `--schematic-parity --refill-zones --save-board`, then the BOMs.
3. Read `validation/erc/pump_v2-erc.rpt` and `validation/drc/pump_v2-drc.rpt`.
4. Compare the numbers with section 7. Update this file, `FINAL_HANDOVER.md` §6 and `HANDOVER_GUIDE.md` §8 with the real numbers.
5. Inspect the changed areas in pcbnew. Review images, drawn by `scripts/pcbplot.py` and not by KiCad, are in `docs/handover/images/`:
   - `fix_2026-10-31_48v_j703.png`
   - `fix_2026-10-31_u301_softstart.png`
   - `fix_2026-10-31_console_enc.png`

## 9. Engineering review notes (for the successor)

- **FLY_SS** uses two 0.5/0.3 mm vias, the board minimum (`min_via_diameter` 0.5, annular 0.1). Confirm with the fab (U-16). A one-layer FLY_SS route needs FLY_EN re-routed around the north of U301.
- **U301 east channel:** gaps of 0.150–0.152 mm, exactly the 0.15 mm rule. Fine for DRC, with no margin for a tighter fab.
- **ENC_A_S:** 6 vias over 65 mm. It runs in the same corridor as ENC_B_S, passing the R307/R308 feedback divider and the flyback block. It keeps the 0.6 mm HV48 clearance, but it is a long digital line near a switching stage. Review crosstalk and EMC, or shorten the route after the U501 re-layout.
- **J503** is no longer at a board edge. That is acceptable for a bench console cable; revisit with any enclosure.
- **Autorouted copper around the placeholder transformer T301** is still not final (U-04, U-21, FL-1 to FL-4, FL-9).
- **Stored zone fills** are cut-back approximations. Refill in KiCad before any review or output.

## 10. Decisions still requiring owner approval (unchanged by this session)

| ID | Decision |
| --- | --- |
| U-04 / FL-4 | Flyback transformer T301 selection |
| U-05 | ST documents: STM32WBA55 datasheet, NUCLEO-WBA55CG (MB1803) files, RF design guide, STM32C031 datasheet |
| U-06 / FL-7 | 48 V output switch and bleeder: design them, or delete the placeholders and keep R311 |
| U-23 / FL-8 | Secondary OVP on +48V_RAW (54.2 V ceiling vs the PMD401's 50.4 V maximum) |
| FL-3 | AGND/PGND grounding strategy |
| FL-6 / CF-6 and U-17 | HV clearance rule; JST SH rating for the 48 V lead to J703 |
| U-16 / U-20 | Fab and stack-up (also sets the 50 Ω RF width and the minimum via) |
| U-18, U-15, U-24 | Battery, connector and fuse, and charge current; TVS parts; input-current budget |

The FL-1 and FL-2 flyback loop compaction (blocker report) was **not** done. It depends on the transformer footprint (FL-4), and the blocker report lists it as needing approval to modify the flyback layout.

## 11. Files changed in this session

| File | Change |
| --- | --- |
| `hardware/kicad/pump_v2.kicad_pcb` | Moves, routes, stub removal, silkscreen, re-clipped stored zone fills |
| `scripts/gen_pcb.py` | `ANCHORS` record the new C305, TP302 and J503 positions; C305 removed from `NEAR` |
| `scripts/pcbcheck.py`, `pcbedit.py`, `pcbroute.py`, `pcbsilk.py`, `pcbplot.py`, `layout_fixes.py`, `report_unrouted.py` | New tooling (pure Python + shapely) |
| `validation/logs/layout_fixes_2026-10-31.log`, `pcbcheck_2026-10-31.txt`, `unrouted_nets_2026-10-31.txt` | New results (pcbcheck.py, not kicad-cli) |
| `docs/handover/images/fix_2026-10-31_*.png` | Review plots of the changed areas |
| `docs/handover/LAYOUT_FIXES_2026-10-31.md` (this file), `FINAL_HANDOVER.md`, `HANDOVER_GUIDE.md`, `UNRESOLVED_ISSUES.md`, `BLOCKER_RESOLUTION_REPORT.md`, `decisions/DECISION_LOG.md` §7, `CLAUDE.md` (status line) | Documentation |

**Git:**

- Checkpoint tag `checkpoint/pre-layout-fixes-2026-10-31` → `976a17b` (known-good baseline).
- Tooling commit `070c403`.
- Layout and documentation commit `2ca5934` (section 12).

## 12. Commit record

| Commit | Content |
| --- | --- |
| `976a17b` | Known-good baseline (tag `checkpoint/pre-layout-fixes-2026-10-31`) |
| `070c403` | Tooling only (pcbcheck/pcbedit/pcbroute/pcbplot/pcbsilk/layout_fixes/report_unrouted) |
| `2ca5934` | **Layout fixes, validation logs and documentation (this report)** |

To go back to the baseline board: `git checkout 976a17b -- hardware/kicad/pump_v2.kicad_pcb`. The tag `checkpoint/pre-layout-fixes-2026-10-31` was created in the session's clone, but the remote refused the tag push (only the working branch can be pushed from the cloud session). The baseline commit itself is in the pushed branch history. Re-create the tag locally with `git tag checkpoint/pre-layout-fixes-2026-10-31 976a17b`.
