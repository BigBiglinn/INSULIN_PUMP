# Assumptions and deviations: Rev B digital handover design

Date: 10 Oct 2026. Applies to `hardware/kicad/pump_v2.*` generated from `scripts/design.py`.

**This is a bench-only digital handover prototype, used with water or 0.9 % saline only and never connected to a person or an animal. It is not fabrication-approved and has not been validated.**

Each component carries a `Status` field (schematic, BOM and PCB) with one of these values:

- `DECIDED`: locked in the handoff documents
- `DS`: taken from a cited datasheet
- `CALC`: calculated
- `ASSUMED`: listed below
- `TBD`: part or value open
- `PLACEHOLDER`: block not designed

## 1. Deviations from the handoff documents

| # | Deviation | Source it departs from | Authority |
| --- | --- | --- | --- |
| DV-1 | Digital Rev B design started before any Rev A bench validation | K-7 / U-6 sequencing ("Rev A before Rev B") | Owner, 10 Oct 2026 (new objective). Fabrication is still gated by Rev A results |
| DV-2 | INA219 current monitor not carried to Rev B | P-01 ("Rev B carries the Rev A circuit"); Rev A item 18 | Owner, 10 Oct 2026. S-13 VBAT sensing is OPEN (R107/R108/C104 DNP placeholder) |
| DV-3 | Supervisor gate default: both 10 k options (R403 pull-up, R404 pull-down) placed, both DNP | K-10 as wired on Rev A (pull-down fitted) | Owner, 10 Oct 2026 (left unresolved) |
| DV-4 | Kill network drives LM51551 UVLO/EN instead of a Pololu EN pin | K-10 was defined on the Rev A Pololu U3V70F12 | Follows K-12 (LM51551 decided). Same resistor values; thresholds re-checked against TI SNVSB75E (sheet "Kill path") |
| DV-5 | K-12 "switched output" not designed: Q302/Q303/R309/R310 are DNP placeholders, and R311 (0 R) bypasses the switch | K-12 | Owner, 10 Oct 2026 |
| DV-6 | 4-layer stack-up adopted | P-02 was PROPOSED | Owner approved, 10 Oct 2026 |
| DV-7 | Encoder A/B also routed to the supervisor (TIM3) through R711/R712 | S-07 was PROPOSED | Owner approved, 10 Oct 2026 |
| DV-8 | MAX3485 RS-485 transceiver placed on Rev B | Not on the Rev B parts list | Carried from Rev A item 9 under P-01; needed for PMD401 servo-mode setup (`X0Y13,3`, `X0Y32`) |
| DV-9 | Rev A bulk capacitors carried to Rev B (C301 220 µF/16 V, C311 47 µF/100 V, C702 100 µF/100 V) | The Rev B list does not mention them | P-01 carry-over; adequacy for the flyback is TBD |
| DV-10 | Status LEDs D501/D601, test points, console header J503 and SWD headers J502/J601 added | Not in any parts list | Bring-up/debug aids; P-07 (test points) was PROPOSED. Removable without circuit impact |

No locked component (K-3 to K-6, K-9 Rev A parts, K-12 Rev B power parts) was substituted. No prohibited part (HARDWARE_CONSTRAINTS section 2) is used.

## 2. Engineering assumptions

| # | Assumption | Where | How to close |
| --- | --- | --- | --- |
| A-1 | STM32WBA55CG package is UFQFPN48 (the only "CG" package in the ST pin data shipped with KiCad). Temperature suffix (U6/U7) open | U501 | Confirm against the ST datasheet / orderable list |
| A-2 | STM32C031C6 package is LQFP48 (C6T6). The C6U6 (UFQFPN48) also exists | U601 | Owner / NUCLEO-C031C6 user manual |
| A-3 | MCU pin assignment derived from ST alternate-function data in the KiCad 10 symbols (table in `HANDOVER_GUIDE.md`) | U501, U601 | Re-create in STM32CubeMX and check against the datasheets before layout freeze |
| A-4 | C031 NRST is on PF2 (PF2-NRST) and BOOT0 is shared with PA14 | U601 | ST datasheet |
| A-5 | WBA55 PH3 doubles as BOOT0; 10 k pull-down boots from flash | R501 | ST datasheet |
| A-6 | WBA55 SMPS topology is VLXSMPS → inductor → VDD11. VDDHPA, VDDANA, VDDRF and VDDRFPA connections are unknown (DNP 0 R links to 3V3) | L501, C509–C513, R510–R513 | ST datasheet. These cause the 6 ERC errors on purpose |
| A-7 | Decoupling 100 nF per supply pin plus 4.7 µF bulk on both MCUs; 100 nF on NRST | C501–C508, C601–C604 | ST datasheets |
| A-8 | 32 MHz HSE crystal in a 2016 package, with load capacitors DNP (internal trim assumed) | Y501, C516, C517 | ST RF reference design (not identified, OPEN B.24) |
| A-9 | TPS62840 orderable variant is DLC (SON-8) and VSET 267 k gives 3.3 V. MODE = GND (auto PFM/PWM), STOP = GND, EN tied to VIN | U201, R201 | TI SLVSEC6D VSET table (value confirmed); variant is the owner's choice (B.12) |
| A-10 | LM51551 uses BIAS = VCC = VBAT (1S start ≥ 2.97 V). Gate drive is therefore VBAT, so Q301 must be logic-level | U301, Q301 | TI SNVSB75E section 1; FET selection TBD |
| A-11 | FB divider 470 k / 10 k sets 48.0 V nominal (VREF 1 V ±1 %) | R307, R308 | Calculation; tolerance stack vs 45.6–50.4 V not done |
| A-12 | BQ25188 YBG ball pitch is 0.4 mm (inferred from the 1.1 × 1.6 mm body; drawing not text-extractable) | U101 footprint `TI_YBG0008_DSBGA-8_P0.4mm_UNVERIFIED` | TI YBG0008 mechanical drawing |
| A-13 | BQ25188 TS/MR has a fixed 10 k to GND as an NTC stand-in (pack NTC unknown). TS/MR held low for long enough enters ship mode | R101 | Pack definition (B.20); or disable TS via TS_EN |
| A-14 | Charger connects to VBAT_FUSED (after the fuse, before the master switch), so charging works with the switch off. Load is on VBAT; BQ25188 SYS is unloaded (E-09) | sheet "Power input" | Owner review |
| A-15 | Battery connector XT30PW-M (Rev A style); USB-C power-only receptacle (GCT USB4125) with 5.1 k Rd for the charger input; master switch is off-board on a 5.08 mm terminal | J101, J102, J103 | B.19, B.20 |
| A-16 | LL06 encoder connector J705 mirrors the PMD401 sensor connector (pin 1 I+, 2 GND, 3 5 V, 4 B+, 5 A+, 6 screen), so the kit encoder cable plugs in | J705 | Check against the delivered cable |
| A-17 | Encoder powered from 3V3 by default (JP701 bridged 1-2). PMD401 5V Out is the alternative and dies with the 48 V rail | JP701 | LL06 datasheet supply range (OPEN item 12) |
| A-18 | TVS: 5 V-class, SOD-323, part TBD; series resistors 100 R | D701–D709, R702–R712 | OPEN B.15; IF-02 measurement |
| A-19 | Edge-connector orientation derived from footprint geometry (body vs pads), not from connector drawings | J101–J103, J701–J705 | Check each footprint against the connector drawing |
| A-20 | Generic 4-layer rules: 0.15 mm track/space, 0.3 mm drill / 0.5 mm via, 0.3 mm copper-to-edge. HV48 net class 0.6 mm clearance on all layers (conservative reading of P-03; CF-6 unresolved) | `pump_v2.kicad_pro` | Fab rule file (B.7); IPC-2221C table |
| A-21 | Board 110 × 78 mm, 4 × M3 holes. Size is not set by any requirement (B.6) | PCB | Enclosure / mechanical design |
| A-22 | Default KiCad 4-layer 1.6 mm stack-up. RF trace is not impedance-controlled (U.FL is next to the MCU) | PCB | Fab stack-up; 50 Ω calculation |

## 3. Data sources used in this session

| Document | Revision | File |
| --- | --- | --- |
| PiezoMotor PMD401 Technical Manual | 150025-01 (downloaded from the `/2026/03/` path; the `/2019/03/` link in SOURCE_DOCUMENTS returns HTML) | `docs/datasheets/PMD401_150025_Technical_Manual.pdf` |
| TI LM5155/LM51551 | SNVSB75E, Aug 2023 | `docs/datasheets/lm51551.pdf` |
| TI BQ25188 | SLUSFJ3, Nov 2024 | `docs/datasheets/bq25188.pdf` |
| TI TPS62840 | SLVSEC6D, Mar 2020 | `docs/datasheets/tps62840.pdf` |
| TI INA219 | (downloaded; not used after the owner dropped the INA219) | `docs/datasheets/ina219.pdf` |
| ST STM32WBA55CG / STM32C031C6 datasheets, UM3301 | **not obtained**: st.com unreachable from this machine | — |
| KiCad 10.0.3 libraries | STM32 symbols (ST pin data), footprints | installed library |
