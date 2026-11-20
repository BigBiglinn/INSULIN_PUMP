/* Main MCU (STM32WBA55CG) configuration. Every constant names its source.
 * Status words as in the hardware design: DECIDED (owner), DS (datasheet), CALC, ASSUMED, MEASURE (to be
 * replaced by the named bench check before any accuracy claim).
 * BENCH-ONLY PROTOTYPE: water or 0.9 % saline, never on a person or an animal, never with insulin.
 */
#ifndef PUMP_CONFIG_H
#define PUMP_CONFIG_H

/* ---------------- dose geometry ---------------- */
#define CFG_COUNTS_PER_U_X10     74895   /* CALC: 10 uL / 16.69 mm^2 = 599.2 um / 0.080 um = 7489.5 counts per U
                                            (Hamilton 81320 bore 4.61 mm, LL06 E2 80 nm encoder). MEASURE: DA-02 */
#define CFG_ENC_NM_PER_COUNT     80      /* DS: LL06 option E2, vendor reply 8 Oct 2026 */

/* ---------------- dose limits (K-14, S-05, D-06: DECIDED) ---------------- */
#define CFG_DOSE_MIN_MU          50      /* 0.05 U */
#define CFG_DOSE_STEP_MU         50      /* bolus granularity 0.05 U */
#define CFG_BOLUS_MAX_MU         10000   /* 10 U */
#define CFG_HOUR_MAX_MU          15000   /* 15 U in any rolling hour */
#define CFG_BASAL_MAX_MU_H       5000    /* D-07 (Proposed): 0.05..5.0 U/h */
#define CFG_BASAL_PULSE_MU       50      /* D-07: basal delivered as 0.05 U pulses */

/* ---------------- motion (K-15, D-08, D-09, D-10) ---------------- */
#define CFG_RATE_CAP_HZ          15      /* DECIDED: speed cap about 15 waveform steps/s */
#define CFG_RATE_MIN_HZ          2       /* ASSUMED: slowest approach rate near the target */
#define CFG_SLOW_ZONE_COUNTS     150     /* ASSUMED: start slowing ~2.7 full steps before target */
#define CFG_STOP_BAND_COUNTS     0       /* stop on reaching the target (approach is slow and one-sided) */
#define CFG_SETTLE_MS            50
#define CFG_DOSE_TOL_PERMILLE    10      /* D-10 (Proposed): +/-1 % or +/-4 counts, whichever is larger */
#define CFG_DOSE_TOL_MIN_COUNTS  4
#define CFG_STEP_NOLOAD_NM       4500    /* DS: LL06 no-load full step ~4.5 um. MEASURE: MT-04 */

/* ---------------- sensorless occlusion (K-13, S-08) ---------------- */
#define CFG_OCC_RATIO_PERMILLE   600     /* PLACEHOLDER: alarm when step length < 60 % of no-load.
                                            Must be set from the MT-05 step-length-vs-load curve and OC-05 */
#define CFG_OCC_WINDOW_STEPS     2       /* evaluate every 2 commanded waveform steps */
#define CFG_OCC_CONFIRM          3       /* consecutive low windows before the alarm */
#define CFG_STALL_STEPS          20      /* OC-08: 20 commanded steps with < 1 step of travel = stall */

/* ---------------- PMD401 (manual 150025-01) ---------------- */
#define CFG_PMD_MAX_RATE_HZ      1500    /* DS: maximum wfm-step rate */
#define CFG_PMD_SPI_FULLSCALE    32767   /* ASSUMED: +32767 = +1500 Hz (linear). Manual gives no scale.
                                            MEASURE: MT-03 / FT-07 (the encoder loop absorbs scale error, the
                                            firmware speed cap does NOT; the supervisor rate check is the backstop) */
#define CFG_PMD_SPI_PERIOD_MS    1       /* refresh well inside the ~10 ms timeout (F-06: gap < 5 ms) */
#define CFG_PMD_UNPARK_MIN_MS    80      /* DS: at least 80 ms to power up after AEN high */
#define CFG_PMD_PARK_MS          300     /* DS: ~250 ms to park, + margin */
#define CFG_PMD_BOOT_TIMEOUT_MS  5000    /* ASSUMED: boot time after 48 V unknown (MT-07); Y41 reboot ~2.5 s */
#define CFG_PMD_QUERY_PERIOD_MS  200     /* poll X0Y13 until the PMD401 answers */
#define CFG_PMD_REQUIRE_SERVO    1       /* refuse to move unless X0Y13 reports 3 (servo mode, MT-01) */

/* ---------------- 48 V rail (LM51551) ---------------- */
#define CFG_PGOOD_TIMEOUT_MS     600     /* CALC: soft start 91-111 ms with C305 = 1 uF; generous margin */
#define CFG_GRANT_TIMEOUT_MS     300
#define CFG_READY_TIMEOUT_MS     1500

/* ---------------- battery (S-13) ---------------- */
#define CFG_VBAT_STOP_MV         3400    /* DECIDED: dosing stops at 3.4 V */
#define CFG_VBAT_WARN_MV         3500    /* Proposed: warning at 3.5 V */
#define CFG_VBAT_PERIOD_MS       100

/* ---------------- charger BQ25188 (SLUSFJ3) ---------------- */
#define CFG_CHG_I2C_ADDR         0x6Au   /* DS: 7-bit address */
#define CFG_CHG_ICHG_MA          200     /* ASSUMED: charge current OPEN (B.19); change to the cell's rating */
#define CFG_CHG_SERVICE_MS       10000   /* any I2C transaction resets the 160 s watchdog */

/* ---------------- timing guards ---------------- */
#define CFG_DOSE_TIME_MARGIN_MS  5000    /* move-phase time limit = expected time x 3 + this */

#endif
