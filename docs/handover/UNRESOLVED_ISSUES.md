# Unresolved issues: Rev B digital handover design

Updated 10 Oct 2026 (second session); layout items updated 31 Oct and 1 Nov 2026; completion-session items U-39 to U-44 added 1 Nov (decisions in `OWNER_APPROVAL_SHEET.md`) (`LAYOUT_FIXES_2026-10-31.md`, `LAYOUT_FIXES_2026-11-01.md`). Recommendations for every critical item: `ENGINEERING_BLOCKER_REVIEW_2026-11-01.md`; detailed decision proposals and the owner-decision list: `FINAL_ENGINEERING_REVIEW_2026-11-01.md`. Severity:

- **Critical**: blocks any build, or leaves a safety function without evidence.
- **Major**: the board will not work as intended until it is resolved.
- **Minor**: cosmetic, documentation or optimisation.

Item numbers in brackets (for example "item 4", "B.16") refer to `requirements/OPEN_QUESTIONS.md`.

## Closed in the second session

| ID | Was | Resolution |
| --- | --- | --- |
| U-01 | Supervisor veto gate default undecided | Owner: R403 pull-up fitted, R404 removed (veto on by default) |
| U-02 | PMD401 AEN fail-safe | Owner: open-drain Q402 BSS138 plus R405 gate pull-up. Parked by default, and the PMD401's own 22 k pull-up gives the run level. Still needs SG-05 on hardware |
| U-07 | No battery-voltage sensing | R107/R108 1 M/1 M plus C104 100 nF into PB9 (ADC4_IN10), CALC. ADC leakage still to be checked in the ST datasheet (see U-05) |
| U-13 | BQ25188 TS/MR handling and defaults | R101 = 10 k as specified in SLUSFJ3 for the "TS not used" case. Defaults: VBATREG 4.20 V, ICHG 10 mA, watchdog on. Firmware must set the charge current |
| (part of U-10) | Pin maps unverified | All 41 assigned functions checked against the STM32CubeMX 6.18.1 database by `scripts/verify_pinmap.py`: 0 failures. PF2-NRST, PH3-BOOT0 and PA14-BOOT0 confirmed |

## Closed on 31 Oct and 1 Nov 2026

| ID | Was | Resolution |
| --- | --- | --- |
| U-39 | **Soft-start lock-out (found 1 Nov by simulation).** C305 47 nF gave a 4.7 ms soft start that needs 1.54 A to charge 151 µF; the LM51551 would run at current limit, arm its 64-cycle hiccup and never reach 48 V | C305 = 2.2 µF (220 ms; worst-case minimum 1.5 µF), commit `a768755`. CALC + SIM (`sim_flyback_cycle.py`, `sim_flyback_closedloop.py`); bench test PW-SS still needed |
| (U-21 part) | ENC_I_M and VBAT_SENSE unconnected | Routed 1 Nov (`layout_fixes_3.py`); kicad-cli CI run 4: 22 unconnected |

## Critical

| ID | Issue | Placeholder in design | Needed to close |
| --- | --- | --- | --- |
| U-04 | **Flyback transformer T301 not selected.** Power stage is dimensioned and simulated open-loop (`FLYBACK_DESIGN.md`), but there is no real transformer, so leakage-dependent clamp/snubber values and compensation are provisional | T301 = `XFMR_PLACEHOLDER_4P` (12 × 12 mm), with the specification in its Note field | Pick a transformer that meets FLYBACK_DESIGN.md §4, replace the footprint, re-tune R306/C308/R313/C312, verify the loop (TI model or bench) |
| U-05 | **STM32WBA55 supply/RF wiring not from the datasheet.** SMPS inductor, VDD11, VDDHPA/VDDANA/VDDRF/VDDRFPA, decoupling, HSE crystal and load, RF match. ST datasheets could not be downloaded (st.com blocked from this machine) and were not supplied in this session | L501, C509–C515, R510–R513 (DNP), L502, Y501. **These are the 6 ERC errors** | ST STM32WBA55CG datasheet plus the WBA hardware/RF design guide; same for the STM32C031C6 decoupling |
| U-03 | Speed cap is enforced only in firmware (item 2, S-06). The supervisor now counts the encoder (S-07) | Firmware | Supervisor rate check, then FT-02 |
| U-06 | K-12 "switched output" and the E-11 bleeder are not designed | Q302/Q303/R309/R310/R312 DNP; R311 0 R bypass | High-side switch ≥ 100 V class; bleeder value |
| U-37 | **J703 (JST SM02B-SRSS-TB) is reportedly rated 50 V AC/DC** (distributor listings; the JST datasheet could not be read). The rail is 48 V nominal, up to 50.4 V normally and up to 55.9 V at the LM51551 OVP (worst case) | — | Confirm in the JST datasheet; if 50 V, use a ≥ 100 V board connector with an SH cable to the PMD401 (review §7) |
| U-38 | **R307 (470 kΩ, FB divider top) working voltage.** 0603 footprint, no MPN; sees ≈ 47 V (up to ≈ 55 V). An open R307 is the U-23 single fault | — | Choose a part with a datasheet working voltage ≥ 75 V (or a 1206); same rule for any new 48 V divider (final review §1.3) |
| U-23 | 60 V fault ceiling relies on LM51551 OVP through the FB divider (52.8 V typical, 49.9–55.9 V worst case). An open R307 (or shorted R308) is an uncovered single fault. Simulation 1 Nov: hiccup only slows the rise; at no load the rail passes 55.9 V after 336 ms and 100 V after 2.9 s; with the proposed independent OVP it latches at ≈ 52.5 V [SIM] | — | Independent OVP (approval sheet decision 1) |

## New on 1 Nov (completion session; all on `OWNER_APPROVAL_SHEET.md`)

| ID | Severity | Issue | Needed to close |
| --- | --- | --- | --- |
| U-40 | Major | A 6 → 100 mA load **step** trips the LM51551 hiccup about 3 ms after the step at Vin 3.0 V and 3.4 V (48 V off for 110 ms); none at 4.2 V. A 20 ms ramp does not trip it [SIM] | Firmware FW-R1 (≥ 20 ms speed ramp); optional R305 18 mΩ + T301 I<sub>sat</sub> ≥ 6.5 A (decision 8); bench PW-LS |
| U-41 | Major | Q301 (25 V) sees about 25.7 V during current-limit operation at V<sub>out</sub> ≥ 48 V and 22–24 V on load steps [SIM]; 18.4–18.7 V in normal operation | Clamp re-tune with the real T301, or a 30–40 V FET (decision 9) |
| U-42 | Major | Unload overshoot +1.3 V [SIM] on top of the 1 % setpoint corner 49.4 V gives 50.7 V, above the PMD401's 50.4 V | 0.1 % R307/R308 (decision 6) |
| U-43 | Major | Supervisor has no battery-voltage input (A2 review) | Spare STM32C031 ADC on VBAT_SENSE (decision 14) |
| U-44 | Critical (part of U-03) | S-06 with the proposed SPI gate holds only if the PMD401 SPI timeout is ≤ 18 ms at 15 mm/s (2 ms worst-case detection) [CALC `runaway_timing.py`]; the manual says "about 10 ms" | Ask PiezoMotor; measure (SG-06b) |

## Major

| ID | Issue | Needed to close |
| --- | --- | --- |
| U-10 | Electrical pin properties not checked: 5 V tolerance of the pins facing the PMD401 and encoder, drive current, ADC leakage, reset-state behaviour | ST datasheets |
| U-11 | WBA55 TIM2 width (32-bit?) unconfirmed (CF-21/FW-08) | RM0493 |
| U-12 | Footprints still to be checked against drawings: BQ25188 YBG (pitch inferred 0.4 mm), CSD16340Q3 DQG (KiCad TI NexFET pattern; source-to-gate pad gap 0.14 mm needs the scoped 0.127 mm DRC rule) | TI drawings |
| U-14 | Encoder supply voltage and cable pinout unverified (item 12) | LL06 datasheet, delivered cable |
| U-15 | TVS parts (D701–D709) not chosen | Part selection after IF-02 |
| U-16 | No fab chosen; rules are generic. Two scoped DRC exceptions exist (J703 vendor connector; Q301 pad pitch) | Fab rule file and stack-up |
| U-17 | Connector orientations derived heuristically; JST SH rating for the 48 V lead not confirmed | Connector drawings |
| U-18 | Battery connector, cell, fuse part number, master switch, charge current not decided (B.19, B.20) | Owner or successor |
| U-19 | Thermal check: R306 ≈ 0.4 W, R313 ≈ 0.17 W, R305, Q301, D301 | After U-04 |
| U-20 | RF trace not impedance-controlled | Stack-up, ST reference |
| U-21 | **Routing incomplete / not reviewed.** 1 Nov (CI run 4, `a768755`), kicad-cli: **22 unconnected** (12 ST placeholders, 1 DNP switch, 3 at the BQ25188 WCSP, 6 boxed in by the U501 fan-out). Every remaining genuine item is blocked by U-05 or U-12, not by routing effort. The flyback loop is still autorouted around a placeholder transformer, so it is not final | Hand-route and review in pcbnew after U-04/U-05/U-12; the CI workflow re-checks every push |
| U-24 | Input current at full PMD401 speed is about 2.0–2.3 A at 3.0 V (simulation), at or above the E-05 2.1 A budget | Measure PMD401 current at dosing speed (MT-07); re-check the battery-path ratings |
| U-22 | Freerouting ran with default telemetry during the first session (disabled afterwards) | Note only |

## Minor

| ID | Issue |
| --- | --- |
| U-30 | ERC `lib_symbol_mismatch` on U701 (MAX3485) is cosmetic. Fix with *Update Symbols from Library* in Eeschema |
| U-31 | Schematic drawn label-style (every pin carries a net label) |
| U-32 | Silkscreen overlaps. The bottom-side disclaimer texts were mirrored on 31 Oct; J501/J102 edge references moved; D704 reference still at the edge. Counts unverified |
| U-34 | Datasheets still missing: ST parts, LL06, MAX3485, connectors, Molicel cell, transformer |
