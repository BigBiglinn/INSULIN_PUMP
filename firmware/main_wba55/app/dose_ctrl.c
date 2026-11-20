#include "dose_ctrl.h"
#include "dose_limits.h"
#include "hardened.h"
#include "load_est.h"
#include "pmd401.h"
#include "pump_config.h"
#include "pump_port.h"

/* ------------------------------------------------------------------ state */
static main_state_t st;
static fault_t flt;
static uint32_t t_state;                 /* time the current state was entered */
static uint8_t dose_id;
static uint32_t req_mu;
static volatile hu32_t target;           /* absolute encoder target, hardened */
static volatile uint32_t auth;           /* H_TRUE only between a valid grant and the end of the dose */
static uint32_t target_counts;
static int32_t pos, pos_start;
static uint32_t enc_last;
static bool enc_init;
static int32_t rate_mhz;                 /* last commanded rate */
static uint32_t move_limit_ms;
static bool abort_req;
static bool spi_on;
static load_est_t le;
static dose_record_t rec;
static bool rec_ready;
static bool ready_seen;
static uint32_t t_ready;

/* link */
static link_rx_t rx;
static uint8_t seq;
static uint32_t t_link_tx, t_link_rx;
static bool link_ever;
static s2m_t sup;
static bool clear_pending;
static uint32_t t_clear;

#ifdef PUMP_TEST
static bool test_runaway; static int16_t test_word; static bool test_skip_link;
#endif

static const char *const fault_names[FLT__COUNT] = {
    "none", "link lost", "supervisor trip", "supervisor state", "grant timeout",
    "PGOOD timeout", "PGOOD lost", "PMD401 boot timeout", "PMD401 not in servo mode",
    "READY timeout", "PMD401 FAULT", "PMD401 not ready", "occlusion", "stall", "dose error (D-10)",
    "move timeout", "integrity", "overspeed"
};

const char *dose_fault_name(fault_t f) { return (f < FLT__COUNT) ? fault_names[f] : "?"; }

static void enter(main_state_t s) { st = s; t_state = port_ms(); }

/* ------------------------------------------------------------------ encoder */
static void enc_update(void)
{
    uint32_t raw = port_enc_raw();
    if (!enc_init) { enc_last = raw; enc_init = true; return; }
    int32_t d = (port_enc_bits() == 16u) ? (int32_t)(int16_t)(uint16_t)(raw - enc_last)
                                         : (int32_t)(raw - enc_last);
    enc_last = raw;
    pos += d;
}

/* ------------------------------------------------------------------ outputs */
static void rail_off(void)
{
    port_set_48v_enable(false);
    if (spi_on) { port_pmd_spi_enable(false); spi_on = false; }
    auth = H_FALSE;
}

static void send_rate(int32_t mhz)
{
    rate_mhz = mhz;
    if (!spi_on) { return; }
    int16_t w = pmd_rate_to_word(mhz);
    if (w != 0 && auth != H_TRUE) { w = 0; }     /* no motion without a live authorisation */
    port_pmd_spi_write(w);
}

static void fault(fault_t f)
{
    if (st == MST_FAULT) { return; }
    if (spi_on) { port_pmd_spi_write(0); }      /* stop at once instead of waiting for the 10 ms timeout */
    rail_off();
    flt = f;
    rec.result = RES_FAULT; rec.fault = f; rec.t_end = port_ms();
    rec.delivered_counts = pos - pos_start;
    bool ok;
    rec.delivered_mu = (rec.delivered_counts > 0) ? cal_counts_to_mu((uint32_t)rec.delivered_counts, &ok) : 0u;
    if (rec.dose_id != 0u) {
        limits_record(rec.delivered_mu, port_ms());   /* whatever went in counts against the hour */
        rec_ready = true;
    }
    port_log("FAULT: "); port_log(dose_fault_name(f)); port_log("\r\n");
    enter(MST_FAULT);
}

/* ------------------------------------------------------------------ link */
static void link_service(uint32_t now)
{
    uint8_t buf[32];
    size_t n;
    while ((n = port_link_recv(buf, sizeof buf)) > 0u) {
        for (size_t i = 0; i < n; i++) {
            s2m_t s;
            if (link_rx_push_s2m(&rx, buf[i], &s)) {
                /* accept only answers to one of our last few frames (fresh token) */
                if ((uint8_t)(seq - s.seq_echo) < 4u) {
                    sup = s; t_link_rx = now; link_ever = true;
                }
            }
        }
    }
#ifdef PUMP_TEST
    if (test_skip_link) { return; }
#endif
    if ((now - t_link_tx) >= LINK_PERIOD_MS) {
        t_link_tx = now;
        m2s_t m;
        seq++;
        m.seq = seq; m.state = (uint8_t)st; m.dose_id = dose_id;
        m.cmd = M2S_CMD_NONE;
        if (clear_pending) {
            /* repeat the clear request until the supervisor is SAFE (it waits for 1 s without motion) */
            if (sup.state == SST_SAFE || (now - t_clear) > 5000u) { clear_pending = false; }
            else { m.cmd = M2S_CMD_CLEAR_TRIP; }
        }
        m.auth_counts = (st == MST_IDLE || st == MST_FAULT) ? 0u : target_counts;
        uint8_t out[LINK_MAX_FRAME];
        port_link_send(out, link_encode_m2s(&m, out));
    }
}

bool dose_link_alive(void) { return link_ever && (port_ms() - t_link_rx) < LINK_TIMEOUT_MS; }
sup_state_t dose_sup_state(void) { return (sup_state_t)sup.state; }
uint8_t dose_sup_trip(void) { return sup.trip; }
int32_t dose_sup_count(void) { return sup.sup_count; }

/* ------------------------------------------------------------------ API */
void dose_init(void)
{
    st = MST_IDLE; flt = FLT_NONE; t_state = port_ms();
    dose_id = 0u; auth = H_FALSE; hu32_set(&target, 0u);
    pos = 0; enc_init = false; rate_mhz = 0; spi_on = false; abort_req = false; rec_ready = false;
    link_rx_init(&rx); seq = 0u; t_link_tx = port_ms(); t_link_rx = 0u; link_ever = false;
    sup.state = SST_TRIP; sup.trip = TRIP_NONE; clear_pending = false; t_clear = 0u;
    port_set_48v_enable(false);
    port_pmd_spi_enable(false);
#ifdef PUMP_TEST
    test_runaway = false; test_skip_link = false;
#endif
}

bool dose_start(uint32_t mu)
{
    if (st != MST_IDLE || !dose_link_alive() || sup.state != SST_SAFE) { return false; }
    bool ok;
    uint32_t counts = cal_mu_to_counts_carry(mu, &ok);
    if (!ok || counts == 0u) { return false; }
    dose_id = (uint8_t)(dose_id + 1u); if (dose_id == 0u) { dose_id = 1u; }
    req_mu = mu; target_counts = counts;
    pos_start = pos;
    hu32_set(&target, (uint32_t)(pos_start + (int32_t)counts));
    abort_req = false;
    rec.dose_id = dose_id; rec.req_mu = mu; rec.target_counts = counts; rec.delivered_counts = 0;
    rec.delivered_mu = 0u; rec.result = RES_NONE; rec.fault = FLT_NONE; rec.t_start = port_ms();
    /* expected move time at the cap with the no-load step, x3, plus margin */
    uint32_t cnt_per_step = CFG_STEP_NOLOAD_NM / CFG_ENC_NM_PER_COUNT;
    move_limit_ms = (uint32_t)(((uint64_t)counts * 1000u * 3u) / ((uint64_t)cnt_per_step * CFG_RATE_CAP_HZ)) +
                    CFG_DOSE_TIME_MARGIN_MS;
    enter(MST_REQUEST);
    return true;
}

void dose_abort(void) { if (st != MST_IDLE && st != MST_FAULT) { abort_req = true; } }

void dose_clear_fault(void)
{
    if (st == MST_FAULT) { flt = FLT_NONE; enter(MST_IDLE); }
    clear_pending = true;       /* ask the supervisor to clear its latch as well (needs IDLE) */
    t_clear = port_ms();
}

main_state_t dose_state(void) { return st; }
fault_t dose_fault(void) { return flt; }
int32_t dose_position(void) { return pos; }

bool dose_last(dose_record_t *r)
{
    if (!rec_ready) { return false; }
    *r = rec; rec_ready = false;
    return true;
}

static void finish(dose_result_t res)
{
    rec.result = res; rec.t_end = port_ms();
    rec.delivered_counts = pos - pos_start;
    bool ok;
    rec.delivered_mu = (rec.delivered_counts > 0) ? cal_counts_to_mu((uint32_t)rec.delivered_counts, &ok) : 0u;
    limits_record(rec.delivered_mu, port_ms());
    rec_ready = true;
}

/* ------------------------------------------------------------------ the 1 ms tick */
void dose_tick(void)
{
    uint32_t now = port_ms();
    int32_t pos_before = pos;
    enc_update();
    int32_t dpos = pos - pos_before;
    link_service(now);
#ifdef PUMP_TEST
    if (test_runaway) {            /* FT-02 model: corrupted main logic, heartbeat alive, full-rate SPI */
        if (spi_on) { port_pmd_spi_write(test_word); }
        return;
    }
#endif
    uint32_t in_state = now - t_state;

    /* checks common to every active state */
    if (st != MST_IDLE && st != MST_FAULT) {
        if (!dose_link_alive()) { fault(FLT_LINK_LOST); return; }
        if (sup.state == SST_TRIP) { fault(FLT_SUP_TRIP); return; }
        if (!limits_integrity_ok() || !hu32_ok(&target)) { fault(FLT_INTEGRITY); return; }
    }

    switch (st) {
    case MST_IDLE:
        break;

    case MST_REQUEST:
        if (abort_req) { finish(RES_ABORTED); enter(MST_IDLE); break; }
        if (sup.state == SST_GRANTED && sup.dose_id == dose_id) {
            auth = H_TRUE;
            h_jitter(port_random());
            if (auth != H_TRUE || !hu32_ok(&target)) { fault(FLT_INTEGRITY); break; }
            port_set_48v_enable(true);
            enter(MST_RAIL_UP);
        } else if (in_state > CFG_GRANT_TIMEOUT_MS) {
            fault(FLT_GRANT_TIMEOUT);
        }
        break;

    case MST_RAIL_UP:
        if (sup.state != SST_GRANTED) { fault(FLT_SUP_STATE); break; }
        if (abort_req) { rail_off(); enter(MST_PARKING); break; }
        if (!spi_on) {
            if (port_fly_pgood()) {
                port_pmd_spi_enable(true); spi_on = true;
                send_rate(0);
                pmd_query_start(now);
            } else if (in_state > CFG_PGOOD_TIMEOUT_MS) {
                fault(FLT_PGOOD_TIMEOUT);
            }
            break;
        }
        if (!port_fly_pgood()) { fault(FLT_PGOOD_LOST); break; }
        send_rate(0);
        switch (pmd_query_poll(now)) {
        case PQ_SERVO_OK: ready_seen = false; enter(MST_UNPARK_REQ); break;
        case PQ_NOT_SERVO: fault(FLT_PMD_NOT_SERVO); break;
        case PQ_TIMEOUT: fault(FLT_PMD_BOOT_TIMEOUT); break;
        default: break;
        }
        break;

    case MST_UNPARK_REQ:
        if (!port_fly_pgood()) { fault(FLT_PGOOD_LOST); break; }
        if (port_pmd_fault()) { fault(FLT_PMD_FAULT); break; }
        if (abort_req) { enter(MST_PARKING); break; }
        send_rate(0);
        if (sup.state == SST_RUN && sup.dose_id == dose_id && port_pmd_ready()) {
            if (!ready_seen) { ready_seen = true; t_ready = now; }
            if ((now - t_ready) >= CFG_PMD_UNPARK_MIN_MS) {
                le_reset(&le);
                enter(MST_MOVE);
            }
        } else {
            ready_seen = false;
            if (in_state > CFG_READY_TIMEOUT_MS) { fault(FLT_READY_TIMEOUT); }
        }
        break;

    case MST_MOVE: {
        if (!port_fly_pgood()) { fault(FLT_PGOOD_LOST); break; }
        if (port_pmd_fault()) { fault(FLT_PMD_FAULT); break; }
        if (!port_pmd_ready()) { fault(FLT_PMD_NOT_READY); break; }
        if (sup.state != SST_RUN) { fault(FLT_SUP_STATE); break; }
        if (in_state > move_limit_ms) { fault(FLT_MOVE_TIMEOUT); break; }
        /* own speed check: more than 4x the travel the cap allows in 1 ms (1 ms granularity is coarse;
           the supervisor checks independently over 10 ms windows) */
        if (dpos > 8) { fault(FLT_OVERSPEED); break; }
        if (abort_req) { send_rate(0); enter(MST_SETTLE); break; }
        int32_t remaining = (int32_t)target.v - pos;
        if (remaining <= CFG_STOP_BAND_COUNTS) {
            send_rate(0);
            enter(MST_SETTLE);
            break;
        }
        int32_t r = CFG_RATE_CAP_HZ * 1000;
        if (remaining < CFG_SLOW_ZONE_COUNTS) {
            r = CFG_RATE_MIN_HZ * 1000 + (int32_t)(((int64_t)(CFG_RATE_CAP_HZ - CFG_RATE_MIN_HZ) * 1000 * remaining) /
                                                   CFG_SLOW_ZONE_COUNTS);
        }
        send_rate(r);
        le_result_t lr = le_update(&le, (uint32_t)r, dpos);
        if (lr == LE_OCCLUSION) { fault(FLT_OCCLUSION); break; }
        if (lr == LE_STALL) { fault(FLT_STALL); break; }
        break;
    }

    case MST_SETTLE:
        send_rate(0);
        if (in_state >= CFG_SETTLE_MS) {
            int32_t delivered = pos - pos_start;
            int32_t err = delivered - (int32_t)target_counts;
            if (err < 0) { err = -err; }
            int32_t tol = (int32_t)((target_counts * CFG_DOSE_TOL_PERMILLE) / 1000u);
            if (tol < CFG_DOSE_TOL_MIN_COUNTS) { tol = CFG_DOSE_TOL_MIN_COUNTS; }
            if (!abort_req && err > tol) { fault(FLT_DOSE_ERROR); break; }
            enter(MST_PARKING);
        }
        break;

    case MST_PARKING:
        /* supervisor parks the motor on seeing PARKING; keep the rail up while it parks, then cut it */
        send_rate(0);
        auth = H_FALSE;
        if (in_state >= CFG_PMD_PARK_MS) {
            rail_off();
            if (sup.state == SST_SAFE || in_state > CFG_PMD_PARK_MS + 500u) {
                finish(abort_req ? RES_ABORTED : RES_DONE);
                enter(MST_IDLE);
            }
        }
        break;

    case MST_FAULT:
    default:
        rail_off();
        break;
    }
}

#ifdef PUMP_TEST
void dose_test_runaway(int16_t word) { test_runaway = true; test_word = word; }
void dose_test_skip_link(bool skip) { test_skip_link = skip; }
void dose_test_corrupt_target(void) { target.v ^= 0x40u; }
#endif
