/* Dose command packets received over BLE (U-11, C-01..C-04).
 *
 * Packet (11 bytes): op(u8) | counter(u32 LE) | arg(u32 LE) | crc16(BE, CCITT-FALSE over the first 9 bytes)
 *
 * Accepted only when the link is encrypted and bonded with LE Secure Connections (C-02), the CRC matches,
 * and the counter is strictly greater than the last accepted one (replay protection, C-03).
 * NOTE: a CRC detects corruption, not deliberate tampering. Integrity against an attacker comes from the
 * LE link encryption (AES-CCM MIC). An application-level MAC (C-03 "check value") is still OPEN.
 */
#ifndef BLE_CMD_H
#define BLE_CMD_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define BLE_PKT_LEN 11u

typedef enum {
    BOP_BOLUS = 0x01,        /* arg = mU */
    BOP_SET_BASAL = 0x02,    /* arg = mU per hour (0 = basal off) */
    BOP_STOP = 0x03,         /* stop delivery and basal */
    BOP_CLEAR_FAULT = 0x04,
    BOP_STATUS = 0x05
} ble_op_t;

typedef enum {
    BR_OK = 0, BR_INSECURE, BR_LENGTH, BR_CRC, BR_REPLAY, BR_BAD_OP
} ble_rx_t;

typedef struct { uint8_t op; uint32_t counter; uint32_t arg; } ble_cmd_t;

void ble_cmd_init(void);
ble_rx_t ble_cmd_parse(const uint8_t *p, size_t n, bool secure, ble_cmd_t *out);
size_t ble_cmd_build(uint8_t op, uint32_t counter, uint32_t arg, uint8_t *out);  /* for tests and the phone app */

#endif
