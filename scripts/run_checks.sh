#!/usr/bin/env bash
# Run ERC, DRC (with schematic parity) and BOM export for Piezo Insulin Pump v2.
# Reports land in validation/ and docs/. Read the reports - exit codes alone prove nothing,
# and a clean report does not prove the circuit works.
set -u
cd "$(dirname "$0")/.."
K=hardware/kicad
mkdir -p validation/erc validation/drc validation/logs

kicad-cli sch erc --format report --severity-all \
  -o validation/erc/pump_v2-erc.rpt "$K/pump_v2.kicad_sch"

kicad-cli pcb drc --format report --severity-all --schematic-parity --refill-zones --save-board \
  -o validation/drc/pump_v2-drc.rpt "$K/pump_v2.kicad_pcb"

kicad-cli sch export bom -o docs/bom.csv \
  --fields "Reference,Value,Footprint,MPN,Status,QUANTITY,DNP" \
  --labels "Refs,Value,Footprint,MPN,Status,Qty,DNP" \
  --group-by "Value,Footprint,MPN,Status,DNP" --ref-range-delimiter "" "$K/pump_v2.kicad_sch"

kicad-cli sch export bom -o docs/bom_detailed.csv \
  --fields "Reference,Value,Footprint,MPN,Status,DNP,Note" \
  --labels "Ref,Value,Footprint,MPN,Status,DNP,Note / source" \
  --ref-range-delimiter "" "$K/pump_v2.kicad_sch"

echo "== ERC summary";  grep -E "^\[" validation/erc/pump_v2-erc.rpt | sed 's/\]:.*/]/' | sort | uniq -c
echo "== DRC summary";  grep -E "^\[" validation/drc/pump_v2-drc.rpt | sed 's/\]:.*/]/' | sort | uniq -c | sort -rn
