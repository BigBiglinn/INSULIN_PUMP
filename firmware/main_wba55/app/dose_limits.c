#include "dose_limits.h"
#include "hardened.h"
#include "pump_config.h"
#include "pump_port.h"

/* Rolling hour: 60 one-minute buckets of delivered mU, keyed by the absolute minute number. */
#define NB 60u
static uint32_t b_min[NB];
static uint32_t b_mu[NB];

static volatile hu32_t lim_min, lim_step, lim_bolus, lim_hour;
static volatile hu32_t cal_cpu_x10;
static uint32_t carry;     /* remainder in 1/10000 count */

void limits_init(void)
{
    for (unsigned i = 0; i < NB; i++) { b_min[i] = 0xFFFFFFFFu; b_mu[i] = 0u; }
    hu32_set(&lim_min, CFG_DOSE_MIN_MU);
    hu32_set(&lim_step, CFG_DOSE_STEP_MU);
    hu32_set(&lim_bolus, CFG_BOLUS_MAX_MU);
    hu32_set(&lim_hour, CFG_HOUR_MAX_MU);
    hu32_set(&cal_cpu_x10, CFG_COUNTS_PER_U_X10);
    carry = 0u;
}

bool limits_integrity_ok(void)
{
    return hu32_ok(&lim_min) && hu32_ok(&lim_step) && hu32_ok(&lim_bolus) && hu32_ok(&lim_hour) &&
           hu32_ok(&cal_cpu_x10);
}

uint32_t limits_hour_sum(uint32_t now_ms)
{
    uint32_t now_min = now_ms / 60000u, sum = 0u;
    for (unsigned i = 0; i < NB; i++) {
        /* bucket of minute m counts while now_min - m < 60 (covers at least the last 59-60 minutes;
           the bucket granularity makes the window slightly longer than 1 h, i.e. conservative) */
        if (b_min[i] != 0xFFFFFFFFu && (now_min - b_min[i]) < NB) {
            sum += b_mu[i];
        }
    }
    return sum;
}

void limits_record(uint32_t delivered_mu, uint32_t now_ms)
{
    uint32_t m = now_ms / 60000u;
    unsigned i = (unsigned)(m % NB);
    if (b_min[i] != m) { b_min[i] = m; b_mu[i] = 0u; }
    b_mu[i] += delivered_mu;
}

lim_result_t limits_check(uint32_t req_mu, uint32_t now_ms)
{
    hflow_t f; hflow_reset(&f);
    if (!limits_integrity_ok()) { return LIM_INTEGRITY; }
    hflow_step(&f, 1u);
    if (req_mu < lim_min.v) { return LIM_BELOW_MIN; }
    hflow_step(&f, 2u);
    if ((req_mu % lim_step.v) != 0u) { return LIM_NOT_MULTIPLE; }
    hflow_step(&f, 4u);
    if (req_mu > lim_bolus.v) { return LIM_ABOVE_BOLUS_MAX; }
    hflow_step(&f, 8u);
    uint32_t hs = limits_hour_sum(now_ms);
    if (hs + req_mu > lim_hour.v) { return LIM_HOUR_EXCEEDED; }
    hflow_step(&f, 16u);
    /* second, independent evaluation of the two over-dose limits after a random delay */
    h_jitter(port_random());
    if (!(req_mu <= (~lim_bolus.nv)) || !(limits_hour_sum(now_ms) + req_mu <= (~lim_hour.nv))) {
        return LIM_INTEGRITY;
    }
    hflow_step(&f, 32u);
    if (!hflow_check(&f, 63u) || !limits_integrity_ok()) { return LIM_INTEGRITY; }
    return LIM_OK;
}

void cal_set_counts_per_u_x10(uint32_t v) { hu32_set(&cal_cpu_x10, v); }

bool cal_get_counts_per_u_x10(uint32_t *v)
{
    if (!hu32_ok(&cal_cpu_x10)) { return false; }
    *v = cal_cpu_x10.v;
    return true;
}

uint32_t cal_mu_to_counts(uint32_t mu, bool *ok)
{
    uint32_t c = 0u;
    *ok = cal_get_counts_per_u_x10(&c);
    if (!*ok) { return 0u; }
    /* counts = mu/1000 U * c/10 counts/U, rounded */
    return (uint32_t)(((uint64_t)mu * c + 5000u) / 10000u);
}

uint32_t cal_mu_to_counts_carry(uint32_t mu, bool *ok)
{
    uint32_t c = 0u;
    *ok = cal_get_counts_per_u_x10(&c);
    if (!*ok) { return 0u; }
    uint64_t total = (uint64_t)mu * c + carry;
    carry = (uint32_t)(total % 10000u);
    return (uint32_t)(total / 10000u);
}

uint32_t cal_counts_to_mu(uint32_t counts, bool *ok)
{
    uint32_t c = 0u;
    *ok = cal_get_counts_per_u_x10(&c);
    if (!*ok || c == 0u) { *ok = false; return 0u; }
    return (uint32_t)(((uint64_t)counts * 10000u + c / 2u) / c);
}

#ifdef PUMP_TEST
void limits_test_flip_bit(unsigned which)
{
    switch (which) {
    case 0: lim_bolus.v ^= 0x00004000u; break;   /* 10 U -> ~26 U if unchecked */
    case 1: lim_hour.v ^= 0x00010000u; break;
    case 2: cal_cpu_x10.v ^= 0x00000100u; break;
    default: lim_min.v ^= 1u; break;
    }
}
#endif
