@title

@unnumbered Certificate

This is to certify that the project report entitled **"Piezo Insulin Pump v2: Design of a Battery-Powered, Piezoelectric Syringe-Drive Insulin Pump Prototype with Dual-MCU Safety Architecture and Bluetooth Low Energy (Rev B Digital Design)"**, submitted by **[Student name] ([Roll number])** to the Indian Institute of Technology Guwahati in partial fulfilment of the requirements for the degree of Bachelor of Technology, is a record of work carried out under my supervision. The contents of this report have not been submitted elsewhere for the award of any degree.

[Fill in or replace with the department's prescribed certificate wording.]

Signature of Supervisor: ______________________

Name: [Supervisor name]

Designation and Department: [Designation], [Department]

Date: ______________          Place: Guwahati

@unnumbered Declaration

I declare that this report is my own record of the engineering work described in it. Where I have used ideas, data, figures or words from other sources, I have cited them. The numerical results in this report come from the design files, calculation scripts, simulation decks and tool reports kept in the project repository (`BigBiglinn/INSULIN_PUMP`). Each result is labelled as a calculation, a simulation or a software check. **No hardware was built or measured for this report, and no result in it is presented as a measurement.**

Software assistance: parts of the design documentation, the analysis scripts and the drafting of this report were prepared with an AI coding assistant (Claude Code). Every number reported here was checked against the repository file it comes from, and the scripts that produce the figures are included so that each result can be regenerated.

I understand that any misrepresentation of the work may lead to disciplinary action by the Institute.

Signature: ______________________

Name: [Student name]          Roll number: [Roll number]

Date: ______________

@unnumbered Acknowledgement

[Personalise this page.] I thank my supervisor, [Supervisor name], for guidance throughout the project, and the [Department name], IIT Guwahati, for laboratory facilities and funding. I also thank B Charan, the project owner, whose design decisions are recorded in the project's decision log, and the members of the team developing the continuous glucose monitor, whose platform this pump will eventually serve. The design work used KiCad 10, LTspice, ngspice, STM32CubeMX and Freerouting. I am grateful to the authors of these tools and to the component manufacturers whose datasheets and application notes are cited in the references.

@unnumbered Abstract

An insulin pump must deliver very small, accurate volumes of drug and must stop safely when anything goes wrong. This project set out to recreate the function of such a pump as a bench-only engineering prototype, for use with water or saline only and never on a person or an animal. The first version (v1) was a C++ closed-loop simulator, HybridPancreasSim, which modelled glucose–insulin dynamics with the Bergman minimal model and compared PID and predictive controllers with a safety supervisor. It was paired with a demonstration rig built from an ESP32, an A4988 driver and a NEMA 17 stepper on a leadscrew. The second version (v2), the subject of most of this report, replaces the stepper and leadscrew with a Piezo LEGS LL06 linear piezoelectric motor. The motor pushes the plunger of a 1 mL Hamilton glass syringe directly, and a PiezoMotor PMD401 driver drives it. An STM32WBA55CG microcontroller with an integrated Bluetooth Low Energy radio handles dosing, and an independent STM32C031C6 supervisor can only stop the motor. Everything runs from a single Li-ion cell, with a 48 V flyback converter for the motor rail.

The work followed a phased engineering workflow: a requirements register (14 owner requirements and 76 numbered technical requirements), a decision log, a component selection checked against datasheets, and then a generated KiCad 10 design. A single Python design file (`scripts/design.py`) is the source of truth for 144 bill-of-materials references on eight hierarchical schematic sheets. The PCB is four layers, 111.6 × 85.1 mm, with 158 footprints, 1114 track segments and 277 vias. The 48 V stage, an LM51551 non-isolated flyback with a Coilcraft HPH6-0090L transformer, was dimensioned by hand calculation and checked with LTspice, ngspice and a cycle-by-cycle Python model. The simulations found three design errors before any hardware existed: a 47 nF soft-start capacitor that would lock the converter in hiccup, a 100 V output Schottky that rang to breakdown, and a 25 V switching MOSFET without voltage margin. In open-loop simulation the adopted power stage reaches 81.7 % efficiency at 3.0 V input and 84.5 % at 4.2 V input at the full 100 mA load.

At the final checkpoint (tag `pcb-p6-final`, 1 November 2026) the archived KiCad 10.0.3 reports show 0 ERC errors, 0 DRC violations, 0 unconnected items and 0 schematic-to-PCB parity issues. For this report the independent netlist and connectivity checks were re-run on that board: 451 of 451 schematic pins agree with the design source, and there are no shorts and no unrouted nets. These are software results only. No board has been fabricated and no bench test has been run, so dosing accuracy, occlusion detection and the safety paths remain unverified. Open items include the switching-FET voltage margin, the transformer leakage inductance, the LM51551 slope compensation and the PMD401 absolute maximum voltage. The report records every one of these with its evidence and its next step.

**Keywords:** insulin pump, piezoelectric linear motor, syringe drive, STM32WBA55, Bluetooth Low Energy, flyback converter, LM51551, fail-safe design, KiCad, Bergman minimal model.

@toc

@lof

@lot

@unnumbered List of Abbreviations

!table nonum-abbrev | Abbreviations and symbols used in this report | 1,4
| Term | Meaning |
| ADC | Analog-to-digital converter |
| AEN | Axis enable input of the PMD401 driver (LOW = motor parked) |
| BLE | Bluetooth Low Energy |
| BOM | Bill of materials |
| CALC / DS / ASSUMED / TBD / PLACEHOLDER / DECIDED | Status labels carried by every part in the design source ({sec:status}) |
| CCM | Continuous conduction mode |
| CGM | Continuous glucose monitor |
| DNP | Do not populate (footprint present, part not fitted) |
| DRC / ERC | Design rule check / electrical rules check (KiCad) |
| ECO | Engineering change order |
| EN / UVLO | Enable / under-voltage lock-out input of the LM51551 |
| FET / MOSFET | Field-effect transistor |
| FT, DA, OC, SG, PW, MT, MF, IF, IN, FW, BL, BT, PB | Check-group prefixes of the validation plan ({app:vplan}) |
| HSE / LSE | High-speed (32 MHz) / low-speed (32.768 kHz) external crystal |
| IPC | Association Connecting Electronics Industries (PCB standards body) |
| K-n | Locked owner decision number n ({tab:locked}) |
| LEGS | PiezoMotor's walking-leg piezo actuation principle |
| MCU | Microcontroller unit |
| OVP | Over-voltage protection |
| PCB | Printed circuit board |
| PID | Proportional–integral–derivative controller |
| PMD401 | PiezoMotor driver for the LL06 motor |
| RCD | Resistor–capacitor–diode clamp |
| RF | Radio frequency |
| RHPZ | Right-half-plane zero |
| SPI / UART / I²C / SWD | Serial peripheral interface / asynchronous serial / inter-IC bus / serial wire debug |
| TIR | Time in range (glucose 70–180 mg/dL) |
| TVS | Transient voltage suppressor |
| U | Insulin unit; here 1 U = 10.0 µL of U-100 solution (water or saline in this project) |
| VBAT | Battery rail after the master switch |
