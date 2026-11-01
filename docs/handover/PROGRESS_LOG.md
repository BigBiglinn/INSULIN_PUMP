# Progress log (live record for resuming work)

Update this file at every checkpoint. Newest first.

## 1 Nov 2026: completion session

| Step | Result | Commit |
| --- | --- | --- |
| Baseline | HEAD `7cc348e`, clean tree. pcbcheck: 24 unconnected on 19 nets, matching CI run 2 | — |
| Closed-loop flyback modelling | Level 2 (ngspice behavioural) and level 3 (cycle model) built from SNVSB75E; they agree with each other and with level 1 | `a768755`, `15707e8`, `c10dbe4` |
| Soft-start finding | 47 nF → hiccup lock-out; C305 = 2.2 µF applied to design.py, schematic and PCB | `a768755` |
| Routing | ENC_I_M and VBAT_SENSE routed; 22 unconnected | `a768755` |
| KiCad CI | Run 4 on `a768755`: ERC 6 + 1 (unchanged), DRC 0 copper, 0 parity, 0 footprint errors, 22 unconnected, 122 silk. Reports archived | `15707e8` |
| Load-step study | Hiccup on 100 mA steps at 3.0/3.4 V; a 20 ms ramp avoids it → FW-R1 | `15707e8` |
| Fault studies | Open R307: ratchet to 100 V in 2.9 s at no load; proposed OVP latches at 52.5 V. Short: hiccup in 0.23 ms | `15707e8` |
| Runaway timing | S-06 met with the SPI gate only if the PMD401 timeout ≤ 18 ms | `15707e8` |
| ST evidence | NUCLEO-WBA55CG reference firmware: SMPS supply, HSE 32 MHz, LSE for RTC and radio | `15707e8` |
| BOM | `bom_full.csv` with selection classes; reference set identical to the kicad-cli export | `15707e8` |
| Long switching startup run (260 ms, 3.0 V, 100 mA during startup) | Regulates (47.99 V, 4.80 W, 1.94 A in) but the hiccup rule triggers at 214 ms → FW-R2: keep the motor parked until PGOOD | final commit of the session |
| Documentation | 36-section report, approval sheet, fabrication blockers, firmware review, file index; register U-39 to U-44, A-28 to A-30, decision log §10 | `15707e8` |

## Where to resume

1. Owner works through `OWNER_APPROVAL_SHEET.md`.
2. With ST documents: re-lay U501 power/RF/crystals, then route the 12 + 6 dependent items.
3. With the TI YBG drawing: verify the U101 footprint, then route its 3 items.
4. With the transformer: footprint, clamp/snubber re-tune, re-run `sim_flyback_closedloop.py` (ideally with TI's model), finalise compensation.
5. Implement approved decisions 1, 2, 3 and 14 (new circuitry), push, and read the CI reports.

Commands that must still pass after any change: `python3 scripts/pcbcheck.py`, `python3 scripts/gen_bom_full.py`, `python3 scripts/audit_calcs.py`, plus the CI workflow on push.
