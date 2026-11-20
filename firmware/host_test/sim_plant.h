/* PC model of the hardware around the two MCUs: kill path, LM51551 rail, PMD401, LL06, syringe and line.
 * It is an ASSUMED plant (behaviour from the PMD401 manual and the project's design numbers), not a
 * validated model. Its purpose is to exercise the firmware logic, not to predict accuracy on hardware. */
#ifndef SIM_PLANT_H
#define SIM_PLANT_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    /* parameters */
    double step_um_noload;      /* LL06 no-load full step (2..8 um, 4.5 typical) */
    double friction_n;          /* plunger friction */
    double stall_n;             /* 6.5 N */
    double spi_scale_err;       /* actual/assumed SPI rate scale, 1.0 = as assumed */
    double compliance_ul_bar;   /* line compliance */
    double outflow_ul_s_bar;    /* open-line conductance */
    bool occluded;
    bool servo_mode;            /* PMD401 Y13 == 3 */
    uint32_t pmd_boot_ms;       /* boot time after 48 V rises (unknown on hardware, MT-07) */
    bool pmd_fault;             /* FAULT line asserted */
    bool enc_frozen;            /* encoder wire lost */
    uint16_t vbat_mv;
    bool main_halted;           /* main MCU stopped (debugger halt): outputs keep their last state */
    bool sup_dead;              /* supervisor in reset/unpowered: pins high-Z -> pull-ups -> veto ON, parked */
    bool link_cut;              /* heartbeat wires open */

    /* pins driven by the MCUs */
    bool mcu_en, sup_veto, sup_parked, spi_enabled;

    /* state */
    uint32_t ms;
    double v48;
    bool pmd_powered;
    uint32_t pmd_on_ms;
    bool pmd_booted;
    bool unparked;              /* motor powered up (after AEN high + 100 ms) */
    uint32_t aen_change_ms;
    bool aen_last;
    int16_t spi_word;
    uint32_t spi_last_ms;
    double x_um;                /* plunger position */
    double p_bar;
    double delivered_ul;
    double max_step_rate_hz;    /* highest stepping rate actually reached */
    double max_speed_um_s;
} plant_t;

extern plant_t P;

void plant_reset(void);
void plant_step(void);           /* advance 1 ms */
bool plant_pgood(void);
bool plant_ready_line_low(void); /* READY as seen at the MCU pin (LOW when unpowered: level shifter) */
bool plant_fault_line_high(void);
int32_t plant_counts(void);
void plant_spi_write(int16_t w);
void plant_rs485_rx_line(const char *line, char *reply, int n);  /* returns "" if no answer */

#endif
