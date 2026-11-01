# Provenance of the KiCad reports in `validation/erc/` and `validation/drc/`

| Item | Value |
| --- | --- |
| Tool | `kicad-cli` **10.0.4** (official Docker image `kicad/kicad:10.0.4-full`; 10.0.3, the version in CLAUDE.md, has no image) |
| Where it ran | GitHub Actions, GitHub-hosted runner, workflow `.github/workflows/kicad-checks.yml` (read-only: board not saved) |
| Run | [kicad-checks run 8](https://github.com/BigBiglinn/INSULIN_PUMP/actions/runs/41278158464), job 124764458377, 1 Nov 2026 (earlier: runs 2, 4, 5, 6, 7) |
| Board / schematic | commit `32c4a8b` (`hardware/kicad/pump_v2.kicad_pcb`, `pump_v2.kicad_sch`) |
| Commands | `kicad-cli sch erc --format report --severity-all`; `kicad-cli pcb drc --format report --severity-all --schematic-parity --refill-zones` |
| Library tables | KiCad's shipped default `sym-lib-table` / `fp-lib-table` installed in the job's HOME (without them every symbol and footprint reports a library issue) |
| How the files got here | Copied verbatim from the job log (the job prints both reports between `=====BEGIN/END ... REPORT=====` markers); line endings converted to CRLF to match the repository |

Summary of these reports (current board):

| Check | Result |
| --- | --- |
| ERC | 6 × `power_pin_not_driven` (intentional STM32WBA55 placeholders, U-05) + 1 × `lib_symbol_mismatch` (U701 MAX3485, cosmetic) — identical to the 10 Oct baseline (the C305 value change in `a768755` did not change ERC) |
| DRC copper (clearance, shorts, holes, edge, courtyards, dangling, thermals) | **0** |
| Schematic parity | **0** issues |
| Unconnected items | **19** (22 on `a768755`; U101 escapes routed in `ab2eba2`) |
| Silkscreen | 69 overlap, 52 over copper, 1 board edge |
| Footprint/library | 0 footprint errors; the `lib_footprint_mismatch` on U101 seen in run 7 is gone after `32c4a8b` |
| Export dry run | Gerbers (4 copper layers + mask/paste/silk/Edge.Cuts) and Excellon drill generated with `--check-zones`; inspected by `scripts/inspect_fab_outputs.py` → `validation/logs/fab_dryrun.txt`. **Not a release** |

BOM exports `docs/bom.csv` and `docs/bom_detailed.csv` come from the same run (only C305 changed).
The 10 Oct kicad-cli 10.0.3 reports of the earlier board are kept in `baseline_2026-10-10/` for comparison.
The first CI run ([run 1](https://github.com/BigBiglinn/INSULIN_PUMP/actions/runs/41266999207), board of commit `ab69cdf`) found 28 unconnected, 0 copper errors and **3 dangling track ends**, which the 31 Oct Python checker had missed; they were removed in `ef091c3`.
A clean ERC/DRC report does not show that the circuit works.
