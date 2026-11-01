# Piezo Insulin Pump v2: Rev B digital handover guide

Prepared 10 Oct 2026 for the engineer who takes over the project. Layout-only fixes were added on 31 Oct 2026 without KiCad: see `LAYOUT_FIXES_2026-10-31.md`. **They are not yet verified by kicad-cli.**

> **Completion session (1 Nov 2026), start here.** Status and next steps: `OWNER_APPROVAL_SHEET.md` (17 decisions, recommendations and consequences), `FABRICATION_BLOCKERS.md` (everything that still prevents fabrication), `FIRMWARE_DESIGN_REVIEW.md`, `PROJECT_FILE_INDEX.md`, `PROGRESS_LOG.md`, and the 36-section `../report/PROJECT_ENGINEERING_REPORT.md`. Changes in this session:
> - **C305 47 nF → 2.2 µF.** Simulation showed the 4.7 ms soft start locks the LM51551 in hiccup, so 48 V would never come up.
> - ENC_I_M and VBAT_SENSE routed. kicad-cli CI run 4 on `a768755`: 0 copper errors, 0 parity, **22 unconnected**.
> - Closed-loop and cycle-by-cycle flyback simulations, runaway timing model, detailed BOM (`../bom_full.csv`), ST reference-firmware evidence.
>
> **BENCH-ONLY PROTOTYPE.** Use water or 0.9 % saline only. Never connect it to a person or an animal, and do not use real insulin.
>
> **NOT FABRICATION-APPROVED. NOT VALIDATED.** The design contains TBD and PLACEHOLDER parts, and no Rev A bench result exists yet. A clean ERC or DRC report does not prove the circuit works.

## 1. What this package is

This is a digitally complete Rev B board: hierarchical schematic, footprints, placed and routed 4-layer PCB, BOM and validation reports. It was built on the handoff design basis and the locked decisions K-1 to K-18. Unverified items appear in the design in three ways:

- A `Status` field on every part (`DECIDED`, `DS`, `CALC`, `ASSUMED`, `TBD`, `PLACEHOLDER`).
- DNP marks on undecided options.
- Placeholder footprints for undesigned blocks (the flyback transformer, the 48 V output switch).

Read these alongside this guide:

- `ASSUMPTIONS_AND_DEVIATIONS.md`: every assumption (A-1 to A-22) and every deviation from the handoff (DV-1 to DV-10).
- `UNRESOLVED_ISSUES.md`: critical, major and minor open items (U-xx).
- `../../decisions/DECISION_LOG.md` section 6: owner decisions made on 10 Oct 2026.
- `../bom.csv` (grouped) and `../bom_detailed.csv` (per part, with the source or justification for each value).

## 2. File map

| Path | Content |
| --- | --- |
| `hardware/kicad/pump_v2.kicad_pro` | KiCad 10 project: net classes (Default, PWR, HV48, RF) and board rules |
| `hardware/kicad/pump_v2.kicad_sch` + 7 sub-sheets | Hierarchical schematic (root plus power_input, power_3v3, power_48v, safety, mcu_main, mcu_supervisor, pmd_interface) |
| `hardware/kicad/pump_v2.kicad_pcb` | 4-layer PCB, 110 × 85 mm |
| `hardware/kicad/pump_v2.kicad_dru` | Custom DRC rule (scoped J703 exception only) |
| `hardware/kicad/pump_v2.kicad_sym`, `pump_v2.pretty/` | Project symbols (LM51551, BQ25188, TPS62840DLC, TBD FETs, transformer) and footprints (transformer placeholder, BQ25188 YBG unverified) |
| `scripts/design.py` | **Single source of truth**: every part, net, value, status and note |
| `scripts/gen_library.py`, `gen_schematic.py`, `gen_pcb.py`, `kicadlib.py` | Generators (see section 6) |
| `validation/erc/`, `validation/drc/` | Real kicad-cli reports (10 Oct; they describe the board BEFORE the 31 Oct layout fixes) |
| `validation/logs/*_2026-10-31.*` | 31 Oct layout-fix log and pcbcheck.py results (pure Python, not kicad-cli) |
| `scripts/pcbcheck.py`, `pcbedit.py`, `pcbroute.py`, `pcbsilk.py`, `pcbplot.py`, `layout_fixes.py`, `report_unrouted.py` | KiCad-free checker, editor, router and the 31 Oct fix procedure (need `pip install shapely numpy matplotlib`) |
| `docs/datasheets/` | Datasheets actually used (PMD401 manual 150025-01, TI LM51551, BQ25188, TPS62840, INA219) |

## 3. Architecture as implemented

```
1S protected cell -> J101 XT30 -> F101 5 A -> J102 (off-board master switch) -> VBAT
   VBAT_FUSED -> U101 BQ25188 BAT (charging only; SYS unloaded, E-09) <- J103 USB-C VBUS
   VBAT -> U201 TPS62840 -> +3V3 -> U501 WBA55, U601 C031, U701 MAX3485, encoder (JP701 default)
   VBAT -> U301 LM51551 non-isolated flyback (Q301 CSD16340Q3, D301 PNE20010ER + snubber; T301 PLACEHOLDER) -> +48V_RAW -> R311 0R (switch bypass) -> +48V_MOT -> J703 -> PMD401
Kill path (sheet "Kill path"): FLY_EN = LM51551 UVLO/EN
   R401 4.7k to GND (default OFF) | U501 PB7 -> R402 1k -> FLY_EN | Q401 BSS138 (gate = U601 PB0 SUP_VETO) shorts FLY_EN
   Gate default: R403 10k PULL-UP fitted (owner 10 Oct) -> veto ON unless U601 drives PB0 LOW
PMD401 servo connector J701 (SPI mode 3 <=500 kbit/s, SS, AEN) and status connector J702 (Ready, Fault):
   TVS + 100R on every line. AEN driven OPEN-DRAIN by Q402 BSS138 (gate = U601 PB1 SUP_PARK, R405 10k pull-up):
   parked by default; supervisor drives PB1 LOW to unpark (owner 10 Oct)
LL06 encoder J705 -> TVS -> 100R -> U501 TIM2 (PB6/PA8) and separately 100R -> U601 TIM3 (PA6/PA7) (S-07)
RS-485 setup link: U501 USART2 + DE -> U701 MAX3485 -> J704
Heartbeat / supervisor link: U501 LPUART1 (PB5 TX / PA1 RX) <-> U601 USART2 (PA3 RX / PA2 TX)
BLE: U501 RF -> pi-match placeholder (C514/L502/C515) -> J501 U.FL
```

## 4. MCU pin map (functions VERIFIED against the STM32CubeMX 6.18.1 database: validation/logs/pinmap_check.md)

### U501 STM32WBA55CGUx (UFQFPN48)

| Pin | Port | Net | Function |
| --- | --- | --- | --- |
| 13 | PA0 | PMD_SCLK_M | SPI3_SCK → PMD401 SPI_SCLK (mode 3) |
| 15 | PB8 | PMD_MOSI_M | SPI3_MOSI → PMD401 SPI_MOSI |
| 9 | PA5 | PMD_SS_M | SPI3_NSS (or GPIO) → PMD401 SPI_SS |
| 20 | PB6 | ENC_A_M | TIM2_CH1 encoder A |
| 5 | PA8 | ENC_B_M | TIM2_CH2 encoder B |
| 48 | PB14 | ENC_I_M | Encoder index (GPIO/EXTI) |
| 32 | PB0 | RS485_DI | USART2_TX |
| 29 | PA11 | RS485_RO | USART2_RX |
| 31 | PB1 | RS485_DE | USART2_DE (drives DE and /RE) |
| 21 | PB5 | HB_M2S | LPUART1_TX → supervisor |
| 12 | PA1 | HB_S2M | LPUART1_RX ← supervisor |
| 4 | PB12 | CON_MAIN_TX | USART1_TX bench console (TX only: PA8, the only USART1_RX pin, carries the encoder) |
| 7 | PA6 | I2C_SCL | I2C3_SCL (BQ25188) |
| 6 | PA7 | I2C_SDA | I2C3_SDA (BQ25188) |
| 19 | PB7 | MCU_48V_EN | GPIO out, drives FLY_EN via R402 1k |
| 33 | PB15 | PMD_READY_M | GPIO in (0 = ready) |
| 23 | PB4 | PMD_FAULT_M | GPIO in (1 = fault) |
| 28 | PA12 | FLY_PGOOD | GPIO in, LM51551 PGOOD |
| 10 | PA2 | CHG_INT_N | GPIO in / EXTI, BQ25188 /INT |
| 14 | PB9 | VBAT_SENSE | ADC4_IN10 (divider DNP, U-07) |
| 30 | PB2 | LED_MAIN | Status LED |
| 27 / 26 / 24 | PA13 / PA14 / PB3 | MAIN_SWDIO / SWCLK / SWO | SWD → J502 |
| 34 | PH3 | MAIN_BOOT0 | 10k pull-down (verify BOOT0 function) |
| 36 | NRST | MAIN_NRST | J502 pin 10, 100 nF |
| 37 | RF | RF_MCU | BLE RF → pi-match → U.FL |
| 41 / 42 | OSC_OUT / OSC_IN | HSE_OUT / HSE_IN | 32 MHz crystal Y501 |
| 16 / 17 | PC15 / PC14 | LSE_OUT / LSE_IN | Optional 32.768 kHz (DNP) |
| NC | PA15, PC13, PA10, PA9 | — | Spare |

### U601 STM32C031C6Tx (LQFP48 assumed)

| Pin | Port | Net | Function |
| --- | --- | --- | --- |
| 19 | PB0 | SUP_VETO | GPIO out → Q401 gate (HIGH or high-Z = veto ON via R403; drive LOW to permit 48 V) |
| 20 | PB1 | SUP_PARK | GPIO out → Q402 gate (HIGH or high-Z = AEN low = PARK; drive LOW to unpark) |
| 17 | PA6 | ENC_A_S | TIM3_CH1 own encoder count (S-07) |
| 18 | PA7 | ENC_B_S | TIM3_CH2 |
| 13 | PA2 | HB_S2M | USART2_TX → main |
| 14 | PA3 | HB_M2S | USART2_RX ← main |
| 29 / 32 | PA9 / PA10 | CON_SUP_TX / RX | USART1 console |
| 21 | PB2 | LED_SUP | Status LED |
| 35 / 36 | PA13 / PA14 | SUP_SWDIO / SWCLK | SWD → J601 (PA14 shares BOOT0) |
| 10 | PF2 | SUP_NRST | NRST (PF2-NRST assumed) |

All other C031 GPIOs carry no-connect flags.

## 5. Validation status (actual tool output)

See section 8 for the numbers from the final run. The report files are in `validation/erc/` and `validation/drc/`.

Distinguish three levels of validation:

1. **Software validation (done):** ERC and DRC runs, plus schematic-to-PCB parity.
2. **Bench validation (not done):** the entire `requirements/VALIDATION_PLAN.md`.
3. **Manufacturing acceptance (not started):** no fab, no DFM review, no Gerbers.

## 6. Regenerating the design

The KiCad files are generated, so edit `scripts/design.py` rather than the schematic when changing circuit content. Hand edits in KiCad are fine once you stop regenerating, but **regenerating overwrites the schematic, and `gen_pcb.py place` overwrites the PCB**, including routing. Commit first.

```bash
python scripts/gen_library.py                     # project symbols/footprints
python scripts/gen_schematic.py                   # .kicad_sch + .kicad_pro net classes
kicad-cli sch export netlist --format kicadsexpr -o hardware/kicad/pump_v2.net hardware/kicad/pump_v2.kicad_sch
"C:\Program Files\KiCad\10.0\bin\python.exe" scripts/gen_pcb.py place          # board, placement, planes
"C:\Program Files\KiCad\10.0\bin\python.exe" scripts/gen_pcb.py dsn  <file.dsn> # Specctra export (outer pours excluded, inner layers marked 'power')
#   Freerouting 2.1.0 (Java 21); disable telemetry in freerouting.json first:
#   java -jar freerouting-2.1.0.jar -de file.dsn -do file.ses --gui.enabled=false --router.job_timeout=00:12:00
#   (2.1.0 ignores -mp; repeat dsn -> route -> ses for incremental passes)
"C:\Program Files\KiCad\10.0\bin\python.exe" scripts/gen_pcb.py ses  <file.ses> # import routes, refill zones
kicad-cli sch erc --format report --severity-all -o validation/erc/pump_v2-erc.rpt hardware/kicad/pump_v2.kicad_sch
kicad-cli pcb drc --format report --severity-all --schematic-parity --refill-zones --save-board -o validation/drc/pump_v2-drc.rpt hardware/kicad/pump_v2.kicad_pcb
bash scripts/run_checks.sh                        # ERC, DRC (+parity), BOMs
```

Freerouting and the Java runtime were used from a temporary folder and are **not** part of the repository.

## 7. Recommended next steps (in order)

1. Get the **ST STM32WBA55CG and STM32C031C6 datasheets** and the WBA hardware/RF design guide. Then wire the six placeholder supply pins, decoupling, SMPS, HSE and RF match (U-05). This removes the 6 ERC errors properly.
2. **Owner/successor decisions:** veto gate default (U-01), AEN pull-down after IF-02 (U-02), VBAT sensing (U-07), battery/charger connectors (U-18).
3. **Design the flyback** (U-04): choose the transformer and replace the placeholder footprint, then Q301, D301, R305, clamp, RT/SS/compensation. Simulate in LTspice, including transient response, TX-burst droop on 3V3, and the 60 V fault ceiling.
4. Recreate both pin maps in **STM32CubeMX** and fix any conflicts (U-10, U-11).
5. Verify every footprint against its drawing (BQ25188 YBG pitch U-12, connector orientations U-17). Choose a fab and import its rules and stack-up (U-16, U-20).
6. Re-route by hand where the autorouter is weak: 48 V loop, flyback switching loop (P-03/L-5 proposed), RF trace, battery path width (IPC-2152 for 2.1 A).
7. Only then: Rev A bench results (DA, OC, SG, FT groups), engineering review, release checks, then Gerbers (CLAUDE.md Phase 6).

## 8. Final run results (kicad-cli 10.0.3, 10 Oct 2026)

> These are the results for the board **before** the 31 Oct 2026 layout fixes (commit `976a17b`). The reports are now in `validation/*/baseline_2026-10-10/`.
>
> **Current board (1 Nov 2026), real kicad-cli 10.0.4 in GitHub Actions on commit `ef091c3`:**
> - ERC: 6 × `power_pin_not_driven` (intentional) + 1 × `lib_symbol_mismatch` (U701).
> - DRC: **0 copper errors, 0 schematic-parity issues, 24 unconnected**, 69/52/1 silkscreen warnings.
>
> See `validation/KICAD_CI_PROVENANCE.md` and `../report/PROJECT_ENGINEERING_REPORT.md` §16. To re-run, push to the branch (`.github/workflows/kicad-checks.yml`) or run `scripts/run_checks.sh` locally.

Reproduce with `bash scripts/run_checks.sh`. The reports are `validation/erc/pump_v2-erc.rpt` and `validation/drc/pump_v2-drc.rpt`.

### ERC: 6 errors, 1 warning (none excluded or suppressed)

| Count | Type | Cause | Action |
| --- | --- | --- | --- |
| 6 | `power_pin_not_driven` (error) | U501 VLXSMPS, VDD11, VDDANA, VDDHPA, VDDRF and VDDRFPA sit on their own placeholder nets because their correct connection is unknown without the ST datasheet | **Intentional and genuine.** Resolve per U-05, not by adding PWR_FLAGs |
| 1 | `lib_symbol_mismatch` (warning) | U701 MAX3485: the generator's flattening of the derived library symbol | Cosmetic (U-30). In Eeschema use *Update Symbols from Library* |

### DRC (with `--schematic-parity --refill-zones`)

| Count | Type | Meaning |
| --- | --- | --- |
| 0 | clearance / shorting / hole / edge / courtyard | **No copper rule violations.** HV48 nets hold 0.6 mm everywhere except inside J703, under the scoped rule in `pump_v2.kicad_dru` (vendor JST SH 1.0 mm pitch, U-17) |
| 0 | schematic parity | Footprints, values, fields and DNP/BOM attributes match the schematic |
| 63 | `unconnected_items` | **Routing is incomplete**: 63 connections on 55 nets (list in `validation/logs/unrouted_nets.txt`). Mostly MCU signal escapes, the flyback control nets and the PMD401 interface (U-21) |
| 10 | `via_dangling` | Router leftover vias; delete or reuse during hand routing |
| 3 | `starved_thermal` | Thermal relief with fewer than 2 spokes (USB-C shield pad, two fine-pitch GND pads); review |
| 65 / 47 / 3 | silkscreen overlap / over copper / edge | Cosmetic; tidy before any fabrication |
| 2 | `nonmirrored_text_on_back_layer` | The two bottom-silk disclaimer lines; mirror them in pcbnew |

### Routing method and limits

- **Planes:** In1.Cu is a solid GND plane. In2.Cu is split: VBAT under the battery strip, along a bottom band and under the 48 V block; +3V3 everywhere else. F.Cu and B.Cu carry GND pours.
- **Fan-out:** 143 of 148 SMD plane-net pads were fanned out by script to vias into their plane (`validation/logs/fanout_unconnected.txt` lists the rest).
- **Signal routing:** Freerouting 2.1.0 ran three passes (one full, two incremental) with a 12-minute job limit each. Its own counts plateaued at about 40–65 unrouted. Freerouting telemetry and analytics were switched off after the first runs (its defaults had them enabled).
- **Not done by any automated step:**
  - Impedance control: the RF trace is not 50 Ω controlled.
  - Switching-loop minimisation for the flyback.
  - IPC-2152 current-width checks on the battery path.
  - Length or skew checks.
  - Hand review of every routed segment.

  **The routing is a starting point, not a reviewed layout.**

### BOM

- `docs/bom.csv`: 74 grouped lines.
- `docs/bom_detailed.csv`: 131 placed references, each with its Status and a source/justification note.
- Status breakdown: DECIDED 23, DS 14, CALC 2, ASSUMED 34, TBD 27, PLACEHOLDER 31. 24 references are DNP.
- Test points, mounting holes and PWR_FLAGs are excluded from the BOM.

### Images and PDF

- `images/pcb_placement_fab.png`: placement and courtyards.
- `images/pcb_routed_top_bottom.png`: F.Cu and B.Cu copper with silkscreen (10 Oct board).
- `images/fix_2026-10-31_*.png`: plots of the areas changed on 31 Oct (drawn by `scripts/pcbplot.py`, not KiCad).
- `pump_v2_schematic.pdf`: all 8 schematic sheets.
