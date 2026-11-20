#include "ble_cmd.h"
#include "../../common/link_proto.h"

static uint32_t last_counter;
static bool have_counter;

void ble_cmd_init(void) { last_counter = 0u; have_counter = false; }

static uint32_t g32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

ble_rx_t ble_cmd_parse(const uint8_t *p, size_t n, bool secure, ble_cmd_t *out)
{
    if (!secure) { return BR_INSECURE; }
    if (n != BLE_PKT_LEN) { return BR_LENGTH; }
    uint16_t crc = (uint16_t)(((uint16_t)p[9] << 8) | p[10]);
    if (link_crc16(p, 9u) != crc) { return BR_CRC; }
    uint32_t ctr = g32(&p[1]);
    if (have_counter && ctr <= last_counter) { return BR_REPLAY; }
    if (p[0] < BOP_BOLUS || p[0] > BOP_STATUS) { return BR_BAD_OP; }
    last_counter = ctr; have_counter = true;
    out->op = p[0]; out->counter = ctr; out->arg = g32(&p[5]);
    return BR_OK;
}

size_t ble_cmd_build(uint8_t op, uint32_t counter, uint32_t arg, uint8_t *o)
{
    o[0] = op;
    for (int i = 0; i < 4; i++) { o[1 + i] = (uint8_t)(counter >> (8 * i)); o[5 + i] = (uint8_t)(arg >> (8 * i)); }
    uint16_t c = link_crc16(o, 9u);
    o[9] = (uint8_t)(c >> 8); o[10] = (uint8_t)c;
    return BLE_PKT_LEN;
}
