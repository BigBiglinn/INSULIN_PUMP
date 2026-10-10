# Unresolved issues: Rev B digital handover design

Date: 10 Oct 2026. Severity:

- **Critical**: blocks any fabrication, or is a safety-function gap.
- **Major**: the board will not work as intended until it is resolved.
- **Minor**: documentation, cosmetic or optimisation.

IDs in brackets refer to `requirements/OPEN_QUESTIONS.md`. None of these is resolved by the design files; each has a clearly marked placeholder.

## Critical

| ID | Issue | Placeholder in design | Needed to close |
| --- | --- | --- | --- |
| U-01 | Supervisor veto gate default is undecided (item 3 / CF-9). With neither R403 nor R404 fitted the BSS138 gate floats while the C031 is in reset or unpowered | R403 (pull-up) and R404 (pull-down), both DNP | Owner decision, then SG-03 on hardware |
| U-02 | PMD401 AEN has an internal 22 k pull-up (manual 150025-01 section 3.5), so a dead supervisor leaves the motor **enabled** (item 4) | R713 DNP, value TBD | IF-02 measurement of the pull-up rail, a pull-down value, then SG-05 |
| U-03 | Speed cap exists only in main-MCU firmware (item 2, S-06). The supervisor now sees the encoder (S-07), but no hardware rate limit exists | Firmware task | PiezoMotor answer on a stored rate limit, or a supervisor rate check plus FT-02 |
| U-04 | 48 V flyback power stage is not designed: transformer, FET, rectifier, sense resistor, RCD clamp, RT, SS and compensation are all TBD (B.16). Output voltage is set (470 k/10 k) but regulation, ripple and 60 V fault ceiling (E-11) are unverified | T301 / Q301 / D301 / D302 / R301 / R303 / R305 / R306 / C305–C308 with TBD values; transformer footprint is a 12 × 12 mm PLACEHOLDER | Flyback design (TI WEBENCH / SNVSB75E section 10), then transformer footprint, then simulation (LTspice is available) |
| U-05 | STM32WBA55 power and RF pins not wired from the datasheet: SMPS inductor, VDD11, VDDHPA, VDDANA, VDDRF, VDDRFPA, decoupling, HSE load, RF matching | L501, C509–C515, R510–R513 (DNP), L502, Y501. **These are the 6 ERC errors** | ST STM32WBA55CG datasheet + ST RF/hardware design guide (AN for WBA) — st.com was unreachable in this session |
| U-06 | K-12 "switched output" and E-11 discharge are not designed | Q302/Q303/R309/R310/R312 DNP; R311 0 R bypass fitted | High-side switch design ≥ 100 V class, bleeder value |
| U-07 | Battery-voltage sensing for the S-13 3.4 V stop is not defined after the INA219 was dropped | R107/R108/C104 DNP divider on PB9 (ADC4_IN10) | Owner choice: divider (with switched low side for Iq) or a monitor IC |

## Major

| ID | Issue | Needed to close |
| --- | --- | --- |
| U-10 | Both MCU pin maps are derived, not CubeMX-verified (A-3). 5 V tolerance of every pin facing the PMD401/encoder is unconfirmed (PMD401 pull-up rail unstated) | CubeMX project, ST datasheet FT column, IF-02 |
| U-11 | WBA55 TIM2 width (32-bit?) unconfirmed (CF-21); firmware must extend if 16-bit (FW-08) | RM0493 |
| U-12 | BQ25188 footprint pitch inferred (A-12) | TI YBG0008 drawing, then fix the footprint |
| U-13 | BQ25188 TS/MR handling and charge current not set (A-13, B.19); risk of unintended ship mode | Pack definition, firmware I²C init |
| U-14 | Encoder supply voltage and cable pinout unverified (A-16, A-17, item 12) | LL06 datasheet, delivered cable, MT-08 |
| U-15 | TVS parts not chosen; SPI clock edge integrity through TVS + 100 R not checked (IF-03/IF-04) | Part selection, scope checks |
| U-16 | No fab selected; rules are generic (A-20). HV48 spacing 0.6 mm everywhere is conservative, but CF-6 is open | Fab rule file, IPC-2221C table |
| U-17 | Connector orientations derived heuristically (A-19); JST SH 1 mm contact current rating for the 48 V lead not confirmed | Connector drawings |
| U-18 | Battery connector, cell, fuse part, master switch part and charger input connector not decided (B.19, B.20) | Owner |
| U-19 | No thermal or power calculations for the flyback / FET / transformer (CLAUDE.md Phase 5) | After U-04 |
| U-20 | RF trace not impedance-controlled; U.FL placed next to the MCU | Stack-up, 50 Ω coplanar geometry, ST reference |
| U-21 | **PCB routing incomplete:** 63 unconnected items on 55 nets after autorouting, plus 10 dangling vias and 3 starved thermals (`validation/logs/unrouted_nets.txt`). Autorouted tracks have not been reviewed for loop area, current capacity or signal integrity | Hand-route the remainder in pcbnew. Re-route the flyback power loop and the 48 V path by hand once U-04 is designed |
| U-22 | Freerouting ran with its default telemetry and analytics enabled for the first runs in this session (disabled afterwards). Board data was processed locally; whether anonymous usage statistics were sent was not verified | Note only; disable telemetry in `freerouting.json` before any reuse |

## Minor

| ID | Issue |
| --- | --- |
| U-30 | ERC warning `lib_symbol_mismatch` on U701 (MAX3485): the generator's flattening of the derived library symbol differs cosmetically from KiCad's. Fix: in Eeschema, Tools → Update Symbols from Library (U701 only) |
| U-31 | Schematic drawn label-style (every pin has a net label, few wires). Electrically complete, but a human redraw would read better |
| U-32 | Silkscreen reference/value text overlaps on dense areas; cosmetic, check before any fab |
| U-33 | Silkscreen overlaps (65), silk over copper (47), unmirrored bottom text (2): cosmetic DRC items |
| U-34 | Many vendor datasheets still missing (SOURCE_DOCUMENTS.md section 4): LL06, MAX3485, BSS138, connectors, Molicel cell |
