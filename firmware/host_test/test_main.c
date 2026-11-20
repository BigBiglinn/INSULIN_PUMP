/* Host tests: both MCU firmwares run against the plant model, 1 ms per step.
 * Test names follow requirements/VALIDATION_PLAN.md. A PASS here is a software result on an ASSUMED
 * plant; it is not evidence about the hardware. Build and run:  make -C firmware/host_test
 */
#include "sim_plant.h"
#include "../main_wba55/app/pump_app.h"
#include "../main_wba55/app/dose_ctrl.h"
#include "../main_wba55/app/dose_limits.h"
#include "../main_wba55/app/load_est.h"
#include "../main_wba55/app/ble_cmd.h"
#include "../supervisor_c031/app/sup_logic.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int sim_verbose;
extern bool sim_ble_secure;
void sim_ports_reset(void);

static int n_pass, n_fail;
#define AREA 16.69
#define COUNTS_PER_U 7489.5

static void check(int ok, const char *name, const char *detail)
{
    printf("%-6s %-58s %s\n", ok ? "PASS" : "FAIL", name, detail);
    if (ok) { n_pass++; } else { n_fail++; }
}

static void step(void)
{
    plant_step();
    if (!P.main_halted) { pump_app_tick(); }
    if (!P.sup_dead) { sup_tick(); }
}
static void run(uint32_t ms) { for (uint32_t i = 0; i < ms; i++) { step(); } }

static void boot(void)
{
    plant_reset(); sim_ports_reset();
    sup_init(); pump_app_init(); le_set_noload_nm(4500u);
    run(200);
}

/* run until the main MCU is idle (or faulted) after having left idle; returns elapsed ms */
static uint32_t run_dose(uint32_t timeout_ms)
{
    uint32_t t0 = P.ms;
    bool left = false;
    while (P.ms - t0 < timeout_ms) {
        step();
        if (dose_state() != MST_IDLE) { left = true; }
        if (left && (dose_state() == MST_IDLE || dose_state() == MST_FAULT)) { run(500); break; }
    }
    return P.ms - t0;
}

static int32_t counts_now(void) { return (int32_t)floor(P.x_um / 0.080 + 0.5); }
static double ul_of_counts(int32_t c) { return c * 0.080 * AREA * 1e-3; }

static void wait_state(main_state_t s, uint32_t timeout)
{
    uint32_t t0 = P.ms;
    while (dose_state() != s && P.ms - t0 < timeout) { step(); }
}

int main(int argc, char **argv)
{
    char d[200];
    if (argc > 1 && strcmp(argv[1], "-v") == 0) { sim_verbose = 1; }
    printf("Host tests: main (STM32WBA55) + supervisor (STM32C031) firmware on an ASSUMED plant model\n\n");

    /* ---------------------------------------------------------------- FW-04: 40 x 0.05 U */
    boot();
    {
        int32_t c0 = counts_now(); int bad = 0; int32_t worst = 0;
        for (int i = 0; i < 40; i++) {
            pump_app_request_bolus(50);
            run_dose(20000);
            uint32_t n; const dose_record_t *r = pump_app_last(&n);
            int32_t e = r->delivered_counts - 375; if (e < 0) { e = -e; }
            if (e > worst) { worst = e; }
            if (r->result != RES_DONE || e > 4) { bad++; }
        }
        double ul = ul_of_counts(counts_now() - c0);
        snprintf(d, sizeof d, "total %.4f uL of 20 uL (%.3f %%), worst pulse error %d counts, max rate %.2f Hz",
                 ul, (ul - 20.0) / 20.0 * 100.0, (int)worst, P.max_step_rate_hz);
        check(bad == 0 && fabs(ul - 20.0) / 20.0 < 0.005 && P.max_step_rate_hz <= 15.01,
              "FW-04/DA-05  40 x 0.05 U pulses, each 375 +/- 4 counts", d);
    }

    /* ---------------------------------------------------------------- 5 U bolus */
    boot();
    {
        int32_t c0 = counts_now();
        pump_app_request_bolus(5000);
        uint32_t t = run_dose(200000);
        const dose_record_t *r = pump_app_last(NULL);
        double u = (counts_now() - c0) / COUNTS_PER_U;
        snprintf(d, sizeof d, "%.4f U in %.1f s (plunger), record %ld counts, result %d", u, t / 1000.0,
                 (long)r->delivered_counts, r->result);
        check(r->result == RES_DONE && fabs(u - 5.0) / 5.0 < 0.01, "FW-04  5 U bolus within D-10 (1 %)", d);
    }

    /* ---------------------------------------------------------------- step length 2..8 um */
    {
        double sl[] = { 2.0, 8.0 };
        for (int k = 0; k < 2; k++) {
            boot();
            P.step_um_noload = sl[k]; le_set_noload_nm((uint32_t)(sl[k] * 1000.0));  /* MT-04 calibration */
            int32_t c0 = counts_now();
            pump_app_request_bolus(1000);
            run_dose(200000);
            const dose_record_t *r = pump_app_last(NULL);
            double u = (counts_now() - c0) / COUNTS_PER_U;
            snprintf(d, sizeof d, "step %.0f um: %.4f U, result %d", sl[k], u, r->result);
            check(r->result == RES_DONE && fabs(u - 1.0) < 0.01, "FW-04  1 U bolus with 2 um / 8 um step length", d);
        }
    }

    /* ---------------------------------------------------------------- FT-07: SPI scale error */
    {
        double se[] = { 0.73, 1.27 };
        for (int k = 0; k < 2; k++) {
            boot();
            P.spi_scale_err = se[k];
            int32_t c0 = counts_now();
            pump_app_request_bolus(1000);
            run_dose(200000);
            const dose_record_t *r = pump_app_last(NULL);
            double u = (counts_now() - c0) / COUNTS_PER_U;
            snprintf(d, sizeof d, "scale x%.2f: %.4f U, result %d, max rate %.1f Hz", se[k], u, r->result,
                     P.max_step_rate_hz);
            check(r->result == RES_DONE && fabs(u - 1.0) < 0.01, "FT-07  SPI rate scale +/-27 %: dose still in D-10", d);
        }
        printf("       note: with a +27 %% scale error the motor runs at 19 Hz, above the 15 Hz cap: the firmware\n"
               "       cap depends on the unmeasured SPI scale (MT-03); the supervisor rate limit is the backstop.\n");
    }

    /* ---------------------------------------------------------------- OC-02: occlusion on a 5 U bolus */
    boot();
    {
        P.occluded = true;
        int32_t c0 = counts_now();
        pump_app_request_bolus(5000);
        run_dose(200000);
        int32_t pushed = counts_now() - c0;
        snprintf(d, sizeof d, "fault '%s' after %.3f U pushed, peak %.2f bar (%.0f mmHg)",
                 dose_fault_name(dose_fault()), pushed / COUNTS_PER_U, P.p_bar, P.p_bar * 750.06);
        check(dose_fault() == FLT_OCCLUSION && pushed < (int32_t)COUNTS_PER_U,
              "OC-02  blocked line: alarm before 1 U is pushed", d);
        printf("       note: the alarm threshold (60 %% of no-load step) is a PLACEHOLDER until MT-05/OC-05.\n");
    }

    /* ---------------------------------------------------------------- FT-11: bad requests, hour limit */
    boot();
    {
        lim_result_t a = pump_app_request_bolus(0), b = pump_app_request_bolus(40), c = pump_app_request_bolus(10050),
                     e = pump_app_request_bolus(75);
        int ok1 = a == LIM_BELOW_MIN && b == LIM_BELOW_MIN && c == LIM_ABOVE_BOLUS_MAX && e == LIM_NOT_MULTIPLE;
        pump_app_request_bolus(10000); run_dose(400000);
        pump_app_request_bolus(5000); run_dose(200000);
        uint32_t n; pump_app_last(&n);
        lim_result_t f = pump_app_request_bolus(50);
        snprintf(d, sizeof d, "0/0.04/10.05/0.075 U refused (%d %d %d %d); after %u doses (%.2f U) next 0.05 U -> %d",
                 a, b, c, e, n, limits_hour_sum(P.ms) / 1000.0, f);
        check(ok1 && f == LIM_HOUR_EXCEEDED, "FT-11  invalid sizes refused; 16th unit in the hour refused", d);
    }

    /* ---------------------------------------------------------------- BLE command layer */
    boot();
    {
        uint8_t pkt[BLE_PKT_LEN];
        ble_cmd_build(BOP_BOLUS, 10, 1000, pkt);
        sim_ble_secure = false; ble_rx_t r1 = pump_app_ble_rx(pkt, BLE_PKT_LEN);
        sim_ble_secure = true;  ble_rx_t r2 = pump_app_ble_rx(pkt, BLE_PKT_LEN);
        ble_rx_t r3 = pump_app_ble_rx(pkt, BLE_PKT_LEN);                 /* replay */
        ble_cmd_build(BOP_STATUS, 11, 0, pkt); pkt[5] ^= 1u;
        ble_rx_t r4 = pump_app_ble_rx(pkt, BLE_PKT_LEN);                 /* altered */
        snprintf(d, sizeof d, "insecure %d, valid %d, replay %d, tampered %d", r1, r2, r3, r4);
        check(r1 == BR_INSECURE && r2 == BR_OK && r3 == BR_REPLAY && r4 == BR_CRC,
              "BL-02/03/04  insecure, replayed and altered commands refused", d);
        pump_app_stop();
    }

    /* ---------------------------------------------------------------- FT-12: corrupted values */
    boot();
    {
        limits_test_flip_bit(0);
        lim_result_t r = pump_app_request_bolus(1000);
        boot();
        pump_app_request_bolus(2000);
        wait_state(MST_MOVE, 20000); run(300);
        dose_test_corrupt_target(); run(50);
        fault_t f = dose_fault();
        run(1000);
        snprintf(d, sizeof d, "flipped bolus limit -> %d; flipped target mid-move -> fault '%s', sup %d",
                 r, dose_fault_name(f), sup_state());
        check(r == LIM_INTEGRITY && f == FLT_INTEGRITY && sup_state() == SST_TRIP,
              "FT-12  bit flips in limits and target detected, dosing locked", d);
    }

    /* ---------------------------------------------------------------- FT-01: main MCU hangs mid-bolus */
    boot();
    {
        pump_app_request_bolus(5000);
        wait_state(MST_MOVE, 20000); run(2000);
        int32_t c0 = counts_now(); uint32_t t0 = P.ms;
        P.main_halted = true;
        uint32_t t_stop = 0, t_trip = 0; int32_t last = c0;
        for (int i = 0; i < 2000; i++) {
            step();
            if (!t_stop && i > 2 && counts_now() == last && P.spi_word == 0) { t_stop = P.ms - t0; }
            last = counts_now();
            if (!t_trip && sup_state() == SST_TRIP) { t_trip = P.ms - t0; }
        }
        int32_t over = counts_now() - c0;
        snprintf(d, sizeof d, "motor stopped after %u ms (PMD401 SPI timeout), supervisor trip after %u ms "
                 "(%s), extra travel %d counts (%.4f U)", t_stop, t_trip, sup_trip_name(sup_trip()), (int)over,
                 over / COUNTS_PER_U);
        check(t_stop > 0 && t_stop <= 15 && t_trip > 0 && t_trip <= 300 && over < 3745,
              "FT-01/SG-04  main MCU halt: stop <= ~10 ms, trip <= 300 ms", d);
    }

    /* ---------------------------------------------------------------- FT-04: heartbeat wire open */
    boot();
    {
        pump_app_request_bolus(5000);
        wait_state(MST_MOVE, 20000); run(1000);
        int32_t c0 = counts_now(); uint32_t t0 = P.ms;
        P.link_cut = true;
        uint32_t t_trip = 0, t_mf = 0;
        for (int i = 0; i < 1000; i++) {
            step();
            if (!t_trip && sup_state() == SST_TRIP) { t_trip = P.ms - t0; }
            if (!t_mf && dose_state() == MST_FAULT) { t_mf = P.ms - t0; }
        }
        int32_t over = counts_now() - c0;
        snprintf(d, sizeof d, "supervisor trip %u ms, main fault %u ms ('%s'), extra travel %d counts",
                 t_trip, t_mf, dose_fault_name(dose_fault()), (int)over);
        check(t_trip && t_trip <= 300 && t_mf && t_mf <= 300 && over < 3745,
              "FT-04  heartbeat link cut mid-bolus: both sides stop", d);
    }

    /* ---------------------------------------------------------------- FT-03 / SG-03: supervisor dead */
    boot();
    {
        P.sup_dead = true;
        run(300);
        pump_app_request_bolus(1000);
        run(10000);
        P.mcu_en = true; run(500);          /* even with the main enable forced high */
        snprintf(d, sizeof d, "main state %d, rail %.1f V, travel %d counts", dose_state(), P.v48, (int)counts_now());
        check(dose_state() == MST_IDLE && P.v48 < 1.0 && counts_now() == 0,
              "FT-03/SG-03  dead supervisor: no 48 V, no motion", d);
    }

    /* ---------------------------------------------------------------- FT-02: runaway with live heartbeat */
    boot();
    {
        pump_app_request_bolus(5000);
        wait_state(MST_MOVE, 20000); run(500);
        int32_t c0 = counts_now(); uint32_t t0 = P.ms;
        dose_test_runaway(32767);
        uint32_t t_trip = 0;
        for (int i = 0; i < 3000; i++) {
            step();
            if (!t_trip && sup_state() == SST_TRIP) { t_trip = P.ms - t0; }
        }
        int32_t over = counts_now() - c0;
        snprintf(d, sizeof d, "supervisor '%s' trip after %u ms; extra travel %.2f U (S-06 limit 0.5 U)",
                 sup_trip_name(sup_trip()), t_trip, over / COUNTS_PER_U);
        check(sup_trip() == TRIP_RATE && t_trip <= 15, "FT-02  runaway detected by the supervisor rate check", d);
        printf("       %s: extra delivery %s the 0.5 U limit. The supervisor can only remove 48 V and park;\n"
               "       the motor keeps stepping until the rail sags (~90 ms) or parking completes (~250 ms). Meeting S-06\n"
               "       needs a hardware gate on the SPI path (open item U-03), not firmware.\n",
               over < 3745 ? "PASS" : "EXPECTED GAP", over < 3745 ? "is within" : "EXCEEDS");
    }

    /* ---------------------------------------------------------------- BT-02: low battery */
    boot();
    {
        P.vbat_mv = 3350; run(300);
        lim_result_t r = pump_app_request_bolus(1000);
        P.vbat_mv = 3800; run(300);
        pump_app_request_bolus(5000);
        wait_state(MST_MOVE, 20000); run(1000);
        P.vbat_mv = 3390;
        run_dose(20000);
        const dose_record_t *rec = pump_app_last(NULL);
        snprintf(d, sizeof d, "request at 3.35 V -> %d; drop to 3.39 V mid-bolus -> result %d, fault '%s', state %d",
                 r, rec->result, dose_fault_name(dose_fault()), dose_state());
        check(r == LIM_LOW_BATTERY && rec->result == RES_ABORTED && dose_state() == MST_IDLE,
              "BT-02  refused at 3.4 V; dose in progress ends cleanly", d);
    }

    /* ---------------------------------------------------------------- MT-01: PMD401 not in servo mode */
    boot();
    {
        P.servo_mode = false;
        pump_app_request_bolus(1000);
        run_dose(20000);
        snprintf(d, sizeof d, "fault '%s', travel %d counts", dose_fault_name(dose_fault()), (int)counts_now());
        check(dose_fault() == FLT_PMD_NOT_SERVO && counts_now() == 0, "MT-01  PMD401 not in servo mode: no motion", d);
    }

    /* ---------------------------------------------------------------- FT-13: driver FAULT line */
    boot();
    {
        pump_app_request_bolus(5000);
        wait_state(MST_MOVE, 20000); run(1000);
        P.pmd_fault = true; run(1000);
        snprintf(d, sizeof d, "fault '%s', supervisor %d", dose_fault_name(dose_fault()), sup_state());
        check(dose_fault() == FLT_PMD_FAULT && sup_state() == SST_TRIP, "FT-13  PMD401 FAULT asserted: dosing stops", d);
    }

    /* ---------------------------------------------------------------- FT-05: encoder lost mid-move */
    boot();
    {
        pump_app_request_bolus(5000);
        wait_state(MST_MOVE, 20000); run(1000);
        double x0 = P.x_um;
        P.enc_frozen = true;
        run(5000);
        double over_u = (P.x_um - x0) / 0.080 / COUNTS_PER_U;
        snprintf(d, sizeof d, "fault '%s', travel after loss %.3f U (limit 0.5 U)", dose_fault_name(dose_fault()), over_u);
        check((dose_fault() == FLT_STALL || dose_fault() == FLT_OCCLUSION) && over_u < 0.5,
              "FT-05  encoder wire lost: fault within 0.5 U", d);
        printf("       note: a frozen encoder looks like zero step length, so it is reported as occlusion or stall.\n");
    }

    /* ---------------------------------------------------------------- SG-07: latch and clear */
    {
        dose_clear_fault();               /* continues from the faulted state above */
        P.enc_frozen = false;
        run(3000);
        sup_state_t s1 = sup_state();
        pump_app_request_bolus(100);
        run_dose(20000);
        const dose_record_t *r = pump_app_last(NULL);
        snprintf(d, sizeof d, "supervisor after clear %d; next dose result %d", s1, r->result);
        check(s1 == SST_SAFE && r->result == RES_DONE, "SG-07  trip latched until cleared on purpose, then usable", d);
    }

    /* ---------------------------------------------------------------- unexpected motion while parked */
    boot();
    {
        P.x_um += 100.0;                 /* rod pushed by 100 um with the motor parked */
        run(50);
        snprintf(d, sizeof d, "supervisor %d ('%s')", sup_state(), sup_trip_name(sup_trip()));
        check(sup_state() == SST_TRIP && sup_trip() == TRIP_UNEXPECTED_MOTION,
              "S-07  travel while parked detected by the supervisor", d);
    }

    /* ---------------------------------------------------------------- DA-06: basal 1 U/h for 1 h */
    boot();
    {
        int32_t c0 = counts_now();
        pump_app_set_basal(1000);
        run(3600u * 1000u);
        pump_app_set_basal(0); run(20000);
        uint32_t n; pump_app_last(&n);
        double u = (counts_now() - c0) / COUNTS_PER_U;
        snprintf(d, sizeof d, "%u pulses, %.4f U in 1 h", n, u);
        check(n >= 20 && n <= 21 && fabs(u - 0.05 * n) < 0.005 * n, "DA-06  basal 1 U/h as 0.05 U pulses", d);
    }

    printf("\n%d passed, %d failed\n", n_pass, n_fail);
    return n_fail ? 1 : 0;
}
