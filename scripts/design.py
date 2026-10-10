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
          status="DECIDED", mpn="BQ25188YBGR", note="K-12. Pinout TI SLUSFJ3 Table 5-1. Footprint pitch UNVERIFIED (see footprint descr)")
    C(s, "C101", "2.2uF/25V", "VBUS_CHG", "GND", FP_C0805, status="DS",
      note="IN: >=1 uF effective after DC bias (SLUSFJ3 Table 5-1); 25 V for 5 V USB + margin")
    C(s, "C102", "1uF/10V", "VBAT_FUSED", "GND", status="DS", note="BAT: >=1 uF ceramic (SLUSFJ3 Table 5-1)")
    C(s, "C103", "10uF/10V", "CHG_SYS", "GND", FP_C0805, status="DS", note="SYS: >=10 uF ceramic (SLUSFJ3 Table 5-1); SYS otherwise unloaded (E-09)")
    R(s, "R101", "10k_TBD", "CHG_TS", "GND", status="TBD",
      note="TS/MR: pack NTC not defined (OPEN B.20). Fixed 10k stands in for a 10k NTC at 25 C; TS can be disabled via TS_EN. "
           "WARNING: TS/MR held low enters ship mode")
    s.add("J103", "Connector:USB_C_Receptacle_PowerOnly_6P", "USB_C_PWR",
          {"A9": "VBUS_CHG", "B9": "VBUS_CHG", "A5": "USB_CC1", "B5": "USB_CC2", "A12": "GND", "B12": "GND", "SH": "GND"},
          "Connector_USB:USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal", status="ASSUMED", mpn="GCT USB4125",
          note="Charger input connector OPEN B.19; USB-C power-only sink assumed")
    R(s, "R102", "5.1k", "USB_CC1", "GND", status="ASSUMED", note="USB-C sink Rd on CC1 (USB Type-C spec value)")
    R(s, "R103", "5.1k", "USB_CC2", "GND", status="ASSUMED", note="USB-C sink Rd on CC2 (USB Type-C spec value)")
    R(s, "R104", "10k", "I2C_SCL", "+3V3", status="DS", note="SCL pull-up to logic rail, 10k per SLUSFJ3 Table 5-1")
    R(s, "R105", "10k", "I2C_SDA", "+3V3", status="DS", note="SDA pull-up to logic rail, 10k per SLUSFJ3 Table 5-1")
    R(s, "R106", "10k", "CHG_INT_N", "+3V3", status="DS", note="/INT open drain, 1-20k pull-up allowed (SLUSFJ3)")
    R(s, "R107", "TBD", "VBAT", "VBAT_SENSE", dnp=True, status="PLACEHOLDER",
      note="VBAT sense divider for S-13 3.4 V cut-off. INA219 omitted on Rev B by owner (10 Oct 2026); sensing method OPEN")
    R(s, "R108", "TBD", "VBAT_SENSE", "GND", dnp=True, status="PLACEHOLDER", note="see R107")
    C(s, "C104", "100nF", "VBAT_SENSE", "GND", dnp=True, status="PLACEHOLDER", note="see R107")
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
    L(s, "L201", "2.2uH", "BUCK_SW", "+3V3", "Inductor_SMD:L_0603_1608Metric", status="DS",
      note="2.2 uH per SLVSEC6D typical application; specific part TBD from SLVSEC6D Table 4 (Isat/DCR)")
    C(s, "C201", "4.7uF/10V", "VBAT", "GND", status="DS", note="CIN 4.7 uF required (SLVSEC6D pin table)")
    C(s, "C202", "10uF/10V", "+3V3", "GND", FP_C0805, status="DS", note="COUT 10 uF (SLVSEC6D typical application)")
    FLAG(s, "#FLG201", "+3V3")
    TP(s, "TP201", "+3V3")

    # ===================================================================== 3
    s = Sheet("48V flyback", "power_48v.kicad_sch", "LM51551 non-isolated flyback, 48 V motor rail")
    sheets.append(s)
    s.notes.append("K-12 / DECIDED 29 Sep: Rev B 48 V stage is an LM51551 flyback (plain boost hits the 93 % duty limit).\n"
                   "Topology follows TI SNVSB75E Figure 10-12 'Typical Non-Isolated Flyback'; BIAS tied to VCC for 1S start (>=2.97 V).\n"
                   "POWER STAGE NOT DESIGNED: transformer, FET, diode, sense resistor, clamp, RT, SS and compensation are TBD (OPEN B.16).\n"
                   "Kill path: UVLO/EN driven by FLY_EN (sheet 'Kill path'). EN < 0.4 V min (SNVSB75E) = shutdown. A flyback has no DC path\n"
                   "from VBAT to the output, so EN low de-energises the rail. K-12 'switched output' + E-11 bleeder: DNP PLACEHOLDERS only.\n"
                   "E-06: every 48 V capacitor rated >= 100 V. E-03: 45.6-50.4 V at the PMD401.")
    CP(s, "C301", "220uF/16V", "VBAT", "GND", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm", status="DECIDED",
       note="Bulk at converter input, carried from Rev A item 25 (220 uF/16 V low-ESR); adequacy for flyback TBD")
    C(s, "C302", "10uF/10V", "VBAT", "GND", FP_C0805, status="TBD", note="Input ceramic, value TBD with power-stage design")
    C(s, "C303", "10uF/10V", "VBAT", "GND", FP_C0805, status="TBD", note="Input ceramic, value TBD with power-stage design")
    s.add("U301", "pump_v2:LM51551", "LM51551DSSR",
          {"1": "VBAT", "2": "VBAT", "12": "FLY_EN", "10": "FLY_RT", "9": "FLY_SS", "11": "FLY_PGOOD",
           "3": "FLY_GATE", "5": "FLY_CS", "8": "FLY_FB", "6": "FLY_COMP", "4": "GND", "7": "GND", "13": "GND"},
          status="DECIDED", mpn="LM51551DSSR",
          note="K-12. Pinout SNVSB75E Table 7-1. BIAS=VCC (SNVSB75E sec.1: 2.97-16 V). UVLO/EN max = VBIAS+0.3 V; FLY_EN <= 0.82 x 3V3 <= VBAT")
    C(s, "C304", "1uF/10V", "VBAT", "GND", status="TBD", note="BIAS/VCC bypass to PGND (SNVSB75E Table 7-1); value TBD")
    R(s, "R301", "TBD", "FLY_RT", "GND", status="TBD", note="RT sets fsw 100 kHz-2.2 MHz; TBD with transformer")
    C(s, "C305", "TBD", "FLY_SS", "GND", status="TBD", note="Soft-start cap (10 uA source); TBD")
    R(s, "R302", "100k", "FLY_PGOOD", "+3V3", status="ASSUMED", note="PGOOD open-drain pull-up to 3V3 (<= VBIAS)")
    R(s, "R303", "TBD", "FLY_COMP", "FLY_COMP_RC", status="TBD", note="Compensation Rc; TBD")
    C(s, "C306", "TBD", "FLY_COMP_RC", "GND", status="TBD", note="Compensation Cc; TBD")
    C(s, "C307", "TBD", "FLY_COMP", "GND", dnp=True, status="TBD", note="Optional HF compensation pole; TBD")
    s.add("Q301", "pump_v2:Q_NMOS_TDSON8_TBD", "NMOS_TBD", {"4": "FLY_GATE", "5": "FLY_SW", "1": "FLY_CS", "2": "FLY_CS", "3": "FLY_CS"},
          status="PLACEHOLDER", note="Flyback switch: logic-level (gate drive = VBAT 3.0-4.2 V), Vds/Id/Rds TBD. Footprint is a placeholder")
    R(s, "R305", "TBD", "FLY_CS", "GND", FP_R2512, status="TBD", note="Current sense (100 mV limit threshold, SNVSB75E); value TBD")
    s.add("T301", "pump_v2:XFMR_FLYBACK_TBD", "XFMR_TBD", {"1": "VBAT", "2": "FLY_SW", "3": "GND", "4": "FLY_SEC"},
          status="PLACEHOLDER", note="Flyback transformer part/turns ratio OPEN B.16. Dot polarity per standard flyback (opposite windings)")
    s.add("D301", "Device:D_Schottky", "D_TBD_100V", {"2": "FLY_SEC", "1": "+48V_RAW"}, "Diode_SMD:D_SMA",
          status="TBD", note="Output rectifier >= 100 V class; part TBD")
    s.add("D302", "Device:D_Schottky", "D_CLAMP_TBD", {"2": "FLY_SW", "1": "FLY_CLAMP"}, "Diode_SMD:D_SMA",
          status="TBD", note="Primary RCD clamp diode; need and values TBD with transformer leakage")
    R(s, "R306", "TBD", "FLY_CLAMP", "VBAT", FP_R1206, status="TBD", note="RCD clamp resistor TBD")
    C(s, "C308", "TBD", "FLY_CLAMP", "VBAT", FP_C0805, status="TBD", note="RCD clamp capacitor TBD")
    C(s, "C309", "2.2uF/100V", "+48V_RAW", "GND", FP_C1210, status="TBD", note="Output ceramic; >=100 V rating per E-06 DECIDED; value TBD")
    C(s, "C310", "2.2uF/100V", "+48V_RAW", "GND", FP_C1210, status="TBD", note="Output ceramic; >=100 V per E-06; value TBD")
    CP(s, "C311", "47uF/100V", "+48V_RAW", "GND", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", status="DECIDED",
       note="47 uF/100 V carried from Rev A item 23 (DC2628A output). Series/size TBD")
    R(s, "R307", "470k 1%", "+48V_RAW", "FLY_FB", status="CALC",
      note="Vout = 1.0 V x (1 + 470k/10k) = 48.0 V (VREF 1 V +/-1 %, SNVSB75E). Tolerance stack not verified vs 45.6-50.4 V")
    R(s, "R308", "10k 1%", "FLY_FB", "GND", status="CALC", note="see R307")
    # --- K-12 switched output: placeholder only
    s.add("Q302", "pump_v2:Q_PMOS_SOT23_TBD", "PMOS_TBD", {"1": "SW48_GATE", "2": "+48V_RAW", "3": "+48V_MOT"},
          footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2", dnp=True,
          status="PLACEHOLDER", note="K-12 'switched output' high-side switch NOT DESIGNED (owner 10 Oct: placeholder). >=100 V class")
    R(s, "R309", "TBD", "SW48_GATE", "+48V_RAW", dnp=True, status="PLACEHOLDER", note="Q302 gate-source pull-up placeholder")
    R(s, "R310", "TBD", "SW48_GATE", "SW48_DRV", dnp=True, status="PLACEHOLDER", note="Q302 gate drive placeholder")
    s.add("Q303", "pump_v2:Q_NMOS_SOT23_TBD", "NMOS_TBD", {"1": "FLY_EN", "2": "GND", "3": "SW48_DRV"},
          footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2", dnp=True,
          status="PLACEHOLDER", note="Level-shift placeholder driven by FLY_EN. >=100 V class (BSS138 50 V fails the 80 % rule)")
    R(s, "R311", "0R", "+48V_RAW", "+48V_MOT", FP_R1206, status="ASSUMED",
      note="Bypass of the undesigned output switch Q302 so the rail is usable. Remove if Q302 is designed in")
    R(s, "R312", "TBD", "+48V_MOT", "GND", FP_R2512, dnp=True, status="PLACEHOLDER",
      note="E-11 (proposed) bleeder: < 5 V within 5 s. Value/power TBD")
    TP(s, "TP301", "+48V_MOT")
    TP(s, "TP302", "FLY_PGOOD")

    # ===================================================================== 4
    s = Sheet("Kill path (fail-off)", "safety.kicad_sch", "48 V enable kill path: main MCU enable, supervisor veto")
    sheets.append(s)
    s.notes.append("K-10 DECIDED (fail-off): 4.7 k pull-down on the enable, main MCU drives it through 1 k, supervisor veto via one BSS138.\n"
                   "On Rev B the enable node is LM51551 UVLO/EN (FLY_EN). EN rising threshold 0.4-0.7 V, UVLO 1.425-1.575 V (SNVSB75E).\n"
                   "MCU high: 3.3 V x 4.7/(4.7+1) = 2.72 V -> run.  Pull-down only: 0 V -> shutdown.  BSS138 on: ~0 V -> shutdown.\n"
                   "UNRESOLVED (OPEN item 3 / CF-9): BSS138 gate default. R403 (pull-UP, veto on by default) and R404 (pull-DOWN,\n"
                   "as wired on Rev A) are BOTH placed DNP. Owner decision required before build. With neither fitted the gate floats\n"
                   "while the supervisor is in reset - this is NOT an acceptable build state. SG-03 must be run after the decision.")
    R(s, "R401", "4.7k", "FLY_EN", "GND", status="DECIDED", note="K-10 enable pull-down (fail-off default)")
    R(s, "R402", "1k", "MCU_48V_EN", "FLY_EN", status="DECIDED", note="K-10 main MCU drive resistor so the supervisor can overpower it")
    s.add("Q401", "Transistor_FET:BSS138", "BSS138", {"1": "SUP_VETO", "2": "GND", "3": "FLY_EN"},
          "Package_TO_SOT_SMD:SOT-23", status="DECIDED", mpn="BSS138", note="K-10 supervisor veto FET (drain to EN, source to GND)")
    R(s, "R403", "10k", "SUP_VETO", "+3V3", dnp=True, status="PLACEHOLDER",
      note="OPEN item 3 option A: pull-up -> veto ON by default (proposed 10 Oct report). Owner decision pending")
    R(s, "R404", "10k", "SUP_VETO", "GND", dnp=True, status="PLACEHOLDER",
      note="OPEN item 3 option B: pull-down as wired on Rev A (K-10). Breaks S-01 with a dead supervisor. Owner decision pending")
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
                   "ST DATASHEET NOT AVAILABLE in this session (st.com unreachable): SMPS inductor, VDD11, VDDRF/VDDRFPA/VDDHPA/VDDANA\n"
                   "connections, decoupling values, HSE crystal/load caps, BOOT0 strap and RF matching are PLACEHOLDERS (see ERC report).")
    nm = {
        "1": "GND", "2": "+3V3", "3": "WBA_VLXSMPS", "45": "WBA_VDD11", "8": "+3V3",
        "11": "+3V3", "22": "+3V3", "35": "+3V3", "44": "+3V3", "49": "GND",
        "38": "WBA_VDDHPA", "39": "WBA_VDDANA", "40": "WBA_VDDRF", "43": "WBA_VDDRFPA",
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
    C(s, "C505", "100nF", "+3V3", "GND", status="ASSUMED", note="VDDA decoupling; VERIFY (filtering) vs ST datasheet")
    C(s, "C506", "100nF", "+3V3", "GND", status="ASSUMED", note="VDDSMPS decoupling; VERIFY vs ST datasheet")
    C(s, "C507", "4.7uF", "+3V3", "GND", status="ASSUMED", note="Bulk; VERIFY vs ST datasheet")
    C(s, "C508", "100nF", "MAIN_NRST", "GND", status="ASSUMED", note="NRST filter cap (common ST practice); VERIFY")
    L(s, "L501", "L_SMPS_TBD", "WBA_VLXSMPS", "WBA_VDD11", "Inductor_SMD:L_0805_2012Metric", status="PLACEHOLDER",
      note="SMPS inductor between VLXSMPS and VDD11 ASSUMED topology; value and topology from ST datasheet TBD (or LDO mode)")
    C(s, "C509", "TBD", "WBA_VDD11", "GND", status="PLACEHOLDER", note="VDD11 capacitor TBD per ST datasheet")
    for net, cref, rref in [("WBA_VDDHPA", "C510", "R510"), ("WBA_VDDANA", "C511", "R511"),
                            ("WBA_VDDRF", "C512", "R512"), ("WBA_VDDRFPA", "C513", "R513")]:
        C(s, cref, "TBD", net, "GND", status="PLACEHOLDER", note=f"{net[4:]} decoupling TBD per ST datasheet")
        R(s, rref, "0R_VERIFY", net, "+3V3", dnp=True, status="PLACEHOLDER",
          note=f"{net[4:]} supply connection UNKNOWN without ST datasheet; DNP link to 3V3 reserves the option. Do not fit unverified")
    C(s, "C514", "TBD", "RF_MCU", "GND", FP_C0402, dnp=True, status="PLACEHOLDER", note="RF pi-match shunt 1; values per ST RF reference (not identified, OPEN B.24/25)")
    L(s, "L502", "TBD", "RF_MCU", "RF_ANT", "Inductor_SMD:L_0402_1005Metric", status="PLACEHOLDER", note="RF pi-match series element; fit 0R/value per ST reference")
    C(s, "C515", "TBD", "RF_ANT", "GND", FP_C0402, dnp=True, status="PLACEHOLDER", note="RF pi-match shunt 2")
    s.add("J501", "Connector:Conn_Coaxial", "U.FL", {"1": "RF_ANT", "2": "GND"},
          "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", status="ASSUMED", mpn="Hirose U.FL-R-SMT-1",
          note="Owner decision 10 Oct: U.FL + pi-match placeholder instead of an antenna. 50 ohm trace impedance TBD with stack-up")
    s.add("Y501", "Device:Crystal_GND24", "32MHz_TBD", {"1": "HSE_IN", "3": "HSE_OUT", "2": "GND", "4": "GND"},
          "Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm", status="TBD", note="32 MHz HSE (PB-06). Crystal part and load per ST reference TBD")
    C(s, "C516", "TBD", "HSE_IN", "GND", FP_C0402, dnp=True, status="PLACEHOLDER", note="HSE load cap; may be unnecessary (internal trim) - VERIFY")
    C(s, "C517", "TBD", "HSE_OUT", "GND", FP_C0402, dnp=True, status="PLACEHOLDER", note="HSE load cap; VERIFY")
    s.add("Y502", "Device:Crystal", "32.768kHz", {"1": "LSE_IN", "2": "LSE_OUT"},
          "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", dnp=True, status="PLACEHOLDER", note="Optional LSE; need TBD (OPEN B.24)")
    C(s, "C518", "TBD", "LSE_IN", "GND", FP_C0402, dnp=True, status="PLACEHOLDER", note="LSE load cap")
    C(s, "C519", "TBD", "LSE_OUT", "GND", FP_C0402, dnp=True, status="PLACEHOLDER", note="LSE load cap")
    R(s, "R501", "10k", "MAIN_BOOT0", "GND", status="ASSUMED", note="PH3-BOOT0 strap low = boot from flash; VERIFY vs ST datasheet")
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
          "19": "SUP_VETO", "20": "PMD_AEN_S", "17": "ENC_A_S", "18": "ENC_B_S", "21": "LED_SUP"}
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
                   "AEN has a 22k internal pull-up (manual): a dead supervisor leaves the motor ENABLED unless R706 is fitted (OPEN item 4).\n"
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
    lines = [("PMD_MOSI", "PMD_MOSI_M"), ("PMD_SS", "PMD_SS_M"), ("PMD_SCLK", "PMD_SCLK_M"), ("PMD_AEN", "PMD_AEN_S"),
             ("PMD_READY", "PMD_READY_M"), ("PMD_FAULT", "PMD_FAULT_M"), ("ENC_A", "ENC_A_M"), ("ENC_B", "ENC_B_M"),
             ("ENC_I", "ENC_I_M")]
    for i, (ext, mcu) in enumerate(lines):
        TVS(s, f"D{701 + i}", ext)
        R(s, f"R{702 + i}", "100R", mcu, ext, status="DECIDED", note="E-07 series resistor ('about 100 ohm', value to confirm)")
    R(s, "R711", "100R", "ENC_A_S", "ENC_A", status="DECIDED", note="S-07: supervisor's own series resistor on encoder A")
    R(s, "R712", "100R", "ENC_B_S", "ENC_B", status="DECIDED", note="S-07: supervisor's own series resistor on encoder B")
    R(s, "R713", "TBD", "PMD_AEN", "GND", dnp=True, status="PLACEHOLDER",
      note="OPEN item 4: AEN pull-down to beat the PMD401 22k internal pull-up; value after IF-02 measurement. Owner decision")
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
