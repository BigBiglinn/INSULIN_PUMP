# Owner approval sheet: Rev B decisions that block fabrication

Consolidated 1 Nov 2026 (completion session). Supersedes the decision lists in `FINAL_ENGINEERING_REVIEW_2026-11-01.md` §4.2 and `PROJECT_ENGINEERING_REPORT.md` §31 where they differ; the detailed evidence for decisions 1–8 is in Part 2 of the final review and is not repeated here.

**How to use this sheet.** Each line has a recommended option. Mark **Approve**, **Approve with change** or **Reject**, sign and date it, and commit it. The successor engineer then implements the approved changes, re-runs the checks listed under "Verification after approval", and records the result in `decisions/DECISION_LOG.md`. Nothing on this sheet has been implemented in the design yet. The only engineering-level change made in this session is C305, in §B.

Evidence labels: [DS] manufacturer datasheet in `docs/datasheets/`; [REF] ST reference firmware configuration (`validation/logs/st_cubewba_evidence.md`); [CALC] calculation (script named); [SIM] simulation of a model, not a measurement; [ASSUMED]; [NV] not verified; [WEB-2ND] secondary web source.

The device is a water/saline bench prototype only. It must never be connected to a person or an animal.

## A. Safety-critical decisions

| # | Decision | Recommended option | Key numbers | If approved | If not approved |
| --- | --- | --- | --- | --- | --- |
| 1 | **Independent 48 V over-voltage protection** (U-23) | A comparator with an internal reference on its **own** divider from +48V_RAW, with an open-drain output wired to FLY_EN. The supervisor latches it via the veto. A supervisor ADC monitor is a second layer. Trip about **52.5 V** with a 0.1 % divider and a ±1 % reference (band 51.9–53.1 V) | Single fault R307 open, no load: the rail passes 50.4 V 112 ms after the fault, 55.9 V at 336 ms and 100 V at 2.9 s [SIM cycle model]. The LM51551 hiccup only slows it. With the proposed trip, the rail latches off at the first crossing; overshoot after the trip is 0.07 V [SIM switching model] | New parts chosen from their datasheets; about 4 nets; route near Q401/U601; re-run CI | **Fabrication blocked.** The open-FB single fault is uncovered (S-04) |
| 2 | **Motor runaway stop** (S-06, U-03) | OR gate on PMD_SS with SUP_SPI_BLOCK pulled up (blocked by default), plus a two-tier TIM3 rate check. On a trip, assert the SPI block **and** the 48 V veto | Detection ≤ 2 ms worst case. At 15 mm/s: 0.30 U with a 10 ms PMD401 timeout, 0.55 U with 20 ms. **S-06 is met only if the PMD401 SPI timeout is ≤ 18 ms** [CALC `runaway_timing.py`] | New gate, 1 net, PMD_SS re-route. Ask PiezoMotor for the guaranteed timeout and measure it (SG-06) | **Fabrication blocked.** The firmware speed cap is the only protection (R1) |
| 3 | **Output switch versus bleeder** (U-06, E-11) | Option A: delete the Q302/Q303/R309/R310 placeholders; fit R312 = **10 kΩ, ≥ 0.5 W, ≥ 100 V working voltage** | 4.4 s to < 5 V from 55.9 V worst case (C<sub>max</sub> 180.8 µF); 0.31 W at 55.9 V [CALC `audit_calcs.py`]. With the bleeder fitted, the open-FB rail sags instead of rising [SIM cycle model] | SW48_GATE unconnected item disappears (22 → 21); E-11 met by calculation | E-11 unmet; one unconnected item stays |
| 4 | **J703 connector rating** (U-37) | Board side: a connector with a manufacturer rating **≥ 100 V DC**; an SH-housing cable to the PMD401 | Rail 45.6–50.4 V normal, up to 55.9 V at the LM51551 OVP worst case. JST SH listing 50 V [WEB-2ND] | Footprint change at J703; re-route +48V_MOT; removes one DRU exception | **Fabrication blocked.** Connector possibly operated above its rating |
| 5 | **HV clearance** (P-03, CF-6) | Keep HV48 at 0.6 mm on all layers; sign off against IPC-2221C (document not in repo) | ≤ 56 V worst case | Rule frozen | Rule stays provisional |
| 6 | **Feedback divider precision** (new, from E-03 and the PMD401 50.4 V limit) | R307/R308 **0.1 %** with R307 rated **≥ 75 V** working voltage (U-38) | 1 % parts: setpoint 46.6–49.4 V. Unload overshoot +1.3 V [SIM] → up to 50.7 V > 50.4 V. With 0.1 %: upper corner 48.6 V + 1.3 V = 49.9 V [CALC `audit_calcs.py`] | MPN fields set; no layout change | PMD401 50.4 V maximum can be exceeded transiently at the tolerance corner |

## B. Power-stage decisions (48 V flyback)

| # | Decision | Recommended option | Key numbers | Consequence |
| --- | --- | --- | --- | --- |
| 7 | **Transformer T301** (U-04) | Custom winding to the `FLYBACK_DESIGN.md` specification, with **I<sub>sat</sub> raised to ≥ 6.5 A** (see 8); in parallel, check Coilcraft Hexa-Path parts against it | Primary RMS 2.30 A, secondary RMS 0.21 A; n = 5, L<sub>p</sub> 7.3 µH (5–10 µH), leakage ≤ 2 % [CALC] | Footprint, clamp/snubber re-tune, loop re-simulation, layout loop compaction |
| 8 | **Current-limit headroom** (new: load steps) | **Firmware requirement FW-R1:** ramp every PMD401 speed change over ≥ 20 ms. Optional extra margin: R305 22 → 18 mΩ (limit 5.2–5.9 A) together with T301 I<sub>sat</sub> ≥ 6.5 A | A 6 → 100 mA **step** trips the LM51551 hiccup about 3 ms after the step at Vin 3.0 V and 3.4 V (none at 4.2 V); the 48 V rail would then stop for 110 ms. The same demand as a **20 ms ramp** at 3.0 V: no hiccup, dip 0.19 V, peak 3.39 A, V<sub>DS</sub> 18.4 V, about 83 % efficiency [SIM switching model + hiccup rule] | FW-R1 is firmware only; FW-R2 (motor parked until PGOOD) also needed, because startup into full load at 3.0 V trips hiccup [SIM]. The R305 option is a value change (2512 footprint kept) plus a T301 spec change |
| 9 | **Q301 voltage rating — FABRICATION BLOCKER** (U-41) | **Replace Q301 with a ≥ 40 V N-MOSFET**, either one whose R<sub>DS(on)</sub> is specified at V<sub>GS</sub> ≤ 2.5 V, or any 40–60 V logic-level part combined with an auxiliary T301 winding feeding BIAS so that VCC is regulated (6.75 V typical [DS]). Also add a gate resistor footprint (0 Ω default, 4.7–10 Ω fitted if needed), place D302/C308 tight at the drain, and fit the interim clamp (done) | Investigation 1 Nov (`validation/sim/q301_stress/results.md`, 33 cases): the 25.7 V was **physical, not numerical** (26.1–26.2 V with the model breakdown removed and a 4× finer step). It occurs only in current-limit operation. Worst corner (V<sub>in</sub> 4.2 V, rail 55.9 V, V<sub>CLTH</sub> 107 mV, 3 % leakage): **31.4 V** with the 10 Oct clamp; **22.1 V** with the re-tuned clamp R306 220 Ω / C308 470 nF on an ideal layout; but **28.3 V with 2 nH and 33 V with 5 nH** of drain-loop inductance. A 10 Ω gate resistor + RC snubber reduce 5 nH to 23.9 V (96 %). Normal operation 14.7–15.3 V with the new clamp. A 25 V part therefore cannot be shown to stay below its 25 V abs max [DS] under fault current limit | New part; footprint may change. CSD16340Q3 and the in-repo CSD17575Q3 both use TI's "Q3" package (each datasheet §7.1/7.2), CSD17578Q3A uses "Q3A"; the land patterns must be compared drawing to drawing before reuse, and other makers' packages differ. In-repo 30 V options CSD17575Q3/CSD17578Q3A specify R<sub>DS(on)</sub> only at 4.5 V with V<sub>GS(th)</sub> up to 1.8–1.9 V [DS], so they are **not** valid at a 3.0 V gate drive without the auxiliary-winding change |
| 10 | **Q301 footprint** | Move the four pads to TI's exact 0.65 mm pitch (SLPS247E §7.2) | Present footprint matches within 5 µm; removes a 0.127 mm DRU exception | Footprint edit; re-route Q301 pins |
| 11 | **R313 snubber resistor** | ≥ 0.5 W (2010/2512), ≥ 200 V | 0.14–0.17 W [SIM]; sees about 100 V peak | Footprint change |

## C. Main MCU, battery and project decisions

| # | Decision | Recommended option | Evidence | Consequence |
| --- | --- | --- | --- | --- |
| 12 | **ST documents** (U-05) | Provide DS14127 (STM32WBA55 datasheet), RM0493, AN5948, AN6373 and the MB1803 (NUCLEO-WBA55CG) schematic, or allow st.com in the session network policy | Without them, 12 + 6 unconnected items and 6 ERC errors cannot be closed | Unblocks the WBA55 power/RF/crystal design and fan-out |
| 12a | SMPS or LDO core supply | **SMPS** (ST's own choice on NUCLEO-WBA55CG) | `RCC.SupplySource=PWR_SMPS_SUPPLY` [REF] | Inductor value from AN6373 |
| 12b | Antenna | Keep U.FL to an external 2.4 GHz antenna for the bench | No RF data in the repo | Matching network values from AN5948 |
| 12c | LSE crystal | **Fit** Y502 (32.768 kHz), now DNP | ST reference uses LSE for the RTC and radio sleep timer [REF] | DNP → fitted; load caps from the datasheet |
| 13 | **Battery subsystem** (U-18) | Molicel P28A protected 1S pack, **5 A slow-blow fuse**, **0.5 A charge current** (the VBAT_FUSED charge track routed 1 Nov is 0.2 mm: ≈ 4 °C rise at 0.5 A, ≈ 20 °C at 1 A by the IPC-2221 equation, so I<sub>CHG</sub> ≤ 0.5 A unless the track is widened) with T<sub>REG</sub> 80 °C, XT30 confirmed, E-10 adopted | Charger loss 1.0 W at 0.5 A versus 2.0 W at 1 A [CALC]; cell data [WEB-2ND] | Fuse MPN, firmware ICHG setting |
| 14 | **Supervisor battery monitoring** (new, A2) | Connect a spare STM32C031 ADC pin to VBAT_SENSE (shared 1 M/1 M divider) so the supervisor can enforce the low-voltage stop independently | At present only the main MCU reads VBAT; the supervisor cannot | 1 net; pin confirmed in CubeMX |
| 15 | **Fab house and stack-up** (U-16, U-20) | Choose before RF and fine-pitch routing | — | DRC rules and impedance |
| 16 | ~~BQ25188 YBG land pattern~~ **CLOSED 1 Nov** (U-12) | The drawing **is** in the repo PDF (SLUSFJ3 §13.1, vector graphics; read by rendering pp. 50–52). Footprint corrected to it: pads 0.20 → 0.23 mm, NSMD mask +0.05 mm, 0.25 mm square paste; ball map checked against Table 5-1 | [DS] | U101 escapes routed (CHG_INT_N, I2C_SDA, I2C_SCL re-routed, VBAT_FUSED) |
| 17 | **Remaining PROPOSED requirements** (OPEN item 15) | Accept, change or strike each | — | Requirements frozen |
| 19 | **CS-pin RC filter on U301** (new, U-45) | Add RF 100 Ω between FLY_CS (R305/Q301 source) and U301 pin 5, and CF 470 pF from pin 5 to GND, as TI recommends against the leading-edge spike (SNVSB75E §9.3.7: RF 10–200 Ω, CF 100 pF–2 nF; 3·RF·CF = 141 ns < (1−D)/f<sub>SW</sub> = 0.77 µs; 2·RF·CF = 94 ns < t<sub>ON(min)</sub> 140 ns) | Without it, the turn-on spike counts as current limit and trips the 64-cycle hiccup on **every** full-load start at V<sub>CLTH</sub> 93 mV, for C305 = 2.2, 3.3 and 4.7 µF. With it: 2.2 µF nominal passes; the tolerance corners 2.4 µF-eq and 3.4 µF-eq pass (5.7 % margin at 3.4 µF-eq); 3.0 V/100 mA steps still need FW-R1 [SIM] | 2 parts (0603), 1 new net, local re-route at U301 pin 5. Connectivity change → approval |

## E. Closure review (final completion pass, 1 Nov 2026)

Which decisions the available evidence now closes. **None of the safety-critical decisions can be closed without the owner**; the evidence for each is complete enough to decide.

| # | Can it be closed now? | Evidence available | What is still missing |
| --- | --- | --- | --- |
| 1 Independent OVP | No: owner + part datasheet | Need shown by simulation (ratchet to 100 V in 2.9 s at no load); latch behaviour simulated | Comparator/reference datasheet; approval |
| 2 Runaway stop | No: owner + PiezoMotor data | Timing calculated; S-06 bound: timeout ≤ 18 ms | PMD401 guaranteed timeout; gate part datasheet; approval |
| 3 Switch vs bleeder | Ready to decide | Bleeder calculation; bleeder effect in open-FB fault simulated | Owner choice (E-11 status) |
| 4 J703 | No | Distributor listing only [WEB-2ND] | JST datasheet or ≥ 100 V part datasheet |
| 5 HV clearance | No | 0.6 mm used on all layers; worst rail now bounded at 55.9 V (53.1 V with decision 1) | IPC-2221C document for sign-off |
| 6 FB divider 0.1 %, R307 ≥ 75 V | Ready to decide | Tolerance stack and overshoot simulated | Resistor datasheet (no MPN chosen) |
| 7 Transformer | No | Specification complete | Part or custom winding; leakage measurement |
| 8 Load-step headroom | **Mitigation defined** | 20 ms ramp simulated clean | Owner adopts FW-R1 (firmware) |
| 9 Q301 rating | **Partly done**: clamp re-tuned (engineering change, see `decisions/DECISION_LOG.md` §11) | 33-case stress sweep | ≥ 40 V part choice (datasheet), possibly auxiliary winding: **fabrication blocker** |
| 10 Q301 footprint | Superseded if 9 changes the part | — | — |
| 11 R313 ≥ 0.5 W, ≥ 200 V | Ready to decide | Simulated dissipation 0.14–0.17 W normal | Resistor datasheet; footprint 1206 → 2010/2512 |
| 12 ST documents | No | ST reference firmware: SMPS, HSE, LSE [REF] | DS14127, AN5948, AN6373, MB1803 |
| 13 Battery, fuse, charge current | No | Calculations | Cell/fuse datasheets; approval |
| 14 Supervisor VBAT | Ready to decide | Gap identified | Approval; pin check in CubeMX |
| 15, 17 | No | — | Owner |
| 16 BQ25188 land pattern | **Closed** | TI YBG0008-C01 drawing in the repo PDF | — |
| 19 CS RC filter | Ready to decide | 9 worst-case soft-start/step runs | Approval (connectivity change) |
| 18 C305 value | **Done (engineering, CALC value): 4.7 µF/10 V X5R ±20 %** | Worst-case end-of-ramp runs (§27.2) | Full-load start robustness also needs decision 19; with the motor parked during start-up (FW-R2), every value passes, including the 1.6 µF-eq corner |


### Q301 replacement: electrical requirements (decision 9)

Derived from the schematic and `validation/sim/q301_stress/results.md`. A part qualifies only on the strength of its **manufacturer datasheet**. Threshold voltage is not evidence of drive, and R<sub>DS(on)</sub> quoted only at 4.5 V or 10 V does not count.

| Parameter | Requirement | Basis |
| --- | --- | --- |
| V<sub>DS</sub> (abs max) | **≥ 40 V**, with the drain loop verified ≤ 5 nH (33.8 V worst simulated = 84 %); **≥ 60 V** if the loop cannot be verified (39.5 V at 10 nH = 66 %) | Worst corner: V<sub>in</sub> 4.2 V, rail 55.9 V, V<sub>CLTH</sub> 107 mV, 3 % leakage, current limit |
| R<sub>DS(on)</sub> | **Specified (max) at V<sub>GS</sub> = 2.5 V** in the electrical table; ≤ 15 mΩ at 25 °C. Gate drive is VBAT = 3.0–4.2 V (BIAS = VCC = VBAT, SNVSB75E §9.3.2), minus driver drop | Primary RMS 2.30 A [CALC] → ≤ 0.1 W conduction loss at 125 °C |
| Q<sub>G</sub> | Q<sub>G</sub> at 3–4.5 V ≤ ≈ 15 nC (hard limit Q<sub>G</sub>·f<sub>SW</sub> < 35 mA → 117 nC [DS SNVSB75E Eq. 18]) | Switching loss and driver current |
| I<sub>D</sub> | Pulsed ≥ 10 A; continuous ≥ 5 A at T<sub>A</sub> 70 °C | I<sub>pk</sub> up to 5.9 A at current limit [SIM] |
| Avalanche | E<sub>AS</sub> rated (single pulse) | Fault margin |
| Package | SON 3.3 × 3.3 class with an exposed drain pad; the land pattern is checked against the manufacturer's drawing before reuse of the Q301 footprint | Layout |
| Availability | Two or more distributors listed with stock, or an owner-confirmed source | Not checkable from the design environment |

**Alternative, if no part meets the 2.5 V requirement:** add an auxiliary T301 winding feeding BIAS through a diode, so that VCC regulates at 6.5–7 V [DS SNVSB75E Table, V<sub>VCC-REG</sub>]. A 40–60 V part specified at V<sub>GS</sub> = 4.5 V then qualifies. This is a transformer and schematic change (decision 7).

**Evidence still missing:** no ≥ 40 V MOSFET datasheet is in the repository, and no manufacturer or distributor site was reachable (st.com, ti.com, nexperia, vishay, onsemi, infineon, diodes, aosmd, octopart, mouser and digikey all failed, 1 Nov 2026). **Q301 stays unresolved.**

## D. Approval record

| # | Approve / change / reject | Signature | Date |
| --- | --- | --- | --- |
| 1–17 | | | |

## Verification after approval (for the successor engineer)

1. Edit `scripts/design.py`, then apply the same edits to the schematic and PCB (or regenerate with the KiCad libraries installed). Commit before running generators.
2. Push to the branch: `.github/workflows/kicad-checks.yml` runs ERC, DRC with parity and the BOM export. Archive the reports.
3. Re-run `scripts/sim_flyback_cycle.py`, `scripts/sim_flyback_closedloop.py` (with the real T301 and preferably the TI model), `scripts/runaway_timing.py` and `scripts/audit_calcs.py`.
4. Regenerate `docs/bom_full.csv` with `scripts/gen_bom_full.py`.
