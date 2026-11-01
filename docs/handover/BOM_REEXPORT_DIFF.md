# BOM re-export: differences from the stale export (11 Oct 2026)

**Scope.** This is an export refresh only. No schematic, value, footprint or status was edited in this change.

**Exports.** `docs/bom.csv` and `docs/bom_detailed.csv` were re-exported from the committed schematic with the same `kicad-cli sch export bom` options as `scripts/run_checks.sh`.

**Why they were stale.** The previous exports date from commit `8241494`. The schematic was changed afterwards, in commit `51575de` ("Design v2"), whose decisions are recorded in `decisions/DECISION_LOG.md` and `docs/handover/FLYBACK_DESIGN.md`. The schematic sheets are byte-identical between tag `baseline-routing-e8d141c` and the current head. Every difference below therefore comes from `51575de`.

**Counts.** Component rows go from 131 to 133: 4 added and 2 removed.

## Parts added (in the schematic since 51575de)

| Ref | Value | Footprint | Status | Source note (from the schematic) |
|---|---|---|---|---|
| C312 | 100pF/250V C0G | C_1206 | CALC | D301 RC snubber capacitor; sees about 100 V peak, so a 250 V C0G part |
| R313 | 220R 1206 | R_1206 | CALC | D301 RC snubber (sim run 3). Value depends on the real T301 leakage; re-tune on the bench |
| Q402 | BSS138 | SOT-23 | DECIDED | Owner, 10 Oct 2026: open-drain AEN driver; parked by default |
| R405 | 10k | R_0603 | DECIDED | Owner, 10 Oct 2026: Q402 gate pull-up, so parked by default |

## Parts removed

| Ref | Old row | Reason |
|---|---|---|
| R404 | 10k, PLACEHOLDER, DNP | Removed by the owner decision (veto pull-up R403 fitted instead) |
| R713 | TBD, PLACEHOLDER, DNP | Replaced by Q402/R405 open-drain AEN |

## Value, footprint, MPN, status or DNP changes

| Ref | Field: old → new |
|---|---|
| C104 | Status PLACEHOLDER → CALC; DNP → fitted |
| C302, C303 | Value 10uF/10V → 10uF/10V X5R; Status TBD → CALC |
| C304 | Value 1uF/10V → 2.2uF/10V; Status TBD → DS |
| C305 | Value TBD → 47nF; Status TBD → CALC |
| C306 | Value TBD → 180nF; Status TBD → CALC |
| C307 | Value TBD → 3.3nF; Status TBD → CALC; DNP → fitted |
| C308 | Value TBD → 22nF/50V X7R; Status TBD → CALC |
| C309, C310 | Value 2.2uF/100V → 2.2uF/100V X7R; Status TBD → CALC |
| D301 | D_TBD_100V, D_SMA → PNE20010ER, Nexperia_CFP3_SOD-123W; MPN Nexperia PNE20010ER; Status TBD → DS |
| D302 | D_CLAMP_TBD, D_SMA → PMEG10020ELR, Nexperia_CFP3_SOD-123W; MPN Nexperia PMEG10020ELR; Status TBD → DS |
| Q301 | NMOS_TBD, TDSON-8-1 → CSD16340Q3, VSON-8 3.3x3.3 NexFET; MPN TI CSD16340Q3; Status PLACEHOLDER → DS |
| R101 | Value 10k_TBD → 10k; Status TBD → DS |
| R107, R108 | Value TBD → 1M 1%; Status PLACEHOLDER → CALC; DNP → fitted |
| R301 | Value TBD → 73.2k 1%; Status TBD → CALC |
| R303 | Value TBD → 3.01k 1%; Status TBD → CALC |
| R305 | Value TBD → 22m 1% 1W; Status TBD → CALC |
| R306 | Value TBD → 390R 1W; footprint R_1206 → R_2512; Status TBD → CALC |
| R403 | Status PLACEHOLDER → DECIDED; DNP → fitted |
| T301, U101 | Source note text only; value, footprint and status unchanged (T301 is still the PLACEHOLDER transformer) |

## Status of the BOM

"CALC" values are engineering calculations and simulations, not bench-verified. TBD and PLACEHOLDER rows remain, including T301, R312, the WBA55 supply capacitors and the output-switch parts.

This BOM is not a purchasing or fabrication BOM.
