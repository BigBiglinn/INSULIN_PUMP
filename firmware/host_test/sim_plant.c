#include "sim_plant.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

plant_t P;

#define AREA_MM2 16.69          /* Hamilton 81320 */
#define N_PER_BAR (AREA_MM2 * 0.1)   /* 1 bar = 0.1 N/mm^2 -> 1.669 N */

void plant_reset(void)
{
    memset(&P, 0, sizeof P);
    P.step_um_noload = 4.5; P.friction_n = 1.0; P.stall_n = 6.5; P.spi_scale_err = 1.0;
    P.compliance_ul_bar = 2.0; P.outflow_ul_s_bar = 20.0; P.servo_mode = true; P.pmd_boot_ms = 1500;
    P.vbat_mv = 3800; P.sup_veto = true; P.sup_parked = true;
}

static bool en_node(void)
{
    bool veto = P.sup_dead ? true : P.sup_veto;
    bool ovp = P.v48 > 51.5;              /* D303/Q304 trip, modelled at mid-band */
    return P.mcu_en && !veto && !ovp;
}

bool plant_pgood(void) { return en_node() && P.v48 >= 45.0; }

bool plant_ready_line_low(void)
{
    if (!P.pmd_powered) { return true; }  /* shifter: unpowered PMD401 reads LOW (= "ready") */
    return P.pmd_booted && P.unparked;
}

bool plant_fault_line_high(void) { return P.pmd_powered && P.pmd_fault; }

int32_t plant_counts(void)
{
    static int32_t frozen;
    int32_t c = (int32_t)floor(P.x_um / 0.080 + 0.5);
    if (!P.enc_frozen) { frozen = c; }
    return frozen;
}

void plant_spi_write(int16_t w)
{
    if (!P.pmd_powered || !P.spi_enabled) { return; }
    P.spi_word = w; P.spi_last_ms = P.ms;
}

void plant_rs485_rx_line(const char *line, char *reply, int n)
{
    reply[0] = '\0';
    if (!P.pmd_powered || !P.pmd_booted) { return; }
    if (strcmp(line, "X0Y13\r") == 0) { snprintf(reply, (size_t)n, "X0Y13:%d\r", P.servo_mode ? 3 : 1); }
}

void plant_step(void)
{
    P.ms++;
    /* rail: ~100 ms soft-start ramp when enabled, RC decay through 10 k bleeder and 182 uF when not */
    if (en_node()) { P.v48 += 0.48; if (P.v48 > 48.0) { P.v48 = 48.0; } }
    else { P.v48 -= P.v48 / 1820.0; }

    bool powered = P.v48 >= 40.0;
    if (powered && !P.pmd_powered) { P.pmd_on_ms = P.ms; P.pmd_booted = false; P.unparked = false; }
    if (!powered) { P.pmd_booted = false; P.unparked = false; P.spi_word = 0; }
    P.pmd_powered = powered;
    if (powered && !P.pmd_booted && (P.ms - P.pmd_on_ms) >= P.pmd_boot_ms) { P.pmd_booted = true; }

    bool parked = P.sup_dead ? true : P.sup_parked;
    bool aen = !parked;
    if (aen != P.aen_last) { P.aen_last = aen; P.aen_change_ms = P.ms; }
    if (P.pmd_booted) {
        if (aen && !P.unparked && (P.ms - P.aen_change_ms) >= 100u) { P.unparked = true; }
        if (!aen && P.unparked && (P.ms - P.aen_change_ms) >= 250u) { P.unparked = false; } /* ASSUMED: keeps
                                                     stepping until the ~250 ms power-down completes */
    }

    /* PMD401 stops if no SPI word for about 10 ms */
    if (P.ms - P.spi_last_ms > 10u) { P.spi_word = 0; }

    double rate = 0.0;
    if (P.pmd_booted && P.unparked && P.v48 >= 45.6 && !P.pmd_fault) {
        rate = (double)P.spi_word * (1500.0 / 32767.0) * P.spi_scale_err;
        if (rate > 1500.0) { rate = 1500.0; }
        if (rate < -1500.0) { rate = -1500.0; }
    }
    double force = P.friction_n + P.p_bar * N_PER_BAR;
    double step = P.step_um_noload * (1.0 - force / P.stall_n);
    if (step < 0.0) { step = 0.0; }
    double dx = rate * step / 1000.0;           /* um in 1 ms */
    if (fabs(rate) > P.max_step_rate_hz) { P.max_step_rate_hz = fabs(rate); }
    if (fabs(dx) * 1000.0 > P.max_speed_um_s) { P.max_speed_um_s = fabs(dx) * 1000.0; }
    P.x_um += dx;

    double dv = AREA_MM2 * dx * 1e-3;           /* uL */
    double out = P.occluded ? 0.0 : P.p_bar * P.outflow_ul_s_bar / 1000.0;
    if (out < 0.0) { out = 0.0; }
    P.p_bar += (dv - out) / P.compliance_ul_bar;
    if (P.p_bar < 0.0) { P.p_bar = 0.0; }
    P.delivered_ul += out;
}
