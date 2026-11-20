# Conclusion {#ch:concl}

## Achievements against the objectives

{tab:achieve} compares the outcome with the objectives of {sec:objectives}.

!table tab:achieve | Objectives and outcome | 3,1.2,3.6
| Objective | Outcome | Evidence |
| 1. Requirements register, decision log, validation plan | Achieved | 14 owner requirements, 76 technical requirements, 18 locked decisions, a dated decision log, 13-group validation plan (Appendices A–C) |
| 2. Component selection with reasons and alternatives | Achieved | {sec:decisions}; rejected-parts register; datasheets in the repository |
| 3. Fail-off safety architecture | Achieved in design; not proven | Pull-ups and pull-downs set the off state in copper; independent OVP trip. The S-06 runaway check needs supervisor firmware |
| 4. Rev A bench design and Rev B PCB | Rev A designed (not built); Rev B designed | 37-line Rev A list; 144-reference Rev B design |
| 5. Digitally verified Rev B | Achieved | ERC 0, DRC 0, unconnected 0, parity 0 (kicad-cli 10.0.3); independent re-run: 451/451 pins, 0 islands, 0 shorts |
| 6. Power electronics verified before hardware | Partly achieved | Three design errors found and fixed by simulation; switch margin, slope compensation and control loop open |
| 7. Complete handover documentation | Achieved | Handover guide, assumptions and deviations, unresolved issues, ECO records, this report |

## What the work shows

The project produced a complete, internally consistent design for a battery-powered piezoelectric syringe pump. A single cell powers both a 3.3 V logic rail and a 48 V motor rail that exists only while a dose moves. Every way in which either microcontroller can fail (reset, crash, loss of power) leaves the motor unpowered and parked, because the off state is set by resistors in copper rather than by firmware. The design is traceable: every value on the board has a recorded source and status, every change since 10 October is a tagged, reviewable step, and every check can be re-run from the repository.

The most useful engineering result is negative in form: **simulation found three errors that would each have prevented the board from working or destroyed a part**. They were a soft-start capacitor 20 times too small, a rectifier that would ring to breakdown, and a switching FET without voltage margin. The simulations also quantified the efficiency of the adopted 48 V stage (81.7–84.5 % at full load in the open-loop model). The energy estimate showed that standby power, not dosing, will decide battery life. That tells the bench work what to measure first.

## Limitations

- **No hardware evidence.** Dose accuracy, occlusion detection (the project's main novelty), the kill path, the efficiency and the battery life are all unmeasured. The design is a strong starting point for Rev A and Rev B bench work, not a demonstrated pump.
- **Open critical items:** Q301 voltage margin, transformer leakage, LM51551 slope compensation, the PMD401 absolute maximum voltage, and the firmware-only speed cap ({tab:open}).
- **Models, not vendor models.** No LM51551 SPICE model was available, so the control loop is unverified. The FET and diode models are fitted to datasheets.
- **The v1 simulator results** are reported from the project records only, pending the source files ({sec:v1}).
- **Generic fabrication rules:** no fab house, stack-up or DFM review.

The appropriate statement of the project's state is therefore: **module-level design and simulation completed; software verification of the complete board completed; individual hardware testing not started; integrated system testing not started.**

# Future Scope {#ch:future}

The improvements below are specific and ordered. Each names the check or document that closes it.

1. **Close the flyback design.** Add slope compensation (R305 → 18 mΩ, RSL ≈ 887 Ω) and re-run the start-up model. Obtain HPH6-0090L samples and measure their leakage. Choose a verified ≥ 40 V logic-level FET or measure the AONR34332C drain voltage on the bench (PB-10). Run TI's LM5155 model or a bench Bode measurement for the loop.
2. **Ask PiezoMotor the four drafted questions:** the absolute maximum on the 48 V input, behaviour at 50.4–54 V, signal levels and pull-up rails, and input capacitance. Then set the OVP trip accordingly.
3. **Rework the power-stage copper** (review F-C4, F-M1, F-M2, F-M13): pours on the battery path and the primary loop, a Kelvin sense trace, via arrays under the exposed pads, and power net classes for VBAT, VBAT_FUSED and GND.
4. **Add the missing protection footprints:** encoder pull-ups (F-M7), RS-485 TVS (F-M9), a USB VBUS TVS, an RO pull-up, and test points on every rail and safety signal.
5. **Build Rev A** and run the validation plan in order: incoming inspection, power tree, kill path. Then measure the step-length-against-load curve (MT-05), which decides whether sensorless occlusion detection works.
6. **Write the supervisor firmware** with an independent rate check against its own encoder count, so that single-fault check FT-02 can pass. Then write the dosing firmware against the obligations in {sec:fw}.
7. **Measure the Rev B idle power** and choose the cell, writing the missing `requirements/power_budget.md`.
8. **Choose a fab house,** import its rules and stack-up, recompute the RF line widths from it, and only then generate fabrication outputs after a release review (Phase 6).
9. **Agree the CGM protocol** with the other team and define the link-loss behaviour (C-05). Implement LE Secure Connections and command counters (C-02, C-03).
10. **Commit the v1 simulator and the reference firmware** to the repository, so that the closed-loop results can be regenerated and the dosing code can be tested against the Rev A hardware.
