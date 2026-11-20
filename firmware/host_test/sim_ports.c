/* pump_port.h and sup_port.h implemented on top of the plant model, for the host tests. */
#include "sim_plant.h"
#include "../main_wba55/app/pump_port.h"
#include "../supervisor_c031/app/sup_port.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int sim_verbose = 0;
bool sim_ble_secure = true;
uint8_t sim_ble_last_notify[16];

/* byte queues for the two link directions */
typedef struct { uint8_t b[4096]; size_t h, t; } q_t;
static q_t q_m2s, q_s2m;
static void q_put(q_t *q, const uint8_t *p, size_t n) { for (size_t i = 0; i < n; i++) { q->b[q->h] = p[i]; q->h = (q->h + 1u) % sizeof q->b; } }
static size_t q_get(q_t *q, uint8_t *p, size_t max)
{
    size_t n = 0;
    while (n < max && q->t != q->h) { p[n++] = q->b[q->t]; q->t = (q->t + 1u) % sizeof q->b; }
    return n;
}
static char rs485_reply[64];

void sim_ports_reset(void)
{
    memset(&q_m2s, 0, sizeof q_m2s); memset(&q_s2m, 0, sizeof q_s2m);
    rs485_reply[0] = '\0'; sim_ble_secure = true;
}

/* ---------------- main MCU ---------------- */
uint32_t port_ms(void) { return P.ms; }
void port_set_48v_enable(bool on) { P.mcu_en = on; }
bool port_fly_pgood(void) { return plant_pgood(); }
bool port_pmd_ready(void) { return plant_ready_line_low(); }
bool port_pmd_fault(void) { return plant_fault_line_high(); }
void port_pmd_spi_enable(bool e) { P.spi_enabled = e; }
void port_pmd_spi_write(int16_t w) { plant_spi_write(w); }
void port_rs485_send(const char *line) { plant_rs485_rx_line(line, rs485_reply, sizeof rs485_reply); }
bool port_rs485_get_line(char *buf, size_t n)
{
    if (rs485_reply[0] == '\0') { return false; }
    snprintf(buf, n, "%s", rs485_reply); rs485_reply[0] = '\0';
    return true;
}
uint32_t port_enc_raw(void) { return (uint32_t)(uint16_t)plant_counts(); }   /* exercise the 16-bit extension */
unsigned port_enc_bits(void) { return 16u; }
void port_link_send(const uint8_t *p, size_t n) { if (!P.link_cut) { q_put(&q_m2s, p, n); } }
size_t port_link_recv(uint8_t *p, size_t max) { return q_get(&q_s2m, p, max); }
uint16_t port_vbat_mv(void) { return P.vbat_mv; }
bool port_i2c_write(uint8_t a, uint8_t r, uint8_t v) { (void)a; (void)r; (void)v; return true; }
bool port_i2c_read(uint8_t a, uint8_t r, uint8_t *v) { (void)a; (void)r; *v = 0; return true; }
void port_log(const char *s) { if (sim_verbose) { printf("  [main %6u] %s", P.ms, s); } }
void port_led(bool on) { (void)on; }
void port_wdg_kick(void) { }
uint32_t port_random(void) { static uint32_t x = 0x12345678u; x ^= x << 13; x ^= x >> 17; x ^= x << 5; return x; }
bool port_ble_link_secure(void) { return sim_ble_secure; }
void port_ble_notify(const uint8_t *p, size_t n) { memcpy(sim_ble_last_notify, p, n < 16 ? n : 16); }

/* ---------------- supervisor ---------------- */
uint32_t sport_ms(void) { return P.ms; }
void sport_set_veto(bool v) { P.sup_veto = v; }
void sport_set_parked(bool p) { P.sup_parked = p; }
uint16_t sport_enc_raw16(void) { return (uint16_t)plant_counts(); }
void sport_link_send(const uint8_t *p, size_t n) { if (!P.link_cut) { q_put(&q_s2m, p, n); } }
size_t sport_link_recv(uint8_t *p, size_t max) { return q_get(&q_m2s, p, max); }
void sport_log(const char *s) { if (sim_verbose) { printf("  [sup  %6u] %s", P.ms, s); } }
void sport_led(bool on) { (void)on; }
void sport_wdg_kick(void) { }
