#include "sup_logic.h"
#include "sup_config.h"
#include "sup_port.h"

#include <stdio.h>

static sup_state_t st;
static trip_reason_t trip;
static uint32_t t_state;
static int32_t pos, pos_start, pos_safe_ref, pos_still;
static uint16_t enc_last;
static bool enc_init;
static int32_t hist[SUP_RATE_WINDOW_MS];
static unsigned hidx;

static link_rx_t rx;
static bool have_seq;
static uint8_t last_seq, cur_dose, done_dose;
static uint32_t t_rx, t_still;
static m2s_t m;               /* last valid frame */
static uint32_t auth_counts, run_limit_ms;
static bool parking;
static uint32_t t_park;

/* rolling hour of forward travel while running: 60 one-minute buckets */
static uint32_t hb_min[60], hb_cnt[60];

static const char *const tnames[] = { "none", "link lost", "token error", "rate", "overtravel", "reverse",
                                       "timeout", "main fault", "unexpected motion", "bad request" };
const char *sup_trip_name(trip_reason_t t) { return (unsigned)t < 10u ? tnames[t] : "?"; }

sup_state_t sup_state(void) { return st; }
trip_reason_t sup_trip(void) { return trip; }
int32_t sup_pos(void) { return pos; }

static uint32_t mu_to_counts(uint32_t mu)
{
    return (uint32_t)(((uint64_t)mu * SUP_COUNTS_PER_U_X10 * SUP_MARGIN_PERMILLE) / 10000000ull);
}

uint32_t sup_hour_counts(void)
{
    uint32_t now_min = sport_ms() / 60000u, s = 0u;
    for (unsigned i = 0; i < 60u; i++) {
        if (hb_min[i] != 0xFFFFFFFFu && (now_min - hb_min[i]) < 60u) { s += hb_cnt[i]; }
    }
    return s;
}

static void hour_add(uint32_t counts)
{
    uint32_t mm = sport_ms() / 60000u; unsigned i = (unsigned)(mm % 60u);
    if (hb_min[i] != mm) { hb_min[i] = mm; hb_cnt[i] = 0u; }
    hb_cnt[i] += counts;
}

static void outputs(void)
{
    bool veto = !(st == SST_GRANTED || st == SST_RUN);
    bool park = !(st == SST_RUN) || parking;
    if (st == SST_RUN && parking && (sport_ms() - t_park) >= SUP_PARK_MS) { veto = true; }
    sport_set_parked(park);
    sport_set_veto(veto);
}

static void enter(sup_state_t s)
{
    st = s; t_state = sport_ms();
    if (s == SST_SAFE) { pos_safe_ref = pos; parking = false; }
    outputs();
}

static void do_trip(trip_reason_t r)
{
    if (st == SST_TRIP) { return; }
    if (st == SST_GRANTED || st == SST_RUN) {
        int32_t moved = pos - pos_start;            /* travel of the tripped dose counts against the hour */
        if (moved > 0) { hour_add((uint32_t)moved); }
        done_dose = cur_dose;
    }
    trip = r;
    st = SST_TRIP; t_state = sport_ms(); parking = false;
    sport_set_parked(true);
    sport_set_veto(true);
    char s[64];
    snprintf(s, sizeof s, "SUP TRIP: %s (pos %ld)\r\n", sup_trip_name(r), (long)pos);
    sport_log(s);
}

void sup_init(void)
{
    sport_set_veto(true);
    sport_set_parked(true);
    trip = TRIP_NONE; pos = 0; enc_init = false; hidx = 0u;
    for (unsigned i = 0; i < SUP_RATE_WINDOW_MS; i++) { hist[i] = 0; }
    for (unsigned i = 0; i < 60u; i++) { hb_min[i] = 0xFFFFFFFFu; hb_cnt[i] = 0u; }
    link_rx_init(&rx); have_seq = false; cur_dose = done_dose = 0u; t_rx = sport_ms();
    m.state = MST_IDLE; m.cmd = 0u; m.dose_id = 0u; m.auth_counts = 0u;
    t_still = sport_ms(); pos_still = 0;
    enter(SST_SAFE);
    sport_log("SUP v0.1 - BENCH ONLY\r\n");
}

static void reply(void)
{
    s2m_t s;
    s.seq_echo = last_seq; s.state = (uint8_t)st; s.dose_id = cur_dose; s.trip = (uint8_t)trip; s.sup_count = pos;
    uint8_t out[LINK_MAX_FRAME];
    sport_link_send(out, link_encode_s2m(&s, out));
}

static void link_service(uint32_t now)
{
    uint8_t buf[32]; size_t n;
    while ((n = sport_link_recv(buf, sizeof buf)) > 0u) {
        for (size_t i = 0; i < n; i++) {
            m2s_t f;
            if (!link_rx_push_m2s(&rx, buf[i], &f)) { continue; }
            /* token check: sequence must advance by 1..3 (allowing two lost frames); a repeat or a
               backwards step is not a heartbeat */
            uint8_t adv = (uint8_t)(f.seq - last_seq);
            if (have_seq && (adv == 0u || adv > 3u)) {
                if (st == SST_GRANTED || st == SST_RUN) { do_trip(TRIP_SEQ_ERROR); }
                continue;
            }
            have_seq = true; last_seq = f.seq; m = f; t_rx = now;
            reply();
        }
    }
}

void sup_tick(void)
{
    uint32_t now = sport_ms();
    sport_wdg_kick();

    /* encoder, extended from 16 to 32 bit */
    uint16_t raw = sport_enc_raw16();
    if (!enc_init) { enc_last = raw; enc_init = true; }
    int32_t d = (int32_t)(int16_t)(uint16_t)(raw - enc_last);
    enc_last = raw;
    pos += d;
    int32_t past = hist[hidx];
    hist[hidx] = pos; hidx = (hidx + 1u) % SUP_RATE_WINDOW_MS;
    int32_t win = pos - past;                     /* travel over the last 10 ms */
    if (d != 0 && (pos - pos_still > 4 || pos_still - pos > 4)) { pos_still = pos; t_still = now; }

    link_service(now);
    bool link_ok = have_seq && (now - t_rx) < LINK_TIMEOUT_MS;

    if (st == SST_GRANTED || st == SST_RUN) {
        if (!link_ok) { do_trip(TRIP_LINK_LOST); }
        else if (m.state == MST_FAULT) { do_trip(TRIP_MAIN_FAULT); }
        else if (win > SUP_RATE_MAX_COUNTS || win < -SUP_RATE_MAX_COUNTS) { do_trip(TRIP_RATE); }
        else if (pos - pos_start > (int32_t)(auth_counts + auth_counts / 100u + SUP_OVERTRAVEL_COUNTS)) {
            do_trip(TRIP_OVERTRAVEL);
        } else if (pos_start - pos > SUP_REVERSE_COUNTS) { do_trip(TRIP_REVERSE); }
    }
    switch (st) {
    case SST_SAFE:
        if (pos - pos_safe_ref > SUP_IDLE_MOTION_COUNTS || pos_safe_ref - pos > SUP_IDLE_MOTION_COUNTS) {
            do_trip(TRIP_UNEXPECTED_MOTION); break;
        }
        if (link_ok && m.state == MST_REQUEST && m.dose_id != 0u && m.dose_id != done_dose) {
            uint32_t req = m.auth_counts;
            if (req == 0u || req > mu_to_counts(SUP_BOLUS_MAX_MU) ||
                sup_hour_counts() + req > mu_to_counts(SUP_HOUR_MAX_MU)) {
                do_trip(TRIP_BAD_REQUEST); break;
            }
            cur_dose = m.dose_id; auth_counts = req; pos_start = pos;
            run_limit_ms = (uint32_t)(((uint64_t)req * 1000u * 3u) / ((uint64_t)SUP_STEP_COUNTS * SUP_CAP_HZ)) +
                           SUP_RUN_MARGIN_MS;
            enter(SST_GRANTED);
        }
        break;

    case SST_GRANTED:
        if (m.state == MST_UNPARK_REQ && m.dose_id == cur_dose) { enter(SST_RUN); }
        else if (m.state == MST_IDLE || m.state == MST_PARKING) { done_dose = cur_dose; enter(SST_SAFE); }
        else if ((now - t_state) > SUP_GRANT_MAX_MS) { done_dose = cur_dose; enter(SST_SAFE); }
        break;

    case SST_RUN:
        if (!parking && (m.state == MST_PARKING || m.state == MST_IDLE)) { parking = true; t_park = now; }
        if (!parking && (now - t_state) > run_limit_ms) { do_trip(TRIP_TIMEOUT); break; }
        if (parking && (now - t_park) >= SUP_PARK_MS + 50u) {
            int32_t moved = pos - pos_start;
            if (moved > 0) { hour_add((uint32_t)moved); }
            done_dose = cur_dose;
            enter(SST_SAFE);
            break;
        }
        outputs();
        break;

    case SST_TRIP:
    default:
        if (link_ok && m.cmd == M2S_CMD_CLEAR_TRIP && m.state == MST_IDLE &&
            (now - t_still) >= SUP_CLEAR_STILL_MS) {
            trip = TRIP_NONE; auth_counts = 0u;
            sport_log("SUP: trip cleared\r\n");
            enter(SST_SAFE);
        }
        break;
    }
    if (st == SST_TRIP) {            /* re-assert every tick */
        sport_set_veto(true);
        sport_set_parked(true);
    }
}
