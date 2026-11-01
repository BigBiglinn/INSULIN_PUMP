> **1 Nov 2026 update.** The design passes ERC and DRC with 0 violations and is fully routed (Stage P6, `PCB_STAGES.md`). Nothing was built or measured.
>
> Closed since this register was written: U-04 selection (HPH6-0090L), U-05 (ECO1, DS14127), U-06 and U-23 design side (ECO1/ECO2), U-15 (PESD5V0S1BA), U-21 (routing), U-30, U-32. Q301 pinout confirmed against the AOS datasheet (`docs/datasheets/AONR34332C.pdf`): 1-3 S, 4 G, 5-8 D. The footprint is still the KiCad NexFET pattern, not checked against an AOS land drawing.
>
> **Still open, and not closable digitally:**
> - Q301 margin: simulated AONR34332C peak 25.8-28.9 V on a 30 V part with 3-5 nH loop inductance and 2-10 % leakage, about 29.9 V at the worst corner with the 1 V TVS heating estimate (`validation/sim/q301/RESULTS.md`). This supports the earlier 27.9-30.3 V estimate; margin is still not established. T301 leakage unpublished; clamp and snubber values provisional. At 10 % leakage and the 4.9 A limit the TVS takes about 3 W steadily, rating not checked.
> - PMD401 absolute maximum: OVP trip 50.5-53.9 V can exceed 50.4 V. Vendor question not sent.
> - LM51551 control loop not modelled; no thermal or signal-integrity simulation of the final copper.
> - Footprint checks: BQ25188 pitch inferred (U-12); connector orientation (U-17); J703 rating at 48 V (0.40 mm pad gap).
> - U-16 (no fab or stack-up, so RF impedance U-20 is estimated), U-14, U-18, U-24.
> - Parts: F101 no part (no 5 A fuse in the 2920 footprint found); R316, R317, C314 values TBD and unfitted.

# Unresolved issues: Rev B digital handover design

Updated 10 Oct 2026 (second session). Severity:

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

## Critical

| ID | Issue | Placeholder in design | Needed to close |
| --- | --- | --- | --- |
| U-04 | **Flyback transformer T301 not selected.** Power stage is dimensioned and simulated open-loop (`FLYBACK_DESIGN.md`), but there is no real transformer, so leakage-dependent clamp/snubber values and compensation are provisional | T301 = `XFMR_PLACEHOLDER_4P` (12 × 12 mm), with the specification in its Note field | Pick a transformer that meets FLYBACK_DESIGN.md §4, replace the footprint, re-tune R306/C308/R313/C312, verify the loop (TI model or bench) |
| U-05 | **STM32WBA55 supply/RF wiring not from the datasheet.** SMPS inductor, VDD11, VDDHPA/VDDANA/VDDRF/VDDRFPA, decoupling, HSE crystal and load, RF match. ST datasheets could not be downloaded (st.com blocked from this machine) and were not supplied in this session | L501, C509–C515, R510–R513 (DNP), L502, Y501. **These are the 6 ERC errors** | ST STM32WBA55CG datasheet plus the WBA hardware/RF design guide; same for the STM32C031C6 decoupling |
| U-03 | Speed cap is enforced only in firmware (item 2, S-06). The supervisor now counts the encoder (S-07) | Firmware | Supervisor rate check, then FT-02 |
| U-06 | K-12 "switched output" and the E-11 bleeder are not designed | Q302/Q303/R309/R310/R312 DNP; R311 0 R bypass | High-side switch ≥ 100 V class; bleeder value |
| U-23 | 60 V fault ceiling relies on LM51551 OVP through the FB divider (51.4–54.2 V). An open R307/R308 is an uncovered single fault, and 54.2 V is above the PMD401's 50.4 V maximum | — | Secondary OVP clamp or crowbar, or a redundant divider; decision |

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
| U-21 | **Routing incomplete / not reviewed.** See `validation/logs/unrouted_nets.txt` for the current count. The flyback loop is placed compactly but routed by the autorouter around a placeholder transformer, so it is not final | Hand-route and review in pcbnew after U-04/U-05 |
| U-24 | Input current at full PMD401 speed is about 2.0–2.3 A at 3.0 V (simulation), at or above the E-05 2.1 A budget | Measure PMD401 current at dosing speed (MT-07); re-check the battery-path ratings |
| U-22 | Freerouting ran with default telemetry during the first session (disabled afterwards) | Note only |

## Minor

| ID | Issue |
| --- | --- |
| U-30 | ERC `lib_symbol_mismatch` on U701 (MAX3485) is cosmetic. Fix with *Update Symbols from Library* in Eeschema |
| U-31 | Schematic drawn label-style (every pin carries a net label) |
| U-32 | Silkscreen overlaps; unmirrored bottom-side disclaimer text |
| U-34 | Datasheets still missing: ST parts, LL06, MAX3485, connectors, Molicel cell, transformer |
