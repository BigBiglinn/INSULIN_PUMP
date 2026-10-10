# COMPONENTS_AND_BOM.md

Sources: 10 Oct 2026 requirements report (37-item Rev A list, Rev B list), "Insulin Pump Rev A – Parts List" and "Insulin Pump Rev A – Component Roles" (30 Sep 2026), "Piezo Insulin Pump — Rev A Final Project Report" (29 Sep 2026), PiezoMotor quotation thread (8 Oct 2026).

Rules for this file:

- Part numbers are copied exactly as recorded. Where the project only records a generic description (for example "1S protection board, 5 A"), no manufacturer part number exists in the project. Do not invent one.
- Do not substitute any selected part. Approved alternatives are listed in section 5; there are no others.
- Prices and stock are snapshots from the dates shown. Re-check before ordering.

## 1. Rev A bench build (DECIDED, list declared final 29–30 Sep 2026, restated 10 Oct 2026)

37 line items in seven groups.

### 1.1 Motion and fluid

| # | Part | Qty | Job | Rating to check against |
| --- | --- | --- | --- | --- |
| 1 | PiezoMotor Piezo LEGS LL06 linear motor, item code **LL06A0-101M1G1E2** (guided, 100.8 mm rod, front adapter, 80 nm encoder = option E2) | 1 | Pushes the plunger | 6.5 N stall, 0–3 N working load, 48 V max drive, encoder quadrature at 3.3–5 V |
| 2 | PiezoMotor **PMD401** driver (in the Starter Kit) | 1 | Makes the four 0–48 V phase waveforms | 48 V ±5 %, 6 mA idle, ≤ 100 mA, SPI mode 3, stops after about 10 ms without data |
| 3 | Starter Kit motor cable, encoder cable, 48 V supply | 1 set | First motor bring-up before the battery chain is trusted | Supply inside 45.6–50.4 V |
| 4 | Hamilton **1001 TLL** gastight syringe, PN **81320** | 1 (2 advised) | Reservoir | 1 mL, 4.61 mm bore, 60 mm stroke, PTFE Luer lock, 13.8 bar |
| 5 | Disposable 1 mL syringes | 5 | Fit trials so the Hamilton is not scratched | none |
| 6 | Luer 3-way stopcock and short extension line | 2 sets | Joins syringe, transducer and outlet; the stopcock is the test occlusion | Luer lock |

### 1.2 Control

| # | Part | Qty | Job | Rating to check against |
| --- | --- | --- | --- | --- |
| 7 | ST **NUCLEO-WBA55CG** | 1 | Main MCU: BLE, dose control, encoder counter, PMD401 link | 1.71–3.6 V; external 3.3 V goes to JP2 pin 2 with JP2 removed |
| 8 | ST **NUCLEO-C031C6** | 1 | Supervisor: heartbeat check, park line, 48 V veto | 2.0–3.6 V; external 3.3 V through its IDD jumper |
| 9 | **MAX3485** TTL-to-RS-485 module, 3.3 V | 1 | Setup link to the PMD401 | 3.0–3.6 V supply |
| 10 | USB-to-RS-485 adapter | 0–1 | Only for driving the PMD401 from DriveLab on a PC | optional |

### 1.3 Battery and protection

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

### 1.4 3.3 V rail

| # | Part | Qty | Job | Rating to check against |
| --- | --- | --- | --- | --- |
| 19 | Microchip **MCP1700-3302E/TO** LDO (TO-92) | 1 | 3.3 V for both MCUs, INA219, MAX3485 | ≤ 6 V in, 250 mA, 1.6 µA quiescent |
| 20 | 1 µF ceramic capacitor | 2 | LDO input and output | ≥ 10 V |

### 1.5 48 V rail

| # | Part | Qty | Job | Rating to check against |
| --- | --- | --- | --- | --- |
| 21 | Pololu **U3V70F12** step-up (F12 variant of the U3V70x family) | 1 | 3.7 → 12 V; its enable pin is the kill switch | ≥ 2.9 V in; output disconnects when disabled. EN has a 100 kΩ pull-up to VIN on the module; off level 0.4 V |
| 22 | Analog Devices **DC2628A** (LT8362 demo board) | 1 | 12 → 48 V | 10–36 V in, 46.5–49.5 V out |
| 23 | 47 µF / 100 V radial electrolytic | 1 | Replaces the DC2628A's stock 33 µF / 50 V output capacitor; soldered across the VOUT/GND turrets | 100 V |
| 24 | 100 µF / 100 V low-ESR radial electrolytic | 1 | Bulk capacitor at the PMD401 input | 100 V |
| 25 | 220 µF / 16 V low-ESR radial electrolytic | 1 | Pololu input, next to the battery line | 16 V |
| 26 | 47 µF / 25 V radial electrolytic | 1 | DC2628A input | 25 V |

### 1.6 Enable logic, protection, wiring

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

### 1.7 Bench reference instruments

| # | Part | Qty | Job | Limit to remember |
| --- | --- | --- | --- | --- |
| 35 | Disposable IBP (invasive blood pressure) transducer | 2 | Reference pressure to judge the sensorless estimate | reads −50 to 300 mmHg only; survives ≥ 4000 mmHg |
| 36 | **HX711** breakout | 2 | 24-bit reader for the transducer | gain 128; 10 or 80 samples/s |
| 37 | NewAE **ChipWhisperer-Husky** | 0–1 | Glitch testing, stretch goal | optional |

From the lab (not purchased): analytical balance (0.1 mg, and access to a 0.01 mg one for single small doses), oscilloscope, current-limited bench supply, multimeter, force gauge or spring scale to 5 N, calipers, dial indicator, thermometer to 0.1 K.

### 1.8 Parts with no manufacturer part number recorded

Only items 1, 2, 4, 7, 8, 11, 19, 21, 22, 27, 34 and 37 carry a manufacturer part number. Items 9, 14, 18 and 36 are named by their IC (a generic module built around it). Everything else is specified by description only. The exact TVS part, IBP transducer model, protection-board model and capacitor series were never fixed. The Parts List links for these are store listings or store searches, not part numbers.

## 2. Needed by the requirements but not in any list yet (OPEN)

| Item | Needed for | Note |
| --- | --- | --- |
| Syringe mount and plunger coupling | M-03 to M-06 | Not designed yet; all mechanics and fluid-path checks wait on it |
| Buzzer with a driver the supervisor controls | S-12 | The Nucleo LEDs cover the light on Rev A; there is no sound source |
| STOP push button wired to the supervisor | S-01, S-04 | The Nucleo user button can stand in on Rev A |
| Pull-down resistor on the PMD401 park line | S-01 | Value depends on the PMD401 pull-up, which is still to be measured |
| Reference pressure gauge or sensor, 0–2 bar | S-08 | The IBP transducer stops reading at 0.4 bar |
| Second pair of encoder inputs on the supervisor | S-07 | Wiring only, two more series resistors |

## 3. Rev B board parts (not ordered; list is DECIDED per P-04, details OPEN)

Rev B reuses the motor (item 1), the PMD401 driver (item 2) and the syringe (item 4), and replaces the dev boards and power modules with chips on one PCB.

| Part | Replaces | Open point |
| --- | --- | --- |
| ST **STM32WBA55CG** chip | NUCLEO-WBA55CG | Antenna and crystal layout from the ST reference. Full orderable part number (package, temperature suffix) not recorded |
| ST **STM32C031C6** chip | NUCLEO-C031C6 | Full orderable part number (package suffix) not recorded |
| TI **BQ25188** charger | TP4056 module | Charge current setting |
| TI **LM51551** with a flyback transformer, switched 48 V output | Pololu U3V70F12 + DC2628A | Transformer part number not chosen. Switching FET, diode and output-switch parts not chosen |
| TI **TPS62840** buck | MCP1700 LDO | 3.3 V setting resistor. Orderable variant not recorded |
| 1S protected Li-ion cell | 18650 + protection board | Capacity, from the measured power budget |
| 4-layer PCB | breadboard and wiring | Size not fixed |

Not yet on any Rev B list but implied by the requirements: the BSS138 veto FET, enable and gate resistors, TVS and 100 Ω series parts on PMD401 signals, current monitor, battery connector, PMD401 connector, encoder connector, SWD connector, test points, buzzer, STOP button. None of these has a Rev B part number or footprint decision recorded.

## 4. Key part data recorded in the project (CONFIRMED from datasheets/manuals/vendor unless marked)

### LL06 (PiezoMotor Piezo LEGS linear motor)

| Spec | Value |
| --- | --- |
| Stall force | 6.5 N |
| Holding force (unpowered) | > 6.5 N, self-locking |
| Recommended operating force | 0–3 N |
| Drive voltage | 0–48 V, four phases |
| Power | 5 mW per Hz of step rate |
| No-load full step | about 4.5 µm (PMD401 manual: 5 ± 3 µm, shrinks with load) |
| Top speed | ≤ 15 mm/s |
| Encoder (option E2) | 80 nm per count, quadrature A/B, 3.3–5 V (vendor reply, 8 Oct 2026) |
| Rod | 100.8 mm drive rod |
| Stroke | Recorded three ways: 0–77.4 mm, 74.1 mm, ≤ 73.9 mm. OPEN, see conflict CF-1 |
| Size | 23.4 × 19.6 × 10.5 mm |
| Operating temperature | −20 to +70 °C |

### PMD401 (PiezoMotor driver)

- Supply 48 V ±5 % (45.6–50.4 V); about 6 mA idle, ≤ 100 mA at full speed.
- Servo mode: takes a 16-bit signed step rate over SPI (mode 3). The MCU reads the encoder and closes the position loop.
- Stops the motor if no SPI data arrives for about 10 ms.
- AEN low parks the motor (about 250 ms). Unpark needs ≥ 80 ms.
- Ready and Fault status outputs.
- Signals are 3.3–5 V with no EMC protection; the manual requires TVS and series resistors.
- Setup over RS-485. Servo mode is set with `X0Y13,3` then `X0Y32`. SPI bit order is checked with `XE`.
- UNVERIFIED: SPI maximum speed (15 Mbit/s on the web page, 500 kbit/s in the manual), SPI word scale, bit order, pull-up rail voltage, boot time, current at dosing speed, park-input default. See `OPEN_QUESTIONS.md`.

### Hamilton 81320 (1001 TLL)

1 mL gastight, PTFE Luer lock, 4.61 mm bore, 60 mm stroke, 13.8 bar. Plunger friction is unpublished and not yet measured.

### MCU boards

| Item | NUCLEO-WBA55CG / STM32WBA55CG | NUCLEO-C031C6 / STM32C031C6 |
| --- | --- | --- |
| Core | Cortex-M33, TrustZone | Cortex-M0+, 48 MHz |
| Memory | 1 MB flash with ECC | Parity SRAM |
| Other | BLE (recorded as 5.3 in one place, 5.4 in another; see conflict CF-12). No USB device port, so the console is UART (noted in the superseded specification; confirm in the datasheet) | BOR, 2 watchdogs |
| Supply | 1.71–3.6 V | 2.0–3.6 V |
| Nucleo external 3.3 V feed | Remove JP2, feed JP2 pin 2 (ST UM3301). ST-LINK stays on USB | Through its IDD jumper (check its user manual) |

## 5. Approved alternatives (complete list; nothing else is approved)

| For | Approved alternative | Condition |
| --- | --- | --- |
| MCP1700-3302E/TO on Rev A | TI **TPS62840-1DLCEVM55** (0–1, optional) | Only to validate the Rev B buck early; set 3.3 V with Rx4 per its EVM guide. Not needed for Rev A to work |
| Molicel INR18650-P28A | A second identical cell | Optional spare |
| Hamilton 81320 | A second identical syringe | Advised spare |
| PC control of the PMD401 | USB-to-RS-485 adapter | Optional; the MAX3485 on the Nucleo talks to the PMD401 directly |
| Balance | 0.01 mg balance | For single 0.05 U dose claims |
| Hamilton 81320, if friction > 3 N | "Change the syringe" | No replacement part has been chosen. OPEN |

History that looks like an alternative but is not one:

- **INA226 module → INA219 module.** The INA226 was the original choice. It was out of stock everywhere checked on 30 Sep 2026 and was replaced by the INA219 module (0.1 Ω shunt covers 3.2 A). INA219 is the current part. The 20 mΩ, 1 W, 2512 shunt listed for the INA226 swap is no longer needed and is not in the 37-item list.
- **TPS62840 EVM → MCP1700.** Cost saving on Rev A. TPS62840 goes straight onto the Rev B PCB.
- **Two BSS138 → one BSS138.** Simplified kill switch; now fail-off.

## 6. Removed or rejected parts. Do not reintroduce (DECIDED)

| Part | Why it was dropped |
| --- | --- |
| TI DRV8662, TI DRV2700 | Single-channel PZT drivers. The LL06 needs four synchronized 0–48 V channels, which the PMD401 provides |
| Single PZT + valve (diaphragm pump) | Scrapped for positive displacement |
| Shinsei USR30-E3 (and USR30 / D6030 ultrasonic motors) | Humidity limits incompatible with Guwahati's climate; thrust-load limits incompatible with a leadscrew; impractical size |
| New Scale Squiggle (SQL-1.8 / SQL-3.4), DTI motors | Earlier candidates, not selected |
| NEMA 17 (JK42HS40-1204AF-02), A4988, T8 leadscrew, ESP32 DevKit, 11.1 V 3S LiPo | v1 prototype only |
| NEMA 8 / NEMA 11 steppers, TMC2209, DRV8834 | Interim v2 idea; NEMA 8 rejected as too large |
| Faulhaber AM0820 + 08/1K 64:1 gearhead, STSPIN220 (Pololu #2876), AS5048A, Honeywell ABP2 | Stepper-based v2 plan, replaced by the piezo design |
| LT20 motor, Hamilton 1005 (2.5 mL), AS5311, TMP117, MAX17048, TPS2660 eFuse, FRAM, memory LCD | Belong to the superseded Master Engineering Specification |
| STM32U585RIT6 / NUCLEO-U575ZI-Q, nRF5340 / nRF52840 BLE module, STM32C011 | 25 Sep plan, replaced by WBA55 + C031 |
| NUCLEO-WB55RG, NUCLEO-G431RB, NUCLEO-G474RE | Candidates not selected. WBA55CG kept for TrustZone, simpler single-core BLE firmware, stronger radio and a direct path to the Rev B PCB |
| Custom HV transformer driver, leadscrew assembly | Removed with the earlier draft |
| TI BQ25180 | Replaced by BQ25188 |
| Robu TPS61040-based boost module | 50 mA against 450 mA needed; no true output disconnect |
| Any boost module without true shutdown ahead of the DC2628A | It would pass VIN to the output when disabled and defeat the kill switch |
| Plain boost for 3.0–4.2 V → 48 V on Rev B | Hits the 93 % duty limit; flyback chosen |

## 7. Sourcing

### 7.1 Motor kit (PiezoMotor, quote-only)

| Item | Recorded value |
| --- | --- |
| Supplier | PiezoMotor (Uppsala, Sweden); contact first name Marcus |
| First quote | Ref. 20261008-012546920, €1,805, FCA Uppsala, prepayment. Wrong: it carried two motor lines |
| Revised quote | Item code LL06A0-101M1G1E2 at €984; total €1,619; payment 30 days; DAP shipping to Guwahati €150 |
| Kit contents (vendor reply) | Motor cable, encoder cable, 48 V supply (plus the PMD401 driver) |
| Encoder output (vendor reply) | Quadrature, 3.3–5 V |
| Lead time | 3–4 weeks from payment |
| Not recorded | Whether the quote was accepted or paid. Whether the final order confirmation says DAP Guwahati (the quote still listed FCA Uppsala). Whether a USB–RS-485 cable is in the kit (the 29 Sep report says yes; the vendor's contents list does not mention it) |

### 7.2 Store links recorded in "Insulin Pump Rev A – Parts List" (30 Sep 2026)

"search" means the link was a store search, not a specific listing.

| Part | Store recorded |
| --- | --- |
| NUCLEO-WBA55CG, NUCLEO-C031C6 | DigiKey India (search) |
| MAX3485 module | Robu (`robu.in/product/max3485-module-ttl-to-rs485-3-3v/`) |
| USB-to-RS-485 adapter | Robu (search) |
| Molicel INR18650-P28A | Robu or ElectronicsComp. Robu was out of stock on 30 Sep; ElectronicsComp ₹451 |
| 18650 holder | Roboman |
| 1S 5 A protection board | Robu listing; out of stock on 30 Sep, redirected to RoboComp ₹58 |
| TP4056 USB-C protected charger | Robu |
| Inline blade fuse holders (5 pcs), 5 A fuses, toggle switch | Robu (holders listing; fuses and switch are searches) |
| INA219 module | Robu ₹139 |
| MCP1700-3302E/TO, 1 µF caps | DigiKey India (search) |
| TPS62840-1DLCEVM55 (optional) | DigiKey India listing 296-TPS62840-1DLCEVM55-ND |
| Pololu U3V70F12 | Fab.to.Lab (`fabtolab.com/step-up-voltage-regulator-u3v70x`, pick F12) |
| DC2628A | Mouser India or DigiKey India |
| Electrolytic capacitors, BSS138, resistors, Ohmite 20J470E | DigiKey India (search) |
| SOT-23 adapter, XT30 male + female, silicone wire | Robu |
| Disposable syringes | Any pharmacy |
| Hamilton 81320 | Through a lab-supply distributor in India (Sigma-Aldrich India was among the stores checked) |

Other recorded sourcing facts:

- Stores checked on 30 Sep 2026: Robu, Mouser India, ElectronicsComp, RoboComp, Fab.to.Lab, Roboman, Robocraze, Kitsguru, Sigma-Aldrich India.
- Required priced parts totalled about ₹36,801 on 30 Sep 2026, before the LL06 kit and before Mouser GST and duty.
- DigiKey India: free delivery at ₹7,000+, otherwise ₹1,200; duty and GST paid on delivery. Robu ships free above ₹499.
- DC2628A stock at Mouser India is recorded two ways (6 in stock with a 9-week lead time after that; 9 in stock with no restock planned). Both are stale. See conflict CF-11.
- Earlier USD prices (29 Sep 2026, `Pump_RevA_BOM.xlsx`): NUCLEO-WBA55CG US$58.34 (Future Electronics), Hamilton 81320 US$82 (Chrom Tech), ChipWhisperer-Husky US$599. Other prices in that file were rough estimates.
- Per-line prices and clickable links live in the Excel parts list (35 components, 30 Sep 2026) and in `Pump_RevA_BOM.xlsx` (29 Sep 2026). They are not reproduced here and those files are not stored in the project. See `SOURCE_DOCUMENTS.md`.

### 7.3 Rev B sourcing

Nothing recorded. No supplier, price or stock check exists for BQ25188, LM51551, TPS62840, the bare MCUs, the flyback transformer or the PCB fab.
