# D7 investigation: scratch evidence (NOT applied to the project PCB)

Every file here was produced on **scratch copies** of the board at `route-stage5a-done`. None of them has been applied to `hardware/kicad/pump_v2.kicad_pcb`. The write-up is in `docs/handover/ROUTING_STAGES.md` §7.

| File | What it is |
|---|---|
| `req.json` | Grid-router request: FLY_PGOOD → TP302, then RS485_RO and LED_MAIN (owner scope: pins 29 and 30 only). RF_ANT and RF_MCU margins set to "same layer only" for the second run. |
| `reqC.json`, `escapes.json`, `routesC.json` | Variant C: hand fan-out of pins 28–31, with the RS485_DE via moved, plus the routed FLY_PGOOD tail |
| `variantC_drc.json` | DRC of variant C. **Not clean:** 6 tracks_crossing, 1 clearance and 1 short against MAIN_NRST, MAIN_BOOT0, MAIN_SWO and WBA_VDDHPA. (The `lib_footprint_issues` entries are a scratch-folder artefact.) |
| `reqD.json` / `routesD.json`, `reqD2.json` / `routesD2.json` | Variant D: RS485_DI and RS485_DE vias also freed, two routing orders. RS485_RO (and, in one order, LED_MAIN) found no route. |
