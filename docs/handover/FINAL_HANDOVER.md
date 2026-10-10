# Piezo Insulin Pump v2: final digital handover

10 Oct 2026. Read this first. Details are in `HANDOVER_GUIDE.md`, `FLYBACK_DESIGN.md`, `UNRESOLVED_ISSUES.md` and `ASSUMPTIONS_AND_DEVIATIONS.md`.

> **Safety limits.** This is a bench-only prototype for water or 0.9 % saline. Never connect it to a person or an animal, and never use real insulin.
>
> **Not fabrication-ready.** No Gerbers have been generated. Nothing has been built or measured. A clean ERC or DRC report does not show that the circuit works.

## 1. Opening the project

- Open `hardware/kicad/pump_v2.kicad_pro` in **KiCad 10.0.x**. The project library (`pump_v2.kicad_sym`, `pump_v2.pretty`) is referenced through the project-local `sym-lib-table` and `fp-lib-table`.
- The schematic is hierarchical: a root sheet plus 7 sub-sheets (power input/charger, 3V3 buck, 48 V flyback, kill path, main MCU, supervisor, PMD401/encoder).
- The PCB is 4 layers, 110 × 85 mm:
  - L1/L4: signals plus GND pours.
  - L2: solid GND.
  - L3: VBAT (battery strip, bottom band and 48 V block) and +3V3 (elsewhere).
- Every part carries `Status` (DECIDED, DS, CALC, ASSUMED, TBD or PLACEHOLDER), `MPN` and `Note` fields. The Note field records the source or justification for the value.

## 2. Regenerating (source of truth: `scripts/design.py`)

```bash
python scripts/gen_library.py
python scripts/gen_schematic.py
python scripts/verify_pinmap.py                      # pin map vs STM32CubeMX database
kicad-cli sch export netlist --format kicadsexpr -o hardware/kicad/pump_v2.net hardware/kicad/pump_v2.kicad_sch
"C:\Program Files\KiCad\10.0\bin\python.exe" scripts/gen_pcb.py place     # OVERWRITES the PCB, including routing
"C:\Program Files\KiCad\10.0\bin\python.exe" scripts/gen_pcb.py dsn  out.dsn
java -jar freerouting-2.1.0.jar -de out.dsn -do out.ses --gui.enabled=false --router.job_timeout=00:12:00
"C:\Program Files\KiCad\10.0\bin\python.exe" scripts/gen_pcb.py ses  out.ses
"C:\Program Files\KiCad\10.0\bin\python.exe" scripts/hand_route.py validation/drc/pump_v2-drc.rpt <NET...>   # optional
bash scripts/run_checks.sh                            # ERC, DRC with parity, BOMs
```

Notes:

- Freerouting 2.1.0 needs Java 21 and is not in the repository. Disable its telemetry in `freerouting.json` before use.
- Commit before regenerating. Once you start hand-editing in KiCad, stop regenerating, or port your edits back into `design.py` and `gen_pcb.py`.

## 3. What is digitally complete

- **Circuit:** the full circuit for all locked parts (K-3 to K-6, K-12), with connector pinouts confirmed from the PMD401 manual 150025-01.
- **Fail-safe paths, as owner-approved on 10 Oct:**
  - 48 V veto defaults ON (R403 pull-up).
  - PMD401 AEN defaults PARKED (open-drain Q402 + R405).
  - The K-10 enable network is unchanged.
- **Pin maps:** both MCU pin maps verified against the STM32CubeMX 6.18.1 database (`validation/logs/pinmap_check.md`, 0 failures).
- **Charger:** BQ25188 configured from its datasheet (TS resistor; register defaults documented). The firmware must set the charge current and service the watchdog.
- **Battery sensing:** VBAT divider for the S-13 3.4 V stop.
- **48 V flyback:** dimensioned from the LM51551 datasheet with real, datasheet-backed FET and rectifiers. The open-loop power stage was simulated in LTspice (`validation/sim/`).
- **PCB:** placed and mostly routed, with **0 copper DRC violations and 0 schematic-parity issues** in the final run (section 6).

## 4. What is incomplete (do these in order)

1. **ST datasheets (U-05):** obtain the STM32WBA55CG and STM32C031C6 datasheets and the WBA RF/hardware design guide; st.com was blocked from the machine used. Then wire VDD11, the SMPS inductor, VDDHPA, VDDANA, VDDRF and VDDRFPA, decoupling, the 32 MHz HSE and the RF pi-match. This removes the 6 intentional ERC errors.
2. **Flyback transformer (U-04):** choose a part that meets `FLYBACK_DESIGN.md` §4. Replace the placeholder footprint, re-tune the clamp/snubber, and verify the loop (TI LM5155 model or bench).
3. **Routing (U-21):** finish the remaining unconnected items (`validation/logs/unrouted_nets.txt`). Then hand-review the flyback loop, the 48 V path and the RF trace. The autorouted copper around the placeholder transformer is **not final**.
4. **Open decisions:** 48 V output switch and bleeder (U-06), secondary OVP (U-23), battery connector/cell/fuse and charge current (U-18), TVS parts (U-15).
5. **Footprint checks:** BQ25188 YBG pitch, CSD16340Q3 DQG, connector orientations (U-12, U-17). Choose a fab and load its rules (U-16).
6. **Only then:** Rev A bench validation (`requirements/VALIDATION_PLAN.md`), engineering review, and then fabrication outputs.

## 5. Placeholders, DNP parts and unverified items

See `docs/bom_detailed.csv`, which lists every reference with its status and note. Summary:

- **PLACEHOLDER:**
  - T301 transformer (footprint is a placeholder).
  - Q302/Q303/R309/R310/R312 (48 V output switch and bleeder, DNP).
  - L501, C509–C515, R510–R513, L502, Y502, C516–C519 (WBA55 supply, RF and crystal items pending the ST datasheet).
- **Unverified footprints:**
  - BQ25188 YBG (inferred 0.4 mm pitch).
  - CSD16340Q3 (KiCad TI NexFET pattern).
  - Transformer placeholder.
  - Connector orientations.
- **Scoped DRC exceptions in `pump_v2.kicad_dru`:** J703 (vendor JST SH pitch, +48 V next to GND) and Q301 (NexFET pad pitch). No other rule is relaxed.

## 6. Final validation results

Filled in from the last `scripts/run_checks.sh` run (see section 7 of `HANDOVER_GUIDE.md` for how to reproduce).

- ERC: see `validation/erc/pump_v2-erc.rpt`.
- DRC: see `validation/drc/pump_v2-drc.rpt`.
- Unrouted nets: see `validation/logs/unrouted_nets.txt`.

**Software validation only.** Nothing here proves the board works. There has been no bench validation and no manufacturing review.
