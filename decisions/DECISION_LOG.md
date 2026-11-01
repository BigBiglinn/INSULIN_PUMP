# DECISION_LOG.md

Decisions recorded in the project, oldest first. "Owner" = B Charan. A decision counts as DECIDED when the owner stated it or accepted it into the final parts list. Suggestions written by Claude that the owner has not signed off are listed separately in section 4 and are not decisions.

Dates are from project records (2026).

## 1. Decisions that must not be changed without the owner's approval

| # | Locked decision |
| --- | --- |
| K-1 | Water or saline only, bench only, never on a person or an animal |
| K-2 | Piezo motor + positive-displacement syringe. No diaphragm/valve pump, no stepper, no screw |
| K-3 | Motor: Piezo LEGS LL06, item code LL06A0-101M1G1E2 (guided, 100.8 mm rod, front adapter, 80 nm encoder) |
| K-4 | Driver: PMD401, used as bought |
| K-5 | Syringe: Hamilton 1001 TLL, PN 81320 |
| K-6 | Main MCU: STM32WBA55CG (NUCLEO-WBA55CG). Supervisor: STM32C031C6 (NUCLEO-C031C6). STM32 only |
| K-7 | Two stages: Rev A on the bench first, Rev B PCB second |
| K-8 | Rev A runs from the single Li-ion cell through the real power tree |
| K-9 | Rev A power tree parts: Molicel INR18650-P28A, 1S 5 A protection board, 5 A fuse, switch, INA219, MCP1700-3302E/TO, Pololu U3V70F12, DC2628A (LT8362), TP4056 for charging only |
| K-10 | Kill path is fail-off: 4.7 kΩ EN pull-down, main MCU through 1 kΩ, supervisor veto through one BSS138 |
| K-11 | 48 V rail on only while dosing |
| K-12 | Rev B power parts: BQ25188, LM51551 flyback with switched output, TPS62840, 1S protected cell |
| K-13 | Sensorless occlusion detection from step length is the occlusion method. No pressure sensor on the final device |
| K-14 | Dose limits: 0.05 U minimum, 10 U maximum bolus, 15 U per rolling hour |
| K-15 | Dosing speed cap about 15 steps/s |
| K-16 | Firmware: plain C11 behind `pump_port.h`; the owner writes it, with explained reference code |
| K-17 | BLE on the WBA55: phone now, CGM team's protocol later |
| K-18 | Rev A parts from Indian websites where possible; cost cut only where performance is untouched |

## 2. Chronological log

### v1 (before September 2026)

| Date | Decision | Rationale | Status |
| --- | --- | --- | --- |
| Before Sep | Build HybridPancreasSim: C++ closed-loop simulator (Bergman minimal model, PID, predictive controller, safety supervisor, fault injection) plus an ESP32 demo | Demonstrate control concepts used in commercial pumps | SUPERSEDED as hardware. Simulator results stand as background: PID about 89 % time in range; Predictive + Supervisor about 93 % with 0 % hypoglycemia |
| Before Sep | ESP32 DevKit + A4988 (SmartElex) + NEMA 17 JK42HS40-1204AF-02 on a T8 leadscrew, 11.1 V 3S LiPo; STEP = GPIO26, DIR = GPIO27 | Visible motor movement for a demo | SUPERSEDED |
| 8 Sep | Goal is to recreate the pump's function, not a specific commercial device's architecture | Owner's clarification | DECIDED |
| 8 Sep | Cost and part sourcing are not constraints; full lab available. Piezo motor considered to shrink the device | Owner's clarification | DECIDED (later refined on 30 Sep: still minimise cost where free) |

### v2 re-scope

| Date | Decision | Rationale | Status |
| --- | --- | --- | --- |
| 21 Sep | Everything built so far is prototype only. v2: smaller motor, all on STM32, close to industry grade | Owner | DECIDED |
| 21 Sep | End goal: small working prototype, correct dosing, never on humans | Owner | DECIDED |
| 21 Sep | Whole project in 30 days | Owner | DECIDED |
| 22 Sep | Keep Rev A (bench) → Rev B (PCB). Do not skip straight to a PCB | The owner weighed the 30-day timeline against the risk and chose not to take it | DECIDED |
| 22 Sep | STM32WBA55CG as main MCU, STM32C031C6 as independent supervisor | Integrated BLE and TrustZone on the main MCU; a dissimilar second MCU so one fault cannot defeat both | DECIDED (survived every later redesign) |
| 22 Sep | Stepper plan: Faulhaber AM0820 + 64:1 gearhead, STSPIN220, AS5048A, Honeywell ABP2 | Smaller than NEMA 8 | SUPERSEDED by the piezo design |
| 22–24 Sep | "Piezo-LEGS Insulin Pump v2 — Master Engineering Specification" written (LT20 motor, Hamilton 1005, AS5311 encoders, flyback, R-01 to R-29, changes C14 and C15) and a 154-slide review deck built from it | Full-scope autonomous design exercise | SUPERSEDED. The 10 Oct report treats it as superseded and reuses only test ideas |
| 25 Sep | Owner scrapped all prior piezo-motor work and restated the architecture: 3.7 V battery → HV boost → PZT driver → PZT; same cell powers the STM32 | Owner wants own architecture and novelty | DECIDED (architecture). The parts chosen that day (STM32U585, DRV8662, nRF module, STM32C011, valve pump) are SUPERSEDED |
| 25 Sep | Electronics first; mechanical only after the PZT is running | Owner | DECIDED |
| 25 Sep | BLE to connect a CGM. Phone input now; another team's custom CGM later | Owner | DECIDED |
| 27 Sep | Scrap single-PZT + valve (diaphragm) pump. Use a piezo motor driving a positive-displacement syringe | Owner | DECIDED |
| 27 Sep | Reject Shinsei USR30-E3 | Datasheet check: humidity limits incompatible with Guwahati's climate, thrust-load limits incompatible with a leadscrew, impractical size | DECIDED |
| 27 Sep | Select Piezo LEGS LL06 with PMD401, NUCLEO-WBA55CG, NUCLEO-C031C6, Hamilton 81320, disposable IBP transducer as bench reference; BQ25188 and LM51551 for Rev B | Checked against datasheets and manuals | DECIDED |
| 27 Sep | Remove diaphragm pump, Shinsei motor, NUCLEO-G474RE, custom HV transformer driver, leadscrew assembly, BQ25180 | Listed with reasons at the time | DECIDED |
| 27 Sep | Novelty directions: (1) sensorless occlusion detection from commanded steps versus encoder travel, (2) fault-injection hardening of dose logic, verified with ChipWhisperer | Fits the hardware and the owner's fault-injection background | DECIDED (2 is a stretch goal) |
| 27 Sep | Owner learns the firmware: explained reference code plus a staged course | Owner's preference | DECIDED |
| 29 Sep | Rev A parts list declared final and ready to order: LL06 Starter Kit (PMD401), Hamilton 1 mL, NUCLEO-WBA55CG, NUCLEO-C031C6 | Owner | DECIDED |
| 29 Sep | LL06 configurator: 80 nm encoder, front adapter, 0–77.4 mm stroke, Starter Kit | 0.05 U is only about 30 µm of travel, so 1.25 µm is too coarse for self-sensing; front adapter mounts the plunger pusher; only that stroke option covers 60 mm | DECIDED |
| 29 Sep | DRV8662 and DRV2700 are out | Single-channel; the LL06 needs four synchronized 0–48 V channels | DECIDED |
| 29 Sep | PMD401 in servo mode: MCU sends a signed step rate over SPI and closes the loop on the encoder itself | Needed for self-sensing; gives the SPI-timeout stop path | DECIDED |
| 29 Sep | Force rule: friction + occlusion load under about 3 N (half of stall) | LL06 recommended range | DECIDED |
| 29 Sep | Speed cap about 15 waveform steps/s (about 0.11 U/s) | Faster plunger motion raises line pressure on its own and looks like an occlusion | DECIDED |
| 29 Sep | Default limits: 0.05 U minimum, 10 U bolus, 15 U per rolling hour | Project values, not clinical | DECIDED |
| 29 Sep | Rev B 48 V stage is a flyback, not a plain boost | A plain boost from 3.0–4.2 V to 48 V hits the 93 % duty limit | DECIDED |
| 29 Sep | Rev A runs from the kit's 48 V supply; battery chain waits for Rev B | Simplest bring-up | SUPERSEDED on 30 Sep |
| 30 Sep | Rev A is powered from the 3.7 V battery | Validate the power tree before the PCB | DECIDED |
| 30 Sep | Buy Rev A parts from Indian websites; minimise cost where performance is not sacrificed | Owner | DECIDED |
| 30 Sep | Two-stage boost on Rev A: Pololu U3V70F12 (3.7 → 12 V) then DC2628A / LT8362 (12 → 48 V) | Off-the-shelf; each stage efficient; DC2628A gives 48 V with no rework | DECIDED |
| 30 Sep | Pololu U3V70F12 kept in first position | It truly disconnects its output when disabled, so switching it off kills the whole 48 V chain | DECIDED |
| 30 Sep | Kill switch made fail-off: 4.7 kΩ EN pull-down, main MCU through 1 kΩ, supervisor BSS138 veto | The Pololu's EN has a 100 kΩ pull-up to VIN, so the earlier design was fail-on | DECIDED |
| 30 Sep | One BSS138 instead of two | Simpler, and now fail-off | DECIDED |
| 30 Sep | DC2628A output capacitor replaced by 47 µF / 100 V | Stock 50 V part would run at 96 % of its rating | DECIDED |
| 30 Sep | MCP1700-3302E/TO LDO on Rev A instead of the TPS62840 EVM; TPS62840 goes onto the Rev B PCB | Cost; MCU load is about 30 mA; LDO is quieter for ADC readings | DECIDED |
| 30 Sep | INA226 module replaced by INA219 module | INA226 out of stock everywhere checked; INA219's 0.1 Ω shunt covers 3.2 A | DECIDED |
| 30 Sep | Load runs from the 5 A protection board; TP4056 for charging only | The TP4056 module's own protection trips near 3 A, too close to the 2.1 A peak | DECIDED |
| 30 Sep | Firmware stops dosing at VBAT ≤ 3.4 V | Below about 3.35 V the 3.3 V rail follows the battery down and the MAX3485 needs ≥ 3.0 V | DECIDED |
| 30 Sep | Stay with NUCLEO-WBA55CG over NUCLEO-WB55RG | TrustZone, simpler single-core BLE firmware, stronger radio, direct path to the Rev B PCB | DECIDED |
| 30 Sep | Reject the Robu TPS61040-based boost | 50 mA against 450 mA needed; no true output disconnect | DECIDED |
| 30 Sep | USB-to-RS-485 adapter optional; one cell required, second optional; fit-test with disposable syringes | Cost | DECIDED |
| 8 Oct | Order one guided LL06 with the 80 nm encoder (E2), 100.8 mm rod, one front adapter: LL06A0-101M1G1E2 | The first quote wrongly carried two motor lines; vendor confirmed E2 = 80 nm and quadrature 3.3–5 V output | DECIDED (quote requested). Acceptance and payment not recorded |
| 10 Oct | The LT20 / Hamilton 1005 Master Engineering Specification is superseded; baseline is the LL06 design frozen 29–30 Sep and quoted 8 Oct | Written into the requirements report | DECIDED by the report; no objection recorded |
| 10 Oct | Rev B described as a custom 4-layer PCB | Requirements report | 4 layers is PROPOSED (P-02) |

## 3. Design reasoning worth keeping

- Unpowered is safe because a LEGS motor with no voltage clamps its rod at more than its stall force (6.5 N). Every power-loss or reset fault ends in a locked plunger, so there is no free flow.
- The PMD401 idles at about 0.29 W on 48 V (about 7 Wh per day). Leaving the rail on would drain a small cell within a day. The LL06 holds position unpowered, so the rail can be switched off between doses with no plunger drift.
- Dose is tracked as an absolute encoder position, not as a sum of increments, so per-pulse errors do not pile up.
- The 3.3 V rail is tapped from the battery bus, not from the boost chain, so motor current pulses never reach the logic.
- The supervisor differs from the main MCU in core, clock and code base so one bug or one clock fault cannot defeat both.

## 4. Proposals awaiting sign-off (not decisions)

Written by Claude in the 10 Oct report. The owner was asked to accept, change or strike each one and has not yet done so.

- Requirements marked Proposed: D-07, D-10 to D-15, S-04, S-06, S-07, S-09, S-10, S-12, S-14, S-15, E-10, E-11, M-03 to M-05, M-08 to M-10, F-04 to F-08, C-02, C-03, C-05, C-06, P-02, P-03, P-05 to P-08. Partly proposed: D-09 (one-sided stop), S-08 (limits), S-13 (3.5 V warning), S-16 (boot tests), E-06 (80 % rule), E-08 (all but signal type), F-09 (token heartbeat).
- Change the 10 kΩ BSS138 gate resistor from a pull-down to a pull-up to 3.3 V, so the veto is on by default and the supervisor must drive the gate low to permit a dose. Also make the main MCU refuse to dose without a supervisor reply.
- Fit a pull-down on the PMD401 park line strong enough to win against the PMD401's internal pull-up.
- Wire encoder A/B to a C031 timer as well, with its own series resistors, and give the supervisor its own count against the dose limits.
- Add a buzzer driven by the supervisor and a STOP button on a supervisor input.
- Add a 0–2 bar reference pressure sensor, or set the occlusion alarm at or under 0.4 bar.
- Ask PiezoMotor whether the PMD401 can store a hard maximum rate.

## 5. Decisions nobody has made yet

Board size and outline, fab house, connector types, MCU pin assignment, flyback transformer, cell size for Rev B, charge current, battery-life target, link-loss behaviour, CGM message format. See `OPEN_QUESTIONS.md`.

## 6. Decisions recorded in the Claude Code session of 10 Oct 2026 (digital handover objective)

Added after the handoff snapshot. Source: the owner's messages and answers in this session.

| Date | Decision | Rationale | Status |
| --- | --- | --- | --- |
| 10 Oct | Project objective changed: produce a reasonably complete, digitally usable KiCad schematic and PCB for v2 as a **handover prototype**. Fabrication and hardware validation are NOT required before handover. Rev A physical tests are no longer a prerequisite for starting digital design | The owner is leaving the project before completion | DECIDED (owner). Supersedes the "Rev A before Rev B design work" sequencing for the digital design only; K-7 still applies to any fabrication |
| 10 Oct | Supervisor veto gate default (OPEN item 3 / CF-9): place footprints for BOTH a 10 k pull-up and a 10 k pull-down, both DNP, and leave the choice unresolved | Owner chose not to decide in this session | DECIDED (owner) as "unresolved, both footprints". Build is NOT acceptable until one is chosen |
| 10 Oct | BLE RF: U.FL connector with a 3-element pi-match placeholder instead of an antenna | ST RF reference documents unavailable; avoids unverified antenna geometry | DECIDED (owner) |
| 10 Oct | 48 V: K-10 kill network drives LM51551 UVLO/EN; K-12 "switched output" high-side switch and E-11 bleeder placed as DNP placeholders only | A flyback has no DC input-to-output path, so EN low de-energises the rail; switch not designed | DECIDED (owner) |
| 10 Oct | Approved additions: 4-layer stack-up (P-02) and encoder A/B to the C031 supervisor timer (S-07) | Owner selection | DECIDED (owner). P-02 and S-07 move from PROPOSED to DECIDED |
| 10 Oct | Not added to the Rev B board: buzzer + STOP button (S-12) and the INA219 current monitor | Owner did not select them | DECIDED (owner). INA219 omission is a deviation from P-01 ("Rev B carries the Rev A circuit"); battery-voltage sensing for S-13 is therefore OPEN (DNP divider placeholder R107/R108) |
| 10 Oct (later session) | Supervisor veto default: **R403 10 k pull-up fitted**, R404 removed. Veto is ON whenever the supervisor is in reset, crashed or not driving PB0 low | Owner choice after trade-off: meets S-01 (dead supervisor blocks 48 V) at the cost of availability | DECIDED (owner). Closes OPEN item 3 / CF-9. Deviation DV-3 from the Rev A pull-down |
| 10 Oct (later session) | PMD401 AEN: **open-drain BSS138 (Q402) with 10 k gate pull-up (R405)**; supervisor PB1 (SUP_PARK) drives LOW to unpark. Direct drive and the AEN pull-down placeholder R713 removed | PMD401 has a 22 k internal pull-up to an unstated rail; open drain parks by default and lets the PMD401's own pull-up set the run level, so no 3.3/5 V level question | DECIDED (owner). Closes the design side of OPEN item 4; SG-05 still required on hardware |
| 10 Oct (later session) | Flyback switch Q301 = TI CSD16340Q3; rectifier D301 = Nexperia PNE20010ER (200 V) with RC snubber R313/C312; clamp diode D302 = Nexperia PMEG10020ELR | Datasheet-backed: RDS(on) rated at VGS 2.5 V (gate drive = VBAT); 100 V Schottky rejected after open-loop simulation showed rectifier ringing to breakdown | Engineering selection within the K-12 LM51551 flyback. T301 transformer remains a PLACEHOLDER (no verifiable part) |

## 7. Layout-only changes, Claude Code session of 31 Oct 2026

The owner's instruction for this session: complete the PCB layout fixes that need no new datasheet and no owner-level electrical decision, keep every electrical decision unchanged, and report anything that would need one. All entries below are **engineering choices within that instruction**, not owner decisions. No schematic, part, value, footprint or net change was made. Details and evidence: `docs/handover/LAYOUT_FIXES_2026-10-31.md`.

| Date | Decision | Rationale | Status |
| --- | --- | --- | --- |
| 31 Oct | Recoverable checkpoint: git tag `checkpoint/pre-layout-fixes-2026-10-31` on `976a17b` before any board edit | CLAUDE.md rule 6 | Done |
| 31 Oct | KiCad could not be run in the cloud session (only Ubuntu's KiCad 7 was installable; running the KiCad 10 container image was refused by the session's permission policy). Layout edits were made by script on the S-expression file and checked with a new pure-Python checker (`scripts/pcbcheck.py`) calibrated on the 10 Oct kicad-cli report | Owner asked for the layout work to proceed, and for validation to be reported as unverified if KiCad is unavailable | **KiCad ERC/DRC NOT run on the modified board.** Must be run (with zone refill) before any further use |
| 31 Oct | +48V_MOT routed R311.2 → J703.2 (F.Cu) and C702.1 → that route (B.Cu, one via), 0.4 mm, ≥ 0.75 mm to other nets (HV48 rule 0.6 mm). No DRU rule changed | Blocker report §2.2; layout only | Done, unverified in KiCad. U-17 (JST SH rating at 48 V) and FL-6/CF-6 (HV clearance rule) stay OPEN |
| 31 Oct | C305 (CSS) moved north of U301 (rotated 180°); FLY_SS routed pin 9 → via → B.Cu → via → C305.1 (two 0.5/0.3 mm vias); AGND pin 7 tied to the exposed pad; FLY_FB/FLY_RT/FLY_PGOOD escapes re-routed. A one-layer FLY_SS route was not possible without moving FLY_EN | SNVSB75E pin table (SS cap ground to AGND) and §10.5.1 ("connect the exposed pad to the AGND and PGND pins under the device") | Done, unverified in KiCad. FL-3 (AGND/PGND strategy) stays OPEN |
| 31 Oct | TP302 (FLY_PGOOD test point) moved from beside J703 onto the FLY_PGOOD trace next to U301/R302 | Probe PGOOD at its source; frees the J703 corridor | Done |
| 31 Oct | J503 (console header: GND, CON_MAIN_TX, CON_SUP_TX, CON_SUP_RX) moved from the top edge to the free area between the two MCUs (pin 1 at 133.5, 147.5 mm); CON_SUP_TX/RX and CON_MAIN_TX routed to it | Gives all three console nets short routes (the supervisor nets were 55–56 mm cross-board gaps) | Done. Header is no longer at a board edge; acceptable for a bench console cable, revisit with the enclosure |
| 31 Oct | R711/R712 NOT moved. R712 → U601 (ENC_B_S) was already routed; ENC_A_S routed from R711 alongside it instead | Moving the 100 Ω resistors next to U601 only transfers the 60 mm run to the ENC_A/ENC_B nets and would break a finished route | Done |
| 31 Oct | FLY_PGOOD → U501.28 (PA12) left unconnected | Pin 28 is enclosed by the pin 27/29 escapes inside the WBA55 fan-out that must be redone from the ST documents (U-05) | OPEN, route after the WBA re-layout |
| 31 Oct | Dead-end autorouter stubs removed (8 dangling vias, 1 dangling track and the stub tracks leading only to them) | Leftovers on nets that were unconnected anyway; no connection removed | Done |
| 31 Oct | B.SilkS disclaimer texts mirrored and centred (wording unchanged); edge-clipped references of J501 and J102 and the references of moved parts repositioned | Cosmetic DRC warnings | Done; D704 reference left in place (no clear spot). Silkscreen counts unverified |

## 8. Claude Code session of 1 Nov 2026 (layout completion, verification, review)

Engineering choices within the owner's 1 Nov instruction (route ENC_I, ENC_VCC, RS485_B and +3V3 at R302.2 where safe; review the critical blockers; find a legitimate KiCad environment; write the project report). **No owner decision was taken on the owner's behalf; no electrical or safety decision was made.**

| Date | Decision | Rationale | Status |
| --- | --- | --- | --- |
| 1 Nov | KiCad checks run on GitHub-hosted runners with the official `kicad/kicad:10.0.4-full` image (`.github/workflows/kicad-checks.yml`, read-only), not in the cloud sandbox | The sandbox refused to run the container locally (respected); CI on the owner's repository is the standard legitimate route. 10.0.3 has no image; 10.0.4 is the nearest | Done; reports archived in `validation/` with provenance |
| 1 Nov | ENC_VCC, ENC_I and the R302.2 +3V3 link routed; R714 (DNP RS-485 termination) moved to the bus end between U701 and J704, and its 20 mm RS485_A stub removed | Layout only; termination belongs at the bus end | Done; kicad-cli: 0 copper errors, 24 unconnected |
| 1 Nov | Python checker dangling test corrected (end point must lie in same-net copper) | kicad-cli run 1 exposed 3 dangling ends the 31 Oct checker missed | Done; the 31 Oct report carries a correction note |
| 1 Nov | Stale BOM files replaced by kicad-cli exports from CI | The old files dated from Stage 2 (pre design v2) | Done (133 references, 79 lines) |
| 1 Nov | Blocker recommendations written (`docs/handover/ENGINEERING_BLOCKER_REVIEW_2026-11-01.md`) | Owner request | **All PROPOSED; owner decisions listed there** |

## 9. Final engineering review, 1 Nov 2026

Review only. **No schematic, PCB, part or value change; no owner decision taken.** Output: `docs/handover/FINAL_ENGINEERING_REVIEW_2026-11-01.md`.

| Date | Item | Result | Status |
| --- | --- | --- | --- |
| 1 Nov | Audit of the engineering report (recomputed in `scripts/audit_calcs.py`) | 12 corrections (A1–A12). Most important: LM51551 OVP worst case 49.9–55.9 V (not 51.4–54.2 V); two diagram errors; simulation-agreement wording | Report, blocker review, FLYBACK_DESIGN, UNRESOLVED_ISSUES, A-21 corrected |
| 1 Nov | CSD16340Q3 footprint compared with TI SLPS247E §7.2 | Matches within 5 µm; TI pitch would remove the Q301 DRU exception | Proposal (owner approval) |
| 1 Nov | New issue U-38: R307 (0603, no MPN) working voltage at ≈ 47–55 V | Needs ≥ 75 V-rated part | OPEN |
| 1 Nov | Eight decision proposals (ST power/RF, transformer, independent OVP, SPI-gate runaway stop, J703, switch vs bleeder, HV clearance, battery/fuse/charge) | Written with evidence, calculations, pros/cons, schematic/PCB changes, risks | **All PROPOSED; owner decisions in §4.2 of the review** |
| 1 Nov | 24 unconnected items classified by trial routing (not committed) | 2 routable now (deferred), 21 blocked by datasheets (12 + 6 ST, 3 TI YBG), 1 by an owner decision | Documented |

## 10. Completion session, 1 Nov 2026

Engineering-level work under the owner's master execution prompt ("implement every technically justified change that does not require owner approval"). **No owner decision was taken.** Everything owner-dependent is on `docs/handover/OWNER_APPROVAL_SHEET.md`.

| Date | Item | Rationale / evidence | Status |
| --- | --- | --- | --- |
| 1 Nov | **C305 47 nF → 2.2 µF/10 V X7R** (same 0603 footprint), in `design.py`, `power_48v.kicad_sch` and `pump_v2.kicad_pcb` | SNVSB75E §9.3.10 requires the soft start to avoid current limit. 47 nF (4.7 ms) demands 1.54 A into 151 µF, so the converter would sit in hiccup and never reach 48 V. Shown by two independent models (`sim_flyback_cycle.py`, `sim_flyback_closedloop.py`); worst-case minimum 1.5 µF. A correction of a CALC value, not a change of architecture or part selection | Done, commit `a768755`; CI run 4 clean (ERC unchanged, DRC 0 copper, 0 parity) |
| 1 Nov | ENC_I_M and VBAT_SENSE routed (`layout_fixes_3.py`) | Classified "routable immediately" by the final review; short routes that can be redone with the U501 re-layout | Done; 24 → 22 unconnected (kicad-cli) |
| 1 Nov | Closed-loop behavioural switching model, cycle-by-cycle model, runaway timing model, detailed BOM generator | Phase C/F of the master prompt | Done; results in `validation/sim/`, `validation/logs/`, `docs/bom_full*` |
| 1 Nov | STM32WBA55 SMPS mode and LSE use recommended from ST's public reference firmware (`validation/logs/st_cubewba_evidence.md`) | st.com unreachable; ST's GitHub repositories reachable | Recommendation only (decision 12) |
| 1 Nov | New findings U-40 to U-44 (load-step hiccup, Q301 margin at current limit, unload overshoot vs 50.4 V, supervisor VBAT, PMD401 timeout bound) | Simulation and calculation | On the approval sheet (decisions 6, 8, 9, 14, 2) |
| 1 Nov | Report restructured to 36 sections; approval sheet, fabrication blockers, firmware review, file index, progress log | Phase G/H | Done |
