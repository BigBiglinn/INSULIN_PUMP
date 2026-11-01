# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# STM32 + Bluetooth PCB Engineering Project

## Mission
Design a reliable, manufacturable, battery-powered STM32 PCB with Bluetooth connectivity. The exact STM32 part numbers are supplied by the user. Use the approved project requirements as the authority for all design decisions.

Optimize for electrical correctness, battery life, reliability, manufacturability, serviceability, testability, and reasonable cost.

## Project status
Project: Piezo Insulin Pump v2 (bench-only, water/saline, never on a person or animal). Handoff documents are in `PROJECT_OVERVIEW.md`, `decisions/`, `requirements/`, `docs/SOURCE_DOCUMENTS.md` (they use upper-case file names, not the names in the deliverables list below).

10 Oct 2026: the owner changed the objective to a **digital Rev B handover design** (no fabrication or bench validation before handover; see `decisions/DECISION_LOG.md` section 6). A generated KiCad 10 project now exists in `hardware/kicad/` (schematic, 4-layer PCB, project library), built from `scripts/design.py` by `scripts/gen_*.py`. It is NOT fabrication-approved: TBD/PLACEHOLDER parts, ST datasheet items and owner decisions are open. 1 Nov 2026: objective is digital only (no fabrication); fully routed, ERC and DRC 0 violations at tag `pcb-p6-final`, see `docs/handover/PCB_STAGES.md` Stage P6. Start with `docs/handover/HANDOVER_GUIDE.md`, `ASSUMPTIONS_AND_DEVIATIONS.md` and `UNRESOLVED_ISSUES.md`. Regenerating overwrites the KiCad files, so commit before running the generators.

## Non-negotiable rules
1. Never invent hardware requirements, component specifications, datasheet values, pin mappings, package dimensions, or validation results.
2. Separate verified facts, engineering assumptions, proposed choices, and unresolved questions.
3. Do not choose the PCB layer count, board dimensions, battery voltage, Bluetooth architecture, or regulator until the requirements and constraints have been analyzed.
4. Prefer official manufacturer datasheets, reference manuals, errata, and verified footprints.
5. Preserve all original requirements and maintain a decision log.
6. Never overwrite the last known-good design without creating a recoverable checkpoint (in practice, a git commit or tag of the known-good state before modifying it).
7. Never claim that an artifact was generated or a test passed without checking the actual file or tool output.

## Mandatory workflow
- Phase 0: Discover tools, inspect available project inputs, and establish the requirements register.
- Phase 1: Produce a block diagram, power architecture, interface list, Bluetooth architecture options, preliminary BOM, and risk register.
- Phase 2: Verify component selection and design the schematic.
- Phase 3: Validate the schematic and BOM before PCB layout.
- Phase 4: Verify footprints, define manufacturing constraints, select the stack-up, place components, and route the board.
- Phase 5: Run ERC, DRC, netlist consistency checks, power and thermal calculations, and relevant simulations.
- Phase 6: Generate manufacturing outputs only after engineering review and release checks.

Never skip a phase without documenting the reason and receiving approval where required.

At each phase, report changed files, checks performed, actual results, assumptions, and remaining risks.

## Battery and power engineering
- Determine the complete input voltage range and battery chemistry from approved requirements.
- Calculate operating, peak, startup, sleep, and standby current where applicable.
- Estimate battery life using documented current assumptions and realistic conversion losses.
- Verify regulator operating range, dropout, quiescent current, stability, transient response, thermal dissipation, and component ratings.
- Check reverse polarity, overcurrent, undervoltage, charging, protection, and power-path requirements where applicable.
- Do not add a charging circuit or assume USB charging is required unless specified.
- Validate decoupling, reset, startup, brownout, and power sequencing requirements against the selected MCU documentation.

## Bluetooth engineering
- Establish whether Bluetooth is implemented in the STM32, a separate module, or another approved architecture.
- Do not assume BLE, Bluetooth Classic, a particular module, antenna type, or radio certification requirements without confirmation.
- Verify the actual wireless device's supply requirements, interface, pinout, antenna constraints, RF keep-out, ground layout, and regulatory documentation.
- Account for radio transmit-current peaks and their effect on the supply rail.
- Keep the antenna and RF layout consistent with manufacturer reference guidance.

## Schematic and layout integrity
- Verify all MCU supply pins, ground pins, reset, boot, clock, programming, and debugging connections.
- Verify package suffixes, pin numbering, footprint dimensions, connector orientation, and pin assignments.
- Use trace widths, clearances, vias, and copper weights appropriate to current, voltage, impedance, thermal limits, and fabrication capabilities.
- Evaluate return-current paths, ground planes, analog circuitry, switching regulators, clocks, and RF placement according to the actual circuit.
- Do not suppress warnings merely to obtain a clean ERC or DRC report.

## Validation
- Run the installed KiCad CLI and inspect the real ERC and DRC reports.
- Verify schematic-to-PCB connectivity and footprint assignments.
- Use calculations and simulations appropriate to the circuit.
- Track every unresolved critical and major issue.
- Distinguish software validation from bench validation and manufacturing acceptance.
- A clean ERC/DRC report is not proof that the circuit works.

Do not declare the board ready for fabrication until all critical issues have been resolved and the final design has been reviewed.

## Deliverables (maintained files)
- `requirements/design_requirements.md`: original requirements, preserved verbatim
- `requirements/requirements_register.md`
- `requirements/power_budget.md`
- `requirements/component_sources.md`
- `decisions/decision_log.md`
- `docs/bom.csv`
- `docs/datasheets/`
- `docs/bringup_test_plan.md`
- `docs/release_report.md`
- `hardware/kicad/`: KiCad project (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, libraries)
- `scripts/`: check and output automation
- `validation/`: `erc/` and `drc/` reports, `logs/` for other tool output
- `manufacturing/`: Gerbers, drill, pick-and-place (Phase 6 only)

## Tooling
- **KiCad 10.0.3**: `kicad-cli` (`C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`) is on PATH.
- **LTspice**: reachable through the `ltspice` MCP server for circuit simulation (for example regulator transient response and TX-burst supply droop).

Typical commands, with `<name>` replaced by the actual project file name once it exists:

```powershell
# Electrical rules check -> validation/erc
kicad-cli sch erc --format report --severity-all --exit-code-violations -o validation/erc/<name>-erc.rpt hardware/kicad/<name>.kicad_sch

# Design rules check, including schematic/PCB parity -> validation/drc
kicad-cli pcb drc --format report --severity-all --schematic-parity --exit-code-violations -o validation/drc/<name>-drc.rpt hardware/kicad/<name>.kicad_pcb

# BOM -> docs
kicad-cli sch export bom -o docs/bom.csv hardware/kicad/<name>.kicad_sch

# Fabrication outputs -> manufacturing (Phase 6 only)
kicad-cli pcb export gerbers -o manufacturing/gerbers/ hardware/kicad/<name>.kicad_pcb
kicad-cli pcb export drill   -o manufacturing/gerbers/ hardware/kicad/<name>.kicad_pcb
kicad-cli pcb export pos     -o manufacturing/pos.csv  hardware/kicad/<name>.kicad_pcb
```

Confirm flags with `kicad-cli <subcommand> --help` before relying on them. KiCad files are S-expression text; any hand or scripted edit must be followed by an ERC/DRC run, and the reports read, not just the exit code.
