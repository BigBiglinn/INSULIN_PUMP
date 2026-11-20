"""Generate the report appendices (docs/project_report/src/90_appendix.md) from repository files,
so that the appendices always reproduce the current requirement, decision, validation and BOM records
verbatim. Run from the repository root:  python scripts/report_appendix.py
"""
import os, re, csv, subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "docs", "project_report", "src", "90_appendix.md")
o = []
w = o.append
n = [0]


def tables_under(path, heading_regex, stop_regex=r"^## "):
    """Yield (subheading, table_lines) for markdown tables inside the section matching heading_regex."""
    lines = open(os.path.join(ROOT, path), encoding="utf-8").read().splitlines()
    on, sub, tbl = False, None, []
    for ln in lines + [""]:
        if re.match(heading_regex, ln):
            on = True; sub = re.sub(r"^#+\s*", "", ln); continue
        if on and re.match(stop_regex, ln) and not re.match(heading_regex, ln):
            if tbl:
                yield sub, tbl; tbl = []
            on = False; continue
        if not on:
            continue
        if ln.startswith("###"):
            if tbl:
                yield sub, tbl; tbl = []
            sub = re.sub(r"^#+\s*", "", ln); continue
        if ln.startswith("|"):
            tbl.append(ln)
        elif tbl:
            yield sub, tbl; tbl = []


def emit(caption, tbl, widths=""):
    n[0] += 1
    w(f"!table tab:app{n[0]} | {caption}" + (f" | {widths}" if widths else ""))
    o.extend(tbl)
    w("")


def code_file(path, caption):
    w(f"!code {path} | {caption}")
    w("")


# ------------------------------------------------------------------ A requirements
w("@appendix Requirements Register {#app:req}")
w("This appendix reproduces the technical requirements from `requirements/DESIGN_REQUIREMENTS.md` without "
  "change. Status is as recorded: **Decided** requirements are binding; **Proposed** requirements were written "
  "from standard practice and still need the owner's sign-off. Check IDs refer to Appendix C.")
w("")
for sub, tbl in tables_under("requirements/DESIGN_REQUIREMENTS.md", r"^## 3\. Requirements"):
    emit(f"Requirements: {sub}", tbl, "0.6,1.4,3.2,1,1")
for sub, tbl in tables_under("requirements/DESIGN_REQUIREMENTS.md", r"^## 4\. Non-functional"):
    emit("Non-functional requirements", tbl, "1,4,1.2")
for sub, tbl in tables_under("requirements/DESIGN_REQUIREMENTS.md", r"^## 5\. Standards"):
    emit("Standards and how far each is followed (the pump is not certified to any of them)", tbl, "2,3")
w("## Hardware constraints")
w("The interface requirements and Rev B layout restrictions are reproduced below from `requirements/HARDWARE_CONSTRAINTS.md`.")
w("")
for sub, tbl in tables_under("requirements/HARDWARE_CONSTRAINTS.md", r"^## 5\. Interface"):
    emit("Interface requirements", tbl, "1.4,3.4,1.6")
for sub, tbl in tables_under("requirements/HARDWARE_CONSTRAINTS.md", r"^## 6\. Layout"):
    emit("Rev B layout restrictions", tbl, "0.5,4,1.4")

# ------------------------------------------------------------------ B decisions and open questions
w("@appendix Decision Log, Open Questions and Document Conflicts {#app:dec}")
w("Reproduced from `decisions/DECISION_LOG.md` and `requirements/OPEN_QUESTIONS.md`.")
w("")
for sub, tbl in tables_under("decisions/DECISION_LOG.md", r"^## 2\. Chronological"):
    emit(f"Decision log: {sub}", tbl, "0.7,3.2,2.6,1.4")
for h in (r"^## 6\.", r"^## 7\.", r"^## 8\.", r"^## 9\."):
    for sub, tbl in tables_under("decisions/DECISION_LOG.md", h):
        emit(f"Decision log: {sub}", tbl, "0.7,3.2,2.6,1.4")
for sub, tbl in tables_under("requirements/OPEN_QUESTIONS.md", r"^## A\. "):
    emit("Open items carried from the 10 Oct 2026 report", tbl, "0.4,2,2.2,2.6")
for sub, tbl in tables_under("requirements/OPEN_QUESTIONS.md", r"^## C\. "):
    emit("Contradictions between project documents (CF-1 to CF-23)", tbl, "0.6,2.4,2.4,1.8")

# ------------------------------------------------------------------ C validation plan
w("@appendix Validation Plan {#app:vplan}")
w("The complete bench validation plan from `requirements/VALIDATION_PLAN.md`. **No check has a recorded result.** "
  "Groups run in order; if any kill-path (SG) check fails, testing stops until it passes.")
w("")
for sub, tbl in tables_under("requirements/VALIDATION_PLAN.md", r"^## Part A\."):
    emit("Part A: Rev B board checks", tbl, "0.6,1.6,3,2.4")
for sub, tbl in tables_under("requirements/VALIDATION_PLAN.md", r"^## Part B\.", stop_regex=r"^## Part C"):
    emit(f"Bench checks: {sub}", tbl, "0.6,1.6,3,2.4")
for sub, tbl in tables_under("requirements/VALIDATION_PLAN.md", r"^## Part D\."):
    emit("Checks run once, then only after a change", tbl, "3,3")

# ------------------------------------------------------------------ D BOM
w("@appendix Bills of Materials {#app:bom}")
w("## Rev A bench build (37 lines)")
w("Reproduced from `requirements/COMPONENTS_AND_BOM.md` section 1.")
w("")
for sub, tbl in tables_under("requirements/COMPONENTS_AND_BOM.md", r"^## 1\. Rev A"):
    emit(f"Rev A parts: {sub}", tbl, "0.4,2.6,0.5,2,2.2")
w("## Rev B board (144 references)")
w("Generated from `docs/bom_detailed.csv` (kicad-cli export at `pcb-p6-final`). The per-part justification is in "
  "the `Note` field of that file and in `scripts/design.py`. DNP = not fitted.")
w("")
rows = list(csv.DictReader(open(os.path.join(ROOT, "docs/bom_detailed.csv"), encoding="utf-8")))
tbl = ["| Ref | Value | MPN | Status | DNP |"]
for r in rows:
    tbl.append(f"| {r['Ref']} | {r['Value']} | {r['MPN'] or '–'} | {r['Status']} | {'DNP' if r['DNP'].strip() else ''} |")
emit("Rev B bill of materials", tbl, "0.8,1.6,2.6,1,0.5")

# ------------------------------------------------------------------ E reports
w("@appendix Archived Tool Reports and Re-run Outputs {#app:reports}")
w("## KiCad reports at pcb-p6-final")
for path, cap in (("validation/erc/pump_v2-erc.rpt", "Final ERC report (kicad-cli 10.0.3)"),
                  ("validation/drc/pump_v2-drc.rpt", "Final DRC report (kicad-cli 10.0.3, schematic parity, zones refilled)"),
                  ("validation/logs/p6_strict_erc.rpt", "ERC with every ignored check enabled (scratch copy)"),
                  ("validation/logs/p6_netlist_audit.txt", "Pad-net audit against the netlist")):
    code_file(path, cap)
w("## Pin-map check summary")
for sub, tbl in tables_under("validation/logs/pinmap_check.md", r"^## U501", stop_regex=r"^## U601"):
    emit("STM32CubeMX 6.18.1 pin check, U501 STM32WBA55CGUx", tbl, "0.5,1.5,0.7,1.6,1.4,1")
for sub, tbl in tables_under("validation/logs/pinmap_check.md", r"^## U601", stop_regex=r"^\*\*Result"):
    emit("STM32CubeMX 6.18.1 pin check, U601 STM32C031C6Tx", tbl, "0.5,1.5,0.7,1.6,1.4,1")
w("## Outputs re-run for this report (20 Nov 2026)")
for f, cap in (("design_calcs.txt", "scripts/review/design_calcs.py"),
               ("lm51551_startup.txt", "validation/sim/lm51551_startup.py"),
               ("flyback_layout_sens.txt", "scripts/review/run_flyback_sens.sh (ngspice 42)"),
               ("rf_line_solver.txt", "validation/sim/rf_line_solver.py"),
               ("rf_eco1_widths.txt", "rf_line_solver.solve() at the two as-built widths"),
               ("sch_netlist_check.txt", "scripts/review/sch_netlist_check.py"),
               ("energy_estimate.txt", "scripts/report_energy_estimate.py")):
    code_file(f"docs/project_report/evidence/{f}", f"Output of {cap}")
w("## Simulation logs")
for path, cap in (("validation/sim/flyback_openloop.log", "LTspice open-loop flyback log"),
                  ("validation/sim/q301/RESULTS.md", "Q301 stress results")):
    code_file(path, cap)

# ------------------------------------------------------------------ F code
w("@appendix Code Listings {#app:code}")
w("## v1 HybridPancreasSim (C++)")
w("!box Pending. | The v1 C++ sources (`BergmanModel.h`, `Controllers.h` and the rest of the merged codebase) "
  "and the v2 reference firmware (`pump_fw.zip`) will be listed here once they are committed to the repository. "
  "They are not reproduced from memory.")
w("")
w("## Project scripts")
w("The table lists every script in the repository with its length and purpose. The scripts that define the "
  "circuit or produce the numbers in Chapter 5 are listed in full after it.")
w("")
purpose = {
    "design.py": "Single source of truth: every part, value, footprint, net, status and note",
    "gen_library.py": "Writes the project symbol and footprint library", "gen_schematic.py": "Writes the 8 schematic sheets and net classes",
    "gen_pcb.py": "Board outline, placement, planes, fan-out, Specctra DSN/SES exchange", "kicadlib.py": "KiCad S-expression helpers",
    "hand_route.py": "Applies explicit routes from the DRC report", "grid_route.py": "Grid router for staged connections",
    "route_stage.py": "Applies a reviewed JSON route stage", "pcb_eco.py": "Applies footprint and placement changes after an ECO",
    "pcb_silk.py": "Silkscreen clean-up", "pcb_outline.py": "Board outline change", "pcb_rf_mask.py": "Opens the solder mask over the RF line",
    "eval_placement.py": "Scores placement variants on scratch copies", "compare_placement.py": "Compares placement variants",
    "compare_stage.py": "Compares a routing stage with its checkpoint", "reconcile_unrouted.py": "Classifies unconnected items",
    "unrouted_corridors.py": "Finds free straight corridors for unrouted pairs", "review_clearance.py": "Clearance margins along routes",
    "verify_pinmap.py": "Checks MCU pin functions against the STM32CubeMX database", "run_checks.sh": "ERC, DRC with parity, BOM export",
    "report_figures.py": "Figures of this report", "report_energy_estimate.py": "Energy estimate of Chapter 5",
    "report_appendix.py": "Generates these appendices", "build_project_report.py": "Builds this report (DOCX and PDF)",
}
tbl = ["| Script | Lines | Purpose |"]
for f in sorted(os.listdir(os.path.join(ROOT, "scripts"))):
    p = os.path.join(ROOT, "scripts", f)
    if os.path.isfile(p) and f.endswith((".py", ".sh")):
        tbl.append(f"| `scripts/{f}` | {sum(1 for _ in open(p, encoding='utf-8'))} | {purpose.get(f, '')} |")
for f in sorted(os.listdir(os.path.join(ROOT, "scripts", "review"))):
    p = os.path.join(ROOT, "scripts", "review", f)
    if os.path.isfile(p) and not f.endswith(".pyc"):
        tbl.append(f"| `scripts/review/{f}` | {sum(1 for _ in open(p, encoding='utf-8'))} | Independent review checker |")
for f in ("validation/sim/lm51551_startup.py", "validation/sim/rf_line_solver.py"):
    tbl.append(f"| `{f}` | {sum(1 for _ in open(os.path.join(ROOT, f), encoding='utf-8'))} | Simulation model |")
emit("Scripts in the repository", tbl, "2.6,0.6,3.6")
for path, cap in (("scripts/design.py", "Listing F.1: scripts/design.py (circuit definition)"),
                  ("validation/sim/lm51551_startup.py", "Listing F.2: LM51551 cycle-by-cycle start-up model"),
                  ("validation/sim/rf_line_solver.py", "Listing F.3: 2-D finite-difference RF line solver"),
                  ("scripts/review/design_calcs.py", "Listing F.4: independent design calculations"),
                  ("scripts/verify_pinmap.py", "Listing F.5: MCU pin-map check against STM32CubeMX"),
                  ("scripts/run_checks.sh", "Listing F.6: KiCad check script"),
                  ("scripts/report_energy_estimate.py", "Listing F.7: energy estimate")):
    code_file(path, cap)

# ------------------------------------------------------------------ G files
w("@appendix Repository Map and Reproduction {#app:files}")
w("Repository: `BigBiglinn/INSULIN_PUMP`, branch `master` at the merge of pull request #2 (commit `38cb21c`). "
  "Design of record: tag `pcb-p6-final`.")
w("")
tbl = ["| Path | Content |",
       "| `PROJECT_OVERVIEW.md`, `CLAUDE.md` | Project purpose, rules and workflow |",
       "| `requirements/` | Design requirements, hardware constraints, components and BOM, open questions, validation plan |",
       "| `decisions/DECISION_LOG.md` | Every decision with date, rationale and status |",
       "| `hardware/kicad/` | KiCad 10 project: 8 schematic sheets, 4-layer PCB, project library, rules |",
       "| `scripts/` | Design source, generators, routing tools, checks, report builders |",
       "| `validation/erc`, `validation/drc` | kicad-cli reports |",
       "| `validation/sim` | LTspice decks and logs, start-up model, RF solver, Q301 study |",
       "| `validation/routing`, `validation/placement`, `validation/logs` | Stage specifications, comparisons and logs |",
       "| `docs/handover/` | Handover guide, status, ECO records, PCB stages, assumptions, unresolved issues |",
       "| `docs/review/` | Independent design review |",
       "| `docs/datasheets/` | Datasheets actually used (PMD401, LM51551, BQ25188, TPS62840, CSD16340Q3, PNE20010ER, PMEG10020ELR, BSS138, INA219) |",
       "| `docs/project_report/` | This report, its source, figures and the re-run evidence |"]
emit("Repository map", tbl, "2.4,4")
w("To regenerate this report and its evidence from the repository root:")
w("")
w("!codeblock")
for c in ("python scripts/review/sch_netlist_check.py > docs/project_report/evidence/sch_netlist_check.txt",
          "python scripts/review/pcb_check.py        > docs/project_report/evidence/pcb_check.txt",
          "python scripts/review/design_calcs.py     > docs/project_report/evidence/design_calcs.txt",
          "sh scripts/review/run_flyback_sens.sh     > docs/project_report/evidence/flyback_layout_sens.txt   # ngspice >= 42",
          "(cd validation/sim && python lm51551_startup.py) > docs/project_report/evidence/lm51551_startup.txt",
          "(cd validation/sim && python rf_line_solver.py)  > docs/project_report/evidence/rf_line_solver.txt",
          "python scripts/report_energy_estimate.py",
          "python scripts/report_figures.py",
          "python scripts/report_appendix.py",
          "python scripts/build_project_report.py        # needs LibreOffice, poppler-utils, python-docx",
          "bash scripts/run_checks.sh                    # KiCad 10.0.x: ERC, DRC with parity, BOMs"):
    w(c)
w("!endcode")
w("")

open(OUT, "w", encoding="utf-8").write("\n".join(o) + "\n")
print("wrote", OUT, "tables:", n[0])
