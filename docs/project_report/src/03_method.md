# Methodology and System Design {#ch:method}

## Engineering workflow

### Phased process

The work followed a seven-phase workflow, fixed in the project instructions (`CLAUDE.md`) before any design began ({tab:phases}). A phase may be skipped only with a documented reason and the owner's approval. Phase 6 (manufacturing outputs) was formally removed on 1 November 2026, when the owner decided that the board would not be fabricated.

!table tab:phases | Engineering phases and their status at the end of the project | 1,4,3
| Phase | Content | Status |
| 0 | Discover tools, inspect inputs, establish the requirements register | Done (requirements/, 10 Oct 2026) |
| 1 | Block diagram, power architecture, interface list, Bluetooth options, preliminary BOM, risk register | Done |
| 2 | Verify component selection; design the schematic | Done, with TBD items recorded |
| 3 | Validate schematic and BOM before layout | Done in software (ERC, netlist audit, pin-map check) |
| 4 | Footprints, manufacturing constraints, stack-up, placement, routing | Done digitally; fab rules and some footprint drawings open |
| 5 | ERC, DRC, parity, power and thermal calculations, simulations | Done in software; thermal and control-loop simulation open |
| 6 | Manufacturing outputs after release review | Not applicable: no fabrication (owner, 1 Nov 2026) |

### Rules of evidence

Seven rules governed every step. Several of them shaped this report directly:

1. Never invent requirements, component data, pin mappings, package dimensions or validation results.
2. Keep verified facts, engineering assumptions, proposed choices and unresolved questions separate.
3. Do not fix layer count, board size, battery voltage, radio architecture or regulators before the requirements are analysed.
4. Prefer official datasheets, reference manuals, errata and verified footprints.
5. Preserve the original requirements and keep a decision log.
6. Create a recoverable checkpoint (a git commit or tag) before modifying a known-good design.
7. Never claim that an artifact was generated or a test passed without checking the actual file or tool output.

The handoff documents label every statement CONFIRMED, DECIDED, PROPOSED, ASSUMPTION, OPEN or SUPERSEDED. Rule 6 produced a dense set of git tags (for example `route-stage1-before`, `sch-eco1-done`, `pcb-p6-final`). Every routing or schematic stage can therefore be compared with, or restored to, the state before it.

### Status of every component value {#sec:status}

Every part in the design carries a `Status` field, which appears in the schematic, the BOM and the PCB:

- **DECIDED**: locked in the handoff documents;
- **DS**: value or connection taken from a cited datasheet;
- **CALC**: calculated, with the calculation in the part's Note field;
- **ASSUMED**: an engineering assumption, listed in the assumptions register;
- **TBD**: part or value not yet determined;
- **PLACEHOLDER**: block not designed.

A reader can see at a glance how much of the design rests on evidence ({fig:bomstatus}).

## Requirements

### Owner-level requirements

{tab:ownerreq} lists the owner's requirements in the owner's terms. An earlier statement (22 September 2026) fixed the success criterion: dosing accuracy within ±5 % of the commanded volume, measured gravimetrically on water.

!table tab:ownerreq | Owner-level requirements (all DECIDED) | 1,6,2
| # | Requirement | Stated |
| U-1 | Smaller device with a smaller motor than v1 | 21 Sep 2026 |
| U-2 | Everything on STM32, not ESP32 | 21 Sep 2026 |
| U-3 | More professional, close to industry grade | 21 Sep 2026 |
| U-4 | A small working prototype; correct dosing defines success; never tested on humans | 21 Sep 2026 |
| U-5 | Whole project in 30 days | 21 Sep 2026 |
| U-6 | Two stages: Rev A bench validation, then Rev B PCB | Sep 2026 |
| U-7 | 3.7 V battery → high-voltage stage → piezo driver → piezo motor; the same cell powers the STM32 | 25 Sep 2026 |
| U-8 | Piezo motor driving a positive-displacement syringe; no single-PZT valve pump | 27 Sep 2026 |
| U-9 | The project must have novelty | Sep 2026 |
| U-10 | Electronics first; mechanics only after the piezo motor runs | Sep 2026 |
| U-11 | BLE on the device: phone now, a custom CGM (another team) later | Sep 2026 |
| U-12 | Rev A powered from the 3.7 V battery, so that the power tree is proven before the PCB | 30 Sep 2026 |
| U-13 | Rev A parts from Indian websites; minimise cost where performance is not sacrificed | 30 Sep 2026 |
| U-14 | Recreate the pump's function; do not copy a commercial architecture | Sep 2026 |

### Technical requirements and derived numbers

The owner requirements were expanded into 76 numbered technical requirements in seven groups: dosing (D-01 to D-15), safety (S-01 to S-16), electrical (E-01 to E-11), mechanical (M-01 to M-10), firmware (F-01 to F-09), communication (C-01 to C-07) and Rev B PCB (P-01 to P-08). {app:req} reproduces them in full with their status. Requirements written by the design assistant from standard practice are marked **Proposed** and are not binding until the owner signs them off.

The requirements rest on a few quantities that follow from the syringe geometry and the motor data. The Hamilton 81320 syringe has a 4.61 mm bore, so its cross-sectional area is

!eq eq:area | A = π·d^{2}/4 = π × (4.61 mm)^{2}/4 = 16.69 mm^{2}

and one unit (10 µL = 10 mm^{3}) corresponds to a plunger travel of

!eq eq:travel | x_{1U} = V/A = 10 mm^{3} / 16.69 mm^{2} = 0.599 mm = 599 µm

With the 80 nm encoder, 1 U is 599 µm / 0.080 µm = 7489 counts and one count is 16.69 mm^{2} × 0.080 µm = 1.34 nL (0.00013 U). A force balance on the plunger gives the motor load caused by line pressure p:

!eq eq:force | F = p·A ;   1 bar → 10^{5} Pa × 16.69×10^{−6} m^{2} = 1.67 N

so the 6.5 N stall force limits line pressure to about 3.9 bar with zero friction, well below the syringe's 13.8 bar rating. {tab:derived} collects these numbers.

!table tab:derived | Numbers the requirements depend on (calculated or quoted, none measured) | 3,2,3
| Quantity | Value | Basis |
| Syringe bore / area | 4.61 mm / 16.69 mm² | Hamilton 81320; {eq:area} |
| 1 U (10 µL, U-100) | 599 µm = 7,489 counts | {eq:travel} |
| Smallest dose 0.05 U (0.5 µL) | 30.0 µm = 375 counts | calculation |
| One encoder count (80 nm) | 1.34 nL = 0.00013 U | calculation |
| Full syringe | 60 mm = 1.00 mL = 100 U = 750,000 counts | needs a 32-bit position |
| Force from line pressure | 0.83 N at 0.5 bar; 1.67 N at 1 bar | {eq:force} |
| Highest pressure the motor can make | about 3.9 bar (6.5 N stall, no friction) | syringe rated 13.8 bar |
| Working load limit | 3 N (friction + pressure) | LL06 recommended 0–3 N |
| No-load full step | about 4.5 µm, shrinking with load | LL06 data; PMD401 manual 5 ± 3 µm |
| Dosing speed cap | about 15 steps/s ≈ 0.11 U/s | project value (K-15) |
| Motor top speed if uncapped | 15 mm/s ≈ 25 U/s | why the speed cap is a safety item (S-06) |
| Motor rail | 48 V ±5 % (45.6–50.4 V), 6 mA idle, ≤ 100 mA | PMD401 manual |
| Battery draw (Rev A budget) | about 2.1 A at 3.0 V; about 0.11 W idle with 48 V off | not measured |
| PMD401 idle on 48 V | about 0.29 W (about 7 Wh per day if left on) | reason the rail is switched |
| Thermal expansion of a full syringe | about 0.02 U per K | water, 1 mL |

### Locked decisions

Eighteen decisions were locked by the owner and may not be changed without approval ({tab:locked}). They are constraints on everything that follows.

!table tab:locked | Locked owner decisions K-1 to K-18 | 1,7
| # | Decision |
| K-1 | Water or saline only, bench only, never on a person or an animal |
| K-2 | Piezo motor + positive-displacement syringe; no diaphragm or valve pump, no stepper, no screw |
| K-3 | Motor: Piezo LEGS LL06, item code LL06A0-101M1G1E2 (guided, 100.8 mm rod, front adapter, 80 nm encoder) |
| K-4 | Driver: PMD401, used as bought |
| K-5 | Syringe: Hamilton 1001 TLL, PN 81320 |
| K-6 | Main MCU STM32WBA55CG; supervisor STM32C031C6; STM32 only |
| K-7 | Two stages: Rev A bench first, Rev B PCB second |
| K-8 | Rev A runs from the single Li-ion cell through the real power tree |
| K-9 | Rev A power parts: Molicel INR18650-P28A, 1S 5 A protection, 5 A fuse, switch, INA219, MCP1700-3302E/TO, Pololu U3V70F12, DC2628A (LT8362), TP4056 for charging only |
| K-10 | Kill path is fail-off: 4.7 kΩ enable pull-down, main MCU through 1 kΩ, supervisor veto through one BSS138 |
| K-11 | 48 V rail on only while dosing |
| K-12 | Rev B power parts: BQ25188, LM51551 flyback, TPS62840, 1S protected cell |
| K-13 | Sensorless occlusion detection from step length; no pressure sensor on the final device |
| K-14 | Dose limits: 0.05 U minimum, 10 U maximum bolus, 15 U per rolling hour |
| K-15 | Dosing speed cap about 15 steps/s |
| K-16 | Firmware in plain C11 behind `pump_port.h`; the owner writes it from explained reference code |
| K-17 | BLE on the WBA55: phone now, the CGM team's protocol later |
| K-18 | Rev A parts from Indian websites where possible; cost cut only where performance is untouched |

## System architecture {#sec:arch}

{fig:block} shows the Rev B system as implemented. A single protected Li-ion cell feeds two converters directly. The TPS62840 buck makes the 3.3 V logic rail. The LM51551 flyback makes the 48 V motor rail, which exists only while a dose is moving. Taking the logic rail from the battery bus rather than from the boost chain keeps motor current pulses away from the logic supply. The BQ25188 charger sits on the fused battery node, and its system output is deliberately left unloaded, so that the charger is never the load path (E-09).

The main MCU commands a signed step rate to the PMD401 over SPI (servo mode) and closes the position loop itself on the LL06 encoder. Dose is tracked as an **absolute** encoder target, not as a sum of increments, so per-pulse errors cannot accumulate. The supervisor MCU receives a heartbeat from the main MCU, counts the same encoder independently (S-07), and owns two stop actions: a veto on the 48 V enable and the PMD401 park line. It cannot command motion.

!fig fig:block | docs/project_report/figures/fig_block_diagram.png | System block diagram of the Rev B board. Blue: main-MCU signals; green: supervisor signals; orange: 48 V rail and its enable. | 6.27

{tab:interfaces} lists the external interfaces of the board.

!table tab:interfaces | Interface list (Rev B) | 2,3,4
| Interface | Connector / pins | Specification |
| Battery | J101 XT30 (assumed) | 1S protected cell 3.0–4.2 V; 5 A fuse F101; external master switch on J102 |
| Charger input | J103 USB-C, power only | 5 V VBUS; 5.1 kΩ Rd on CC1/CC2 |
| PMD401 servo (SPI) | J701 JST SH 6-pin | SPI mode 3, ≤ 500 kbit/s, 16-bit signed step rate; SS; AEN (LOW = park); 1 kΩ series + TVS |
| PMD401 status | J702 JST SH 4-pin | READY (0 = ready), FAULT (1 = error), via BSS138 level shifters |
| PMD401 power | J703 JST SH 2-pin | 48 V ±5 %, ≤ 100 mA |
| PMD401 RS-485 | J704 JST SH 3-pin | set-up and read-back (`X0Y13,3`, `X0Y32`), MAX3485 |
| LL06 encoder | J705 JST SH 6-pin | quadrature A/B + index, 80 nm/count, 3.3–5 V; supply from 3V3 (JP701) |
| BLE | J501 U.FL | 2.4 GHz, 50 Ω after the MLPF-WB-04D3 filter |
| Debug | J502, J601 (10-pin 1.27 mm SWD); J503 console | one per MCU |

## Design decisions and their justification {#sec:decisions}

Each major decision is set out below in the same five steps: what was chosen, why, which alternatives were considered, the supporting calculation, and how the choice is or will be verified.

### Actuator: Piezo LEGS LL06 linear motor (K-3)

- **Chosen:** LL06A0-101M1G1E2 [20], a guided motor with a 100.8 mm rod, front adapter and the 80 nm encoder option (E2).
- **Why:** it pushes the plunger directly, with no gears and no screw (U-8, D-01). It self-locks when unpowered at more than 6.5 N, so loss of power cannot cause free flow. Its stroke covers the 60 mm syringe. With the 80 nm encoder, the smallest dose (0.05 U ≈ 30 µm) spans 375 counts, enough for closed-loop control and step-length sensing. The coarser 1.25 µm option would give only 24 counts.
- **Alternatives:** NEMA 17 with leadscrew (v1; too large), NEMA 8/11, Faulhaber AM0820 with 64:1 gearhead (interim v2 plan), Shinsei USR30-E3 ultrasonic motor (rejected on humidity, thrust load and size), New Scale Squiggle, DTI motors, PiezoMotor LT20 (superseded specification).
- **Calculation:** working load ≤ 3 N, which equals about 1.8 bar plus 1.5 N friction ({eq:force}). The speed cap of 15 steps/s × 4.5 µm ≈ 68 µm/s ≈ 0.11 U/s.
- **Verification:** MT-04 (no-load step length 2–8 µm), MT-05 (step length against load, the occlusion calibration), MT-06 (unpowered hold ≤ 6 µm under 3 N). None has been run.

### Driver: PiezoMotor PMD401 in servo mode (K-4)

- **Chosen:** the PMD401 as bought, in servo mode. The MCU sends a 16-bit signed step rate over SPI and closes the position loop on the encoder.
- **Why:** the LL06 needs four synchronised 0–48 V phase waveforms. Servo mode gives the MCU the encoder for self-sensing, and the PMD401 stops the motor by itself after about 10 ms without SPI data, which provides an independent stop path (S-03).
- **Alternatives:** TI DRV8662 and DRV2700 (single-channel, rejected); a custom piezo driver (prohibited); position mode inside the PMD401 (rejected because the MCU must see the encoder).
- **Verification:** MT-01 (servo mode survives a power cycle), IF-03 (SPI mode, bit order and speed), SG-06 (driver timeout). An important open item: the PMD401 manual gives no absolute maximum on its 48 V input ({sec:open}).

### Microcontrollers: STM32WBA55CG main, STM32C031C6 supervisor (K-6)

- **Chosen:** STM32WBA55CGU6 (Cortex-M33 with TrustZone, 1 MB flash with ECC, integrated BLE radio, UFQFPN48) as the main MCU; STM32C031C6 (Cortex-M0+, 48 MHz, LQFP48 assumed) as the supervisor.
- **Why main:** BLE is required (U-11) and an integrated radio avoids a separate module. TrustZone and ECC flash support the firmware hardening objectives (F-03, C-07). A single-core BLE stack is simpler than the dual-core STM32WB55. The NUCLEO-WBA55CG development board offers a direct path from Rev A to Rev B.
- **Why supervisor:** it differs from the main MCU in core, clock and code base, so one bug or one clock fault cannot defeat both. It has brown-out reset and two watchdogs (F-07, F-09).
- **Peripherals needed and allocated ({sec:pinmap}):** a timer in encoder mode (TIM2) for the LL06 quadrature; SPI3 to the PMD401; USART2 with a DE output for RS-485; LPUART1 for the heartbeat; I²C3 for the charger; ADC4 for battery voltage; a console UART (TX only, because the only USART1_RX pin carries the encoder); and SWD. The supervisor needs one timer in encoder mode (TIM3), one USART for the heartbeat, one USART for a console, and two GPIOs for veto and park.
- **Alternatives:** STM32U585 with an nRF52840/nRF5340 module and STM32C011 (the 25 September plan, superseded); NUCLEO-WB55RG; NUCLEO-G431RB and G474RE; ESP32 (excluded by U-2).
- **Verification:** all 41 assigned pin functions were checked against the STM32CubeMX 6.18.1 MCU database, with 0 failures ({sec:pinres}). Electrical pin properties (5 V tolerance, drive strength, leakage) still need the ST datasheets.

### 48 V stage: LM51551 non-isolated flyback (K-12)

- **Chosen:** TI LM51551 peak-current-mode controller in the datasheet's non-isolated flyback topology, with BIAS tied to VCC so that it starts from a 1S cell (≥ 2.97 V). Transformer: Coilcraft HPH6-0090L (n = 5). Switch: AOS AONR34332C (30 V).
- **Why:** a plain boost from 3.0 V to 48 V needs D ≈ 0.94, beyond the 93 % duty limit. A flyback with n = 5 runs at D = 0.70–0.77 ({eq:duty}). It also gives true shutdown: with EN low there is no DC path from VBAT to the output.
- **Alternatives:** plain boost (rejected); two cascaded modules as on Rev A (kept for Rev A only); TPS61040 boost module (50 mA against 450 mA needed, and no true output disconnect).
- **Calculation and verification:** {sec:flyback} and {sec:sims}.

### 3.3 V rail: TPS62840 buck on Rev B, MCP1700 LDO on Rev A

- **Chosen:** TPS62840DLC with VSET = 267 kΩ, giving 3.3 V. On Rev A, the MCP1700-3302E/TO.
- **Why:** the buck's quiescent current is very low, which matters for battery life (E-10). On Rev A the logic load is only about 30 mA, the LDO is cheaper, and it is quieter for ADC readings. Below about 3.4 V input the buck runs in 100 % mode, and 3V3 then follows VBAT, which is why dosing stops at 3.4 V (S-13).
- **Verification:** PW-01 and PW-11. On Rev B the inductor footprint was corrected in ECO1 ({sec:eco}).

### Charger: TI BQ25188 (K-12)

- **Chosen:** BQ25188 on VBAT_FUSED, with the SYS output carrying only its required 10 µF capacitor.
- **Why:** it supports I²C configuration and a 4.20 V regulation default (E-09). Placing it on the fused node, ahead of the master switch, keeps the load out of the charger path. The 10 kΩ TS/MR resistor follows the datasheet's "TS not used" case.
- **Open:** the default charge current is only 10 mA and the I²C watchdog resets the registers, so firmware must configure the part and keep it serviced ({sec:review}, finding F-M10).

### Wireless: BLE through a U.FL connector

- **Chosen:** the WBA55's own radio, through ST's MLPF-WB-04D3 matched filter and a 63 Ω / 50 Ω coplanar line, to a U.FL connector.
- **Why:** no separate radio module is needed (HARDWARE_CONSTRAINTS item 15). A connector avoids an unverified antenna geometry, by owner decision on 10 October.
- **Verification:** line impedance calculated with a 2-D field solver ({sec:rf}). BL-01 to BL-08 for the link and its security.

## Safety architecture {#sec:safety}

**Safe state (S-01):** 48 V rail off, motor parked and clamped. Loss of either MCU, of the heartbeat or of any rail must end in this state. {fig:killpath} shows how the copper enforces it.

!fig fig:killpath | docs/project_report/figures/fig_kill_path.png | Kill path and park path. Pull resistors set the off state in hardware (P-05); an MCU must actively drive a pin to permit 48 V or to unpark the motor. | 6.27

- **Default off.** R401 (4.7 kΩ) holds the LM51551 UVLO/EN node FLY_EN at 0 V. The main MCU raises it through R402 (1 kΩ). The resulting divider gives 3.3 V × 4.7/(4.7 + 1) = 2.72 V, above the 1.575 V UVLO maximum ({eq:killpath}).
- **Veto on by default.** Q401 (BSS138) shorts FLY_EN to ground. Its gate pull-up R403 (10 kΩ, owner decision 10 October) keeps the veto **on** whenever the supervisor is in reset, crashed with its pin high or high-impedance, or unpowered. The supervisor must drive PB0 low to permit 48 V. This reverses the Rev A pull-down, which would have let a dead supervisor give no veto (OPEN item 3, check SG-03).
- **Parked by default.** The PMD401 AEN input has an internal 22 kΩ pull-up. It is driven open-drain by Q402, whose gate pull-up R405 keeps AEN low (parked) unless the supervisor drives PB1 low. The PMD401's own pull-up sets the run level, so there is no 3.3 V versus 5 V level question.
- **Independent over-voltage trip (ECO2).** D303 (BZX84B51, 51 V zener), R314/R315/C313 and Q304 pull FLY_EN low when +48V_RAW exceeds 50.5–53.9 V. The trip is independent of the LM51551 feedback divider, so an open R307 is no longer an uncovered single fault.
- **Three stop paths (S-03):** (1) the PMD401 stops the motor after about 10 ms without SPI data; (2) the supervisor parks the motor and cuts 48 V on a bad heartbeat; (3) firmware performs a safe halt on detected corruption.

!eq eq:killpath | V_{FLY_EN} = V_{3V3}·R401/(R401 + R402) = 3.3 V × 4.7/5.7 = 2.72 V  (2.47–2.78 V for V_{3V3} = 3.0–3.37 V)

**Known gap (S-06, U-03):** the 15 steps/s speed cap is enforced only in main-MCU firmware. A main MCU that keeps its heartbeat alive while commanding full speed (about 25 U/s) would empty the syringe in about 4 s, and the supervisor would see only its own encoder count. The supervisor's encoder input (S-07) makes a rate check possible in supervisor firmware. That firmware has not been written, and single-fault check FT-02 **cannot pass** until it exists.

## Verification strategy

Three levels of validation are kept strictly apart throughout the report:

1. **Software validation:** ERC, DRC, schematic-to-PCB parity, netlist audits, pin-map checks, calculations and simulations. Done.
2. **Bench validation:** the 13 check groups of the validation plan (incoming inspection → power tree → kill path → interfaces → motor → mechanics → dose accuracy → occlusion → single-fault matrix → firmware → BLE → battery → Rev B board). Not started.
3. **Manufacturing acceptance:** fabrication, DFM review, assembly inspection. Not started; not planned.

The validation plan sets the order of the bench groups. If any kill-path (SG) check fails, testing stops, because nothing after it is meaningful until the kill path works. Dose accuracy is measured by weight, following IEC 60601-2-24 [7], AAMI TIR101 and ISO 8655-6 [23]: a 0.1 mg balance, a drift blank before every session, and 1 U = 9.98 mg of water at 0.998 g/mL. A single 0.05 U dose (0.50 mg) cannot be proven to ±5 % on a 0.1 mg balance; it needs a 0.01 mg balance or must be stated as position-verified only. {app:vplan} reproduces the full plan.
