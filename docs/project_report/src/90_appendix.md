@appendix Requirements Register {#app:req}
This appendix reproduces the technical requirements from `requirements/DESIGN_REQUIREMENTS.md` without change. Status is as recorded: **Decided** requirements are binding; **Proposed** requirements were written from standard practice and still need the owner's sign-off. Check IDs refer to Appendix C.

!table tab:app1 | Requirements: 3.1 Dosing and performance | 0.6,1.4,3.2,1,1
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

!table tab:app2 | Requirements: 3.2 Safety | 0.6,1.4,3.2,1,1
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

!table tab:app3 | Requirements: 3.3 Electrical and power | 0.6,1.4,3.2,1,1
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

!table tab:app4 | Requirements: 3.4 Mechanical and fluid path | 0.6,1.4,3.2,1,1
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

!table tab:app5 | Requirements: 3.5 Firmware | 0.6,1.4,3.2,1,1
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

!table tab:app6 | Requirements: 3.6 Communication and security | 0.6,1.4,3.2,1,1
| ID | Requirement | Target | Status | Checked by |
| --- | --- | --- | --- | --- |
| C-01 | Link | BLE from a phone now; the CGM team's own protocol later | Decided | BL-01 |
| C-02 | Pairing | LE Secure Connections with passkey or numeric comparison, bonded; dose commands refused on an unencrypted or "Just Works" link | Proposed | BL-01, BL-02 |
| C-03 | Command protection | Each dose command carries a counter and a check value so replayed or altered commands are refused | Proposed | BL-03, BL-04 |
| C-04 | Limits ignore the source | S-05 limits apply to every command, whoever sent it | Decided | BL-05, FT-11 |
| C-05 | Link loss | Defined behaviour when the phone or CGM goes quiet: no new automatic doses on glucose data older than 15 min | Proposed | BL-06 |
| C-06 | Debug access | SWD locked on Rev B | Proposed | PB-12 |
| C-07 | Glitch resistance (stretch) | Voltage and clock glitching cannot get an over-limit dose accepted | Decided as stretch goal | FT-14 |

!table tab:app7 | Requirements: 3.7 Rev B PCB | 0.6,1.4,3.2,1,1
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

!table tab:app8 | Non-functional requirements | 1,4,1.2
| Area | Requirement | Status |
| --- | --- | --- |
| Schedule | 30 days from 21 Sep 2026 (about 21 Oct 2026) | DECIDED; at risk, see `OPEN_QUESTIONS.md` |
| Build quality | Close to industry grade | DECIDED |
| Sourcing | Indian websites for Rev A parts where possible; cost minimised without losing performance | DECIDED |
| Staging | Rev A gates Rev B. The schedule gates on dosing accuracy before PCB work is committed | DECIDED |
| Honesty of data | No invented part numbers or values. Unverified values are marked | DECIDED (owner instruction) |
| Records | One line per check; hazard table; change log for firmware and wiring; calibration record per syringe; third-party code list | PROPOSED (report section 6.14) |
| Learning | Owner writes the firmware; reference code must be explained | DECIDED |

!table tab:app9 | Standards and how far each is followed (the pump is not certified to any of them) | 2,3
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

## Hardware constraints
The interface requirements and Rev B layout restrictions are reproduced below from `requirements/HARDWARE_CONSTRAINTS.md`.

!table tab:app10 | Interface requirements | 1.4,3.4,1.6
| Interface | Requirement | Status |
| --- | --- | --- |
| PMD401 SPI | Mode 3; 16-bit signed step rate; ≤ 500 kbit/s until PiezoMotor confirms more; refresh gap well under the 10 ms timeout (target longest gap under 5 ms) | Mode and timeout CONFIRMED from manual; speed limit conflicting (item 11); 5 ms PROPOSED |
| PMD401 word scale and bit order | Unknown; measured at bring-up | OPEN |
| PMD401 park (AEN) | Low = park, about 250 ms. Firmware sends nothing for 80 ms after unpark | CONFIRMED from manual |
| PMD401 signal levels | 3.3–5 V, no EMC protection on the driver. Pull-up rail voltage not stated in the manual | OPEN, measure first |
| PMD401 boot time after 48 V rises | Unknown. Firmware must wait at least the measured time | OPEN |
| RS-485 | MAX3485 at 3.3 V. Setup and read-back only | DECIDED |
| Encoder | Quadrature A/B, 3.3–5 V, 80 nm per count. No counts lost up to full motor speed. Count must survive 48 V switching | Signal type CONFIRMED by vendor; rest PROPOSED |
| Encoder supply | If the encoder is powered from the switched side, the count can jump when 48 V cycles. Feed it from the logic rail if needed | OPEN (item 12) |
| BLE | Phone now, CGM team's protocol later. LE Secure Connections with passkey or numeric comparison, bonded. Command counter + check value | Link DECIDED; security PROPOSED |
| Debug | SWD locked on Rev B | PROPOSED |
| Bench pressure reference | IBP transducer → HX711. Reads only to 300 mmHg (0.4 bar). Bench only, not on Rev B | DECIDED |
| Fluid | Luer lock at every joint | DECIDED |

!table tab:app11 | Rev B layout restrictions | 0.5,4,1.4
| # | Restriction | Status |
| --- | --- | --- |
| L-1 | 4 layers with one unbroken ground plane (P-02) | PROPOSED |
| L-2 | Boost/flyback, driver connector and 48 V capacitors grouped at one end of the board (P-03) | PROPOSED |
| L-3 | Spacing on 48 V and flyback-secondary nets (48–65 V): at least 0.6 mm on outer layers, 0.1 mm on inner layers. Enforce with a net-class rule. Confirm both against the IPC-2221C table (P-03, PB-04) | PROPOSED; inner figure conflicts with an older note, see conflict CF-6 |
| L-4 | Battery-path trace width from IPC-2152 for 2.1 A at a 10 K rise (PB-05) | PROPOSED |
| L-5 | Flyback switching loop small and on one layer (PB-05) | PROPOSED |
| L-6 | Antenna keep-out, matching parts and 32 MHz crystal copied from the ST reference design, unchanged (P-06, PB-06) | PROPOSED; the ST reference document is not identified in the project |
| L-7 | Pull resistors that set the off state (boost enable, park line, supervisor gate) are on the board, not left to firmware (P-05) | PROPOSED |
| L-8 | Test point on every rail and every safety signal (P-07) | PROPOSED |
| L-9 | Capacitors on the 48 V rail ≥ 100 V; nothing above 80 % of its voltage rating (E-06) | Caps DECIDED; 80 % PROPOSED |
| L-10 | Footprints from package drawings per IPC-7351; pin 1 marked; verified by 1:1 print or datasheet drawing (PB-03) | PROPOSED |
| L-11 | ERC and DRC clean in KiCad with the fab's rule file; each waived warning explained (PB-02) | PROPOSED |
| L-12 | Built and inspected to IPC Class 2; order the bare board to Class 2 (P-08) | PROPOSED |
| L-13 | Rev B schematic compared net by net with the Rev A wiring as built; every difference listed with its reason (P-01, PB-01) | DECIDED |

@appendix Decision Log, Open Questions and Document Conflicts {#app:dec}
Reproduced from `decisions/DECISION_LOG.md` and `requirements/OPEN_QUESTIONS.md`.

!table tab:app12 | Decision log: v1 (before September 2026) | 0.7,3.2,2.6,1.4
| Date | Decision | Rationale | Status |
| --- | --- | --- | --- |
| Before Sep | Build HybridPancreasSim: C++ closed-loop simulator (Bergman minimal model, PID, predictive controller, safety supervisor, fault injection) plus an ESP32 demo | Demonstrate control concepts used in commercial pumps | SUPERSEDED as hardware. Simulator results stand as background: PID about 89 % time in range; Predictive + Supervisor about 93 % with 0 % hypoglycemia |
| Before Sep | ESP32 DevKit + A4988 (SmartElex) + NEMA 17 JK42HS40-1204AF-02 on a T8 leadscrew, 11.1 V 3S LiPo; STEP = GPIO26, DIR = GPIO27 | Visible motor movement for a demo | SUPERSEDED |
| 8 Sep | Goal is to recreate the pump's function, not a specific commercial device's architecture | Owner's clarification | DECIDED |
| 8 Sep | Cost and part sourcing are not constraints; full lab available. Piezo motor considered to shrink the device | Owner's clarification | DECIDED (later refined on 30 Sep: still minimise cost where free) |

!table tab:app13 | Decision log: v2 re-scope | 0.7,3.2,2.6,1.4
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

!table tab:app14 | Decision log: 6. Decisions recorded in the Claude Code session of 10 Oct 2026 (digital handover objective) | 0.7,3.2,2.6,1.4
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

!table tab:app15 | Decision log: 7. Routing decisions, 11 Oct 2026 (Claude Code session, branch `placement-opt`) | 0.7,3.2,2.6,1.4
| Date | Decision | Rationale | Status |
| --- | --- | --- | --- |
| 11 Oct | D1: rotate R301, R302, C305 and R308 by 180° to give the FLY_PGOOD escape at U301 | Cleanest option; no grounding-topology change | DECIDED (owner); applied at `route-d1-done` |
| 11 Oct | D2: SW48_GATE / SW48_DRV floating placeholder copper. Copper change deferred; the concern is documented | Output switch (U-06) not designed | DEFERRED (owner) |
| 11 Oct | D3: undefined placeholder circuitry stays unrouted. RS485_B → R714 only after the owner is asked | Avoid inventing connections | DECIDED (owner) |
| 11 Oct | D4: no routing on the BQ25188 footprint until the TI drawing is checked | U-12 | DECIDED (owner): wait |
| 11 Oct | D5: wait for the ST documents before the crystal, RF and supply connections | U-05 | DECIDED (owner): wait |
| 11 Oct | D6: no grounding-topology change, and no grounding-dependent layout change, without review | FL-3 open | DECIDED (owner) |
| 11 Oct | D7: FLY_PGOOD → U501.28 deferred into a coordinated U501 pin 24–38 fan-out review after DS14127 and the ST RF layout documentation | The scratch investigation showed that re-routing pins 29/30 alone cannot free pin 28. A B.Cu crossing under RF_ANT is not assumed acceptable. Leftover segments are cleaned up only in a reviewed change. A pin reassignment needs explicit approval of the schematic and firmware/CubeMX change. | DEFERRED (owner) |
| 11 Oct | D8: PMD_READY_M and other possibly voltage-incompatible MCU inputs stay unrouted | PB15 tolerance (U-10) and the PMD401 Ready output level are not verified | BLOCKED (owner) |
| 11 Oct | D9: MAIN_SWCLK deferred to a joint review of the crystal layout and the SWD stub | Depends on the crystal layout (D5) | BLOCKED (owner) |

!table tab:app16 | Decision log: 8. Schematic ECO1, 31 Oct 2026 | 0.7,3.2,2.6,1.4
| Date | Decision | Rationale | Status |
| --- | --- | --- | --- |
| 31 Oct | Objective is now a fabricated, working bench prototype; owner approved the recommended architecture where evidence supports it and asked for schematic implementation. K-7 Rev A gate: owner has not separately waived it in writing | Owner instruction | DECIDED (owner) for ECO1; K-7 waiver OPEN |
| 31 Oct | ECO1: WBA55 supplies per DS14127 Fig. 15; MLPF-WB-04D3; HPH6-0090L; 1 uF soft start; 10 k bleeder; SMBJ48A clamp; K-12 switched output removed; READY/FAULT level shifters; LSE fitted; no MCU pin changes | Verification in ECO1_SCHEMATIC.md | IMPLEMENTED in schematic; PCB pending owner review |

!table tab:app17 | Decision log: 9. Digital completion, 1 Nov 2026 | 0.7,3.2,2.6,1.4
| Date | Decision | Rationale | Status |
| --- | --- | --- | --- |
| 1 Nov | Objective is a digital design only, no fabrication. Replaces the 31 Oct "fabricated, working prototype" objective. K-7 and the Phase 6 manufacturing outputs do not apply | Owner | DECIDED (owner) |
| 1 Nov | P3 hold lifted: flyback and 48 V routed with Q301 margin, T301 leakage and PMD401 overvoltage still open | These need hardware or the vendor; they cannot be closed digitally | DECIDED (owner authorised defaults) |
| 1 Nov | D4 lifted: U101 routed on the 0.4 mm footprint. Pitch still inferred | SLUSFJ3 copy has no outline drawing | DECIDED; footprint stays marked UNVERIFIED |
| 1 Nov | ENC_I_M: one B.Cu crossing under RF_MCU with In1 GND between; WBA_VDD11 B.Cu jog moved north of pin 48. Replaces the D7 caution for this net only | Avoids a schematic and firmware pin change | DECIDED (owner authorised defaults) |
| 1 Nov | OVP group moved beside C311/C702; R315 and C313 on B.Cu | Original spot needed crossings; the top side under the capacitor bodies has no room | DECIDED |
| 1 Nov | D701-D709 = Nexperia PESD5V0S1BA,115 | Bidirectional, VRWM 5 V, SOD323, from Nexperia product data | DECIDED |
| 1 Nov | PWR_FLAG on WBA_VDDSMPS, WBA_VLXSMPS, WBA_VDD11, WBA_VDDHPA, WBA_VDDRFPA | These rails are fed through a bead or inductor, or by the chip's SMPS, so no pin is a KiCad power output | DECIDED |
| 1 Nov | MAX3485 flattened into the project symbol library | Clears lib_symbol_mismatch; same pins and graphics | DECIDED |

!table tab:app18 | Open items carried from the 10 Oct 2026 report | 0.4,2,2.2,2.6
| # | Open item | Why it matters | How the report says to close it |
| --- | --- | --- | --- |
| 1 | Motor delivery is 3–4 weeks from payment | Lands in early to mid November, after the 21 Oct target | Pay now and ask for stock or express. Incoming-inspection, power-tree, kill-path and all firmware checks can run without the motor |
| 2 | The speed cap lives only in main-MCU firmware | Uncapped, the motor reaches about 25 U/s; a runaway with a live heartbeat is not stopped (S-06) | Ask PiezoMotor whether the PMD401 can store a hard maximum rate. If not, the supervisor must enforce it (item 5) |
| 3 | Supervisor gate defaults to "no veto" | The 10 kΩ gate pull-down keeps the BSS138 off when the supervisor is dead or in reset, so the main MCU alone can switch 48 V on. That breaks S-01. Check SG-03 fails as wired | Make the 10 kΩ a pull-up to 3.3 V so the veto is on by default and the supervisor must drive the gate low to permit a dose. Also make the main MCU refuse to dose without a supervisor reply. Then run SG-03 |
| 4 | Park line default is unknown | If the PMD401 pulls its park input high inside, a dead supervisor leaves the motor enabled | Measure in IF-02, fit a pull-down strong enough to win, prove it with SG-05 |
| 5 | Supervisor cannot see plunger travel | It can only judge the heartbeat, not the dose (S-07) | Wire encoder A/B to a C031 timer as well, with its own series resistors, and give it its own count against the S-05 limits |
| 6 | No buzzer and no STOP button in the parts | S-12 and SG-08 need them | Add a buzzer driven by the supervisor and a STOP button on a supervisor input |
| 7 | Reference pressure sensor stops at 0.4 bar | The simulated alarm point was about 773 mmHg (1.03 bar), more than twice what the IBP transducer can read | Add a 0–2 bar reference, or set the alarm at or under 0.4 bar and check it still clears friction noise |
| 8 | Balance resolution | 0.1 mg cannot prove a single 0.05 U dose to 5 % | Book time on a 0.01 mg balance, or claim single small doses as position-verified only |
| 9 | Syringe mount and coupling are not designed | All mechanics, fluid, accuracy and occlusion checks wait for them | Design and print or machine them while the motor ships; trial-fit with disposable syringes |
| 10 | Plunger friction is unknown | It sets the occlusion headroom; above 3 N the syringe must change | Check MF-01 on the day the Hamilton arrives |
| 11 | PMD401 unknowns: SPI top speed (15 Mbit/s on the web page, 500 kbit/s in the manual), command scale, bit order, pull-up voltage, boot time, current at dosing speed | Each one changes a driver setting or a firmware delay | IF-02, IF-03, MT-03, MT-07; ask PiezoMotor for the SPI limit in writing |
| 12 | Where the encoder gets its power | If it is fed from the switched side, the count can jump every time 48 V cycles | MT-08; feed it from the logic rail if needed |
| 13 | Rod stroke figure | Notes give more than one value (see conflict CF-1) | Read it off the order confirmation; either one covers the 60 mm syringe |
| 14 | Earlier docs disagree with the final design | See conflicts CF-2, CF-3, CF-4 | Update both older docs to: INA219, 80 nm encoder, RS-485 for setup and SPI for the rate command |
| 15 | Limits marked Proposed | They are Claude's suggestions from standard practice, not project decisions | Go through requirement sections 3.1 to 3.7 and accept, change or strike each one |
| 16 | Link-loss behaviour and the CGM protocol | C-05 and BL-06 cannot be tested against an unwritten rule | Write one page: what the pump does when the phone or CGM goes quiet, and the message format agreed with the CGM team |
| 17 | Rev B choices: flyback transformer, cell size, board outline, battery-life target | They block the layout | Fix them after PW-09, MT-07 and BT-01 give real power numbers |
| 18 | Standards to confirm | IEC 62304 edition 2 status; the IEC 60601-2-24 figures quoted from memory; the CDSCO risk class | Check the IEC webstore and the standard text through the institute library |
| 19 | Temperature and low basal rates | A full syringe moves about 0.02 U per K, a fifth of an hour's dose at 0.1 U/h | Keep the draft shield on, log temperature in DA-07, and state the window the accuracy claim covers |

!table tab:app19 | Contradictions between project documents (CF-1 to CF-23) | 0.6,2.4,2.4,1.8
| ID | Conflict | Where each side appears | Current reading |
| --- | --- | --- | --- |
| CF-1 | LL06 stroke: 0–77.4 mm vs 74.1 mm vs ≤ 73.9 mm | 77.4: configurator selection and quote thread. 74.1: "notes" cited in the 10 Oct report. 73.9: Parts List integration check | OPEN. Read it off the order confirmation. All cover 60 mm |
| CF-2 | Encoder resolution: 1.25 µm vs 80 nm | 1.25 µm: Parts List (30 Sep) says to order it. 80 nm: 29 Sep report, quote, 10 Oct report | 80 nm (E2) is what was quoted. Parts List is stale |
| CF-3 | Current monitor: INA226 (swap shunt to 20 mΩ if R100) vs INA219 (R100 expected) | INA226: Parts List and Component Roles docs. INA219: 30 Sep chat decision, 10 Oct report | INA219. Older docs are stale. Note the opposite meaning of an R100 marking in the two versions |
| CF-4 | How the PMD401 is commanded and who closes the loop | Component Roles: commands over RS-485, PMD401 closes the position loop with the motor's encoder. 29 Sep and 10 Oct reports: SPI servo mode, MCU reads the encoder and closes the loop; RS-485 for setup only | SPI servo mode per the later report. Component Roles is stale. The Parts List firmware note "command relative PMD401 moves after each 48 V power-up" belongs to the old arrangement |
| CF-5 | Rev A power source: kit's 48 V supply vs the battery | 29 Sep report: Rev A runs from the kit supply, battery chain waits for Rev B. 30 Sep owner decision: Rev A from the battery | Battery. The 29 Sep report was not updated. The kit supply is still used for first motor bring-up |
| CF-6 | Inner-layer spacing for 48–65 V nets: 0.1 mm vs 0.2 mm | 0.1 mm: 10 Oct report P-03 / PB-04 (IPC-2221C). 0.2 mm internal: superseded Master Specification, which cited IPC-2221B as allowing 0.6 / 0.1 mm | OPEN. P-03 is PROPOSED and itself says to confirm against the IPC-2221C table |
| CF-7 | "Rev B carries the Rev A circuit as bench-proven" vs a different Rev B power stage | P-01 and the report scope ("the same circuit on a custom 4-layer PCB") vs P-04 (LM51551 flyback replaces Pololu + DC2628A; TPS62840 replaces MCP1700; BQ25188 replaces TP4056; protected cell replaces 18650 + board) | OPEN. The Rev B power stage is not what Rev A proves. Only the optional TPS62840-1DLCEVM55 gives any early evidence. The owner should say whether Rev B power parts need their own bench stage |
| CF-8 | E-02 says 3.3 V "through an LDO"; P-04 says TPS62840 buck on Rev B | Both in the 10 Oct report | OPEN wording. E-02 describes Rev A |
| CF-9 | BSS138 gate default: pull-down vs pull-up | Pull-down to GND: Component Roles and Parts List (reason given: keep the BSS138 off while the C031 boots). Pull-up to 3.3 V: 10 Oct report, item 3 | OPEN. As wired, a dead supervisor gives no veto and S-01 is not met |
| CF-10 | Schedule: finish about 21 Oct vs motor arriving early to mid November | Owner's 30-day target vs vendor lead time | OPEN |
| CF-11 | DC2628A at Mouser India: "6 in stock, 9-week lead time after" vs "9 in stock, no restock planned". Also where to buy it: one DigiKey India cart (Parts List) vs prices taken from Mouser India because DigiKey India could not be read (chat record) | Parts List vs 30 Sep chat summary | Both stale. Re-check stock |
| CF-12 | STM32WBA55 Bluetooth version: 5.3 vs 5.4 | 5.3: 27 Sep selection notes. 5.4: superseded Master Specification | OPEN. Take it from the ST datasheet |
| CF-13 | Delivery term: DAP Guwahati (€150) vs FCA Uppsala | Agreed in the revised quote; the quote document still listed FCA Uppsala | OPEN until the order confirmation is seen |
| CF-14 | Starter Kit contents: includes a USB–RS-485 cable vs not listed | 29 Sep report vs the vendor's contents list (motor cable, encoder cable, 48 V supply) | OPEN. Affects whether item 10 (USB-to-RS-485 adapter) is needed |
| CF-15 | Occlusion alarm level vs what the bench reference can read | Simulated alarm about 773 mmHg (1.03 bar); IBP transducer reads to 300 mmHg (0.4 bar) | OPEN, same as item 7 |
| CF-16 | PMD401 SPI maximum: 15 Mbit/s vs 500 kbit/s | PiezoMotor web page vs PMD401 manual | OPEN, same as item 11. Design for 500 kbit/s |
| CF-17 | Heartbeat: a UART link vs "a changing token, not a level"; period and timeout undefined | UART: Component Roles. Token: 10 Oct report (PROPOSED). 100 ms period / 300 ms timeout appear only in the superseded specification; the 10 Oct report uses a 300 ms trip time (S-04, PROPOSED) | OPEN |
| CF-18 | Resistor package: 0603 vs through-hole | Parts List store searches are for 0603 parts; 10 Oct list says the 4.7 kΩ parts are through-hole | Minor. Rev A is breadboarded |
| CF-19 | Supervisor "owns AEN and the 48 V enable" vs "main MCU switches the enable, supervisor has a veto" | 29 Sep report wording vs the power-tree wiring | The wiring description is the detailed one. Wording should be aligned |
| CF-20 | Size of the Rev A parts list: 9 lines vs 35 components vs 37 lines | 29 Sep report and `Pump_RevA_BOM.xlsx`; 30 Sep Excel parts list; 10 Oct report | 37 lines (10 Oct) is the baseline. The two spreadsheets predate it and differ from it |
| CF-21 | Encoder counter width: 32-bit timer vs 16-bit extended to 32 | Superseded specification (TIM2, 32-bit) vs current notes ("encoder wraparound 16-bit to 32-bit", FW-08 "if a 16-bit timer is used") | OPEN. Depends on the pin assignment |
| CF-22 | "Measure plunger force before ordering the LL06 kit" vs the kit already quoted and "pay now" | Parts List checklist vs 10 Oct report item 1 and item 10 (friction measured when the Hamilton arrives) | OPEN. The order of these two steps was reversed in practice |
| CF-23 | "Rev A powered from the battery, not bench power" vs "bench supply first, battery second, PMD401 last" | Owner decision of 30 Sep vs the power-tree check sequence | Probably compatible (bench supply only for staged bring-up, then the cell). Worth one line of confirmation from the owner |

@appendix Validation Plan {#app:vplan}
The complete bench validation plan from `requirements/VALIDATION_PLAN.md`. **No check has a recorded result.** Groups run in order; if any kill-path (SG) check fails, testing stops until it passes.

!table tab:app20 | Part A: Rev B board checks | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| PB-01 | Schematic against the bench | Compare the Rev B schematic net by net with the Rev A wiring as built | Every difference listed with its reason |
| PB-02 | ERC and DRC | Run both in KiCad with the fab's rule file | No errors; each waived warning explained |
| PB-03 | Footprints | Print at 1:1 and lay the parts on it, or compare with each datasheet drawing | Every footprint fits; pin 1 marked |
| PB-04 | Spacing | Net-class rule on the 48 V and flyback secondary nets | At least 0.6 mm on outer layers and 0.1 mm on inner layers; confirm both against the IPC-2221C table |
| PB-05 | Current paths | Battery-path trace width from IPC-2152 for 2.1 A; area of the flyback switching loop | Width meets the calculation for a 10 K rise; loop small and on one layer |
| PB-06 | RF | Antenna keep-out, matching parts and 32 MHz crystal against the ST reference design | Same as the reference |
| PB-07 | Defaults and test points | Pull resistors on boost enable, park line and supervisor gate; a test point on each rail and safety signal | All present in the layout |
| PB-08 | Bare board | Multimeter between 48 V, 3.3 V, battery and ground before soldering | No shorts |
| PB-09 | Assembly inspection | Under magnification, against IPC-A-610 Class 2 | No bridges, tombstones, lifted pins or unsoldered thermal pads |
| PB-10 | Flyback | 48 V across 3.0–4.2 V in and 0–100 mA out; peak voltage on the FET and diode; enable off | Inside 45.6–50.4 V; nothing above 80 % of its voltage rating; output off when disabled |
| PB-11 | Charger and protection | Read back the BQ25188 settings; repeat BT-03 and PW-10 | Same limits |
| PB-12 | Debug lock | Set read-out protection and try to read the flash over SWD | Read refused |
| PB-13 | Regression | Repeat the power-tree (PW) and kill-path (SG) groups, then DA-03, OC-02 and FT-01 on the board | Same limits as Rev A |

!table tab:app21 | Bench checks: 1. Incoming inspection, before any power | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| IN-01 | Motor identity | Read the code on the LL06; check rod, front adapter, encoder cable | Code LL06A0-101M1G1E2, 100.8 mm rod, no chips or marks on the rod. Keep the rod clean and dry; never oil it |
| IN-02 | Kit contents | Unpack against the order confirmation | PMD401, motor cable, encoder cable, 48 V supply |
| IN-03 | Kit supply | Multimeter, no load | 45.6–50.4 V |
| IN-04 | Syringe | Look for cracks; move the plunger by hand over the full stroke | Smooth travel, Luer lock intact |
| IN-05 | Cell | Check wrap and markings, measure open-circuit voltage, weigh it | Above 3.0 V; weight matches the Molicel datasheet |
| IN-06 | Current monitor | Read the shunt marking on the INA219 module | R100 |
| IN-07 | DC2628A capacitor swap | Fit the 47 µF / 100 V part across VOUT and GND before first power | Stock 50 V capacitor no longer the only output capacitor |
| IN-08 | Polarity | Every electrolytic, both XT30 pairs, the cell holder | Matches the wiring diagram; 5 A fuse fitted |
| IN-09 | Nucleo power jumpers | WBA55: JP2 removed, 3.3 V to JP2 pin 2. C031: IDD jumper as its user manual says | Read back against both user manuals before applying 3.3 V |

!table tab:app22 | Bench checks: 2. Power tree: bench supply first, battery second, PMD401 last | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| PW-01 | LDO alone | Bench supply swept 3.0–4.2 V into the MCP1700 with a 50 mA load | 3.23–3.37 V for 3.5 V in and above; at least 3.0 V at 3.2 V in |
| PW-02 | 48 V stage, no load | 12 V bench supply limited to 0.5 A into the DC2628A | 46.5–49.5 V; no heavy ringing on the switch node |
| PW-03 | 48 V stage, loaded | Add the 470 Ω load for 10 min | 45.6–50.4 V including ripple; hottest part below 60 °C; record ripple and input current |
| PW-04 | Load step | Switch the 470 Ω load in and out on the scope | Stays inside 45.6–50.4 V in both directions |
| PW-05 | 12 V stage | Pololu from a bench supply swept 3.0–4.2 V, feeding the loaded DC2628A | 11.5–12.5 V. With enable low the output reads 0 V, not the input voltage |
| PW-06 | Whole chain on the cell | Repeat PW-03 and PW-04 from the battery through protection, fuse, switch and INA219 | Same limits; battery current ≤ 2.1 A; no MCU reset |
| PW-07 | Default off | Power the battery side with both MCUs held in reset, then with both unpowered | Enable node ≤ 0.2 V and 48 V rail at 0 V |
| PW-08 | Rail discharge | Scope the 48 V rail when enable goes low, PMD401 connected | Below 5 V within 5 s; record the time |
| PW-09 | Idle draw | INA219 against a multimeter, 48 V off | Record; the budget is about 0.11 W |
| PW-10 | Battery protection | Put a bench supply in place of the cell and ramp it down. Never short a real cell to test this | Protection board opens at its datasheet cut-off |
| PW-11 | Logic rail under motor load | Bench supply at 3.4 V in place of the cell, motor at dosing speed, scope the 3.3 V rail | At least 3.0 V and no brown-out reset. The 0.1 Ω shunt alone drops about 0.2 V at 2 A |

!table tab:app23 | Bench checks: 3. Kill path | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| SG-01 | Main MCU switches the rail | Toggle its enable pin | 48 V on when high, off when low |
| SG-02 | Supervisor veto | Main pin held high, supervisor turns the BSS138 on | Enable below 0.4 V, 48 V off |
| SG-03 | Dead supervisor | Hold the supervisor in reset, then unpower it, then ask the main MCU to dose | No 48 V, no motion. **As wired today this fails**; see `OPEN_QUESTIONS.md` item 3 |
| SG-04 | Heartbeat loss | Halt the main MCU with the debugger mid-move; scope heartbeat, park line and 48 V | Park line low and enable low within 300 ms |
| SG-05 | Park line default | Pull the supervisor's park-line wire off | PMD401 sees "parked" |
| SG-06 | Driver timeout | Stop SPI traffic while moving, with the heartbeat kept alive by a test build | Motor stops in about 10 ms |
| SG-07 | Latch | Remove the cause of any trip | 48 V stays off until cleared on purpose |
| SG-08 | STOP button | Press during a bolus | Motion stops within 300 ms; record the over-travel in counts |

!table tab:app24 | Bench checks: 4. Boards and interfaces | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| IF-01 | No back-feed | USB (ST-LINK) and external 3.3 V both connected; measure current through the feed jumper | Nothing flows back into the on-board regulator; 3.3 V does not move when USB is plugged or pulled |
| IF-02 | PMD401 signal levels | Before any MCU pin is connected, measure the PMD401's pull-up voltage on each signal line | No MCU pin sees more than its rating. If the pull-ups are 5 V, use 5 V-tolerant pins or open-drain outputs |
| IF-03 | SPI | Scope clock, data and chip select | Mode 3, correct bit order, 500 kbit/s or less until PiezoMotor confirms a higher limit |
| IF-04 | Encoder signals | Scope A and B at the MCU pin with the TVS and 100 Ω fitted, at dosing speed and at the fastest rewind speed | Clean edges, a quarter cycle apart, levels inside the pin limits |
| IF-05 | Encoder count integrity | Drive 10 mm out and back to a fixed stop, 20 times | Same count at the stop within ±3 counts every time; direction sign correct |
| IF-06 | Setup link | Write and read back PMD401 settings over RS-485 | Read back equals written |
| IF-07 | Current monitor | Compare the INA219 with a multimeter at 0.1, 1 and 2 A | Voltage within 1 %, current within 3 % |
| IF-08 | Heartbeat | Scope the main-to-supervisor line; then hold it high, hold it low | Period and token as designed; a stuck line in either state trips the supervisor |

!table tab:app25 | Bench checks: 5. Motor and driver | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| MT-01 | Servo mode | Set it over RS-485 (`X0Y13,3` then `X0Y32`), then power-cycle | Setting survives the power cycle |
| MT-02 | Park and unpark timing | Scope the park line and the encoder | Parks in about 250 ms; firmware sends nothing for 80 ms after unpark |
| MT-03 | Rate scale and speed cap | Command known rates and measure encoder speed; then command above the cap from a test build | Record counts per second per command unit. Speed stays at or below 15 steps/s whatever is commanded |
| MT-04 | No-load step length | Encoder travel divided by waveform steps, both directions | 2 to 8 µm; record the value and the room temperature |
| MT-05 | Step length against load | Push against known forces from 0 to 3 N in 0.5 N steps, three runs | A smooth, repeatable falling curve. This curve is the calibration of the occlusion sensor |
| MT-06 | Unpowered hold | 48 V off; push the rod with 3 N for 1 min in each direction | Travel no more than 6 µm (75 counts) |
| MT-07 | Driver current and boot time | Current at idle and at dosing speed; time from 48 V rising to the PMD401 accepting a command | Record both; firmware waits at least the measured boot time |
| MT-08 | Count across rail switching | Switch 48 V off and on 100 times, motor still, then again with 1 N on the rod | Count moves by no more than ±2 in total. If the encoder loses power with the rail, feed it from the logic side |
| MT-09 | Driver status lines | Power up with the motor cable unplugged | Fault seen by the MCU; dosing refused |

!table tab:app26 | Bench checks: 6. Mechanics and fluid path | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| MF-01 | Plunger friction | Syringe full of water, line attached, outlet open. Force gauge at five positions along the stroke, five runs each | Breakaway and running under 1.5 N. Between 1.5 and 3 N, lower the alarm pressure. Above 3 N, change the syringe |
| MF-02 | Alignment | Drive the plunger with the motor at dosing speed and read force from the MT-05 curve | No more than 0.3 N above MF-01; step length even along the stroke |
| MF-03 | Lost motion | Dial indicator on the plunger; reverse direction 10 times | Plunger follows the encoder within 3 µm |
| MF-04 | Barrel hold and siphon | Push and pull the barrel with 3 N; then leave unpowered for 1 h with the outlet 1 m below the pump | Barrel does not shift; plunger travel no more than 6 µm |
| MF-05 | Leak | Close the stopcock, go to 1.5 × the alarm pressure, hold 10 min | No wet joint; pressure falls by less than 5 % |
| MF-06 | Priming | Fill with degassed water and prime until the line runs clear; log the volume | No visible bubble in syringe, stopcock or line; prime volume not in the dose ledger |
| MF-07 | Line compliance | Stopcock closed, advance in 0.01 U steps, read pressure | Record µL per bar. Repeat after re-priming; a large change means trapped air |
| MF-08 | End of travel | Run to the software end stop at both ends | Stops before the plunger reaches the glass; the motor never stalls on the syringe |
| MF-09 | Stroke fit | Measure usable rod travel with the syringe mounted | 60 mm plus at least 2 mm spare at each end |

!table tab:app27 | Bench checks: 7. Dose accuracy by weight (the acceptance gate) | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| DA-01 | Drift blank | 30 min with the pump idle and the tube in the vial | Balance moves by no more than 0.1 mg. If it moves more, fix the setup before measuring anything |
| DA-02 | Volume calibration | Deliver 5 × 10 U and weigh each; work out µL per count; repeat on three fills | The three results agree within 0.3 %; value stored twice with a CRC |
| DA-03 | 1 U bolus | 25 in a row, each weighed | Each within 9.98 ± 0.50 mg; mean within 2 % |
| DA-04 | 10 U bolus | 5 in a row | Each within 3 % of 99.8 mg |
| DA-05 | 0.05 U dose | 25 in a row; weigh the running total and log encoder travel per pulse | Any 20 pulses in a row total 9.98 ± 0.50 mg; each pulse is 375 ± 4 counts |
| DA-06 | Basal at 1 U/h | 5 h run, first hour discarded, balance logged every 30 s | Mean flow in each 1 h window within 5 %; trumpet curve plotted |
| DA-07 | Basal at 0.1 U/h | At least 10 h, room temperature logged alongside | Judged on windows that deliver 0.5 U or more; expect temperature to be the largest error |
| DA-08 | Back pressure | Repeat DA-03 with the outlet 1.36 m above and 1.36 m below the pump (±100 mmHg) | Each bolus still within 5 % |
| DA-09 | Position in the syringe | Repeat DA-03 near full, at half and near empty | The three means agree within 1 % |
| DA-10 | Counts against weight | For every dose of 1 U or more above, compare volume from counts with volume from weight | Agree within 1 % |
| DA-11 | Temperature | Repeat DA-03 at 18 °C and 28 °C | Record only |

!table tab:app28 | Bench checks: 8. Occlusion and pressure | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| OC-01 | No false alarms | 200 mixed deliveries, basal pulses and boluses from 0.05 to 10 U, into an open line | No occlusion alarm |
| OC-02 | Blocked line, bolus | Close the stopcock and command a 5 U bolus; log pressure and counts | Alarm before 1 U has gone in; motor load at alarm no more than 3 N; record the peak pressure |
| OC-03 | Blocked line, basal | Close the stopcock during 1 U/h basal | Alarm within 2 h; record time and missed dose |
| OC-04 | Release | After the alarm, open the stopcock with the outlet in the vial | No more than 0.5 U (5 mg) comes out |
| OC-05 | Estimate against reference | Step the pressure up to the alarm point and compare the step-length estimate with the reference at each step | Record the error at each point; this sets how tight the alarm threshold can be |
| OC-06 | Air in the line | Add a 10 µL bubble and repeat OC-02 | Alarm still comes; record how much later |
| OC-07 | Partial block | Fit a restrictor (fine needle or pinch clamp) and repeat DA-03 | Either accuracy holds or an alarm is raised; never a silent shortfall above 5 % |
| OC-08 | Stall | Run the plunger into a fixed stop | "Steps without travel" fault within the set step count; motor stops pushing |
| OC-09 | No syringe | Command a prime with the syringe removed | Flagged as abnormally low load, if this feature is kept |

!table tab:app29 | Bench checks: 9. Single-fault matrix | 0.6,1.6,3,2.4
| ID | Fault | How to create it | Pass |
| --- | --- | --- | --- |
| FT-01 | Main MCU hangs mid-bolus | Halt with the debugger | Driver stops the motor in about 10 ms; supervisor trips within 300 ms |
| FT-02 | Main MCU runs away | Test build that commands full rate and keeps the heartbeat alive | Within the 0.5 U limit. **Cannot pass until S-06 and S-07 are built** |
| FT-03 | Supervisor dead | Reset it, then unpower it | No dose can start; main MCU alarms |
| FT-04 | Heartbeat wire | Open it, short it to 3.3 V, short it to ground | Trip every time |
| FT-05 | Encoder wire lost mid-move | Pull A, then B | Fault within the set step count; no further pushing |
| FT-06 | Encoder direction wrong | Swap A and B | Fault on the first move |
| FT-07 | Rate scale wrong | Scale the SPI command by +27 % and −27 % | Dose still lands inside D-10 |
| FT-08 | 48 V low | Feed the PMD401 from a bench supply at 44 V | Dosing stops. Do not test above 50.4 V |
| FT-09 | Brown-out mid-dose | Ramp the battery-side supply from 3.7 V down to 2.8 V during a bolus | Clean stop, motor clamped, no reset loop |
| FT-10 | Power cycle mid-dose | Switch off and on during a bolus | Comes up idle, reports the unfinished dose, does not resume it; position and ledger intact |
| FT-11 | Bad requests | 0 U, 0.04 U, 10.05 U, a negative value, a 16th unit inside one hour | All refused and logged |
| FT-12 | Corrupted stored values | Flip one bit in the limits, the target, the authorisation flag and one calibration copy | Detected every time; dosing locked |
| FT-13 | Driver fault line | Assert Fault or drop Ready | Dosing stops |
| FT-14 | Glitching (stretch) | ChipWhisperer-Husky voltage and clock glitches aimed at the limit checks | No over-limit dose accepted; record attempts and any hits |
| FT-15 | Enable pin stuck high | Tie the MCU side of the 1 kΩ resistor to 3.3 V | Supervisor still pulls enable below 0.4 V |

!table tab:app30 | Bench checks: 10. Firmware | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| FW-01 | Unit tests | Run on the PC against the simulated motor and syringe | All pass; full statement and branch coverage on dose_ctrl, load_est and hardened |
| FW-02 | Static analysis | A MISRA checker over the safety modules | No open mandatory or required finding; each deviation written down with its reason |
| FW-03 | Compiler hygiene | Build with -Wall -Wextra -Werror; search for malloc, recursion and loops with no bound | Clean build; none in the safety modules |
| FW-04 | Simulator regression on the owner's own rewrite | The tests the reference code passed: 40 × 0.05 U, a 5 U bolus, step lengths from 2 to 8 µm, blocked line, bit flips, MCU hang | 40 pulses total 20 µL within 0.5 %; every injected fault detected |
| FW-05 | Loop timing on the board | Toggle a pin in the control loop; scope the period and the gap between SPI frames | Period jitter under 10 %; longest SPI gap under 5 ms, half the driver timeout |
| FW-06 | Watchdogs and brown-out | Force a hang on each MCU and read the reset-cause register | Watchdog reset on both; brown-out reset enabled |
| FW-07 | Stack | Fill pattern and high-water mark after the whole test set | Under 70 % used |
| FW-08 | Position counter | If a 16-bit timer is used, cross its wrap point 100 times each way at rewind speed | The 32-bit position never jumps |
| FW-09 | Start-up self-test | Flash CRC, RAM test, clock check; then corrupt one flash byte in a test image | Corruption caught; dosing locked |
| FW-10 | Event log | Run a day of mixed deliveries and read the log back after a power cycle | Every delivery has commanded volume, measured volume and a timestamp; nothing lost |
| FW-11 | Supervisor review | Someone other than the author reads the supervisor code against S-01 to S-07 | Review notes kept |
| FW-12 | Traceability | One table: requirement, code module, check ID | No requirement without a check; firmware build hash in every test record |

!table tab:app31 | Bench checks: 11. BLE and security | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| BL-01 | Pairing | Pair from the phone and read the link's security level | LE Secure Connections with passkey or numeric comparison; bonded |
| BL-02 | Unpaired access | Write to the dose characteristic from an unpaired device, then from a "Just Works" pairing | Refused both times |
| BL-03 | Replay | Capture a valid dose command and send it again | Refused |
| BL-04 | Tamper | Change one bit of a valid command | Refused |
| BL-05 | Bad data | 10,000 random and out-of-range packets | No crash, no reset, no dose |
| BL-06 | Link loss | Switch the phone off mid-bolus; then let the glucose data go stale | Behaves exactly as C-05 is written; no automatic dose on data older than 15 min |
| BL-07 | Command to motion | Time from phone send to first encoder movement | Record |
| BL-08 | Radio sanity | Packet loss at 1 m and 5 m next to a busy Wi-Fi router | Record; this is not an approval test |

!table tab:app32 | Bench checks: 12. Battery and endurance | 0.6,1.6,3,2.4
| ID | Check | How | Pass |
| --- | --- | --- | --- |
| BT-01 | Run time | From full: 1 U/h basal plus three 5 U boluses a day, down to the 3.4 V cut-off | Record the days; Rev B target is 3 |
| BT-02 | Low battery | Bench supply ramped down slowly in place of the cell | Warning at 3.5 V; dosing refused with an alarm at 3.4 V; a dose in progress ends cleanly |
| BT-03 | Charging | Charge from 3.4 V, logging voltage, current and cell temperature | Ends at 4.20 ± 0.05 V; cell warms by less than 10 K |
| BT-04 | Wear | Five full syringes (500 U) of mixed delivery, then repeat DA-03, MT-04 and MF-01 | Mean dose moved by less than 1 %; step length and friction within 10 % of their first values |
| BT-05 | Heat | Prime continuously for 10 min; thermometer or thermal camera on both boost stages, PMD401, motor and syringe | Nothing above 60 °C; syringe warms by less than 1 K |

!table tab:app33 | Checks run once, then only after a change | 3,3
| Check | Redo only when |
| --- | --- |
| Encoder direction and count integrity (IF-05) | Encoder wiring or timer setup changes |
| SPI mode, bit order, rate scale (IF-03, MT-03) | PMD401 settings or the SPI driver change |
| PMD401 pull-up voltage (IF-02) | Never again for the same driver board |
| INA219 accuracy (IF-07) | The module is replaced |
| Plunger friction and volume calibration (MF-01, DA-02) | A different syringe is fitted. Do both per syringe, not per session |
| Kill path (all SG checks) | Any change to enable wiring or supervisor firmware. This one is always rerun in full |

@appendix Bills of Materials {#app:bom}
## Rev A bench build (37 lines)
Reproduced from `requirements/COMPONENTS_AND_BOM.md` section 1.

!table tab:app34 | Rev A parts: 1.1 Motion and fluid | 0.4,2.6,0.5,2,2.2
| # | Part | Qty | Job | Rating to check against |
| --- | --- | --- | --- | --- |
| 1 | PiezoMotor Piezo LEGS LL06 linear motor, item code **LL06A0-101M1G1E2** (guided, 100.8 mm rod, front adapter, 80 nm encoder = option E2) | 1 | Pushes the plunger | 6.5 N stall, 0–3 N working load, 48 V max drive, encoder quadrature at 3.3–5 V |
| 2 | PiezoMotor **PMD401** driver (in the Starter Kit) | 1 | Makes the four 0–48 V phase waveforms | 48 V ±5 %, 6 mA idle, ≤ 100 mA, SPI mode 3, stops after about 10 ms without data |
| 3 | Starter Kit motor cable, encoder cable, 48 V supply | 1 set | First motor bring-up before the battery chain is trusted | Supply inside 45.6–50.4 V |
| 4 | Hamilton **1001 TLL** gastight syringe, PN **81320** | 1 (2 advised) | Reservoir | 1 mL, 4.61 mm bore, 60 mm stroke, PTFE Luer lock, 13.8 bar |
| 5 | Disposable 1 mL syringes | 5 | Fit trials so the Hamilton is not scratched | none |
| 6 | Luer 3-way stopcock and short extension line | 2 sets | Joins syringe, transducer and outlet; the stopcock is the test occlusion | Luer lock |

!table tab:app35 | Rev A parts: 1.2 Control | 0.4,2.6,0.5,2,2.2
| # | Part | Qty | Job | Rating to check against |
| --- | --- | --- | --- | --- |
| 7 | ST **NUCLEO-WBA55CG** | 1 | Main MCU: BLE, dose control, encoder counter, PMD401 link | 1.71–3.6 V; external 3.3 V goes to JP2 pin 2 with JP2 removed |
| 8 | ST **NUCLEO-C031C6** | 1 | Supervisor: heartbeat check, park line, 48 V veto | 2.0–3.6 V; external 3.3 V through its IDD jumper |
| 9 | **MAX3485** TTL-to-RS-485 module, 3.3 V | 1 | Setup link to the PMD401 | 3.0–3.6 V supply |
| 10 | USB-to-RS-485 adapter | 0–1 | Only for driving the PMD401 from DriveLab on a PC | optional |

!table tab:app36 | Rev A parts: 1.3 Battery and protection | 0.4,2.6,0.5,2,2.2
| # | Part | Qty | Job | Rating to check against |
| --- | --- | --- | --- | --- |
| 11 | Molicel **INR18650-P28A** cell | 1 (second optional) | Only power source | 2800 mAh, 3.0–4.2 V, high-drain. No built-in protection |
| 12 | 18650 holder with leads | 1 | Swappable cell | carries 2.1 A |
| 13 | 1S protection board, 5 A | 1 | Over-discharge, over-current, short | 5 A, above the 2.1 A peak |
| 14 | **TP4056** USB-C charger, protected type | 1 | Charging only | ends at 4.2 V; its own cut-off near 3 A is why the load does not run through it |
| 15 | Inline blade fuse holder | 1 | Wiring short protection | fits a 5 A blade fuse |
| 16 | 5 A blade fuses | 1 pack | | 32 V |
| 17 | Toggle switch | 1 | Master on/off | ≥ 5 A DC |
| 18 | **INA219** current monitor module | 1 | Battery voltage and current for the 3.4 V cut-off and the power budget | 0.1 Ω shunt (marked R100), reads to 3.2 A, 26 V bus |

!table tab:app37 | Rev A parts: 1.4 3.3 V rail | 0.4,2.6,0.5,2,2.2
| # | Part | Qty | Job | Rating to check against |
| --- | --- | --- | --- | --- |
| 19 | Microchip **MCP1700-3302E/TO** LDO (TO-92) | 1 | 3.3 V for both MCUs, INA219, MAX3485 | ≤ 6 V in, 250 mA, 1.6 µA quiescent |
| 20 | 1 µF ceramic capacitor | 2 | LDO input and output | ≥ 10 V |

!table tab:app38 | Rev A parts: 1.5 48 V rail | 0.4,2.6,0.5,2,2.2
| # | Part | Qty | Job | Rating to check against |
| --- | --- | --- | --- | --- |
| 21 | Pololu **U3V70F12** step-up (F12 variant of the U3V70x family) | 1 | 3.7 → 12 V; its enable pin is the kill switch | ≥ 2.9 V in; output disconnects when disabled. EN has a 100 kΩ pull-up to VIN on the module; off level 0.4 V |
| 22 | Analog Devices **DC2628A** (LT8362 demo board) | 1 | 12 → 48 V | 10–36 V in, 46.5–49.5 V out |
| 23 | 47 µF / 100 V radial electrolytic | 1 | Replaces the DC2628A's stock 33 µF / 50 V output capacitor; soldered across the VOUT/GND turrets | 100 V |
| 24 | 100 µF / 100 V low-ESR radial electrolytic | 1 | Bulk capacitor at the PMD401 input | 100 V |
| 25 | 220 µF / 16 V low-ESR radial electrolytic | 1 | Pololu input, next to the battery line | 16 V |
| 26 | 47 µF / 25 V radial electrolytic | 1 | DC2628A input | 25 V |

!table tab:app39 | Rev A parts: 1.6 Enable logic, protection, wiring | 0.4,2.6,0.5,2,2.2
| # | Part | Qty | Job | Rating to check against |
| --- | --- | --- | --- | --- |
| 27 | **BSS138** N-MOSFET with SOT-23 (to DIP) adapter | 1 | Supervisor veto on the boost enable | 50 V, sees ≤ 4.2 V |
| 28 | 4.7 kΩ resistor | 3 | Enable pull-down (1); I²C pull-ups to 3.3 V (2) | through-hole (10 Oct list) |
| 29 | 1 kΩ resistor | 1 | Main MCU pin to enable, so the supervisor can overpower it | |
| 30 | 10 kΩ resistor | 1 | BSS138 gate default. Direction (pull-down as wired, or pull-up as proposed) is OPEN, see `OPEN_QUESTIONS.md` item 3 | |
| 31 | TVS diodes (3.3–5 V) and 100 Ω resistors | 1 kit | Protection on PMD401 signal lines | required by the PMD401 manual |
| 32 | **XT30** connector pairs | 2 | Battery lead and 48 V lead | polarised |
| 33 | Silicone wire, 18 AWG and 22 AWG | 2 m + 3 m | 18 AWG on the battery side; 22 AWG for 3.3 V, signals and the 48 V line (≤ 100 mA) | 2.1 A on 18 AWG |
| 34 | Ohmite **20J470E**, 470 Ω / 10 W | 1 | Dummy load for the 48 V rail (about 102 mA, 4.9 W) | 10 W |

!table tab:app40 | Rev A parts: 1.7 Bench reference instruments | 0.4,2.6,0.5,2,2.2
| # | Part | Qty | Job | Limit to remember |
| --- | --- | --- | --- | --- |
| 35 | Disposable IBP (invasive blood pressure) transducer | 2 | Reference pressure to judge the sensorless estimate | reads −50 to 300 mmHg only; survives ≥ 4000 mmHg |
| 36 | **HX711** breakout | 2 | 24-bit reader for the transducer | gain 128; 10 or 80 samples/s |
| 37 | NewAE **ChipWhisperer-Husky** | 0–1 | Glitch testing, stretch goal | optional |

## Rev B board (144 references)
Generated from `docs/bom_detailed.csv` (kicad-cli export at `pcb-p6-final`). The per-part justification is in the `Note` field of that file and in `scripts/design.py`. DNP = not fitted.

!table tab:app41 | Rev B bill of materials | 0.8,1.6,2.6,1,0.5
| Ref | Value | MPN | Status | DNP |
| C101 | 2.2uF/25V | – | DS |  |
| C102 | 1uF/10V | – | DS |  |
| C103 | 10uF/10V | – | DS |  |
| C104 | 100nF | – | CALC |  |
| C201 | 4.7uF/10V | – | DS |  |
| C202 | 10uF/10V | – | DS |  |
| C301 | 220uF/16V | – | DECIDED |  |
| C302 | 10uF/10V X5R | – | CALC |  |
| C303 | 10uF/10V X5R | – | CALC |  |
| C304 | 2.2uF/10V | – | DS |  |
| C305 | 1uF/10V X7R | – | CALC |  |
| C306 | 180nF | – | CALC |  |
| C307 | 3.3nF | – | CALC |  |
| C308 | 100nF/50V X7R | – | CALC |  |
| C309 | 2.2uF/100V X7R | – | CALC |  |
| C310 | 2.2uF/100V X7R | – | CALC |  |
| C311 | 47uF/100V | – | DECIDED |  |
| C312 | 100pF/250V C0G | – | CALC |  |
| C313 | 10nF | – | CALC |  |
| C314 | TBD | – | PLACEHOLDER | DNP |
| C501 | 100nF | – | ASSUMED |  |
| C502 | 100nF | – | ASSUMED |  |
| C503 | 100nF | – | ASSUMED |  |
| C504 | 100nF | – | ASSUMED |  |
| C505 | 100nF | – | DS |  |
| C506 | 10uF/10V | Murata GRM188C81A106MA73 | DS |  |
| C507 | 10uF/10V | – | DS |  |
| C508 | 100nF | – | DS |  |
| C509 | 4.7uF | Murata GRM155R60J475ME47D | DS |  |
| C510 | 470nF | – | DS |  |
| C511 | 100nF | – | DS |  |
| C512 | 100nF | – | DS |  |
| C513 | 100nF | – | DS |  |
| C518 | 6pF C0G | – | DS |  |
| C519 | 6pF C0G | – | DS |  |
| C520 | 1uF | – | DS |  |
| C521 | 1uF | – | DS |  |
| C601 | 100nF | – | ASSUMED |  |
| C602 | 100nF | – | ASSUMED |  |
| C603 | 4.7uF | – | ASSUMED |  |
| C604 | 100nF | – | ASSUMED |  |
| C701 | 100nF | – | ASSUMED |  |
| C702 | 100uF/100V | – | DECIDED |  |
| C703 | 100nF | – | ASSUMED |  |
| D301 | PNE20010ER | Nexperia PNE20010ER | DS |  |
| D302 | PMEG10020ELR | Nexperia PMEG10020ELR | DS |  |
| D303 | BZX84B51 | Vishay BZX84B51-E3-08 | CALC |  |
| D304 | SMAJ15A | Littelfuse SMAJ15A | CALC |  |
| D501 | LED_GRN | – | ASSUMED |  |
| D601 | LED_RED | – | ASSUMED |  |
| D701 | PESD5V0S1BA | Nexperia PESD5V0S1BA,115 | DS |  |
| D702 | PESD5V0S1BA | Nexperia PESD5V0S1BA,115 | DS |  |
| D703 | PESD5V0S1BA | Nexperia PESD5V0S1BA,115 | DS |  |
| D704 | PESD5V0S1BA | Nexperia PESD5V0S1BA,115 | DS |  |
| D705 | PESD5V0S1BA | Nexperia PESD5V0S1BA,115 | DS |  |
| D706 | PESD5V0S1BA | Nexperia PESD5V0S1BA,115 | DS |  |
| D707 | PESD5V0S1BA | Nexperia PESD5V0S1BA,115 | DS |  |
| D708 | PESD5V0S1BA | Nexperia PESD5V0S1BA,115 | DS |  |
| D709 | PESD5V0S1BA | Nexperia PESD5V0S1BA,115 | DS |  |
| F101 | 5A | – | TBD |  |
| FB501 | 47R@100MHz | Taiyo Yuden LSMGA160808T470RG | DS |  |
| FB502 | 47R@100MHz | Taiyo Yuden LSMGA160808T470RG | DS |  |
| FL501 | MLPF-WB-04D3 | ST MLPF-WB-04D3 | DS |  |
| J101 | BATTERY_1S | AMASS XT30PW-M | ASSUMED |  |
| J102 | MASTER_SW_EXT | – | ASSUMED |  |
| J103 | USB_C_PWR | GCT USB4125 | ASSUMED |  |
| J501 | U.FL | Hirose U.FL-R-SMT-1 | ASSUMED |  |
| J502 | SWD_10pin | – | ASSUMED |  |
| J503 | CONSOLE | – | ASSUMED |  |
| J601 | SWD_10pin | – | ASSUMED |  |
| J701 | PMD401_SERVO | JST SM06B-SRSS-TB | DS |  |
| J702 | PMD401_STATUS | JST SM04B-SRSS-TB | DS |  |
| J703 | PMD401_48V | JST SM02B-SRSS-TB | DS |  |
| J704 | PMD401_RS485 | JST SM03B-SRSS-TB | DS |  |
| J705 | LL06_ENCODER | JST SM06B-SRSS-TB | ASSUMED |  |
| JP301 | BRIDGED | – | CALC |  |
| JP701 | ENC_VCC_SEL | – | ASSUMED |  |
| L201 | 2.2uH | Murata DFE201612E-2R2M=P2 | DS |  |
| L501 | 2.2uH | Murata LQM21PN2R2MGH | DS |  |
| L503 | 10nH | Murata LQG15HS10NJ02D | DS |  |
| Q301 | AONR34332C | AOS AONR34332C | DS |  |
| Q304 | BSS138 | BSS138 (e.g. Nexperia BSS138P) | CALC |  |
| Q401 | BSS138 | BSS138 | DECIDED |  |
| Q402 | BSS138 | BSS138 (e.g. Nexperia BSS138P) | DECIDED |  |
| Q701 | BSS138 | BSS138 (e.g. Nexperia BSS138P) | DS |  |
| Q702 | BSS138 | BSS138 (e.g. Nexperia BSS138P) | DS |  |
| R101 | 10k | – | DS |  |
| R102 | 5.1k | – | ASSUMED |  |
| R103 | 5.1k | – | ASSUMED |  |
| R104 | 10k | – | DS |  |
| R105 | 10k | – | DS |  |
| R106 | 10k | – | DS |  |
| R107 | 200k 1% | – | CALC |  |
| R108 | 200k 1% | – | CALC |  |
| R201 | 267k 1% | – | DS |  |
| R301 | 73.2k 1% | – | CALC |  |
| R302 | 100k | – | ASSUMED |  |
| R303 | 3.01k 1% | – | CALC |  |
| R305 | 22m 1% 1W | – | CALC |  |
| R306 | 330R 1W | – | CALC |  |
| R307 | 470k 0.1% | – | CALC |  |
| R308 | 10k 0.1% | – | CALC |  |
| R311 | 0R | – | ASSUMED |  |
| R312 | 10k 1% 1W | – | CALC |  |
| R313 | 220R 1206 | – | CALC |  |
| R314 | 1k | – | CALC |  |
| R315 | 10k | – | CALC |  |
| R316 | TBD | – | PLACEHOLDER | DNP |
| R317 | TBD | – | PLACEHOLDER | DNP |
| R401 | 4.7k | – | DECIDED |  |
| R402 | 1k | – | DECIDED |  |
| R403 | 10k | – | DECIDED |  |
| R405 | 10k | – | DECIDED |  |
| R501 | 10k | – | ASSUMED |  |
| R502 | 1k | – | ASSUMED |  |
| R513 | 0R | – | DS | DNP |
| R601 | 1k | – | ASSUMED |  |
| R701 | 0R | – | ASSUMED |  |
| R702 | 1k | – | CALC |  |
| R703 | 1k | – | CALC |  |
| R704 | 1k | – | CALC |  |
| R705 | 100R | – | DECIDED |  |
| R706 | 100R | – | DECIDED |  |
| R707 | 100R | – | DECIDED |  |
| R708 | 100R | – | DECIDED |  |
| R709 | 100R | – | DECIDED |  |
| R710 | 100R | – | DECIDED |  |
| R711 | 100R | – | DECIDED |  |
| R712 | 100R | – | DECIDED |  |
| R714 | 120R | – | ASSUMED | DNP |
| R715 | 100k | – | CALC |  |
| R716 | 100k | – | CALC |  |
| R717 | 15k | – | CALC |  |
| R718 | 33k | – | CALC |  |
| R719 | 15k | – | CALC |  |
| T301 | HPH6-0090L | Coilcraft HPH6-0090L | DS |  |
| U101 | BQ25188YBGR | BQ25188YBGR | DECIDED |  |
| U201 | TPS62840DLCR | TPS62840DLCR | DECIDED |  |
| U301 | LM51551DSSR | LM51551DSSR | DECIDED |  |
| U501 | STM32WBA55CGUx | STM32WBA55CGU6 (temp suffix TBD) | DECIDED |  |
| U601 | STM32C031C6Tx | STM32C031C6T6 (package ASSUMED) | DECIDED |  |
| U701 | MAX3485 | MAX3485 SOIC-8 (suffix TBD) | DECIDED |  |
| Y501 | 32MHz | NDK NX1612SA-32MHZ-EXS00A-CS09166 | DS |  |
| Y502 | 32.768kHz | NDK NX1610SE-32.768KHZ-EXS00A-MU01501 | DS |  |

@appendix Archived Tool Reports and Re-run Outputs {#app:reports}
## KiCad reports at pcb-p6-final
!code validation/erc/pump_v2-erc.rpt | Final ERC report (kicad-cli 10.0.3)

!code validation/drc/pump_v2-drc.rpt | Final DRC report (kicad-cli 10.0.3, schematic parity, zones refilled)

!code validation/logs/p6_strict_erc.rpt | ERC with every ignored check enabled (scratch copy)

!code validation/logs/p6_netlist_audit.txt | Pad-net audit against the netlist

## Pin-map check summary
!table tab:app42 | STM32CubeMX 6.18.1 pin check, U501 STM32WBA55CGUx | 0.5,1.5,0.7,1.6,1.4,1
| Pin | CubeMX name | Type | Net | Intended | Result |
| --- | --- | --- | --- | --- | --- |
| 1 | VSSSMPS | Power | `GND` |  | power pin |
| 2 | VDDSMPS | Power | `WBA_VDDSMPS` |  | power pin |
| 3 | VLXSMPS | Power | `WBA_VLXSMPS` |  | power pin |
| 4 | PB12 | I/O | `CON_MAIN_TX` | USART1_TX | OK |
| 5 | PA8 | I/O | `ENC_B_M` | TIM2_CH2 | OK |
| 6 | PA7 | I/O | `I2C_SDA` | I2C3_SDA | OK |
| 7 | PA6 | I/O | `I2C_SCL` | I2C3_SCL | OK |
| 8 | VDDA | Power | `+3V3` |  | power pin |
| 9 | PA5 | I/O | `PMD_SS_M` | SPI3_NSS | OK |
| 10 | PA2 | I/O | `CHG_INT_N` | GPIO | OK |
| 11 | VDD | Power | `+3V3` |  | power pin |
| 12 | PA1 | I/O | `HB_S2M` | LPUART1_RX | OK |
| 13 | PA0 | I/O | `PMD_SCLK_M` | SPI3_SCK | OK |
| 14 | PB9 | I/O | `VBAT_SENSE` | ADC4_IN10 | OK |
| 15 | PB8 | I/O | `PMD_MOSI_M` | SPI3_MOSI | OK |
| 16 | PC15-OSC32_OUT | I/O | `LSE_OUT` | RCC_OSC32_OUT | OK |
| 17 | PC14-OSC32_IN | I/O | `LSE_IN` | RCC_OSC32_IN | OK |
| 18 | PC13 | I/O | `NC` |  | no function claimed |
| 19 | PB7 | I/O | `MCU_48V_EN` | GPIO | OK |
| 20 | PB6 | I/O | `ENC_A_M` | TIM2_CH1 | OK |
| 21 | PB5 | I/O | `HB_M2S` | LPUART1_TX | OK |
| 22 | VDD | Power | `+3V3` |  | power pin |
| 23 | PB4 (NJTRST) | I/O | `PMD_FAULT_M` | GPIO | OK |
| 24 | PB3 (JTDO/TRACESWO) | I/O | `MAIN_SWO` | DEBUG_JTDO-SWO | OK |
| 25 | PA15 (JTDI) | I/O | `NC` |  | no function claimed |
| 26 | PA14 (JTCK/SWCLK) | I/O | `MAIN_SWCLK` | DEBUG_JTCK-SWCLK | OK |
| 27 | PA13 (JTMS/SWDIO) | I/O | `MAIN_SWDIO` | DEBUG_JTMS-SWDIO | OK |
| 28 | PA12 | I/O | `FLY_PGOOD` | GPIO | OK |
| 29 | PA11 | I/O | `RS485_RO` | USART2_RX | OK |
| 30 | PB2 | I/O | `LED_MAIN` | GPIO | OK |
| 31 | PB1 | I/O | `RS485_DE` | USART2_DE | OK |
| 32 | PB0 | I/O | `RS485_DI` | USART2_TX | OK |
| 33 | PB15 | I/O | `PMD_READY_M` | GPIO | OK |
| 34 | PH3-BOOT0 | I/O | `MAIN_BOOT0` | GPIO | OK |
| 35 | VDD | Power | `+3V3` |  | power pin |
| 36 | NRST | Reset | `MAIN_NRST` | <Reset> | OK |
| 37 | RF | MonoIO | `RF_MCU` | <MonoIO> | OK |
| 38 | VDDHPA | Power | `WBA_VDDHPA` |  | power pin |
| 39 | VDDANA | Power | `WBA_VDD11` |  | power pin |
| 40 | VDDRF | Power | `+3V3` |  | power pin |
| 41 | OSC_OUT | I/O | `HSE_OUT` |  | unchecked |
| 42 | OSC_IN | I/O | `HSE_IN` |  | unchecked |
| 43 | VDDRFPA | Power | `WBA_VDDRFPA` |  | power pin |
| 44 | VDD | Power | `+3V3` |  | power pin |
| 45 | VDD11 | Power | `WBA_VDD11` |  | power pin |
| 46 | PA10 | I/O | `NC` |  | no function claimed |
| 47 | PA9 | I/O | `NC` |  | no function claimed |
| 48 | PB14 | I/O | `ENC_I_M` | GPIO | OK |
| 49 | VSS (exposed pad) | Power | `GND` |  | power pin |

!table tab:app43 | STM32CubeMX 6.18.1 pin check, U601 STM32C031C6Tx | 0.5,1.5,0.7,1.6,1.4,1
| Pin | CubeMX name | Type | Net | Intended | Result |
| --- | --- | --- | --- | --- | --- |
| 1 | PC13 | I/O | `NC` |  | no function claimed |
| 2 | PC14-OSCX_IN (PC14) | I/O | `NC` |  | no function claimed |
| 3 | PC15-OSCX_OUT (PC15) | I/O | `NC` |  | no function claimed |
| 4 | PF3 | I/O | `NC` |  | no function claimed |
| 5 | VREF+ | MonoIO | `+3V3` |  | unchecked |
| 6 | VDD/VDDA | Power | `+3V3` |  | power pin |
| 7 | VSS/VSSA | Power | `GND` |  | power pin |
| 8 | PF0-OSC_IN (PF0) | I/O | `NC` |  | no function claimed |
| 9 | PF1-OSC_OUT (PF1) | I/O | `NC` |  | no function claimed |
| 10 | PF2-NRST | I/O | `SUP_NRST` | <NRST> | OK |
| 11 | PA0 | I/O | `NC` |  | no function claimed |
| 12 | PA1 | I/O | `NC` |  | no function claimed |
| 13 | PA2 | I/O | `HB_S2M` | USART2_TX | OK |
| 14 | PA3 | I/O | `HB_M2S` | USART2_RX | OK |
| 15 | PA4 | I/O | `NC` |  | no function claimed |
| 16 | PA5 | I/O | `NC` |  | no function claimed |
| 17 | PA6 | I/O | `ENC_A_S` | TIM3_CH1 | OK |
| 18 | PA7 | I/O | `ENC_B_S` | TIM3_CH2 | OK |
| 19 | PB0 | I/O | `SUP_VETO` | GPIO | OK |
| 20 | PB1 | I/O | `SUP_PARK` | GPIO | OK |
| 21 | PB2 | I/O | `LED_SUP` | GPIO | OK |
| 22 | PB10 | I/O | `NC` |  | no function claimed |
| 23 | PB11 | I/O | `NC` |  | no function claimed |
| 24 | PB12 | I/O | `NC` |  | no function claimed |
| 25 | PB13 | I/O | `NC` |  | no function claimed |
| 26 | PB14 | I/O | `NC` |  | no function claimed |
| 27 | PB15 | I/O | `NC` |  | no function claimed |
| 28 | PA8 | I/O | `NC` |  | no function claimed |
| 29 | PA9/NC | I/O | `CON_SUP_TX` | USART1_TX | OK |
| 30 | PC6 | I/O | `NC` |  | no function claimed |
| 31 | PC7 | I/O | `NC` |  | no function claimed |
| 32 | PA10/NC | I/O | `CON_SUP_RX` | USART1_RX | OK |
| 33 | PA11 [PA9]/PA9 [PA11] | I/O | `NC` |  | no function claimed |
| 34 | PA12 [PA10]/PA10 [PA12] | I/O | `NC` |  | no function claimed |
| 35 | PA13 | I/O | `SUP_SWDIO` | DEBUG_SWDIO | OK |
| 36 | PA14-BOOT0 | I/O | `SUP_SWCLK` | DEBUG_SWCLK | OK |
| 37 | PA15 | I/O | `NC` |  | no function claimed |
| 38 | PD0 | I/O | `NC` |  | no function claimed |
| 39 | PD1 | I/O | `NC` |  | no function claimed |
| 40 | PD2 | I/O | `NC` |  | no function claimed |
| 41 | PD3 | I/O | `NC` |  | no function claimed |
| 42 | PB3 | I/O | `NC` |  | no function claimed |
| 43 | PB4 | I/O | `NC` |  | no function claimed |
| 44 | PB5 | I/O | `NC` |  | no function claimed |
| 45 | PB6 | I/O | `NC` |  | no function claimed |
| 46 | PB7 | I/O | `NC` |  | no function claimed |
| 47 | PB8 | I/O | `NC` |  | no function claimed |
| 48 | PB9 | I/O | `NC` |  | no function claimed |

## Outputs re-run for this report (20 Nov 2026)
!code docs/project_report/evidence/design_calcs.txt | Output of scripts/review/design_calcs.py

!code docs/project_report/evidence/lm51551_startup.txt | Output of validation/sim/lm51551_startup.py

!code docs/project_report/evidence/flyback_layout_sens.txt | Output of scripts/review/run_flyback_sens.sh (ngspice 42)

!code docs/project_report/evidence/rf_line_solver.txt | Output of validation/sim/rf_line_solver.py

!code docs/project_report/evidence/rf_eco1_widths.txt | Output of rf_line_solver.solve() at the two as-built widths

!code docs/project_report/evidence/sch_netlist_check.txt | Output of scripts/review/sch_netlist_check.py

!code docs/project_report/evidence/energy_estimate.txt | Output of scripts/report_energy_estimate.py

## Simulation logs
!code validation/sim/flyback_openloop.log | LTspice open-loop flyback log

!code validation/sim/q301/RESULTS.md | Q301 stress results

@appendix Code Listings {#app:code}
## v1 HybridPancreasSim (C++)
!box Pending. | The v1 C++ sources (`BergmanModel.h`, `Controllers.h` and the rest of the merged codebase) and the v2 reference firmware (`pump_fw.zip`) will be listed here once they are committed to the repository. They are not reproduced from memory.

## Project scripts
The table lists every script in the repository with its length and purpose. The scripts that define the circuit or produce the numbers in Chapter 5 are listed in full after it.

!table tab:app44 | Scripts in the repository | 2.6,0.6,3.6
| Script | Lines | Purpose |
| `scripts/build_project_report.py` | 581 | Builds this report (DOCX and PDF) |
| `scripts/compare_placement.py` | 205 | Compares placement variants |
| `scripts/compare_stage.py` | 79 | Compares a routing stage with its checkpoint |
| `scripts/design.py` | 471 | Single source of truth: every part, value, footprint, net, status and note |
| `scripts/eval_placement.py` | 135 | Scores placement variants on scratch copies |
| `scripts/gen_library.py` | 266 | Writes the project symbol and footprint library |
| `scripts/gen_pcb.py` | 775 | Board outline, placement, planes, fan-out, Specctra DSN/SES exchange |
| `scripts/gen_schematic.py` | 344 | Writes the 8 schematic sheets and net classes |
| `scripts/grid_route.py` | 270 | Grid router for staged connections |
| `scripts/hand_route.py` | 181 | Applies explicit routes from the DRC report |
| `scripts/kicadlib.py` | 185 | KiCad S-expression helpers |
| `scripts/pcb_eco.py` | 248 | Applies footprint and placement changes after an ECO |
| `scripts/pcb_outline.py` | 24 | Board outline change |
| `scripts/pcb_rf_mask.py` | 16 | Opens the solder mask over the RF line |
| `scripts/pcb_silk.py` | 163 | Silkscreen clean-up |
| `scripts/reconcile_unrouted.py` | 120 | Classifies unconnected items |
| `scripts/report_appendix.py` | 223 | Generates these appendices |
| `scripts/report_energy_estimate.py` | 71 | Energy estimate of Chapter 5 |
| `scripts/report_figures.py` | 393 | Figures of this report |
| `scripts/review_clearance.py` | 85 | Clearance margins along routes |
| `scripts/route_stage.py` | 221 | Applies a reviewed JSON route stage |
| `scripts/run_checks.sh` | 27 | ERC, DRC with parity, BOM export |
| `scripts/unrouted_corridors.py` | 71 | Finds free straight corridors for unrouted pairs |
| `scripts/verify_pinmap.py` | 101 | Checks MCU pin functions against the STM32CubeMX database |
| `scripts/review/design_calcs.py` | 68 | Independent review checker |
| `scripts/review/flyback_layout_sens.cir.tmpl` | 48 | Independent review checker |
| `scripts/review/pcb_check.py` | 212 | Independent review checker |
| `scripts/review/run_flyback_sens.sh` | 7 | Independent review checker |
| `scripts/review/sch_netlist_check.py` | 57 | Independent review checker |
| `scripts/review/sexp.py` | 16 | Independent review checker |
| `validation/sim/lm51551_startup.py` | 106 | Simulation model |
| `validation/sim/rf_line_solver.py` | 54 | Simulation model |

!code scripts/design.py | Listing F.1: scripts/design.py (circuit definition)

!code validation/sim/lm51551_startup.py | Listing F.2: LM51551 cycle-by-cycle start-up model

!code validation/sim/rf_line_solver.py | Listing F.3: 2-D finite-difference RF line solver

!code scripts/review/design_calcs.py | Listing F.4: independent design calculations

!code scripts/verify_pinmap.py | Listing F.5: MCU pin-map check against STM32CubeMX

!code scripts/run_checks.sh | Listing F.6: KiCad check script

!code scripts/report_energy_estimate.py | Listing F.7: energy estimate

@appendix Repository Map and Reproduction {#app:files}
Repository: `BigBiglinn/INSULIN_PUMP`, branch `master` at the merge of pull request #2 (commit `38cb21c`). Design of record: tag `pcb-p6-final`.

!table tab:app45 | Repository map | 2.4,4
| Path | Content |
| `PROJECT_OVERVIEW.md`, `CLAUDE.md` | Project purpose, rules and workflow |
| `requirements/` | Design requirements, hardware constraints, components and BOM, open questions, validation plan |
| `decisions/DECISION_LOG.md` | Every decision with date, rationale and status |
| `hardware/kicad/` | KiCad 10 project: 8 schematic sheets, 4-layer PCB, project library, rules |
| `scripts/` | Design source, generators, routing tools, checks, report builders |
| `validation/erc`, `validation/drc` | kicad-cli reports |
| `validation/sim` | LTspice decks and logs, start-up model, RF solver, Q301 study |
| `validation/routing`, `validation/placement`, `validation/logs` | Stage specifications, comparisons and logs |
| `docs/handover/` | Handover guide, status, ECO records, PCB stages, assumptions, unresolved issues |
| `docs/review/` | Independent design review |
| `docs/datasheets/` | Datasheets actually used (PMD401, LM51551, BQ25188, TPS62840, CSD16340Q3, PNE20010ER, PMEG10020ELR, BSS138, INA219) |
| `docs/project_report/` | This report, its source, figures and the re-run evidence |

To regenerate this report and its evidence from the repository root:

!codeblock
python scripts/review/sch_netlist_check.py > docs/project_report/evidence/sch_netlist_check.txt
python scripts/review/pcb_check.py        > docs/project_report/evidence/pcb_check.txt
python scripts/review/design_calcs.py     > docs/project_report/evidence/design_calcs.txt
sh scripts/review/run_flyback_sens.sh     > docs/project_report/evidence/flyback_layout_sens.txt   # ngspice >= 42
(cd validation/sim && python lm51551_startup.py) > docs/project_report/evidence/lm51551_startup.txt
(cd validation/sim && python rf_line_solver.py)  > docs/project_report/evidence/rf_line_solver.txt
python scripts/report_energy_estimate.py
python scripts/report_figures.py
python scripts/report_appendix.py
python scripts/build_project_report.py        # needs LibreOffice, poppler-utils, python-docx
bash scripts/run_checks.sh                    # KiCad 10.0.x: ERC, DRC with parity, BOMs
!endcode

