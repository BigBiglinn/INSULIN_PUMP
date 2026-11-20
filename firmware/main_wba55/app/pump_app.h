/* Top level of the main MCU application. Call pump_app_init() once after the CubeMX initialisation and
 * pump_app_tick() every 1 ms (SysTick flag polled in the main loop). */
#ifndef PUMP_APP_H
#define PUMP_APP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "ble_cmd.h"
#include "dose_limits.h"
#include "dose_ctrl.h"

void pump_app_init(void);
void pump_app_tick(void);

/* BLE entry point (call from the GATT write handler of the dose-command characteristic) */
ble_rx_t pump_app_ble_rx(const uint8_t *p, size_t n);

/* direct entry used by the bench console / host tests; applies the same limits as BLE (C-04) */
lim_result_t pump_app_request_bolus(uint32_t mu);
lim_result_t pump_app_set_basal(uint32_t mu_per_h);
void pump_app_stop(void);
void pump_app_clear_fault(void);

bool pump_app_battery_low(void);
uint32_t pump_app_basal_mu_h(void);
/* last completed dose record and the number of completed doses since start */
const dose_record_t *pump_app_last(uint32_t *count);

#endif
