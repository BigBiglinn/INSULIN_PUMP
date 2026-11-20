/* Sensorless load estimate from step length (K-13, S-08): the LL06 step shrinks as the load rises, so
 * measured encoder travel per commanded waveform step estimates the back-pressure. */
#ifndef LOAD_EST_H
#define LOAD_EST_H

#include <stdbool.h>
#include <stdint.h>

typedef enum { LE_OK = 0, LE_OCCLUSION, LE_STALL } le_result_t;

typedef struct {
    uint32_t msteps_win;     /* commanded milli-steps in the current window */
    int32_t counts_win;      /* encoder counts in the current window */
    uint32_t msteps_noprog;  /* commanded milli-steps since the last full step of real travel */
    int32_t counts_noprog;
    uint8_t low_streak;
    uint32_t last_step_nm;   /* last evaluated step length */
} load_est_t;

void le_reset(load_est_t *e);
/* no-load step length in nm: calibration from bench check MT-04 (default CFG_STEP_NOLOAD_NM) */
void le_set_noload_nm(uint32_t nm);
uint32_t le_noload_nm(void);
/* per 1 ms: rate_mhz = commanded rate in milli-Hz (waveform steps), dcounts = encoder delta */
le_result_t le_update(load_est_t *e, uint32_t rate_mhz, int32_t dcounts);

#endif
