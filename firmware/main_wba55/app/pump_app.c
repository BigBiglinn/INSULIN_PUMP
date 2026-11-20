#include "pump_app.h"
#include "charger.h"
#include "dose_ctrl.h"
#include "pump_config.h"
#include "pump_port.h"

#include <stdio.h>

static uint32_t t_vbat, t_status;
static uint16_t vbat_mv;
static bool batt_low, batt_warn;
static uint32_t basal_mu_h, t_next_basal;
static uint32_t pending_bolus_mu;
static uint32_t lastlog_state = 0xFFu;
static dose_record_t last_rec;
static uint32_t n_done;

const dose_record_t *pump_app_last(uint32_t *count) { if (count) { *count = n_done; } return &last_rec; }

void pump_app_init(void)
{
    limits_init();
    ble_cmd_init();
    dose_init();
    vbat_mv = port_vbat_mv();
    t_vbat = t_status = port_ms();
    batt_low = batt_warn = false;
    basal_mu_h = 0u; pending_bolus_mu = 0u; n_done = 0u;
    port_log("PUMP main v0.1 - BENCH ONLY: water/saline, never on a person or animal\r\n");
}

bool pump_app_battery_low(void) { return batt_low; }
uint32_t pump_app_basal_mu_h(void) { return basal_mu_h; }

lim_result_t pump_app_request_bolus(uint32_t mu)
{
    if (batt_low) { return LIM_LOW_BATTERY; }
    if (pending_bolus_mu != 0u) { return LIM_BUSY; }
    lim_result_t r = limits_check(mu, port_ms());
    if (r == LIM_OK) { pending_bolus_mu = mu; }
    return r;
}

lim_result_t pump_app_set_basal(uint32_t mu_per_h)
{
    if (mu_per_h == 0u) { basal_mu_h = 0u; return LIM_OK; }
    if (!limits_integrity_ok()) { return LIM_INTEGRITY; }
    if (mu_per_h < CFG_BASAL_PULSE_MU || mu_per_h > CFG_BASAL_MAX_MU_H || (mu_per_h % CFG_BASAL_PULSE_MU) != 0u) {
        return LIM_BAD_BASAL;
    }
    basal_mu_h = mu_per_h;
    t_next_basal = port_ms();
    return LIM_OK;
}

void pump_app_stop(void) { basal_mu_h = 0u; pending_bolus_mu = 0u; dose_abort(); }
void pump_app_clear_fault(void) { dose_clear_fault(); }

ble_rx_t pump_app_ble_rx(const uint8_t *p, size_t n)
{
    ble_cmd_t c;
    ble_rx_t r = ble_cmd_parse(p, n, port_ble_link_secure(), &c);
    if (r != BR_OK) { return r; }
    lim_result_t lr = LIM_OK;
    switch (c.op) {
    case BOP_BOLUS: lr = pump_app_request_bolus(c.arg); break;
    case BOP_SET_BASAL: lr = pump_app_set_basal(c.arg); break;
    case BOP_STOP: pump_app_stop(); break;
    case BOP_CLEAR_FAULT: pump_app_clear_fault(); break;
    default: break;
    }
    /* reply: op, result, state, fault, position (LE) */
    uint8_t rep[8];
    int32_t pos = dose_position();
    rep[0] = c.op; rep[1] = (uint8_t)lr; rep[2] = (uint8_t)dose_state(); rep[3] = (uint8_t)dose_fault();
    for (int i = 0; i < 4; i++) { rep[4 + i] = (uint8_t)((uint32_t)pos >> (8 * i)); }
    port_ble_notify(rep, sizeof rep);
    return BR_OK;
}

static void log_record(const dose_record_t *r)
{
    char s[128];
    static const char *const res[] = { "-", "done", "aborted", "fault" };
    snprintf(s, sizeof s, "DOSE id=%u req=%lu mU target=%lu cnt delivered=%ld cnt (%lu mU) %s %s t=%lu ms\r\n",
             r->dose_id, (unsigned long)r->req_mu, (unsigned long)r->target_counts, (long)r->delivered_counts,
             (unsigned long)r->delivered_mu, res[r->result], r->result == RES_FAULT ? dose_fault_name(r->fault) : "",
             (unsigned long)(r->t_end - r->t_start));
    port_log(s);
}

void pump_app_tick(void)
{
    uint32_t now = port_ms();
    port_wdg_kick();

    /* battery (S-13): stop at 3.4 V, warn at 3.5 V; a dose in progress ends cleanly */
    if ((now - t_vbat) >= CFG_VBAT_PERIOD_MS) {
        t_vbat = now;
        vbat_mv = port_vbat_mv();
        bool low = vbat_mv <= CFG_VBAT_STOP_MV;
        if (low && !batt_low) {
            port_log("BATTERY LOW: dosing stopped\r\n");
            pump_app_stop();
        }
        batt_low = low;
        bool warn = vbat_mv <= CFG_VBAT_WARN_MV;
        if (warn && !batt_warn) { port_log("BATTERY WARNING\r\n"); }
        batt_warn = warn;
    }

    charger_tick(now);
    dose_tick();

    /* start pending work when idle: a bolus first, then due basal pulses */
    if (dose_state() == MST_IDLE && !batt_low) {
        if (pending_bolus_mu != 0u) {
            if (limits_check(pending_bolus_mu, now) != LIM_OK) {
                pending_bolus_mu = 0u;                                 /* limits re-checked at start */
            } else if (dose_start(pending_bolus_mu)) {
                pending_bolus_mu = 0u;
            }
        } else if (basal_mu_h != 0u && (int32_t)(now - t_next_basal) >= 0) {
            uint32_t interval = (uint32_t)((3600000ull * CFG_BASAL_PULSE_MU) / basal_mu_h);
            if (limits_check(CFG_BASAL_PULSE_MU, now) == LIM_OK && dose_start(CFG_BASAL_PULSE_MU)) {
                t_next_basal += interval;
            } else if (limits_check(CFG_BASAL_PULSE_MU, now) != LIM_OK) {
                t_next_basal += interval;                              /* skipped pulse is not made up */
                port_log("BASAL pulse refused by hour limit\r\n");
            }
        }
    }

    dose_record_t r;
    if (dose_last(&r)) { last_rec = r; n_done++; log_record(&r); }

    if (dose_state() != lastlog_state) {
        char s[64];
        snprintf(s, sizeof s, "STATE %u sup=%u\r\n", (unsigned)dose_state(), (unsigned)dose_sup_state());
        port_log(s);
        lastlog_state = dose_state();
    }
    port_led(dose_state() == MST_FAULT ? ((now / 100u) & 1u) : (dose_state() != MST_IDLE));
    (void)t_status;
}
