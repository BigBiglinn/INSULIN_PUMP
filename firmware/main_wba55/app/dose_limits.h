/* Dose request validation (S-05, C-04: limits apply to every command whatever its source) and the
 * rolling-hour ledger of delivered insulin units. Units: milli-units (mU), 1 U = 1000 mU = 10 uL. */
#ifndef DOSE_LIMITS_H
#define DOSE_LIMITS_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    LIM_OK = 0,
    LIM_BELOW_MIN,
    LIM_NOT_MULTIPLE,
    LIM_ABOVE_BOLUS_MAX,
    LIM_HOUR_EXCEEDED,
    LIM_INTEGRITY,           /* a stored limit failed its complement check: dosing locked (S-16) */
    LIM_LOW_BATTERY,         /* S-13: cell at or below 3.4 V */
    LIM_BUSY,                /* a bolus is already queued */
    LIM_BAD_BASAL            /* basal rate outside 0.05..5 U/h or not a multiple of 0.05 U/h */
} lim_result_t;

void limits_init(void);
lim_result_t limits_check(uint32_t req_mu, uint32_t now_ms);
void limits_record(uint32_t delivered_mu, uint32_t now_ms);
uint32_t limits_hour_sum(uint32_t now_ms);
bool limits_integrity_ok(void);

/* calibration: encoder counts per unit x10 (D-14: weight calibration, stored with complement) */
void cal_set_counts_per_u_x10(uint32_t v);
bool cal_get_counts_per_u_x10(uint32_t *v);   /* false on integrity failure */
uint32_t cal_mu_to_counts(uint32_t mu, bool *ok);
/* same, carrying the sub-count remainder from one dose to the next so repeated small doses do not
 * accumulate rounding error (dose is tracked as an absolute position) */
uint32_t cal_mu_to_counts_carry(uint32_t mu, bool *ok);
uint32_t cal_counts_to_mu(uint32_t counts, bool *ok);

#ifdef PUMP_TEST
void limits_test_flip_bit(unsigned which);    /* fault injection for FT-12 */
#endif

#endif
