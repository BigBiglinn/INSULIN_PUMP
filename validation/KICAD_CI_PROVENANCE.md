# Provenance of the KiCad reports in `validation/erc/` and `validation/drc/`

| Item | Value |
| --- | --- |
| Tool | `kicad-cli` **10.0.4** (official Docker image `kicad/kicad:10.0.4-full`; 10.0.3, the version in CLAUDE.md, has no image) |
| Where it ran | GitHub Actions, GitHub-hosted runner, workflow `.github/workflows/kicad-checks.yml` (read-only: board not saved) |
| Run | [kicad-checks run 4](https://github.com/BigBiglinn/INSULIN_PUMP/actions/runs/41272581019), job 124748205593, 1 Nov 2026 (earlier: run 2, job 124732911164, board `ef091c3`) |
| Board / schematic | commit `a768755` (`hardware/kicad/pump_v2.kicad_pcb`, `pump_v2.kicad_sch`) |
| Commands | `kicad-cli sch erc --format report --severity-all`; `kicad-cli pcb drc --format report --severity-all --schematic-parity --refill-zones` |
| Library tables | KiCad's shipped default `sym-lib-table` / `fp-lib-table` installed in the job's HOME (without them every symbol and footprint reports a library issue) |
| How the files got here | Copied verbatim from the job log (the job prints both reports between `=====BEGIN/END ... REPORT=====` markers); line endings converted to CRLF to match the repository |

Summary of these reports (current board):

| Check | Result |
| --- | --- |
| ERC | 6 × `power_pin_not_driven` (intentional STM32WBA55 placeholders, U-05) + 1 × `lib_symbol_mismatch` (U701 MAX3485, cosmetic) — identical to the 10 Oct baseline (the C305 value change in `a768755` did not change ERC) |
| DRC copper (clearance, shorts, holes, edge, courtyards, dangling, thermals) | **0** |
| Schematic parity | **0** issues |
| Unconnected items | **22** (24 on `ef091c3`; ENC_I_M and VBAT_SENSE routed in `a768755`) |
| Silkscreen | 69 overlap, 52 over copper, 1 board edge |

BOM exports `docs/bom.csv` and `docs/bom_detailed.csv` come from the same run (only C305 changed).
The 10 Oct kicad-cli 10.0.3 reports of the earlier board are kept in `baseline_2026-10-10/` for comparison.
The first CI run ([run 1](https://github.com/BigBiglinn/INSULIN_PUMP/actions/runs/41266999207), board of commit `ab69cdf`) found 28 unconnected, 0 copper errors and **3 dangling track ends**, which the 31 Oct Python checker had missed; they were removed in `ef091c3`.
A clean ERC/DRC report does not show that the circuit works.
