#include "load_est.h"
#include "pump_config.h"

static uint32_t noload_nm = CFG_STEP_NOLOAD_NM;
void le_set_noload_nm(uint32_t nm) { if (nm >= 1000u && nm <= 9000u) { noload_nm = nm; } }
uint32_t le_noload_nm(void) { return noload_nm; }

void le_reset(load_est_t *e)
{
    e->msteps_win = 0u; e->counts_win = 0; e->msteps_noprog = 0u; e->counts_noprog = 0;
    e->low_streak = 0u; e->last_step_nm = noload_nm;
}

le_result_t le_update(load_est_t *e, uint32_t rate_mhz, int32_t dcounts)
{
    uint32_t dmsteps = rate_mhz / 1000u;          /* milli-steps in 1 ms = rate[mHz] / 1000 */
    e->msteps_win += dmsteps;
    e->counts_win += dcounts;
    e->msteps_noprog += dmsteps;
    e->counts_noprog += dcounts;

    /* stall: CFG_STALL_STEPS commanded steps without one no-load step of travel (OC-08) */
    const int32_t one_step_counts = (int32_t)(noload_nm / CFG_ENC_NM_PER_COUNT);
    if (e->counts_noprog >= one_step_counts) {
        e->msteps_noprog = 0u; e->counts_noprog = 0;
    } else if (e->msteps_noprog >= (uint32_t)CFG_STALL_STEPS * 1000u) {
        return LE_STALL;
    }

    if (e->msteps_win >= (uint32_t)CFG_OCC_WINDOW_STEPS * 1000u) {
        int32_t c = e->counts_win > 0 ? e->counts_win : 0;
        e->last_step_nm = (uint32_t)(((uint64_t)(uint32_t)c * CFG_ENC_NM_PER_COUNT * 1000u) / e->msteps_win);
        if (e->last_step_nm * 1000u < noload_nm * (uint32_t)CFG_OCC_RATIO_PERMILLE) {
            if (++e->low_streak >= CFG_OCC_CONFIRM) {
                return LE_OCCLUSION;
            }
        } else {
            e->low_streak = 0u;
        }
        e->msteps_win = 0u; e->counts_win = 0;
    }
    return LE_OK;
}
