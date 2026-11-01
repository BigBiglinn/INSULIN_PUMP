# Independent design review: Piezo Insulin Pump v2, Rev B handover

Date: 1 Nov 2026. Scope: the whole project as it stands at commit `976a17b`, covering requirements, `scripts/design.py`, the eight schematic sheets, the 4-layer PCB, the project library, the BOMs and the handover documents.

Method: every result below was produced in this review by the reviewer's own scripts and calculations, checked against the datasheets in `docs/datasheets/`. Earlier ERC/DRC reports, earlier simulation results and the handover registers were **not** used as evidence. They were read only afterwards, to mark which findings were already known.

BENCH-ONLY PROTOTYPE: water or saline, never on a person or an animal. Nothing here is a bench result. A clean check is not proof that the circuit works.

## 1. What was run, and what could not be

| Check | Tool (reproducible) | Result |
| --- | --- | --- |
| Schematic netlist vs `design.py`: geometric pin, wire and label extraction from all 8 `.kicad_sch` files | `scripts/review/sch_netlist_check.py` → `validation/review/sch_netlist_check.txt` | 411/411 pins match; 0 dangling pins without a no-connect flag |
| PCB pad nets vs `design.py` (parity) | `scripts/review/pcb_check.py` | All pads match; only intentional `unconnected-*` NC pins differ |
| PCB copper connectivity: tracks, vias, through-hole pads and zone fills joined per layer | same → `validation/review/pcb_check.txt` | **28 nets with 35 missing connections** |
| Shorts (copper of different nets overlapping) | same | 0 |
| Clearance against net-class rules (plus the two scoped `.kicad_dru` exceptions) | same; custom pads approximated by their bounding size | 0 violations against the rules *as written* (see F-M11: the rules themselves have gaps) |
| Track width and length on every current-carrying net | same | See F-C4, F-M1, F-M2 |
| Courtyard overlap and board-edge containment (bounding boxes) | inline check | 0 overlaps; all parts inside the 110 × 85 mm outline |
| In1.Cu ground plane continuity | inline check | Unbroken: voids are via and hole antipads only, so L-1 is met |
| IC pin maps (WBA55, C031, BQ25188, TPS62840, LM51551, MAX3485, CSD16340Q3) | symbol pin and alternate-function dump; datasheet pin tables | All correct (§4) |
| Design equations: slope compensation, current limit, FB tolerance, OVP, kill-path levels, bleed time, IR drop, encoder timing | `scripts/review/design_calcs.py` → `validation/review/design_calcs.txt` | See §2 and §3 |
| Flyback power stage, layout sensitivity (new ngspice netlist, open loop, spec transformer) | `scripts/review/run_flyback_sens.sh` → `validation/review/flyback_layout_sens.txt` | Peak Vds 17.7–17.9 V with a tight clamp; **26.2–28.2 V with ~25 nH clamp-path inductance** |
| BOM vs design | inline check | `docs/bom.csv` and `docs/bom_detailed.csv` are **stale** (F-M14) |

**Not run, and why:**
- **KiCad 10 ERC/DRC.** This container has only Ubuntu's KiCad 7.0.11, which cannot open these KiCad 10 files (PCB format version 20260206). Running a downloaded KiCad 10 image was refused by the session's permission policy. The PCB checks above are an independent geometric DRC, not KiCad's. The KiCad 10 ERC/DRC must still be run with `scripts/run_checks.sh` on a machine that has KiCad 10.0.3.
- **ST datasheets.** st.com and ti.com are blocked from this container, so the STM32WBA55 and STM32C031 power-pin, decoupling, SMPS and RF requirements could not be read. Only the pin data packaged in the KiCad symbols was available.
- No bench, fabrication or RF measurement of any kind.

Severity scale: **Critical** means the board cannot work, or a part is overstressed, or a DECIDED requirement fails. **Major** means likely malfunction, a requirement violation, or a wrong order. **Minor** means robustness, maintainability or margin. A **"New"** tag means the finding is not recorded in `docs/handover/`.

## 2. Critical findings

### F-C1. Board is not fully routed: 35 connections missing on 28 nets
Evidence: `validation/review/pcb_check.txt`. Functionally fatal gaps include:
- `+48V_MOT` to J703: the PMD401 gets no 48 V.
- `VBAT_FUSED` to U101.C2: the charger is not connected to the cell.
- `MAIN_SWCLK`: the main MCU cannot be programmed.
- `PMD_MOSI_M`, `PMD_SCLK_M`, `PMD_READY_M`: no motor command or status.
- `HSE_IN` / `HSE_OUT`: no 32 MHz clock, so no BLE.
- `RF_MCU`: no RF path.
- `WBA_VDD11` and the four RF/analog supply nets (also F-C2).
- `ENC_VCC` (encoder unpowered), `ENC_I_M`, `ENC_A_S`: the supervisor loses encoder A.
- `FLY_SS`: no soft start, so start-up runs at the current limit.
- `FLY_PGOOD`, `VBAT_SENSE`, `I2C_SDA`, `CHG_INT_N`, `CON_SUP_TX/RX`, and `+3V3` to R302.

`RS485_B` is open only to DNP R714, and `SW48_GATE` only among DNP placeholders.
Fix: do not keep routing the present placement. First apply the placement fixes F-C3, F-C4, F-M3, F-M6 and F-M15, which move the same parts that block today's corridors. Then re-route. Accept the board only when KiCad 10 DRC reports 0 unconnected items with `--schematic-parity`.

### F-C2. STM32WBA55 supply pins are not actually supplied
Evidence: `design.py:288-318`. VDDHPA (38), VDDANA (39), VDDRF (40) and VDDRFPA (43) connect to +3V3 only through DNP 0 Ω links (R510–R513). Their capacitors are "TBD". The SMPS inductor L501 and the VDD11 capacitor C509 are "TBD" and their topology is assumed. As built, these pins float, so the radio, and possibly the core, will not run.
Fix: get the STM32WBA55 datasheet (power-supply scheme section), ST's STM32WBA hardware getting-started application note, and the NUCLEO-WBA55CG schematic. Copy the exact supply connections, the SMPS-or-LDO choice, the L/C values and the decoupling. Then replace R510–R513 with fixed connections and remove the PLACEHOLDER status. (Known as an ST-datasheet item; still critical.)

### F-C3. RCD clamp placed ~25 mm from the switch node lets Q301 exceed its 25 V rating (New)
Evidence: D302 sits at (196.3, 142.2), C308 at (190.3, 145.0) and R306 at (175.4, 143.0). Q301's drain is at (171.6, 159.5) and T301 pin 2 at (175.5, 159.5). FLY_SW totals 38 mm of track, including a layer change. My simulation (`flyback_layout_sens.txt`, same spec transformer with k = 0.99) gives:
- peak Vds 17.7 V (3.0 V in) and 17.9 V (4.2 V in) with a tight clamp;
- **28.2 V and 26.2 V** with about 25 nH in the clamp path. That is my estimate of roughly 1 nH/mm for today's routing, not an extracted value.

The CSD16340Q3 is rated 25 V. This overstresses the FET and fails the E-06 80 % rule (20 V) by a wide margin.
Fix: put D302 directly next to the Q301 drain and T301 pin 2, and C308/R306 next to D302. Return the clamp to the C302/C303 VBAT pads on F.Cu, with a loop under ~10 mm² and no vias. Re-simulate with the extracted loop inductance. If the margin is still short with the real T301 leakage, the owner can approve a 30–40 V FET (the clamp would then be re-tuned).

### F-C4. FLY_CS track carries the primary current at 0.2 mm and sits inside the current-sense path (New)
Evidence: Q301 source pads (169.76, 158.5–159.8) connect to R305 pad 1 (168.04, 164.6) through about 6 mm of 0.2 mm track. U301 CS (pin 5) taps the network at the Q301 end. That track is about 15 mΩ at 25 °C, so the sensed resistance is 37 mΩ instead of 22 mΩ. That gives **Ilim(min) = 93 mV / 37 mΩ = 2.5 A**. The simulated peak needed at 3.0 V and 100 mA is 3.4 A, so the converter current-limits and cannot hold 48 V at low battery (E-03). The same 0.2 mm track also carries about 2.3 A rms (heating), and R305's ground pad returns through one via.
Fix: abut R305 to the Q301 source pads with a solid F.Cu pour at least 2 mm wide. Run a separate thin Kelvin trace from R305 pad 1 to CS. Give R305 pad 2 at least 4–6 vias to the In1 ground. Return U301 PGND to the same point.

### F-C5. No slope compensation at D ≈ 0.71–0.79 in peak-current-mode CCM (New)
Evidence: SNVSB75E §9.3.6, eq. 8. The primary-referred falling slope is (48 + 0.9)/5/7.3 µH = 1.34 A/µs. With RS = 22 mΩ, the requirement is 0.5 × 1.2 × 1.34 A/µs × 22 mΩ = 17.7 kV/s, but the fixed ramp gives only 40 mV × 298 kHz = 11.9 kV/s. The design has no RSL (CS connects straight to the sense resistor), so subharmonic oscillation is expected at heavy load. That would make the 48 V rail ripple and its regulation unpredictable (E-03).
Fix (eq. 9 and 10, `design_calcs.txt`): add RSL between the R305/Q301 junction and CS. Re-balance RS, because RSL lowers the current limit:
- **RS = 18 mΩ with RSL ≈ 880 Ω (E96 887 Ω)** gives an 82 % optimal ramp and Ilim 4.0–4.9 A, so the T301 Isat ≥ 5 A spec is unchanged. Recommended.
- Keeping RS = 22 mΩ needs RSL ≈ 1.37 kΩ, but then Ilim(min) = 2.76 A, below the required peak. Rejected.
- RS = 15 mΩ with RSL 510 Ω gives Ilim up to 6.4 A, which means a bigger transformer.

An optional RF/CF filter at CS is shown in SNVSB75E Fig. 9-17. Confirm the values with TI's LM5155x design calculator once T301 is real.

### Already tracked, still critical
These are listed for completeness and are already in `UNRESOLVED_ISSUES.md`:
- T301 is a placeholder footprint and part, so the clamp and snubber values are provisional.
- The K-12 switched 48 V output (Q302/Q303) is not designed; R311 0 Ω bypasses it.
- The S-06 runaway cap is not enforced in hardware.

## 3. Major findings

| ID | Finding | Evidence | Fix |
| --- | --- | --- | --- |
| F-M1 (New) | Battery path from F101 to J102 (VBAT_FUSED) is a **0.2 mm** track carrying the full 2.1 A (E-05, L-4) | 26.9 mm × 0.2 mm ≈ 66 mΩ, so 0.14 V drop and 0.29 W at 2.1 A. IPC-2152 puts 0.2 mm/1 oz at roughly 0.7–0.8 A for a 10 K rise. With estimated cell, protection, fuse and switch resistances, VBAT at the ICs falls to about 3.03 V at the 3.4 V dosing cut-off. That eats the margin for E-02 (≥ 3.0 V) and the LM51551 BIAS minimum of 2.97 V | Make the F101→J102 path a pour or ≥ 1.0 mm on F.Cu, duplicated on B.Cu. Add VBAT_FUSED (and VBAT) to the PWR net class |
| F-M2 (New) | VBAT feed to the flyback primary: 0.2–0.3 mm tracks and only 3 VBAT vias within 10 mm of C302/C303/T301 | `pcb_check.txt` track summary; via count | Put a VBAT pour on F.Cu joining C302, C303 and T301.1. Use ≥ 6 vias to the In2 VBAT plane next to C302/C303 |
| F-M3 (New) | Secondary AC loop is large: C309/C310 (the 48 V ceramics) sit about 33 mm from D301 | C309 at (158.4, 142.7), D301 at (191.9, 159.5) | Place C309/C310 at the D301 cathode, returning straight to T301 pin 3. Keep C311 close as well. Re-check the D301 reverse voltage (simulated 92–98 V with a tight loop; 200 V part) |
| F-M4 (New) | R307 (470 k, FB top) is an 0603 with about 47 V across it: 94 % of a typical 50 V rating, failing E-06's 80 % rule | `design.py:233` uses FP_R | Use a 1206 (or larger) part with ≥ 150 V working voltage, or two series resistors (for example 2 × 232 k plus a trim), then re-run the tolerance stack (currently 46.6–49.4 V) |
| F-M5 (New) | TPS62840 inductor L201 uses an **0603** footprint. TI lists only 2016/2012 parts (DFE201612E, DFE201210S), and the high-side limit is 1.0–1.4 A, so an 0603 2.2 µH part would saturate | `design.py:162`; SLVSEC6D Table 2/4 | Use a 2016 footprint and Murata DFE201612E-2R2M (TI's reference) or an equivalent with Isat ≥ 1.4 A |
| F-M6 (New) | RF chain: the pi-match (C514/L502/C515) is at y = 132, below the MCU, while RF pin 37 is on the top edge (y = 115.6) and J501 is at y = 103.5. RF_ANT is 51 mm of 0.3 mm track with two vias, partly on B.Cu over the +3V3/VBAT plane. The PCB has **no stack-up**, so the impedance is undefined (P-06/L-6) | `pcb_check.txt`, pad coordinates | Move the match to within about 2 mm of pin 37 and J501 to within about 10 mm. Keep the RF on F.Cu only, over unbroken In1 GND, as a grounded coplanar line with a via fence. Define the stack-up in the board setup and size the 50 Ω width from it. Take the match from the ST reference once identified |
| F-M7 (New) | No pull-ups on ENC_A/B/I. The PMD401 normally supplies 10 k / ~20 k pull-ups on these inputs (manual 150025-01 §3.4), which suggests the LL06 outputs may be open-collector. If so, this board counts nothing. At the full 188 k counts/s, MCU internal pull-ups (~40 k) give 9–18 µs edges against 5.3 µs edge spacing | `design.py:388-404` | Add 10 k pull-up footprints to ENC_VCC on ENC_A, ENC_B and ENC_I (fit or DNP once the output type is confirmed). Choose low-capacitance TVS parts for these lines |
| F-M8 (New) | READY and FAULT fail unsafe. READY = 0 means "ready" and FAULT = 0 means "no error", so an unpowered PMD401 or an unplugged J702 reads as **ready, no fault** | PMD401 manual §3.5 | Add pull-up footprints to +3V3 on PMD_READY_M and PMD_FAULT_M (4.7–10 k, set against the PMD401's internal ~20 k at IF-02), so an open cable reads "not ready / fault". In firmware, trust READY only while FLY_PGOOD is high and after the PMD401 boot delay. Add a cable-unplug case to FT-05 |
| F-M9 (New) | E-07 is not met on RS-485: the PMD401 Data+/Data− lines (J704) have no TVS and no series resistor | `design.py:384, 407` | Add an RS-485-rated TVS array (asymmetric −7/+12 V class) at J704. 10–22 Ω series resistors are acceptable at 115.2 kbit/s. The PMD401 manual points to TI SN65HVD82 for the surge scheme |
| F-M10 (New) | A-14 claims "charging works with the switch off". With the switch off, +3V3 and the MCU are dead, so the BQ25188 runs at its reset ICHG (register 0x4 reset = 0x5, which the design note reads as 10 mA). Its I²C watchdog also resets registers to default whenever the host stops talking | SLUSFJ3 §7.3.8.7, §7.5.1.5 | Decide the charge procedure: charge with the master switch on, with firmware setting ICHG and servicing or disabling the watchdog (and 48 V held off while charging). Otherwise the owner approves a charger whose current is set by a resistor. Correct A-14 either way |
| F-M11 (New) | Net-class gaps. FLY_SNUB swings with FLY_SEC (up to ~100 V) but is in Default (0.15 mm), against L-3. SW48_GATE/SW48_DRV become 48 V nodes once Q302 is designed. VBAT, VBAT_FUSED, FLY_CS and GND have no power class, so new tracks default to 0.2 mm | `pump_v2.kicad_pro` netclass_patterns | Add FLY_SNUB, SW48_GATE and SW48_DRV to HV48. Add VBAT, VBAT_FUSED, FLY_CS and GND to PWR, with a width constraint in `.kicad_dru` for the battery path (for example `(constraint track_width (min 1.0mm))` on VBAT*) |
| F-M12 | E-11 (proposed): only the FB divider bleeds the 48 V rail, giving τ ≈ 72 s and 162 s to reach 5 V. R312 is DNP "TBD" | `design_calcs.txt` §6 | Fit R312 = 12 kΩ 2512: 5 V in 4.0 s, 0.19 W and 4 mA only while 48 V is on, which lowers the flyback headroom by 4 %. Needs owner sign-off of E-11 |
| F-M13 (New) | Every zone uses `connect_pads thru_hole_only`, so no SMD pad, including the U301 and U501 exposed pads and R305, is flooded. Each depends on a single track-and-via escape. Only 1 GND via lies within 6 mm of R305 | `pcb_check.txt` ZONES; via count | Use solid zone connection for GND on F.Cu in the power stage, or local pours. Put a via array (4–6 vias) under the U301 EP (SNVSB75E §10.5.1) and the WBA55 EP |
| F-M14 (New) | **Both BOMs are stale.** They predate design v2: they omit Q402, R405 (the AEN fail-safe), R313 and C312, still list the removed R404/R713, and show D301 as "D_TBD_100V", C304 as 1 µF and the compensation as TBD. Ordering from them would build the wrong safety circuit | `docs/bom.csv` 74 rows; `docs/bom_detailed.csv` | Regenerate both from the schematic (`kicad-cli sch export bom`) after the fixes, and add a design-vs-BOM check to `run_checks.sh` |
| F-M15 (New) | FLY_GATE runs 14 mm at 0.2 mm with a layer change. SNVSB75E asks for a "short, low inductance path" | track summary | Place Q301 within about 5 mm of U301 pin 3, keep the gate on one layer, and run PGND next to it |
| Tracked | No secondary OVP: an open R307 is an uncovered single fault, and LM51551 OVP (50.8–54.8 V) is above the PMD401's 50.4 V | U-23 | Second, independent divider and comparator, or a crowbar onto FLY_EN; owner decision |
| Tracked | BQ25188 WCSP footprint pitch unverified; XT30 pad polarity unverified; T301 placeholder footprint; no fab rule file or stack-up | U-12, U-16, U-20, U-04 | Read the TI YBG0008 and AMASS drawings and fix them before layout freeze |

## 4. Minor findings

| ID | Finding | Fix |
| --- | --- | --- |
| F-m1 (New) | WBA55 and C031 decoupling caps sit in rows 5–8 mm from the supply pins | Place each 100 nF at its pin with a direct via to In1 GND (after F-C2 fixes the values) |
| F-m2 (New) | MAX3485 /RE is tied to DE, so RO goes high-Z while transmitting and USART2_RX floats | Enable the PA11 internal pull-up, or add a 10–47 k pull-up on RS485_RO |
| F-m3 (New) | E-10 battery life is not computed. MAX3485 (always powered), the LL06 encoder on +3V3 (current unknown, and it must stay powered to keep the count), the LEDs and the BLE duty all count against it | Write the missing `requirements/power_budget.md` once the cell capacity (B.20) and encoder current are known |
| F-m4 (New) | Common-cause single fault: both MCUs share +3V3, so a shorted TPS62840 high-side FET puts up to 4.2 V on both, above their 3.6 V operating maximum | Add an OV detector whose open-drain output pulls FLY_EN low, or give the supervisor its own regulator; record it in the FMEA |
| F-m5 (New) | Test points are missing on VBUS_CHG, VBAT_FUSED, +48V_RAW, PMD_5V, ENC_VCC, SUP_PARK, MCU_48V_EN, HB_M2S and HB_S2M (P-07 proposed: "every rail and every safety signal") | Add 1 mm pads |
| F-m6 (New) | No reverse-polarity protection on J101 (XT30 is keyed, and the fuse blows through the body diodes) | Optional low-RDS(on) P-FET in the battery path, or rely on the keyed connector with a documented assumption |
| F-m7 (New) | No ESD protection on USB-C VBUS or CC | VBUS TVS (≥ 6 V standoff) and CC ESD diodes |
| F-m8 | 48 V on JST SH (J703) is at the connector family's voltage limit. It is the vendor's choice on the PMD401 side | Tracked U-17; confirm the JST rating |
| F-m9 (New) | The deliverables named in `CLAUDE.md` (`requirements_register.md`, `power_budget.md`, `component_sources.md`, `bringup_test_plan.md`, `release_report.md`) do not exist; similar content lives in upper-case files | Add the missing power budget and release report, or update `CLAUDE.md` to point at the existing files |
| F-m10 | CF-8: E-02 still says "LDO" while Rev B uses the TPS62840 buck | Owner wording change |

## 5. Checks that passed (independently verified)

- TPS62840DLC pinout (SLVSEC6D pin table) and VSET 267 k → 3.3 V (window 256–278 k). EN = VIN, MODE = GND (power-save), STOP = GND.
- LM51551 DSS pinout (Table 7-1). BIAS = VCC is allowed from 2.97 V. RT 73.2 k → 298 kHz (eq. 5). The DSS0012B land pattern matches the KiCad WSON-12 3 × 2, EP 1 × 2.65 footprint.
- Kill path: MCU high gives FLY_EN 2.47–2.78 V (> 1.575 V UVLO max); pull-down only gives 0 V; veto gives about 0 V (< 0.33 V EN falling min). UVLO hysteresis-current error is 4 mV. The veto default-ON (R403) and park default (Q402/R405) are in copper (P-05).
- 48 V DC set point 46.6–49.4 V with VREF ±1 % and 1 % resistors, inside 45.6–50.4 V with about 1 V each side for ripple and load step. Simulated ripple 53–68 mV p-p (electrolytic bulk reduced to 10 µF in the sim, so the real ripple is no worse).
- Steady-state flyback at 3.0 V in: 47.2 V, Ipk 3.4 A; D301 reverse voltage about 92–98 V on a 200 V part; clamp about 15 V with a tight layout.
- BQ25188 pinout (Table 5-1); BAT on VBAT_FUSED; SYS unloaded (E-09); 10 k TS/MR; I²C pull-ups 10 k.
- PMD401 servo (J701), status (J702), power (J703), RS-485 (J704) and encoder (J705) pinouts match manual 150025-01 §3.4/§3.5. SPI is mode 3 at ≤ 500 kbit/s.
- MCU pin functions: TIM2 CH1/CH2 encoder (PB6/PA8), SPI3 SCK/MOSI/NSS (PA0/PB8/PA5), USART2 TX/RX/DE (PB0/PA11/PB1), LPUART1 heartbeat (PB5/PA1, crossed correctly to C031 USART2 PA3/PA2), I2C3 (PA6/PA7), ADC4_IN10 on PB9 for VBAT_SENSE, SWD on PA13/PA14/PB3. C031: TIM3 CH1/CH2 on PA6/PA7, USART1 PA9/PA10, NRST on PF2.
- MAX3485 pinout; RS-485 polarity (A = Data+, B = Data−).
- No shorts; no clearance violations against the existing rules; no courtyard overlaps; continuous In1 ground plane; schematic = `design.py` = PCB.

## 6. Recommended fix order

1. Owner decisions that change parts or requirements: the F-C3 FET fallback, F-M10 charge procedure, F-M12/E-11, U-23 OVP, F-m4, F-m6. Also identify T301 and get the ST WBA55/C031 documents (F-C2).
2. Edit `scripts/design.py`, in a checkpoint commit first per rule 6:
   - F-C5: add RSL and set R305 to 18 mΩ;
   - F-M4: R307 package;
   - F-M5: L201 footprint;
   - F-M7: ENC pull-ups;
   - F-M8: READY/FAULT pull-ups;
   - F-M9: RS-485 TVS;
   - F-M12: R312 value;
   - F-m2: RO pull-up;
   - F-m5: test points;
   - F-C2: the WBA55 supply network once the ST data is in hand.

   Then update the net classes and the `.kicad_dru` (F-M11).
3. Regenerate the schematic, then run KiCad 10 ERC and read the report.
4. Re-place the power stage, RF and MCU decoupling (F-C3, F-C4, F-M1–M3, F-M6, F-M13, F-M15, F-m1). Define the stack-up. Then route to 0 unconnected (F-C1).
5. Run KiCad 10 DRC with `--schematic-parity`, re-run `scripts/review/*.py`, and re-simulate the flyback with the real T301 model and extracted loop inductances.
6. Regenerate both BOMs (F-M14) and update `docs/handover/UNRESOLVED_ISSUES.md` with the "New" items above.
