# Piezo Insulin Pump v2 Rev B: current status and handoff (living document)

**Updated:** 11 Oct 2026, after routing Stage 3 (tag `route-stage3-done`, branch `placement-opt`).

**Board status:**
- Digital design only. **NOT fully connected, NOT electrically verified, NOT fabrication-ready.**
- Bench prototype for water or 0.9 % saline only. Never to be connected to a person or animal, and never to be used with insulin.

**Recovery points (never amended):**

| Tag | State |
|---|---|
| `baseline-routing-e8d141c` | Before placement optimisation |
| `9da03dc` (commit) | Approved v2 placement |
| `route-stage1-before` | Before Stage 1 routing |
| `route-stage1a-hand` | Stage 1 power-critical routes |
| `route-stage1-done` | Stage 1 complete |
| `route-stage2-before` | Before Stage 2 |
| `route-stage2-done` | Stage 2 complete (commit 3f7ba36) |
| `route-d1-before` | = 3f7ba36 |
| `route-d1-done` | D1 rotation milestone complete (commit 6a4367b) |
| `route-stage3-before` | = 6a4367b |
| `route-stage3-done` | Stage 3 complete |

## 1. Completed work

| Milestone | Commit | Record |
|---|---|---|
| Blocker-resolution report | b0e5473 | `BLOCKER_RESOLUTION_REPORT.md` |
| Placement proposal (v1–v3 evaluated on scratch copies) | 932d752 | `PLACEMENT_PROPOSAL.md` §0–7 |
| Approved v2 placement applied (no M8; R711/R712/R312 not moved) | 9da03dc | `PLACEMENT_PROPOSAL.md` §8 |
| Stale BOM re-exported; every difference documented | 0b56596 | `BOM_REEXPORT_DIFF.md` |
| Pre-routing reconciliation and topology gate | 9710ac7 | `ROUTING_STAGES.md` §0 |
| Stage 1: LM51551 controller nets | 8c1c80c, 844fa0a | `ROUTING_STAGES.md` §1 |
| Audit and routing plan; owner rulings on D1–D6 | 4510a91 (and the Stage 2 commit) | this document, §3–5 |
| Stage 2: ENC_VCC, PMD_5V, CON_SUP_TX/RX | 3f7ba36 | `ROUTING_STAGES.md` §2 |
| D1: R301/R302/C305/R308 rotated 180°; FB/SS/RT re-routed; FLY_PGOOD U301.11–R302 and +3V3 to R302 | 6a4367b | `ROUTING_STAGES.md` §3 |
| Stage 3: FLY_EN (without the DNP Q303) and HB_S2M | Stage 3 commit | `ROUTING_STAGES.md` §4 |

## 2. Test results

**Only software checks have been run.** No electrical, bench or manufacturing test has been performed. Nothing below is evidence that the circuit works.

| Check (kicad-cli 10.0.3) | Result at `route-stage3-done` |
|---|---|
| ERC | 6 `power_pin_not_driven` on U501 pins 3, 38, 39, 40, 43 and 45. These are intentional: the WBA55 supply wiring waits for the ST documents and they are not suppressed. Plus 1 cosmetic `lib_symbol_mismatch` on U701. |
| DRC copper (clearance, short, crossing, hole, edge) | 0 |
| Schematic–PCB parity | 0 |
| Unconnected pairs | **54** (59 after D1; 61 after Stage 2; 67 after Stage 1; 80 after placement) |
| Warnings | 6 via_dangling, 1 track_dangling (pre-existing, on WBA55 and group-G nets); 83 silk_overlap, 71 silk_over_copper, 3 silk_edge, 2 unmirrored text (cosmetic) |
| Simulation | Flyback open-loop LTspice runs only (`FLYBACK_DESIGN.md`). No control-loop model exists for the LM51551. |

## 3. Net-by-net audit of the unconnected pairs

This audit was taken at `route-stage1-done` (67 pairs). Stage 2 closed 6 (**[routed, Stage 2]**), D1 closed 2 (**[routed, D1]**) and Stage 3 closed 5 (**[routed, Stage 3]**); 54 remain. The current per-pair list is always `validation/logs/unrouted_reconciliation.md`: W 12 / P 11 / R 19 / G 12 = 54.

**Sources:**
- `validation/drc/pump_v2-drc.json` (DRC at `route-stage1-done`);
- `validation/logs/unrouted_reconciliation.md`;
- `validation/logs/unrouted_corridors.txt`.

The gaps are straight-line distances between the reported endpoints.

**Status key:**
- **R** = can be routed from existing evidence;
- **G** = needs an owner decision at a gate (D-x, §5);
- **B** = blocked by missing documents or an unresolved design decision.

### 3.1 WBA55-dependent (12 pairs, status B: needs DS14127, RM0493, ES0592, AN5948 and the NUCLEO schematic, U-05)

| Net | Endpoints | Gap (mm) | Blocker |
|---|---|---|---|
| HSE_IN | U501.42 – Y501.1 | 9.4 | HSE crystal routing and load capacitors need the ST oscillator and layout guidance |
| HSE_IN | C516.1 (DNP, placeholder) – U501.42 | 17.8 | As above; C516 value and fit TBD |
| HSE_OUT | U501.41 – Y501.3 | 8.2 | As above |
| HSE_OUT | C517.1 (DNP, placeholder) – U501.41 | 18.6 | As above |
| LSE_IN | U501.17 – Y502.1 (DNP, placeholder) | 16.0 | LSE crystal fit and routing guidance |
| LSE_IN | C518.1 (DNP, placeholder) – U501.17 | 15.9 | As above |
| RF_MCU | track – U501.37 | 16.5 | RF matching and 50 Ω line need AN5948 and the stack-up (U-20) |
| WBA_VDD11 | L501.2 (placeholder) – U501.45 | 5.7 | VDD11 and SMPS configuration from DS14127 |
| WBA_VDD11 | U501.45 – C509.1 (placeholder) | 8.5 | As above |
| WBA_VDDANA | track – U501.39 | 19.1 | Supply topology from DS14127 |
| WBA_VDDRF | track – U501.40 | 16.9 | As above |
| WBA_VDDRFPA | U501.43 – track | 13.2 | As above |

### 3.2 Flyback power stage (5 pairs, status B: transformer U-04 / FL-1 / FL-4; the two pairs ending on T301 itself are counted in §3.4)

| Net | Endpoints | Gap (mm) | Blocker |
|---|---|---|---|
| FLY_SW | D302.2 – Q301.5 | 3.7 | Switch-node geometry depends on the real T301; the switch node and clamp loop should be laid out together |
| FLY_CLAMP | C308.1 – D302.1 | 1.8 | RCD clamp loop geometry and values depend on T301 leakage |
| FLY_CLAMP | R306.1 – C308.1 | 8.2 | As above |
| FLY_SEC | R313.1 – D301.2 | 2.1 | Snubber values and placement depend on T301 |
| FLY_SNUB | R313.2 – C312.1 | 2.8 | As above |

### 3.3 48 V output (8 pairs, status B: OVP U-23 / FL-8, output switch U-06, J703 rating U-17 / FL-6 / CF-6)

| Net | Endpoints | Gap (mm) | Blocker |
|---|---|---|---|
| +48V_RAW | D301.1 – C312.2 | 2.1 | OVP may need space on +48V_RAW; snubber depends on T301 |
| +48V_RAW | D301.1 – C310.1 | 3.5 | OVP / output decision |
| +48V_RAW | C310.1 – C309.1 | 3.5 | As above |
| +48V_RAW | C309.1 – R311.1 | 5.2 | As above; R311 0 R is the bypass of the undesigned switch |
| +48V_RAW | C311.1 (PTH) – C312.2 | 16.4 | As above |
| +48V_MOT | R311.2 – J703.2 | 4.0 | J703 (JST SH, 1.0 mm pitch) rating at 48 V and the HV48 clearance rule are unapproved |
| +48V_MOT | J703.2 – TP301.1 | 3.9 | As above |
| +48V_MOT | C702.1 (PTH) – R311.2 | 8.5 | As above |

### 3.4 Placeholder or DNP endpoints (11 pairs)

| Net | Endpoints | Gap (mm) | Status |
|---|---|---|---|
| +48V_MOT | TP301.1 – R312.1 (DNP bleeder) | 20.7 | B (U-06 / E-11) |
| +48V_MOT | R312.1 – Q302.3 (DNP switch) | 45.6 | B (U-06) |
| +48V_RAW | R311.1 – R309.2 (DNP) | 5.7 | B (U-06) |
| +48V_RAW | Q302.2 – Q302.2 (tab and pin of the DNP part) | 6.3 | B (U-06) |
| +48V_RAW | Q302.2 – C311.1 | 19.0 | B (U-06) |
| +48V_RAW | Q302.2 – R307.1 | 25.2 | B (U-06) |
| SW48_GATE | R309.1 (DNP) – track | 21.8 | B (U-06). See D2: this net's existing track is floating copper next to the switch node |
| FLY_EN | U301.12 – Q303.1 (DNP level shifter) | 17.2 | B (U-06). The fitted FLY_EN pads are routed in Stage 3 without Q303 |
| FLY_SEC | D301.2 – T301.4 | 3.2 | B (U-04) |
| FLY_SW | T301.2 – D302.2 | 3.9 | B (U-04) |
| RS485_B | R714.2 (DNP 120 R terminator) – U701.7 | 21.2 | **G (D3):** the part's function is defined, so routing its pads is low-risk. J704.2 and U701.7 are already connected. |

**Total check:** 12 (§3.1) + 5 (§3.2) + 8 (§3.3) + 11 (§3.4) + 31 (§3.5) = 67.

### 3.5 Routable now, from existing evidence (status R, unless a gate is named)

| Net | Endpoints | Gap (mm) | Notes |
|---|---|---|---|
| ENC_VCC **[routed, Stage 2]** | JP701.2 – C701.1 | 4.1 | Corridor clear on both layers |
| ENC_VCC **[routed, Stage 2]** | C701.1 – J705.3 | 5.8 | One GND stub in the straight path; short detour |
| PMD_5V **[routed, Stage 2]** | JP701.3 – J702.2 | 13.5 | PMD401 "5V Out" to jumper. Crosses ENC_A, ENC_SHLD and GND on F.Cu; B.Cu has RS485_A/B |
| PMD_5V **[routed, Stage 2]** | J702.2 – J701.3 | 9.0 | Between the two PMD401 connectors; F.Cu crosses PMD_FAULT, MOSI and READY. Likely B.Cu |
| CON_SUP_TX **[routed, Stage 2]** | J503.3 (PTH) – U601.29 | 15.9 | Console to supervisor UART. U601 pins checked by CubeMX |
| CON_SUP_RX **[routed, Stage 2]** | J503.4 (PTH) – U601.32 | 13.4 | As above; corridor nearly clear |
| +3V3 **[routed, D1]** | R302.2 – nearest +3V3 via (147.2, 159.5) | 15.8 | R302 (PGOOD pull-up) sits over the In2 VBAT polygon of the 48 V block, so its +3V3 via has no plane. It needs a track out to the +3V3 plane region (x < 155). |
| FLY_EN **[routed, Stage 3]** | R402.2 – TP401.1 | 3.1 | **Stage 3 safety gate.** Kill-path node (K-10) |
| FLY_EN **[routed, Stage 3]** | R401.1 – TP401.1 | 5.2 | As above |
| FLY_EN **[routed, Stage 3]** | TP401.1 – Q401.3 | 7.0 | As above |
| FLY_EN **[routed, Stage 3]** | Q401.3 – U301.12 | 25.6 | As above. U301 pin 12 escapes south-west to a via at about (164.2, 161.0) that was kept free in Stage 1. Runs past the COMP/FB area on B.Cu. |
| HB_S2M **[routed, Stage 3]** | U501.12 – U601.13 | 42.5 | **Stage 3 safety gate.** U501.12 is on the pin 1–12 side, near the SMPS pins 1–3, so the route must leave room for the ST layout (D5) |
| FLY_PGOOD **[routed, D1]** | U301.11 – R302.1 (local) | 4.0 | Resolved by the D1 rotation (ROUTING_STAGES.md §3) |
| FLY_PGOOD | U301.11 – U501.28 | 41.7 | After D1. U501.28 is on side 25–36 (no supply or oscillator pins) |
| ENC_B | R712.2 – D708.1 | 5.5 | Encoder input protection area |
| ENC_B | D708.1 – R709.2 | 9.8 | As above |
| ENC_B | J705.4 – R712.2 | 36.3 | Long run from J705 (moved earlier) |
| ENC_B_S | U601.18 – R712.1 | 62.6 | Supervisor encoder copy (S-07); long run |
| ENC_A_S | U601.17 – R711.1 | 60.9 | As above (pre-existing genuine) |
| ENC_I | J705.1 – track | 41.6 | Pre-existing genuine |
| VBAT_FUSED | U101.C2 – C102.1 | 7.2 | **G (D4):** U101 BQ25188 YBG footprint pitch is inferred (U-12). Battery-side decoupling (SLUSFJ3) |
| CHG_INT_N | U101.A1 – track | 9.6 | G (D4) |
| I2C_SDA | U101.C1 – R105.1 | 12.4 | G (D4) |
| I2C_SDA | R105.1 – U501.6 | 19.3 | **G (D5):** U501.6 is next to SMPS and VDDA pins |
| PMD_SCLK_M | U501.13 – R704.1 | 36.3 | G (D5): U501.13 is next to the LSE pins 16/17 |
| PMD_MOSI_M | track – R702.1 | 26.0 | G (D5): U501.15, LSE side |
| VBAT_SENSE | track – track (R108 to U501.14 path) | 28.0 | G (D5): U501.14, LSE side |
| CON_MAIN_TX | J503.2 (PTH) – U501.4 | 29.3 | G (D5): U501.4 is next to the SMPS pins |
| ENC_I_M | U501.48 – track | 15.1 | G (D5): U501.48 is next to the VDD11 / RF pins 43–45 |
| MAIN_SWCLK | track – U501.26 | 7.0 | Side 25–36. Can go with Stage 5a |
| PMD_READY_M | U501.33 – R706.1 | 36.3 | Side 25–36. Stage 5a |

## 4. Proposed routing order

Each stage gets the same procedure:
- Checkpoint tag before the stage.
- Explicit route specification (JSON), or a DRC-verified point-to-point route, limited to the named nets.
- Zone refill.
- ERC, DRC with parity, and connectivity checks.
- `compare_stage.py` against the previous checkpoint, reporting every changed or new pair and any copper on non-stage nets.
- A commit, then a stop at every gate marked ⛔.

| Stage | Nets (pairs) | Why this order | Gate |
|---|---|---|---|
| **2 (done)** | ENC_VCC ×2, PMD_5V ×2, CON_SUP_TX, CON_SUP_RX (6). +3V3 to R302 moved to D1 | Short, fully defined, away from U501 and the flyback | ⛔ stopped for review |
| **D1 milestone (done)** | Rotated R301, R302, C305 and R308 by 180°; re-routed FB, SS, RT and the GND fan-outs; FLY_PGOOD U301.11 – R302; +3V3 to R302 (2 pairs closed) | Approved (option 1) | ⛔ stopped for review |
| **3 (done)** | FLY_EN ×4 (not Q303), HB_S2M (5) | Safety-control nets get their own stage and review. The intended pads and levels are in ROUTING_STAGES.md §0.2. A routed net proves continuity only, not fail-off behaviour (SG-03/SG-05 are bench tests). | ⛔ separate safety review |
| **4** | ENC_B ×3, ENC_B_S, ENC_A_S, ENC_I; RS485_B to R714 if D3 is approved (6–7) | Encoder and supervisor signals, away from U501's supply sides | ⛔ |
| **5a** | MAIN_SWCLK, PMD_READY_M, FLY_PGOOD U301.11 – U501.28 (3) | U501 side 25–36 has no supply or oscillator pins. **Owner: only where the pin assignment and supply requirements are verified.** The pins are CubeMX-checked; the supply requirements are still unread (U-05), so each net is checked for independence from the supply layout before routing. | ⛔ |
| **5b** | I2C_SDA (R105–U501), PMD_SCLK_M, PMD_MOSI_M, VBAT_SENSE, CON_MAIN_TX, ENC_I_M (6) | Next to the SMPS, VDDA, LSE and RF pins. **Recommend waiting for the ST documents (D5)** to avoid rework | ⛔ D5 |
| **6** | VBAT_FUSED, CHG_INT_N, I2C_SDA (U101–R105) (3) | Needs D4 (unverified BGA footprint) | ⛔ D4 |
| Blocked | 12 WBA55 + 5 flyback + 8 48 V output + 11 placeholder or DNP (36; 35 if D3 routes R714) | Need documents or design decisions (§5) | n/a |

**Expected count if Stages 2–6 are all approved:** 67 → about 36 (the blocked set), or about 35 if D3 is approved. **The board cannot be completed** until U-04, U-05, U-06 / U-23 and U-17 / FL-6 are resolved.

## 5. Outstanding approvals and decision gates

**Owner rulings, 11 Oct 2026:**
- **D1:** approved, option 1, subject to clearance and connectivity checks. **Applied at `route-d1-done`:** DRC 0 copper violations, parity 0, no regressions, grounding topology unchanged (ROUTING_STAGES.md §3).
- **D2:** copper changes deferred. The concern is documented in §6.
- **D3:** keep the undefined placeholder circuitry unrouted. **Ask the owner before connecting RS485_B to R714.**
- **D4:** wait for the BQ25188 footprint documentation.
- **D5:** wait for the ST documents before the crystal and RF connections. Stage 5a only where the pin assignments and supply requirements are verified.
- **D6:** no grounding-topology change, and no grounding-dependent layout change, without owner review.

The table below is the original proposal, kept for the record.

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| **D1** | FLY_PGOOD U301.11 escape (ROUTING_STAGES.md §1.3) | (a) Rotate R301, R302, C305 and R308 by 180° (component move). (b) Local AGND copper tie to U301 (decides FL-3). (c) Give pin 11 the FLY_EN escape via (worse FLY_EN route). | (a) is the cleanest, with no grounding-topology change |
| **D2** | SW48_GATE / SW48_DRV placeholder tracks. Every endpoint (Q302, Q303, R309, R310) is DNP, so this copper is **floating**. One track runs on F.Cu at x = 170.33, between the Q301 source and drain pads, next to the switch node. | Remove these two placeholder nets' tracks now, or keep them until U-06 | **Remove.** Floating copper beside the switch node is a coupling and EMI concern, and the output-switch layout will be redone anyway. |
| **D3** | Routing to DNP option pads | Route the defined-function DNP R714 (RS-485 terminator); leave the undesigned placeholders (Q302, Q303, R309, R310, R312) unrouted | As stated |
| **D4** | Route on the U101 BQ25188 YBG footprint before the TI drawing check (U-12) | Route now (rework risk) or wait | Wait for the drawing, or accept the risk explicitly |
| **D5** | U501 fan-out next to the supply, oscillator and RF pins before the ST documents | Route now or wait | Wait. Do only side 25–36 (Stage 5a) now |
| **D6** | Gate-drive via crossing, U301 exposed-pad thermal vias, Kelvin landing point | Accept as is; add EP thermal vias (layout addition); refine the Kelvin landing | Add EP thermal vias after FL-3; keep the gate crossing (topologically forced) |

**Open items carried from earlier reports:**
- U-04: transformer.
- U-05: ST documents.
- U-06 / U-23: output switch, bleeder and OVP.
- U-17 / FL-6 / CF-6: J703 rating and the HV48 clearance rule.
- FL-3: AGND / PGND strategy.
- U-12: footprint drawings.
- U-14: encoder supply and pinout.
- U-15: TVS parts.
- U-16: fab and stack-up.
- U-18: battery, connector, fuse and master switch.
- U-20: RF impedance.
- U-24: input current about 2.0–2.3 A against the 2.1 A budget.
- U-10: pin electrical properties.

## 6. Review of sensitive geometry (owner item 6)

| Topic | Current state | Unresolved concern |
|---|---|---|
| Switch node (FLY_SW: Q301.5, D302.2, T301.2) | Not routed (blocked, U-04). The clamp loop is placed compactly (straight path 14 mm). | The final loop area cannot be judged until T301 exists. The node is 7.4 mm, a deliberate trade for the smaller clamp loop. |
| Kelvin sense (U301.5 → R305.1) | Separate 0.2 mm trace with no shared copper | Lands on the outer half of R305.1, not the inner edge. The return side goes through the plane (FL-3). It runs parallel to the 0.5 mm power track for about 3.3 mm. |
| Gate drive (U301.3 → Q301.4) | 4.67 mm, 2 vias | The via pair is forced by the topology. The B.Cu segment references In2 (VBAT), not GND. |
| FLY_EN (Stage 3) | Routed; tightest gap 0.224 mm (FLY_PGOOD); at least 1.79 mm from gate, CS and switch copper | B.Cu run over the In2 VBAT polygon (pulsed primary current); the UVLO/SYNC pin treats falling edges as sync. Coupling not analysed. Fail-off behaviour needs SG-03 / SG-05 on hardware. |
| HB_S2M (Stage 3) | Routed around the WBA55 supply-placeholder block (64.9 mm) | Long heartbeat line; 0.199 mm to SUP_NRST at the U601 corner; heartbeat and timeout behaviour untested (firmware). |
| Exposed-pad grounding (U301.13) | PGND pin 4 joins the pad directly; the pad has 1 plane via | Fewer vias than the SNVSB75E thermal guidance suggests (D6). The AGND/PGND strategy is open (FL-3). |
| SW48_GATE crossing | A placeholder-net track runs between the Q301 source and drain pads. DRC passes. | **Owner deferred the copper change (D2).** Open concern: SW48_GATE and SW48_DRV have only DNP endpoints, so their tracks are floating conductors. One runs on F.Cu at x = 170.33, between the Q301 source pads (CS) and the drain pad (FLY_SW switch node, about 0 to 25 V at 300 kHz). That invites capacitive coupling of switching noise and is a needless antenna. Resolve with U-06 / M8, by removing the tracks or re-routing them away from the switch node. |
| HV48 clearance | 0.6 mm rule enforced. Two scoped exceptions inside the J703 and Q301 footprints only. | The rule value itself is unapproved (FL-6 / CF-6) |

## 7. Assumptions and deviations (current; the full register is `ASSUMPTIONS_AND_DEVIATIONS.md`)

- **Board rules are generic 4-layer values.** No fab has been chosen (U-16).
- **Stage 1 VCC decoupling:** U301 VCC/BIAS is fed through C304, and three plane vias were removed. C305.2 shares R308.2's GND via. These are routing choices; the schematic is unchanged.
- **R312 is not moved.** It keeps its baseline position because the v2 spot collided with R309 once M8 was deferred.
- **Stages 1–3 and D1 do not use Freerouting.** Freerouting 2.1.0 did not honour the net-class restriction or the pass limit.
- **BOM CALC values are calculations and simulations.** None has been bench-verified.
