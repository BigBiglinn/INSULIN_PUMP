# DESIGN_REQUIREMENTS.md

Source: "Piezo Insulin Pump — Design Requirements, Parts and Verification Report" (10 Oct 2026), plus the owner's stated requirements recorded in the project. Requirement IDs are the ones used in that report. Do not renumber them.

Status column, exactly as in the source report:

- **Decided** = already in the project documents or the order. Treat as DECIDED.
- **Proposed** = new in the 10 Oct report, written by Claude from standard practice or from a gap found while writing. **Needs the owner's sign-off. Not yet a requirement.**

"Checked by" refers to check IDs in `VALIDATION_PLAN.md`.

## 1. Owner-level requirements (DECIDED)

| # | Requirement | Stated |
| --- | --- | --- |
| U-1 | Smaller device with a smaller motor than v1 | 21 Sep 2026 |
| U-2 | Everything on STM32, not ESP32 | 21 Sep 2026 |
| U-3 | More professional, close to industry grade | 21 Sep 2026 |
| U-4 | End goal is a small working prototype that just works properly. Correct dosing defines success. Never tested on humans | 21 Sep 2026 |
| U-5 | Whole project (ordering, assembly, everything) in 30 days | 21 Sep 2026 |
| U-6 | Two stages: Rev A bench validation, then Rev B PCB. No skipping straight to PCB | Sep 2026 |
| U-7 | Electronics: 3.7 V battery → high-voltage boost → piezo motor driver → piezo motor; the same 3.7 V also powers the STM32, which controls the driver | 25 Sep 2026 |
| U-8 | Piezo motor driving a positive-displacement syringe. No single-PZT + valve (diaphragm) pump | 27 Sep 2026 |
| U-9 | The project must have novelty, not be a port of existing designs | Sep 2026 |
| U-10 | Electronics first; mechanical only after the piezo motor is running | Sep 2026 |
| U-11 | BLE on the device to connect a CGM. Phone over BLE for now; custom CGM with its own protocol (another team) later | Sep 2026 |
| U-12 | Rev A is powered from the 3.7 V battery, not bench or USB power, so the power tree is validated before the PCB | 30 Sep 2026 |
| U-13 | Rev A parts from Indian websites; minimise cost wherever performance is not sacrificed | 30 Sep 2026 |
| U-14 | Recreate the pump's function; do not replicate a specific commercial device's architecture | Sep 2026 |

An earlier statement of the success criterion (22 Sep 2026): dosing accuracy within ±5 % of commanded volume, measured gravimetrically, water only.

## 2. Numbers the requirements depend on

| Quantity | Value | Where it comes from |
| --- | --- | --- |
| Syringe bore / area | 4.61 mm / 16.69 mm² | Hamilton 81320 (1001 TLL) |
| Volume per µm of travel | 16.69 nL | area × 1 µm |
| 1 U (10 µL, U-100) | 599 µm of travel = 7,489 counts | calc |
| Smallest dose, 0.05 U (0.5 µL) | 30.0 µm = 375 counts | calc |
| One encoder count (80 nm) | 1.34 nL = 0.00013 U | calc |
| Full syringe | 60 mm = 1.00 mL = 100 U = 750,000 counts | needs a 32-bit position |
| Force from line pressure | 0.83 N at 0.5 bar, 1.67 N at 1 bar | pressure × area |
| Highest pressure the motor can make | about 3.9 bar (6.5 N stall, zero friction) | syringe is rated 13.8 bar |
| Working load limit | 3 N total (friction + pressure) | LL06 recommended range 0–3 N |
| No-load full step | about 4.5 µm, shrinks with load | LL06 datasheet; PMD401 manual 5 ± 3 µm |
| Dosing speed cap | about 15 steps/s, roughly 0.11 U/s | project value |
| Motor top speed if uncapped | 15 mm/s = about 25 U/s | why the speed cap is a safety item (S-06) |
| Motor rail | 48 V ±5 % (45.6–50.4 V), 6 mA idle, ≤ 100 mA | PMD401 manual |
| Battery draw | about 2.1 A worst case at 3.0 V (about 1.7 A at 3.7 V, about 6.2 W while the motor runs); about 0.11 W idle with 48 V off | Rev A power budget. Not measured yet |
| Thermal expansion of a full syringe | about 0.02 U per K | water, 1 mL |
| PMD401 idle on 48 V | 48 V × 6 mA ≈ 0.29 W (about 7 Wh per day if left on) | reason the rail is switched |
| PMD401 peak | 48 V × 100 mA ≈ 4.8 W | PMD401 manual |

Numbers from datasheets, the quote or calculations have not been measured on project hardware. See `OPEN_QUESTIONS.md`.

## 3. Requirements

### 3.1 Dosing and performance

| ID | Requirement | Target | Status | Checked by |
| --- | --- | --- | --- | --- |
| D-01 | Actuation | Piezoelectric only: LL06 pushes the plunger directly, no gears, no screw | Decided | MT-04, MF-03 |
| D-02 | Fluid and place of use | Water or 0.9 % saline, bench only, 18–28 °C, never on a person | Decided | all |
| D-03 | Unit | 1 U = 10.0 µL (U-100) | Decided | DA-02 |
| D-04 | Reservoir | Hamilton 1001 TLL, 1.00 mL = 100 U, 60 mm stroke | Decided | MF-09 |
| D-05 | Smallest dose | 0.05 U = 0.5 µL = 30 µm = 375 counts | Decided | DA-05 |
| D-06 | Bolus range | 0.05 to 10 U in 0.05 U steps | Decided | DA-03 to DA-05, FT-11 |
| D-07 | Basal | Delivered as 0.05 U pulses; rate 0.05 to 5.0 U/h set by pulse spacing | Proposed | DA-06, DA-07 |
| D-08 | Delivery speed | Not above 15 steps/s (about 0.11 U/s) in any dosing mode | Decided | MT-03, FT-02 |
| D-09 | Position control | Closed loop on the LL06 encoder to an absolute target; approach from one side, never reverse to trim | Decided (one-sided stop Proposed) | FW-04, DA-10 |
| D-10 | Per-dose delivery check | Encoder travel within ±1 % or ±4 counts of commanded, whichever is larger, else stop and alarm | Proposed | DA-05, FT-05 |
| D-11 | Bolus accuracy | Every bolus ≥ 1 U within ±5 %; 20 × 0.05 U within ±5 % of 1 U | Proposed | DA-03 to DA-05 |
| D-12 | Basal accuracy | Mean flow within ±5 % over any window that delivers ≥ 0.5 U, room drift ≤ 0.5 K | Proposed | DA-06, DA-07 |
| D-13 | Accuracy under back pressure | D-11 still holds with ±100 mmHg at the outlet | Proposed | DA-08 |
| D-14 | Calibration | µL per count from a weight calibration, stored twice with a CRC | Proposed | DA-02, FT-12 |
| D-15 | Prime | Prime volume is logged and kept out of the dose ledger | Proposed | MF-06 |

### 3.2 Safety

| ID | Requirement | Target | Status | Checked by |
| --- | --- | --- | --- | --- |
| S-01 | Safe state | 48 V rail off, motor parked and clamped. Loss of either MCU, the heartbeat or any rail must end here | Decided | SG-03 to SG-05, FT-01, FT-03 |
| S-02 | Default-off enable | Boost enable held below 0.4 V by a 4.7 kΩ pull-down unless the main MCU drives it high through 1 kΩ; supervisor can pull it low through a BSS138 | Decided | PW-07, SG-01, SG-02 |
| S-03 | Three independent stop paths | (1) PMD401 stops on about 10 ms without SPI data, (2) supervisor parks the motor and cuts 48 V on a bad heartbeat, (3) firmware safe-halt on detected corruption | Decided | SG-04, SG-06, FT-12 |
| S-04 | Stop time | Motion stops within 300 ms of any trip; trip latches until cleared on purpose | Proposed | SG-04, SG-07 |
| S-05 | Dose limits | Smallest request 0.05 U, largest bolus 10 U, 15 U in any rolling hour; out-of-range requests refused | Decided | FT-11, BL-05 |
| S-06 | Runaway containment | No single fault delivers more than 0.5 U extra. The 15 steps/s cap must hold outside the main MCU, because the motor can otherwise reach about 25 U/s | Proposed | FT-02, MT-03 |
| S-07 | Independent travel check | Supervisor reads the same encoder A/B and keeps its own count against the S-05 limits | Proposed | FT-02, FT-04 |
| S-08 | Occlusion alarm | Sensorless detection from step length. Alarm before 1 U is pushed into a blocked line on a bolus, and within 2 h at 1 U/h basal | Decided (method), Proposed (limits) | OC-02, OC-03 |
| S-09 | Release after occlusion | No more than 0.5 U leaves the line when the blockage clears | Proposed | OC-04 |
| S-10 | Free flow | No plunger travel above 6 µm (0.01 U) in 1 h unpowered with a 1 m siphon head | Proposed | MT-06, MF-04 |
| S-11 | Pressure ceiling | Motor stall limits pressure to about 3.9 bar; every wetted part rated above that | Decided | MF-05 |
| S-12 | Alarms | Sound and light for occlusion, low battery, reservoir low and empty, system fault, link lost. Supervisor can sound the alarm on its own | Proposed | FT-01, FT-03, BT-02 |
| S-13 | Low battery | Dosing stops at 3.4 V on the cell; warning before that at 3.5 V | Decided (3.4 V), Proposed (warning) | BT-02 |
| S-14 | Reservoir end | Delivery stops before the plunger bottoms; the motor never stalls against the glass | Proposed | MF-08 |
| S-15 | Power loss | A dose cut by power loss is not resumed on restart; position and ledger survive | Proposed | FT-09, FT-10 |
| S-16 | Memory and firmware integrity | Flash CRC and RAM test at boot; limits, target and authorisation stored with complements; any mismatch locks dosing | Decided (hardening), Proposed (boot tests) | FW-09, FT-12, FT-14 |

Why S-06 and S-07 exist: the speed cap is firmware-only today. A main MCU that keeps its heartbeat alive but commands full speed would empty the syringe in about 4 s, and the supervisor as designed would not see it. This is an unresolved design gap, see `OPEN_QUESTIONS.md` items 2, 3 and 5.

### 3.3 Electrical and power

| ID | Requirement | Target | Status | Checked by |
| --- | --- | --- | --- | --- |
| E-01 | Source | One Li-ion cell, 3.0–4.2 V, with protection board, 5 A fuse and master switch | Decided | IN-04, PW-10 |
| E-02 | Logic rail | 3.3 V from the cell through an LDO; never below 3.0 V while dosing | Decided | PW-01, PW-11 |
| E-03 | Motor rail | 48 V ±5 % (45.6–50.4 V) at the PMD401 input, including ripple and a 0 → 100 mA load step | Decided | PW-02 to PW-06 |
| E-04 | Motor rail switching | 48 V on only while a dose moves; off state truly disconnects the load | Decided | PW-05, PW-07, PW-09 |
| E-05 | Current rating | Every part in the battery path rated above the 2.1 A worst-case draw | Decided | PW-06, IF-06 |
| E-06 | Voltage margin | Capacitors on the 48 V rail rated ≥ 100 V; nothing run above 80 % of its voltage rating | Decided (caps), Proposed (80 % rule) | IN-05, PB-10 |
| E-07 | Signal protection | TVS and about 100 Ω in series on every PMD401 signal line; MCU pins never see more than their rated voltage | Decided | IF-02, IF-04 |
| E-08 | Encoder interface | Quadrature A/B at 3.3–5 V into a hardware counter; no counts lost up to full motor speed; count survives 48 V switching | Decided (signal type), Proposed (rest) | IF-04, MT-08, FW-08 |
| E-09 | Charging | Charger used for charging only, never as the load path; ends at 4.20 V | Decided | BT-03 |
| E-10 | Battery life | Rev B runs at least 3 days on its cell at a normal daily profile | Proposed | BT-01 |
| E-11 | Touch safety | Motor rail stays under 60 V DC in every fault; 48 V capacitors discharge to under 5 V within 5 s of switch-off | Proposed | PW-08 |

Note: E-02 says "through an LDO". That describes Rev A (MCP1700). P-04 specifies a TPS62840 buck for Rev B. The source report does not reconcile the wording. See `OPEN_QUESTIONS.md` conflict CF-8.

### 3.4 Mechanical and fluid path

| ID | Requirement | Target | Status | Checked by |
| --- | --- | --- | --- | --- |
| M-01 | Plunger friction | Breakaway and running force under 1.5 N; above 3 N means change the syringe | Decided | MF-01 |
| M-02 | Total load on the motor | Friction plus pressure load at the alarm point ≤ 3 N | Decided | MF-01, OC-02 |
| M-03 | Coupling | Plunger fixed to the LL06 front adapter with no axial play; lost motion on reversal ≤ 3 µm | Proposed | MF-03 |
| M-04 | Alignment | Rod and syringe axes in line; coupling adds no more than 0.3 N to the measured friction | Proposed | MF-02 |
| M-05 | Barrel hold | Barrel does not move under 3 N push or pull | Proposed | MF-04 |
| M-06 | Stroke | 60 mm syringe stroke fits inside the rod travel with margin at both ends | Decided | MF-09 |
| M-07 | Wetted parts | Borosilicate glass, PTFE, Luer-lock line only; all joints Luer lock | Decided | MF-05 |
| M-08 | Leak tightness | No leak and no pressure loss for 10 min at 1.5 × the alarm pressure | Proposed | MF-05 |
| M-09 | Air | Line primed bubble-free before any accuracy or occlusion test; line compliance measured and recorded | Proposed | MF-06, MF-07 |
| M-10 | Heat | No part above 60 °C; syringe warms by less than 1 K in continuous use | Proposed | BT-05 |

### 3.5 Firmware

| ID | Requirement | Target | Status | Checked by |
| --- | --- | --- | --- | --- |
| F-01 | Structure | Plain C11 behind one hardware boundary (`pump_port.h`); the same dosing code runs on the PC simulator and the target | Decided | FW-04 |
| F-02 | Dose state machine | IDLE → UNPARK → MOVE → SETTLE → IDLE, with FAULT reachable from every state | Decided | FW-01, FW-04 |
| F-03 | Hardening | Complement-stored values, doubled limit checks with random delay, encoded booleans, control-flow counter | Decided | FT-12, FT-14 |
| F-04 | Coding standard | MISRA C:2025 on the dosing, occlusion and hardening modules; no open mandatory or required violations; no dynamic memory, no recursion | Proposed | FW-02, FW-03 |
| F-05 | Unit tests | Every safety module tested on the PC with full statement and branch coverage | Proposed | FW-01 |
| F-06 | Timing | Control loop period and SPI refresh measured; SPI gap never near the 10 ms PMD401 timeout in normal running | Proposed | FW-05 |
| F-07 | Watchdogs | Independent watchdog and brown-out reset on both MCUs | Proposed | FW-06 |
| F-08 | Event log | Every delivery (commanded and measured), alarm, fault and link event stored with a timestamp | Proposed | FW-10 |
| F-09 | Supervisor code | Separate code base from the main MCU; heartbeat is a changing token, not a level | Decided (separate MCU), Proposed (token) | FT-04, FW-11 |

Firmware modules named in the project (reference implementation, kept as an answer key while the owner rewrites it): `pump_config.h`, `pump_port.h`, `dose_ctrl.c`, `load_est.c`, `hardened.h`, `port_stm32wba.c`, `pump_app.c`, `sim_plant.c`, `test_main.c`. Still to write as of 29 Sep 2026: C031 supervisor firmware and BLE input.

### 3.6 Communication and security

| ID | Requirement | Target | Status | Checked by |
| --- | --- | --- | --- | --- |
| C-01 | Link | BLE from a phone now; the CGM team's own protocol later | Decided | BL-01 |
| C-02 | Pairing | LE Secure Connections with passkey or numeric comparison, bonded; dose commands refused on an unencrypted or "Just Works" link | Proposed | BL-01, BL-02 |
| C-03 | Command protection | Each dose command carries a counter and a check value so replayed or altered commands are refused | Proposed | BL-03, BL-04 |
| C-04 | Limits ignore the source | S-05 limits apply to every command, whoever sent it | Decided | BL-05, FT-11 |
| C-05 | Link loss | Defined behaviour when the phone or CGM goes quiet: no new automatic doses on glucose data older than 15 min | Proposed | BL-06 |
| C-06 | Debug access | SWD locked on Rev B | Proposed | PB-12 |
| C-07 | Glitch resistance (stretch) | Voltage and clock glitching cannot get an over-limit dose accepted | Decided as stretch goal | FT-14 |

### 3.7 Rev B PCB

| ID | Requirement | Target | Status | Checked by |
| --- | --- | --- | --- | --- |
| P-01 | Same circuit | Rev B carries the Rev A circuit as bench-proven; every change from Rev A is listed and re-tested | Decided | PB-01 |
| P-02 | Stack-up | 4 layers with one unbroken ground plane | Proposed | PB-02 |
| P-03 | 48 V zone | Boost, driver connector and 48 V capacitors grouped at one end; spacing for 48–65 V at least 0.6 mm on outer layers, 0.1 mm inner | Proposed | PB-04 |
| P-04 | Power parts | BQ25188 charger, LM51551 flyback to 48 V with a switched output, TPS62840 for 3.3 V, 1S protected cell | Decided | PB-10, PB-11 |
| P-05 | Safe defaults in copper | Pull resistors that set the off state (boost enable, park line, supervisor gate) placed on the board, not left to firmware | Proposed | PB-07 |
| P-06 | RF | Antenna area and matching copied from the ST reference design | Proposed | PB-06 |
| P-07 | Test access | Test point on every rail and every safety signal | Proposed | PB-07 |
| P-08 | Workmanship | Built and inspected to IPC Class 2; Class 3 is the mark to aim at | Proposed | PB-09 |

## 4. Non-functional requirements

| Area | Requirement | Status |
| --- | --- | --- |
| Schedule | 30 days from 21 Sep 2026 (about 21 Oct 2026) | DECIDED; at risk, see `OPEN_QUESTIONS.md` |
| Build quality | Close to industry grade | DECIDED |
| Sourcing | Indian websites for Rev A parts where possible; cost minimised without losing performance | DECIDED |
| Staging | Rev A gates Rev B. The schedule gates on dosing accuracy before PCB work is committed | DECIDED |
| Honesty of data | No invented part numbers or values. Unverified values are marked | DECIDED (owner instruction) |
| Records | One line per check; hazard table; change log for firmware and wiring; calibration record per syringe; third-party code list | PROPOSED (report section 6.14) |
| Learning | Owner writes the firmware; reference code must be explained | DECIDED |

## 5. Standards and how far each is followed

The pump is not certified to any of these. "Method" = tests are run the way the standard describes. "Design input" = designed to its rule. "Awareness" = real products must meet it; the prototype does not test to it. Editions are as recorded in the 10 Oct report; editions without a link there were not checked against a publisher page.

| Standard (edition as recorded) | Use here |
| --- | --- |
| IEC 60601-2-24:2012, ed. 2.0 | Method for dose accuracy, occlusion and single-fault checks |
| AAMI TIR101 | Method for dose accuracy by weight |
| IEC 60601-1, ed. 3.2 (2005 + A1:2012 + A2:2020) | Design input for S-01, E-11, M-10 |
| IEC 60601-1-10 (2007 + A1:2013 + A2:2020) | Design input for C-05, S-05 once the CGM is connected |
| IEC 60601-1-8 (2006 + A1:2012 + A2:2020) | Design input for S-12 |
| IEC 60601-1-11 (2015 + A1:2020) | Awareness |
| IEC 60601-1-2, ed. 4.1 (2014 + A1:2020) | Awareness; TVS on outside-facing lines is the only action |
| IEC 60529 | Awareness |
| IEC 60068-2 series | Awareness |
| ISO 14971:2019 | Design input: every S-requirement traces to a hazard and to a single-fault check |
| IEC 60812:2018 | Method for the single-fault matrix |
| ISO 13485:2016 | Awareness |
| IEC 62366-1 (2015 + A1:2020) | Awareness |
| IEC 62304:2006 + A1:2015 | Design input for firmware checks |
| IEC 62304 edition 2 | Scheduled for 12 Aug 2026; publication not confirmed. Check before citing |
| MISRA C:2025 | Method for FW-02 |
| IEC 60730-1 Annex H (Class B) | Method for FW-09 |
| Bluetooth Insulin Delivery Service v1.0.1 | Design input for C-03: copy its command layout |
| Bluetooth Core, LE Secure Connections | Design input for C-02 |
| IEC 81001-5-1:2021 | Design input for BLE and security checks |
| ISO/IEEE 11073-10419 | Awareness |
| ETSI EN 300 328, FCC Part 15.247, India WPC approval, Bluetooth qualification | Awareness |
| IEC 62133-2:2017 + A1:2021 | Design input for E-01, E-09 |
| UN 38.3 | Awareness |
| ISO 80369-7:2021 | Design input for M-07 |
| ISO 8655-6 | Method for dose accuracy by weight |
| ISO 10993-1:2025 | Awareness; no body contact here |
| IPC-2221C (2023) | Design input for P-03 |
| IPC-2152 | Design input for PB-05 |
| IPC-7351 | Design input for PB-03 |
| IPC-6012 | Awareness; order Class 2 |
| IPC-A-610 and J-STD-001 | Method for PB-09 |
| Medical Devices Rules, 2017 (CDSCO, India); 21 CFR 880.5730 (USA); Regulation (EU) 2017/745 | Only if this becomes a product. CDSCO risk class for insulin pumps not confirmed |

IEC 60601-2-24 test conditions quoted in the report were written from memory of the 2012 edition. Each must be checked against the standard text before being quoted.

## 6. What is not a requirement

- The uploaded note `some data about the pump` is background on commercial pumps. Its figures (for example 50–100 mbar occlusion thresholds, 500 ms heartbeats, AES-128/256, IPX7/IPX8, 72–80 h wear) are not requirements of this project.
- The older LT20 / Hamilton 1005 "Master Engineering Specification" and its R-01 to R-29 requirements are SUPERSEDED. Do not import its requirements, parts or numbers.
