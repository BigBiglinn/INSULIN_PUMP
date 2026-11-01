# Q301 simulation results (1 Nov 2026)

LTspice 26.1.1, batch mode. Software result only: nothing was built or measured. **Q301 margin stays open.**

## Setup

Forced-peak-current harness from `../flyback_clamp_final.cir`: R306 330 ohm, C308 100 nF, SMAJ15A ceiling at the top of its VBR tolerance, output held at 48.6 V, Lp +5 %. `Lstray` adds the 3-5 nH commutation-loop estimate from `docs/handover/PCB_STAGES.md`. BV is set to 60 V in the models so peaks above 30 V can be read rather than clipped.

## AONR34332C (fitted part), 4.9 A limit

| VBAT | Leakage | Loop L | Vds peak | % of 30 V | TVS power | R306 power | Deck |
|---|---|---|---|---|---|---|---|
| 4.2 V | 2 % | 3 nH | 25.8 V | 86 % | 0 | 0.87 W | `check_aonr_coss_4p2_3n_leak02` |
| 4.2 V | 2 % | 5 nH | 27.2 V | 91 % | 0 | 0.87 W | `check_aonr_coss_4p2_5n_leak02` |
| 4.2 V | 10 % | 3 nH | 27.1 V | 90 % | 3.03 W | 0.98 W | `check_aonr_coss_4p2_3n_leak10` |
| 4.2 V | 10 % | 5 nH | 28.9 V | 96 % | 3.03 W | 0.98 W | `check_aonr_coss_4p2_5n_leak10` |
| 4.2 V | 10 % | 4 nH | 28.0 V | 93 % | not measured | 0.98 W | `short_aonr_4p2` |
| 3.4 V | 10 % | 4 nH | 27.2 V | 91 % | not measured | 0.98 W | `short_aonr_3p4` |

## Conclusions

- No simulated corner exceeds 30 V, but the worst is 28.9 V. Adding the existing 1 V TVS heating estimate gives about 29.9 V, so there is effectively no margin at 10 % leakage. The 80 % derating figure (24 V) is exceeded at every corner above.
- This supports the 27.9-30.3 V estimate in `PCB_STAGES.md`. The 24.4 V in the D304 BOM note excludes loop inductance and should not be read as the expected peak.
- At 10 % leakage and the 4.9 A limit the TVS takes about 3 W steadily. The SMAJ15A continuous rating has not been checked here. Treat this as an overload condition, not an operating point.

## Checks on the numbers

- **Settling:** Vcl 17.96 V at 200-230 us against 17.95 V at 400-430 us; Pin 13.00 W against 13.02 W.
- **Consistency:** the 4 nH result (27.98 V) falls between 3 nH (27.10 V) and 5 nH (28.78 V). The BUK 4.2 V deck reproduced 38.35 V on rerun.
- **Coss sensitivity:** `check_aonr_*` uses Cjo 5 nF, M 0.4; `check_aonr_coss_*` uses a fit read from datasheet Fig. 8. The worst peak moves from 28.78 V to 28.86 V. The 3 nH and 5 nH table rows use the Fig. 8 fit; the 4 nH rows use the original values.
- **Measurement fix:** `Ptv` in the older decks is the loss in Rtv only. `Pdtv` in the `check_*` decks is the TVS power.

## Limits

- The VDMOS model is fitted from datasheet values and curves, not supplied by the vendor. The harness has no copper loss model and no real T301: leakage is unpublished, so 2 % and 10 % are brackets.
- The loop inductance is an estimate, not an extraction from the routed copper. R316, R317 and C314 are not modelled.
- 25 C models only. VBAT 3.0 V was not run with the AONR model; the long `aonr_*` and `buk_*` logs stop mid-run and hold no measurements, except `buk_maxvth_3p0`.

## BUK9M20-40H decks: not evidence

The `buk_*` models are not traceable: the datasheet could not be retrieved (`PCB_STAGES.md`), so their parameters are unverified. They gave 37.4-38.3 V at the 4.9 A limit. In `buk_maxvth_3p0` the FET stays on at 2.9 A with no switching. Neither result should be used to accept or reject that part.

## Regenerating

Run `make.py`, `make2.py`, then `make3.py` from this folder, and each deck with `LTspice.exe -b <deck>.cir`. `.raw` and new `.db` outputs are git-ignored.
