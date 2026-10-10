# HARDWARE_CONSTRAINTS.md

Everything here is a constraint on the Rev A wiring or the Rev B schematic and layout. Labels are as defined in `PROJECT_OVERVIEW.md`. Items marked PROPOSED are not yet binding; they still need the owner's sign-off.

## 1. Mandatory constraints (DECIDED unless marked)

### 1.1 Use and safety

1. Lab prototype only. Water or 0.9 % saline. Never connect to a person or an animal. No real insulin.
2. Safe state = 48 V rail off, motor parked and clamped. Loss of either MCU, the heartbeat or any rail must end in the safe state (S-01).
3. The 48 V enable is off by default in hardware (S-02). A crashed, resetting or unpowered main MCU must leave the motor unpowered.
4. Three independent stop paths must exist (S-03): PMD401 SPI timeout (about 10 ms), supervisor park + 48 V cut on a bad heartbeat, firmware safe-halt on detected corruption.
5. The supervisor is a separate MCU with a separate code base (F-09). Do not merge its function into the main MCU.
6. Dose limits apply to every command regardless of source: 0.05 U minimum, 10 U maximum bolus, 15 U in any rolling hour (S-05, C-04).

### 1.2 Actuation and mechanics

7. Piezoelectric actuation only. LL06 pushes the plunger directly. No gears, no screw, no stepper (D-01).
8. Driver is the PMD401, used as bought. Do not design a custom piezo driver. Do not replace it with a single-channel driver (DRV8662, DRV2700).
9. Reservoir is the Hamilton 1001 TLL, PN 81320: 4.61 mm bore, 60 mm stroke (D-04).
10. Total load on the motor (friction + pressure) ≤ 3 N at the alarm point (M-02). Stall is 6.5 N.
11. Wetted parts: borosilicate glass, PTFE, Luer-lock line only (M-07).
12. Position is a 32-bit quantity: a full syringe is 750,000 counts.

### 1.3 MCUs

13. Main MCU: STM32WBA55CG (NUCLEO-WBA55CG on Rev A). Everything on STM32; no ESP32.
14. Supervisor MCU: STM32C031C6 (NUCLEO-C031C6 on Rev A).
15. BLE is provided by the WBA55's own radio. No separate BLE module.

### 1.4 Power

16. One Li-ion cell, 3.0–4.2 V, is the only power source (E-01). Rev A is powered from the battery, not from bench or USB power, so the power tree is proven before the PCB. Bench supplies are allowed only as stand-ins during the specific checks that call for them.
17. Battery path must include a protection board, a 5 A fuse and a master switch (E-01). Every part in the battery path must be rated above the 2.1 A worst-case draw (E-05).
18. The charger is for charging only and is never the load path (E-09). Rev A: do not run the load from the TP4056 output.
19. Motor rail at the PMD401 input: 48 V ±5 % = 45.6–50.4 V including ripple and a 0 → 100 mA load step (E-03). Never above 50.4 V.
20. The 48 V rail is on only while a dose moves. In the off state the load must be truly disconnected, not left at battery voltage (E-04).
21. The boost stage that carries the enable must give true shutdown (output disconnected when disabled). On Rev A this is why the Pololu U3V70F12 sits first in the chain.
22. Capacitors on the 48 V rail must be rated ≥ 100 V (E-06). The DC2628A's stock 33 µF / 50 V output capacitor must be replaced before first power.
23. Logic rail 3.3 V, never below 3.0 V while dosing (E-02). The 3.3 V rail is taken straight from the battery line, not from the boost chain, so motor current spikes do not reach it.
24. Firmware stops dosing at a cell voltage of 3.4 V (S-13).

### 1.5 Interfaces

25. TVS and about 100 Ω in series on every PMD401 signal line. MCU pins must never see more than their rated voltage (E-07).
26. Encoder A/B quadrature goes into a hardware timer counter on the main MCU, not into GPIO interrupts (E-08).
27. Rev B carries the Rev A circuit as bench-proven. Every change from Rev A must be listed and re-tested (P-01).

## 2. Prohibited choices and actions

### 2.1 Design choices that are ruled out (DECIDED)

- Any stepper, DC gearmotor, leadscrew or rack-and-pinion drive.
- A single PZT + valve (diaphragm) pump.
- Ultrasonic resonant motors (Shinsei USR30 family).
- DRV8662 or DRV2700 as the motor driver.
- ESP32 anywhere in v2.
- A boost module without true shutdown in the enable position.
- A plain boost topology for cell → 48 V on Rev B (93 % duty limit); flyback is the chosen topology.
- Running the load through the charger.
- Replacing any selected component or altering a constraint without the owner's approval.
- Everything listed under "Removed or rejected parts" in `COMPONENTS_AND_BOM.md` section 6.

### 2.2 Things the design deliberately does not have

Do not add these without approval; the 10 Oct report records them as not needed for this pump:

- Resonance tracking or drive-frequency tuning (LEGS motors are driven quasi-statically).
- Backlash compensation or screw-pitch correction.
- An anti-free-flow or anti-siphon valve.
- Motor current as a load signal (piezo legs are capacitive; step length is the signal).
- A home or limit switch.
- A pressure sensor on the final device (the IBP transducer is bench-only).
- Air-in-line or flow sensors.

### 2.3 Bench actions that are forbidden

- Do not connect the pump to a person or an animal, and do not use real insulin for any check.
- Do not short a Li-ion cell to test its protection, charge it unattended, or run the load from the TP4056 output.
- Do not feed 3.3 V into a Nucleo before the jumper change (check IN-09).
- Do not connect any PMD401 signal to an MCU pin before its pull-up voltage is measured (check IF-02).
- Do not take the 48 V rail above 50.4 V to see what the driver does.
- Do not oil the LL06 rod, force it by hand, or let it stall against the glass syringe.
- Do not run an accuracy test without the drift blank (DA-01) first, or with a visible bubble anywhere.
- Do not quote any dose-accuracy, occlusion or single-fault result taken while a kill-path check was failing.

## 3. Pin assignments

### 3.1 MCU pins: none assigned (OPEN)

**No MCU pin assignment exists for v2 anywhere in the project.** No port/pin names (PAx, PBx), timer instances or SPI/UART instances have been fixed for the NUCLEO-WBA55CG or the NUCLEO-C031C6 in the current design. The 9-stage firmware course lists "Port to the NUCLEO-WBA55CG (CubeMX, SPI on the scope, first motion)" as its last stage. Do not invent pin numbers. Pin functions must be assigned (CubeMX) and checked against both MCU datasheets before layout.

Constraints any pin assignment must meet:

- Encoder A/B on timer encoder-mode inputs. If a 16-bit timer is used, firmware extends it to 32 bits (FW-08).
- If the PMD401 pull-ups turn out to be 5 V, the PMD401 signal pins must be 5 V-tolerant or open-drain (IF-02).
- SPI in mode 3 to the PMD401.
- One UART on the main MCU for RS-485 (TX, RX, DE/RE). A separate UART for the bench console (the WBA55 has no USB device port).
- I²C for the current monitor, with 4.7 kΩ pull-ups to 3.3 V.

### 3.2 Functional connections that are fixed (DECIDED, Rev A)

| Signal | From | To | Notes |
| --- | --- | --- | --- |
| Boost enable (EN) | NUCLEO-WBA55CG GPIO, through 1 kΩ | Pololu U3V70F12 EN | Main MCU holds EN high only while dosing |
| EN default | 4.7 kΩ | EN to GND | Holds EN at about 0.19 V with a 4.2 V cell, below the 0.4 V off level (the Pololu has a 100 kΩ pull-up from EN to VIN) |
| Supervisor veto | NUCLEO-C031C6 GPIO | BSS138 gate | BSS138 drain to EN, source to GND. On = EN shorted to ground |
| Gate default | 10 kΩ | BSS138 gate | Wired as a pull-down to GND in the Rev A design. A change to a pull-up to 3.3 V is PROPOSED and OPEN (item 3) |
| Park line (AEN) | NUCLEO-C031C6 (supervisor owns it) | PMD401 AEN | AEN low = parked. Default pull direction and value OPEN (item 4) |
| Rate command | NUCLEO-WBA55CG SPI, mode 3, 16-bit signed step rate | PMD401 | ≤ 500 kbit/s until PiezoMotor confirms a higher limit |
| Setup link | NUCLEO-WBA55CG UART (TX, RX, DE/RE) → MAX3485 → RS-485 A/B | PMD401 | Used to set servo mode and read back settings |
| Encoder A/B | LL06 encoder (quadrature, 3.3–5 V) | NUCLEO-WBA55CG hardware counter | TVS + 100 Ω fitted. A second connection to a C031 timer is PROPOSED (S-07) |
| Ready, Fault | PMD401 | Main MCU | Fault or loss of Ready stops dosing |
| Heartbeat | NUCLEO-WBA55CG | NUCLEO-C031C6 | Recorded as a UART link. A changing token rather than a level is PROPOSED (F-09) |
| Current monitor | INA219 I²C | NUCLEO-WBA55CG | Two 4.7 kΩ pull-ups to 3.3 V |
| Buzzer, STOP button | Supervisor | | Not in the parts yet. PROPOSED (item 6) |

Note on ownership wording: one document says the supervisor "owns AEN and the 48 V enable". The wiring above is what is recorded: the main MCU switches EN, the supervisor can only force it low.

### 3.3 Board-level settings (CONFIRMED from the Parts List integration check)

| Board | Setting |
| --- | --- |
| NUCLEO-WBA55CG | Remove JP2. Feed external 3.3 V into JP2 pin 2 (1.8–3.3 V allowed there; ST UM3301). ST-LINK stays on USB through its level shifters |
| NUCLEO-C031C6 | Feed external 3.3 V through its IDD jumper. Exact jumper to be read from its user manual before power (IN-09) |
| DC2628A | Fit 47 µF / 100 V across the VOUT and GND turrets before first power |
| INA219 module | Shunt must read R100 (0.1 Ω) |
| PMD401 | Servo mode set over RS-485: `X0Y13,3`, then `X0Y32`. Must survive a power cycle (MT-01) |

### 3.4 Connector pinouts: not recorded (OPEN)

The PMD401 connector pinout, the LL06 encoder cable pinout and the motor cable pinout are **not recorded in the project**. They must be taken from the PMD401 Technical Manual and the delivered cables. A past note says the PMD401's encoder connector doubles as the SPI servo interface and that in servo mode the encoder wires go to the STM32; that reading was flagged as unconfirmed.

### 3.5 Historical pin data. Do not use (SUPERSEDED)

- v1 ESP32 rig: GPIO26 = STEP, GPIO27 = DIR, GPIO2 = on-board LED, A4988 driver. v1 only.
- Superseded Master Engineering Specification (LT20 / AS5311 design): TIM2 (32-bit) encoder mode, SPI1 to the PMD401 at 4 MHz with 16-bit frames, I2C1 at 400 kHz with 2.2 kΩ pull-ups, USART1 supervisor link at 115200 8E1, LPUART1 console, TIM16 1 kHz control ISR; supervisor SPI1 as SSI master, TIM3 input capture, USART2 heartbeat 100 ms with a 300 ms timeout; connectors J1–J11. These belong to a different design. They conflict with the current one in places (SPI 4 MHz against ≤ 500 kbit/s; 2.2 kΩ against 4.7 kΩ I²C pull-ups). Listed only so they are recognised if they turn up.

## 4. Power requirements

### 4.1 Rev A power tree (DECIDED)

```
Molicel INR18650-P28A  (TP4056 on B+/B-, charging only)
  -> 18650 holder
  -> 1S 5 A protection board (B+/B- in, P+/P- out)
  -> inline 5 A blade fuse (on P+)
  -> toggle switch (master)
  -> INA219 (high side, 0.1 ohm shunt)
  -> battery bus
       |-> MCP1700-3302E/TO (1 uF in, 1 uF out) -> 3.3 V: both Nucleos, INA219, MAX3485
       |-> 220 uF/16 V -> Pololu U3V70F12 (EN = kill switch) -> 12 V
              -> 47 uF/25 V -> DC2628A (LT8362) -> 48 V (47 uF/100 V at VOUT)
              -> XT30 -> 100 uF/100 V -> PMD401 -> LL06
```

### 4.2 Rails and limits

| Rail | Requirement | Source |
| --- | --- | --- |
| Cell | 3.0–4.2 V. Charge ends at 4.20 V. Dosing stops at 3.4 V; warning at 3.5 V is PROPOSED | E-01, E-09, S-13 |
| Battery current | About 2.1 A worst case at 3.0 V; about 1.7 A at 3.7 V; about 6.2 W while the motor runs. Not measured yet | Rev A power budget |
| Idle | About 0.11 W with 48 V off. Not measured yet | Rev A power budget |
| 3.3 V | 3.23–3.37 V for ≥ 3.5 V in; at least 3.0 V at 3.2 V in; never below 3.0 V while dosing. Load about 30 mA on Rev A | PW-01, E-02 |
| 12 V (Rev A only) | 11.5–12.5 V. 0 V when disabled, not the input voltage | PW-05 |
| 48 V | 45.6–50.4 V at the PMD401 input including ripple and load step. DC2628A is specified 46.5–49.5 V. 6 mA idle, ≤ 100 mA | E-03 |
| 48 V fault ceiling | Under 60 V DC in every fault. PROPOSED | E-11 |
| 48 V discharge | Below 5 V within 5 s of switch-off. PROPOSED | E-11, PW-08 |
| Voltage derating | Nothing above 80 % of its voltage rating. PROPOSED | E-06 |
| Enable node | ≤ 0.4 V = off (S-02); check limit ≤ 0.2 V with both MCUs in reset or unpowered (PW-07) | S-02 |
| Supply ranges | WBA55 1.71–3.6 V; C031 2.0–3.6 V; MAX3485 3.0–3.6 V; MCP1700 ≤ 6 V in, 250 mA; Pololu ≥ 2.9 V in; DC2628A 10–36 V in; INA219 26 V bus | Parts List voltage check |
| Shunt drop | The 0.1 Ω shunt alone drops about 0.2 V at 2 A. This eats into the LDO headroom near the 3.4 V cut-off | PW-11 |
| Rev B battery life | At least 3 days at a normal daily profile. PROPOSED | E-10 |

### 4.3 Rev B power parts (DECIDED per P-04)

BQ25188 charger; LM51551 flyback to 48 V with a switched output; TPS62840 for 3.3 V; 1S protected cell. Transformer, cell capacity and charge current are OPEN.

## 5. Interface requirements

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

## 6. Layout restrictions (Rev B PCB)

Only P-01 and P-04 are DECIDED. The rest are PROPOSED in the 10 Oct report and need sign-off before they are treated as rules.

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

Not fixed anywhere in the project: board outline and size, layer thickness and copper weight, fab house and its design rules, connector types, mounting holes, enclosure, component side(s), assembly method. See `OPEN_QUESTIONS.md`.

Layout ideas from the superseded Master Engineering Specification, for reference only (not adopted for the LL06 design): 1.6 mm 4-layer stack (L1 parts + signals, L2 solid GND, L3 3V3 and VBAT pours, L4 signals + 48 V zone); supervisor placed between the 48 V zone and the main MCU so gate traces stay short; no split planes; via array under the flyback FET; 100 nF per MCU VDD pin plus 4.7 µF bulk; Tag-Connect TC2030 SWD header per MCU.
