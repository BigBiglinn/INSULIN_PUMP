"""Generates the data charts and block diagrams for the project report from project data."""
import csv, os, subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SIM = r'D:\HybridPancreasSim\HybridPancreasSim\desktop\results'
FIG = os.path.join(HERE, 'figures')
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 11, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.linewidth': .7, 'axes.grid': True,
                     'grid.color': '#e6e6e6', 'grid.linewidth': .6, 'legend.frameon': False,
                     'savefig.dpi': 300, 'savefig.bbox': 'tight'})
# Okabe-Ito colours, always paired with a distinct line style so print and CVD readers can separate them
OR, BL, GN, RD, GY = '#D55E00', '#0072B2', '#009E73', '#CC3311', '#777777'


def load(n):
    R = list(csv.DictReader(open(os.path.join(SIM, n + '.csv'))))
    return {k: [float(r[k]) for r in R] for k in R[0]}


def hours(a):
    return [x / 60 for x in a]


def band(ax):
    ax.axhspan(70, 180, color='#e9f3ec', zorder=0)
    ax.axhline(70, color='#7fae8d', lw=.7, ls=':')
    ax.axhline(180, color='#7fae8d', lw=.7, ls=':')


def xh(ax):
    ax.set_xticks(range(0, 25, 4))
    ax.set_xlim(0, 24)
    ax.set_xlabel('Simulated time (h)')


def save(n):
    plt.savefig(os.path.join(FIG, n + '.png'))
    plt.close()


def charts():
    pid, ps, pr, prs = load('pid_only'), load('pid_supervised'), load('predictive_only'), load('predictive_supervised')
    fu, fs = load('fault_unsupervised'), load('fault_supervised')

    # Earliest C++ simulator
    R = list(csv.DictReader(open(r'D:\PancreasSim\simulation_output.csv')))
    fig, axs = plt.subplots(2, 1, figsize=(7, 3.8), sharex=True)
    T = [float(r['Time']) / 60 for r in R]
    axs[0].plot(T, [float(r['Glucose']) for r in R], color=BL, lw=1.5)
    axs[0].axhline(90, color=GY, lw=.8, ls=':')
    axs[0].text(.2, 96, 'target 90 mg/dL', fontsize=9, color='#444')
    axs[0].set_ylabel('Glucose (mg/dL)')
    axs[1].plot(T, [float(r['PumpDelivery']) for r in R], color=OR, lw=1.2)
    axs[1].set_ylabel('Pump (mU/min)')
    axs[1].set_xlabel('Simulated time (h)')
    axs[1].set_xticks(range(0, 25, 4))
    save('pancreas_sim')

    # Glucose, four configurations
    fig, ax = plt.subplots(figsize=(7, 3.5))
    band(ax)
    ax.plot(hours(pid['time_min']), pid['true_bg'], color=OR, lw=1.5, label='PID only')
    ax.plot(hours(ps['time_min']), ps['true_bg'], color=GY, lw=1, ls='--', label='PID + Supervisor')
    ax.plot(hours(pr['time_min']), pr['true_bg'], color=BL, lw=1.5, label='Predictive only')
    ax.plot(hours(prs['time_min']), prs['true_bg'], color=GN, lw=1, ls=':', label='Predictive + Supervisor')
    for h, g in ((7, 45), (12, 70), (19, 60)):
        ax.annotate(f'{g} g', (h, 45), ha='center', fontsize=9, color='#444')
    ax.set_ylabel('True glucose (mg/dL)')
    ax.set_ylim(40, 320)
    xh(ax)
    ax.legend(ncol=2, fontsize=9, loc='upper left')
    save('glucose_four')

    # Insulin
    fig, ax = plt.subplots(figsize=(7, 2.7))
    ax.plot(hours(pid['time_min']), pid['delivered_mU_min'], color=OR, lw=1.2, label='PID only')
    ax.plot(hours(prs['time_min']), prs['delivered_mU_min'], color=GN, lw=1.2, ls='--', label='Predictive + Supervisor')
    ax.axhline(23.755, color=GY, lw=.8, ls=':')
    ax.text(.15, 30, 'basal 23.76 mU/min', fontsize=9, color='#444')
    ax.set_ylabel('Infusion to plasma (mU/min)')
    xh(ax)
    ax.set_ylim(0, 165)
    ax.legend(fontsize=9, loc='upper left', ncol=2)
    save('insulin_delivery')

    # PID clamp effect
    fig, ax = plt.subplots(figsize=(7, 2.7))
    ax.plot(hours(pid['time_min']), pid['basal_Uhr'], color=OR, lw=1.3, label='PID only')
    ax.plot(hours(ps['time_min']), ps['basal_Uhr'], color=BL, lw=1.1, ls='--', label='PID + Supervisor')
    ax.axhline(4, color=GY, lw=.8, ls=':')
    ax.text(.15, 4.1, 'supervisor limit 4 U/h', fontsize=9, color='#444')
    ax.set_ylabel('Commanded basal (U/h)')
    xh(ax)
    ax.legend(fontsize=9, loc='upper right')
    save('pid_clamp')

    # Fault, whole day
    fig, ax = plt.subplots(figsize=(7, 3.4))
    band(ax)
    ax.plot(hours(fu['time_min']), fu['cgm_seen'], color=GY, lw=.7, label='CGM seen (unsupervised run)')
    ax.plot(hours(fu['time_min']), fu['true_bg'], color=RD, lw=1.5, label='True glucose, unsupervised')
    ax.plot(hours(fs['time_min']), fs['true_bg'], color=GN, lw=1.5, ls='--', label='True glucose, supervised')
    ax.annotate('minimum 51.1 mg/dL\nat t = 273 min', (4.55, 51.1), (6.2, 48), fontsize=9, va='bottom',
                arrowprops=dict(arrowstyle='-', lw=.6))
    ax.set_ylabel('Glucose (mg/dL)')
    ax.set_ylim(40, 400)
    xh(ax)
    ax.legend(fontsize=9, loc='upper right')
    save('fault_day')

    # Fault window
    fig, axs = plt.subplots(2, 1, figsize=(7, 4.2), sharex=True)
    lim = lambda d, k: [(t, v) for t, v in zip(d['time_min'], d[k]) if 165 <= t <= 300]
    for d, c, ls, lb in ((fu, RD, '-', 'Unsupervised'), (fs, GN, '--', 'Supervised')):
        x = lim(d, 'delivered_mU_min')
        axs[0].plot([a for a, _ in x], [b for _, b in x], color=c, ls=ls, lw=1.5, label=lb)
        x = lim(d, 'true_bg')
        axs[1].plot([a for a, _ in x], [b for _, b in x], color=c, ls=ls, lw=1.5, label=lb)
    for a in axs:
        a.axvspan(180, 189, color='#dddddd', zorder=0)
    axs[0].set_ylabel('Infusion (mU/min)')
    axs[0].legend(fontsize=9)
    axs[0].text(190.5, 215, 'faulted samples at t = 180, 183, 186 min', fontsize=9, color='#444')
    axs[1].axhline(70, color='#7fae8d', lw=.7, ls=':')
    axs[1].text(167, 72, '70 mg/dL', fontsize=9, color='#444')
    axs[1].set_ylabel('True glucose (mg/dL)')
    axs[1].set_xlabel('Simulated time (min)')
    save('fault_zoom')

    # Routing convergence
    st = [('Stage 3a-c\nautoroute', 63), ('v2 pass 1', 42), ('v2 pass 2', 37), ('Classified', 35), ('Placement\nrip-up', 80),
          ('Stage 1', 67), ('Stage 2', 61), ('D1', 59), ('Stage 3', 54), ('Stage 4', 48), ('Stage 5a', 48),
          ('ECO/P1', 81), ('P2', 50), ('P4', 37), ('Pre-P6', 34), ('P6', 0)]
    fig, ax = plt.subplots(figsize=(7, 3.1))
    xs = range(len(st))
    ax.plot(xs, [v for _, v in st], color=BL, lw=1.6, marker='o', ms=4)
    for i, (_, v) in enumerate(st):
        ax.annotate(str(v), (i, v), (0, 6), textcoords='offset points', ha='center', fontsize=9)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([s for s, _ in st], rotation=60, ha='right', fontsize=8.5)
    ax.set_ylabel('Unconnected pairs (DRC)')
    ax.set_ylim(-3, 95)
    save('routing_convergence')

    # Q301 corners
    lab = ['2 %, 3 nH', '2 %, 5 nH', '10 %, 3 nH', '10 %, 4 nH', '10 %, 5 nH']
    val = [25.8, 27.2, 27.1, 28.0, 28.9]
    fig, ax = plt.subplots(figsize=(7, 2.5))
    ax.barh(lab[::-1], val[::-1], color=BL, height=.55)
    for i, v in enumerate(val[::-1]):
        ax.text(v - .25, i, f'{v:.1f} V', va='center', ha='right', color='white', fontsize=10)
    ax.axvline(30, color=RD, lw=1.2)
    ax.text(29.9, 4.45, '30 V rating', ha='right', fontsize=9.5, color=RD)
    ax.axvline(24, color=GY, lw=1, ls='--')
    ax.text(23.9, 4.45, '80 % derating, 24 V', ha='right', fontsize=9.5, color='#444')
    ax.set_xlim(0, 32)
    ax.set_ylim(-.5, 4.9)
    ax.set_xlabel('Simulated peak drain-source voltage at VBAT 4.2 V, 4.9 A limit (V)')
    ax.grid(axis='y', visible=False)
    save('q301_peaks')

    # Leakage
    k = [2, 4, 6, 10]
    fig, ax = plt.subplots(figsize=(7, 2.7))
    ax.plot(k, [18.2, 20.0, 20.2, 20.7], color=BL, marker='o', ms=4, label='VBAT 3.0 V')
    ax.plot(k, [19.4, 21.7, 23.0, 24.2], color=OR, marker='s', ms=4, ls='--', label='VBAT 4.2 V')
    ax.axhline(20, color=GY, lw=.9, ls=':')
    ax.text(2.0, 20.15, '80 % of the then-fitted 25 V FET', fontsize=9, color='#444')
    ax.set_xlabel('Assumed transformer leakage (%)')
    ax.set_ylabel('Peak Vds (V)')
    ax.legend(fontsize=9, loc='lower right')
    save('leakage_sweep')


def box(ax, x, y, w, h, t, fc='#f3f6fa', ec='#33475b', fs=9.5, lw=.9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.08', fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=fs, linespacing=1.15)


def arr(ax, a, b, t=None, ls='-', c='#222', off=(0, .1), fs=8.5, cs=None):
    ax.annotate('', b, a, arrowprops=dict(arrowstyle='-|>', lw=1, ls=ls, color=c, shrinkA=0, shrinkB=0,
                                          connectionstyle=cs or 'arc3'))
    if t:
        ax.text((a[0] + b[0]) / 2 + off[0], (a[1] + b[1]) / 2 + off[1], t, ha='center', fontsize=fs, color=c)


def canvas(w, h, sx=9.5):
    fig, ax = plt.subplots(figsize=(sx, sx * h / w))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis('off')
    ax.grid(False)
    return ax


HV, SAFE, MCU, PWR = '#fbe9e3', '#fff4d6', '#e3eefb', '#e7f4ea'


def diagrams():
    # Project evolution
    ax = canvas(14, 5)
    items = [('v1 simulator\nAug 2026', 'C++ Bergman plant,\nPID, predictive,\nsupervisor, fault test'),
             ('v1 rig\nto 8 Sep', 'ESP32, A4988,\nNEMA 17, T8 screw.\nSuperseded'),
             ('v2 re-scope\n21-29 Sep', 'Stepper, valve pump\nrejected; LL06 and\nPMD401 frozen'),
             ('Rev A plan\n30 Sep-10 Oct', 'Power tree, kill path,\n37-line list, motor\nquote, requirements'),
             ('Rev B digital\n10-11 Oct', 'KiCad generated,\nflyback simulated,\nstaged routing'),
             ('ECOs, P6\n31 Oct-1 Nov', 'ST data applied;\n0 ERC, 0 DRC,\n0 unconnected')]
    w = 2.1
    for i, (a, b) in enumerate(items):
        x = .1 + i * 2.32
        box(ax, x, 3.1, w, 1.6, a, fc=MCU, fs=10)
        box(ax, x, .4, w, 2.3, b, fc='#ffffff', fs=9)
        if i < 5:
            arr(ax, (x + w + .03, 3.9), (x + 2.3, 3.9))
    save('evolution')

    # Closed-loop simulation
    ax = canvas(14, 5.8)
    box(ax, 5.2, 4.4, 3.4, 1.1, 'Meal schedule\n45 g, 70 g, 60 g', fc=PWR)
    box(ax, 9.9, 2.4, 3.8, 1.5, 'Bergman plant + EGP\nG, X, I (Euler, 3 min)', fc=HV)
    box(ax, 5.6, 2.4, 2.8, 1.5, 'SC depot\nÏ„ = 40 min', fc='#ffffff')
    box(ax, 1.6, 2.4, 2.8, 1.5, 'Safety\nSupervisor', fc=SAFE)
    box(ax, .2, .3, 3.2, 1.3, 'Controller\nPID or Predictive', fc=MCU)
    box(ax, 5.2, .3, 3.4, 1.3, 'CGM model\nnoise SD 1.5 mg/dL', fc='#ffffff')
    box(ax, 9.9, .3, 3.8, 1.3, 'Fault injector\n380 mg/dL for 3 samples', fc=SAFE)
    arr(ax, (4.45, 3.15), (5.55, 3.15), 'bolus', off=(0, .12))
    arr(ax, (8.45, 3.15), (9.85, 3.15), 'u (mU/min)', off=(0, .12))
    arr(ax, (8.6, 4.9), (11.8, 3.95), 'D (mg/dL/min)', off=(.75, .2))
    arr(ax, (11.8, 2.35), (11.8, 1.65), 'true G', off=(.55, -.05))
    arr(ax, (9.85, .95), (8.65, .95), 'override', off=(0, .1))
    arr(ax, (5.15, .95), (3.45, .95), 'CGM', off=(0, .1))
    arr(ax, (2.2, 1.65), (2.6, 2.35))
    ax.text(2.75, 1.8, 'proposed action', fontsize=8.5)
    arr(ax, (5.2, 5.0), (.8, 1.65), None, ls='--', cs='angle3,angleA=180,angleB=90')
    ax.text(2.6, 5.15, 'announced meal', fontsize=8.5)
    save('sim_block')

    # Bergman
    ax = canvas(14, 4.1)
    box(ax, .3, 1.5, 2.8, 1.3, 'Pump\nu (mU/min)', fc='#ffffff')
    box(ax, 4.1, 1.5, 2.6, 1.3, 'Plasma insulin\nI (mU/L)', fc=MCU)
    box(ax, 7.7, 1.5, 2.6, 1.3, 'Remote action\nX (1/min)', fc=MCU)
    box(ax, 11.1, 1.5, 2.6, 1.3, 'Glucose\nG (mg/dL)', fc=HV)
    box(ax, 10.0, 3.1, 1.9, .85, 'EGP', fc=PWR)
    box(ax, 12.0, 3.1, 1.9, .85, 'Meal D', fc=PWR)
    arr(ax, (3.15, 2.15), (4.05, 2.15), 'u/V', off=(0, .12))
    arr(ax, (6.75, 2.15), (7.65, 2.15), 'p3', off=(0, .12))
    arr(ax, (10.35, 2.15), (11.05, 2.15), 'âˆ’XG', off=(0, .12))
    arr(ax, (11, 3.05), (11.8, 2.85))
    arr(ax, (12.9, 3.05), (12.5, 2.85))
    arr(ax, (5.4, 1.45), (5.4, .7), 'clearance n', off=(1, -.1))
    arr(ax, (9, 1.45), (9, .7), 'decay p2', off=(.85, -.1))
    save('bergman')

    # Supervisor flow
    ax = canvas(14, 7.7)
    b = lambda y, t, fc='#ffffff': box(ax, 2.2, y, 5.4, .85, t, fc=fc)
    ys = [6.7, 5.55, 4.4, 3.25, 2.1, .95]
    txt = ['Read CGM; always call primary controller', 'NaN, or outside 39 to 400 mg/dL?', '|CGM âˆ’ last CGM| > 40 mg/dL?',
           'Change â‰¤ 0.05 for â‰¥ 2 repeats (stuck)?', 'Clamp basal to 0-4 U/h, bolus to 0-10 U', 'Bolus < 5 min after last? Reject it']
    for y, t in zip(ys, txt):
        b(y, t, fc=SAFE if '?' in t else '#ffffff')
    for i in range(5):
        arr(ax, (4.9, ys[i] - .03), (4.9, ys[i + 1] + .9), 'no' if 0 < i < 4 else None, off=(.3, -.08))
    box(ax, 9.5, 3.8, 4.1, 1.3, 'Log alarm, return\nbasal 0, bolus 0\n(fail safe)', fc=HV)
    for y in ys[1:4]:
        arr(ax, (7.65, y + .42), (9.45, 4.45), 'yes' if y == ys[2] else None, off=(0, .1))
    box(ax, 2.2, .02, 5.4, .62, 'Return action to the plant', fc=PWR)
    arr(ax, (4.9, .92), (4.9, .68))
    save('supervisor_flow')

    # Predictive flow
    ax = canvas(14, 5.2)
    box(ax, .2, 3.6, 3.1, 1.3, 'Store CGM\n(last 6 samples)\ndecay IOB', fc=MCU)
    box(ax, 4.1, 3.6, 3.1, 1.3, 'Linear fit, forecast\n30 min ahead', fc=MCU)
    box(ax, 8.0, 3.6, 5.7, 1.3, 'Basal shaping: 0 if pred or now < 70; Ã—0.5 if < 100;\nÃ—1.3 if > 180; Ã—1.1 if > target', fc=PWR, fs=9.5)
    box(ax, 4.1, .4, 4.2, 1.6, 'Meal announced?\ncarbs/CR + (BGâˆ’target)/CF\ncapped at max IOB', fc=SAFE)
    box(ax, 9.3, .4, 4.4, 1.6, 'Otherwise correction if pred > 180,\nIOB < 8 U, lockout â‰¥ 60 min:\n(predâˆ’target)/CF', fc=SAFE, fs=9.5)
    box(ax, .2, .4, 3.1, 1.6, 'Add bolus to IOB;\nreturn basal + bolus', fc='#ffffff')
    arr(ax, (3.35, 4.25), (4.05, 4.25))
    arr(ax, (7.25, 4.25), (7.95, 4.25))
    arr(ax, (10.8, 3.55), (10.8, 2.05))
    arr(ax, (9.25, 1.2), (8.35, 1.2), 'no meal', off=(0, .12))
    arr(ax, (4.05, 1.2), (3.35, 1.2))
    save('predictive_flow')

    # ESP32 wiring
    ax = canvas(14, 5)
    box(ax, 4.8, 1.0, 4.2, 3.2, 'ESP32 DevKit C v4\nsketch.ino\nBergmanModel.h\nControllers.h', fc=MCU)
    box(ax, 10.2, 3.4, 1.7, 1.1, 'A4988', fc='#ffffff')
    box(ax, 12.3, 3.4, 1.5, 1.1, 'Stepper', fc='#ffffff')
    box(ax, 10.2, .9, 3.6, 1.1, 'SSD1306 OLED\n128Ã—64, 0x3C', fc='#ffffff')
    box(ax, .4, 3.3, 2.8, 1, 'Green LED\ndelivering', fc=PWR)
    box(ax, .4, 1.9, 2.8, 1, 'Red LED\nsupervisor fired', fc=HV)
    box(ax, .4, .4, 2.8, 1, 'Serial, 115200\ncommands', fc='#ffffff')
    arr(ax, (9.05, 3.95), (10.15, 3.95), 'D26 STEP, D27 DIR', off=(.0, .12), fs=7.5)
    arr(ax, (11.95, 3.95), (12.25, 3.95))
    arr(ax, (9.05, 1.45), (10.15, 1.45), 'D21, D22', off=(0, .12))
    arr(ax, (4.75, 3.8), (3.25, 3.8), 'D25', off=(0, .1))
    arr(ax, (4.75, 2.4), (3.25, 2.4), 'D33', off=(0, .1))
    arr(ax, (3.25, .9), (4.75, 1.3), 'UART', off=(0, .15))
    save('esp32_wiring')

    # Rev B system
    ax = canvas(14, 8.2)
    box(ax, .2, 6.6, 2.5, 1.2, '1S Li-ion\nJ101, F101 5 A\nJ102 switch', fc=PWR)
    box(ax, .2, 4.8, 2.5, 1.2, 'BQ25188 charger\nUSB-C J103', fc=PWR)
    box(ax, 3.6, 4.8, 2.6, 1.2, 'TPS62840 buck\n+3V3', fc=PWR)
    box(ax, 3.6, 6.6, 3.6, 1.2, 'LM51551 flyback, Q301\nT301 HPH6-0090L, D301', fc=HV)
    box(ax, 8.2, 6.6, 2.5, 1.2, '+48 V rail\nbleeder, OVP trip', fc=HV)
    box(ax, 11.4, 6.6, 2.4, 1.2, 'PMD401 driver\n(off-board)', fc=HV)
    box(ax, 11.4, 4.3, 2.4, 1.2, 'LL06 motor\nand 80 nm encoder', fc='#ffffff')
    box(ax, 11.4, 2.4, 2.4, 1.2, 'Hamilton 81320\n1 mL syringe', fc='#ffffff')
    box(ax, 3.6, 2.2, 3.6, 1.6, 'STM32WBA55CG main MCU\nBLE, dose control,\nTIM2 encoder count', fc=MCU)
    box(ax, 3.6, .1, 3.6, 1.4, 'STM32C031C6 supervisor\nheartbeat, TIM3 count', fc=MCU)
    box(ax, 8.2, 3.1, 2.5, 1.4, 'Interface\nTVS + series R\nMAX3485, shifters', fc='#ffffff')
    box(ax, 8.2, .4, 2.5, 1.5, 'Kill path, FLY_EN\nQ401 veto\nQ402 park', fc=SAFE)
    box(ax, .2, 2.4, 2.4, 1.2, 'U.FL J501\nMLPF-WB-04D3', fc='#ffffff')
    arr(ax, (2.75, 7.2), (3.55, 7.2))
    arr(ax, (7.25, 7.2), (8.15, 7.2))
    arr(ax, (10.75, 7.2), (11.35, 7.2), '48 V', off=(0, .12))
    arr(ax, (12.6, 6.55), (12.6, 5.55), '4 phases', off=(.68, 0))
    arr(ax, (12.6, 4.25), (12.6, 3.65), 'pushes', off=(.55, 0))
    arr(ax, (1.45, 6.55), (1.45, 6.05))
    arr(ax, (3.0, 6.55), (4.6, 6.05), cs='arc3')
    arr(ax, (4.9, 4.75), (4.9, 3.85), '3.3 V', off=(.45, 0))
    arr(ax, (3.55, 3), (2.65, 3), 'RF', off=(0, .12))
    arr(ax, (7.25, 3.6), (8.15, 3.8), 'SPI, UART', off=(0, .15))
    arr(ax, (10.75, 4.0), (11.35, 6.55), None)
    arr(ax, (11.35, 4.7), (10.75, 4.2), 'A/B', off=(.15, .22))
    arr(ax, (5.0, 2.15), (5.0, 1.55), None)
    arr(ax, (5.8, 1.55), (5.8, 2.15), None)
    ax.text(6.55, 1.78, 'heartbeat', fontsize=8.5, ha='center')
    arr(ax, (7.25, 1.0), (8.15, 1.1), 'veto, park', off=(0, .15))
    arr(ax, (7.25, 2.4), (8.15, 1.7), 'enable', off=(.0, .2))
    arr(ax, (9.45, 1.95), (6.3, 6.55), 'FLY_EN', ls='--', c=RD, off=(-1.15, 1.1))
    save('revb_block')

    # Kill path
    ax = canvas(14, 5.4)
    box(ax, .2, 3.6, 3.4, 1.2, 'Main MCU PB7\nMCU_48V_EN', fc=MCU)
    box(ax, 4.4, 3.6, 1.8, 1.2, 'R402\n1 kÎ©', fc='#ffffff')
    box(ax, 7.2, 2.7, 3, 1.2, 'FLY_EN node\nU301 UVLO/EN', fc=SAFE)
    box(ax, 11.2, 2.7, 2.6, 1.2, 'LM51551\n48 V rail', fc=HV)
    box(ax, 7.2, 4.4, 3, .9, 'R401 4.7 kÎ© to GND', fc='#ffffff')
    box(ax, .2, 1.3, 3.4, 1.2, 'Supervisor PB0\nSUP_VETO', fc=MCU)
    box(ax, 4.4, 1.3, 1.8, 1.2, 'R403 10 kÎ©\npull-up', fc=SAFE)
    box(ax, 7.2, .7, 3, 1.2, 'Q401 BSS138\nD to FLY_EN, S to GND', fc='#ffffff', fs=9)
    box(ax, 11.2, .7, 2.6, 1.2, 'D303, Q304\nOVP trip', fc=HV)
    arr(ax, (3.65, 4.2), (4.35, 4.2))
    arr(ax, (6.25, 4.1), (7.15, 3.55))
    arr(ax, (8.7, 4.35), (8.7, 3.95))
    arr(ax, (10.25, 3.3), (11.15, 3.3), 'run â‰ˆ 2.72 V', off=(0, .13), fs=8)
    arr(ax, (3.65, 1.9), (4.35, 1.9))
    arr(ax, (6.25, 1.6), (7.15, 1.4), 'gate', off=(0, .12))
    arr(ax, (8.7, 1.95), (8.7, 2.65), 'shorts', off=(.5, -.05))
    arr(ax, (11.2, 1.9), (10.1, 2.65), 'pulls low', off=(.5, -.25), fs=8)
    save('kill_path')

    # Method flow
    ax = canvas(14, 3.3)
    st = ['Control\nsimulation', 'Architecture\nand parts', 'Requirements\nregister', 'Schematic\nECOs', 'Placement\nand routing', 'ERC, DRC,\nparity', 'SPICE and\ncalculations', 'Bench plan\n(not run)']
    for i, t in enumerate(st):
        x = .05 + i * 1.75
        box(ax, x, 1.2, 1.5, 1.3, t, fs=8.8, fc=MCU if i < 3 else (SAFE if i < 7 else '#ffffff'))
        if i < 7:
            arr(ax, (x + 1.54, 1.85), (x + 1.72, 1.85))
    arr(ax, (10.6, 1.15), (6.2, 1.15), 'findings drive the next ECO or route', ls='--', off=(0, -.45), cs='arc3,rad=-.2', fs=9.5)
    save('method')


def rasters():
    pp = 'pdftoppm'
    A = os.path.join(REPO, 'docs', 'report_assets')
    if os.path.exists(os.path.join(FIG, 'sch-1.png')):
        return
    subprocess.check_call([pp, '-r', '170', '-png', os.path.join(A, 'schematic.pdf'), os.path.join(FIG, 'sch')])
    for l in ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'):
        subprocess.check_call([pp, '-r', '170', '-png', '-singlefile', os.path.join(A, f'layer_{l}.pdf'), os.path.join(FIG, 'layer_' + l.replace('.', '_'))])


if __name__ == '__main__':
    charts()
    diagrams()
    rasters()

