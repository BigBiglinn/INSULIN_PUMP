# Implementation {#ch:impl}

## v1: HybridPancreasSim C++ simulator and ESP32 demonstration rig {#sec:v1}

!box Status of this section: | The v1 C++ source code (`BergmanModel.h`, `Controllers.h` and the rest of the merged codebase), its CSV results, `report.html` and the ESP32 firmware are not yet in the project repository. They exist only as attachments in earlier project conversations (docs/SOURCE_DOCUMENTS.md, section 3). This section therefore records only what the project records state. The full code listing ({app:code}), the model parameters and the result plots will be added from the original files once they are committed to the repository. No v1 number in this report has been regenerated.

### Purpose and structure (as recorded)

HybridPancreasSim was written before September 2026 to demonstrate the control concepts used in commercial closed-loop pumps (decision log, v1). The project records list these components:

- a **plant model**, the Bergman minimal model of glucose–insulin dynamics ({sec:bergman}, {eq:bergman1}–{eq:bergman3}), in `BergmanModel.h`;
- **controllers** in `Controllers.h`: a PID controller and a predictive controller;
- a **safety supervisor** that limits or suspends delivery;
- **fault injection**, to test the supervisor; and
- result output as CSV files and an HTML report (`report.html`), plus a 33-slide presentation.

### Recorded results

The decision log records two summary results of the simulator: the PID controller achieved **about 89 % time in range**, and the predictive controller with the safety supervisor achieved **about 93 % time in range with 0 % hypoglycaemia**. The simulated patient parameters, the meal scenario, the simulation length and the definition of time in range used are not recorded in the repository. These figures are simulation results from v1 and say nothing about the v2 hardware.

### ESP32 demonstration rig (superseded)

The v1 rig used an ESP32 DevKit, a SmartElex A4988 stepper driver and a NEMA 17 motor (JK42HS40-1204AF-02) on a T8 leadscrew, powered from an 11.1 V 3S LiPo, with STEP on GPIO26, DIR on GPIO27 and the on-board LED on GPIO2. A rack-and-pinion drive and OpenSCAD motor-mount and carriage parts were also designed and verified in September 2026. All v1 hardware is superseded and is not carried into v2.

## v2 Rev A: bench build on development boards {#sec:reva}

Rev A was to prove the circuit on the bench with development boards and power modules before any PCB was made (K-7, U-12). The 37-item parts list was declared final on 29–30 September 2026. {app:bom} reproduces the whole list; {tab:reva} summarises it by group.

!table tab:reva | Rev A parts list by group (37 lines; DECIDED) | 2,6
| Group | Main parts |
| Motion and fluid | LL06A0-101M1G1E2 motor; PMD401 driver (Starter Kit, with cables and a 48 V supply); Hamilton 81320 syringe; disposable 1 mL syringes for fit trials; Luer stopcocks |
| Control | NUCLEO-WBA55CG; NUCLEO-C031C6; MAX3485 module; optional USB-to-RS-485 adapter |
| Battery and protection | Molicel INR18650-P28A; holder; 1S 5 A protection board; TP4056 (charging only); 5 A blade fuse; toggle switch; INA219 (0.1 Ω shunt) |
| 3.3 V rail | MCP1700-3302E/TO LDO with 1 µF in and out |
| 48 V rail | Pololu U3V70F12 (3.7 → 12 V, EN = kill switch); DC2628A / LT8362 (12 → 48 V); 47 µF/100 V replacing the stock 33 µF/50 V output capacitor; 100 µF/100 V at the PMD401; 220 µF/16 V and 47 µF/25 V input bulk |
| Enable logic and wiring | BSS138; 4.7 kΩ enable pull-down; 1 kΩ MCU resistor; 10 kΩ gate resistor; TVS + 100 Ω on PMD401 lines; XT30 connectors; silicone wire; Ohmite 20J470E 470 Ω/10 W dummy load |
| Bench instruments | Disposable IBP transducer + HX711 (pressure reference to 300 mmHg); optional ChipWhisperer-Husky for glitch testing |

The Rev A modules and the cell are documented in the parts list [21]. The Rev A power tree is:

!codeblock
Molicel INR18650-P28A  (TP4056 on B+/B-, charging only)
  -> 1S 5 A protection board -> 5 A blade fuse -> toggle switch (master) -> INA219 (0.1 ohm, high side)
  -> battery bus
       |-> MCP1700-3302E/TO (1 uF in, 1 uF out) -> 3.3 V: both Nucleos, INA219, MAX3485
       |-> 220 uF/16 V -> Pololu U3V70F12 (EN = kill switch) -> 12 V
              -> 47 uF/25 V -> DC2628A (LT8362) -> 48 V (47 uF/100 V at VOUT)
              -> XT30 -> 100 uF/100 V -> PMD401 -> LL06
!endcode

Three Rev A decisions show the engineering reasoning applied:

1. **Pololu first in the chain.** The U3V70F12 truly disconnects its output when disabled. Switching it off therefore removes power from the whole 48 V chain. A boost module without true shutdown would pass VBAT to the output when disabled and defeat the kill switch.
2. **Kill switch made fail-off (30 September).** The Pololu EN pin has an internal 100 kΩ pull-up to VIN, so the original wiring was fail-*on*. A 4.7 kΩ pull-down holds EN at 4.2 V × 4.7/(100 + 4.7) ≈ 0.19 V, below the 0.4 V off level. The main MCU overrides it through 1 kΩ, and the supervisor's BSS138 can short it.
3. **DC2628A output capacitor replaced.** The stock 33 µF/50 V part would run at 96 % of its rating at 48 V. It is replaced by 47 µF/100 V (E-06).

Board settings are recorded too: on the NUCLEO-WBA55CG, JP2 is removed and external 3.3 V is fed to JP2 pin 2 (ST UM3301). The PMD401 is set to servo mode over RS-485 with `X0Y13,3`, then `X0Y32`.

**Status:** Rev A was designed but not built. The motor was quoted on 8 October 2026 (LL06A0-101M1G1E2 at €984, total €1,619, DAP Guwahati €150, lead time 3–4 weeks from payment). Acceptance and payment are not recorded. The required priced parts totalled about ₹36,801 on 30 September 2026, before the motor kit and duties.

## Rev B design method: a generated KiCad project {#sec:toolchain}

The Rev B design is not drawn by hand; it was produced and checked with KiCad 10, LTspice, ngspice, Freerouting and STM32CubeMX [24]. A single Python file, `scripts/design.py` (471 lines, listed in {app:code}), describes every part, value, footprint, net, status and justification. Generator scripts turn it into a KiCad 10 project ({fig:toolchain}):

- `gen_library.py` writes the project symbol and footprint library (LM51551, BQ25188, TPS62840DLC, HPH6-0090L, MLPF-WB-04D3, crystals and others);
- `gen_schematic.py` writes the root sheet and seven sub-sheets, with net classes in the project file;
- `gen_pcb.py` places the board, draws planes and fans out plane pads, and exchanges Specctra files with the Freerouting autorouter;
- `hand_route.py`, `grid_route.py`, `route_stage.py` and `pcb_eco.py` apply routes and placement changes from reviewed JSON specifications; and
- `run_checks.sh` runs kicad-cli ERC, DRC with schematic parity, and the BOM export.

This approach makes every circuit change reviewable as a text diff. It makes the source of each value traceable through the part's Note field. Re-running the checks after a change is mechanical. The cost is that regeneration overwrites hand edits, so every change was preceded by a checkpoint commit or tag.

!fig fig:toolchain | docs/project_report/figures/fig_toolchain.png | Design-generation and verification flow. | 6.27

## Rev B schematic {#sec:schematic}

The schematic is hierarchical: a root sheet and seven functional sheets. It is drawn label-style, with every pin carrying a net label. That is less readable than a hand-drawn schematic but exactly traceable to `design.py`. Each sheet carries its design notes as text. {fig:sch2} to {fig:sch8} reproduce the sheets as generated at `pcb-p6-final`. The subsections below explain how each sheet works.

### Root sheet

The root sheet carries the four M3 mounting holes and the project disclaimer: bench-only, not fabrication-approved, contains TBD and PLACEHOLDER parts, a clean ERC/DRC does not prove electrical correctness.

### Power input and charger

The cell connects through J101 to the 5 A fuse F101 (part number TBD), then to J102, a terminal block for the off-board master switch, giving VBAT. The BQ25188 (U101) [4] charges the cell from USB-C (J103, with 5.1 kΩ Rd resistors) on the fused node VBAT_FUSED, ahead of the switch, so charging is possible with the switch off. Its SYS pin has only its 10 µF capacitor. The I²C pull-ups (10 kΩ) and the /INT pull-up go to 3V3. The battery-voltage divider R107/R108 (200 kΩ/200 kΩ, C104 100 nF) feeds U501 ADC4 for the 3.4 V dosing cut-off (S-13). The divider replaces the INA219, which the owner chose not to carry to Rev B. Its values were reduced from 1 MΩ to 200 kΩ in ECO1 so that the ADC leakage error at VBAT is at most 30 mV.

!fig fig:sch2 | docs/project_report/figures/schr-2.png | Schematic sheet 2: battery input, fuse, master switch and BQ25188 charger. | 5.9

### 3.3 V buck

U201 TPS62840DLC with VSET 267 kΩ for 3.3 V (TI SLVSEC6D VSET table [5]), EN tied to VIN, MODE and STOP to ground. L201 is the TI-recommended Murata DFE201612E 2.2 µH [19] (2016 size), and C201/C202 are 4.7 µF in and 10 µF out.

!fig fig:sch3 | docs/project_report/figures/schr-3.png | Schematic sheet 3: TPS62840 3.3 V buck. | 5.9

### 48 V flyback

{sec:flyback} explains this sheet ({fig:sch4}) in detail. It contains U301 LM51551, T301 HPH6-0090L, Q301 AONR34332C, the 22 mΩ sense resistor R305, the RCD clamp (D302, R306, C308) with the SMAJ15A ceiling D304, rectifier D301 with RC snubber R313/C312, output capacitors C309–C311, the feedback divider R307/R308, the 10 kΩ bleeder R312, the independent OVP trip (D303, R314, R315, C313, Q304), the bench-tuning options JP301/R316/R317/C314 (unfitted), and R311 (0 Ω) between +48V_RAW and the motor rail +48V_MOT.

!fig fig:sch4 | docs/project_report/figures/schr-4.png | Schematic sheet 4: LM51551 non-isolated flyback for the 48 V motor rail. | 5.9

### Kill path

R401, R402, Q401/R403 (veto) and Q402/R405 (park), with test points on FLY_EN, SUP_VETO and PMD_AEN ({sec:safety}).

!fig fig:sch5 | docs/project_report/figures/schr-5.png | Schematic sheet 5: fail-off kill path (enable, supervisor veto, park). | 5.9

### Main MCU (STM32WBA55CG)

U501 with its supply network, set by ECO1 from ST DS14127 Figure 15 and the application notes AN6373 and AN5948 [12]:

- **SMPS:** VDDSMPS through ferrite bead FB501 with a 10 µF capacitor. VLXSMPS through a 10 nH RF-noise coil L503 and the 2.2 µH SMPS inductor L501 to VDD11, with 4.7 µF.
- **Supply pins:** VDDANA on VDD11. VDDRF on 3V3. VDDRFPA from VDD11 through bead FB502, which limits TX power to about +3 dBm (R513 is the +10 dBm option). VDDHPA has a capacitor only.
- **Clocks:** 32 MHz NX1612SA crystal using the chip's internal load trim, and a 32.768 kHz NX1610SE crystal with 6 pF capacitors.
- **RF and debug:** MLPF-WB-04D3 RF filter and U.FL J501; SWD header J502; console header J503; BOOT0 pull-down; status LED.

!fig fig:sch6 | docs/project_report/figures/schr-6.png | Schematic sheet 6: main MCU STM32WBA55CG with SMPS, crystals, RF filter and debug. | 5.9

### Supervisor (STM32C031C6)

U601 with decoupling (values to be confirmed against the ST datasheet [13]), SWD header J601 and a status LED. Its pins are SUP_VETO, SUP_PARK, encoder A/B on TIM3, the heartbeat on USART2 and a console on USART1. All other GPIOs carry no-connect flags.

!fig fig:sch7 | docs/project_report/figures/schr-7.png | Schematic sheet 7: supervisor STM32C031C6. | 5.9

### PMD401 and encoder interface

Connectors J701–J705 follow the PMD401 Technical Manual 150025-01 sections 3.4 and 3.5 [6]. Every PMD401 signal has a PESD5V0S1BA TVS and a series resistor (E-07): 1 kΩ on the three SPI lines and 100 Ω elsewhere. Dividers R717–R719 hold the SPI pins below 4 V if the MCU is unpowered while the PMD401 rail decays (ECO2). READY and FAULT reach the MCU through non-inverting BSS138 level shifters Q701/Q702 (ECO1). Encoder A/B go to the main MCU and, through R711/R712, to the supervisor. The encoder is powered from 3V3 by default (JP701), so its count survives 48 V switching. The MAX3485 provides the RS-485 set-up link, and C702 (100 µF/100 V) is the bulk capacitor at the PMD401.

!fig fig:sch8 | docs/project_report/figures/schr-8.png | Schematic sheet 8: PMD401 connectors, encoder, protection, level shifters and RS-485. | 5.9

## 48 V flyback converter design {#sec:flyback}

The design follows the typical non-isolated flyback application in TI SNVSB75E [3]. The requirements are an input of 3.0–4.2 V (dosing stops at 3.4 V), an output of 45.6–50.4 V at the PMD401 including ripple and a 0 → 100 mA load step, and a load of at most 100 mA.

**Switching frequency.** From the datasheet RT equation:

!eq eq:rt | R_{T} = 2.21×10^{10}/f_{SW} − 955  →  R301 = 73.2 kΩ gives f_{SW} = 298 kHz (±15 %)

**Turns ratio and duty cycle.** In continuous conduction a flyback obeys

!eq eq:duty | V_{out} + V_{F} = n·V_{in}·D/(1 − D)  →  D = (V_{out} + V_{F})/(V_{out} + V_{F} + n·V_{in})

With n = 5, V_{out} = 48 V and V_{F} = 0.9 V: D = 48.9/(48.9 + 15.0) = 0.765 at 3.0 V and 48.9/(48.9 + 21.0) = 0.70 at 4.2 V. Both are inside the LM51551's ≥ 90 % maximum duty at 300 kHz.

**Input current and primary inductance.** At 4.8 W out and an assumed 80 % efficiency, the input current is 2.0 A at 3.0 V. The average primary current during the on-time is I_{in}/D = 2.61 A. Choosing a ripple of 40 % (ΔI = 1.05 A):

!eq eq:lp | L_{p} = V_{in}·D/(ΔI·f_{SW}) = 3.0 × 0.765/(1.05 A × 298 kHz) = 7.3 µH

and the peak primary current is 2.61 + 1.05/2 ≈ 3.1 A. Simulation gives 3.4 A including the snubber's reflected current.

**Current limit.** With the 93–107 mV current-limit threshold:

!eq eq:ilim | I_{LIM} = V_{CLTH}/R_{S} = 93…107 mV / 22 mΩ = 4.2…4.9 A

This leaves margin above the 3.4 A needed at 3.0 V and 100 mA, and sets the transformer saturation requirement (≥ 5 A).

**Output voltage.** With V_{REF} = 1.0 V ±1 % and 0.1 % resistors:

!eq eq:vout | V_{out} = V_{REF}·(1 + R307/R308) = 1.0 V × (1 + 470 k/10 k) = 48.0 V ;  range 47.43–48.58 V

The range sits inside 45.6–50.4 V with about 1.8 V of margin on each side for ripple and load steps. The independent review computed 46.6–49.4 V for the earlier 1 % resistors, which is why ECO1 changed R307/R308 to 0.1 %.

**Output capacitance and ripple.**

!eq eq:ripple | ΔV = I_{out}·D/(f_{SW}·C)  →  C ≥ 0.1 A × 0.765/(298 kHz × 0.24 V) = 1.07 µF

Two 2.2 µF/100 V X7R capacitors (C309, C310) allow for about 60 % DC-bias loss. C311 (47 µF/100 V) and C702 (100 µF/100 V) add bulk.

**Device stresses.**

!eq eq:vds | V_{DS} = V_{in,max} + (V_{out} + V_{F})/n + V_{spike} = 4.2 + 9.8 V + V_{spike} = 14.0 V + V_{spike}

!eq eq:vrect | V_{R,D301} = V_{out} + n·V_{in,max} = 48 + 21 = 69 V (+ ringing)

The leakage-inductance spike dominates V_{DS}. It is limited by the RCD clamp (R306 330 Ω, C308 100 nF, D302) with the SMAJ15A ceiling D304. {sec:openloop} to {sec:q301} give the simulated values.

**Right-half-plane zero and compensation.** The CCM flyback has a right-half-plane zero at

!eq eq:rhpz | f_{RHPZ} = (1 − D)^{2}·V_{out}/(2π·D·I_{out}·n^{2}·L_{p}) ≈ 30 kHz  (D = 0.765, I_{out} = 0.1 A, L_{p} = 7.29 µH)

so the crossover was placed at about 3 kHz. The type-II network R303 = 3.01 kΩ, C306 = 180 nF, C307 = 3.3 nF is **preliminary**. LTspice has no LM51551 model, and the result depends on T301 and on the PMD401 cable and bulk capacitance.

**Soft start.** With I_{SS} = 9–11 µA:

!eq eq:tss | t_{SS} = C_{SS}·V_{REF}/I_{SS} = 1 µF × 1 V/(9…11 µA) = 91…111 ms

The original 47 nF (4.7 ms) was found by simulation to lock the converter in its 64-cycle hiccup mode while it charges about 150–182 µF of output capacitance ({sec:softstart}), so ECO1 raised it to 1 µF. Firmware must keep the PMD401 parked until FLY_PGOOD, because a full 100 mA load during start-up still fails at 3.0 V and 3.4 V input.

**Discharge (E-11, proposed).** With the worst-case 182 µF on the rail:

!eq eq:bleed | t_{5V} = R312·C·ln(V_{0}/5 V) = 10 kΩ × 182 µF × ln(50.4/5) = 4.21 s

which meets the "< 5 V within 5 s" target. R312 dissipates 0.25 W at 50.4 V, 29 % of its 1 W rating.

**Over-voltage trip.** The trip level is V_{Z} (49.5–52.0 V at 100 µA) + V_{GS(th)} of Q304 (0.9–1.5 V) + 0.15 V = 50.5–53.7 V, or 53.9 V including the filter delay. That is above the 48.58 V set-point maximum and 6 V below the 60 V touch-safety ceiling.

!table tab:flyparts | Flyback power-stage parts and the evidence for each | 1.2,2,4
| Ref | Part | Evidence / note |
| U301 | TI LM51551DSSR | K-12; pinout SNVSB75E Table 7-1; BIAS = VCC from 2.97 V |
| T301 | Coilcraft HPH6-0090L | Doc 613 [14]: 7.29 µH ±5 % per winding, Isat 27.6 A on one winding, Irms 2.90 A, 131.9 V·µs, 500 Vrms between windings. Primary = winding 3–10; secondary = 5 windings in series (n = 5). **Leakage not published** |
| Q301 | AOS AONR34332C | [15] 30 V, RDS(on) < 2.9 mΩ at VGS 2.5 V, VGS(th) 0.5–1.2 V. Replaced the 25 V CSD16340Q3 [17] in ECO2. **Voltage margin not established** |
| D301 | Nexperia PNE20010ER | [16] 200 V / 1 A hyperfast (trr 25 ns); a 100 V Schottky rang to breakdown in simulation |
| R313 / C312 | 220 Ω 1206 / 100 pF 250 V C0G | Rectifier snubber, 0.14–0.17 W |
| D302 | Nexperia PMEG10020ELR | Clamp diode, 100 V / 2 A Schottky |
| R306 / C308 / D304 | 330 Ω 1 W / 100 nF 50 V / SMAJ15A | RCD clamp with a TVS ceiling (ECO2) |
| R305 | 22 mΩ 1 % 1 W 2512 | Current sense; ILIM 4.2–4.9 A |
| C305 | 1 µF X7R | Soft start 91–111 ms (ECO1) |
| R307 / R308 | 470 kΩ / 10 kΩ, 0.1 % | 48 V set point |
| R312 | 10 kΩ 1 % 1 W 2512 | Bleeder, 4.21 s to 5 V |
| D303, R314, R315, C313, Q304 | BZX84B51, 1 k, 10 k, 10 nF, BSS138 | Independent OVP trip (ECO2); zener and SMAJ15A data from distributors [18] |
| JP301 / R316 / R317 / C314 | bridged / unfitted | Gate resistor and drain snubber options for bench tuning (ECO3) |

## Microcontroller pin maps {#sec:pinmap}

The assignments were derived from the ST pin data shipped with KiCad. All 41 functions were then checked against the STM32CubeMX 6.18.1 database by `scripts/verify_pinmap.py`, with **0 failures** ({tab:pinmain}, {tab:pinsup}). The check confirms that each function exists on its pin and that no signal is used twice. It does not check clock trees, run-time peripheral conflicts, 5 V tolerance or electrical ratings.

!table tab:pinmain | Main MCU U501 (STM32WBA55CGUx, UFQFPN48) pin map | 0.6,0.9,1.6,2.6
| Pin | Port | Net | Function |
| 13 / 15 / 9 | PA0 / PB8 / PA5 | PMD_SCLK_M / PMD_MOSI_M / PMD_SS_M | SPI3 SCK / MOSI / NSS to the PMD401 (mode 3) |
| 20 / 5 | PB6 / PA8 | ENC_A_M / ENC_B_M | TIM2 CH1 / CH2 encoder mode |
| 48 | PB14 | ENC_I_M | encoder index (GPIO/EXTI) |
| 32 / 29 / 31 | PB0 / PA11 / PB1 | RS485_DI / RO / DE | USART2 TX / RX / DE to the MAX3485 |
| 21 / 12 | PB5 / PA1 | HB_M2S / HB_S2M | LPUART1 TX / RX heartbeat link |
| 4 | PB12 | CON_MAIN_TX | USART1 TX console (TX only) |
| 7 / 6 | PA6 / PA7 | I2C_SCL / I2C_SDA | I2C3 to the BQ25188 |
| 19 | PB7 | MCU_48V_EN | GPIO out to FLY_EN through R402 |
| 33 / 23 | PB15 / PB4 | PMD_READY_M / PMD_FAULT_M | GPIO in (via level shifters) |
| 28 | PA12 | FLY_PGOOD | GPIO in, LM51551 PGOOD |
| 10 | PA2 | CHG_INT_N | GPIO in / EXTI, charger interrupt |
| 14 | PB9 | VBAT_SENSE | ADC4_IN10 |
| 30 | PB2 | LED_MAIN | status LED |
| 27 / 26 / 24 / 36 | PA13 / PA14 / PB3 / NRST | SWDIO / SWCLK / SWO / NRST | SWD on J502 |
| 34 | PH3-BOOT0 | MAIN_BOOT0 | 10 kΩ pull-down |
| 37 | RF | RF_MCU | to MLPF-WB-04D3 |
| 41 / 42; 16 / 17 | OSC_OUT / OSC_IN; PC15 / PC14 | HSE; LSE | 32 MHz and 32.768 kHz crystals |

!table tab:pinsup | Supervisor U601 (STM32C031C6Tx, LQFP48 assumed) pin map | 0.6,0.9,1.6,2.6
| Pin | Port | Net | Function |
| 19 | PB0 | SUP_VETO | GPIO out to Q401 gate (HIGH/high-Z = veto ON) |
| 20 | PB1 | SUP_PARK | GPIO out to Q402 gate (HIGH/high-Z = parked) |
| 17 / 18 | PA6 / PA7 | ENC_A_S / ENC_B_S | TIM3 CH1 / CH2, independent encoder count (S-07) |
| 13 / 14 | PA2 / PA3 | HB_S2M / HB_M2S | USART2 TX / RX heartbeat link |
| 29 / 32 | PA9 / PA10 | CON_SUP_TX / RX | USART1 console |
| 21 | PB2 | LED_SUP | status LED |
| 35 / 36 / 10 | PA13 / PA14-BOOT0 / PF2-NRST | SWDIO / SWCLK / NRST | SWD on J601 |

## Printed circuit board {#sec:pcb}

### Stack-up, rules and net classes

The board has four layers. Spacing and current-width targets refer to IPC-2221C and IPC-2152, and land patterns to IPC-7351 [22]. F.Cu and B.Cu carry signals and ground pours. In1.Cu is a solid ground plane, continuous apart from via antipads (requirement L-1, independently checked). In2.Cu is split: VBAT under the battery strip, a bottom band and the 48 V block, and +3V3 elsewhere. The board outline is 111.6 × 85.1 mm with four M3 holes. No size requirement exists (B.6); the right edge was moved out 1.5 mm in stage P1b to give the 13.6 mm tall transformer clearance from the edge. No fab house has been chosen, so the rules are generic ({tab:rules}). The RF line widths assume the JLC04161H-7628 stack-up (0.2104 mm prepreg, εr 4.4), taken from a secondary source.

!table tab:rules | Board design rules and net classes (hardware/kicad/pump_v2.kicad_pro and .kicad_dru) | 2,1,1,1,3
| Class / rule | Clearance | Track | Via (dia/drill) | Nets / scope |
| Default | 0.15 mm | 0.20 mm | 0.6 / 0.3 mm | all others |
| PWR | 0.20 mm | 0.80 mm | 0.7 / 0.35 mm | VBAT_RAW, FLY_SW, FLY_CLAMP |
| HV48 | 0.60 mm | 0.40 mm | 0.6 / 0.3 mm | +48V_RAW, +48V_MOT, FLY_SEC, FLY_SEC_A–D |
| RF | 0.20 mm | 0.30 mm | 0.6 / 0.3 mm | RF_MCU, RF_ANT |
| Board minimums | 0.15 mm | 0.15 mm | 0.5 / 0.3 mm | copper-to-edge 0.3 mm, hole clearance 0.25 mm |
| Scoped exception J703 | 0.35 mm | – | – | pads of the vendor JST SH 48 V connector only |
| Scoped exception Q301 | 0.127 mm | – | – | pads of the VSON-8 NexFET pattern only |
| Scoped exception FL501 | 0.15 mm | – | – | bumps of the MLPF-WB-04D3 only |

The HV48 clearance of 0.6 mm on every layer is a conservative reading of proposal P-03 (0.6 mm outer, 0.1 mm inner); the source conflict CF-6 is unresolved. The three exceptions are scoped to pad pairs inside one footprint each, so no other rule is relaxed.

### Placement

Placement groups the board by function: the battery strip and charger along one edge, the 48 V block (flyback, transformer, PMD401 connectors) at one end (proposal P-03), the WBA55 with its RF filter and U.FL at the opposite end, and the supervisor between them. A placement study on 11 October (`scripts/eval_placement.py`) evaluated three move sets on scratch copies of the board. It measured the straight-line airwire length of 35 nets and the flyback loop metrics, then ran kicad-cli DRC on each copy. The owner-approved variant v2 shortened the clamp loop from 59.7 mm to 13.9 mm, the secondary loop from 73.1 mm to 18.8 mm and the gate path from 11.0 mm to 3.4 mm. Total airwire length fell by 22 % (1323.9 → 1031.6 mm). After ECO1 the real transformer, 32.65 × 26.75 mm, replaced the 12 × 12 mm placeholder, and the 48 V block was re-placed in stage P1.

### Routing history {#sec:routing}

The board was first autorouted with Freerouting 2.1.0 in three passes of 12 minutes each, which plateaued at about 63 unrouted items. After that, routing was done in **staged, owner-gated steps**, each from an explicit JSON route specification, each DRC-checked and tagged ({tab:routing}, {fig:routing}). Freerouting's telemetry was enabled by default during the first runs and was switched off afterwards (U-22).

!table tab:routing | Routing and PCB stages with the unconnected-item count reported by kicad-cli | 1.3,4,1
| Stage | Work | Unconnected |
| Stage 3 passes 2–3 (10 Oct) | Freerouting incremental passes on design v1 | 64 → 63 |
| Design v2 passes 1–2, hand_route | Regenerated board, compact flyback placement | 42 → 37 → 35 |
| Approved placement v2 (11 Oct) | 26 parts moved; 20 + 3 nets ripped up | 80 |
| Stage 1 | LM51551 controller nets (FB, SS, RT, COMP, PGOOD), Kelvin sense, gate | 67 |
| Stage 2 | ENC_VCC, PMD_5V, supervisor console | 61 |
| D1 | R301/R302/C305/R308 rotated 180° to free the FLY_PGOOD escape | 59 |
| Stage 3 | FLY_EN and HB_S2M safety-control nets | 54 |
| Stage 4 | Encoder connections (new `grid_route.py`) | 48 |
| Stage 5a / D7 | MAIN_SWCLK, PMD_READY, FLY_PGOOD → U501.28: blocked; no copper change | 48 |
| P1 (31 Oct) | Footprints and placement updated to ECO1/ECO2; copper removed on changed nets | 81 |
| P2 | RF line, WBA55 supplies, crystals, U501 pins 24–40 | 50 |
| P4 | Independent signals, ECO3 parts | 37 |
| P6 (1 Nov) | Flyback, 48 V rail, OVP group, charger, ENC_I_M; silkscreen | **0** |

!fig fig:routing | docs/project_report/figures/fig_routing_progress.png | Unconnected items at each recorded checkpoint. The two rises are deliberate: rip-up for the approved placement, and new parts added by ECO1/ECO2. | 6.27

Several routing problems needed engineering judgement:

- **U501 pin 28 (FLY_PGOOD).** In stage 5a no escape existed. A scratch investigation (D7) showed that re-routing the pin 29 and pin 30 escapes alone could not free it. The decision was deferred to a coordinated fan-out review of pins 24–38, which stage P2 carried out: FLY_PGOOD was routed in 53.4 mm with 2 vias.
- **ENC_I_M (pin 48).** No route existed without crossing the RF path or changing the pin. The owner authorised one B.Cu crossing under RF_MCU, with the solid In1 ground between them. RF_ANT has no crossing.
- **MAIN_NRST.** It was first routed in 62.5 mm with 6 vias to avoid the RF line, then corrected to 49 mm with 2 vias.
- **FLY_SW.** It runs on B.Cu at 1.0 mm with 2 + 2 vias, because F.Cu is blocked by the T301 pin 9 HV clearance. This adds loop inductance and is a review item.

### RF line

ECO1 replaced the placeholder pi-match with ST's MLPF-WB-04D3 filter, which needs a 63 Ω line from the MCU pin and a 50 Ω line to the connector. A 2-D finite-difference solver (`validation/sim/rf_line_solver.py`) gave widths of 0.20 mm (62.9 Ω) and 0.32 mm (50.5 Ω) with 0.25 mm gaps over the solid In1 plane. The solder mask is opened over both lines, because the mask lowers Z_{0} by about 8 %. Stage P2 routed RF_MCU in 2.5 mm and RF_ANT in 8.5 mm, with no vias, GND stitching on both sides and no crossing on RF_ANT. The previous autorouted path was 50.9 mm long, with 2 vias and 10 crossings.

### Final board

{fig:pcb3d} and {fig:layers} show the board at `pcb-p6-final`. It has 158 footprints, 1114 track segments, 277 vias and 2991 mm of track. Four parts sit on the bottom side (C313, JP301, R315, R316).

!fig fig:pcb3d | docs/report_assets/board_3d_top.png | 3-D render of the Rev B board, top side, at tag pcb-p6-final. | 5.2

!fig fig:pcb3db | docs/report_assets/board_3d_bottom.png | 3-D render of the Rev B board, bottom side. | 5.2

!fig fig:layers | docs/project_report/figures/layer_F.png | Top copper layer (F.Cu) with pads and outline. | 6.27

!fig fig:layerb | docs/project_report/figures/layer_B.png | Bottom copper layer (B.Cu). | 6.27

!fig fig:layerin1 | docs/project_report/figures/layer_In1.png | Inner layer 1 (In1.Cu): solid ground plane. | 6.27

!fig fig:layerin2 | docs/project_report/figures/layer_In2.png | Inner layer 2 (In2.Cu): VBAT and +3V3 power planes. | 6.27

## Firmware architecture {#sec:fw}

Firmware is outside the delivered scope, because the owner writes it personally (K-16). The design was nevertheless fixed and a reference implementation was written in the project on 27 September 2026 as an answer key. Its files are `pump_config.h`, `pump_port.h`, `dose_ctrl.c`, `load_est.c`, `hardened.h`, `port_stm32wba.c`, `pump_app.c`, `sim_plant.c` and `test_main.c` (`pump_fw.zip`), with a nine-stage course (`pump_course.zip`) whose README lists four bugs found. These archives, like the v1 code, are not yet in the repository.

The recorded design is:

- **Plain C11 behind one hardware boundary** (`pump_port.h`), so the same dosing code runs on a PC simulator and on the target (F-01).
- **Dose state machine** IDLE → UNPARK → MOVE → SETTLE → IDLE, with FAULT reachable from every state ({fig:fsm}).
- **Hardening:** values stored with complements, doubled limit checks with random delay, encoded booleans and a control-flow counter (F-03). Verification by voltage and clock glitching is a stretch goal (C-07).
- **Load estimation** from step length (`load_est.c`), the basis of sensorless occlusion detection.

!fig fig:fsm | docs/project_report/figures/fig_dose_fsm.png | Dose state machine (F-02). | 5.8

The reference code passed these simulator tests on an assumed plant: 40 × 0.05 U delivered 19.997 µL of 20 µL (within 0.03 % across step lengths of 2–8 µm); a 5 U bolus delivered 49.998 µL in about 60 s; a 27 % SPI scale error was absorbed by the encoder loop; an occlusion alarm came after about 0.21 U (about 773 mmHg); bit flips in the limits, the target and the authorisation flag were all detected; and an MCU hang stopped the motor within 10 ms. These are simulation results of reference code, not of the owner's firmware and not of hardware.

The hardware design places these **obligations on firmware**, collected from the ECOs and the review:

- keep the PMD401 parked until FLY_PGOOD is high;
- trust READY and FAULT only after FLY_PGOOD, because both read LOW when the PMD401 is unpowered;
- configure the WBA55 SMPS and the TX power for VDDRFPA on VDD11;
- centre the HSE crystal with HSETRIM and leave PC13 unused (ES0592 §2.2.10);
- set the BQ25188 charge current and service or disable its watchdog;
- use VREFINT for battery measurement;
- keep the SPI lines low or high-impedance until FLY_PGOOD; and
- refuse to dose without a supervisor reply.

## Engineering change orders {#sec:eco}

Three schematic change orders, each verified and tagged, brought the design from the 10 October handover to its final state. ECO1 was verified item by item ({tab:eco1}). ECO2 superseded parts of it ({tab:eco2}).

!table tab:eco1 | ECO1 (31 Oct 2026, tag sch-eco1-done): verdicts and changes | 2,1.5,4
| Item | Verdict | Change and evidence |
| WBA55 power | Verified after corrections | Supplies per DS14127 Fig. 15 and AN6373: L501 2.2 µH, FB501/FB502 beads, L503 10 nH, C506 10 µF, C509 4.7 µF, C510 470 nF, VDDRF on 3V3, VDDANA and VDDRFPA on VDD11. R510–R512 placeholder links deleted |
| LM51551 soft start | Verified by simulation; needs hardware test | C305 47 nF → 1 µF; 47 nF fails every corner |
| Transformer | Needs hardware test (leakage) | T301 = HPH6-0090L; all published limits pass; leakage unpublished |
| RF | Corrected | MLPF-WB-04D3; 0.20 mm (63 Ω) and 0.32 mm (50 Ω) lines; mask opened |
| READY / FAULT | Corrected | BSS138 level shifters Q701/Q702 with 100 kΩ pull-ups replace pin moves |
| Clocks | HSE verified; LSI2 needs correction | NX1612SA with internal trim; LSE crystal Y502 fitted |
| 48 V protection | Corrected; needs hardware test | Bleeder R312 10 k fitted; K-12 switched output dropped (EN controls the rail) |
| Other | – | L201 to a 2016 footprint; R107/R108 to 200 kΩ; R307/R308 to 0.1 % |

!table tab:eco2 | ECO2 (31 Oct 2026, tag sch-eco2-done) and ECO3 | 2,5
| Item | Change and reason |
| 48 V clamp | SMBJ48A rejected: clamp voltage at the 0.21 A the converter can deliver is about 59.4 V, only 0.6 V below the 60 V ceiling, and its 53.3 V minimum overlaps the OVP. Replaced by the independent zener/BSS138 trip on FLY_EN (50.5–53.9 V) |
| R312 | Corrected to 10 kΩ 2512 **1 W** (0.25 W is the dissipation) and moved to +48V_RAW beside C311 |
| Flyback clamp | At the 4.9 A limit the old 390 Ω/22 nF clamp reached 26.3 V (2 %), 32.6 V (4 %) and 45.2 V (10 % leakage). New: Q301 AONR34332C 30 V, R306 330 Ω, C308 100 nF, D304 SMAJ15A ceiling |
| PMD401 SPI | No level shifter, because a BSS138's rising edges would take about 1 µs. Series resistors raised to 1 kΩ (back-feed about 3 mA); dividers R717–R719 keep the pins below 4 V when the MCU is unpowered |
| ECO3 | Q301 gate bridge JP301 with an optional gate resistor R316; optional drain snubber R317/C314; all unfitted until measured |
