"""Piezo Insulin Pump v2 - Rev B handover design: circuit definition (single source of truth).

BENCH-ONLY PROTOTYPE. Water / 0.9 % saline only. Never connect to a person or an animal.
NOT fabrication-approved. Many values are TBD or PLACEHOLDER; see docs/handover/.

Status field vocabulary (also used in the BOM):
  DECIDED      locked in the handoff documents (K-xx / Rev A design)
  DS           value or connection taken from the cited official datasheet
  CALC         calculated from datasheet parameters (calculation in the Note field)
  ASSUMED      engineering assumption, listed in docs/handover/ASSUMPTIONS.md
  TBD          part / value not yet determined; footprint is a sized guess
  PLACEHOLDER  circuit block not designed; present only to reserve topology/space
Pin assignments on both MCUs are DERIVED from the ST pin database as packaged in the
KiCad 10 symbol libraries (alternate-function lists). They must be confirmed in
STM32CubeMX against the ST datasheets before layout freeze.
"""

FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_R1206 = "Resistor_SMD:R_1206_3216Metric"
FP_R2512 = "Resistor_SMD:R_2512_6332Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_C1210 = "Capacitor_SMD:C_1210_3225Metric"
FP_C0402 = "Capacitor_SMD:C_0402_1005Metric"
FP_C0402_L = "Inductor_SMD:L_0402_1005Metric"
FP_TVS = "Diode_SMD:D_SOD-323"
FP_LED = "LED_SMD:LED_0603_1608Metric"
FP_SWD = "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical"


class Part:
    def __init__(self, ref, lib_id, value, nets, footprint=None, status="DS", mpn="", note="",
                 dnp=False, nc=()):
        self.ref, self.lib_id, self.value = ref, lib_id, value
        self.nets = dict(nets)          # pin number -> net name
        self.footprint = footprint
        self.status, self.mpn, self.note = status, mpn, note
        self.dnp = dnp
        self.nc = list(nc)              # pin numbers that get a no-connect flag


class Sheet:
    def __init__(self, name, file, title):
        self.name, self.file, self.title = name, file, title
        self.parts = []
        self.notes = []

    def add(self, *a, **k):
        p = Part(*a, **k)
        self.parts.append(p)
        return p


def R(s, ref, value, n1, n2, fp=FP_R, **k):
    return s.add(ref, "Device:R", value, {"1": n1, "2": n2}, fp, **k)


def C(s, ref, value, n1, n2, fp=FP_C, **k):
    return s.add(ref, "Device:C", value, {"1": n1, "2": n2}, fp, **k)


def CP(s, ref, value, pos, neg, fp, **k):
    return s.add(ref, "Device:C_Polarized", value, {"1": pos, "2": neg}, fp, **k)


def L(s, ref, value, n1, n2, fp, **k):
    return s.add(ref, "Device:L", value, {"1": n1, "2": n2}, fp, **k)


def TVS(s, ref, net, **k):
    k.setdefault("status", "TBD")
    k.setdefault("note", "E-07: TVS on every PMD401 signal. Working voltage >=5 V class, low capacitance; part TBD (OPEN B.15)")
    return s.add(ref, "Device:D_TVS", "TVS_5V_TBD", {"1": net, "2": "GND"}, FP_TVS, **k)


def TP(s, ref, net):
    return s.add(ref, "Connector:TestPoint", net, {"1": net}, "TestPoint:TestPoint_Pad_D1.0mm",
                 status="ASSUMED", note="Test point (P-07 proposed; added for bring-up access)")


def FLAG(s, ref, net):
    return s.add(ref, "power:PWR_FLAG", "PWR_FLAG", {"1": net}, None, status="DS",
                 note="ERC power-source marker for a net fed from a connector or inductor")


def SWD(s, ref, pfx, swo):
    nets = {"1": "+3V3", "2": pfx + "_SWDIO", "3": "GND", "4": pfx + "_SWCLK", "5": "GND",
            "9": "GND", "10": pfx + "_NRST"}
    nc = ["7", "8"]
    if swo:
        nets["6"] = pfx + "_SWO"
    else:
        nc.append("6")
    return s.add(ref, "Connector:Conn_ARM_JTAG_SWD_10", "SWD_10pin", nets, FP_SWD, status="ASSUMED",
                 note="ARM Cortex 10-pin 1.27 mm SWD header (connector type OPEN B.26)", nc=nc)


def build():
    sheets = []

    # ===================================================================== 1
    s = Sheet("Power input & charger", "power_input.kicad_sch", "Battery input, fuse, master switch, BQ25188 charger")
    sheets.append(s)
    s.notes.append("Battery path (E-01 DECIDED): 1S protected cell -> J101 -> F101 5 A fuse -> J102 master switch -> VBAT.\n"
                   "Charger (K-12 BQ25188) charges the cell on VBAT_FUSED. E-09: the charger is NEVER the load path:\n"
                   "BQ25188 SYS (CHG_SYS) has only its required 10 uF and no load. Charge current set over I2C (OPEN B.19).\n"
                   "Cell protection is inside the pack (K-12 '1S protected cell'). Cell size/connector OPEN B.20.")
    s.add("J101", "Connector_Generic:Conn_01x02", "BATTERY_1S", {"1": "VBAT_RAW", "2": "GND"},
          "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal", status="ASSUMED", mpn="AMASS XT30PW-M",
          note="XT30 carried from Rev A item 32; Rev B battery connector OPEN B.20. VERIFY pad polarity vs footprint before use")
    s.add("F101", "Device:Fuse", "5A", {"1": "VBAT_RAW", "2": "VBAT_FUSED"}, "Fuse:Fuse_2920_7451Metric",
          status="TBD", note="E-01 5 A fuse DECIDED; SMD part, voltage and breaking-capacity rating TBD")
    s.add("J102", "Connector_Generic:Conn_01x02", "MASTER_SW_EXT", {"1": "VBAT_FUSED", "2": "VBAT"},
          "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
          status="ASSUMED", note="E-01 master switch DECIDED; off-board toggle >=5 A DC wired to this terminal (Rev A item 17)")
    s.add("U101", "pump_v2:BQ25188", "BQ25188YBGR",
          {"A2": "VBUS_CHG", "B1": "I2C_SCL", "C1": "I2C_SDA", "A1": "CHG_INT_N", "D1": "CHG_TS",
           "B2": "CHG_SYS", "C2": "VBAT_FUSED", "D2": "GND"},
          status="DECIDED", mpn="BQ25188YBGR", note="K-12. Pinout SLUSFJ3 Table 5-1. Register defaults (SLUSFJ3 7.5): VBATREG code 70 -> 4.20 V (meets E-09); "
               "ICHG code 5 -> 10 mA (firmware must set charge current, OPEN B.19); I2C watchdog ON by default and resets "
               "registers on expiry. Footprint pitch UNVERIFIED (see footprint descr)")
    C(s, "C101", "2.2uF/25V", "VBUS_CHG", "GND", FP_C0805, status="DS",
      note="IN: >=1 uF effective after DC bias (SLUSFJ3 Table 5-1); 25 V for 5 V USB + margin")
    C(s, "C102", "1uF/10V", "VBAT_FUSED", "GND", status="DS", note="BAT: >=1 uF ceramic (SLUSFJ3 Table 5-1)")
    C(s, "C103", "10uF/10V", "CHG_SYS", "GND", FP_C0805, status="DS", note="SYS: >=10 uF ceramic (SLUSFJ3 Table 5-1); SYS otherwise unloaded (E-09)")
    R(s, "R101", "10k", "CHG_TS", "GND", status="DS",
      note="SLUSFJ3: 'For devices where the TS function is not needed, tie a 10-k resistor to the TS/MR pin.' "
           "10k x ITSMR 38 uA = 0.38 V >> VTSMR 90 mV button threshold, so no false ship-mode press. "
           "Replace with the pack NTC if the cell has one (OPEN B.20)")
    s.add("J103", "Connector:USB_C_Receptacle_PowerOnly_6P", "USB_C_PWR",
          {"A9": "VBUS_CHG", "B9": "VBUS_CHG", "A5": "USB_CC1", "B5": "USB_CC2", "A12": "GND", "B12": "GND", "SH": "GND"},
          "Connector_USB:USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal", status="ASSUMED", mpn="GCT USB4125",
          note="Charger input connector OPEN B.19; USB-C power-only sink assumed")
    R(s, "R102", "5.1k", "USB_CC1", "GND", status="ASSUMED", note="USB-C sink Rd on CC1 (USB Type-C spec value)")
    R(s, "R103", "5.1k", "USB_CC2", "GND", status="ASSUMED", note="USB-C sink Rd on CC2 (USB Type-C spec value)")
    R(s, "R104", "10k", "I2C_SCL", "+3V3", status="DS", note="SCL pull-up to logic rail, 10k per SLUSFJ3 Table 5-1")
    R(s, "R105", "10k", "I2C_SDA", "+3V3", status="DS", note="SDA pull-up to logic rail, 10k per SLUSFJ3 Table 5-1")
    R(s, "R106", "10k", "CHG_INT_N", "+3V3", status="DS", note="/INT open drain, 1-20k pull-up allowed (SLUSFJ3)")
    R(s, "R107", "200k 1%", "VBAT", "VBAT_SENSE", status="CALC",
      note="ECO1. S-13 VBAT sense (INA219 dropped; BQ25188 has no ADC). Ratio 1/2: 4.2 V -> 2.1 V. Drain ~10.5 uA at 4.2 V. "
           "DS14127 Table 76 Ilkg 150 nA max x 100k source = 15 mV at the pin, 30 mV at VBAT (was 150 mV with 1M/1M). "
           "Firmware must use VREFINT (VDDA follows VBAT in buck dropout)")
    R(s, "R108", "200k 1%", "VBAT_SENSE", "GND", status="CALC", note="see R107")
    C(s, "C104", "100nF", "VBAT_SENSE", "GND", status="CALC",
      note="Charge reservoir for ADC sampling from the 100k source (tau 10 ms)")
    FLAG(s, "#FLG101", "GND")
    FLAG(s, "#FLG102", "VBAT")
    FLAG(s, "#FLG103", "VBUS_CHG")
    TP(s, "TP101", "VBAT")
    TP(s, "TP102", "GND")

    # ===================================================================== 2
    s = Sheet("3V3 buck", "power_3v3.kicad_sch", "TPS62840 3.3 V logic rail")
    sheets.append(s)
    s.notes.append("K-12: TPS62840 for 3.3 V on Rev B. Taken from VBAT (not from the 48 V chain), as decided for Rev A.\n"
                   "Below about 3.4 V in, the buck runs in 100 % mode and 3V3 follows VBAT (E-02 >=3.0 V while dosing; S-13 3.4 V stop).\n"
                   "Note CF-8: E-02 wording says 'LDO' (Rev A); Rev B uses the decided TPS62840 buck.")
    s.add("U201", "pump_v2:TPS62840DLC", "TPS62840DLCR",
          {"2": "VBAT", "4": "VBAT", "3": "GND", "6": "GND", "5": "BUCK_VSET", "7": "BUCK_SW", "8": "+3V3", "1": "GND"},
          status="DECIDED", mpn="TPS62840DLCR",
          note="K-12. DLC (SON-8) variant ASSUMED (orderable variant OPEN B.12). EN tied to VIN, MODE=GND (auto PFM/PWM), STOP=GND")
    R(s, "R201", "267k 1%", "BUCK_VSET", "GND", status="DS", note="VSET -> 3.3 V for TPS62840DLC (SLVSEC6D VSET table, E96 nominal)")
    L(s, "L201", "2.2uH", "BUCK_SW", "+3V3", "Inductor_SMD:L_Murata_DFE201610P", status="DS", mpn="Murata DFE201612E-2R2M=P2",
      note="ECO1. SLVSEC6D Table 4 lists 2.0 x 1.6 mm DFE201612E; the old 0603 footprint could not fit it. Footprint is KiCad's Murata 2016 pattern; check land against the Murata drawing")
    C(s, "C201", "4.7uF/10V", "VBAT", "GND", status="DS", note="CIN 4.7 uF required (SLVSEC6D pin table)")
    C(s, "C202", "10uF/10V", "+3V3", "GND", FP_C0805, status="DS", note="COUT 10 uF (SLVSEC6D typical application)")
    FLAG(s, "#FLG201", "+3V3")
    TP(s, "TP201", "+3V3")

    # ===================================================================== 3
    s = Sheet("48V flyback", "power_48v.kicad_sch", "LM51551 non-isolated flyback, 48 V motor rail")
    sheets.append(s)
    s.notes.append("K-12 / DECIDED 29 Sep: Rev B 48 V stage is an LM51551 flyback (plain boost hits the 93 % duty limit).\n"
                   "Topology follows TI SNVSB75E Figure 10-12 'Typical Non-Isolated Flyback'; BIAS tied to VCC for 1S start (>=2.97 V).\n"
                   "Design calculations: docs/handover/FLYBACK_DESIGN.md (fsw ~300 kHz, n = Ns/Np = 5, Lp ~7 uH, Ipk ~3.1 A at 3.0 V / 100 mA).\n"
                   "T301 = Coilcraft HPH6-0090L: pri 3-10, sec = 5 windings in series. Leakage is NOT published: clamp and snubber values need bench tuning.\n"
                   "Compensation values are PRELIMINARY (depend on T301 and the PMD401 cable/bulk capacitance) - simulate/bench before use.\n"
                   "Kill path: UVLO/EN driven by FLY_EN (sheet 'Kill path'). EN < 0.4 V min (SNVSB75E) = shutdown. A flyback has no DC path\n"
                   "from VBAT to the output, so EN low de-energises the rail. ECO1 (owner approved architecture): no output switch; rail control is EN; R312 bleeder and D303 clamp fitted.\n"
                   "E-06: every 48 V capacitor rated >= 100 V. E-03: 45.6-50.4 V at the PMD401.")
    CP(s, "C301", "220uF/16V", "VBAT", "GND", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm", status="DECIDED",
       note="Bulk at converter input, carried from Rev A item 25 (220 uF/16 V low-ESR); adequacy for flyback TBD")
    C(s, "C302", "10uF/10V X5R", "VBAT", "GND", FP_C0805, status="CALC",
      note="Input ceramic. Primary ripple ~1.1 A rms at 3.0 V (FLYBACK_DESIGN.md); 2 x 10 uF; check part ripple rating")
    C(s, "C303", "10uF/10V X5R", "VBAT", "GND", FP_C0805, status="CALC", note="see C302")
    s.add("U301", "pump_v2:LM51551", "LM51551DSSR",
          {"1": "VBAT", "2": "VBAT", "12": "FLY_EN", "10": "FLY_RT", "9": "FLY_SS", "11": "FLY_PGOOD",
           "3": "FLY_GATE", "5": "FLY_CS", "8": "FLY_FB", "6": "FLY_COMP", "4": "GND", "7": "GND", "13": "GND"},
          status="DECIDED", mpn="LM51551DSSR",
          note="K-12. Pinout SNVSB75E Table 7-1. BIAS=VCC (SNVSB75E sec.1: 2.97-16 V). UVLO/EN max = VBIAS+0.3 V; FLY_EN <= 0.82 x 3V3 <= VBAT")
    C(s, "C304", "2.2uF/10V", "VBAT", "GND", status="DS",
      note="VCC/BIAS bypass to PGND: SNVSB75E 'recommended VCC capacitor value is from 1 uF to 4.7 uF'")
    R(s, "R301", "73.2k 1%", "FLY_RT", "GND", status="CALC",
      note="RT = 2.21e10/fsw - 955 (SNVSB75E Eq.5): 73.2k -> fsw = 298 kHz (+/-15 %). DMAX >= ~90 % at this fsw (Fig 8-16)")
    C(s, "C305", "1uF/10V X7R", "FLY_SS", "GND", status="CALC",
      note="ECO1. tSS = 1 uF x 1 V / 9-11 uA = 91-111 ms. 47 nF would trip the LM51551 64-cycle hiccup while charging ~150 uF (validation/sim/lm51551_startup.py). PMD401 must stay parked until FLY_PGOOD")
    R(s, "R302", "100k", "FLY_PGOOD", "+3V3", status="ASSUMED", note="PGOOD open-drain pull-up to 3V3 (<= VBIAS)")
    R(s, "R303", "3.01k 1%", "FLY_COMP", "FLY_COMP_RC", status="CALC",
      note="PRELIMINARY type-II compensation for fc ~3 kHz < fRHPZ/5 (FLYBACK_DESIGN.md). Depends on T301 Lp and output capacitance")
    C(s, "C306", "180nF", "FLY_COMP_RC", "GND", status="CALC", note="PRELIMINARY: compensation zero ~300 Hz (FLYBACK_DESIGN.md)")
    C(s, "C307", "3.3nF", "FLY_COMP", "GND", status="CALC", note="PRELIMINARY: HF pole ~16 kHz (FLYBACK_DESIGN.md)")
    s.add("Q301", "pump_v2:CSD16340Q3", "AONR34332C", {"4": "FLY_GATE", "5": "FLY_SW", "1": "FLY_CS", "2": "FLY_CS", "3": "FLY_CS"},
          "Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET", status="DS", mpn="AOS AONR34332C",
          note="ECO2. 30 V, RDS(on) < 2.9 mohm at VGS 2.5 V, VGS(th) 0.5-1.2 V, Qg(4.5 V) 36 nC, pins 1-3 S, 4 G, 5-8 D (AOS datasheet Rev 2.0). "
               "Replaces the 25 V CSD16340Q3: Vds reaches 26-33 V at the 4.9 A limit without the D304 ceiling. Check land against the AOS outline")
    R(s, "R305", "22m 1% 1W", "FLY_CS", "GND", FP_R2512, status="CALC",
      note="Ilim = VCLTH/Rs = 93..107 mV / 22 mohm = 4.2..4.9 A (SNVSB75E). Peak at 3.0 V / 100 mA ~3.1 A. P ~0.12 W (Irms ~2.3 A)")
    s.add("T301", "pump_v2:HPH6-0090L", "HPH6-0090L",
          {"3": "VBAT", "10": "FLY_SW",
           "1": "GND", "12": "FLY_SEC_A", "2": "FLY_SEC_A", "11": "FLY_SEC_B", "4": "FLY_SEC_B",
           "9": "FLY_SEC_C", "5": "FLY_SEC_C", "8": "FLY_SEC_D", "6": "FLY_SEC_D", "7": "FLY_SEC"},
          status="DS", mpn="Coilcraft HPH6-0090L",
          note="ECO1. Coilcraft Doc 613: 7.29 uH +/-5 % per winding, 0.030 ohm, 131.9 V-us, Isat 4.60 A x 6 / 1 = 27.6 A on one winding, Irms 2.90 A, 500 Vrms between windings. "
               "Pri = middle winding 3(dot)-10. Sec = 1(dot)-12, 2-11, 4-9, 5-8, 6-7 in series, dots aiding, n = 5, dot at GND. "
               "Leakage NOT published: measure with sec shorted. Doc 613 restricts medical use without Coilcraft approval (this is a bench prototype)")
    s.add("D301", "Device:D", "PNE20010ER", {"2": "FLY_SEC", "1": "+48V_RAW"}, "Diode_SMD:Nexperia_CFP3_SOD-123W",
          status="DS", mpn="Nexperia PNE20010ER",
          note="200 V / 1 A hyperfast (trr 25 ns) rectifier, Nexperia datasheet in docs/datasheets. Steady-state VR = 48 + 5 x 4.2 = 69 V, "
               "but open-loop simulation (validation/sim) shows leakage ringing: 200 V breakdown without snubber, 88-97 V with "
               "R313/C312 (49 % of rating). A 100 V Schottky was rejected for this reason. Avg 0.1 A, peak ~0.7 A")
    R(s, "R313", "220R 1206", "FLY_SEC", "FLY_SNUB", FP_R1206, status="CALC",
      note="D301 RC snubber (sim run 3): 0.14-0.17 W at 100 mA -> 1206 >= 0.25 W. Value depends on real T301 leakage: re-tune on bench")
    C(s, "C312", "100pF/250V C0G", "FLY_SNUB", "+48V_RAW", "Capacitor_SMD:C_1206_3216Metric", status="CALC",
      note="D301 RC snubber capacitor; sees ~100 V peak -> 250 V C0G")
    s.add("D302", "Device:D_Schottky", "PMEG10020ELR", {"2": "FLY_SW", "1": "FLY_CLAMP"}, "Diode_SMD:Nexperia_CFP3_SOD-123W",
          status="DS", mpn="Nexperia PMEG10020ELR",
          note="RCD clamp diode (100 V/2 A Schottky; sees ~18.5 V). Clamp values R306/C308 from sim run 3")
    R(s, "R306", "330R 1W", "FLY_CLAMP", "VBAT", FP_R2512, status="CALC",
      note="ECO2. RCD clamp (validation/sim/flyback_clamp_final_330.log): 0.54 W at 2 % leakage, 0.83 W at 4 %. Bench-tune with the real T301")
    C(s, "C308", "100nF/50V X7R", "FLY_CLAMP", "VBAT", FP_C0805, status="CALC", note="ECO2. Larger than 22 nF: cuts clamp ripple and Vds by several volts")
    s.add("D304", "Device:D_Zener", "SMAJ15A", {"1": "FLY_CLAMP", "2": "VBAT"}, "Diode_SMD:D_SMA", status="CALC", mpn="Littelfuse SMAJ15A",
          note="ECO2. Vds ceiling across the clamp: Vds <= 24.4 V (81 % of 30 V) up to 10 % leakage at the 4.9 A limit in simulation. VBR 16.7-18.5 V; conducting steadily means leakage is too high")
    C(s, "C309", "2.2uF/100V X7R", "+48V_RAW", "GND", FP_C1210, status="CALC",
      note="Ripple: dV = Iout x D / (fsw x C) -> needs >= 1.1 uF effective at 48 V for 0.24 V; 2 parts allow ~60 % DC-bias loss. E-06 >= 100 V")
    C(s, "C310", "2.2uF/100V X7R", "+48V_RAW", "GND", FP_C1210, status="CALC", note="see C309")
    CP(s, "C311", "47uF/100V", "+48V_RAW", "GND", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", status="DECIDED",
       note="47 uF/100 V carried from Rev A item 23 (DC2628A output). Series/size TBD")
    R(s, "R307", "470k 0.1%", "+48V_RAW", "FLY_FB", status="CALC",
      note="ECO1. Vout = 1.0 V x (1 + 470k/10k) = 48.0 V; VREF +/-1 % + 0.1 % resistors = 47.43-48.58 V, inside E-03 45.6-50.4 V")
    R(s, "R308", "10k 0.1%", "FLY_FB", "GND", status="CALC", note="see R307")
    # --- ECO1: K-12 switched-output placeholders Q302/Q303/R309/R310 deleted; EN is the rail control
    R(s, "R311", "0R", "+48V_RAW", "+48V_MOT", FP_R1206, status="ASSUMED",
      note="Link between the converter output and the PMD401 rail; lift for bench isolation of the load")
    R(s, "R312", "10k 1% 1W", "+48V_RAW", "GND", FP_R2512, status="CALC",
      note="ECO2. E-11: 50.4 V to 5 V in 4.2 s with 182 uF worst case. Dissipation 0.25 W at 50.4 V, 0.29 W at the 53.9 V trip ceiling: 29 % of the 1 W rating. Element voltage rating >= 100 V required")
    s.add("D303", "Device:D_Zener", "BZX84B51", {"1": "+48V_RAW", "2": "OVP_K"}, "Package_TO_SOT_SMD:SOT-23_Handsoldering" if False else "pump_v2:SOT-23_Zener_A1_K3", status="CALC", mpn="Vishay BZX84B51-E3-08",
          note="ECO2. Independent OVP trip, replaces the SMBJ48A clamp. 51 V +/-2 %, 180 ohm max. Trip 50.5-53.7 V: above the 48.58 V setpoint maximum, below the 60 V ceiling, overlaps the LM51551 OVP 51.4-54.2 V")
    R(s, "R314", "1k", "OVP_K", "OVP_G", status="CALC", note="ECO2. Limits gate current on overshoot")
    R(s, "R315", "10k", "OVP_G", "GND", status="CALC", note="ECO2. Zener bias: 90-150 uA at the FET threshold")
    C(s, "C313", "10nF", "OVP_G", "GND", status="CALC", note="ECO2. Noise filter, about 100 us")
    s.add("Q304", "Transistor_FET:BSS138", "BSS138", {"1": "OVP_G", "2": "GND", "3": "FLY_EN"},
          "Package_TO_SOT_SMD:SOT-23", status="CALC", mpn="BSS138 (e.g. Nexperia BSS138P)",
          note="ECO2. Pulls FLY_EN low on over-voltage, independent of the U301 FB path. Same action as veto Q401; can only stop the rail")
    TP(s, "TP301", "+48V_MOT")
    TP(s, "TP302", "FLY_PGOOD")

    # ===================================================================== 4
    s = Sheet("Kill path (fail-off)", "safety.kicad_sch", "48 V enable kill path: main MCU enable, supervisor veto")
    sheets.append(s)
    s.notes.append("K-10 DECIDED (fail-off): 4.7 k pull-down on the enable, main MCU drives it through 1 k, supervisor veto via one BSS138.\n"
                   "On Rev B the enable node is LM51551 UVLO/EN (FLY_EN). EN rising threshold 0.4-0.7 V, UVLO 1.425-1.575 V (SNVSB75E).\n"
                   "MCU high: 3.3 V x 4.7/(4.7+1) = 2.72 V -> run.  Pull-down only: 0 V -> shutdown.  BSS138 on: ~0 V -> shutdown.\n"
                   "Veto default (owner decision 10 Oct 2026, OPEN item 3 closed): R403 10k PULL-UP fitted -> veto ON whenever the supervisor\n"
                   "is in reset, crashed with its pin high/high-Z, or not running; firmware must drive PB0 LOW to permit 48 V. (R404 removed.)\n"
                   "PMD401 park (owner decision 10 Oct 2026, OPEN item 4): open-drain Q402 BSS138 with R405 10k gate PULL-UP -> AEN held LOW\n"
                   "(parked) by default; the PMD401's own 22k pull-up provides the run level, so no 3.3/5 V level question. Supervisor drives\n"
                   "PB1 (SUP_PARK) LOW to unpark. BSS138 VGS(th) 0.9-1.5 V (Nexperia BSS138P datasheet). SG-03/SG-05 still required on hardware.")
    R(s, "R401", "4.7k", "FLY_EN", "GND", status="DECIDED", note="K-10 enable pull-down (fail-off default)")
    R(s, "R402", "1k", "MCU_48V_EN", "FLY_EN", status="DECIDED", note="K-10 main MCU drive resistor so the supervisor can overpower it")
    s.add("Q401", "Transistor_FET:BSS138", "BSS138", {"1": "SUP_VETO", "2": "GND", "3": "FLY_EN"},
          "Package_TO_SOT_SMD:SOT-23", status="DECIDED", mpn="BSS138", note="K-10 supervisor veto FET (drain to EN, source to GND)")
    R(s, "R403", "10k", "SUP_VETO", "+3V3", status="DECIDED",
      note="Owner 10 Oct 2026: gate pull-UP, veto ON by default (closes OPEN item 3 / CF-9; deviation DV-3 from Rev A pull-down)")
    s.add("Q402", "Transistor_FET:BSS138", "BSS138", {"1": "SUP_PARK", "2": "GND", "3": "PMD_AEN_DRV"},
          "Package_TO_SOT_SMD:SOT-23", status="DECIDED", mpn="BSS138 (e.g. Nexperia BSS138P)",
          note="Owner 10 Oct 2026: open-drain AEN driver. ON (gate high) = AEN low = motor parked. Sinks only the PMD401 22k pull-up")
    R(s, "R405", "10k", "SUP_PARK", "+3V3", status="DECIDED",
      note="Owner 10 Oct 2026: Q402 gate pull-UP -> parked by default; supervisor PB1 LOW unparks")
    TP(s, "TP401", "FLY_EN")
    TP(s, "TP402", "SUP_VETO")
    TP(s, "TP403", "PMD_AEN")

    # ===================================================================== 5
    s = Sheet("Main MCU STM32WBA55", "mcu_main.kicad_sch", "Main MCU STM32WBA55CG: dosing, BLE, encoder, PMD401 SPI")
    sheets.append(s)
    s.notes.append("Pin map DERIVED from ST pin data in the KiCad STM32WBA55CGUx symbol; CONFIRM IN STM32CubeMX before layout freeze.\n"
                   "Encoder on TIM2 CH1/CH2 (PB6/PA8) - TIM2 width must be confirmed in RM0493 (CF-21/FW-08).\n"
                   "SPI3 -> PMD401 (mode 3, <= 500 kbit/s, PMD401 manual 150025-01 sec.5.2). USART2 + DE -> MAX3485. LPUART1 <-> supervisor link.\n"
                   "USART1 TX-only console (PA8, the only USART1_RX pin, carries the encoder).\n"
                   "ECO1: supplies per DS14127 Figure 15 (SMPS scheme), AN6373 and MB1803 B-01. VDDRFPA on the SMPS output limits TX to about +3 dBm (AN6373 sec.7);\n"
                   "for +10 dBm fit R513 and remove FB502. RF: MLPF-WB-04D3 with a 63 ohm line from pin 37 and a 50 ohm line to J501. HSE and LSE per AN5948 Table 5.")
    nm = {
        "1": "GND", "2": "WBA_VDDSMPS", "3": "WBA_VLXSMPS", "45": "WBA_VDD11", "8": "+3V3",
        "11": "+3V3", "22": "+3V3", "35": "+3V3", "44": "+3V3", "49": "GND",
        "38": "WBA_VDDHPA", "39": "WBA_VDD11", "40": "+3V3", "43": "WBA_VDDRFPA",
        "36": "MAIN_NRST", "37": "RF_MCU", "41": "HSE_OUT", "42": "HSE_IN", "16": "LSE_OUT", "17": "LSE_IN",
        "34": "MAIN_BOOT0",
        "13": "PMD_SCLK_M", "15": "PMD_MOSI_M", "9": "PMD_SS_M",
        "20": "ENC_A_M", "5": "ENC_B_M", "48": "ENC_I_M",
        "32": "RS485_DI", "29": "RS485_RO", "31": "RS485_DE",
        "21": "HB_M2S", "12": "HB_S2M", "4": "CON_MAIN_TX",
        "7": "I2C_SCL", "6": "I2C_SDA",
        "19": "MCU_48V_EN", "33": "PMD_READY_M", "23": "PMD_FAULT_M", "28": "FLY_PGOOD", "10": "CHG_INT_N",
        "14": "VBAT_SENSE", "30": "LED_MAIN",
        "27": "MAIN_SWDIO", "26": "MAIN_SWCLK", "24": "MAIN_SWO",
    }
    s.add("U501", "MCU_ST_STM32WB:STM32WBA55CGUx", "STM32WBA55CGUx", nm, status="DECIDED",
          mpn="STM32WBA55CGU6 (temp suffix TBD)", nc=["25", "18", "46", "47"],
          note="K-6. UFQFPN48 (only package for 'CG' in ST data). EP=49=VSS. Pin functions: see sheet note")
    for i, ref in enumerate(["C501", "C502", "C503", "C504"]):
        C(s, ref, "100nF", "+3V3", "GND", status="ASSUMED", note="VDD decoupling per pin; value to VERIFY vs ST datasheet")
    C(s, "C505", "100nF", "+3V3", "GND", status="DS", note="VDDA pin 8, DS14127 Fig.15. No bead: VDDA only serves the VBAT sense ADC")
    C(s, "C520", "1uF", "+3V3", "GND", status="DS", note="ECO1. VDDA pin 8, DS14127 Fig.15 (100 nF + 1 uF)")
    C(s, "C506", "10uF/10V", "WBA_VDDSMPS", "GND", status="DS", mpn="Murata GRM188C81A106MA73",
      note="ECO1. VDDSMPS input cap at pin 2: 10 uF +/-20 %, ESR < 50 mohm, >= 10 V (AN6373 sec.4.3)")
    C(s, "C521", "1uF", "+3V3", "GND", status="DS", note="ECO1. Supply side of FB501 (AN6373 sec.6.2 filter)")
    s.add("FB501", "Device:FerriteBead", "47R@100MHz", {"1": "+3V3", "2": "WBA_VDDSMPS"}, FP_C, status="DS", mpn="Taiyo Yuden LSMGA160808T470RG",
          note="ECO1. AN6373 sec.6.2 recommended VDD filter; DCR < 200 mohm")
    C(s, "C507", "10uF/10V", "+3V3", "GND", FP_C0805, status="DS", note="ECO1. VDD bulk, DS14127 Fig.15 (n x 100 nF + 10 uF)")
    C(s, "C508", "100nF", "MAIN_NRST", "GND", status="DS", note="AN5948 sec.4.5: 100 nF on reset; same power domain so no diode")
    L(s, "L503", "10nH", "WBA_VLXSMPS", "WBA_VLX_L", FP_C0402_L, status="DS", mpn="Murata LQG15HS10NJ02D",
      note="ECO1. AN6373 sec.6.1 RF noise coil, 500 mA, 0.26 ohm")
    L(s, "L501", "2.2uH", "WBA_VLX_L", "WBA_VDD11", "Inductor_SMD:L_0805_2012Metric", status="DS", mpn="Murata LQM21PN2R2MGH",
      note="ECO1. AN6373 sec.4: 2.2 uH +/-20 %, RDC < 500 mohm, Iop > 200 mA, Isat > 800 mA; other values not stable")
    C(s, "C509", "4.7uF", "WBA_VDD11", "GND", FP_C0402, status="DS", mpn="Murata GRM155R60J475ME47D",
      note="ECO1. SMPS output cap, fixed by design: 4.7 uF +/-20 %, ESR < 50 mohm (AN6373 sec.4.3)")
    C(s, "C510", "470nF", "WBA_VDDHPA", "GND", FP_C0402, status="DS", note="ECO1. VDDHPA: capacitor only, no supply (DS14127 sec.3.12). At pin 38")
    C(s, "C511", "100nF", "WBA_VDD11", "GND", FP_C0402, status="DS", note="ECO1. VDDANA pin 39 on the VDD11 node (DS14127 sec.3.12, Fig.15). At pin 39")
    C(s, "C512", "100nF", "+3V3", "GND", FP_C0402, status="DS", note="ECO1. VDDRF pin 40 on VDD (DS14127 sec.3.12). At pin 40")
    C(s, "C513", "100nF", "WBA_VDDRFPA", "GND", FP_C0402, status="DS", note="ECO1. VDDRFPA pin 43 (DS14127 Fig.15). At pin 43")
    s.add("FB502", "Device:FerriteBead", "47R@100MHz", {"1": "WBA_VDD11", "2": "WBA_VDDRFPA"}, FP_C, status="DS", mpn="Taiyo Yuden LSMGA160808T470RG",
          note="ECO1. VDDRFPA from the SMPS output; AN6373 sec.7 filter, as MB1803 L7. Remove if R513 is fitted")
    R(s, "R513", "0R", "WBA_VDDRFPA", "+3V3", dnp=True, status="DS",
      note="ECO1. Alternative for +10 dBm: fit this and remove FB502 (AN6373 sec.7, DS14127 Fig.16). Never fit both")
    s.add("FL501", "pump_v2:MLPF-WB-04D3", "MLPF-WB-04D3", {"A1": "RF_MCU", "A3": "RF_ANT", "A2": "GND", "B1": "GND", "B2": "GND", "B3": "GND"},
          status="DS", mpn="ST MLPF-WB-04D3",
          note="ECO1. DS14446: matched filter for WBA QFN, 50 ohm output. 63 ohm line from U501.37, 50 ohm line to J501, solid GND under both, top GND at the filter, dense stitching. Machine placement required")
    s.add("J501", "Connector:Conn_Coaxial", "U.FL", {"1": "RF_ANT", "2": "GND"},
          "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", status="ASSUMED", mpn="Hirose U.FL-R-SMT-1",
          note="Owner decision 10 Oct: U.FL instead of an antenna. 50 ohm feed from FL501")
    s.add("Y501", "Device:Crystal_GND24", "32MHz", {"1": "HSE_IN", "3": "HSE_OUT", "2": "GND", "4": "GND"},
          "pump_v2:Crystal_NX1612SA", status="DS", mpn="NDK NX1612SA-32MHZ-EXS00A-CS09166",
          note="ECO1. AN5948 Table 5 (Nucleo part), 8 pF load, internal load trim, no external capacitors. Land from ST MB1803. Beside pins 41/42, away from L501 and FL501")
    s.add("Y502", "Device:Crystal", "32.768kHz", {"1": "LSE_IN", "2": "LSE_OUT"},
          "pump_v2:Crystal_NX1610SE", status="DS", mpn="NDK NX1610SE-32.768KHZ-EXS00A-MU01501",
          note="ECO1. Fitted: AN5948 Table 5, radio sleep clock and RTC. Land from ST MB1803. Beside pins 16/17. Do not toggle PC13 (ES0592 sec.2.2.10)")
    C(s, "C518", "6pF C0G", "LSE_IN", "GND", FP_C0402, status="DS", note="ECO1. MB1803 C9, matched to the NX1610SE (AN5948 Fig.14)")
    C(s, "C519", "6pF C0G", "LSE_OUT", "GND", FP_C0402, status="DS", note="ECO1. MB1803 C8, matched to the NX1610SE (AN5948 Fig.14)")
    R(s, "R501", "10k", "MAIN_BOOT0", "GND", status="ASSUMED", note="PH3-BOOT0 strap low = boot from flash (RM0493). MB1803 uses 100k; either works")
    R(s, "R502", "1k", "LED_MAIN", "LED_MAIN_A", status="ASSUMED", note="Status LED (debug aid)")
    s.add("D501", "Device:LED", "LED_GRN", {"2": "LED_MAIN_A", "1": "GND"}, FP_LED, status="ASSUMED", note="Main MCU status LED (debug aid)")
    SWD(s, "J502", "MAIN", swo=True)
    s.add("J503", "Connector_Generic:Conn_01x04", "CONSOLE", {"1": "GND", "2": "CON_MAIN_TX", "3": "CON_SUP_TX", "4": "CON_SUP_RX"},
          "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", status="ASSUMED",
          note="Bench console UART header (WBA55 has no USB device port, HARDWARE_CONSTRAINTS 3.1). 3.3 V logic")

    # ===================================================================== 6
    s = Sheet("Supervisor STM32C031", "mcu_supervisor.kicad_sch", "Supervisor STM32C031C6: heartbeat, park line, 48 V veto, own encoder count")
    sheets.append(s)
    s.notes.append("K-6 / F-09: separate MCU, separate code base. It can only STOP: veto on the 48 V enable (SUP_VETO) and park line (PMD_AEN).\n"
                   "S-07 (approved 10 Oct): encoder A/B also into TIM3 CH1/CH2 via its own series resistors.\n"
                   "Pin map DERIVED from the KiCad STM32C031C6Tx symbol (ST pin data); CONFIRM in CubeMX. NRST assumed on PF2 (PF2-NRST) - VERIFY.\n"
                   "Package LQFP48 (C6T6) ASSUMED; the C031C6 also exists in UFQFPN48 (C6U6).")
    nm = {"6": "+3V3", "5": "+3V3", "7": "GND", "10": "SUP_NRST", "35": "SUP_SWDIO", "36": "SUP_SWCLK",
          "13": "HB_S2M", "14": "HB_M2S", "29": "CON_SUP_TX", "32": "CON_SUP_RX",
          "19": "SUP_VETO", "20": "SUP_PARK", "17": "ENC_A_S", "18": "ENC_B_S", "21": "LED_SUP"}
    used = set(nm)
    nc = [str(i) for i in range(1, 49) if str(i) not in used]
    s.add("U601", "MCU_ST_STM32C0:STM32C031C6Tx", "STM32C031C6Tx", nm, status="DECIDED",
          mpn="STM32C031C6T6 (package ASSUMED)", nc=nc, note="K-6 supervisor. LQFP48 assumed")
    C(s, "C601", "100nF", "+3V3", "GND", status="ASSUMED", note="VDD decoupling; VERIFY vs ST datasheet")
    C(s, "C602", "100nF", "+3V3", "GND", status="ASSUMED", note="VREF+ decoupling; VERIFY vs ST datasheet")
    C(s, "C603", "4.7uF", "+3V3", "GND", status="ASSUMED", note="Bulk; VERIFY vs ST datasheet")
    C(s, "C604", "100nF", "SUP_NRST", "GND", status="ASSUMED", note="NRST filter cap; VERIFY")
    R(s, "R601", "1k", "LED_SUP", "LED_SUP_A", status="ASSUMED", note="Supervisor status LED (debug aid)")
    s.add("D601", "Device:LED", "LED_RED", {"2": "LED_SUP_A", "1": "GND"}, FP_LED, status="ASSUMED", note="Supervisor status LED (debug aid)")
    SWD(s, "J601", "SUP", swo=False)

    # ===================================================================== 7
    s = Sheet("PMD401 & encoder interface", "pmd_interface.kicad_sch", "PMD401 servo/status/power/RS-485 connectors, LL06 encoder, protection")
    sheets.append(s)
    s.notes.append("Connector pinouts CONFIRMED from PiezoMotor PMD401 Technical Manual 150025-01 sec.3.4 / 3.5 (servo mode). All JST SH 1.0 mm.\n"
                   "Servo connector = the PMD401 6-pole sensor connector in servo mode; the LL06 encoder therefore connects to THIS board (J705).\n"
                   "J705 mirrors the PMD401 sensor-connector pinout so the kit encoder cable can plug in - VERIFY against the delivered cable.\n"
                   "E-07: TVS + 100 R on every PMD401 signal line. PMD401 inputs have internal pull-ups (10k/~20k/22k) to an UNSTATED rail (IF-02).\n"
                   "ECO1: READY and FAULT reach the MCU through BSS138 level shifters Q701/Q702: the MCU pin never sees above 3.3 V whatever the PMD401 rail, in reset or unpowered.\n"
                   "FIRMWARE: READY and FAULT both read LOW when the PMD401 is unpowered, so trust them only after FLY_PGOOD is high.\n"
                   "AEN has a 22k internal pull-up (manual); it is driven open-drain by Q402 (sheet Kill path): parked unless the supervisor unparks.\n"
                   "Encoder supply (OPEN item 12): JP701 default 3V3 (logic rail, survives 48 V switching); alternative PMD401 5V Out.")
    s.add("J701", "Connector_Generic_MountingPin:Conn_01x06_MountingPin", "PMD401_SERVO",
          {"1": "PMD_MOSI", "2": "GND", "3": "PMD_5V", "4": "PMD_SS", "5": "PMD_SCLK", "6": "PMD_AEN", "MP": "GND"},
          "Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal", status="DS", mpn="JST SM06B-SRSS-TB",
          note="PMD401 manual 150025-01 sec.3.5 servo connector")
    s.add("J702", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", "PMD401_STATUS",
          {"1": "GND", "2": "PMD_5V", "3": "PMD_READY", "4": "PMD_FAULT", "MP": "GND"},
          "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal", status="DS", mpn="JST SM04B-SRSS-TB",
          note="PMD401 manual sec.3.5 status connector (Ready: 0 = ready; Fault: 1 = error)")
    s.add("J703", "Connector_Generic_MountingPin:Conn_01x02_MountingPin", "PMD401_48V",
          {"1": "GND", "2": "+48V_MOT", "MP": "GND"},
          "Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal", status="DS", mpn="JST SM02B-SRSS-TB",
          note="PMD401 manual sec.3.4 power connector (48 VDC +/-5 %, 5 W). JST SH contact rating vs 100 mA to be confirmed")
    s.add("J704", "Connector_Generic_MountingPin:Conn_01x03_MountingPin", "PMD401_RS485",
          {"1": "GND", "2": "RS485_B", "3": "RS485_A", "MP": "GND"},
          "Connector_JST:JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal", status="DS", mpn="JST SM03B-SRSS-TB",
          note="PMD401 manual sec.3.4: 1 GND485 (100 R to PMD GND), 2 Data-, 3 Data+")
    s.add("J705", "Connector_Generic_MountingPin:Conn_01x06_MountingPin", "LL06_ENCODER",
          {"1": "ENC_I", "2": "GND", "3": "ENC_VCC", "4": "ENC_B", "5": "ENC_A", "6": "ENC_SHLD", "MP": "GND"},
          "Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal", status="ASSUMED", mpn="JST SM06B-SRSS-TB",
          note="Mirrors PMD401 sensor connector (I+, GND, 5V, B+, A+, screen). VERIFY vs LL06 encoder cable")
    R(s, "R701", "0R", "ENC_SHLD", "GND", status="ASSUMED", note="Encoder cable screen to GND")
    s.add("JP701", "Jumper:SolderJumper_3_Bridged12", "ENC_VCC_SEL", {"1": "+3V3", "2": "ENC_VCC", "3": "PMD_5V"},
          "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm_NumberLabels", status="ASSUMED",
          note="OPEN item 12: default 1-2 = 3V3. Encoder supply range not confirmed (vendor: output 3.3-5 V). PMD_5V dies with the 48 V rail")
    C(s, "C701", "100nF", "ENC_VCC", "GND", status="ASSUMED", note="Encoder supply decoupling")
    lines = [("PMD_MOSI", "PMD_MOSI_M"), ("PMD_SS", "PMD_SS_M"), ("PMD_SCLK", "PMD_SCLK_M"), ("PMD_AEN", "PMD_AEN_DRV"),
             ("PMD_READY", "PMD_READY_M"), ("PMD_FAULT", "PMD_FAULT_M"), ("ENC_A", "ENC_A_M"), ("ENC_B", "ENC_B_M"),
             ("ENC_I", "ENC_I_M")]
    shifted = {"PMD_READY_M": "PMD_READY_D", "PMD_FAULT_M": "PMD_FAULT_D"}
    for i, (ext, mcu) in enumerate(lines):
        TVS(s, f"D{701 + i}", ext)
        spi = mcu in ("PMD_MOSI_M", "PMD_SS_M", "PMD_SCLK_M")
        R(s, f"R{702 + i}", "1k" if spi else "100R", shifted.get(mcu, mcu), ext, status="CALC" if spi else "DECIDED",
          note="ECO2. E-07 series resistor raised to 1 k on SPI: limits back-feed into an unpowered PMD401 to about 3 mA; 100 ns with 100 pF at <= 500 kbit/s" if spi else "E-07 series resistor ('about 100 ohm', value to confirm)")
    for rref, net, val in (("R717", "PMD_MOSI_M", "15k"), ("R718", "PMD_SS_M", "33k"), ("R719", "PMD_SCLK_M", "15k")):
        R(s, rref, val, net, "GND", status="CALC",
          note="ECO2. Divider with the PMD401 pull-up: holds the pin below 4 V if VDD is 0 while the PMD401 rail decays (DS14127 Table 27). 3.6 V max at a 5.25 V rail with -30 % pull-up")
    for qref, rref, pin_net, drain in (("Q701", "R715", "PMD_READY_M", "PMD_READY_D"), ("Q702", "R716", "PMD_FAULT_M", "PMD_FAULT_D")):
        s.add(qref, "Transistor_FET:BSS138", "BSS138", {"1": "+3V3", "2": pin_net, "3": drain},
              "Package_TO_SOT_SMD:SOT-23", status="DS", mpn="BSS138 (e.g. Nexperia BSS138P)",
              note="ECO1. Non-inverting level shifter: gate +3V3, source MCU, drain PMD401 side. VGS(th) 0.9-1.5 V. Off when +3V3 is down, so the pin is isolated")
        R(s, rref, "100k", pin_net, "+3V3", status="CALC", note="ECO1. MCU-side high level for the shifter; 33 uA for the PMD401 output to sink")
    R(s, "R711", "100R", "ENC_A_S", "ENC_A", status="DECIDED", note="S-07: supervisor's own series resistor on encoder A")
    R(s, "R712", "100R", "ENC_B_S", "ENC_B", status="DECIDED", note="S-07: supervisor's own series resistor on encoder B")
    CP(s, "C702", "100uF/100V", "+48V_MOT", "GND", "Capacitor_THT:CP_Radial_D12.5mm_P5.00mm", status="DECIDED",
       note="Rev A item 24: 100 uF/100 V low-ESR bulk at the PMD401 input. Series/size TBD")
    s.add("U701", "Interface_UART:MAX3485", "MAX3485", {"1": "RS485_RO", "2": "RS485_DE", "3": "RS485_DE", "4": "RS485_DI",
                                                        "5": "GND", "6": "RS485_A", "7": "RS485_B", "8": "+3V3"},
          "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", status="DECIDED", mpn="MAX3485 SOIC-8 (suffix TBD)",
          note="Rev A item 9 RS-485 setup link (carried per P-01). SOIC-8 variant ASSUMED")
    C(s, "C703", "100nF", "+3V3", "GND", status="ASSUMED", note="MAX3485 decoupling")
    R(s, "R714", "120R", "RS485_A", "RS485_B", dnp=True, status="ASSUMED",
      note="Optional termination; PMD401 has its own switchable AC termination")
    TP(s, "TP701", "PMD_READY")
    TP(s, "TP702", "PMD_FAULT")

    # ===================================================================== root
    root = Sheet("root", "pump_v2.kicad_sch", "Piezo Insulin Pump v2 - Rev B handover prototype")
    for i, ref in enumerate(["H901", "H902", "H903", "H904"]):
        root.add(ref, "Mechanical:MountingHole", "M3", {}, "MountingHole:MountingHole_3.2mm_M3", status="ASSUMED",
                 note="Mounting hole (board mounting OPEN B.6)")
    root.notes.append(
        "PIEZO INSULIN PUMP v2 - REV B DIGITAL HANDOVER PROTOTYPE\n"
        "BENCH-ONLY: water or 0.9 % saline. NEVER connect to a person or an animal. No real insulin.\n"
        "NOT FABRICATION-APPROVED. NOT VALIDATED. Contains TBD and PLACEHOLDER parts (Status field / BOM).\n"
        "Clean ERC/DRC does not prove electrical correctness. Rev A bench validation has not been performed.\n"
        "Design basis: handoff documents 10 Oct 2026; locked decisions K-1..K-18 preserved. See docs/handover/.")
    return root, sheets
