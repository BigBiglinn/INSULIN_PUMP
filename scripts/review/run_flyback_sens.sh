#!/bin/sh
# Reviewer's flyback layout-sensitivity sims (ngspice >= 42). Usage: sh scripts/review/run_flyback_sens.sh
# Args per case: VIN DUTY L_clamp_path L_secondary_path. Electrolytic bulk shrunk to 10 uF only to reach steady state fast.
cd "$(dirname "$0")"
run(){ sed "s/VIN/$1/;s/DTY/$2/;s/LCL/$3/;s/LPAR/$4/" flyback_layout_sens.cir.tmpl > /tmp/fly_$5.cir
  ngspice -b /tmp/fly_$5.cir 2>&1 | grep -E "^(vds_max|vr_d1|vout|ipk|vclamp|vo2pp)" | awk -v h="Vin=$1 D=$2 Lclamp=$3 Lsec=$4" 'BEGIN{printf "%s :",h}{printf " %s=%.3g",$1,$3}END{print ""}'; }
run 3.0 0.775 1n 1n a; run 3.0 0.775 25n 30n b; run 4.2 0.71 1n 1n c; run 4.2 0.71 25n 30n d
