/* BQ25188 charger service (TI SLUSFJ3). Charging is for charging only; the charger is never the load path. */
#ifndef CHARGER_H
#define CHARGER_H

#include <stdbool.h>
#include <stdint.h>

#define BQ_REG_STAT0      0x00u
#define BQ_REG_VBAT_CTRL  0x03u   /* VBATREG = 3.5 V + code x 10 mV; reset 0x46 = 4.20 V */
#define BQ_REG_ICHG_CTRL  0x04u   /* reset 0x05 = 10 mA */
#define BQ_REG_IC_CTRL    0x07u   /* reset 0x84; WATCHDOG_SEL 00 = 160 s, registers reset to default */

uint8_t charger_ichg_code(uint32_t ma);
void charger_tick(uint32_t now);
bool charger_ok(void);
uint8_t charger_stat0(void);

#endif
