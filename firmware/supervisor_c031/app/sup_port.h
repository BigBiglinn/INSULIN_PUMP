/* Hardware boundary of the supervisor firmware. Implemented by port/port_stm32c0.c and by the host simulator. */
#ifndef SUP_PORT_H
#define SUP_PORT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

uint32_t sport_ms(void);
void sport_set_veto(bool veto_on);       /* PB0 SUP_VETO: HIGH (or high-Z, R403 pull-up) = veto ON = 48 V off */
void sport_set_parked(bool parked);      /* PB1 SUP_PARK: HIGH (or high-Z, R405 pull-up) = AEN low = parked */
uint16_t sport_enc_raw16(void);          /* TIM3 encoder counter (16-bit) on PA6/PA7 */
void sport_link_send(const uint8_t *p, size_t n);     /* USART2 to the main MCU */
size_t sport_link_recv(uint8_t *p, size_t max);
void sport_log(const char *s);           /* USART1 console */
void sport_led(bool on);
void sport_wdg_kick(void);

#endif
