# Project file index (1 Nov 2026)

| Path | Content | Maintained by |
| --- | --- | --- |
| `CLAUDE.md` | Project rules and status line | hand |
| `PROJECT_OVERVIEW.md`, `requirements/`, `docs/SOURCE_DOCUMENTS.md` | Original requirements (preserved), constraints, validation plan, open questions, BOM history | hand (originals unchanged) |
| `decisions/DECISION_LOG.md` | Every decision, sections 1–10 | hand |
| **Design source** | | |
| `scripts/design.py` | Single source of truth: every part, value, net, status and note | hand |
| `scripts/gen_library.py`, `gen_schematic.py`, `gen_pcb.py`, `kicadlib.py` | Generators. Regeneration needs the KiCad 10 standard libraries and overwrites `hardware/kicad/`, so commit first | — |
| `hardware/kicad/` | KiCad 10 project: `pump_v2.kicad_pro/.kicad_sch` (8 sheets)/`.kicad_pcb`, project symbol and footprint library, DRU | generators + layout scripts |
| **Layout tooling (KiCad-free)** | | |
| `scripts/pcbcheck.py`, `pcbedit.py`, `pcbroute.py`, `pcbsilk.py`, `pcbplot.py`, `report_unrouted.py`, `unrouted_corridors.py`, `hand_route.py` | Checker (approximation of DRC), S-expression editor, grid router, plotting | — |
| `scripts/layout_fixes.py`, `layout_fixes_2.py`, `layout_fixes_3.py` | Reproducible layout edits of 31 Oct, 1 Nov, 1 Nov (completion) | — |
| **Verification** | | |
| `.github/workflows/kicad-checks.yml` | kicad-cli 10.0.4 ERC, DRC with parity, BOM export on every hardware push | — |
| `validation/erc/`, `validation/drc/`, `validation/KICAD_CI_PROVENANCE.md` | Current kicad-cli reports (CI run 4, `a768755`) and their provenance; 10 Oct baseline subfolders | copied from CI log |
| `validation/logs/` | pcbcheck results, layout-fix logs, pin-map check, calculation audit, runaway timing, ST reference evidence | scripts |
| `scripts/verify_pinmap.py`, `scripts/run_checks.sh` | Pin-map check; local KiCad check commands | — |
| **Calculations and simulations** | | |
| `scripts/audit_calcs.py` → `validation/logs/report_audit_calcs.txt` | Every calculated figure in the report | — |
| `scripts/sim_flyback_ngspice.py` → `validation/sim/ngspice/` | Level 1: open-loop power stage (ngspice re-run of `validation/sim/flyback_openloop.cir`, LTspice) | — |
| `scripts/sim_flyback_closedloop.py` → `validation/sim/ngspice_closedloop/` | Level 2: behavioural closed-loop switching model; startup, load steps, faults | — |
| `scripts/sim_flyback_cycle.py` → `validation/sim/cycle_model/` | Level 3: cycle-by-cycle model with hiccup; soft-start sizing, open-FB fault, short | — |
| `scripts/runaway_timing.py` → `validation/logs/runaway_timing.txt` | Runaway fault-response timing | — |
| **BOM** | | |
| `docs/bom.csv`, `docs/bom_detailed.csv` | kicad-cli BOM exports (CI) | CI |
| `scripts/gen_bom_full.py` → `docs/bom_full.csv`, `docs/bom_full_summary.md` | Detailed engineering BOM with selection classes; consistency check against the kicad-cli export | — |
| `docs/datasheets/` | Manufacturer datasheets used as [DS] evidence | — |
| **Documentation** | | |
| `docs/report/PROJECT_ENGINEERING_REPORT.md`, `docs/report/figures/` | 36-section engineering report and figures | hand + scripts |
| `docs/handover/OWNER_APPROVAL_SHEET.md` | The 17 decisions needed, with recommendations | hand |
| `docs/handover/FABRICATION_BLOCKERS.md` | Everything that still prevents fabrication | hand |
| `docs/handover/FIRMWARE_DESIGN_REVIEW.md` | Phase D review; firmware not implemented | hand |
| `docs/handover/PROGRESS_LOG.md` | Live progress record for resuming work | hand |
| `docs/handover/HANDOVER_GUIDE.md`, `FINAL_HANDOVER.md` | Handover entry points | hand |
| `docs/handover/UNRESOLVED_ISSUES.md`, `ASSUMPTIONS_AND_DEVIATIONS.md` | Issue register U-xx, assumptions A-xx and deviations DV-xx | hand |
| `docs/handover/FLYBACK_DESIGN.md` | Flyback design and transformer specification | hand |
| `docs/handover/FINAL_ENGINEERING_REVIEW_2026-11-01.md`, `ENGINEERING_BLOCKER_REVIEW_2026-11-01.md`, `BLOCKER_RESOLUTION_REPORT.md`, `LAYOUT_FIXES_*.md` | Earlier reviews and layout reports (history) | — |
| `manufacturing/` | Does not exist: Phase 6 only, after review | — |
