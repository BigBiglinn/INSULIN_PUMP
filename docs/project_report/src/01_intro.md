@mainmatter

# Introduction {#ch:intro}

## Background

People with type 1 diabetes produce little or no insulin and depend on insulin delivered from outside the body. One common way to deliver it is continuous subcutaneous insulin infusion by a wearable pump. The pump gives a slow, continuous **basal** flow that stands in for the background secretion of the pancreas, and larger **boluses** on demand, for example at meals. Modern systems add a continuous glucose monitor (CGM) and a control algorithm that adjusts delivery automatically. These are often called hybrid closed-loop or "artificial pancreas" systems.

Whatever the control algorithm, the pump mechanism has a hard engineering job. With U-100 insulin, one unit (U) is only 10 µL, and the smallest increments that commercial pumps deliver are a few hundredths of a unit, a fraction of a microlitre. The mechanism must turn an electrical command into a fluid volume that small, repeatably, from a battery, in a device small enough to wear. It must also never deliver more than commanded. An insulin overdose can be fatal, so a pump is a safety-critical device and its design is governed by standards such as IEC 60601-2-24 (infusion pumps) and ISO 14971 (risk management) [7], [8].

## Motivation

This project began as a software exercise (v1): a C++ simulator of glucose–insulin dynamics with closed-loop controllers, plus a stepper-motor demonstration rig. The simulator showed that a supervised predictive controller can keep simulated glucose in range. The demonstration rig, however, used a NEMA 17 stepper, a leadscrew and an ESP32, and the owner judged it too large and too far from industry practice. On 21 September 2026 the project owner re-scoped the work (v2) with three goals. The device should be smaller, with a smaller motor. Everything should be on STM32 microcontrollers. The design should come close to industry grade. The owner also asked for real novelty rather than a port of an existing design ({tab:ownerreq}).

Two ideas give the v2 design its technical interest:

1. **Direct piezoelectric drive.** A Piezo LEGS linear motor pushes the syringe plunger directly, with no gearbox and no leadscrew. An unpowered LEGS motor clamps its rod with more than its stall force, so loss of power cannot let the plunger move. With an 80 nm encoder, one encoder count corresponds to about 1.3 nL of fluid.
2. **Sensorless occlusion detection.** The step length of a LEGS motor shrinks as the load on it rises. Comparing commanded waveform steps with the travel measured by the encoder therefore estimates the back-pressure in the line without a pressure sensor. This is the main novelty of the project and its main unproven technical bet ({sec:assumptions}).

## Problem statement

Design a battery-powered insulin-pump prototype that:

- delivers commanded volumes of water or saline from 0.05 U (0.5 µL) to 10 U per bolus, with ±5 % accuracy as the measured target;
- uses a piezoelectric motor driving a positive-displacement syringe, controlled by an STM32 microcontroller with Bluetooth Low Energy;
- reaches a defined safe state (48 V motor rail off, motor parked and clamped) on any single fault of either microcontroller, the heartbeat between them, or any supply rail;
- runs from one Li-ion cell; and
- is documented to the point where another engineer can take it over, because the owner is leaving the project before completion.

The prototype is for the bench only. It is never to be connected to a person or an animal, and never to be used with real insulin. All limits in this report are engineering targets, not clinical claims.

## Objectives {#sec:objectives}

The objectives below are taken from the owner-level requirements recorded on 21–30 September 2026 and from the change of objective recorded on 10 October and 1 November 2026 (decision log, sections 6 and 9).

1. Establish a requirements register, a decision log and a validation plan from the owner's statements and the component datasheets.
2. Select the motor, driver, syringe, microcontrollers and power-conversion parts, and record the reasons for each choice and the alternatives rejected.
3. Design a safety architecture in which either microcontroller failing, in any way, leaves the motor unpowered.
4. Design the Rev A bench build (development boards and power modules) and the Rev B custom PCB that carries the same circuit on one board.
5. Produce a complete, digitally verified Rev B KiCad design: schematic, 4-layer PCB, BOM, with ERC and DRC reports read and every open item recorded.
6. Verify the power electronics, especially the 48 V flyback converter, by calculation and simulation before any hardware is built.
7. Hand the project over with every assumption, deviation and unresolved issue documented.

## Scope and limitations

**In scope:** the electronics of both build stages, the power tree and kill path, the microcontroller pin maps, the 48 V flyback converter, the PCB, the verification plan, and the v1 simulator, which this report summarises as background.

**Out of scope or deferred:** the syringe mount and plunger coupling (deliberately scheduled after the electronics), firmware implementation (the owner writes it personally from the reference design), the glucose control algorithm on hardware (the pump only executes commanded volumes), air-in-line and flow sensors, certification, EMC and radio approval, biocompatibility and any clinical work. The CGM is built by a separate team.

**Limitation of evidence.** On 10 October 2026 the owner changed the objective to a **digital Rev B handover design**, and on 1 November 2026 confirmed that the board will not be fabricated. Consequently:

- no Rev A hardware measurement exists (the motor lead time was 3–4 weeks from payment, and payment is not recorded);
- every result in Chapter 5 is a software check, a hand calculation or a simulation;
- a clean ERC or DRC report does not show that the circuit works.

This limitation is repeated wherever a result could be mistaken for a measurement.

## Project evolution

{fig:timeline} shows the history of the project. The design changed direction several times. The changes are recorded here because a reader who finds an older document should know that it is superseded:

- **v1 (August to early September 2026):** C++ HybridPancreasSim simulator (Bergman minimal model, PID, predictive controller, safety supervisor, fault injection) and an ESP32 + A4988 + NEMA 17 + T8 leadscrew rig. Superseded as hardware; the simulator results remain background.
- **21–24 September:** v2 re-scope. A stepper-based plan (Faulhaber AM0820 with a 64:1 gearhead) and then a large "Master Engineering Specification" built on a PiezoMotor LT20 motor and a 2.5 mL syringe were written. Both are superseded.
- **25–27 September:** the owner restated the architecture (3.7 V battery → high-voltage stage → piezo driver → piezo motor; the same cell powers the STM32). A single-PZT valve pump was considered and scrapped in favour of a piezo motor on a syringe. The LL06 motor, PMD401 driver, Hamilton 81320 syringe and the two STM32 parts were selected.
- **29–30 September:** the Rev A parts list was declared final. The power tree and the fail-off kill path were designed.
- **8–10 October:** the motor quote was revised to the exact item code. The requirements report was written, followed by the handoff documents.
- **10–11 October:** the objective changed to a digital Rev B handover design. A generated schematic and a placed, partly routed PCB were produced, then placement was optimised and routing proceeded in staged, checked steps.
- **31 October–1 November:** engineering change orders ECO1–ECO3 corrected the schematic. PCB stages P1–P6 completed the layout to 0 ERC and 0 DRC violations, and an independent design review was added.

!fig fig:timeline | docs/project_report/figures/fig_timeline.png | Project timeline. Dates are taken from the decision log and the git history; the v1 bar is approximate, because the decision log records v1 only as "before September 2026". | 6.2

## Organisation of the report

Chapter 2 reviews insulin-pump architectures, actuators, occlusion detection, glucose–insulin modelling, safety standards and power conversion for piezo drives. Chapter 3 describes the method: the workflow, the requirements, the system architecture and the reasoning behind each major design decision. Chapter 4 describes the implementation: the v1 simulator, the Rev A bench design, the Rev B schematic, the flyback converter and the PCB. Chapter 5 presents the results of every check, calculation and simulation, including efficiency and an energy estimate, and discusses the problems found and how they were diagnosed. Chapter 6 concludes and Chapter 7 lists specific future work. The appendices hold the full requirement register, the validation plan, the decision log, the BOM, the archived tool reports and the code listings.
