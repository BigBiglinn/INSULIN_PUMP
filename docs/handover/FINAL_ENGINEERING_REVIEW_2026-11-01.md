# Final engineering review: Piezo Insulin Pump v2 Rev B (digital design)

> **Later update (completion session, 1 Nov 2026).** Part 3's two "routable immediately" items are now routed (22 unconnected). C305 was corrected to 2.2 µF, and new findings U-39 to U-44 were added. The owner-decision list in §4.2 is superseded by `OWNER_APPROVAL_SHEET.md` (17 decisions). In §2.4, the runaway timing uses a 1 ms detection; the worst case is 2 ms (0.30 U), see `validation/logs/runaway_timing.txt`.

| | |
| --- | --- |
| Date | 1 Nov 2026 |
| Reviewed state | Commit `b3734aa` (board/schematic unchanged since `ef091c3`) |
| Scope | Audit of `docs/report/PROJECT_ENGINEERING_REPORT.md`; decision proposals for the eight remaining critical issues; classification of the 24 unconnected items; status towards fabrication |
| Design changes made by this review | **None to the schematic or PCB.** Documentation corrections only |

> Bench-only prototype: water or 0.9 % saline, never on a person or an animal, no real insulin. **This design is not fabrication-ready.** Every proposal below needs the owner's approval before it is implemented.

**Evidence labels**

| Label | Meaning |
| --- | --- |
| [DS] | Datasheet in `docs/datasheets/`, text read in this review |
| [REPO] | Project document |
| [CALC] | Recomputed by `scripts/audit_calcs.py` (output: `validation/logs/report_audit_calcs.txt`) |
| [SIM] | Open-loop simulation |
| [KiCad] | kicad-cli 10.0.4 in CI |
| [ROUTER] | `scripts/pcbroute.py` trial on a scratch copy; not applied |
| [WEB-2ND] | Web search summary or distributor page, not the manufacturer's document |

The network policy still blocks st.com, ti.com, jst-mfg.com, coilcraft.com and molicel.com. Checked 1 Nov: no response from any of them.

---

## Part 1. Audit of the engineering report

### 1.1 Corrections made

| # | Report § | Claim as written | Finding | Correction |
| --- | --- | --- | --- | --- |
| A1 | 1, 9.1, 14, 15.2, 18 (and the blocker review) | LM51551 OVP trips at **51.4–54.2 V** | That range assumes a perfect divider and V<sub>REF</sub>. V<sub>OVTH</sub> = 107/110/113 % of V<sub>REF</sub> [DS], V<sub>REF</sub> 0.99–1.01 V [DS], R307/R308 ±1 % | **Typical 52.8 V; worst case 49.9–55.9 V** [CALC]. With the same chip and divider, the trip stays ≥ 7 % above the regulation point, so there is no nuisance trip. The worst-case maximum (55.9 V) is what matters for E-11, J703 and the bleeder |
| A2 | 1, 15.1, 16 | ngspice reproduces LTspice "within about 2 %" | True for V<sub>out</sub> (0.1–0.7 %), I<sub>pk</sub> (0.7–1.8 %), V<sub>DS</sub> (0.4–1.1 %), D301 stress (0–0.6 %), I<sub>in</sub> (0.7–2 %) and P<sub>clamp</sub> (1–2.4 %). **Not true for output ripple** (0.138 vs 0.162 V at 3.0 V, +17 %; 0.144 vs 0.126 V at 4.2 V, −12 %). Efficiency differs by 2 points (0.82 vs 0.80) | Wording changed to "within about 2 % for averages, peaks and stresses; ripple within ±17 %" |
| A3 | 3.1 block diagram | Charger drawn feeding the fuse input (`CHG --> F101`) | Wrong. BQ25188 BAT (C2) is on **VBAT_FUSED**, between F101 and J102 [REPO design.py; A-14] | Diagram redrawn |
| A4 | 13 sequence diagram | Encoder A/B drawn as coming from the PMD401 | Wrong. Encoder A/B/I come from the **LL06 encoder through J705**, not from the PMD401 | Diagram redrawn with the encoder as a separate participant |
| A5 | 7 | BQ25188 "3.0–18 V input" | The feature list says 3.0–18 V, but the electrical table gives **V<sub>IN_OP</sub> 3.6–18 V** [DS] | Corrected; T<sub>REG</sub> 60/80/100 °C selectable added [DS] |
| A6 | 7, 15.2 | Charger dissipation figures | Arithmetic correct [CALC]. **The YBG thermal resistance is not in the repository datasheet**: its thermal table lists only "BQ25185 DLH". Junction temperature therefore cannot be calculated | Note added; T<sub>REG</sub> limits the die temperature by reducing the charge current |
| A7 | 15.2 / blocker review §4 | Bleeder: C<sub>max</sub> ≈ 181.7 µF, R ≤ 11.5 kΩ, 4.3 s | C<sub>max</sub> = 2 × 2.2 + 1.2 × (47 + 100) = **180.8 µF** [CALC] | 10 kΩ gives 4.2 s from 50.4 V and 4.4 s from 55.9 V (still < 5 s); R ≤ 11.5–12.0 kΩ; loss 0.25–0.31 W |
| A8 | Blocker review §9 | 455 s motor time at 50 U/day | At 0.113 U/s it is 444 s | Corrected (negligible effect) |
| A9 | 12.1, 17 (R9) | CSD16340Q3 footprint "unverified" | Checked against TI SLPS247E §7.2 (in the repository) [DS]. Pads 0.63 × 0.50 mm match; the 0.560 mm row-to-drain gap and 3.50 mm overall match; drain pad 1.9 × 2.45 mm matches. Source/gate pad centres are at ±0.33/±0.97 mm against TI's ±0.325/±0.975 mm (0.65 mm pitch), so the gaps are **0.14/0.16 mm against TI's 0.15 mm** | Footprint confirmed within 5 µm. Proposal: move the four pads to TI's exact positions, which gives 0.15 mm gaps and removes the 0.127 mm DRU exception (footprint change, owner approval) |
| A10 | 9.1 / design.py note on Q303 | "BSS138 50 V" | The BSS138P datasheet in the repository gives V<sub>DS</sub> **60 V** [DS]; the 50 V figure came from the Rev A parts list | Report unaffected (no BSS138 sits on a 48 V net). Noted for the placeholder design |
| A11 | 4 | LL06 top speed 15 mm/s | The PMD401's 1500 Hz × about 5 µm limit is about 7.5 mm/s [DS], so 15 mm/s may not be reachable with this driver | Kept as the conservative figure in the runaway calculation; both stated |
| A12 | `ASSUMPTIONS_AND_DEVIATIONS.md` A-21 | Board 110 × 78 mm | The Edge.Cuts lines in the board file are 100–210 × 100–185 mm, i.e. **110 × 85 mm** | A-21 corrected |

### 1.2 Checked and confirmed (no change)

| Area | What was checked | Result |
| --- | --- | --- |
| Dose arithmetic | Area 16.69 mm²; 599.1 µm and 7489 counts per U; 375 counts per 0.05 U; 1.335 nL per count; 1.001 mL per 60 mm; cap 0.113 U/s; 1.67 N at 1 bar; 3.89 bar at stall | All correct [CALC] |
| Flyback | D 0.765/0.699; R<sub>T</sub> 73.2 kΩ; L<sub>p</sub> 7.37 µH; I<sub>pk</sub> 3.14 A; I<sub>lim</sub> 4.23–4.86 A; t<sub>SS</sub> 4.7 ms (4.3–5.2 ms over I<sub>SS</sub>); V<sub>out</sub> 46.6–49.4 V; RHP zero 30.2 kHz; C<sub>out</sub> ≥ 1.07 µF; leakage 1.99 % for k = 0.99 | All correct [CALC] |
| Waveform claims | Drain plateau 12.9 V; D301 steady 63.8 V; primary peak at turn-on from D301 recovery | Consistent. The PNE20010ER datasheet gives I<sub>RM</sub> 1.1 A (typ) [DS], which supports the recovery spike |
| Kill path | FLY_EN 2.72 V when the MCU drives high; EN thresholds rising 0.40–0.70 V, falling 0.33–0.63 V; UVLO rising 1.425–1.575 V [DS]. With the veto on, FLY_EN ≤ 65 mV for R<sub>DS(on)</sub> ≤ 20 Ω | Off state is robust: 65 mV ≪ 0.33 V |
| Ratings | CSD16340Q3: V<sub>DS</sub> 25 V, V<sub>GS</sub> +10/−8 V (gate = VBAT ≤ 4.2 V). PNE20010ER: 200 V / 1 A, t<sub>rr</sub> ≤ 25 ns. PMEG10020ELR: 100 V / 2 A. LM51551 BIAS 2.97–45 V. TPS62840: 1.8–6.5 V, 750 mA [DS] | All parts within rating at the simulated stresses (FET 75 %, rectifier 49 %, clamp diode 19 %, R306 43 %) |
| Schematic / PCB / BOM | 147 symbols = 147 footprints; KiCad parity 0 [KiCad]; BOM 133 = 147 − 10 test points − 4 mounting holes; BOM statuses match the schematic statuses for BOM items | Consistent |
| Figures | Schematic sheet PNGs are renders of the existing PDF; `pcb_full_2026-11-01.png` and `fix_*` images are labelled as `pcbplot.py` drawings, not KiCad renders; the simulation plot is of the adopted case | Correct |
| Safety/limitations | §14 and §19 | Complete for the known gaps. **Added:** the resistor working-voltage issue (§1.3) and the actual OVP range |

### 1.3 Unsupported or under-supported claims (now labelled in the report)

| Claim | Status |
| --- | --- |
| "Below about 3.4 V input the TPS62840 enters 100 % mode" (§8) | Estimate, not derived from SLVSEC6D dropout data. Labelled as an estimate |
| Molicel P28A capacity, charge voltage, discharge current (§7) | Distributor data only [WEB-2ND]. Already labelled |
| LL06 "5 mW per Hz", holding force, top speed | From `COMPONENTS_AND_BOM.md` (project record of the vendor data), not a datasheet in the repository. Labelled [REPO] |
| JST SH 50 V rating; IPC-2221 values; ST SMPS/RF capacitor values | [WEB-2ND] only. Already labelled; not used in the design |
| "PMD401 drive losses at 15 Hz" (dosing-current estimate) | Unknown; the estimate ignores them. Already stated |

**New issue found by the audit: resistor working voltage on 48 V nodes**

- R307 (470 kΩ, top of the FB divider) is in an **0603** footprint with no MPN. It has about 47 V across it in normal operation and up to about 55 V at the OVP ceiling. Under the proposed 80 % rule, its working-voltage rating must be **≥ 69 V** [CALC].
- 0603 thick-film ratings differ by manufacturer, and no part is chosen.
- If R307 fails open, the converter loses its only voltage feedback (the U-23 single fault).
- **Action:** choose an R307 part with a datasheet working voltage ≥ 75 V (or move it to 1206), and use the same rule for any new 48 V divider (§2.3). Logged as U-38.

---

## Part 2. Decision proposals

Each proposal gives: recommendation · evidence · calculations · advantages and disadvantages · schematic and PCB changes · remaining risks. **None has been implemented.**

### 2.1 STM32WBA55 power and RF implementation (U-05)

**Recommendation**

1. Implement the power, clock and RF circuit **exactly as ST's reference design**: the NUCLEO-WBA55CG MB1803 schematic and layout, plus AN5948 (RF hardware) and AN6373 (embedded SMPS).
2. Footprints for the SMPS configuration (inductor on VLXSMPS → VDD11) with the LDO fallback documented in AN6373.
3. Keep the U.FL connector (owner decision of 10 Oct) behind ST's matching/filter network.

**Evidence**

- [REPO]: pin functions verified (CubeMX 6.18.1). The six supply pins and the RF pin are on placeholder nets (6 ERC errors, 12 unconnected items) [KiCad].
- [WEB-2ND], not applied:
  - The SMPS is a step-down converter whose output is fed back to VDD11.
  - It runs at about 3 MHz and needs an input capacitor, an inductor and an output capacitor, with an optional 10 nH noise filter.
  - About 4.7 µF on VDD11 and about 470 nF on VDDHPA.
  - VDDSMPS and VLXSMPS are grounded in LDO mode.

**Calculations:** none possible without ST's values. No value is proposed here, by rule.

| Advantages | Disadvantages |
| --- | --- |
| SMPS: lower MCU current, which helps E-10 battery life (idle dominates, §2.8) | SMPS adds an inductor, needs a careful local layout, and puts a 3 MHz noise source next to the RF |
| LDO: simplest, fewer parts | LDO: higher current |

**Schematic changes:**
- Replace the L501, C509–C515, R510–R513, L502, Y501/Y502 and C516–C519 placeholders with ST's values and parts.
- Connect VDDHPA, VDDANA, VDDRF and VDDRFPA as ST shows; delete unused placeholders.
- Confirm BOOT0 (PH3) strapping (A-5).

**PCB changes:**
- Re-place Y501 within a few mm of pins 41/42, and L501 and the VDD11 capacitor at pins 3/45.
- Route the RF as 50 Ω coplanar line on the chosen stack-up (U-20), with a via fence.
- Then re-fan-out U501 and route the 12 group-A items. This also frees the 6 boxed-in U501 nets (Part 3).

**Remaining risks:** RF performance is unmeasured; certification is out of scope; ADC leakage (A-27) and pin 5 V tolerance (U-10) still need the datasheet.

### 2.2 Flyback transformer selection (U-04)

**Recommendation:** issue the §9 specification to a magnetics vendor for a **custom-wound** part, and in parallel check Coilcraft Hexa-Path (HP/HPH) in a 1 + 5 connection against the specification. Take whichever meets every line first.

**Evidence**

- R305 22 mΩ with V<sub>CLTH</sub> 93–107 mV gives a 4.23–4.86 A peak limit [DS] [CALC], so I<sub>sat</sub> must be ≥ 5 A.
- Hexa-Path is six 1:1 windings, 5–50 W [WEB-2ND]; the single-winding I<sub>sat</sub> at L<sub>p</sub> ≈ 7 µH is unverified.

**Calculations [CALC]** (3.0 V, 100 mA, D = 0.765, L<sub>p</sub> 7.3 µH):

| Quantity | Value |
| --- | --- |
| Primary RMS | 2.30 A |
| Secondary RMS | 0.21 A (average during off-time 0.43 A) |
| Energy at current limit | ½ L<sub>p</sub> I<sub>lim</sub>² = 86 µJ |

The specification (I<sub>rms</sub> ≥ 2.5 A primary, ≥ 0.3 A secondary) has margin over these.

| Option | Advantages | Disadvantages |
| --- | --- | --- |
| Custom winding | Exact n, L<sub>p</sub>, leakage | Lead time and cost |
| Catalogue part | Fast | A 1:1 winding carrying 3.5 A peak may saturate or overheat; leakage of series-connected windings is unknown |

**Schematic changes:** T301 symbol pin mapping if it differs; real MPN and status.

**PCB changes:**
- Replace `XFMR_PLACEHOLDER_4P`.
- Then the flyback loop compaction (FL-1, FL-2: clamp D302/C308/R306 at the T301/Q301 drain; C309/C310 at the D301 cathode).
- Re-route the flyback block by hand.

**After the part arrives:**
- Re-run `scripts/sim_flyback_ngspice.py` with the real L<sub>p</sub>, leakage and DCR.
- Re-tune R306/C308 for V<sub>DS</sub> ≤ 20 V and R313/C312 for D301 ≤ 120 V.

**Remaining risks:**
- Leakage above 2 % raises clamp loss and V<sub>DS</sub>.
- The loop is still unsimulated: use the TI LM5155 PSpice model [WEB-2ND] and a bench Bode measurement.

### 2.3 Independent 48 V over-voltage protection (U-23)

**Recommendation** (two layers):

1. **Hardware OVP:**
   - A comparator or voltage supervisor with an internal reference, powered from +3V3.
   - Fed by its **own** divider from +48V_RAW, with an open-drain output wired-OR onto **FLY_EN** (the existing kill node).
   - The output also goes to a supervisor GPIO, so the supervisor latches the fault by holding the veto.
2. **Supervisor ADC monitor** of the same rail on a spare STM32C031 analog pin, enforcing the 45.6–50.4 V window in firmware.

**Evidence**

- OVP is sensed on FB only [DS SNVSB75E §9.3.13]; an open R307/R308 leaves the rail uncontrolled.
- FLY_EN low is a valid shutdown: V<sub>EN(FALLING)</sub> ≥ 0.33 V [DS], and the kill path already pulls FLY_EN to ≤ 65 mV [CALC].
- Free STM32C031 pins exist: PA0, PA1, PA4, PA5 and PB3–PB9 are no-connects [REPO]. Their analog function must be confirmed in CubeMX before use.

**Calculations [CALC]**

- **Trip point:** above the regulation worst case (49.4 V) plus load-step overshoot, and below 60 V (E-11). A **52.5 V** trip with a ±1 % reference and a 0.1 % divider gives a **51.9–53.1 V** band.
- **Divider:** R<sub>bot</sub> = R<sub>top</sub> · V<sub>ref</sub>/(V<sub>trip</sub> − V<sub>ref</sub>). With R<sub>top</sub> = 1 MΩ: 23.4 kΩ for a 1.2 V reference or 7.7 kΩ for a 0.4 V reference; about 52 µA, 2.7 mW.
- **R<sub>top</sub> rating:** working voltage ≥ 70 V (§1.3).

**Advantages:**
- Covers the open-FB single fault independently of firmware.
- A latched trip meets "trip latches" (S-04).

**Disadvantages:**
- Cannot also guarantee the PMD401's 50.4 V maximum with 1 % FB resistors.
- Doing so needs 0.1 % FB resistors (setpoint 47.5–48.5 V) and a trip around 50.0 V ± 0.6 V. That is a tight tolerance stack, so the owner should choose.

**Schematic changes:**
- New sheet section "48 V OVP": U4xx comparator/supervisor (part to be chosen from its datasheet), R4xx/R4yy divider, filter capacitor.
- Output OVP_N to FLY_EN and to a supervisor GPIO; a supervisor ADC divider.
- Status: new parts DS/CALC once chosen.

**PCB changes:**
- Place the divider in the 48 V block (top resistor in the HV48 class, 0.6 mm).
- Route OVP_N to FLY_EN (near Q401) and to U601. About 4 new nets.

**Remaining risks:**
- Comparator response time against the converter's overshoot rate (unknown until the transformer and loop are known).
- The latch policy needs firmware.

### 2.4 Motor runaway protection: supervisor-controlled SPI gating (S-06, U-03)

**Recommendation**

- **Hardware gate:** insert a single-gate **OR** gate in **PMD_SS** (the PMD401's active-low slave select, "set low during transmit; about 20 kΩ pull-up" [DS]), between U501 and the 100 Ω series resistor.
  - Gate inputs: PMD_SS_M from U501 and **SUP_SPI_BLOCK** from a spare supervisor GPIO, with a 10 kΩ **pull-up**.
  - When the supervisor is dead or in reset, or decides to block, SS is held high. The PMD401 then receives no SPI frames and stops the motor about 10 ms later (PMD401 manual §5.2 [DS]).
  - Gating SS rather than SCLK avoids feeding a partial clock into a frame.
- **Supervisor firmware:** a TIM3 encoder rate check in two tiers:
  - **Fast tier**, every 1 ms: block if more than 10 counts/ms (0.8 mm/s, about 12× the cap).
  - **Slow tier**, every 100 ms: block above 1.5× the cap.
  - On a trip: block SPI, then veto, then park.

**Calculations [CALC]**

| Case | Result |
| --- | --- |
| S-06 budget | 0.5 U = 300 µm |
| Fast tier at 15 mm/s | 187 counts/ms, detected in ≤ 1 ms; 1 ms + 10 ms PMD401 timeout = 11 ms → 165 µm = **0.28 U** (< 0.5 U) |
| Just below the fast-tier threshold (0.8 mm/s) | Slow tier: 100 ms + 10 ms = 110 ms → 88 µm = 0.15 U |
| Park only (250 ms) | Fails at speeds above 1.2 mm/s |

Deceleration distance after the PMD401 stops is unknown, so measure it (SG-06).

| Advantages | Disadvantages |
| --- | --- |
| Fails safe (pull-up blocks) | One more part in the SPI path |
| Independent of the main MCU; uses the driver's own documented timeout | Relies on the PMD401's "about 10 ms" timeout, which is not a guaranteed maximum |
| Fast enough for S-06 | The PMD401's input threshold and pull-up rail are unknown (IF-02) |

**Schematic changes:**
- U7xx single OR gate (3.3 V logic; part to be chosen from its datasheet).
- New net SUP_SPI_BLOCK (supervisor GPIO, 10 kΩ pull-up to +3V3).
- PMD_SS_M re-routed through the gate.
- CubeMX check of the chosen supervisor pin.

**PCB changes:**
- Gate near R703/J701.
- SUP_SPI_BLOCK route from U601 (about 50 mm; it can follow the existing supervisor corridor).
- Re-route PMD_SS_M, which is already routed and would need a short re-route.

**Remaining risks:**
- Firmware correctness of the rate check.
- Encoder failure (S-07 relies on the same encoder). Consider an independent plausibility check (commanded rate against measured rate).

### 2.5 J703 connector voltage rating (U-37)

**Recommendation**

1. Confirm the rating in JST's SH datasheet.
2. Unless JST states ≥ 70 V DC, change the **board-side** J703 to a connector with a manufacturer rating **≥ 100 V DC** and ≥ 0.6 mm pad-to-pad spacing.
3. Use a short cable with the SH housing only at the PMD401 end, where it is the vendor's own choice.

**Evidence:**
- [WEB-2ND] distributors list SM02B-SRSS-TB at 50 V AC/DC (0.7 or 1.0 A).
- [DS] the PMD401 uses JST SH connectors for its own I/O.
- Current DRU exception: 0.35 mm pad-to-pad inside J703.

**Calculations [CALC]:**
- Rail up to 50.4 V normally and up to 55.9 V at the OVP worst case.
- With 80 % derating, the rating must be ≥ 69.9 V.
- Current is ≤ 0.1 A [DS PMD401].

| Advantages | Disadvantages |
| --- | --- |
| Removes a rating violation and the DRC exception | A custom cable; larger footprint (about 2.5–5 mm pitch families); mechanical layout at the right edge changes |

**Schematic change:** J703 footprint and MPN fields only (same 2-pin net).

**PCB changes:**
- New footprint at the right edge.
- Re-route the short +48V_MOT and GND entry (0.4 mm, HV48).
- Delete the `J703_vendor_connector_pitch` DRU rule.

**Remaining risk:** the PMD401's own SH input is still the vendor's design; document it as a vendor limitation.

### 2.6 48 V output switch versus bleeder (U-06, E-04, E-11)

**Recommendation (Option A):**
- Do **not** build the K-12 high-side switch.
- Delete Q302, Q303, R309 and R310; keep R311 (0 Ω).
- Fit **R312 = 10 kΩ**, ≥ 0.5 W, working voltage ≥ 100 V (2512 footprint already placed).

**Evidence:**
- The flyback has no DC path from VBAT to the output when the LM51551 is disabled [REPO, decision log 10 Oct; transformer + D301].
- The rail is on only while dosing (K-11), so a permanent bleeder costs energy only during dosing.

**Calculations [CALC]:**

| Item | Value |
| --- | --- |
| Rail capacitance | 151.4 µF nominal, 180.8 µF assumed maximum (+20 % electrolytics) |
| Discharge time with 10 kΩ | 3.5 s (nominal, from 50.4 V); 4.2 s (C<sub>max</sub>, 50.4 V); 4.4 s (C<sub>max</sub>, 55.9 V) — all < 5 s (E-11) |
| Dissipation | 0.25 W at 50.4 V; 0.31 W at 55.9 V |
| Added load | 5 mA |
| Daily energy (50 U/day profile, assumed) | ≈ 0.03 Wh |

| Advantages | Disadvantages |
| --- | --- |
| Fewer parts; no ≥ 100 V P-MOSFET and level shifter; removes the SW48_GATE unconnected item; simplest proof for E-11 (PW-08) | Relies on the converter disable plus the bleeder as the "disconnect" (owner must accept this reading of E-04 and K-12) |

**Option B (switch):** galvanic semiconductor disconnect, at the cost of a design and fault analysis.

**Schematic changes (A):**
- Delete the four placeholders.
- R312 value, power, voltage and MPN; status CALC.
- Remove the SW48_GATE and SW48_DRV nets.

**PCB changes (A):** delete Q302/Q303/R309/R310 footprints and the SW48_GATE stub tracks. CI DRC must then show 23 unconnected.

**Remaining risk:** the bleeder resistor's reliability. If it fails open, the discharge time grows; PW-08 checks it.

### 2.7 High-voltage PCB clearance (P-03, CF-6)

**Recommendation:**
- Keep **0.6 mm on all layers** for HV48 (+48V_RAW, +48V_MOT, FLY_SEC) as implemented.
- Confirm against a purchased IPC-2221C Table 6-1, then sign off P-03.

**Evidence:**
- [KiCad]: 0 clearance errors with HV48 0.6 mm.
- [WEB-2ND]: secondary sources give IPC-2221B 31–100 V as B1 (internal) 0.1 mm and B2 (external uncoated) 0.6 mm.
- [SIM]: FLY_SEC/D301 peaks of 89–97 V, so the 51–100 V row applies.

**Calculations:** worst-case DC 55.9 V (OVP) and 97 V transient peaks, both ≤ 100 V.

| Advantages | Disadvantages |
| --- | --- |
| Conservative; already verified; no change | Slightly more board area than the 0.1 mm internal minimum |

**Schematic/PCB changes:** none. Only the J703 exception remains, resolved by §2.5.

**Remaining risk:** the secondary-source table values. Coated or uncoated assumptions depend on solder mask.

### 2.8 Battery, fuse and charge-current selection (U-18, E-01, E-05, E-09, E-10)

**Recommendation**

| Item | Proposal |
| --- | --- |
| Cell | Keep the Molicel INR18650-P28A (K-9, already the Rev A cell), as a **protected pack** (K-12) |
| Fuse F101 | 5 A (E-01, decided), slow-blow, 2920 SMD; DC voltage rating ≥ 6 V; interrupting rating ≥ the pack's protected short-circuit current. Choose from the fuse datasheet and the protection board's limit |
| Charge current | **0.5 A**, set by firmware at start-up (BQ25188 default 10 mA [DS]); T<sub>REG</sub> = 80 °C; watchdog serviced |
| E-05 | Keep 2.1 A normal; size VBAT copper and connectors for the 4.9 A peak current limit |

**Evidence:**
- BQ25188: I<sub>CHG</sub> 5–1000 mA; V<sub>IN_OP</sub> 3.6–18 V; selectable T<sub>REG</sub> 60/80/100 °C; V<sub>BATREG</sub> default 4.20 V [DS].
- Full-speed input current 2.0–2.07 A [SIM].
- Molicel P28A 2800 mAh typical, 35 A continuous [WEB-2ND].

**Calculations [CALC]:**

| Quantity | Value |
| --- | --- |
| Charger loss at 0.5 A from 5 V | 1.0 W at a 3.0 V cell; 0.4 W at 4.2 V. T<sub>REG</sub> reduces the current if the die reaches the set limit. **No YBG θ<sub>JA</sub> in the repository datasheet**, so T<sub>j</sub> is not computable |
| Charge time 0 → 100 % (CC portion) | ≈ 2.8 Ah ÷ 0.5 A ≈ 5.6 h (plus the CV tail) |
| Dosing-speed battery current | ≈ 0.15 A (estimate) |
| Idle power for 3 days | ≤ 0.126 W |

| Advantages | Disadvantages |
| --- | --- |
| 0.5 A: low charger heat, conservative for the cell | Slow charge |
| 1 A: faster charge | Up to 2 W in a WCSP |

**Schematic changes:** F101 MPN; J101 (XT30 ASSUMED) or the pack connector; none for the charge current (firmware).

**PCB changes:** IPC-2152 width check of VBAT_RAW, VBAT_FUSED and VBAT for 4.9 A peak and 2.1 A continuous (PB-05). Not yet done.

**Remaining risks:**
- Real Rev B idle power (BT-01) decides E-10.
- The cell's standard charge current is not confirmed (Molicel datasheet not available).

---

## Part 3. The 24 unconnected items

Trial routing with `pcbroute.py` on a scratch copy, no rip-up, 0.2 mm track, router clearances = net-class rules [ROUTER]. **Nothing was committed.**

### 3.1 Classification

| Class | Count | Items | Evidence |
| --- | --- | --- | --- |
| **Routable immediately** | **2** | ENC_I_M (U501.48 → R710.1): 31.9 mm, 2 vias, 0 violations. VBAT_SENSE (U501.14 → divider): 33.4 mm, 4 vias, 0 violations | [ROUTER] |
| **Blocked by missing datasheets: ST** (STM32WBA55 power/clock/RF) | 12 | HSE_IN ×2, HSE_OUT ×2, LSE_IN ×2, RF_MCU, WBA_VDD11 ×2, WBA_VDDANA, WBA_VDDRF, WBA_VDDRFPA | Values unknown (U-05) |
| **Blocked by missing datasheets: U501 re-fan-out** | 6 | I2C_SDA (R105 → U501.6), PMD_SCLK_M, PMD_MOSI_M, PMD_READY_M, MAIN_SWCLK, FLY_PGOOD (→ PA12) | [ROUTER]: no path; the pins are boxed in by neighbouring escapes. Needs U501's fan-out to be redone, which only makes sense together with the ST-guided re-layout (§2.1). PMD_* pins also need the ST 5 V-tolerance data (U-10) |
| **Blocked by missing datasheets: TI YBG drawing** (BQ25188) | 3 | VBAT_FUSED (U101.C2), CHG_INT_N (U101.A1), I2C_SDA (U101.C1 → R105) | The ball pitch is unverified, and the repository's SLUSFJ3 has no package-drawing pages (checked). VBAT_FUSED has a geometric route (8.7 mm, 2 vias), but it is a charge-current path (≤ 1 A) needing an IPC-2152 width, from pads that may move. CHG_INT_N and I2C_SDA: no path [ROUTER] |
| **Blocked by an unapproved decision** | 1 | SW48_GATE | §2.6: disappears with Option A |
| **Total** | **24** | | |

### 3.2 Recommendation on the two routable items

- **Not routed in this review.** Both pass through the U501 fan-out that §2.1 will re-lay.
- ENC_I_M's pin (48) sits next to the SMPS pins (1–3) where L501 must go.
- VBAT_SENSE is a 500 kΩ analog node; a 33 mm path with 4 vias through digital escapes is acceptable for a DC measurement (C104 sits at the divider), but it is better routed once.
- **Route both immediately after the ST re-layout**, or route them now if the owner prefers a lower interim count (24 → 22).

---

## Part 4. Final status and owner decisions

### 4.1 Status

| Area | Status |
| --- | --- |
| Fabrication readiness | **Not ready** |
| Unconnected items | 24 |
| Owner decisions open | 8 critical (below) + 3 supporting |
| Hardware tested | Nothing |

### 4.2 Owner decisions needed before Rev B can move towards fabrication

| # | Decision | Proposal (Part 2) | Unblocks |
| --- | --- | --- | --- |
| 1 | Supply ST DS + AN5948 + AN6373 + MB1803 schematic (or allow st.com); SMPS vs LDO; keep U.FL | §2.1 | 12 + 6 unconnected; 6 ERC errors; RF |
| 2 | Transformer: custom winding vs catalogue (Hexa-Path check) | §2.2 | Flyback layout, clamp/snubber, loop |
| 3 | Independent OVP (hardware comparator to FLY_EN + supervisor ADC); trip voltage; 0.1 % dividers | §2.3 | U-23 single fault |
| 4 | Supervisor SPI gate on PMD_SS + two-tier rate check | §2.4 | S-06 runaway |
| 5 | J703: confirm JST; ≥ 100 V board connector + SH cable | §2.5 | Rating; DRU exception |
| 6 | Output switch vs bleeder (Option A recommended); accept E-11 | §2.6 | E-04/E-11; SW48_GATE item |
| 7 | HV clearance sign-off after reading IPC-2221C | §2.7 | P-03, CF-6 |
| 8 | Cell (pack), fuse part, charge current 0.5 A, E-10 | §2.8 | BOM, battery life |
| 9 | R307 (and any 48 V divider resistor) with ≥ 75 V working voltage; R313 ≥ 0.5 W | §1.3, blocker review §3 | Single-fault robustness |
| 10 | Q301 footprint pads moved to TI's exact positions (removes the 0.127 mm DRU exception) | §1.1 A9 | Rule compliance |
| 11 | Fab house and stack-up; then IPC-2152 width check and RF 50 Ω | — | Manufacturing rules |

### 4.3 After the decisions, before fabrication (engineering steps)

1. Implement the approved changes in `scripts/design.py`. Regenerate the schematic only (the PCB is hand-maintained now) and update the PCB.
2. Let CI run ERC/DRC/BOM.
3. Route the remaining items; hand-review the flyback loop and RF; clean the silkscreen.
4. Verify every footprint against its drawing (BQ25188 YBG, connectors; PB-03).
5. Run the loop simulation with the real transformer.
6. Hold a design review.
7. Build Rev A on the bench, as the owner's gate for fabrication (K-7, DV-1).
8. Only then produce Phase 6 outputs.
