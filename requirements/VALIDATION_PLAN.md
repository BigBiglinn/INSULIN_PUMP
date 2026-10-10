# VALIDATION_PLAN.md

Source: section 6 and 7 of "Piezo Insulin Pump — Design Requirements, Parts and Verification Report" (10 Oct 2026). Check IDs and pass limits are copied from it. The whole plan was written by Claude; the owner has not signed off the limits (see `OPEN_QUESTIONS.md` item 15). Limits that restate a DECIDED requirement are binding; the rest are PROPOSED.

As of 10 Oct 2026 no check has a recorded result.

## Map

| Kind of check | Where |
| --- | --- |
| Schematic | Part A: PB-01, PB-02 (ERC), PB-07 |
| PCB layout | Part A: PB-02 (DRC), PB-03 to PB-07 |
| Manufacturing and assembly | Part A: PB-08, PB-09 |
| Electrical bring-up of the board | Part A: PB-10 to PB-13 |
| Electrical bench checks (Rev A, repeated on Rev B through PB-13) | Part B: groups 1 to 5 |
| Mechanical, fluid, accuracy, occlusion, fault, firmware, BLE, battery | Part B: groups 6 to 12 |

## Rules for every check

1. Write down the measured number, not only pass or fail.
2. Timing checks get a scope screenshot saved with the check ID in the file name.
3. Change one thing at a time. If a check fails, fix it and rerun that whole group.
4. If anything in the kill-path group (SG) fails, stop. Nothing after it is meaningful until the kill path works.
5. Limits marked *record* have no pass value yet; the first measurement sets it.
6. Groups run in order. A group must pass before the next one is powered or filled.

Order: incoming inspection (IN) → power tree (PW) → kill path (SG) → boards and interfaces (IF) → motor and driver (MT) → mechanics and fluid (MF) → dose accuracy (DA) → occlusion (OC) → single-fault matrix (FT) → firmware (FW) → BLE and security (BL) → battery and endurance (BT) → Rev B board (PB).

---

## Part A. Rev B board: schematic, PCB, manufacturing, bring-up

Before the Rev B schematic is drawn, `OPEN_QUESTIONS.md` items 2, 3 and 4 should be settled, and the missing inputs in its section B must be answered.

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

Related requirements to check in the schematic and layout review (see `DESIGN_REQUIREMENTS.md`): P-01 to P-08, S-01, S-02, E-03 to E-08, E-11.

Schematic review points that follow from the open design gaps (not separate check IDs in the source):

- Boost-enable default-off network present with the recorded values (4.7 kΩ to GND, 1 kΩ from the main MCU, BSS138 to GND).
- Supervisor gate default direction matches whatever the owner decides for item 3.
- Park-line pull-down present, value from the measured PMD401 pull-up (item 4).
- TVS + series resistor on every PMD401 signal line.
- All 48 V rail capacitors rated ≥ 100 V.
- Charger output is not in the load path.

---

## Part B. Bench checks (Rev A)

### 1. Incoming inspection, before any power

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

### 2. Power tree: bench supply first, battery second, PMD401 last

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

### 3. Kill path

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

### 4. Boards and interfaces

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

### 5. Motor and driver

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

### 6. Mechanics and fluid path

Blocked until the syringe mount and plunger coupling exist.

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

### 7. Dose accuracy by weight (the acceptance gate)

Method follows IEC 60601-2-24 and AAMI TIR101, shortened where a prototype does not need a 24 h run.

Setup, the same for every run:

1. Balance on a solid bench inside a draft shield, switched on for an hour first. Room at 20 ± 2 °C and steady within 0.5 K during a run.
2. Collection vial part-filled with water under a thin layer of light oil, so nothing evaporates. Outlet tip below the surface and not touching the glass.
3. Outlet at the same height as the syringe, except in DA-08.
4. Degassed water at room temperature. Let the filled pump sit 30 min before the first reading.
5. Balance logged to a PC with a timestamp, next to the encoder count.
6. Mass to volume at 0.998 g/mL: 1 U weighs 9.98 mg, and 0.05 U weighs 0.50 mg.
7. Run DA-01 at the start of every session.

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

A 0.1 mg balance can prove the 1 U and 20-pulse limits but not a single 0.05 U dose: ±5 % of 0.50 mg is 0.025 mg. Use a 0.01 mg balance for that claim, or state it as position-verified only.

### 8. Occlusion and pressure

The IBP transducer reads to 300 mmHg (0.4 bar). Use it up to there and a 0–2 bar reference above (not yet in the parts list).

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

### 9. Single-fault matrix

For each row, record the travel in counts from the moment of the fault to standstill. Unless the row says otherwise, pass is no more than 0.5 U of extra delivery (3,745 counts) and an alarm.

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

### 10. Firmware

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

Reference results from the simulator (reference code, assumed plant; not hardware): 40 × 0.05 U gave 19.997 µL of 20 µL, within 0.03 % across 2–8 µm step lengths; 5 U bolus gave 49.998 µL in about 60 s; a 27 % SPI scale error was absorbed by the encoder loop; occlusion alarm after about 0.21 U into a blocked line (about 773 mmHg); bit flips in limits, target and authorisation flag all detected; MCU hang stops the motor in 10 ms.

### 11. BLE and security

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

### 12. Battery and endurance

| ID | Check | How | Pass |
| --- | --- | --- | --- |
| BT-01 | Run time | From full: 1 U/h basal plus three 5 U boluses a day, down to the 3.4 V cut-off | Record the days; Rev B target is 3 |
| BT-02 | Low battery | Bench supply ramped down slowly in place of the cell | Warning at 3.5 V; dosing refused with an alarm at 3.4 V; a dose in progress ends cleanly |
| BT-03 | Charging | Charge from 3.4 V, logging voltage, current and cell temperature | Ends at 4.20 ± 0.05 V; cell warms by less than 10 K |
| BT-04 | Wear | Five full syringes (500 U) of mixed delivery, then repeat DA-03, MT-04 and MF-01 | Mean dose moved by less than 1 %; step length and friction within 10 % of their first values |
| BT-05 | Heat | Prime continuously for 10 min; thermometer or thermal camera on both boost stages, PMD401, motor and syringe | Nothing above 60 °C; syringe warms by less than 1 K |

---

## Part C. Records to keep

- One line per check: ID, date, hardware revision, firmware build hash, measured value, pass or fail, who ran it, file name of the scope shot or log.
- A hazard table in the ISO 14971 style: hazard, the requirement that controls it, the check that proves it.
- A change log for firmware and for wiring, so a result can be tied to the build it was taken on.
- The calibration record for each syringe used.
- A list of third-party code with versions (ST HAL, BLE stack, any libraries).

## Part D. Check once, then only after a change

| Check | Redo only when |
| --- | --- |
| Encoder direction and count integrity (IF-05) | Encoder wiring or timer setup changes |
| SPI mode, bit order, rate scale (IF-03, MT-03) | PMD401 settings or the SPI driver change |
| PMD401 pull-up voltage (IF-02) | Never again for the same driver board |
| INA219 accuracy (IF-07) | The module is replaced |
| Plunger friction and volume calibration (MF-01, DA-02) | A different syringe is fitted. Do both per syringe, not per session |
| Kill path (all SG checks) | Any change to enable wiring or supervisor firmware. This one is always rerun in full |

## Part E. Not needed for this prototype

Not needed for a lab prototype (comes back if it ever becomes a product): test-house certification to IEC 60601-1; EMC chamber tests (IEC 60601-1-2); radio approval and Bluetooth qualification; biocompatibility, sterility, insulin compatibility and stability; clinical evaluation and patient usability studies; ingress, drop, vibration and shipping tests; a quality system and full design history file (ISO 13485); the 24 h settling run before basal accuracy tests (shortened to 1 h; say so next to the result); transport tests on the cell (UN 38.3; buy genuine cells).

Not needed because of how this pump works: resonance tracking; backlash or screw-pitch compensation; an anti-free-flow valve (MT-06 and MF-04 prove the clamp once); motor current as a load signal; a home or limit switch (MF-08 covers the ends); a pressure sensor on the final device; air-in-line and flow sensors (priming and the compliance check are the only air control, a stated limit of this pump); motor life testing (BT-04 is enough); checking the PMD401's waveforms; tuning the glucose controller on hardware; correcting for insulin viscosity or density (density is within about 1 % of water).

## Part F. Do not do

- Do not connect the pump to a person or an animal, and do not use real insulin for any check here.
- Do not short a Li-ion cell to test its protection, charge it unattended, or run the load from the TP4056 output.
- Do not feed 3.3 V into a Nucleo before the jumper change in IN-09.
- Do not connect any PMD401 signal to an MCU pin before IF-02.
- Do not take the 48 V rail above 50.4 V to see what the driver does.
- Do not oil the LL06 rod, force it by hand, or let it stall against the glass syringe.
- Do not run an accuracy test without DA-01 first, or with a visible bubble anywhere.
- Do not quote any dose-accuracy, occlusion or single-fault result taken while a kill-path check was failing.
