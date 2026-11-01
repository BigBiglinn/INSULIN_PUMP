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
| 9 | **Q301 voltage margin** (new; fault and current-limit operation) | Re-tune the RCD clamp (R306/C308) with the real T301 for V<sub>DS</sub> ≤ 20 V **at current limit**, or move to a 30–40 V NexFET with Q<sub>g</sub> ≤ 6.5 nC | V<sub>DS</sub> 18.4–18.7 V in normal operation (including the 20 ms ramp), but 22–24 V on 100 mA load steps and about 25.7 V (model breakdown) at current limit with V<sub>out</sub> ≥ 48 V, against 25 V V<sub>DS</sub> [DS]; E<sub>AS</sub> 80 mJ single pulse [DS] | Part or value change after T301 |
| 10 | **Q301 footprint** | Move the four pads to TI's exact 0.65 mm pitch (SLPS247E §7.2) | Present footprint matches within 5 µm; removes a 0.127 mm DRU exception | Footprint edit; re-route Q301 pins |
| 11 | **R313 snubber resistor** | ≥ 0.5 W (2010/2512), ≥ 200 V | 0.14–0.17 W [SIM]; sees about 100 V peak | Footprint change |

## C. Main MCU, battery and project decisions

| # | Decision | Recommended option | Evidence | Consequence |
| --- | --- | --- | --- | --- |
| 12 | **ST documents** (U-05) | Provide DS14127 (STM32WBA55 datasheet), RM0493, AN5948, AN6373 and the MB1803 (NUCLEO-WBA55CG) schematic, or allow st.com in the session network policy | Without them, 12 + 6 unconnected items and 6 ERC errors cannot be closed | Unblocks the WBA55 power/RF/crystal design and fan-out |
| 12a | SMPS or LDO core supply | **SMPS** (ST's own choice on NUCLEO-WBA55CG) | `RCC.SupplySource=PWR_SMPS_SUPPLY` [REF] | Inductor value from AN6373 |
| 12b | Antenna | Keep U.FL to an external 2.4 GHz antenna for the bench | No RF data in the repo | Matching network values from AN5948 |
| 12c | LSE crystal | **Fit** Y502 (32.768 kHz), now DNP | ST reference uses LSE for the RTC and radio sleep timer [REF] | DNP → fitted; load caps from the datasheet |
| 13 | **Battery subsystem** (U-18) | Molicel P28A protected 1S pack, **5 A slow-blow fuse**, **0.5 A charge current** with T<sub>REG</sub> 80 °C, XT30 confirmed, E-10 adopted | Charger loss 1.0 W at 0.5 A versus 2.0 W at 1 A [CALC]; cell data [WEB-2ND] | Fuse MPN, firmware ICHG setting |
| 14 | **Supervisor battery monitoring** (new, A2) | Connect a spare STM32C031 ADC pin to VBAT_SENSE (shared 1 M/1 M divider) so the supervisor can enforce the low-voltage stop independently | At present only the main MCU reads VBAT; the supervisor cannot | 1 net; pin confirmed in CubeMX |
| 15 | **Fab house and stack-up** (U-16, U-20) | Choose before RF and fine-pitch routing | — | DRC rules and impedance |
| 16 | **BQ25188 YBG land pattern** (U-12) | Provide TI's YBG package drawing (PDF in the repo lacks it) | — | Unblocks 3 unconnected items |
| 17 | **Remaining PROPOSED requirements** (OPEN item 15) | Accept, change or strike each | — | Requirements frozen |

## D. Approval record

| # | Approve / change / reject | Signature | Date |
| --- | --- | --- | --- |
| 1–17 | | | |

## Verification after approval (for the successor engineer)

1. Edit `scripts/design.py`, then apply the same edits to the schematic and PCB (or regenerate with the KiCad libraries installed). Commit before running generators.
2. Push to the branch: `.github/workflows/kicad-checks.yml` runs ERC, DRC with parity and the BOM export. Archive the reports.
3. Re-run `scripts/sim_flyback_cycle.py`, `scripts/sim_flyback_closedloop.py` (with the real T301 and preferably the TI model), `scripts/runaway_timing.py` and `scripts/audit_calcs.py`.
4. Regenerate `docs/bom_full.csv` with `scripts/gen_bom_full.py`.
