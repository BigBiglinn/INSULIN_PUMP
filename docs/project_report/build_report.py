"""Builds Project_Report.docx. Run with python-docx on sys.path; finalize.ps1 updates fields and exports the PDF."""
import csv, os, subprocess, sys
sys.path.insert(0, os.environ.get('DOCX_LIB', ''))
from build_lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
FIG = os.path.join(HERE, 'figures')
SIM = r'D:\HybridPancreasSim\HybridPancreasSim'
PSIM = r'D:\PancreasSim'
PY = r'C:\Users\cherr\Desktop\Intern\insulin_pump_sim'
HO = os.path.join(REPO, 'docs', 'handover')
ALARMS = os.environ.get('ALARM_LOG', '')
f = lambda n: os.path.join(FIG, n + '.png')
rd = lambda *p: open(os.path.join(*p), encoding='utf-8', errors='replace').read()


def front(r):
    d = r.d
    for t, st in (('PROJECT REPORT', 'FrontTitle'),):
        d.add_paragraph(t, style=st)
    p = d.add_paragraph('Closed-Loop Insulin Delivery: From Control Simulation on the Bergman Minimal Model to a Digitally Complete Piezoelectric Bench-Pump PCB', style='FrontTitle')
    r.P('Submitted in partial fulfilment of the requirements of the [[degree / course name]]', 'Centered')
    d.add_paragraph('', style='Centered')
    r.P('by', 'Centered')
    r.P('**B Charan** [[confirm full name as on institute records]]', 'Centered')
    r.P('Roll No. [[roll number]]', 'Centered')
    d.add_paragraph('', style='Centered')
    r.P('Under the guidance of', 'Centered')
    r.P('[[supervisor name and designation]]', 'Centered')
    d.add_paragraph('', style='Centered')
    r.P('Department of [[department]]', 'Centered')
    r.P('Indian Institute of Technology Guwahati', 'Centered')
    r.P('November 2026', 'Centered')
    d.add_paragraph('', style='Centered')
    r.P('**Bench-only engineering prototype. Water or 0.9 % saline only. Never to be connected to a person or an animal, and never to be used with insulin.**', 'Centered')

    r.front('Certificate')
    r.P('This is to certify that the work contained in this report, entitled "Closed-Loop Insulin Delivery: From Control Simulation on the Bergman Minimal Model to a Digitally Complete Piezoelectric Bench-Pump PCB", was carried out by B Charan (Roll No. [[roll number]]) under my supervision.')
    r.P('[[Use the department template if one is prescribed. To be signed by the supervisor only after reading the report.]]')
    for _ in range(3):
        d.add_paragraph()
    r.P('Signature: ______________________          Date: ______________')
    r.P('[[Supervisor name, designation, department]]')

    r.front('Declaration')
    r.P('I declare that this report is a record of my own project work, that sources are cited where they are used, and that results are reported as they were obtained, including failed attempts.')
    r.P('**Use of AI tools.** Large parts of the project\'s code, calculations, KiCad generation scripts and documents were produced with an AI assistant (Claude, Anthropic) under my direction, and this report was drafted with the same assistant from the project files. The project records mark text written by the assistant and not signed off as PROPOSED. Numerical results in this report were re-extracted from the original data files or tool reports; they were not written from memory.')
    r.P('[[Confirm this declaration matches the institute\'s policy on AI assistance before signing.]]')
    for _ in range(2):
        d.add_paragraph()
    r.P('Signature: ______________________          Date: ______________')

    r.front('Acknowledgement')
    r.P('[[Name your supervisor, lab staff, the CGM team and anyone else who helped. The project records do not list these people, so they are left for you to add.]]')
    r.P('The project used open tools and data from their authors: the simglucose simulator, KiCad, LTspice, Freerouting and the manufacturers\' public datasheets.')

    r.front('Abstract')
    r.P('Automated insulin delivery combines a glucose sensor, a control algorithm, a pump and a safety layer. This project followed that chain from algorithm to hardware design. It began with a Python study on the simglucose UVA/Padova simulator and a separate C++ Bergman minimal-model simulator. These were merged into HybridPancreasSim, a single C++ code base running PID control, a Control-IQ-style predictive controller and an independent safety supervisor, on both desktop and ESP32 targets. The hardware objective then moved to a battery-powered piezoelectric syringe pump: a Piezo LEGS LL06 motor, PMD401 driver and Hamilton 1 mL syringe, controlled by an STM32WBA55 with Bluetooth LE and supervised by a dissimilar STM32C031.')
    r.P('On the calibrated Bergman plant over one simulated 24 h day with three meals, the predictive controller reached 93.3 % time in range against 89.0 % for PID, with peak glucose 224.7 against 298.8 mg/dL and no time below 70 mg/dL. Injecting a false 380 mg/dL sensor reading drove true glucose to 51.1 mg/dL without the supervisor, with 114 min below 70 mg/dL; with the supervisor, glucose stayed above 70 mg/dL all day. A 4-layer, 111.5 × 85 mm Rev B board with 158 footprints was designed in KiCad 10 and reported 0 ERC violations, 0 DRC violations, 0 unconnected pads and 0 schematic-parity issues. Open-loop LTspice runs of an earlier flyback stage gave 82 to 85 % simulated efficiency.')
    r.P('**All results are simulation, calculation or software-rule checks. Nothing in the Rev B design has been built or measured, and the bench validation plan has not been run.** Critical items remain open, including the switching-FET voltage margin, transformer leakage and the PMD401 absolute maximum voltage. The board is not fabrication-ready and this work makes no clinical claim.')
    r.P('**Keywords:** artificial pancreas, Bergman minimal model, PID control, predictive control, safety supervisor, fault injection, piezoelectric motor, flyback converter, STM32WBA55, PCB design.')

    r.front('Table of Contents')
    r.toc(' TOC \\o "1-2" \\h \\z \\u ')
    r.front('List of Figures')
    r.toc(' TOC \\h \\z \\t "Figure Caption,1" ')
    r.front('List of Tables')
    r.toc(' TOC \\h \\z \\t "Table Caption,1" ')
    r.P('Tables inside the record appendices (C to H) are reproduced from project documents and are not numbered here.')

    r.front('List of Abbreviations')
    r._grid(['Term', 'Meaning', 'Term', 'Meaning'], [
        ['ADC', 'Analog-to-digital converter', 'IOB', 'Insulin on board'],
        ['AEN', 'PMD401 park/enable input', 'LBGI', 'Low blood glucose index'],
        ['AID', 'Automated insulin delivery', 'LDO', 'Low-dropout regulator'],
        ['BG', 'Blood glucose', 'LSE', 'Low-speed external oscillator'],
        ['BLE', 'Bluetooth Low Energy', 'MCU', 'Microcontroller unit'],
        ['BOM', 'Bill of materials', 'MPC', 'Model predictive control'],
        ['CCM', 'Continuous conduction mode', 'OVP', 'Overvoltage protection'],
        ['CF', 'Correction factor (mg/dL per U)', 'PID', 'Proportional-integral-derivative'],
        ['CGM', 'Continuous glucose monitor', 'RF', 'Radio frequency'],
        ['CR', 'Carbohydrate ratio (g per U)', 'RHP', 'Right-half-plane'],
        ['DNP', 'Do not populate', 'SC', 'Subcutaneous'],
        ['DRC', 'Design rules check', 'SMPS', 'Switched-mode power supply'],
        ['ECO', 'Engineering change order', 'SPI', 'Serial peripheral interface'],
        ['EGP', 'Endogenous glucose production', 'SWD', 'Serial wire debug'],
        ['ERC', 'Electrical rules check', 'T1D', 'Type 1 diabetes'],
        ['FET', 'Field-effect transistor', 'TIR', 'Time in range (70 to 180 mg/dL)'],
        ['HBGI', 'High blood glucose index', 'TVS', 'Transient voltage suppressor'],
        ['HSE', 'High-speed external oscillator', 'U', 'Insulin unit; 1 U = 10 µL at U-100'],
    ], [1, 3, 1, 3], 'Cell')


def ch1(r):
    r.chapter('Introduction', 1)
    r.S('Background')
    r.P('People with type 1 diabetes depend on external insulin. An insulin pump gives a slow basal flow and larger meal boluses. A hybrid closed-loop system adds a continuous glucose sensor and an algorithm that adjusts delivery automatically [5]. Three engineering problems meet in such a system: the control law, the precision of the actuator, and the behaviour when any part fails.')
    r.S('Motivation')
    r.P('A wrong dose can harm quickly, and a faulty sensor reading looks exactly like a real one to a controller. This makes the problem a useful engineering exercise: a control result only has value if it survives faults, and a pump design only has value if it reaches a safe state on its own. The project was also set a novelty requirement (U-9), which led to sensorless occlusion detection from the motor\'s step length.')
    r.S('Problem Statement')
    r.P('Develop and evaluate closed-loop insulin control with an independent safety layer in simulation, then design the electronics of a small, battery-powered, bench-only pump that could execute commanded doses correctly and stop safely on any single fault. The final objective, set by the project owner on 1 November 2026, is a digitally complete design with no fabrication.')
    r.S('Objectives')
    r.N('Compare PID and predictive control on a virtual patient, with and without a safety supervisor, using standard glycaemic metrics.',
        'Show the value of the supervisor through a sensor fault-injection test.',
        'Run the same control code on a desktop and on an embedded target.',
        'Select an actuation, control and power architecture for a piezoelectric syringe pump, with recorded reasoning.',
        'Produce a complete schematic and routed 4-layer PCB with clean ERC, DRC and parity reports.',
        'Analyse the power stage by calculation and SPICE, and report what cannot be closed without hardware.',
        'Write a bench validation plan and a handover record for the next engineer.')
    r.S('Scope and Limits')
    r.P('The work is an engineering prototype. It is restricted to water or 0.9 % saline, on the bench, at 18 to 28 °C, and is never to be connected to a person or an animal (decision K-1). Every limit in this report is an engineering target, not a clinical claim. The pump follows the methods of medical standards where useful but is not certified to any of them.')
    r.S('Evidence Levels Used in This Report')
    r.P('Every number in this report belongs to one level in {tab:levels}. No measured value exists for the Rev B design or the piezo hardware, so no result here should be read as experimental.')
    r.tab('Evidence levels', 'levels', ['Level', 'Meaning', 'Examples'], [
        ['Calculation', 'Hand or script calculation from datasheet values', 'Duty cycle, Lp, discharge time'],
        ['Simulation', 'Numerical model of a circuit or patient', 'Bergman runs, LTspice decks'],
        ['Software rule check', 'A tool compares design files with rules', 'ERC, DRC, parity, pin map'],
        ['Bench measurement', 'Instrument reading on real hardware', '**None exists for Rev B or Rev A**'],
    ], [1.3, 3, 2])
    r.S('Project Evolution')
    r.P('{fig:evolution} shows how the work moved. The hardware objective changed several times, and each change is recorded in the decision log (Appendix D). The objective changed from a Rev A bench build, to a digital handover on 10 October, to a fabricated prototype on 31 October, and finally to digital-only on 1 November 2026.')
    r.fig(f('evolution'), 'Project stages from the first simulators to the final digital board.', 'evolution')
    r.P('The Python study (13 July 2026) and the first C++ simulator (28 July 2026) came first; their file dates are the record. HybridPancreasSim merged them in August. {tab:stages} lists what each stage left behind.')
    r.tab('Stages and artefacts', 'stages', ['Stage', 'Date (2026)', 'Artefact', 'Current status'], [
        ['Python study', '13 Jul', '`insulin_pump_sim`: controllers, evaluation, fault demo', 'Background result'],
        ['First C++ simulator', '28 Jul', '`PancreasSim`: Bergman plant, PID, MPC stub', 'Merged'],
        ['HybridPancreasSim', 'Aug', 'Merged C++ code, HTML report, ESP32 firmware', 'Results stand; hardware superseded'],
        ['v1 stepper rig', 'to 8 Sep', 'ESP32, A4988, NEMA 17, T8 leadscrew, 3S LiPo', 'Superseded (no measurements on file)'],
        ['v2 architecture', '21 to 30 Sep', 'LL06, PMD401, WBA55, C031; Rev A list, firmware reference', 'Current baseline'],
        ['Requirements', '10 Oct', 'Requirements, parts and verification report', 'Current baseline, partly PROPOSED'],
        ['Rev B digital', '10 Oct to 1 Nov', 'KiCad project, simulations, handover documents', 'Final state, tag `pcb-p6-final`'],
    ], [1.5, 1, 3.2, 1.8])
    r.S('Report Organisation')
    r.P('Chapter 2 reviews existing work. Chapter 3 gives the method and models, and justifies design choices. Chapter 4 describes the software and hardware implementation. Chapter 5 presents results, efficiency and failed attempts. Chapter 6 concludes and identifies specific future work. The appendices hold all source code, raw run reports and the complete project records.')


def ch2(r):
    r.chapter('Literature Review', 2)
    r.S('Glucose-Insulin Models')
    r.P('The Bergman minimal model describes glucose and insulin dynamics with a few parameters and was introduced to estimate insulin sensitivity [1]. Its small state count makes it suitable for a microcontroller. The UVA/Padova simulator is far larger and is intended to stand in for preclinical trials of closed-loop algorithms [2]; simglucose is an open-source Python implementation of the earlier version [3]. This project used both: UVA/Padova through simglucose for the first study, and Bergman where the code had to run on an embedded target.')
    r.S('Control Strategies')
    r.P('PID reacts to the present error and has no knowledge of meals. Hybrid closed-loop systems add a forecast and an announced meal bolus. Control-IQ, for example, was evaluated in a randomised trial [5]; only its public description informed the predictive controller here. This project does not reproduce that product. A true MPC was planned in the first C++ simulator, but its controller remained a proportional placeholder and was not used for any result (Section 4.2).')
    r.S('Glycaemic Metrics')
    r.P('Time in range 70 to 180 mg/dL and time below 70 mg/dL are the consensus reporting metrics for CGM data [6]. LBGI and HBGI weight excursions through a log-symmetrising transformation, so severe lows count far more than mild ones [4]. Both are used in Chapter 5, on simulated data only.')
    r.S('Commercial Pump Architectures')
    r.P('The project\'s background note surveyed commercial pumps (Medtronic MiniMed, Tandem t:slim X2, Insulet Omnipod). Its main lesson for this work was architectural: a main processor runs the therapy while a second, independent processor checks limits and can remove motor power. That pattern shaped the supervisor in simulation and the C031 on the board. The note\'s figures were treated as background and not as requirements. Owner decision U-14 was to recreate the function, not to copy any specific product.')
    r.S('Piezoelectric Drug Delivery')
    r.P('A paper by Kaçar, Özer and Taşçıoğlu used a piezoelectric valveless micropump with PID control on a Bergman plant [7]. It was background only, as its actuator differs from the one chosen. The single-PZT and valve route was examined and rejected on 27 September 2026 in favour of positive displacement (Section 3.9).')
    r.S('Standards')
    r.P('IEC 60601-2-24 and AAMI TIR101 describe dose-accuracy testing, ISO 14971 risk management, IEC 62304 software life cycle, and IPC-2221/IPC-2152 board design [15]-[19]. The full list and how far each is followed appear in Appendix C. Only web summaries were available: the standard texts themselves were not held, and values quoted from them in project documents are flagged for checking.')
    r.S('Gap Addressed')
    r.P('Published simulation studies often stop at the algorithm, and pump designs seldom show the path from an algorithm\'s fault behaviour to hardware. This project carries one safety idea, an independent supervisor that fails safe, from simulation through firmware concept into copper. Its proposed novelty, sensorless occlusion detection from step length, is still an unproven hypothesis on hardware.')


def ch3(r):
    r.chapter('Methodology', 3)
    r.S('Overall Approach')
    r.P('The method in {fig:method} moved from algorithm to architecture, then through iterated schematic and layout steps. Each step ended with real tool output, and every board state was tagged in git before modification. This made every step recoverable: the final repository holds 45 commits and 34 tags.')
    r.fig(f('method'), 'Development flow. The bench step was planned but not run.', 'method')
    r.S('Patient Model')
    r.P('The plant is the Bergman minimal model with parameters for a T1D patient, shown in {fig:bergman}. It has three states: glucose G (mg/dL), remote insulin action X (1/min) and plasma insulin I (mU/L).')
    r.fig(f('bergman'), 'Compartments of the Bergman plant with the added EGP term.', 'bergman', 5.6)
    r.eq('dG/dt = −p~1~(G − G~b~) − XG + EGP + D', 'bg')
    r.eq('dX/dt = −p~2~X + p~3~(I − I~b~)', 'bx')
    r.eq('dI/dt = −n(I − I~b~) + u/V', 'bi')
    r.P('Here u is pump infusion (mU/min) and D is meal glucose appearance (mg/dL/min). The states advance by forward Euler with a 3 min step and are limited to non-negative values. {tab:bparams} lists the constants.')
    r.tab('Plant constants as coded', 'bparams', ['Symbol', 'Value', 'Meaning'], [
        ['p~1~', '0', 'Glucose effectiveness, 0 for T1D'], ['p~2~', '0.0106 1/min', 'Insulin action decay'],
        ['p~3~', '8.1 × 10^−6^', 'Insulin sensitivity gain'], ['n', '0.0926 1/min', 'Insulin clearance'],
        ['V', '12 L', 'Insulin distribution volume'], ['G~b~, I~b~', '90 mg/dL, 15 mU/L', 'Basal references'],
        ['EGP', '1.96 mg/dL/min', 'Added hepatic production (calibrated)'],
    ], [1, 2, 3.5])
    r.SS('Why an EGP term was added')
    r.P('The original T1D form has p~1~ = 0 and no glucose source. Any positive basal gives X > 0, so dG/dt is always negative and fasting glucose collapses towards zero. The first C++ simulator showed this tendency: with basal only 1 mU/min, its glucose was still falling at the end of the day. EGP gives a finite steady state. Setting the derivatives to zero gives:')
    r.eq('I~ss~ = I~b~ + u/(nV),   X~ss~ = p~3~(I~ss~ − I~b~)/p~2~,   G~ss~ = EGP/X~ss~', 'ss')
    r.P('With basal 1.4253 U/h (adult#003, from simglucose), u = 23.755 mU/min. Then I~ss~ = 36.38 mU/L, X~ss~ = 0.016336 1/min and G~ss~ = 119.98 mg/dL, which matches the coded initial state (120, 0.016335, 36.38). I recomputed these independently of the C++ code.')
    r.SS('Why Bergman and not UVA/Padova in the final simulator')
    r.P('simglucose is a Python dependency too heavy to run on a microcontroller. The merged code kept the portable parts, namely the controllers, supervisor and metrics. Constants such as K~carb~ and EGP were re-calibrated for this simpler plant, so absolute glucose values differ between stages and should not be compared as if they were the same patient.')
    r.S('Meal, Insulin and Sensor Models')
    r.P('Meals of 45, 70 and 60 g occur at 07:00, 12:00 and 19:00. Each one appears uniformly over a 45 min window:')
    r.eq('D(t) = Σ m~i~ K~carb~ / W   for t~i~ ≤ t < t~i~ + W,   K~carb~ = 3.5 mg/dL/g,   W = 45 min', 'meal')
    r.P('Bergman has no subcutaneous depot, so a bolus would act instantly. A first-order depot releases it instead, with Δt = 3 min and τ = 40 min. Basal goes directly to the plasma input:')
    r.eq('R~k~ = S~k~ Δt/τ,   S~k+1~ = S~k~ + bolus~k~ − R~k~', 'depot')
    r.eq('u~k~ = 1000 (basal/60 + R~k~/Δt)   [mU/min]', 'units')
    r.P('The CGM reading is true glucose plus Gaussian noise of 1.5 mg/dL standard deviation, using a fixed seed (42). The noise is needed: without it, the noiseless plant at steady state looks frozen and falsely trips the stuck-sensor check. The injected fault is kept exact, so that a real frozen sensor is still detectable. The closed loop is shown in {fig:simblock}.')
    r.fig(f('sim_block'), 'Closed-loop simulation structure in main.cpp.', 'simblock')
    r.S('Controllers')
    r.SS('PID baseline')
    r.P('The controller trims basal about the patient\'s steady need, with target 120 mg/dL, K~P~ = 0.02, K~I~ = 0.0002 and K~D~ = 0.01. The integral state is limited to ±2000 to prevent windup, and basal cannot go below zero. It delivers no boluses.')
    r.eq('basal = basal~0~ + K~P~e + K~I~∫e dt + K~D~ de/dt,   e = CGM − target', 'pid')
    r.SS('Predictive controller')
    r.P('This Control-IQ-style controller ({fig:predflow}) fits a line through the last six CGM samples and extrapolates 30 min ahead. It shapes basal from the forecast, gives a meal bolus when a meal is announced, and otherwise allows a correction bolus limited by IOB and a 60 min lockout. IOB decays linearly over 4 h, an approximation noted for improvement.')
    r.eq('Ĝ = max(20, a(t~last~ + 30) + b),   (a, b) from least squares over 6 samples', 'pred')
    r.eq('bolus~meal~ = min[ m/CR + max(0, (CGM − target)/CF), IOB~max~ ]', 'bolus')
    r.eq('bolus~corr~ = min[ (Ĝ − target)/CF, IOB~max~ − IOB ],   if Ĝ > 180 and IOB < IOB~max~', 'corr')
    r.P('The merged simulator uses CR = 14 g/U, CF = 50 mg/dL/U and IOB~max~ = 8 U. The class default for CR is 10; 14 was chosen for the Bergman plant.')
    r.fig(f('predictive_flow'), 'Decision flow of the predictive controller.', 'predflow')
    r.SS('Why these two controllers')
    r.P('{tab:ctrl} summarises the choice, using the five questions set for every design decision.')
    r.tab('Control design decision', 'ctrl', ['Question', 'Answer'], [
        ['What was chosen?', 'PID as baseline; linear-forecast predictive controller as candidate'],
        ['Why?', 'PID shows what reaction alone can do. The forecast captures the main benefit of hybrid closed loop with a few lines of code that fit an MCU'],
        ['Alternatives?', 'True MPC, left as a stub in `PancreasSim` because no QP solver was built'],
        ['Reasoning?', 'A rapid meal rise cannot be caught by reactive control given insulin delay; an announced bolus acts ahead of the rise'],
        ['Verification?', 'Four-way 24 h simulation in both Python and C++. No hardware or clinical verification'],
    ], [1.2, 5])
    r.S('Safety Supervisor')
    r.P('The supervisor wraps any controller ({fig:supflow}) and trusts only limits it can check itself. It always calls the primary controller, so the primary\'s state stays consistent, then checks the sensor and the proposed action. This mirrors the dual-MCU pattern of real pumps.')
    r.fig(f('supervisor_flow'), 'Decision flow of the SafetySupervisor.', 'supflow', 5.4)
    r.tab('Supervisor limits as coded', 'suplim', ['Check', 'Limit', 'Action'], [
        ['CGM range', '39 to 400 mg/dL, NaN rejected', 'Suspend'], ['CGM jump', 'More than 40 mg/dL between samples', 'Suspend'],
        ['CGM stuck', 'Change ≤ 0.05 mg/dL, count reaches 2', 'Suspend'], ['Basal', '0 to 4 U/h', 'Clamp'],
        ['Bolus size', '0 to 10 U', 'Clamp'], ['Bolus interval', 'At least 5 min', 'Reject bolus'],
    ], [1.5, 3.2, 1.2])
    r.S('Evaluation Metrics')
    r.P('Metrics use **true** plant glucose, not the CGM reading, over 480 samples. TIR counts samples from 70 to 180 mg/dL inclusive. The risk indices use the Kovatchev transformation [4]:')
    r.eq('f(G) = 1.509[(ln G)^1.084^ − 5.381],   r(G) = 10 f(G)^2^', 'risk')
    r.eq('LBGI = (1/N) Σ r(G)|~f<0~,   HBGI = (1/N) Σ r(G)|~f≥0~', 'lbgi')
    r.S('Fault-Injection Method')
    r.P('A value of 380 mg/dL replaces the CGM for three consecutive samples from t = 180 min (steps 60 to 62). The fault affects only what the controller sees. It ran on the predictive controller, with and without the supervisor, using the same meals and noise seed.')
    r.S('Hardware Architecture')
    r.P('The Rev B architecture is shown in {fig:revb}. One Li-ion cell feeds a 3.3 V buck for logic and a flyback for the 48 V motor rail. The motor rail runs only during a dose. The main MCU closes the position loop on the motor\'s encoder and commands a step rate over SPI, while the supervisor owns the veto and the park line.')
    r.fig(f('revb_block'), 'Rev B system block diagram. The red dashed line is the enable path of the 48 V stage.', 'revb')
    r.SS('Dose arithmetic')
    r.P('The syringe bore of 4.61 mm has an area of 16.69 mm², so 1 µm of travel is 16.69 nL. All the following values are calculated.')
    r.eq('x = V/A = 10 µL / 16.69 mm² = 599 µm per unit, or 7,489 encoder counts at 80 nm', 'dose')
    r.P('The smallest dose, 0.05 U, is 30.0 µm or 375 counts. A full syringe is 750,000 counts, so position must be a 32-bit value. Line pressure p gives motor load F = pA: 0.83 N at 0.5 bar and 1.67 N at 1 bar. The 6.5 N stall force limits pressure to about 3.9 bar against the syringe\'s 13.8 bar rating.')
    r.S('Component and Design Decisions')
    r.P('{tab:decide} gives the main hardware decisions, the alternatives rejected, the supporting reasoning and how far each was verified. The whole chronological log is in Appendix D.')
    r.tab('Engineering justification of main choices', 'decide', ['Choice', 'Why', 'Alternatives rejected', 'Support', 'Verified by'], [
        ['Piezo LEGS LL06, 80 nm encoder', 'Direct drive with no gears. Self-locks unpowered above 6.5 N, so power loss clamps the plunger', 'NEMA 8/11, Faulhaber AM0820 (size); Shinsei USR30 (humidity limits for Guwahati, thrust load, size); Squiggle, DTI (not selected); LT20 (superseded)', '0.05 U is about 30 µm; a 1.25 µm encoder is too coarse to sense step length', 'Vendor reply and datasheet; not measured'],
        ['PMD401 driver', 'Four synchronised 0 to 48 V channels; servo SPI mode; 10 ms SPI timeout gives a stop path', 'DRV8662, DRV2700 (single channel); custom HV driver', 'Motor needs four phases', 'Manual; not measured'],
        ['Hamilton 81320 syringe', 'Glass and PTFE positive displacement, known bore, 13.8 bar', 'Diaphragm and valve pump; Hamilton 1005', 'Pressure ceiling calculation', 'Friction unknown'],
        ['STM32WBA55CG main MCU', 'BLE and TrustZone on one chip, single-core BLE firmware, stronger radio than WB55', 'NUCLEO-WB55RG; STM32U585 + nRF module; G431, G474; ESP32 (owner: STM32 only)', 'No separate radio module; path from Nucleo to PCB', 'CubeMX database, 41 assigned functions, 0 failures'],
        ['STM32C031C6 supervisor', 'Different core, clock and code base, so one fault cannot defeat both', 'STM32C011; merged function in one MCU', 'Single-fault reasoning', 'Pin map; firmware not written'],
        ['LM51551 flyback', 'Plain boost from 3 V to 48 V hits the 93 % duty limit; n = 5 gives D = 0.70 to 0.77', 'Plain boost; two-stage modules (used only on Rev A plan)', '{eq:duty}', 'Open-loop SPICE; no loop model'],
        ['HPH6-0090L transformer', 'Off-the-shelf; 7.29 µH, 1 + 5 windings, 27.6 A saturation in this connection', 'LPR6235-253LMR (1.3 A saturation); Würth LT3748 parts (step-down ratio)', 'Coilcraft Doc 613', 'Leakage unpublished'],
        ['AONR34332C switch', 'Rated at 2.5 V gate (under 2.9 mΩ) because gate drive equals VBAT', 'CSD16340Q3 (25 V, margin failed); CSD18543Q3A, AON2240, SSM3K339R (gate or loss)', 'Clamp study at 4.9 A', 'SPICE; margin still open'],
        ['TPS62840 3.3 V buck', 'Very low quiescent current for battery life', 'MCP1700 LDO (Rev A plan only)', 'P-04', 'Datasheet'],
        ['BQ25188 charger', 'Decided part; SYS unloaded so charger is never the load path (E-09)', 'BQ25180; TP4056 (Rev A plan)', 'SLUSFJ3', 'Footprint pitch inferred'],
        ['Veto default on (R403 pull-up)', 'A dead supervisor must block 48 V (S-01)', 'Rev A pull-down, which gives no veto when dead', 'Owner, 10 Oct', 'Hardware test SG-03 not run'],
        ['4 layers, solid GND on In1', 'RF reference, pulsed return currents', 'Layer count was analysed before choice as required', 'P-02', 'DRC; no SI analysis'],
        ['U.FL with MLPF-WB-04D3', 'Avoids unverified antenna geometry; ST integrated filter', 'PCB antenna; discrete pi-match placeholder', 'DS14446, AN5948', 'Solver estimate; no RF test'],
    ], [1.3, 2, 1.9, 1.2, 1.1])
    r.S('Power Stage Calculations')
    r.P('All design values come from TI SNVSB75E and are calculated [8]. With turns ratio n = N~s~/N~p~ = 5 and V~F~ ≈ 0.9 V:')
    r.eq('V~out~ + V~F~ = n V~in~ D/(1 − D)  ⇒  D = 0.765 at 3.0 V; D = 0.70 at 4.2 V', 'duty')
    r.eq('f~sw~ = 2.21×10^10^/(R~T~ + 955) = 298 kHz   for R~T~ = 73.2 kΩ', 'fsw')
    r.eq('L~p~ = V~in~ D/(ΔI f~sw~) = 3.0 × 0.765/(1.04 A × 298 kHz) ≈ 7.3 µH', 'lp')
    r.eq('I~lim~ = V~CLTH~/R~s~ = (93 to 107 mV)/22 mΩ = 4.2 to 4.9 A', 'ilim')
    r.eq('t~ss~ = C~ss~ V~ref~/I~ss~ = 1 µF × 1 V/10 µA = 100 ms', 'tss')
    r.eq('V~out~ = 1 V × (1 + 470 kΩ/10 kΩ) = 48.0 V', 'vout')
    r.eq('ΔV = I~out~D/(f~sw~C)  ⇒  C ≥ 1.1 µF effective for 0.24 V ripple', 'ripple')
    r.eq('t~dis~ = R C ln(V~0~/5 V) = 10 kΩ × 182 µF × ln(50.4/5) = 4.21 s', 'dis')
    r.P('The primary average current at 3.0 V, 4.8 W output and an assumed 80 % efficiency is 2.61 A, with ΔI at 40 % of that. The soft-start value was first 47 nF (4.7 ms) and was raised after simulation showed repeated hiccup (Section 5.7). The bleeder result satisfies the proposed E-11 limit of 5 V within 5 s. With 0.1 % divider resistors, the setpoint is 47.43 to 48.58 V.')
    r.S('Fail-Safe Kill Path')
    r.P('{fig:kill} shows the kill path. FLY_EN is the LM51551 UVLO/EN pin. R401 pulls it low by default, and the MCU can raise it only through 1 kΩ, giving 3.3 × 4.7/5.7 = 2.72 V, above the 1.5 V UVLO threshold. Q401 can short the node regardless of the MCU, and its gate pull-up holds the veto on until the supervisor actively drives it low. An independent zener trip (D303, Q304) also pulls FLY_EN low at a calculated 50.5 to 53.9 V. The PMD401 AEN input uses the same logic through open-drain Q402, parked by default.')
    r.fig(f('kill_path'), 'Kill path around FLY_EN.', 'kill')
    r.P('Three independent stop paths are specified (S-03): the PMD401 stops after about 10 ms without SPI data; the supervisor parks and cuts 48 V on a bad heartbeat; and firmware halts on detected corruption. **Copper continuity does not prove this behaviour. Checks SG-01 to SG-08 need hardware and have not been run.**')
    r.S('Requirements and Validation Plan')
    r.P('The requirements register holds 14 owner-level requirements and 76 numbered technical requirements in seven groups (Appendix C), and many are marked PROPOSED pending sign-off. The bench plan (Appendix D) has 13 check groups, from incoming inspection to Rev B regression, with a rule that nothing downstream counts if a kill-path check fails. It is a plan; no line has a recorded result.')


def ch4(r):
    r.chapter('Implementation', 4)
    r.S('Software Stage 1: Python Study')
    r.P('`insulin_pump_sim` uses simglucose with patient adult#003, a Dexcom sensor model and an Insulet pump model, with the same three meals. It introduced the `Controller.policy()` interface, the four configurations and the fault demo. The source is in Appendix B.')
    r.S('Software Stage 2: First C++ Simulator')
    r.P('`PancreasSim` is a small C++ loop with a 1 min step: a Bergman plant without EGP, a PID with target 90 mg/dL and ±500 anti-windup, a 25 mU/min pump limit and meals given directly as disturbance. It logs to CSV for `plot.py`. Its `MPCController` holds only a TODO and a proportional placeholder. This stage established the plant used later, and showed why EGP was needed.')
    r.S('Software Stage 3: HybridPancreasSim')
    r.P('The merged project keeps a single set of headers. `BergmanModel.h` is the plant. `Controllers.h` holds the base class and the three controllers. `main.cpp` runs the configurations, computes metrics, and writes six CSV files plus a self-contained `report.html` with inline SVG charts and no library dependency. I confirmed that the desktop and ESP32 copies of both headers are byte-identical. All code is listed in Appendix A.')
    r.tab('Source files', 'src', ['File', 'Bytes', 'Role'], [
        ['`desktop/BergmanModel.h`', '2,679', 'Plant with EGP, Euler step'], ['`desktop/Controllers.h`', '11,191', 'PID, Predictive, SafetySupervisor'],
        ['`desktop/main.cpp`', '20,102', 'Runs, fault test, metrics, CSV, HTML and SVG'], ['`esp32/sketch.ino`', '10,308', 'Firmware: manual and auto modes'],
        ['`esp32/diagram.json`', '1,863', 'Wokwi wiring'], ['`esp32/libraries.txt`', '66', 'Arduino library list'],
    ], [2.6, .8, 3.2])
    r.P('Build and run, using MinGW g++ 6.3.0 on this machine:')
    r.code('g++ -O2 -std=c++17 -o hybrid_sim main.cpp\n./hybrid_sim')
    r.d.add_paragraph()
    r.S('ESP32 Firmware')
    r.P('The firmware runs Predictive + Supervisor on-device ({fig:esp}). In manual mode a typed glucose value goes through the supervised controller and moves the stepper in proportion, at 256 steps per unit. In auto mode the on-board Bergman patient runs a closed loop, one 5 min step every 250 ms. A red LED lights when the supervisor logs a new alarm. Typing `120` twice and then `380` demonstrates a rejection, which shows `SUSPEND` on the OLED.')
    r.fig(f('esp32_wiring'), 'ESP32 demonstration wiring from diagram.json.', 'esp', 5.6)
    r.P('The firmware step is 5 min against 3 min on desktop, and its noise is uniform instead of Gaussian, so its traces would differ from Chapter 5. No log of a firmware run is on file, so I report the code and wiring but no firmware results. This hardware belongs to v1 and is fully replaced in v2.')
    r.S('Design Automation for the Board')
    r.P('`scripts/design.py` (437 lines) is the single source of truth for parts, nets and status. Generators produce the library, schematic and first PCB. After routing began, the board was edited in place by reviewed scripts to preserve copper. {tab:scripts} lists the toolchain.')
    r.tab('Board scripts (Python)', 'scripts', ['Script', 'Lines', 'Purpose'], [
        ['`design.py`', '437', 'Parts, nets, values, status, notes'], ['`gen_library.py`', '230', 'Project symbols and footprints'],
        ['`gen_schematic.py`', '297', 'Hierarchical schematic and net classes'], ['`gen_pcb.py`', '707', 'Board, placement, planes, Specctra exchange, moves'],
        ['`kicadlib.py`', '155', 'KiCad S-expression helpers'], ['`route_stage.py`', '204', 'Applies explicit, reviewable route specifications'],
        ['`grid_route.py`', '240', 'Deterministic A* router for one named connection'], ['`hand_route.py`', '154', 'DRC-gated connection attempts'],
        ['`pcb_eco.py`', '220', 'Applies footprint and placement ECOs in place'], ['`pcb_silk.py`, `pcb_outline.py`, `pcb_rf_mask.py`', '149, 24, 16', 'Silkscreen, outline, RF mask opening'],
        ['`verify_pinmap.py`', '91', 'Checks pins against STM32CubeMX database'], ['`eval_placement.py`, `compare_placement.py`, `compare_stage.py`', '109, 178, 66', 'Scratch evaluation, comparison with checkpoints'],
        ['`reconcile_unrouted.py`, `unrouted_corridors.py`, `review_clearance.py`', '101, 66, 73', 'Unconnected-pair accounting, corridors, clearances'],
    ], [3, .8, 3])
    r.S('Schematic')
    r.P('The schematic is hierarchical, with a root and seven sub-sheets. Each part carries a Status field (DECIDED, DS, CALC, ASSUMED, TBD or PLACEHOLDER), an MPN and a source note. Of 144 references in `docs/bom_detailed.csv`: 52 are DS, 35 CALC, 30 ASSUMED, 23 DECIDED, 3 PLACEHOLDER and 1 TBD. The sheets appear in Section 4.11.')
    r.SS('Schematic change orders')
    r.P('ECO1 applied the ST data once available, correcting WBA55 supply wiring to DS14127 Fig. 15, adding the RF filter, selecting the real transformer, raising soft start to 1 µF, fitting the LSE crystal and adding BSS138 shifters for READY and FAULT. ECO2 replaced a TVS clamp with an independent trip, changed Q301 to a 30 V part with a clamp ceiling, and added 1 kΩ and divider protection on SPI. ECO3 added an optional gate resistor with a bridge, and an unfitted drain snubber. Each was checked against a net plan, and full records are in Appendix F.')
    r.S('PCB Layout')
    r.tab('Final board data from validation/logs/p6_netlist_audit.txt', 'board', ['Item', 'Value'], [
        ['Outline', '111.5 × 85 mm, 4 M3 holes'], ['Layers', 'F.Cu and B.Cu with GND pours; In1 solid GND; In2 VBAT and +3V3 split'],
        ['Footprints', '158 (4 parts on B.Cu: C313, JP301, R315, R316)'], ['Tracks / vias', '1,114 / 277'], ['Routed length', '2,991 mm'],
        ['Generic rules', '0.15 mm track and space; 0.3 mm drill, 0.5 mm via; 0.3 mm copper to edge'], ['HV48 class', '0.6 mm clearance on all layers'],
        ['RF line', 'U501 to filter 0.20 mm, filter to U.FL 0.32 mm, gap 0.25 mm, mask open; assumed JLC04161H-7628 stack-up'],
        ['Scoped DRC exceptions', '3: J703, Q301, FL501 pad gaps (`pump_v2.kicad_dru`)'],
    ], [1.7, 4.8])
    r.S('Placement and Routing Stages')
    r.P('The first autorouted board stalled, since Freerouting plateaued around 40 to 65 unrouted connections. Analysis in the blocker report showed the cause was placement: the U501 fan-out was congested, connectors were far from their MCUs, and the flyback block sat between the MCUs and PMD401 connectors. The clamp and secondary loops were also long. Three placement variants were evaluated on scratch copies, and the owner approved v2 without M8, also leaving R711, R712 and R312 in place.')
    r.tab('Effect of the applied placement (straight pad-to-pad, indicative)', 'place', ['Loop or path', 'Baseline (mm)', 'After (mm)'], [
        ['Clamp loop', '59.7', '13.9'], ['Secondary loop', '73.1', '18.8'], ['Gate', '11.0', '3.4'], ['Current sense', '12.9', '6.5'],
        ['VCC capacitor', '6.6', '3.2'], ['Soft start', '6.1', '3.5'], ['R311 to J703', '13.3', '4.0'], ['C702 to J703', '18.3', '11.2'],
        ['FLY_SW node (made worse deliberately)', '3.9', '7.4'], ['35 tracked nets, total airwire', '1,323.9', '1,031.6 (−22 %)'],
    ], [3.5, 1.2, 1.5])
    r.fig(os.path.join(REPO, 'validation', 'placement', 'placement_baseline_e8d141c.png'), 'Placement at the baseline routing tag, before optimisation.', 'pl0', 5.2)
    r.fig(os.path.join(REPO, 'validation', 'placement', 'placement_applied_v2.png'), 'Approved v2 placement after rip-up (not yet routed).', 'pl1', 5.2)
    r.P('Routing then proceeded in stages with explicit geometry, each followed by DRC, parity and a comparison with its checkpoint. Stages 1 to 4 covered controller nets, encoder and console, the D1 rotation, safety nets and encoder connections. Stage 5a and the D7 investigation closed nothing, but showed U501 pin 28 could not be escaped without coordinated work. After the ECOs, P1 updated footprints in place, P2 and P4 routed RF, supplies and signals, and P6 finished the flyback, 48 V and charger. Details are in Appendix G.')
    r.fig(os.path.join(REPO, 'validation', 'routing', 'p2', 'p2_u501_fcu.png'), 'F.Cu around U501 after Stage P2. The RF line runs straight to the filter and U.FL with no vias.', 'p2', 4.8)
    r.S('RF Layout')
    r.P('A 2-D finite-difference solver (`validation/sim/rf_line_solver.py`) estimated line impedance. It gives 60.6 Ω on ST\'s own 0.30/0.15 mm example, for which ST specifies 63 Ω, so it reads about 4 % low. Earlier width estimates of 0.25 and 0.36 mm were corrected. The final lines are 0.20 mm (62.9 Ω, to match the filter input) and 0.32 mm (50.5 Ω), with ±3 Ω sensitivity to dielectric and height. The RF_ANT line has 0 crossings. RF_MCU has one crossing, ENC_I_M on B.Cu with In1 GND between; coupling was not analysed. These are estimates with an assumed stack-up.')
    r.S('Board Views')
    r.P('{fig:top} and {fig:bot} are KiCad renders of the final board. Some parts, including T301, have no 3D model, so only their pads appear. {fig:layers} shows the four copper layers.')
    r.fig(os.path.join(REPO, 'docs', 'report_assets', 'board_3d_top.png'), 'Rendered top view of the final board. T301 pads appear at lower right without a body model.', 'top', 5.6)
    r.fig(os.path.join(REPO, 'docs', 'report_assets', 'board_3d_bottom.png'), 'Rendered bottom view of the final board.', 'bot', 5.6)
    import PIL.Image as I
    ims = [I.open(f('layer_' + x)).convert('RGB') for x in ('F_Cu', 'In1_Cu', 'In2_Cu', 'B_Cu')]
    ims = [im.crop(I.eval(im, lambda v: 255 - v).getbbox()) for im in ims]
    w, h = ims[0].size
    sheet = I.new('RGB', (2 * w + 60, 2 * h + 60), 'white')
    for i, im in enumerate(ims):
        sheet.paste(im.resize((w, h)), ((i % 2) * (w + 60), (i // 2) * (h + 60)))
    sheet.save(f('layers_all'))
    r.fig(f('layers_all'), 'Copper layers: F.Cu (top left), In1.Cu (top right), In2.Cu (bottom left), B.Cu (bottom right).', 'layers')
    r.fig(os.path.join(HO, 'images', 'pcb_routed_top_bottom.png'), 'Early autorouted board of 10 October with the placeholder transformer, kept to show the starting point. Superseded.', 'early', 5)
    r.S('Schematic Sheets')
    r.P('The eight sheets follow in landscape. The vector original is `docs/report_assets/schematic.pdf`.')


def sch_pages(r):
    sec = r.d.add_section(WD_SECTION.NEW_PAGE)
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Inches(11.69), Inches(8.27)
    names = ['Root sheet', 'Battery input, fuse, master switch and BQ25188 charger', 'TPS62840 3.3 V logic rail', 'LM51551 48 V flyback',
             'Kill path', 'Main MCU STM32WBA55', 'Supervisor STM32C031', 'PMD401 and encoder interface']
    for i, n in enumerate(names, 1):
        r.fig(f(f'sch-{i}'), f'Schematic sheet {i} of 8: {n}.', f'sch{i}', 8.6)
    sec2 = r.d.add_section(WD_SECTION.NEW_PAGE)
    sec2.orientation = WD_ORIENT.PORTRAIT
    sec2.page_width, sec2.page_height = Inches(8.27), Inches(11.69)


def ch5(r):
    r.chapter('Results and Discussion', 5)
    r.P('All results in this chapter are simulations or software checks. No value is a measurement.')
    r.S('Python Study on UVA/Padova (simglucose)')
    r.tab('Python study results from results/summary_metrics.csv (adult#003, 24 h)', 'py', ['Configuration', 'TIR (%)', '<70 (%)', '<54 (%)', '>180 (%)', '>250 (%)', 'LBGI', 'HBGI', 'Insulin (U)'], [
        ['PID', '77.5', '0.0', '0.0', '22.5', '0.0', '0.20', '4.08', '54.6'], ['PID + Supervisor', '77.5', '0.0', '0.0', '22.5', '0.0', '0.20', '4.08', '54.6'],
        ['Predictive', '99.6', '0.0', '0.0', '0.4', '0.0', '0.03', '1.47', '55.8'], ['Predictive + Supervisor', '99.6', '0.0', '0.0', '0.4', '0.0', '0.03', '1.47', '55.8'],
    ], [2.2, .7, .7, .7, .7, .7, .6, .6, .8])
    r.P('The predictive controller added 22.1 points of TIR for only 1.2 U more insulin. The supervisor changed nothing on the clean day. {fig:pycomp} is the original plot. In its 6 h fault test (no meals), the supervisor zeroed delivery on two of three faulted samples; the second sample passed at 1.85 U/h, as the README states. Boluses in the CSV total 1.263 U in both runs and are 0 U in the window, so the README\'s statement that the fault triggers a correction bolus is not borne out by these files.')
    r.fig(os.path.join(PY, 'results', 'comparison.png'), 'Original Python comparison plot from results/comparison.png. CGM traces, supervised and unsupervised traces overlap.', 'pycomp', 5.6)
    r.S('First C++ Simulator')
    r.P('{fig:psim} shows the 1 min PID run from its saved CSV. Starting at 160 mg/dL, glucose peaked at 194.3 mg/dL at the 750 min sample after the 4 mg/dL/min lunch disturbance. Its minimum, 78.4 mg/dL, came at the start of lunch. TIR was 96.6 % over 1,441 samples, and the run ended at 87.9 mg/dL. I re-derived these from the file. Meals here are not comparable with later stages, since D was chosen directly and not derived from carbohydrate grams.')
    r.fig(f('pancreas_sim'), 'PancreasSim PID run: glucose and pump delivery.', 'psim', 5.6)
    r.S('HybridPancreasSim: Four-Way Comparison')
    r.P('I rebuilt the simulator from the current source and re-ran it. All six regenerated CSV files were **byte-identical** to the saved ones in `desktop/results` and `results`, so these results are reproducible on this machine. {tab:metrics} comes from those files.')
    r.tab('Four configurations and fault runs, 24 h, calibrated Bergman plant', 'metrics', ['Run', 'TIR %', '<70 %', '>180 %', 'Mean', 'SD', 'Min', 'Max', 'LBGI', 'HBGI', 'Insulin U'], [
        ['PID', '88.96', '0.00', '11.04', '128.0', '40.6', '81.1', '298.8', '0.42', '2.38', '38.24'],
        ['PID + Sup.', '88.54', '0.00', '11.46', '128.7', '41.1', '84.6', '299.6', '0.36', '2.46', '38.06'],
        ['Predictive', '93.33', '0.00', '6.67', '114.4', '30.2', '71.5', '224.7', '0.92', '1.06', '42.98'],
        ['Pred. + Sup.', '93.33', '0.00', '6.67', '114.4', '30.2', '71.5', '224.7', '0.92', '1.06', '42.98'],
        ['Fault, no Sup.', '85.83', '7.92', '6.25', '109.3', '33.6', '51.1', '224.4', '2.09', '1.05', '45.98'],
        ['Fault, Sup.', '92.92', '0.00', '7.08', '117.5', '29.4', '74.2', '224.3', '0.61', '1.14', '41.73'],
    ], [1.5, .7, .6, .7, .7, .55, .55, .65, .6, .6, .8])
    r.P('Glucose values are in mg/dL. "Insulin" is the sum of infusion to plasma over the day, so bolus insulin still in the depot at 24 h is excluded.')
    r.fig(f('glucose_four'), 'True glucose for four configurations. Shading is 70 to 180 mg/dL; the two predictive traces coincide.', 'g4')
    r.SS('Interpretation')
    r.B('**Predictive against PID.** TIR rises by 4.37 points, and time above 180 mg/dL falls from 2.65 h to 1.60 h per day. Peak glucose falls by 74.1 mg/dL. An announced bolus acts during the meal rise, while PID must wait for error to grow, as {fig:ins} shows.',
        '**The cost.** The predictive controller uses 12.4 % more insulin and has a higher LBGI (0.92 against 0.42), with a minimum of 71.5 mg/dL at t = 534 min, only 1.5 mg/dL above the low limit. The improvement is not free: it moves risk towards the low side. A different CR or plant could cross 70 mg/dL.',
        '**Supervisor on a clean day.** With the predictive controller it logged 0 alarms and its output was identical, as a safety layer should be.',
        '**Supervisor is not always invisible.** With PID it logged 23 alarms and reduced TIR slightly, from 88.96 to 88.54 %. {fig:clamp} shows why: PID asks for up to 5.40 U/h at lunch and dinner, above the 4 U/h limit. In addition, at t = 1140 min one false stuck-sensor alarm suspended delivery for a step, when noise by chance produced consecutive near-identical readings. This is a real false positive of the 0.05 mg/dL tolerance.')
    r.fig(f('insulin_delivery'), 'Infusion reaching plasma for PID and Predictive + Supervisor.', 'ins')
    r.fig(f('pid_clamp'), 'Commanded PID basal, showing the 4 U/h clamp at lunch and dinner and the false suspension before dinner.', 'clamp')
    r.S('Fault-Injection Result')
    r.fig(f('fault_day'), 'False 380 mg/dL sensor reading at t = 180 min, whole day.', 'fd')
    r.fig(f('fault_zoom'), 'Infusion and true glucose around the fault.', 'fz')
    r.tab('Fault window from the CSV files', 'fw', ['t (min)', 'CGM seen', 'Unsupervised basal (U/h)', 'Unsupervised bolus (U)', 'Supervised basal (U/h)', 'Supervised bolus (U)'], [
        ['177', '118.3', '1.57', '0', '1.57', '0'], ['180', '380', '1.85', '**8.0**', '0', '0'], ['183', '380', '1.85', '0', '**1.85**', '0'],
        ['186', '380', '1.85', '0', '0', '0'], ['189', '≈117', '1.85', '0', '0', '0'], ['192', '≈115 to 117', '0', '0', '0', '0'],
    ], [.8, 1, 1.3, 1.3, 1.3, 1.3])
    r.P('Without the supervisor, the controller trusted the reading and commanded an 8.0 U correction, the IOB limit. Infusion peaked at 230.9 mU/min, and glucose fell to **51.1 mg/dL at t = 273 min**, staying below 70 mg/dL for 114 min. With the supervisor, the 8 U bolus was blocked, true glucose never went below 74.2 mg/dL all day, and TIR stayed at 92.92 %.')
    r.P('The log contains exactly six alarm lines, three detections with three suspensions (Appendix B). Three detailed observations matter:')
    r.N('**One faulted sample passes.** At t = 183 min the second 380 reading is identical to the first, so it neither jumps nor yet meets the stuck count. Basal of 1.85 U/h goes through for one 3 min step (30.9 mU/min). The Python study showed the same behaviour. It is small here because the bolus is locked out, but the detector is one sample late by design.',
        '**Alarm times lag by one step.** Logged times are 183, 189 and 192 min, for samples at t = 180, 186 and 189 min, because the supervisor advances its clock before checking.',
        '**The primary keeps phantom insulin on board.** The supervisor zeroes the bolus, but the wrapped controller has already added 8 U to its own IOB. It therefore allows less correction later: bolus for the day falls from 14.25 to 12.50 U, and the breakfast peak rises from 183.7 to 191.5 mg/dL. A supervisor needs a way to tell the controller what was really delivered; this is a specific improvement.')
    r.P('**Correction to a project record.** `README.md` says unsupervised glucose falls "toward ~75 mg/dL" and lists PID + Supervisor at 89.0 %. The data give 51.1 mg/dL and 88.54 %. The generated `report.html` already shows 88.5 %. This report uses the data. The README statement of about 230 mU/min is correct.')
    r.S('Control Limitations')
    r.P('These results describe one virtual patient on one day with one noise seed, ideal meal announcement and a simplified model. Constants were calibrated on the same scenario on which they were tested, so the numbers show relative behaviour and are not an estimate of performance. The 93.3 % and the Python 99.6 % should not be compared, as the plants differ. No sensitivity sweep or population run was done.')
    r.S('Efficiency')
    r.P('"Efficiency" has two separate meanings in this project, summarised with their evidence level in {tab:eff}.')
    r.tab('Efficiency summary', 'eff', ['Quantity', 'Result', 'Level'], [
        ['Glycaemic gain, predictive over PID', '+4.37 TIR points for +12.4 % insulin (Bergman); +22.1 points for +2.2 % (Python)', 'Simulation'],
        ['Flyback, 100 V Schottky, no snubber (rejected)', '82.4 % at 3.0 V, 86.6 % at 4.2 V', 'Open-loop SPICE'],
        ['Flyback, adopted 10 Oct design with snubber', '**81.7 % at 3.0 V, 84.5 % at 4.2 V**', 'Open-loop SPICE'],
        ['Final design (AONR34332C, HPH6, 330 Ω clamp)', 'Not established. Listed in the project records as bench only', 'None'],
        ['Motor rail input current at 100 mA, 3.0 V', '2.03 A average in the adopted run, against the 2.1 A budget', 'Open-loop SPICE'],
    ], [3, 3, 1])
    r.P('The adopted run gave P~in~ 5.99 to 6.14 W and P~out~ 4.90 to 5.19 W into a 480 Ω load. The losses named in the log are 0.35 to 0.42 W in the clamp and 0.14 to 0.17 W in the snubber. The model uses generic device models, an ideal fixed-duty gate and an assumed 2 % leakage. Output voltage was 48.5 to 49.9 V at fixed duty, and ripple 0.14 V peak to peak.')
    r.P('**A warning about one data set.** The later HPH6 leakage sweep logs "efficiency" up to 143 %. These are not physical. The output had not settled in low-coupling runs, so stored energy distorts the ratio. The project record already says those efficiency values are not meaningful, and they are not used here.')
    r.SS('Indicative battery life (calculation)')
    r.P('E-10 proposes at least 3 days on one cell. Using Rev A budget figures (about 6.2 W motor running, 0.11 W idle), a 2.8 Ah cell at 3.7 V (10.4 Wh), and the BT-01 profile of 39 U/day at 0.11 U/s:')
    r.eq('E~day~ = 0.11 W × 24 h + 6.2 W × (39 U / 0.11 U/s) ≈ 2.64 + 0.61 = 3.25 Wh  ⇒  about 3.2 days', 'batt')
    r.P('This is only a rough check. It ignores 48 V rail rise time for each of the many basal pulses, the bleeder (about 0.1 A input while on), the usable capacity down to 3.4 V, and radio activity. It also uses Rev A figures, and the Rev B cell has not been chosen. Margin against 3 days is therefore not shown.')
    r.S('Power Stage Simulation')
    r.tab('Open-loop runs of the 10 October flyback (LTspice 26.1.1)', 'fb', ['Run', 'Configuration', 'Result', 'Decision'], [
        ['1', '100 V Schottky, 560 Ω/10 nF clamp', 'Vds 22.6 V (90 % of 25 V); diode ringing to 100 V breakdown', 'Rejected'],
        ['2', 'Added 100 Ω/470 pF snubber, 270 to 390 Ω/22 nF clamp', 'Vds 16.7 V, diode 81 to 91 V; snubber 0.5 to 0.63 W; 4.25 A peak at current limit', 'Rejected'],
        ['3', '200 V PNE20010ER, 220 Ω/100 pF, 390 Ω/22 nF', 'Ipk 3.39/2.74 A; Vds 18.5 V (74 %); diode 88 to 97 V (49 %)', 'Adopted, later revised'],
    ], [.5, 2.5, 3, 1])
    r.P('Choosing the real transformer changed the picture, because its leakage is unpublished. {fig:leak} shows the sweep at about 3.1 to 3.4 A. Peak Vds rises with leakage and exceeded 80 % of the 25 V FET then fitted.')
    r.fig(f('leakage_sweep'), 'Peak Q301 voltage against assumed leakage (hph6_leakage.log; indicative, low-coupling runs not fully settled).', 'leak', 5.6)
    r.P('Testing at the true 4.9 A current limit was worse: 26.3 V at 2 % leakage and 45.2 V at 10 %. This led to ECO2: a 30 V FET, 330 Ω/100 nF clamp and an SMAJ15A ceiling, giving 22.8 to 24.4 V, which is 81 % of 30 V. Those figures exclude loop inductance. Adding the estimated 3 to 5 nH loop gives {fig:q301}.')
    r.fig(f('q301_peaks'), 'AONR34332C peak voltage with loop inductance (validation/sim/q301/RESULTS.md). Labels give leakage and loop inductance.', 'q301', 5.8)
    r.P('The worst corner is 28.9 V, or about 29.9 V with the 1 V TVS heating estimate. No corner exceeds 30 V, but every corner exceeds the proposed 80 % derating. **Voltage margin on Q301 is therefore not established.** At 10 % leakage the TVS absorbs about 3 W in this overload condition, and its continuous rating has not been checked.')
    r.SS('Soft start')
    r.P('A cycle-by-cycle model of the datasheet hiccup rule, written for this project and not a vendor model, tested start-up over VIN, COUT, VCLTH and ISS corners.')
    r.tab('Soft-start capacitor study (lm51551_startup.py)', 'ss', ['C~SS~', 'Result'], [
        ['47 nF', 'Fails every corner: repeated hiccup, stuck below 11 V'], ['220 nF', 'Fails every corner'], ['470 nF', 'Mixed, not robust'],
        ['**1 µF**', '**Passes every corner: 91 to 111 ms, 0 hiccups, peak 3.09 A against 4.2 A minimum limit**'],
    ], [1, 5])
    r.P('With a full 100 mA load during start, even 1 µF fails at 3.0 and 3.4 V, so firmware must keep the PMD401 parked until FLY_PGOOD. The loop itself was not simulated, as LTspice has no LM51551 model.')
    r.S('Software Rule Checks')
    r.P('I re-ran ERC and DRC with kicad-cli 10.0.3 on the final files while preparing this report and read both reports. They agree with the saved ones (Appendix B).')
    r.tab('Final software validation', 'val', ['Check', 'Result', 'Note'], [
        ['ERC', '0 errors, 0 warnings', 'Earlier 5 errors were real power pins; closed by PWR_FLAGs on rails fed through a bead, inductor or the SMPS'],
        ['DRC, all severities', '0 violations', 'Was 305 before P6, mostly cosmetic silkscreen'], ['Unconnected', '0', 'From 34 before P6'],
        ['Schematic parity', '0', ''], ['Pad nets against netlist', '493 compared, 0 mismatches', '`p6_netlist_audit.txt`'], ['MCU pin map', '0 failing', 'Functions only, not electrical limits'],
    ], [2, 1.7, 3])
    r.P('Some checks are off: missing courtyard, track not centred on via, tuning geometry, footprint filters and footprint type in DRC; single-use labels, four-way junctions, SPICE model and footprint filters in ERC. On a scratch copy with these enabled, the only findings were 6 footprint-filter notes on deliberate assignments. Three scoped clearance exceptions remain. **A clean report shows the design meets its rules, not that the circuit works.**')
    r.fig(f('routing_convergence'), 'Unconnected pairs through the project. Rises are deliberate: rip-up for placement, and new parts after the ECOs.', 'conv')
    r.S('Validation Status')
    r.tab('Validation levels reached', 'status', ['Item', 'Calculated', 'Simulated', 'Software-checked', 'Built / measured'], [
        ['Control algorithms', 'n/a', 'Yes (module, fixed scenario)', 'n/a', 'No'],
        ['Supervisor logic', 'n/a', 'Yes', 'n/a', 'No on pump hardware'],
        ['ESP32 firmware', 'n/a', 'No log on file', 'n/a', 'No log on file'],
        ['Flyback power stage', 'Yes', 'Open loop only', 'ERC, DRC', 'No'], ['Flyback control loop', 'Preliminary', 'No', 'n/a', 'No'],
        ['Kill path', 'Levels only', 'No', 'Connectivity only', 'No'], ['RF', 'Solver estimate', 'No field simulation', 'DRC', 'No'],
        ['Pump firmware', 'n/a', 'Reference code on simulated plant, code not in this repository', 'n/a', 'No'],
        ['Occlusion detection', 'n/a', 'Assumed plant, simulated', 'n/a', 'No'], ['Dose accuracy', 'Arithmetic', 'Simulated plant only', 'n/a', 'No'],
        ['Integrated system', 'n/a', 'No', 'n/a', '**No**'],
    ], [1.8, 1, 1.8, 1.1, 1])
    r.P('The project records give these reference firmware results on an assumed plant: 40 × 0.05 U gave 19.997 µL of 20 µL; a 5 U bolus gave 49.998 µL; and occlusion alarmed after about 0.21 U into a blocked line at about 773 mmHg. The code (`pump_fw.zip`) lives in a past conversation and not in the project folders, so I could not re-run it; these figures are quoted from `VALIDATION_PLAN.md` only.')
    r.S('Requirements Against Design')
    r.tab('Selected requirements and status', 'req', ['ID', 'Requirement', 'Design response', 'Status'], [
        ['S-01', 'Loss of an MCU or heartbeat ends in safe state', 'R403, R405 pull-ups, R401 pull-down, unpowered motor clamps', 'In design; test pending'],
        ['S-02', 'Enable default off', 'R401 4.7 kΩ, R402 1 kΩ, Q401', 'In design; test pending'],
        ['S-06', 'Runaway limited, speed cap outside main MCU', 'Supervisor counts encoder on TIM3; rate check not written', '**Open (U-03)**'],
        ['S-13', 'Stop at 3.4 V', 'R107/R108 divider to ADC', 'In design; firmware pending'],
        ['E-03', '48 V ±5 % including load step', 'Setpoint 47.43 to 48.58 V; load step not simulated', 'Partly shown'],
        ['E-05', 'Parts above 2.1 A', 'Input about 2.0 to 2.3 A at 3.0 V full speed', '**Marginal (U-24)**'],
        ['E-06', 'Nothing above 80 % of rating (proposed)', 'Q301 peak 86 to 96 %', '**Not met in simulation**'],
        ['E-11', 'Under 60 V fault; under 5 V in 5 s', 'Trip at 50.5 to 53.9 V; 4.21 s calculated', 'Calculated'],
        ['S-08', 'Sensorless occlusion alarm', 'Firmware method; encoder and SPI present', 'Hypothesis unproven'],
        ['P-02', '4 layers, unbroken ground', 'In1 solid GND', 'Met in layout'],
        ['P-07', 'Test point on every rail and safety signal', 'TP101 to TP702 placed', 'Partly reviewed'],
    ], [.6, 2.3, 2.5, 1.2])
    r.S('Failed Attempts and How They Were Diagnosed')
    r.tab('Failures and diagnosis', 'fail', ['Problem', 'How it was found', 'Outcome'], [
        ['Fasting glucose collapsed in pure Bergman model', 'Equation analysis; dG/dt always negative', 'EGP term added'],
        ['False stuck-sensor alarms at steady state', 'Clean-day alarms on noiseless plant', 'Sensor noise added; one PID false alarm remains'],
        ['MPC never finished', 'Code holds a TODO and a placeholder', 'Left unused; future work'],
        ['Rev A gate pull-down failed S-01', 'Reasoned review: dead supervisor gives no veto', 'Pull-up chosen'],
        ['100 V Schottky ringing to breakdown', 'Open-loop SPICE', '200 V diode and snubber'],
        ['47 nF soft start would hiccup', 'Start-up model', 'Raised to 1 µF'],
        ['SMBJ48A clamp inadequate', 'Dynamic resistance: 59.4 V cold, 0.6 V margin', 'Replaced by zener trip'],
        ['CSD16340Q3 margin', 'Clamp study at 4.9 A', 'Changed to 30 V AONR34332C; still open'],
        ['BUK9M20-40H decks', 'Model not traceable; FET stuck on in one deck', 'Excluded as evidence'],
        ['Freerouting ignored limits', 'Routed nets outside stage; 51 passes, no timeout', 'Output discarded; explicit routes and own router'],
        ['Own router keep-outs not applied', 'A route appeared under C518', 'Zero-radius bug fixed; output discarded'],
        ['R312 overlap in applied placement', 'Scratch copy before applying', 'R312 left in place'],
        ['U501 pin 28 had no escape', 'D7 scratch variants A to D, including DRC failure', 'Deferred; resolved in P2 after ST data'],
        ['st.com unreachable; no ST documents', 'Downloads failed', 'WBA55 wiring held as visible ERC errors until ECO1'],
        ['ERC errors not hidden', 'Six then five errors kept open', 'Closed only after evidence'],
    ], [2.6, 2.4, 2.2])


def ch6(r):
    r.chapter('Conclusion and Future Scope', 6)
    r.S('Conclusion')
    r.P('The project carried one engineering idea from simulation to board layout. In simulation, a linear-forecast controller with meal boluses outperformed PID on time in range (93.3 % against 89.0 %) and peak glucose, at the cost of more insulin and a lower minimum. An independent supervisor turned a false sensor reading from a 114 min low reaching 51.1 mg/dL into no low at all, and stayed silent on the predictive clean day. The same analysis found its weaknesses: one faulted sample passes, one false alarm occurs with PID, and suppressed boluses remain in the controller\'s IOB.')
    r.P('On the hardware side, the architecture is recorded with reasons and alternatives, and the Rev B board is complete in KiCad with 0 ERC and DRC violations, 0 unconnected pads and 0 parity differences. Engineering analysis also changed the design materially, including the soft start, rectifier, transformer, switching FET, OVP and RF widths.')
    r.tab('Objectives against achievement', 'obj', ['Objective', 'Outcome'], [
        ['Compare controllers', 'Done in Python and C++'], ['Show supervisor value', 'Done, with limits identified'], ['Same code on desktop and embedded', 'Headers byte-identical; firmware results not on file'],
        ['Select architecture', 'Done, partly unsigned proposals remain'], ['Complete routed board', 'Done, software checks clean'],
        ['Analyse power stage', 'Partly: open-loop only, Q301 margin open'], ['Validation plan and handover', 'Written; plan not run'],
    ], [3, 3.5])
    r.S('Limitations')
    r.B('Nothing in v2 has been built or measured. Module-level simulation and software checks are done; hardware testing and integrated system testing are not.',
        'Control results rest on one patient, day and seed.',
        'The board is **not fabrication-ready** and has no Gerbers. Footprints for BQ25188 and some connectors are unverified, and no fab house or stack-up was chosen.',
        'The LM51551 loop has no model, and no thermal or signal-integrity analysis was done on the final copper.',
        'Pump and supervisor firmware for this board was not written; the rate limit outside the main MCU (S-06) does not exist yet.',
        'The syringe mount and plunger coupling were not designed, and the PMD401 absolute maximum voltage is unknown.')
    r.S('Future Scope')
    r.tab('Specific improvements', 'future', ['Area', 'Improvement', 'Closes'], [
        ['Control', 'Sweep all 30 simglucose virtual patients, then seeds, meal errors and missed announcements', 'Overfitting to adult#003'],
        ['Control', 'Replace linear forecast with MPC; bi-exponential IOB', 'MPC stub; IOB approximation'],
        ['Supervisor', 'Report actual delivery back to the controller', 'Phantom IOB'],
        ['Supervisor', 'Detect a repeated value on its first repeat when jump occurred; widen stuck logic against noise', 'Passed sample, false alarm'],
        ['Power', 'Measure T301 leakage with secondaries shorted; pass ≤ 2 %, re-select above 4 %', 'Q301 margin'],
        ['Power', 'Consider SMAJ13A and 24 mΩ option; fit R316, R317 and C314 on bench', 'Q301 margin'],
        ['Power', 'Use TI model or bench Bode for loop; do load step', 'E-03, compensation'],
        ['Vendor', 'Send prepared PMD401 question on maximum voltage and logic rail', 'PMD401 protection'],
        ['Safety', 'Write C031 rate check using its own encoder count, then FT-02', 'S-06, U-03'],
        ['Board', 'Choose fab and stack-up, confirm RF widths; verify footprints; thermal check', 'U-12, U-16, U-17, U-19, U-20'],
        ['Test', 'Run the 13 bench groups in order, kill path first, weighed dose accuracy as the gate', 'All measurement gaps'],
        ['Novelty', 'Measure step length against load (MT-05) to test occlusion idea', 'Main technical bet'],
    ], [1, 3.8, 2])


def refs(r):
    r.chapter('References')
    items = [
        'R. N. Bergman, Y. Z. Ider, C. R. Bowden, and C. Cobelli, "Quantitative estimation of insulin sensitivity," Am. J. Physiol., vol. 236, no. 6, pp. E667-E677, 1979.',
        'C. Dalla Man, F. Micheletto, D. Lv, M. Breton, B. Kovatchev, and C. Cobelli, "The UVA/PADOVA type 1 diabetes simulator: new features," J. Diabetes Sci. Technol., vol. 8, no. 1, pp. 26-34, 2014.',
        'J. Xie, "simglucose: a Type-1 diabetes simulator implemented in Python," 2018. [Online]. Available: https://github.com/jxx123/simglucose',
        'B. P. Kovatchev, D. J. Cox, L. A. Gonder-Frederick, and W. Clarke, "Symmetrization of the blood glucose measurement scale and its applications," Diabetes Care, vol. 20, no. 11, pp. 1655-1658, 1997.',
        'S. A. Brown et al., "Six-month randomized, multicenter trial of closed-loop control in type 1 diabetes," N. Engl. J. Med., vol. 381, no. 18, pp. 1707-1717, 2019.',
        'T. Battelino et al., "Clinical targets for continuous glucose monitoring data interpretation," Diabetes Care, vol. 42, no. 8, pp. 1593-1603, 2019.',
        'Kaçar, Özer, and Taşçıoğlu, paper on a piezoelectric valveless micropump with PID control on a Bergman plant, ICAT\'19, 2019. [[Complete title and pages from your copy]]',
        'Texas Instruments, "LM5155x, LM5156x boost/flyback controller," SNVSB75E, Aug. 2023 (`docs/datasheets/lm51551.pdf`). [[Confirm exact title]]',
        'Texas Instruments, BQ25188 datasheet, SLUSFJ3, Nov. 2024; TPS62840 datasheet, SLVSEC6D, Mar. 2020 (`docs/datasheets`).',
        'PiezoMotor, PMD401 Technical Manual, doc. 150025-01 (`docs/datasheets/PMD401_150025_Technical_Manual.pdf`); LL06 product data.',
        'STMicroelectronics, STM32WBA5xxx datasheet DS14127; reference manual RM0493; errata ES0592; application notes AN5948 and AN6373; MLPF-WB-04D3 datasheet DS14446.',
        'Coilcraft, HP/HPH series, Doc 613, rev. 11/23/21.',
        'Alpha and Omega Semiconductor, AONR34332C datasheet; Nexperia, PNE20010ER, PMEG10020ELR, BSS138 and PESD5V0S1BA data (`docs/datasheets`).',
        'KiCad EDA 10.0.3, kicad.org; Analog Devices LTspice 26.1.1; Freerouting 2.1.0; STMicroelectronics STM32CubeMX 6.18.1 database.',
        'IEC 60601-2-24:2012, Medical electrical equipment, Part 2-24: particular requirements for infusion pumps and controllers.',
        'AAMI TIR101, Fluid delivery performance testing for infusion pumps.',
        'ISO 14971:2019, Medical devices: application of risk management to medical devices.',
        'IEC 62304:2006+A1:2015, Medical device software: software life cycle processes.',
        'IPC-2221C (2023), Generic standard on printed board design; IPC-2152, Standard for determining current-carrying capacity in printed board design.',
    ]
    for i, t in enumerate(items, 1):
        p = r.d.add_paragraph(style='Refs')
        p.paragraph_format.left_indent = Inches(.4)
        p.paragraph_format.first_line_indent = Inches(-.4)
        r.rich(p, f'[{i}]  {t}', size=11)


def code_app(r, title, path):
    r.rec_h(title, 1)
    r.code(rd(path))


def app_section(r, letter, title):
    h = r.d.add_heading(level=1)
    h.paragraph_format.page_break_before = True
    h.add_run(f'Appendix {letter}: {title}')
    r.ch = letter
    r.nf = r.nt = r.ne = 0


def sub(r, t):
    r.d.add_heading(t, level=2)


def appendices(r):
    app_section(r, 'A', 'HybridPancreasSim Source Code')
    r.P('Complete source as on disk in `D:\\HybridPancreasSim\\HybridPancreasSim`. `Controllers.h` and `BergmanModel.h` are byte-identical in `desktop/` and `esp32/`, so each is listed once.')
    for t, p in (('A.1 BergmanModel.h', 'desktop/BergmanModel.h'), ('A.2 Controllers.h', 'desktop/Controllers.h'), ('A.3 main.cpp', 'desktop/main.cpp'),
                 ('A.4 esp32/sketch.ino', 'esp32/sketch.ino'), ('A.5 esp32/diagram.json', 'esp32/diagram.json'), ('A.6 esp32/libraries.txt', 'esp32/libraries.txt')):
        sub(r, t)
        r.code(rd(SIM, *p.split('/')))
    sub(r, 'A.7 Project README')
    r.P('Reproduced as written. Two statements are corrected by the data; see Section 5.4.')
    r.md(os.path.join(SIM, 'README.md'))

    app_section(r, 'B', 'Earlier Code and Run Reports')
    sub(r, 'B.1 PancreasSim, first C++ simulator')
    for t in ('BergmanModel.h', 'Controllers.h', 'main.cpp', 'plot.py'):
        r.rec_h(t, 2)
        r.code(rd(PSIM, t))
    sub(r, 'B.2 Python study, insulin_pump_sim')
    for t in ('controllers/pid_controller.py', 'controllers/predictive_controller.py', 'controllers/safety_supervisor.py', 'run_simulation.py', 'evaluate.py', 'fault_injection_demo.py'):
        r.rec_h(t, 2)
        r.code(rd(PY, *t.split('/')))
    r.rec_h('Python project README', 2)
    r.md(os.path.join(PY, 'README.md'))
    sub(r, 'B.3 HybridPancreasSim console output (re-run, 1 November 2026)')
    r.code('adult#003 basal: 1.4253 U/hr\nPID          TIR=89.0%  <70=0.0%  >180=11.0%  mean=128\nPredictive   TIR=93.3%  <70=0.0%  >180=6.7%  mean=114\nPred+Superv  TIR=93.3%  <70=0.0%  >180=6.7%  mean=114\nFault run: 6 supervisor alarms logged\nWrote results/*.csv and results/report.html')
    sub(r, 'B.4 Supervisor alarm logs')
    r.P('Produced by a scratch driver that includes `main.cpp` unchanged and prints each supervised run\'s log. The fourth run (PID with the same fault) was added for this report.')
    r.code(open(ALARMS, encoding='utf-8').read())
    sub(r, 'B.5 Generated report.html (preview image)')
    r.fig(os.path.join(SIM, 'results', 'report_preview.png'), 'Output page generated by main.cpp, saved preview image. Its table matches the Chapter 5 values.', 'html', 3.9)
    sub(r, 'B.6 Half-hourly glucose traces')
    r.P('Full 3 min traces are in `desktop/results/*.csv`. True glucose in mg/dL:')
    names = ['pid_only', 'pid_supervised', 'predictive_only', 'predictive_supervised', 'fault_unsupervised', 'fault_supervised']
    D = {n: list(csv.DictReader(open(os.path.join(SIM, 'desktop', 'results', n + '.csv')))) for n in names}
    rows = [[f'{i * 30 / 60:.1f}'] + [f"{float(D[n][i * 10]['true_bg']):.1f}" for n in names] for i in range(48)]
    r._grid(['Hour', 'PID', 'PID+Sup', 'Pred', 'Pred+Sup', 'Fault', 'Fault+Sup'], rows, [1] * 7, 'SmallCell')
    sub(r, 'B.7 ERC report (validation/erc/pump_v2-erc.rpt)')
    r.code(rd(REPO, 'validation', 'erc', 'pump_v2-erc.rpt'))
    sub(r, 'B.8 DRC report (validation/drc/pump_v2-drc.rpt)')
    r.code(rd(REPO, 'validation', 'drc', 'pump_v2-drc.rpt'))
    sub(r, 'B.9 Netlist audit (validation/logs/p6_netlist_audit.txt)')
    r.code(rd(REPO, 'validation', 'logs', 'p6_netlist_audit.txt'))
    sub(r, 'B.10 Open-loop flyback LTspice log')
    r.code(rd(REPO, 'validation', 'sim', 'flyback_openloop.log'))
    sub(r, 'B.11 HPH6 leakage sweep LTspice log')
    r.P('Efficiency lines in this log are not meaningful for the reason given in Section 5.6.')
    r.code(rd(REPO, 'validation', 'sim', 'hph6_leakage.log'))
    sub(r, 'B.12 Q301 simulation results')
    r.md(os.path.join(REPO, 'validation', 'sim', 'q301', 'RESULTS.md'))

    records = [
        ('C', 'Requirements and Constraints', [('Design requirements', 'requirements/DESIGN_REQUIREMENTS.md'), ('Hardware constraints', 'requirements/HARDWARE_CONSTRAINTS.md'), ('Project overview (10 October handoff)', 'PROJECT_OVERVIEW.md')]),
        ('D', 'Decision Log and Validation Plan', [('Decision log', 'decisions/DECISION_LOG.md'), ('Validation plan', 'requirements/VALIDATION_PLAN.md')]),
        ('E', 'Components and Bill of Materials', [('Components and Rev A list', 'requirements/COMPONENTS_AND_BOM.md'), ('BOM export differences', 'docs/handover/BOM_REEXPORT_DIFF.md')]),
        ('F', 'Power Design and Schematic Change Records', [('Flyback design', 'docs/handover/FLYBACK_DESIGN.md'), ('ECO1 and ECO2', 'docs/handover/ECO1_SCHEMATIC.md')]),
        ('G', 'Placement and Routing Records', [('Blocker resolution', 'docs/handover/BLOCKER_RESOLUTION_REPORT.md'), ('Placement proposal', 'docs/handover/PLACEMENT_PROPOSAL.md'), ('Routing stages', 'docs/handover/ROUTING_STAGES.md'), ('PCB stages', 'docs/handover/PCB_STAGES.md'), ('Status during routing', 'docs/handover/CURRENT_STATUS.md')]),
        ('H', 'Open Issues and Handover Records', [('Unresolved issues', 'docs/handover/UNRESOLVED_ISSUES.md'), ('Open questions', 'requirements/OPEN_QUESTIONS.md'), ('Assumptions and deviations', 'docs/handover/ASSUMPTIONS_AND_DEVIATIONS.md'), ('Handover guide', 'docs/handover/HANDOVER_GUIDE.md'), ('Final handover', 'docs/handover/FINAL_HANDOVER.md'), ('Source documents', 'docs/SOURCE_DOCUMENTS.md'), ('Pin map check', 'validation/logs/pinmap_check.md')]),
    ]
    for L, title, docs in records:
        app_section(r, L, title)
        r.P('The following are the project\'s own records, reproduced so that nothing is lost. They were written at the dates they carry, so earlier sections can be superseded by later ones. Where they differ from Chapters 4 and 5, the final state in Chapters 4 and 5 applies.')
        for i, (t, p) in enumerate(docs, 1):
            sub(r, f'{L}.{i} {t}')
            r.md(os.path.join(REPO, *p.split('/')))
        if L == 'E':
            sub(r, 'E.3 Rev B BOM, per reference (docs/bom_detailed.csv)')
            r.csv_table(os.path.join(REPO, 'docs', 'bom_detailed.csv'), ['Ref', 'Value', 'MPN', 'Status', 'DNP', 'Note / source'], [.7, 1, 1.3, .7, .4, 3])

    app_section(r, 'I', 'Repository History')
    r.P('Full commit list from `git log` on branch `placement-opt`, oldest first, followed by recovery tags.')
    g = subprocess.check_output(['git', '-C', REPO, 'log', '--reverse', '--format=%h %ad %s', '--date=short'], text=True, encoding='utf-8')
    r.code(g)
    r.rec_h('Tags', 2)
    r.code(subprocess.check_output(['git', '-C', REPO, 'tag'], text=True, encoding='utf-8'))


def build(labels):
    r = Rep(labels)
    front(r)
    sec = r.d.add_section(WD_SECTION.NEW_PAGE)
    ch1(r)
    ch2(r)
    ch3(r)
    ch4(r)
    sch_pages(r)
    ch5(r)
    ch6(r)
    refs(r)
    appendices(r)
    secs = r.d.sections
    r.footer_num(secs[0], 'lowerRoman', 1)
    r.footer_num(secs[1], 'decimal', 1)
    for s in secs[2:]:
        pg = s._sectPr.find(qn('w:pgNumType'))
        if pg is not None:
            s._sectPr.remove(pg)
        s.footer.is_linked_to_previous = True
    # the title page carries no number
    secs[0].different_first_page_header_footer = True
    return r


if __name__ == '__main__':
    a = build({})
    b = build(a.new)
    cp = b.d.core_properties
    cp.title, cp.author = 'Closed-Loop Insulin Delivery: Project Report', 'B Charan'
    b.d.save(os.path.join(HERE, 'Project_Report.docx'))
    print('saved', len(b.new), 'labels')
