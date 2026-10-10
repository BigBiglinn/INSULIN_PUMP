# OPEN_QUESTIONS.md

Three lists: (A) open items carried over from the 10 Oct 2026 report, with its numbering kept so that "item 3" means the same thing everywhere; (B) information the Rev B PCB needs that is not recorded anywhere; (C) contradictions between project documents. Nothing here has been resolved on the owner's behalf.

## A. Open items from the 10 Oct 2026 report

Items 2 to 7 are design gaps that change wiring or parts. **Items 2, 3 and 4 should be settled before the Rev B schematic is drawn.**

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

### Numbers that are calculated or quoted but not yet measured

Battery draw (about 2.1 A worst case, 0.11 W idle), 48 V ripple and load-step response, PMD401 current at dosing speed, PMD401 boot time, PMD401 pull-up voltage, SPI word scale and bit order, no-load step length (expected 2–8 µm), step length versus load curve, plunger friction, line compliance, encoder behaviour across 48 V switching, park and unpark timing, every accuracy figure. The simulator's occlusion numbers rest on an assumed plant (friction 1.5 N, compliance 2 µL/bar, linear step versus load).

No Rev A hardware measurement of any kind is recorded in the project as of 10 Oct 2026.

## B. Missing information the Rev B PCB needs

None of the following is recorded in the project. Each needs an answer from the owner, a datasheet or a bench measurement. Do not fill these in by assumption.

### B.1 Project state

1. Do KiCad files for this pump already exist on the Windows computer? The project holds none. If they exist, which revision do they represent, and which KiCad version?
2. Has any Rev A hardware arrived or been tested? Which checks have been run?
3. Was the PiezoMotor quote accepted and paid? On what date? Is the delivery term on the order confirmation DAP Guwahati?
4. Is the 21 Oct 2026 target still in force given the motor lead time?
5. Is Rev B to be drawn now, in parallel with Rev A, or only after Rev A passes? The recorded decision is Rev A first.

### B.2 Board definition

6. Board outline, size limit, thickness, copper weight, mounting, enclosure.
7. Fab house and its design-rule file; assembly method (hand, stencil + reflow, or fab assembly); surface finish.
8. Layer count is PROPOSED as 4. Not signed off.
9. Component placement limits: one side or both; minimum passive size acceptable for hand assembly.
10. Is the PMD401 mounted on the Rev B board, stacked, or connected by cable? Its mechanical drawing and connector family are not recorded.

### B.3 Schematic inputs

11. MCU pin assignment for both MCUs (none exists).
12. Full orderable part numbers: STM32WBA55CG package and suffix; STM32C031C6 package and suffix; TPS62840 variant; BQ25188 package.
13. PMD401 connector pinout and signal list; LL06 encoder connector pinout; encoder supply voltage and source.
14. PMD401 pull-up rail voltage (decides 5 V-tolerant pins or open-drain, and TVS voltage).
15. TVS part number and working voltage; exact series resistor value ("about 100 Ω").
16. Flyback design for the LM51551: transformer part number and turns ratio, switching FET, output diode, output switch, sense resistor, compensation, output capacitors. None chosen.
17. How the Rev B 48 V rail is switched and discharged (E-11 asks for < 5 V within 5 s; no discharge circuit is defined).
18. Rev B current monitor: keep an INA219 on the board, another part, or none?
19. BQ25188 charge current, input connector (USB-C?), and whether power-path is used. Charger must never be the load path (E-09).
20. Rev B cell: chemistry and capacity, connector, and whether protection is in the pack or on the board. Fuse and master switch on Rev B?
21. Supervisor gate default direction (item 3) and park-line pull-down value (item 4).
22. Whether the supervisor gets encoder A/B (item 5), a buzzer and a STOP button (item 6). Buzzer part and driver.
23. Heartbeat definition: physical link, period, token scheme, timeout (see conflict CF-17).
24. Crystal(s): 32 MHz for the WBA55 is named in check PB-06; any 32.768 kHz crystal, load capacitors and the ST reference design document to copy are not identified.
25. Antenna type (PCB antenna, chip antenna or connector) and matching network values.
26. SWD connector type for each MCU; console UART connector; test-point list.
27. Whether the bench-only parts (IBP transducer + HX711, RS-485 setup link) get headers on Rev B.
28. Event-log storage (F-08 is PROPOSED): MCU flash or an external memory?
29. Rev B battery-life target (3 days is PROPOSED) and the daily profile behind it.

### B.4 Mechanical and other

30. Syringe mount and plunger coupling design; how the board sits relative to the motor and syringe.
31. Replacement syringe if friction exceeds 3 N.
32. Link-loss rule and CGM message format (item 16).
33. Which organisation name goes on orders and documents ("Purvoday Biotech" appears once, unconfirmed).

## C. Contradictions between project documents

Conflict IDs use the prefix CF- so they cannot be mistaken for the communication requirements C-01 to C-07.

Listed as found. Where a later owner decision clearly replaced an earlier one, that is noted, but the older document still says the old thing and has not been corrected.

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

## D. Assumptions the documents rely on

- The PMD401 behaves as its manual says in servo mode with this motor and encoder option.
- In servo mode the LL06 encoder signals are available to the MCU (the PMD401 encoder connector doubling as the SPI servo interface was a reading of the connector table, not a stated fact).
- The Molicel cell, protection board and modules bought from retailers are genuine and match their listings.
- The DC2628A regulates inside 46.5–49.5 V as specified when fed 11.5–12.5 V from the Pololu.
- Step length falls smoothly and repeatably with load, so it can serve as an occlusion sensor. This is the main technical bet of the project and is unproven on hardware.
- The CGM team will supply a protocol; nothing about it is defined.
