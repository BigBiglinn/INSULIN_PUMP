# Blocker-resolution report: pump_v2 Rev B digital handover

10 Oct 2026. Covers the board at commit `e8d141c`; the schematic and PCB were **not modified** while preparing this report. Sources:

- `validation/erc/pump_v2-erc.rpt`
- `validation/drc/pump_v2-drc.json`
- `validation/logs/unrouted_nets.txt`
- `validation/logs/unrouted_corridors.txt`, a new read-only analysis produced by `scripts/unrouted_corridors.py`
- `scripts/design.py`
- the STM32CubeMX 6.18.1 database
- the TI LM51551 datasheet, SNVSB75E (`docs/datasheets/lm51551.pdf`)

> Bench-only prototype for water or 0.9 % saline. Never connect it to a person or an animal, and never use real insulin. **The PCB is not fully connected and is not fabrication-ready.** A clean ERC/DRC result would not prove the circuit works.

**Evidence labels used below:**

- **[REPO]**: in the repository and read.
- **[DB]**: STM32CubeMX database.
- **[BOARD]**: measured on the current PCB file.
- **[NEED]**: not in the repository.
- **[APPROVAL]**: an engineering or owner decision.
- **[KNOWN-ID?]**: a document number recalled from general knowledge, which must be confirmed on st.com before use.

---

## 1. STM32WBA55CGUx: documents needed for the supply, clock and RF wiring

### 1.1 Pins affected (from [DB] `STM32WBA55CGUx.xml`)

| Pin | Name | Current net in design | Current state |
| --- | --- | --- | --- |
| 1 / 2 / 3 | VSSSMPS / VDDSMPS / VLXSMPS | GND / +3V3 / WBA_VLXSMPS | L501 (L_SMPS_TBD, 0805) from VLXSMPS to VDD11. Topology is **ASSUMED** |
| 45 | VDD11 | WBA_VDD11 | C509 = TBD. ERC error; 2 unrouted pairs |
| 38 | VDDHPA | WBA_VDDHPA | Fed through DNP R510 / C510 TBD. ERC error (routed, but it ends on DNP parts) |
| 39 | VDDANA | WBA_VDDANA | DNP R511 / C511 TBD. ERC error; 1 unrouted pair |
| 40 | VDDRF | WBA_VDDRF | DNP R512 / C512 TBD. ERC error; 1 unrouted pair |
| 43 | VDDRFPA | WBA_VDDRFPA | DNP R513 / C513 TBD. ERC error; 1 unrouted pair; 3 dangling vias |
| 41 / 42 | OSC_OUT / OSC_IN | HSE_OUT / HSE_IN | Y501 32 MHz (TBD part, 2016), with C516/C517 DNP. 4 unrouted pairs |
| 16 / 17 | PC15-OSC32_OUT / PC14-OSC32_IN | LSE_OUT / LSE_IN | Y502 32.768 kHz, with C518/C519 TBD. 2 unrouted pairs |
| 37 | RF | RF_MCU | C514 (DNP) – L502 – C515 (DNP) pi network to J501 U.FL. 1 unrouted pair |
| 8 | VDDA | +3V3 | Connected. Filtering/decoupling value still **ASSUMED** (A-7) |

### 1.2 Documents required

| # | Document | Status | What it resolves |
| --- | --- | --- | --- |
| ST-1 | **STM32WBA54xx/55xx datasheet** (DS14127 [KNOWN-ID?]), latest revision | [NEED] | <ul><li>Power-supply scheme: SMPS vs LDO mode, inductor value and current rating, VDD11 capacitance.</li><li>VDDHPA, VDDANA, VDDRF and VDDRFPA: whether each is a supply input or an internally generated output to decouple only.</li><li>Decoupling per pin.</li><li>HSE 32 MHz crystal requirements: ESR, CL, internal trim capacitors.</li><li>LSE requirements (gm_crit, CL).</li><li>RF pin impedance.</li><li>GPIO FT/5 V-tolerance (U-10) and ADC leakage (A-27).</li><li>Confirms the package and orderable suffix (A-1).</li></ul> |
| ST-2 | **RM0493**, STM32WBA5x reference manual | [NEED] | <ul><li>PWR chapter (SMPS/LDO selection, VDD11 domain).</li><li>RCC HSE trim registers.</li><li>BOOT0/PH3 option bytes (A-5).</li><li>TIM2 width (U-11).</li></ul> |
| ST-3 | **STM32WBA54xx/55xx errata sheet** (ES number to confirm) | [NEED] | Any silicon limitation on the SMPS, HSE or radio |
| ST-4 | **UM3301** (NUCLEO-WBA55CG, MB1803) plus the **MB1803 schematic and board files** | [NEED] (UM3301 is listed as a link only in `docs/SOURCE_DOCUMENTS.md`) | ST's own reference values: <ul><li>SMPS inductor part.</li><li>VDD11, VDDRF and VDDRFPA capacitors.</li><li>HSE crystal part and load.</li><li>RF matching/filter network and layout.</li></ul> This is the most direct source for L501, C509–C515 and L502 |
| ST-5 | ST application note on **RF hardware design for STM32WBA** (number to confirm; the STM32WB equivalent is AN5165 [KNOWN-ID?]) | [NEED] | <ul><li>RF trace, pi-match topology and harmonic filter.</li><li>Ground and via fencing.</li><li>Antenna keep-out.</li><li>50 Ω stack-up (U-20).</li></ul> |
| ST-6 | **AN2867**, oscillator design guide for STM32 [KNOWN-ID?] and/or **AN5042**, HSE trimming for STM32 wireless MCUs [KNOWN-ID?]; confirm that it covers WBA | [NEED] | Gain margin for the chosen crystals; whether C516/C517 are needed with the internal HSE trim |
| X-1 | Datasheets for the 32 MHz and 32.768 kHz crystals actually chosen (ideally from ST's qualified list in ST-4 or ST-6) | [NEED] | Values for Y501/Y502 footprints, CL and therefore C518/C519 |
| ST-7 | **STM32C031x4/x6 datasheet** (DS number to confirm) and **RM0490** [KNOWN-ID?]; NUCLEO-C031C6 user manual | [NEED] | <ul><li>U601 decoupling (A-7).</li><li>Package C6T6 vs C6U6 (A-2).</li><li>BOOT strap levels.</li><li>FT pins facing the PMD401 and encoder (U-10).</li></ul> |

**Status:** none of ST-1 to ST-7 are in `docs/datasheets/`. st.com is unreachable from this machine, so these documents must be supplied by the owner. The schematic or board design files for MB1803 alone would close most of section 1.1.

**What cannot be inferred:** none of the TBD values (inductor, capacitors, pi-match, load capacitors) or the treatment of VDDHPA/VDDANA/VDDRF/VDDRFPA may be set from memory or from other STM32 families. They stay PLACEHOLDER until ST-1 or ST-4 is read.

---

## 2. +48V_MOT path to J703, and FLY_SS / FLY_PGOOD

### 2.1 Intended connections (from `scripts/design.py`; values as labelled there)

```
T301.4 FLY_SEC ─ D301 (PNE20010ER) ─ +48V_RAW ─┬─ C309, C310 2.2 µF/100 V, C311 47 µF/100 V  → GND
   (snubber R313 220 Ω + C312 100 pF across D301)├─ R307/R308 470 k/10 k → FLY_FB (U301.8)
                                               ├─ R311 0 Ω (ASSUMED bypass of the undesigned switch)
                                               └─ Q302.2 (DNP placeholder, K-12 switch)
+48V_MOT ─┬─ R311.2 / Q302.3 (DNP)
          ├─ TP301
          ├─ R312 (DNP bleeder placeholder, E-11)
          ├─ C702 100 µF/100 V bulk (DECIDED, Rev A item 24)
          └─ J703.2  → PMD401 48 V input (J703.1 = GND)
FLY_SS:    U301.9 ─ C305 47 nF → GND          (tSS ≈ 4.7 ms, CALC)
FLY_PGOOD: U301.11 (open drain) ─┬─ R302 100 k → +3V3 (ASSUMED)
                                 ├─ TP302
                                 └─ U501.28 = PA12, GPIO input ([DB], pinmap_check OK)
```

### 2.2 Board state [BOARD]

Part positions:

| Part | Position (mm) |
| --- | --- |
| R311 | (190.8, 142.2) |
| TP301 | (169.5, 142.0) |
| R312 | (183.9, 143.0) |
| C702 | (196.5, 164.0) |
| J703 | (206.5, 148.0); pad 2 at (204.5, 147.5) |
| Q302 (DNP) | (160.4, 179.6) |
| C305 | (163.8, 146.5) |
| U301 | (164.0, 152.0) |
| R302 | (163.8, 157.5) |
| TP302 | (197.5, 145.0) |

What the DRC reports:

- **+48V_MOT** is split into two copper islands, the R311/TP301 island and the C702 island. **Neither reaches J703.2**, so the PMD401 currently has no 48 V feed on the PCB. The gaps are 13.3 mm and 19.9 mm.
  - The straight F.Cu path from R311 is crossed by D302, TP302, a J703 pad and a FLY_SW track.
  - The B.Cu corridor from C702 to J703 has no foreign tracks or pads. The likely blocker is therefore the HV48 clearance (0.6 mm) at the J703 pad entry: 1.0 mm-pitch JST SH, with GND pour and mounting pads adjacent. The scoped DRU rule only relaxes clearance *between J703's own pads*.
- **FLY_SS:** C305 sits on the opposite side of U301 from pin 9 (6.1 mm gap). The path crosses U301 pads and the FLY_FB/FLY_RT/FLY_EN/FLY_COMP_RC/FLY_PGOOD tracks.
- **FLY_PGOOD:** U301.11–R302 is connected. U501.28 (33.8 mm away) and TP302 (31.8 mm away, placed near J703) are not.

### 2.3 Datasheet evidence for these circuits

| Item | Evidence | Finding |
| --- | --- | --- |
| SS pin | [REPO] SNVSB75E pin table; ISS 9–11 µA; abs max SS 3.8 V | "Connect the ground connection of the capacitor to AGND"; the layout guideline says connect CSS to AGND. C305 47 nF gives 4.3–5.2 ms over the ISS range (CALC). **The electrical design is supported; only placement is wrong.** |
| PGOOD pin | [REPO] SNVSB75E §9.3.9 and abs max footnote 4 | Open drain. "Recommended minimum pullup resistor value is 10 k". Pin voltage ≤ VBIAS + 0.3 V; sink limited to 1 mA when VPGOOD > VBIAS. With BIAS = VBAT ≥ 3.0 V in operation, a 3.3 V pull-up meets the limit. R302 = 100 k (≥ 10 k) keeps any diode-path current ≤ 33 µA. **Supported by existing evidence.** Open point: behaviour when VBAT < 3.0 V while +3V3 is still present (TPS62840 dropout region). That review needs no new document. |
| PGOOD as an MCU input | ST-1 [NEED] | PA12 input thresholds and FT rating: not verified (U-10) |
| J703 / PMD401 input | [REPO] PMD401 manual §3.4: 48 VDC ±5 %, 5 W | About 0.1 A. Low current, but HV clearance applies |
| JST SM02B-SRSS-TB voltage/current rating | **[NEED]** JST SH datasheet | U-17: whether a 1.0 mm-pitch SH connector is acceptable at 48 V (and up to the 54.2 V OVP ceiling) |
| C702, C311 series and ratings | **[NEED]** (series TBD in the design) | Ripple current, ESR, footprint confirmation |
| Q302/Q303 switch, R312 bleeder | **[APPROVAL]** U-06 (no part chosen) | Placeholders; Q302 is placed at (160, 180), **far from the R311 → J703 path**. If the switch is designed in, it must move next to R311 |

---

## 3. Unconnected nets, grouped by circuit

Endpoints are taken from `validation/drc/pump_v2-drc.json`. "Blocked by" comes from `validation/logs/unrouted_corridors.txt`. All gaps are ≥ 5.7 mm, so none is a false positive.

### 3a. Requires ST documents (group A, 12 pairs; do not route until section 1 is closed)

| Net | Endpoint 1 | Endpoint 2 | Reason blocked |
| --- | --- | --- | --- |
| WBA_VDD11 ×2 | U501.45 | L501.2; C509.1 | Topology and values unverified; congested U501 fan-out (+3V3, NRST, SWO, RF_ANT, VDDHPA tracks) |
| WBA_VDDANA | U501.39 | track stub near C502 (138.5, 131.0) | Pin function unverified (input or decoupled output); 19 mm detour |
| WBA_VDDRF | U501.40 | track stub (142.5, 131.1) | As above |
| WBA_VDDRFPA | U501.43 | track stub (148.8, 128.7) | As above; 3 dangling vias on this net |
| HSE_IN ×2 | U501.42 | Y501.1; C516.1 | Y501 is 9.4 mm from the pins and C516/C517 are 18 mm away. Crystal placement must be redone to ST guidance |
| HSE_OUT ×2 | U501.41 | Y501.3; C517.1 | As above |
| LSE_IN ×2 | U501.17 | Y502.1; C518.1 | Y502 and C518 are on different sides of U501 (16 mm each) |
| RF_MCU | U501.37 | stub at the pi network (149.5, 132.0) | 16.5 mm RF run through the decoupling area. Needs the ST RF layout and stack-up (U-20) |

### 3b. DNP placeholder only (group B, 1 pair)

| Net | Endpoints | Reason |
| --- | --- | --- |
| SW48_GATE | R309.1 (193.2, 144.8) ↔ R310/Q302 stub (171.5, 147.0) | Undesigned output switch (U-06). Q302 is placed 35 mm away from R309 |

### 3c. Genuine functional connections (group C, 22 pairs)

| Circuit | Net | Endpoint 1 | Endpoint 2 | Gap | Reason blocked | Needs |
| --- | --- | --- | --- | --- | --- | --- |
| **48 V output** | +48V_MOT | R311.2 island (192.3, 142.2) | J703.2 | 13.3 | D302, TP302, a FLY_SW track; HV48 0.6 mm at J703 | Layout; JST rating [NEED] |
| | +48V_MOT | C702 island (195.3, 165.2) | J703.2 | 19.9 | B.Cu corridor clear; HV clearance at the J703 pad entry and GND pour | Layout; CF-6 clearance interpretation [APPROVAL] |
| **Flyback control** | FLY_SS | C305.1 | U301.9 | 6.1 | C305 on the wrong side of U301 | Placement only (evidence in repo) |
| | FLY_PGOOD | U501.28 (PA12) | U301.11 | 33.8 | Crosses U501 and HSE area, C309, flyback tracks | Routing; better after the WBA re-layout |
| | FLY_PGOOD | U301/R302 stub | TP302 | 31.8 | TP302 placed near J703, across the flyback stage | Move TP302 (placement) |
| **Power/charger (U101 BQ25188, YBG WCSP)** | VBAT_FUSED | U101.C2 | C102.1 | 7.2 | U101 balls and CHG_SYS/CHG_TS/I2C_SCL tracks; WCSP escape | Footprint pitch unverified (U-12) |
| | CHG_INT_N | U101.A1 | stub (109.0, 119.9) | 11.6 | WCSP escape; USB_CC/VBUS tracks | U-12 |
| | I2C_SDA | U101.C1 | R105.1 | 12.4 | WCSP escape | U-12 |
| | I2C_SDA | R105.1 | U501.6 | 19.3 | U501 fan-out, Y501 | Routing |
| | VBAT_SENSE | stub (117.7, 125.3) | stub (145.7, 124.4) | 28.0 | R108, TP101/102; VBAT/VBAT_FUSED tracks | Routing; ADC leakage check (ST-1) |
| **Supply** | +3V3 | via (147.2, 159.5) | stub (164.6, 157.5) | 17.6 | U601 pads, 9 signal nets on F.Cu | Routing (could use the In2 +3V3 plane via) |
| **Main MCU (U501) signals** | MAIN_SWCLK | B.Cu stub (145.1, 124.2) | U501.26 | 7.0 | U501 fan-out; dangling track | Routing |
| | PMD_SCLK_M | U501.13 | R704.1 | 36.3 | 16 nets crossed (U501 escape plus encoder area) | Routing / placement |
| | PMD_MOSI_M | B.Cu stub (151.1, 123.3) | R702.1 | 26.0 | 10 nets on F.Cu, 6 on B.Cu | Routing |
| | PMD_READY_M | U501.33 | R706.1 | 36.3 | R705, R710–R712, PMD_AEN tracks | Routing |
| | ENC_I_M | U501.48 | stub (160.1, 118.7) | 15.1 | U501 fan-out; dangling via | Routing |
| **Supervisor (U601) signals** | ENC_A_S | U601.17 (PA6) | R711.1 | 60.9 | Board-length run across the flyback (+48V_RAW, C304, C309) | Placement of R711/R712 next to U601 |
| | CON_SUP_TX | J503.3 | U601 stub (152.6, 159.0) | 55.7 | J503 is at the top edge and U601 at the bottom; crosses the U501 area | Placement of J503 near U601 |
| | CON_SUP_RX | U601.32 | J503.4 | 56.2 | As above | As above |
| **PMD401 / encoder interface** | ENC_I | J705.1 | stub (182.4, 106.2) | 41.6 | Runs along the RS-485/encoder connector row | Routing / placement |
| | ENC_VCC | stub (171.8, 104.3) | stub (187.1, 108.7) | 15.9 | PMD_5V, PMD_* signal tracks | Routing |
| | RS485_B | R714.2 (DNP termination) | J704/U701 stub (194.5, 129.4) | 21.2 | U701 pads | Routing (the U701–J704 segment is already connected) |

**Main systemic causes [BOARD]:**

1. U501 fan-out congestion, a 0.5 mm-pitch QFN48 with the WBA placeholders packed around it.
2. Long cross-board links caused by connector and resistor placement (J503 vs U601, and R711/R712 vs U601).
3. The flyback block sitting between the MCUs and the PMD401 connectors.

This is why the DRC-gated hand router rejected every candidate except two. Most group-C items need **placement changes in `gen_pcb.py`**, not only routing.

---

## 4. ERC errors, DRC warnings and flyback-layout decisions

### 4.1 ERC (`validation/erc/pump_v2-erc.rpt`: 6 errors, 1 warning)

| Item | Cause | Resolution path |
| --- | --- | --- |
| 6 × `power_pin_not_driven` on U501 pins 3, 45, 39, 38, 40 and 43 | Intentional: those nets end on placeholder or DNP parts | Wire per ST-1/ST-4. **No PWR_FLAG will be added to hide them** |
| 1 × `lib_symbol_mismatch` warning on U701 (MAX3485) | Embedded symbol differs from the installed library copy | *Update Symbols from Library*, or regenerate. A cosmetic schematic edit, resolvable from existing evidence. Needs permission because it touches the schematic |

### 4.2 DRC (`validation/drc/pump_v2-drc.json`)

- 0 copper violations; 0 schematic-parity issues.
- 35 unconnected pairs (section 3).

| Warning | Count | Detail | Resolution |
| --- | --- | --- | --- |
| via_dangling | 8 | VBAT_SENSE (145.4, 124.7); ENC_VCC (171.8, 104.4); WBA_VDDRFPA ×3 (155.6, 128.5 / 160.7, 128.6 / 148.8, 113.5); CON_SUP_TX (152.6, 159.0); PMD_MOSI_M (158.0, 123.5); ENC_I_M (160.1, 118.7) | Router leftovers on unfinished nets. Remove or reuse during routing |
| track_dangling | 1 | MAIN_SWCLK B.Cu 0.78 mm stub (145.1, 124.2) | Same as above |
| silk_overlap / silk_over_copper | 75 / 55 | Mostly R309, D707–D709, C514–C517, D501, R704/R705, TP302 | Silkscreen clean-up after final placement |
| silk_edge_clearance | 3 | Reference fields of J501, J102 and D704 at the board edge | Move the reference text |
| nonmirrored_text_on_back_layer | 2 | B.Silk disclaimer texts | Mirror the text (gen_pcb). Keep the wording |

### 4.3 Flyback-layout decisions (findings from the current placement [BOARD] against SNVSB75E §10.5.1 [REPO])

| # | Finding | Guideline | Decision needed |
| --- | --- | --- | --- |
| FL-1 | **Clamp loop is long.** The D302 clamp diode is at (196.3, 142.1) and C308 at (190.2, 145.0), about 30 mm from the Q301 drain/T301 FLY_SW (171–180, 156–160). R306 is at (175.4, 143.0) | Leakage energy must be clamped in a minimal loop (FLY_SW → D302 → C308 → VBAT) | Move D302/C308/R306 next to T301 pin 2 and Q301. Layout change, **approval to modify the PCB** |
| FL-2 | **Secondary/output loop is long.** C309/C310 (ceramic COUT) are at x ≈ 160–165, while D301 is at (190.5, 159.5) and T301 secondary return pin 3 is at (180, 156) | "Make the switching loop (COUT to D1 to Q1 to RS to COUT) as small as possible"; "Use a small size ceramic capacitor for COUT" | Move C309/C310 next to the D301 cathode and the T301 return |
| FL-3 | AGND and PGND are a single `GND` net (U301 pins 4, 7, 13) | "Connect the AGND pin to the RUVLOB, RT, CSS, RFBB components"; PGND straight to the RS centre; exposed pad joins them under the device | Keep a single net with a local AGND copper island (net-tie), or a solid plane only. **[APPROVAL]** |
| FL-4 | Transformer footprint is a 12 × 12 mm placeholder (U-04) | — | Final loop geometry cannot be fixed until T301 is chosen. **[APPROVAL] and [NEED] transformer datasheet** |
| FL-5 | D301 thermal copper | "Leave a copper area near the D1 diode for thermal dissipation" | Size after U-19 thermal estimate |
| FL-6 | HV48 clearance 0.6 mm on all layers (A-20, CF-6 unresolved); J703 1.0 mm pitch | IPC-2221 interpretation | **[APPROVAL]**: confirm the clearance rule and connector suitability (U-17) |
| FL-7 | Q302 placeholder far from the output path | — | Decide U-06 (design the switch, or delete the placeholders and keep R311) **[APPROVAL]** |
| FL-8 | Secondary OVP (U-23); 54.2 V OVP ceiling exceeds the PMD401's 50.4 V | — | **[APPROVAL]**: add a clamp/crowbar or a redundant divider, which affects layout space near +48V_RAW |
| FL-9 | Autorouted flyback copper is not final | — | Re-route the flyback by hand after FL-1 to FL-4 |

---

## 5. What can be resolved from existing evidence, and what cannot

| Category | Items | Evidence | Still needs |
| --- | --- | --- | --- |
| **A. Resolvable now from repo evidence (layout only, no electrical change)** | <ul><li>FLY_SS (move C305 to pin 9).</li><li>FLY_PGOOD (route; move TP302 near U301).</li><li>FL-1 and FL-2 loop compaction.</li><li>Dangling vias and track.</li><li>Silkscreen, edge text and mirrored text.</li><li>Supervisor links: move J503 and R711/R712 near U601.</li><li>+3V3, ENC_VCC, ENC_I, RS485_B, PMD_* signal routes.</li><li>+48V_MOT routing *geometry*.</li></ul> | SNVSB75E pin table and §10.5.1; netlist; DRC | Your permission to modify `gen_pcb.py` placement and the PCB |
| **B. Resolvable now, schematic-side** | U701 `lib_symbol_mismatch` | ERC | Permission to touch the schematic (cosmetic) |
| **C. Needs ST documents** | <ul><li>Group A (12 pairs).</li><li>6 ERC errors.</li><li>Placement of Y501, Y502, L501 and the pi network.</li><li>VDDA filter.</li><li>U601 decoupling.</li><li>U-10 pin tolerance.</li><li>A-27 ADC leakage (VBAT_SENSE).</li><li>A-5 BOOT0.</li><li>U-11.</li></ul> | — | ST-1 to ST-7 (section 1.2) |
| **D. Needs other datasheets** | <ul><li>JST SM02B-SRSS-TB rating (+48V_MOT, U-17).</li><li>BQ25188 YBG0008 mechanical drawing, read by a person (U-12): the PDF is in the repo but the drawing is not machine-readable here, and it governs the VBAT_FUSED, CHG_INT_N and I2C_SDA escape.</li><li>Transformer (U-04).</li><li>C702/C311 series.</li><li>Crystal datasheets.</li></ul> | — | Supplied PDFs or a manual read |
| **E. Needs engineering approval** | <ul><li>U-04 transformer choice.</li><li>U-06 output switch/bleeder (FL-7).</li><li>U-23 secondary OVP (FL-8).</li><li>FL-3 grounding strategy.</li><li>FL-6 / CF-6 HV clearance rule.</li><li>U-24 input current budget.</li><li>U-16 fab choice and stack-up (also sets the RF 50 Ω width, U-20).</li></ul> | — | Owner decision |

**Sequencing recommendation:** do category C before the heavy routing around U501. The WBA55 placeholders (Y501, Y502, L501, C509–C519) occupy the area that blocks most group-C signal nets, so routing those nets first would be redone once the ST layout is applied. Category A flyback and connector work (FL-1, FL-2, FLY_SS, FLY_PGOOD, the J503/R711/R712 moves) is independent of the ST documents and could proceed first **once you approve PCB modifications**.

A staged routing plan, with checks after each batch, will be proposed once the blockers above are resolved, as requested.
