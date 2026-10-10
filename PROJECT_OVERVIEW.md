# PROJECT_OVERVIEW.md

Handoff snapshot: 10 Oct 2026. Source project: claude.ai Project "INSULIN_PUMP" (also called HybridPancreasSim v2 / "Piezo Insulin Pump").

## How to read these handoff files

Every statement in the eight handoff files carries one of these labels, or sits in a section that carries it.

| Label | Meaning |
| --- | --- |
| CONFIRMED | Fact taken from a datasheet, manual, vendor reply or a measurement, as recorded in the project. Not re-verified on 10 Oct 2026. |
| DECIDED | A decision the project owner (B Charan) made or accepted. Do not change without approval. |
| PROPOSED | A suggestion written by Claude in a project document. Not signed off. Treat as a draft, not a requirement. |
| ASSUMPTION | Something the documents rely on but nobody has confirmed. |
| OPEN | Missing, unmeasured or conflicting. See `OPEN_QUESTIONS.md`. |
| SUPERSEDED | Recorded earlier, replaced later. Kept only so it is not reintroduced by mistake. |

Read order for a new session: this file, `DECISION_LOG.md`, `HARDWARE_CONSTRAINTS.md`, `COMPONENTS_AND_BOM.md`, `DESIGN_REQUIREMENTS.md`, `OPEN_QUESTIONS.md`, `VALIDATION_PLAN.md`, `SOURCE_DOCUMENTS.md`.

## Purpose

Build a small, close-to-industry-grade insulin pump prototype that doses correctly on the bench. (DECIDED)

- A Piezo LEGS LL06 linear piezo motor pushes the plunger of a Hamilton 1 mL glass syringe directly. No gears, no screw.
- An STM32WBA55 (main MCU, BLE) runs dosing. An STM32C031 (supervisor MCU) can only stop it.
- Everything runs from one Li-ion cell.
- Success is correct dosing measured by weight on water, plus a safe stop on every single fault.

## Hard limits on use (DECIDED)

- Lab prototype only. Water or 0.9 % saline only. Bench only, 18–28 °C.
- Never connected to a person or an animal. No real insulin.
- Every requirement and pass limit is an engineering target, not a clinical claim.
- The pump is designed and tested to the methods in the medical standards but is not certified to any of them.
- The goal is to recreate the pump's function, not to copy any commercial device's architecture.

## Intended functionality

- Bolus: 0.05 to 10 U in 0.05 U steps (1 U = 10.0 µL, U-100). (DECIDED)
- Basal: delivered as 0.05 U pulses, 0.05 to 5.0 U/h. (PROPOSED)
- Closed-loop position control on the LL06's own 80 nm encoder, to an absolute target. (DECIDED)
- Sensorless occlusion detection: step length shrinks as load rises, so commanded steps versus encoder travel gives back-pressure. This is the main novelty. (DECIDED)
- Fault-injection hardening of the dosing firmware, tested with voltage and clock glitching. Stretch goal. (DECIDED as stretch)
- Control input: a phone over BLE now. Later, a custom CGM with its own protocol, built by another team. (DECIDED)
- The 48 V motor rail is on only while a dose is moving. An unpowered LEGS motor clamps its rod, so off is the safe state. (DECIDED)

## Build stages (DECIDED)

| Stage | What it is | State on 10 Oct 2026 |
| --- | --- | --- |
| v1 | C++ simulator (HybridPancreasSim) plus ESP32 + A4988 + NEMA 17 syringe rig | Prototype only. Fully replaced. Do not carry any v1 hardware forward. |
| Rev A | Bench build on NUCLEO-WBA55CG + NUCLEO-C031C6, PMD401 driver, battery power tree on modules | Parts list declared final 29 Sep 2026. No record of any Rev A hardware measurement yet. Motor quote received 8 Oct 2026; payment and delivery not recorded. |
| Rev B | Custom 4-layer KiCad PCB carrying the bench-proven Rev A circuit | Not started in this project. See below. |

The owner considered skipping Rev A and going straight to a PCB, and decided against it. Rev A bench validation comes before Rev B PCB work. (DECIDED)

## State of the PCB work (read this before opening KiCad)

- This project contains **no KiCad files, no schematic, no netlist, no footprints and no board outline**. None were uploaded and none were generated here.
- The only uploaded project file is the reference note `some data about the pump` (background on commercial insulin pumps).
- The project has no custom instructions set.
- The one conversation titled "PCB design project" (10 Oct 2026) only covered what Claude can and cannot do for PCB design. No board constraints were given in it. Claude asked for board size, layer count, form factor, battery and fab house; none were answered.
- Rev B requirements exist only as the short table in `DESIGN_REQUIREMENTS.md` section 3.7, mostly PROPOSED.
- Several inputs the layout needs are still OPEN: MCU pin assignment, PMD401 connector pinout, flyback transformer part number, cell size, board outline, fab house. See `OPEN_QUESTIONS.md`.
- Any KiCad files on the Windows computer were not visible to this project. If they belong to a different board (for example a separate CGM transmitter board), these documents do not describe them.

## Scope

In scope:

- Rev A bench electronics: power tree, kill path, MCU boards, driver interface, bench reference sensors.
- Rev B PCB: STM32WBA55CG + STM32C031C6, charger, 48 V flyback, 3.3 V buck, protection, connectors to the PMD401, encoder, battery.
- Firmware for both MCUs (the owner writes it; see "Working style").
- Verification plan and records.

Out of scope or deferred:

- Syringe mount and plunger coupling: not designed yet. Mechanical work was deliberately put after the electronics.
- Glucose control algorithm on hardware: the pump only executes commanded volumes. The control loop was proven in the v1 simulator.
- Air-in-line and flow sensors: not in the design.
- A pressure sensor on the final device: the IBP transducer is bench reference only.
- Certification, EMC chamber tests, radio approval, biocompatibility, clinical work.
- The CGM itself: built by another team (their platform was described as nRF52840-based).

## Timeline

- 30 days from 21 Sep 2026, target about 21 Oct 2026. (DECIDED)
- Motor lead time is 3–4 weeks from payment, which lands in early to mid November. (CONFIRMED from vendor reply; conflicts with the target, see `OPEN_QUESTIONS.md`)
- Power-tree, kill-path and firmware checks can run without the motor.

## Resources and constraints on the work (DECIDED)

- Funded project, not a personal one. Almost all feasible components and equipment can be used.
- Fully equipped electronics lab (oscilloscope and standard equipment).
- Rev A parts are to be bought from Indian websites where possible, with cost minimised wherever that does not sacrifice performance.
- Location for shipping: Guwahati, India.
- The quotation conversation refers to the organisation as Purvoday Biotech. (ASSUMPTION: confirm before using on paperwork)

## Working style the owner asked for

- Casual, terse, direct answers. No padding.
- The owner wants to write the pump firmware personally. Provide explained reference code plus guides so the logic can be learned and reproduced, not just finished code.
- Flag contradictions with earlier constraints immediately instead of working around them.
- Do not invent data. Mark anything unverified.

## Current design in one paragraph

Cell (Molicel INR18650-P28A) → 1S 5 A protection board → 5 A fuse → master switch → INA219 → two branches. Branch 1: MCP1700-3302E/TO LDO → 3.3 V for both Nucleos, INA219 and MAX3485. Branch 2: Pololu U3V70F12 (3.7 → 12 V, its enable pin is the kill switch) → DC2628A / LT8362 (12 → 48 V) → PMD401 → LL06 → Hamilton 1001 TLL (PN 81320). The main MCU sends a step rate to the PMD401 over SPI and reads the LL06 encoder itself. The supervisor watches a heartbeat, owns the PMD401 park line (AEN) and can force the boost enable low through a BSS138. Rev B replaces the modules with BQ25188 (charger), LM51551 flyback (48 V), TPS62840 (3.3 V) and the bare MCUs on one 4-layer board.
