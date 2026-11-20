/* Hardware boundary of the main MCU firmware (K-16, F-01). Everything above this file is plain C11 and
 * runs unchanged on the PC simulator (firmware/host_test) and on the STM32WBA55 (port/port_stm32wba.c).
 * All functions are non-blocking.
 */
#ifndef PUMP_PORT_H
#define PUMP_PORT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

uint32_t port_ms(void);                       /* free-running millisecond counter */

/* 48 V rail and PMD401 status (sheet "Kill path", "PMD401 & encoder interface") */
void port_set_48v_enable(bool on);            /* PB7 MCU_48V_EN -> R402 -> FLY_EN */
bool port_fly_pgood(void);                    /* PA12 FLY_PGOOD, true = LM51551 power good */
bool port_pmd_ready(void);                    /* PB15, true when READY line is LOW (= ready to run) */
bool port_pmd_fault(void);                    /* PB4, true when FAULT line is HIGH (= error) */

/* PMD401 SPI (SPI3, mode 3, <= 500 kbit/s). enable=false puts the pins in analog mode so an unpowered
 * PMD401 is not back-fed (ECO2); enable only after FLY_PGOOD. */
void port_pmd_spi_enable(bool enable);
void port_pmd_spi_write(int16_t rate_word);

/* PMD401 RS-485 set-up link (USART2 + DE, MAX3485), 115200 8N1, ASCII lines ending in CR */
void port_rs485_send(const char *line);       /* starts transmission, returns immediately */
bool port_rs485_get_line(char *buf, size_t n);/* true when a complete CR-terminated line was received */

/* LL06 encoder on TIM2 (encoder mode). Raw counter value; width given by port_enc_bits(). */
uint32_t port_enc_raw(void);
unsigned port_enc_bits(void);                 /* 16 or 32 (TIM2 width to be confirmed in RM0493, CF-21) */

/* supervisor link (LPUART1) */
void port_link_send(const uint8_t *p, size_t n);
size_t port_link_recv(uint8_t *p, size_t max);

/* battery voltage at the cell in mV (VBAT_SENSE = VBAT / 2 on ADC4_IN10, VREFINT-corrected) */
uint16_t port_vbat_mv(void);

/* BQ25188 on I2C3 */
bool port_i2c_write(uint8_t addr7, uint8_t reg, uint8_t val);
bool port_i2c_read(uint8_t addr7, uint8_t reg, uint8_t *val);

/* misc */
void port_log(const char *s);                 /* USART1 TX-only console */
void port_led(bool on);
void port_wdg_kick(void);
uint32_t port_random(void);                   /* RNG peripheral */

/* BLE glue: the CubeWBA BLE application calls pump_app_ble_rx() from the GATT write handler and
 * reports link security here. */
bool port_ble_link_secure(void);              /* encrypted, bonded, LE Secure Connections (C-02) */
void port_ble_notify(const uint8_t *p, size_t n);

#endif
