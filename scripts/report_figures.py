"""Figures for the project report (docs/project_report/figures/).

Every number plotted here is read from a file in the repository, or copied from the
document named in the comment beside it. Nothing is measured on hardware: the project
has no hardware results. Run from the repository root:  python scripts/report_figures.py
"""
import os, re, csv, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "docs", "project_report", "figures")
EVD = os.path.join(ROOT, "docs", "project_report", "evidence")
os.makedirs(OUT, exist_ok=True)

# Palette: validated categorical slots 1-3 (dataviz reference palette, light mode)
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d3"
FILL = {"pwr": "#e8f0fb", "hv": "#fdebe3", "mcu": "#e6f6ef", "safe": "#f3f2ee", "ext": "#ffffff"}

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "savefig.dpi": 220, "savefig.bbox": "tight",
})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name))
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- diagram helpers
def box(ax, x, y, w, h, text, kind="ext", fs=8.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=FILL[kind], ec=INK2, lw=0.9))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
            fontweight="bold" if bold else "normal", linespacing=1.15)
    return (x, y, w, h)


def arrow(ax, p, q, text=None, color=INK2, style="-|>", ls="-", fs=7.5, off=(0, 0.08)):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=9, lw=1.0, color=color, ls=ls))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha="center", va="bottom",
                fontsize=fs, color=INK2)


def canvas(w, h, W=10, H=6):
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def wire(ax, pts, color=INK2, label=None, lpos=None, ha="left", head=True, both=False):
    """Orthogonal polyline with an arrow head on the last segment."""
    xs, ys = zip(*pts)
    ax.plot(xs[:-1] if head else xs, ys[:-1] if head else ys, color=color, lw=1.1, solid_capstyle="butt")
    if head:
        ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="<|-|>" if both else "-|>",
                                     mutation_scale=9, lw=1.1, color=color))
    if label:
        ax.text(lpos[0], lpos[1], label, fontsize=7.5, color=INK2, ha=ha, va="center",
                bbox=dict(fc="white", ec="none", pad=0.4))


def block_diagram():
    fig, ax = canvas(24.5, 15, 10.5, 6.6)
    box(ax, 0.3, 11, 3.2, 2.0, "1S Li-ion cell\n(protected pack)\nJ101 XT30", "pwr")
    box(ax, 4.3, 11, 3.0, 2.0, "F101 5 A fuse\nJ102 master\nswitch", "pwr")
    box(ax, 0.3, 6.6, 3.2, 2.0, "USB-C J103\n(power only)", "ext")
    box(ax, 4.3, 6.6, 3.0, 2.0, "BQ25188\ncharger U101\n(charge only)", "pwr")
    box(ax, 9.0, 11, 3.5, 2.0, "TPS62840 buck U201\nVBAT to 3.3 V", "pwr")
    box(ax, 9.0, 5.6, 3.5, 3.4, "LM51551 flyback\nU301 + T301\n(HPH6-0090L)\nVBAT to 48 V\nEN = FLY_EN", "hv")
    box(ax, 14.5, 11, 3.5, 2.0, "Main MCU\nSTM32WBA55CG\nU501", "mcu", bold=True)
    box(ax, 14.5, 13.7, 3.5, 1.1, "U.FL J501: BLE", "ext", fs=8)
    box(ax, 14.5, 6.6, 3.5, 2.4, "Supervisor MCU\nSTM32C031C6\nU601", "mcu", bold=True)
    box(ax, 9.0, 1.4, 3.5, 3.0, "Kill path\nR401 4.7 k to GND\nR402 1 k, Q401 veto\nQ402 park, Q304 OVP", "safe")
    box(ax, 14.5, 1.4, 3.5, 3.0, "MAX3485 RS-485\nset-up link (J704);\nTVS + series R on\nPMD401 lines", "safe", fs=8)
    box(ax, 20.0, 5.8, 3.4, 3.6, "PiezoMotor\nPMD401 driver\n4 x 0-48 V\nphases", "ext")
    box(ax, 20.0, 2.6, 3.4, 2.0, "Piezo LEGS LL06\n80 nm encoder", "ext")
    box(ax, 20.0, 0.2, 3.4, 1.6, "Hamilton 1001 TLL\n1 mL syringe", "ext", fs=8)
    # power
    wire(ax, [(3.5, 12), (4.3, 12)])
    wire(ax, [(7.3, 12), (9.0, 12)], label="VBAT", lpos=(7.45, 12.45))
    wire(ax, [(8.1, 12), (8.1, 7.3), (9.0, 7.3)])
    wire(ax, [(3.5, 7.6), (4.3, 7.6)], label="VBUS", lpos=(3.45, 8.2))
    wire(ax, [(5.8, 8.6), (5.8, 11.0)], label="VBAT_FUSED", lpos=(5.95, 9.8))
    wire(ax, [(12.5, 12), (14.5, 12)], label="+3V3", lpos=(12.75, 12.45))
    wire(ax, [(12.5, 6.1), (20.0, 6.1)], color=C2, label="+48V_MOT", lpos=(12.8, 6.55))
    # signals
    wire(ax, [(18.0, 11.5), (21.7, 11.5), (21.7, 9.4)], color=C1, label="SPI step rate", lpos=(18.3, 11.9))
    wire(ax, [(21.7, 5.8), (21.7, 4.6)], label="phases", lpos=(21.85, 5.2))
    wire(ax, [(21.7, 2.6), (21.7, 1.8)], label="rod", lpos=(21.85, 2.2))
    wire(ax, [(23.4, 3.9), (24.1, 3.9), (24.1, 12.5), (18.0, 12.5)], color=C1, label="encoder A/B/I", lpos=(19.0, 12.9))
    wire(ax, [(20.0, 3.3), (19.2, 3.3), (19.2, 7.4), (18.0, 7.4)], color=C3, label="enc A/B", lpos=(18.2, 7.85))
    wire(ax, [(16.25, 9.0), (16.25, 11.0)], both=True, label="heartbeat", lpos=(16.4, 10.0))
    wire(ax, [(16.25, 13.0), (16.25, 13.7)], both=True)
    wire(ax, [(14.5, 11.4), (13.6, 11.4), (13.6, 3.8), (12.5, 3.8)], color=C1, label="MCU_48V_EN", lpos=(12.6, 10.3), ha="left")
    wire(ax, [(14.5, 7.0), (14.0, 7.0), (14.0, 2.6), (12.5, 2.6)], color=C3, label="VETO / PARK", lpos=(12.55, 2.1))
    wire(ax, [(10.75, 4.4), (10.75, 5.6)], color=C2, label="FLY_EN", lpos=(10.9, 5.0))
    wire(ax, [(10.75, 1.4), (10.75, 0.7), (19.5, 0.7), (19.5, 5.0), (20.6, 5.0), (20.6, 5.8)], color=C3,
         label="AEN (park)", lpos=(15.5, 0.7), ha="center")
    ax.text(0.3, 14.4, "Blue: main-MCU signals    Green: supervisor signals    Orange: 48 V rail and enable",
            color=INK2, fontsize=8)
    save(fig, "fig_block_diagram.png")


def power_tree():
    fig, ax = canvas(20, 8, 10.5, 4.3)
    box(ax, 0.2, 3.2, 2.6, 1.6, "Cell 3.0-4.2 V\n(1S protected)", "pwr")
    box(ax, 3.4, 3.2, 2.4, 1.6, "F101 5 A\nJ102 switch", "pwr")
    box(ax, 6.6, 5.6, 3.4, 1.8, "TPS62840 buck\nVSET 267 k -> 3.3 V\n2.2 uH, 10 uF", "pwr")
    box(ax, 6.6, 0.6, 3.4, 2.4, "LM51551 flyback\n298 kHz, n = 5\nLp 7.29 uH, Rs 22 mohm\nsoft start 1 uF", "hv")
    box(ax, 6.6, 3.3, 3.4, 1.6, "BQ25188 charger\n(on VBAT_FUSED,\nSYS unloaded)", "pwr")
    box(ax, 11.0, 5.6, 4.0, 1.8, "+3V3 loads: WBA55, C031,\nMAX3485, encoder (JP701),\npull-ups, LEDs", "mcu")
    box(ax, 11.0, 0.6, 4.0, 2.4, "+48V_RAW (45.6-50.4 V)\nC309/C310 2.2 uF/100 V\nC311 47 uF/100 V\nR312 10 k bleeder\nD303/Q304 OVP trip", "hv")
    box(ax, 16.0, 0.6, 3.6, 2.4, "R311 0 R -> +48V_MOT\nC702 100 uF/100 V\nJ703 -> PMD401\n(<= 100 mA, 4.8 W)", "hv")
    box(ax, 16.0, 5.6, 3.6, 1.8, "VBAT_SENSE divider on VBAT\n200 k / 200 k\n-> U501 ADC4 (S-13)", "safe")
    arrow(ax, (2.8, 4.0), (3.4, 4.0))
    arrow(ax, (5.8, 4.4), (6.6, 6.4), "VBAT")
    arrow(ax, (5.8, 4.0), (6.6, 4.0))
    ax.text(6.2, 3.0, "VBAT_FUSED", fontsize=7.5, color=INK2, ha="center")
    arrow(ax, (5.8, 3.6), (6.6, 1.8), "VBAT", off=(-0.5, 0))
    arrow(ax, (10.0, 6.5), (11.0, 6.5))
    arrow(ax, (10.0, 1.8), (11.0, 1.8))
    arrow(ax, (15.0, 1.8), (16.0, 1.8))
    ax.text(0.2, 7.5, "Rev B power tree as implemented (scripts/design.py, tag pcb-p6-final)", fontsize=8.5, color=INK2)
    save(fig, "fig_power_tree.png")


def kill_path():
    fig, ax = canvas(20, 9, 10, 4.6)
    box(ax, 0.3, 6.3, 3.4, 1.6, "Main MCU PB7\nMCU_48V_EN", "mcu")
    box(ax, 0.3, 3.4, 3.4, 1.6, "Supervisor PB0\nSUP_VETO\n(R403 10 k pull-up)", "mcu")
    box(ax, 0.3, 0.5, 3.4, 1.6, "Supervisor PB1\nSUP_PARK\n(R405 10 k pull-up)", "mcu")
    box(ax, 5.0, 6.3, 2.4, 1.6, "R402\n1 k", "safe")
    box(ax, 5.0, 3.4, 2.4, 1.6, "Q401 BSS138\n(drain on FLY_EN)", "safe")
    box(ax, 9.0, 4.6, 3.0, 2.4, "FLY_EN node\nR401 4.7 k to GND\n(default OFF)", "safe", bold=True)
    box(ax, 9.0, 1.6, 3.0, 2.0, "Q304 BSS138 OVP\nD303 51 V zener\ntrip 50.5-53.9 V", "hv")
    box(ax, 13.6, 4.6, 3.0, 2.4, "LM51551\nUVLO/EN\n<0.33 V = off", "hv")
    box(ax, 13.6, 7.2, 3.0, 1.4, "48 V rail\n(on only while dosing)", "hv")
    box(ax, 5.0, 0.5, 2.4, 1.6, "Q402 BSS138\nopen drain", "safe")
    box(ax, 13.6, 0.5, 3.0, 1.8, "PMD401 AEN\n(22 k internal pull-up)\nLOW = parked", "ext")
    arrow(ax, (3.7, 7.1), (5.0, 7.1))
    arrow(ax, (7.4, 7.1), (9.0, 6.4))
    ax.text(8.2, 7.6, "high: 2.47-2.78 V = run", fontsize=7.5, color=INK2, ha="center")
    arrow(ax, (3.7, 4.2), (5.0, 4.2))
    arrow(ax, (7.4, 4.2), (9.0, 5.2))
    ax.text(8.3, 3.7, "veto on: ~0 V = off", fontsize=7.5, color=INK2, ha="center")
    arrow(ax, (10.5, 3.6), (10.5, 4.6), "pull low", off=(0.6, -0.3))
    arrow(ax, (12.0, 5.8), (13.6, 5.8))
    arrow(ax, (15.1, 7.0), (15.1, 7.2))
    arrow(ax, (3.7, 1.3), (5.0, 1.3))
    arrow(ax, (7.4, 1.3), (13.6, 1.3), "AEN held low unless supervisor drives PB1 low", off=(0, 0.05))
    ax.text(0.3, 8.5, "Any MCU in reset, crashed or unpowered leaves the 48 V rail OFF and the motor PARKED.",
            fontsize=8.5, color=INK2)
    save(fig, "fig_kill_path.png")


def toolchain():
    fig, ax = canvas(20, 5, 10.5, 2.8)
    items = [("scripts/design.py\nsingle source of truth\n(parts, nets, status)", "mcu"),
             ("gen_library.py\ngen_schematic.py\n(8 sheets)", "pwr"),
             ("gen_pcb.py place\nFreerouting / staged\nhand-route scripts", "pwr"),
             ("kicad-cli 10.0.3\nERC, DRC, parity,\nBOM export", "safe"),
             ("review scripts\nnetlist, connectivity,\ncalcs, ngspice/LTspice", "safe")]
    for i, (t, k) in enumerate(items):
        box(ax, 0.2 + i * 4.0, 1.2, 3.4, 2.6, t, k, fs=8)
        if i:
            arrow(ax, (0.2 + i * 4.0 - 0.6, 2.5), (0.2 + i * 4.0, 2.5))
    ax.text(0.2, 4.4, "Every change: checkpoint commit or tag first (CLAUDE.md rule 6), then regenerate, then re-run every check",
            fontsize=8, color=INK2)
    save(fig, "fig_toolchain.png")


def dose_fsm():
    fig, ax = canvas(20, 7, 9.5, 3.4)
    st = ["IDLE", "UNPARK", "MOVE", "SETTLE"]
    for i, s in enumerate(st):
        box(ax, 0.6 + i * 4.8, 3.6, 3.2, 1.6, s, "mcu", fs=10, bold=True)
    for i in range(3):
        arrow(ax, (3.8 + i * 4.8, 4.4), (5.4 + i * 4.8, 4.4))
    wire(ax, [(16.2, 5.2), (16.2, 6.0), (2.2, 6.0), (2.2, 5.2)])
    ax.text(9.2, 6.35, "dose complete: encoder at absolute target", ha="center", fontsize=8, color=INK2)
    box(ax, 7.6, 0.4, 4.8, 1.6, "FAULT (latched)\n48 V off, motor parked", "hv", fs=9, bold=True)
    for i in range(4):
        arrow(ax, (2.2 + i * 4.8, 3.6), (10.0, 2.0), color=C2, ls="--")
    ax.text(15.6, 1.1, "reachable from every state\n(F-02); cleared only on purpose\n(S-04 proposed)",
            fontsize=8, color=INK2)
    save(fig, "fig_dose_fsm.png")


def timeline():
    rows = [("v1: C++ HybridPancreasSim + ESP32/A4988/NEMA 17 rig", "2026-08-01", "2026-09-08", C1),
            ("v2 re-scope; stepper and LT20 specifications (superseded)", "2026-09-21", "2026-09-25", C2),
            ("Piezo architecture, LL06 + PMD401 selected; firmware course", "2026-09-25", "2026-09-29", C2),
            ("Rev A parts list final; power tree and kill path", "2026-09-29", "2026-10-08", C2),
            ("Requirements report; handoff documents", "2026-10-08", "2026-10-10", C3),
            ("Rev B digital design: schematic, PCB, first routing", "2026-10-10", "2026-10-11", C3),
            ("Placement optimisation and staged routing", "2026-10-11", "2026-10-12", C3),
            ("ECO1-ECO3 schematic; PCB stages P1-P4", "2026-10-31", "2026-11-01", C3),
            ("Stage P6: fully routed, ERC/DRC 0; independent review", "2026-11-01", "2026-11-02", C3)]
    import datetime as dt
    d = lambda s: dt.date.fromisoformat(s)
    fig, ax = plt.subplots(figsize=(9.5, 3.6))
    for i, (lbl, a, b, c) in enumerate(rows[::-1]):
        ax.barh(i, (d(b) - d(a)).days or 1, left=d(a).toordinal(), color=c, height=0.55)
        ax.text(d(b).toordinal() + 1, i, lbl, va="center", fontsize=7.8, color=INK)
    ticks = [d(x) for x in ("2026-08-01", "2026-09-01", "2026-10-01", "2026-11-01", "2026-12-01")]
    ax.set_xticks([t.toordinal() for t in ticks]); ax.set_xticklabels([t.strftime("%d %b") for t in ticks])
    ax.set_yticks([]); ax.set_xlim(d("2026-08-01").toordinal(), d("2027-01-25").toordinal())
    ax.grid(axis="y", visible=False)
    ax.text(d("2026-08-01").toordinal(), 9.0, "Blue: v1   Orange: v2 concept and Rev A   Green: Rev B digital design",
            fontsize=8, color=INK2)
    ax.set_ylim(-0.6, 9.4)
    ax.spines["left"].set_visible(False)
    save(fig, "fig_timeline.png")


# ---------------------------------------------------------------- data charts
def routing_progress():
    # Unconnected pairs reported by kicad-cli at each checkpoint (HANDOVER_GUIDE, FINAL_HANDOVER,
    # CURRENT_STATUS sec.2, PLACEMENT_PROPOSAL sec.8, PCB_STAGES P1/P2/P4/P6).
    pts = [("Pass 2\n10 Oct", 64), ("Pass 3", 63), ("v2 pass 1", 42), ("v2 pass 2", 37), ("hand\nroute", 35),
           ("placement\n11 Oct", 80), ("Stage 1", 67), ("Stage 2", 61), ("D1", 59), ("Stage 3", 54),
           ("Stage 4", 48), ("P1\n31 Oct", 81), ("P2", 50), ("P4", 37), ("P6\n1 Nov", 0)]
    fig, ax = plt.subplots(figsize=(9.5, 3.4))
    x = range(len(pts))
    ax.plot(list(x), [p[1] for p in pts], color=C1, lw=2, marker="o", ms=5)
    for i, (l, v) in enumerate(pts):
        ax.text(i, v + 3, str(v), ha="center", fontsize=8, color=INK)
    ax.set_xticks(list(x)); ax.set_xticklabels([p[0] for p in pts], fontsize=7.5)
    ax.set_ylabel("Unconnected items (kicad-cli DRC)"); ax.set_ylim(0, 95)
    ax.axvspan(4.5, 5.5, color=GRID, alpha=0.5, lw=0)
    ax.axvspan(10.5, 11.5, color=GRID, alpha=0.5, lw=0)
    ax.text(5, 90, "rip-up for\nplacement", ha="center", fontsize=7, color=INK2)
    ax.text(11, 90, "ECO1/ECO2\nparts added", ha="center", fontsize=7, color=INK2)
    save(fig, "fig_routing_progress.png")


def softstart():
    # Parsed from the re-run of validation/sim/lm51551_startup.py (docs/project_report/evidence)
    txt = open(os.path.join(EVD, "lm51551_startup.txt")).read()
    res = collections.defaultdict(lambda: [0, 0])
    tmax = collections.defaultdict(float)
    for m in re.finditer(r"^\s*([\d.]+)\s+([\d.]+)\s+(\d+) nF\s+(\d+) mV\s+(\d+) uA\s+(OK|FAIL)(.*)$", txt, re.M):
        css = int(m.group(3)); ok = m.group(6) == "OK"
        res[css][0 if ok else 1] += 1
        t = re.search(r"t=\s*([\d.]+) ms", m.group(7))
        if ok and t:
            tmax[css] = max(tmax[css], float(t.group(1)))
    cs = sorted(res)
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    xs = range(len(cs))
    ax.bar([i - 0.2 for i in xs], [res[c][0] for c in cs], 0.38, color=C3, label="clean start (no hiccup)")
    ax.bar([i + 0.2 for i in xs], [res[c][1] for c in cs], 0.38, color=C2, label="hiccup lock-out")
    for i, c in enumerate(cs):
        ax.text(i - 0.2, res[c][0] + 0.3, str(res[c][0]), ha="center", fontsize=8)
        ax.text(i + 0.2, res[c][1] + 0.3, str(res[c][1]), ha="center", fontsize=8)
    ax.set_xticks(list(xs)); ax.set_xticklabels([f"{c} nF" if c < 1000 else "1 uF" for c in cs])
    ax.set_xlabel("Soft-start capacitor C305"); ax.set_ylabel("Corners (of 12)")
    ax.legend(loc="upper center", ncol=2, fontsize=8, bbox_to_anchor=(0.5, 1.12)); ax.set_ylim(0, 13.5)
    save(fig, "fig_softstart.png")


def q301():
    # validation/sim/q301/RESULTS.md (LTspice 26.1.1), AONR34332C at the 4.9 A limit
    rows = [("4.2 V, 2 %, 3 nH", 25.8), ("4.2 V, 2 %, 5 nH", 27.2), ("4.2 V, 10 %, 3 nH", 27.1),
            ("4.2 V, 10 %, 4 nH", 28.0), ("4.2 V, 10 %, 5 nH", 28.9), ("3.4 V, 10 %, 4 nH", 27.2)]
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    y = range(len(rows))
    ax.barh(list(y), [r[1] for r in rows], color=C1, height=0.55)
    for i, r in enumerate(rows):
        ax.text(r[1] + 0.2, i, f"{r[1]:.1f} V", va="center", fontsize=8)
    ax.axvline(30, color=INK, lw=1.2, ls="-"); ax.text(30.1, 5.45, "30 V rating", fontsize=8)
    ax.axvline(24, color=INK2, lw=1, ls="--"); ax.text(24.1, 5.45, "80 % derating", fontsize=8, color=INK2)
    ax.set_yticks(list(y)); ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.set_xlim(20, 33); ax.invert_yaxis(); ax.set_xlabel("Simulated peak drain voltage (V)")
    ax.grid(axis="y", visible=False)
    save(fig, "fig_q301.png")


def leakage():
    # ECO1_SCHEMATIC.md item 3 (22 nF/390 R clamp, 25 V FET) and ECO2 item 3 (100 nF/330 R + SMAJ15A, 30 V FET)
    k = [2, 4, 6, 10]
    eco1 = [19.4, 21.7, 23.0, 24.2]
    eco2 = [22.8, 23.9, 24.1, 24.4]
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    ax.plot(k, eco1, color=C1, marker="o", lw=2, label="ECO1 clamp, 4.2 V, nominal peak current")
    ax.plot(k, eco2, color=C2, marker="s", lw=2, label="ECO2 clamp + SMAJ15A, 4.2 V, 4.9 A limit")
    ax.set_xlabel("Transformer leakage (% of Lp)"); ax.set_ylabel("Peak Vds (V), no loop L")
    ax.set_xticks(k); ax.legend(fontsize=8, loc="lower right"); ax.set_ylim(15, 27)
    save(fig, "fig_leakage.png")


def openloop():
    # validation/sim/flyback_openloop.log (LTspice 26.1.1), steps 3/4 = adopted run with snubber
    t = open(os.path.join(ROOT, "validation/sim/flyback_openloop.log")).read()
    def meas(name):
        blk = t.split("Measurement: " + name)[1].split("Measurement:")[0]
        return [float(v) for v in re.findall(r"^\s+\d\s+([-\d.e]+)", blk, re.M)]
    eff = meas("eff"); pin = meas("pin"); pout = meas("pout")
    labels = ["3.0 V\nno snubber", "4.2 V\nno snubber", "3.0 V\nsnubber", "4.2 V\nsnubber"]
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.0))
    axs[0].bar(range(4), [e * 100 for e in eff], color=[GRID, GRID, C1, C1])
    for i, e in enumerate(eff):
        axs[0].text(i, e * 100 + 1, f"{e*100:.1f} %", ha="center", fontsize=8)
    axs[0].set_xticks(range(4)); axs[0].set_xticklabels(labels, fontsize=8); axs[0].set_ylim(0, 100)
    axs[0].set_ylabel("Efficiency Pout/Pin (%)")
    axs[0].text(0.5, 92, "grey: rectifier rings to 200 V\n(rejected)", ha="center", fontsize=7, color=INK2)
    w = 0.38
    axs[1].bar([i - w / 2 for i in range(4)], pin, w, color=C2, label="Pin (W)")
    axs[1].bar([i + w / 2 for i in range(4)], pout, w, color=C3, label="Pout (W)")
    axs[1].set_xticks(range(4)); axs[1].set_xticklabels(labels, fontsize=8); axs[1].set_ylabel("Power (W)")
    axs[1].legend(fontsize=8, loc="lower right"); axs[1].set_ylim(0, 7.5)
    save(fig, "fig_openloop.png")


def rf():
    # docs/project_report/evidence/rf_line_solver.txt (re-run of validation/sim/rf_line_solver.py)
    t = open(os.path.join(EVD, "rf_line_solver.txt")).read()
    pts = [(float(a), float(b), float(c), float(d)) for a, b, c, d in
           re.findall(r"JLC7628 w ([\d.]+) g ([\d.]+) Z ([\d.]+), with mask ([\d.]+)", t)]
    g25 = sorted(p for p in pts if abs(p[1] - 0.25) < 1e-6)
    t2 = open(os.path.join(EVD, "rf_eco1_widths.txt")).read()
    for w, a, b in re.findall(r"w ([\d.]+) g 0.25: Z bare ([\d.]+) ohm, with mask ([\d.]+)", t2):
        g25.append((float(w), 0.25, float(a), float(b)))
    g25 = sorted(set(g25))
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    ax.plot([p[0] for p in g25], [p[2] for p in g25], color=C1, marker="o", lw=2, label="bare copper")
    ax.plot([p[0] for p in g25], [p[3] for p in g25], color=C2, marker="s", lw=2, label="under solder mask")
    ax.axhline(50, color=INK2, ls="--", lw=1); ax.axhline(63, color=INK2, ls=":", lw=1)
    ax.text(0.375, 50.6, "50 ohm", fontsize=8, color=INK2); ax.text(0.375, 63.6, "63 ohm", fontsize=8, color=INK2)
    for w in (0.20, 0.32):
        ax.axvline(w, color=GRID, lw=3, zorder=0)
    ax.set_xlabel("Trace width (mm), 0.25 mm gap, 0.2104 mm prepreg, er 4.4")
    ax.set_ylabel("Z0 (ohm)"); ax.legend(fontsize=8)
    save(fig, "fig_rf_line.png")


def bom_status():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "docs/bom_detailed.csv"))))
    c = collections.Counter(r["Status"] for r in rows)
    order = ["DECIDED", "DS", "CALC", "ASSUMED", "TBD", "PLACEHOLDER"]
    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    ax.barh(range(len(order)), [c[o] for o in order], color=C1, height=0.55)
    for i, o in enumerate(order):
        ax.text(c[o] + 0.6, i, str(c[o]), va="center", fontsize=8)
    ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel(f"References in docs/bom_detailed.csv (total {len(rows)})"); ax.grid(axis="y", visible=False)
    save(fig, "fig_bom_status.png")


def checks_history():
    # ERC errors and total DRC violations at the recorded checkpoints
    erc = [("10 Oct", 6), ("ECO1 31 Oct", 5), ("P1-P4", 5), ("P6 1 Nov", 0)]
    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    ax.plot(range(4), [e[1] for e in erc], color=C2, marker="o", lw=2)
    for i, e in enumerate(erc):
        ax.text(i, e[1] + 0.3, str(e[1]), ha="center", fontsize=8)
    ax.set_xticks(range(4)); ax.set_xticklabels([e[0] for e in erc], fontsize=8)
    ax.set_ylabel("ERC errors"); ax.set_ylim(0, 7.5)
    save(fig, "fig_erc_history.png")


def layout_sens():
    # docs/project_report/evidence/flyback_layout_sens.txt (ngspice 42 re-run of the review deck)
    t = open(os.path.join(EVD, "flyback_layout_sens.txt")).read()
    vals = re.findall(r"Vin=([\d.]+) .*?Lclamp=(\S+) .*?vds_max=([\d.]+)", t)
    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    lab = [f"Vin {a} V, Lclamp {b}" for a, b, _ in vals]
    ax.barh(range(len(vals)), [float(v[2]) for v in vals], color=[C1, C2, C1, C2], height=0.55)
    for i, v in enumerate(vals):
        ax.text(float(v[2]) + 0.2, i, f"{float(v[2]):.1f} V", va="center", fontsize=8)
    ax.set_yticks(range(len(vals))); ax.set_yticklabels(lab, fontsize=8); ax.invert_yaxis()
    ax.axvline(25, color=INK, lw=1); ax.text(25.1, -0.45, "25 V (CSD16340Q3)", fontsize=7.5)
    ax.set_xlim(10, 32); ax.set_xlabel("Peak Vds (V)"); ax.grid(axis="y", visible=False)
    save(fig, "fig_layout_sens.png")


if __name__ == "__main__":
    import sys
    ALL = (block_diagram, power_tree, kill_path, toolchain, dose_fsm, timeline, routing_progress,
              softstart, q301, leakage, openloop, rf, bom_status, checks_history, layout_sens)
    for f in ALL:
        if len(sys.argv) == 1 or f.__name__ in sys.argv[1:]:
            f()
