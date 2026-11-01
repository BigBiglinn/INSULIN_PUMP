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

## 7. Routing decisions, 11 Oct 2026 (Claude Code session, branch `placement-opt`)

Full wording and context: `docs/handover/CURRENT_STATUS.md` §5 and `docs/handover/ROUTING_STAGES.md`.

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

## 8. Schematic ECO1, 31 Oct 2026

Full record: `docs/handover/ECO1_SCHEMATIC.md`.

| Date | Decision | Rationale | Status |
| --- | --- | --- | --- |
| 31 Oct | Objective is now a fabricated, working bench prototype; owner approved the recommended architecture where evidence supports it and asked for schematic implementation. K-7 Rev A gate: owner has not separately waived it in writing | Owner instruction | DECIDED (owner) for ECO1; K-7 waiver OPEN |
| 31 Oct | ECO1: WBA55 supplies per DS14127 Fig. 15; MLPF-WB-04D3; HPH6-0090L; 1 uF soft start; 10 k bleeder; SMBJ48A clamp; K-12 switched output removed; READY/FAULT level shifters; LSE fitted; no MCU pin changes | Verification in ECO1_SCHEMATIC.md | IMPLEMENTED in schematic; PCB pending owner review |

## 9. Digital completion, 1 Nov 2026

Owner instruction in this session: the board will not be fabricated, it only has to be complete and error-free digitally, and open choices are to be made without further questions.

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
