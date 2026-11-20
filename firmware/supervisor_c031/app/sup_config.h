/* Supervisor (STM32C031C6) configuration. Independent constants on purpose: the supervisor does not
 * trust the main MCU's configuration (F-09: separate code base). */
#ifndef SUP_CONFIG_H
#define SUP_CONFIG_H

#define SUP_COUNTS_PER_U_X10     74895   /* CALC, same geometry as the main MCU (599 um/U, 80 nm/count) */
#define SUP_MARGIN_PERMILLE      1050    /* 5 % allowance for calibration differences (DA-02) */
#define SUP_BOLUS_MAX_MU         10000   /* K-14 */
#define SUP_HOUR_MAX_MU          15000   /* K-14 */

/* Rate backstop (S-06/S-07). Cap 15 steps/s x worst-case 8 um step (PMD401 manual 5 +/- 3 um)
 * = 120 um/s = 1500 counts/s. Trip at twice that over any 10 ms window: 30 counts / 10 ms. */
#define SUP_RATE_WINDOW_MS       10
#define SUP_RATE_MAX_COUNTS      30

#define SUP_OVERTRAVEL_COUNTS    60      /* beyond auth + D-10 tolerance: about one full step */
#define SUP_REVERSE_COUNTS       120
#define SUP_IDLE_MOTION_COUNTS   750     /* 0.1 U of travel while parked/unpowered = unexpected */
#define SUP_GRANT_MAX_MS         8000    /* rail up + PMD401 boot (unknown, MT-07) + unpark */
#define SUP_PARK_MS              300     /* PMD401 parks in ~250 ms */
#define SUP_RUN_MARGIN_MS        5000
#define SUP_STEP_COUNTS          56      /* 4.5 um no-load step / 80 nm */
#define SUP_CAP_HZ               15
#define SUP_CLEAR_STILL_MS       1000    /* trip clears only after 1 s without motion */

#endif
