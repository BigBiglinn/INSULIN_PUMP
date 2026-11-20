#include "charger.h"
#include "pump_config.h"
#include "pump_port.h"

static uint32_t last = 0u;
static bool first = true, ok = false;
static uint8_t stat0 = 0u;

uint8_t charger_ichg_code(uint32_t ma)
{
    /* SLUSFJ3 Table 7-13: ICHG <= 35 mA: code + 5 mA; ICHG > 35 mA: 40 + (code - 31) x 10 mA; max 1000 mA */
    if (ma > 1000u) { ma = 1000u; }
    if (ma <= 35u) { return (uint8_t)((ma < 5u) ? 0u : (ma - 5u)); }
    if (ma < 40u) { ma = 40u; }
    return (uint8_t)(31u + (ma - 40u) / 10u);
}

/* Re-writes the settings periodically: the I2C watchdog (160 s default) resets every R/W register
 * to its default if the host stops talking, which would drop the charge current back to 10 mA.
 * Leaving the watchdog enabled is deliberate: if this MCU dies, the charger falls back to 10 mA. */
void charger_tick(uint32_t now)
{
    if (!first && (now - last) < CFG_CHG_SERVICE_MS) { return; }
    first = false; last = now;
    bool a = port_i2c_write(CFG_CHG_I2C_ADDR, BQ_REG_VBAT_CTRL, 70u);   /* 4.20 V (E-09) */
    bool b = port_i2c_write(CFG_CHG_I2C_ADDR, BQ_REG_ICHG_CTRL, charger_ichg_code(CFG_CHG_ICHG_MA));
    bool c = port_i2c_read(CFG_CHG_I2C_ADDR, BQ_REG_STAT0, &stat0);
    ok = a && b && c;
    if (!ok) { port_log("CHG: I2C error\r\n"); }
}

bool charger_ok(void) { return ok; }
uint8_t charger_stat0(void) { return stat0; }
