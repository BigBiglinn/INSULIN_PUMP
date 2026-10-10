# SOURCE_DOCUMENTS.md

What the handoff files were built from, where each source lives, and whether it is current. Compiled 10 Oct 2026.

Availability wording used here:

- **In the project** = stored in the claude.ai Project "INSULIN_PUMP".
- **Claude Doc** = a document in the owner's claude.ai artifact list. Seen in that list on 10 Oct 2026. Open it at its link and export it from there.
- **Chat attachment** = a file produced or uploaded inside one past conversation. It is not stored in the project. Whether it can still be downloaded from that conversation was **not checked**.
- **Link only** = a web address written in a project document. The file itself is not stored anywhere in the project. Links were **not opened on 10 Oct 2026**.

## 1. Files uploaded to the project

| File name | What it is | Status |
| --- | --- | --- |
| `some data about the pump` | Text note titled "Technical and Clinical Architecture of Modern Insulin Infusion Pumps". Background on commercial pumps (Medtronic MiniMed, Tandem t:slim X2, Insulet Omnipod): therapy, form factors, MCUs, drive mechanisms, occlusion and air sensors, safety architecture, standards, cybersecurity. Uploaded 4 Aug 2026 | In the project. Background only; none of its figures are project requirements |

This is the only uploaded file. The project has no custom instructions. No KiCad files, schematics, datasheets, CAD or code are stored in the project.

## 2. Project documents (Claude Docs)

| Title (exact) | Date | Link | Status | Used for this handoff |
| --- | --- | --- | --- | --- |
| Piezo Insulin Pump — Design Requirements, Parts and Verification Report | 10 Oct 2026 | https://claude.ai/code/artifact/a37fdb7b-8f28-4b12-9bf2-1abcb303dba0 | **Current baseline** | Read in full. Its embedded architecture diagram ("pump architecture · power and motion chain, two control paths") is a drawing and is not reproduced in the handoff files |
| Insulin Pump Rev A – Component Roles | 30 Sep 2026 | https://claude.ai/code/artifact/18ca028a-eaed-4166-b84d-9ce3c1f833af | Partly stale (INA226, RS-485 command path) | Read in full. Embedded block diagram "Rev A power and control paths · 15 blocks" not reproduced |
| Insulin Pump Rev A – Parts List | 30 Sep 2026 | https://claude.ai/code/artifact/22d6a74d-e658-4eb3-afc1-53b89e771623 | Partly stale (INA226, 1.25 µm encoder). Holds the store links | Read in full |
| Piezo Insulin Pump — Rev A Final Project Report | 29 Sep 2026 | https://claude.ai/code/artifact/f523d4c7-fd70-4335-aa2f-16d1176f96b8 | Mostly current; its "Rev A runs from the kit's 48 V supply" and 9-line BOM were replaced on 30 Sep | Read in full. Embedded diagram "Rev A architecture · signal, power and safety paths" not reproduced |
| Piezo Insulin Pump — Rev A | 29 Sep 2026 | https://claude.ai/code/artifact/d19f062a-3e2d-407f-ab07-6387479aee1f | Not opened for this handoff. Believed to be the 15-slide presentation built from the Final Project Report | Not read |
| Piezo Insulin Pump — Electronics Development Plan | 25 Sep 2026 | https://claude.ai/code/artifact/a3b8ee8d-d733-4306-8e10-d6058e5e1adb | SUPERSEDED (STM32U585 + DRV8662 + valve pump plan) | Known from its conversation summary only |
| Piezo-LEGS Insulin Pump v2 — Master Engineering Specification (Lab Prototype) | 22 Sep 2026 | https://claude.ai/code/artifact/1343aa71-a3eb-4c06-afa9-825defde3d89 | SUPERSEDED (LT20 motor, Hamilton 1005, AS5311; requirements R-01 to R-29; changes C14, C15) | Not re-read. A few passages seen through conversation search. Do not import its content |

## 3. Files produced or uploaded in past conversations (chat attachments)

None of these is stored in the project. File names are given only where the record states them.

| File | Date | Conversation | Status |
| --- | --- | --- | --- |
| `Pump_RevA_BOM.xlsx` | 29 Sep 2026 | "BOM for selected products" | Rev A BOM, 9 line items, USD and INR. Older than the 37-item list |
| Excel parts list, 35 components, with store links and INR prices (file name not recorded) | 30 Sep 2026 | "Buck converter for REV A" | Prices as of 30 Sep 2026. Older than the 37-item list |
| Two block-diagram SVGs: power tree, control/signal paths (file names not recorded) | 30 Sep 2026 | "Buck converter for REV A" | Rev A wiring pictures |
| `pump_fw.zip` | 27 Sep 2026 | "Piezoelectric motor and pump selection" | Reference firmware: `pump_config.h`, `pump_port.h`, `dose_ctrl.c`, `load_est.c`, `hardened.h`, `port_stm32wba.c`, `pump_app.c`, `sim_plant.c`, `test_main.c` |
| `pump_course.zip` | 27 Sep 2026 | "Piezoelectric motor and pump selection" | Nine-stage firmware course, one project folder per stage, with a README listing four bugs found |
| 15-slide presentation with speaker notes (file name not recorded) | 29 Sep 2026 | "Parts to order now" | Rev A summary |
| 154-slide `.pptx` engineering-review deck (file name not recorded) | 24 Sep 2026 | "Analyzing specification document architecture" | Built from the SUPERSEDED Master Specification |
| PiezoMotor quotation ref. 20261008-012546920, the revised quotation for LL06A0-101M1G1E2, and the email replies | 8 Oct 2026 | "Linear motors quotation" | Owner's own documents. The order confirmation, if any, has not been seen |
| Paper: Kaçar, Özer, Taşçıoğlu, ICAT'19 (piezoelectric valveless micropump, COMSOL + Simulink, PID on a Bergman plant) | 21 Sep 2026 | "Bergmen model training comparison" | Background only. Its actuator is unrelated to this design |
| v1 simulator: merged C++ codebase with `Controllers.h` and `BergmanModel.h`, CSV results, `report.html`, ESP32 firmware, a 33-slide PowerPoint deck | Aug–Sep 2026 | Earlier conversations | v1 only |
| v1 mechanics: `hopefully_Final.zip` (owner's upload), `rack_pinion_drive_verified.zip`, `VERIFICATION_REPORT.md`, `BOM_and_assembly.md`, OpenSCAD Part A (motor mount) and Part B (carriage) | Sep 2026 | "CAD verification for stepper motor gear translation mechanism" and others | v1 only. SUPERSEDED |

## 4. Datasheets, manuals and reference designs

**No datasheet, manual or reference design is stored in the project.** The links below are the ones written into project documents on 29–30 Sep 2026.

| Document | Link recorded | Note |
| --- | --- | --- |
| PMD401 Technical Manual (PiezoMotor document 150025) | https://piezomotor.com/wp-content/uploads/2019/03/150025_PMD401_Technical_Manual.pdf | Link only. A 2026/03 path for the same file name was also tried in a past chat; which revision was actually read is not recorded |
| LL06 product page | https://piezomotor.com/linear-direct-drive-piezo-actuators/legs-linear-ll06-piezo-motor/ | Link only |
| ST UM3301 (STM32WBA Nucleo-64 board, MB1803) | https://www.st.com/resource/en/user_manual/um3301-stm32wba-nucleo64-board-mb1803-stmicroelectronics.pdf | Link only. Source of the JP2 instruction |
| DC2628A demo manual | https://www.mouser.com/datasheet/2/609/855_DC2628A_REV01_DEMO_MANUAL-1379821.pdf | Link only |
| DC2628A product page | https://www.analog.com/en/resources/evaluation-hardware-and-software/evaluation-boards-kits/dc2628a.html | Link only |
| TPS62840 product page | https://www.ti.com/product/TPS62840 | Link only |
| TPS62840 EVM user guide (SLUUC18) | https://www.ti.com/lit/ug/sluuc18/sluuc18.pdf | Link only |
| Pololu U3V70x regulators | https://www.pololu.com/category/243/u3v70x-step-up-voltage-regulators | Link only |
| Characterisation of insulin analogues (PMC), S1 Table | https://pmc.ncbi.nlm.nih.gov/articles/PMC5875863/ | Link only. Density and viscosity background |

Standards pages recorded as opened on 10 Oct 2026 by the requirements report: IEC 60601-2-24:2012 (https://webstore.iec.ch/publication/2635); 21 CFR 880.5730 (https://www.law.cornell.edu/cfr/text/21/880.5730); MISRA C:2025 (https://misra.org.uk/?p=28616); IEC 62304 edition 2 summary (https://asd.criticalsoftware.com/en/newsroom/iec-62304-edition-2-changes-august-2026); IPC-2221C (https://webstore.ansi.org/standards/ipc/ipc2221c2023); Bluetooth Insulin Delivery Service v1.0.1 (https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/IDS_v1.0.1/out/en/index-en.html); ISO 10993-1:2025 (https://www.iso.org/standard/84512.html); an ONdrugDelivery article on infusion-pump dose accuracy testing (https://ondrugdelivery.com/challenges-in-testing-the-accuracy-of-infusion-pump-doses/). These are web pages, not the standards' text. No standard text is held.

Documents the Rev B work needs that have **no link and no copy** in the project:

- LL06 datasheet and mechanical drawing; PMD401 mechanical drawing and connector pinout.
- NUCLEO-C031C6 user manual (for the IDD jumper).
- STM32WBA55CG datasheet and reference manual; STM32C031C6 datasheet.
- The ST reference design or RF hardware guideline to copy for the WBA55 antenna, matching network and 32 MHz crystal. It is referred to but never identified.
- TI BQ25188, LM51551 and TPS62840 datasheets; any LM51551 flyback reference design.
- LT8362, MCP1700, INA219, MAX3485, BSS138, TP4056 datasheets.
- Molicel INR18650-P28A datasheet; Hamilton 81320 specification sheet; Pololu U3V70F12 product page.
- KiCad symbols, footprints and 3D models for every Rev B part.
- The fab house's design-rule file.

## 5. Conversations in the project (provenance)

| Date | Title | Link | Relevance |
| --- | --- | --- | --- |
| 10 Oct 2026 | Piezo electric pump design requirements | https://claude.ai/chat/c883fe80-a839-4789-ae7c-334fde379e48 | Produced the current baseline report |
| 10 Oct 2026 | PCB design project | https://claude.ai/chat/d2dff36f-e4ad-4907-b7b6-c42506445d5c | PCB capabilities only; no constraints given |
| 8 Oct 2026 | Linear motors quotation | https://claude.ai/chat/ec33e336-b0e3-4f8b-816d-0796b22ae551 | Motor quote, item code, lead time |
| 30 Sep 2026 | Buck converter for REV A | https://claude.ai/chat/5491d1b5-22fa-4d34-ae1d-c420d517da2b | Power tree, kill path, Indian sourcing |
| 29 Sep 2026 | Seeking novelty in project decisions | https://claude.ai/chat/867a48a0-d913-4297-82ac-6ab262571fa3 | Novelty options |
| 29 Sep 2026 | BOM for selected products | https://claude.ai/chat/5687a704-f320-4ef3-9a73-d49dd8fddf99 | `Pump_RevA_BOM.xlsx` |
| 29 Sep 2026 | Parts to order now | https://claude.ai/chat/637006e2-b828-48c1-aead-53c36b027752 | Final Rev A selection, project report, 15-slide deck |
| 27 Sep 2026 | Piezoelectric motor and pump selection | https://claude.ai/chat/8145023a-be62-4ab0-bccb-1e9a4655f47f | LL06 selection, firmware reference and course |
| 27 Sep 2026 | Drivers and boards list | https://claude.ai/chat/856149a0-5772-40e4-8394-082d593f7acb | SUPERSEDED candidates (WB55RG, DRV8662) |
| 25 Sep 2026 | Insulin pump with piezoelectric motor design | https://claude.ai/chat/085608d9-e733-4193-bd52-986f3e463105 | SUPERSEDED DRV8662 plan; owner's architecture statement |
| 24 Sep 2026 | Analyzing specification document architecture | https://claude.ai/chat/7b1419cb-cdd1-4ea4-9797-3eb492a4afc0 | SUPERSEDED: 154-slide deck |
| 23 Sep 2026 | Document outline and section workflow | https://claude.ai/chat/bb80f948-eabe-4c7c-b98f-68bc2043ff57 | SUPERSEDED: Master Specification |
| 22 Sep 2026 | Starting with REV A | https://claude.ai/chat/9472a80e-92c5-41b8-8628-a65807c4303c | SUPERSEDED stepper Rev A scoping |
| 22 Sep 2026 | Transitioning prototype to industry-grade medical device | https://claude.ai/chat/723f7b2d-32f8-4aba-a6d1-331b7446bef2 | v2 re-scope; WBA55 + C031 first chosen; Rev A → Rev B decision |
| 21 Sep 2026 | Bergmen model training comparison | https://claude.ai/chat/e448e41f-d1b0-44ea-9679-45da113abe30 | Background paper |
| 21 Sep 2026 | Motor types in insulin pumps | https://claude.ai/chat/3d8091bc-49e7-49ec-a6bd-ebb233ad7fc9 | Background |
| 8 Sep 2026 | Replacing stepper motor with piezoelectric motor (two conversations) | https://claude.ai/chat/252388f3-df10-4ed7-b1ed-ee837c4721b2 and https://claude.ai/chat/409f52b1-fcc2-4d7f-8bbc-061ccb9bcb11 | First piezo discussion |
| 8 Sep 2026 | Running newly assembled parts | https://claude.ai/chat/347da6a2-c9f7-40f3-a0c1-d9febb7e29ff | v1 stepper bring-up |
| 7 Sep 2026 | CAD verification for stepper motor gear translation mechanism | https://claude.ai/chat/0b4f000d-c260-467e-83ae-ac2aebf70fb2 | v1 mechanics |

Most conversations were used through their saved summaries, not re-read line by line. Where a handoff statement rests only on a summary, the underlying detail may be thinner than the original.

Also used: the project's saved notes on the owner's stated decisions (project purpose, v2 re-scope, 29–30 Sep decisions).

## 6. Checklist: originals to download or copy by hand

The handoff files carry the requirements, part numbers, decisions and checks. They do not carry the items below.

**Needed for the Rev B PCB work**

- [ ] Any existing KiCad project for this pump from the Windows computer (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, symbol and footprint libraries). None exists in the claude.ai project.
- [ ] PMD401 Technical Manual (PDF) from PiezoMotor, for the connector pinout and signal levels.
- [ ] LL06 datasheet and drawing from PiezoMotor.
- [ ] PiezoMotor quotation (revised, LL06A0-101M1G1E2), the email replies, and the order confirmation once it exists.
- [ ] ST datasheets and reference manuals for STM32WBA55CG and STM32C031C6; UM3301; the NUCLEO-C031C6 user manual.
- [ ] The ST reference design or RF layout guideline for the STM32WBA55 antenna and crystal.
- [ ] TI datasheets: BQ25188, LM51551, TPS62840 (plus SLUUC18 if the EVM is used).
- [ ] DC2628A demo manual and LT8362 datasheet (to compare the Rev A stage with the Rev B flyback).
- [ ] Datasheets for BSS138, MCP1700-3302E/TO, INA219, MAX3485, TP4056, Molicel INR18650-P28A, Hamilton 81320, Pololu U3V70F12.
- [ ] The fab house's design rules and stack-up.

**Project documents to export**

- [ ] "Piezo Insulin Pump — Design Requirements, Parts and Verification Report" (export from its link; includes the architecture diagram).
- [ ] "Insulin Pump Rev A – Component Roles" (for the block diagram).
- [ ] "Insulin Pump Rev A – Parts List" (for the store links).
- [ ] "Piezo Insulin Pump — Rev A Final Project Report" (for the architecture diagram and firmware module table).
- [ ] `some data about the pump` from the project files, if the background is wanted.

**Files from past conversations**

- [ ] The Excel parts list with store links and prices (30 Sep 2026).
- [ ] `Pump_RevA_BOM.xlsx` (29 Sep 2026).
- [ ] The two Rev A block-diagram SVGs (power tree; control and signal paths).
- [ ] `pump_fw.zip` and `pump_course.zip` (firmware reference and course).
- [ ] The 15-slide Rev A presentation, if wanted.

**Only if history is wanted (superseded; do not use as design input)**

- [ ] "Piezo-LEGS Insulin Pump v2 — Master Engineering Specification (Lab Prototype)" and the 154-slide deck.
- [ ] "Piezo Insulin Pump — Electronics Development Plan".
- [ ] v1 simulator code, `report.html`, the 33-slide deck, `hopefully_Final.zip`, `rack_pinion_drive_verified.zip`, `VERIFICATION_REPORT.md`, `BOM_and_assembly.md`, OpenSCAD parts.
