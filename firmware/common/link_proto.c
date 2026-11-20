#include "link_proto.h"

uint16_t link_crc16(const uint8_t *p, size_t n)
{
    uint16_t crc = 0xFFFFu;                     /* CRC-16/CCITT-FALSE, poly 0x1021 */
    for (size_t i = 0; i < n; i++) {
        crc ^= (uint16_t)((uint16_t)p[i] << 8);
        for (int b = 0; b < 8; b++) {
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
        }
    }
    return crc;
}

static void put32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24);
}

static uint32_t get32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static size_t frame(uint8_t type, const uint8_t *pl, uint8_t len, uint8_t *out)
{
    out[0] = LINK_SOF; out[1] = type; out[2] = len;
    for (uint8_t i = 0; i < len; i++) {
        out[3u + i] = pl[i];
    }
    uint16_t c = link_crc16(&out[1], (size_t)len + 2u);
    out[3u + len] = (uint8_t)(c >> 8);
    out[4u + len] = (uint8_t)c;
    return (size_t)len + 5u;
}

size_t link_encode_m2s(const m2s_t *m, uint8_t *out)
{
    uint8_t pl[8] = { m->seq, m->state, m->dose_id, m->cmd, 0, 0, 0, 0 };
    put32(&pl[4], m->auth_counts);
    return frame(LINK_T_M2S, pl, 8u, out);
}

size_t link_encode_s2m(const s2m_t *s, uint8_t *out)
{
    uint8_t pl[8] = { s->seq_echo, s->state, s->dose_id, s->trip, 0, 0, 0, 0 };
    put32(&pl[4], (uint32_t)s->sup_count);
    return frame(LINK_T_S2M, pl, 8u, out);
}

void link_rx_init(link_rx_t *rx)
{
    rx->idx = 0u;
    rx->need = 0u;
}

/* returns the payload length of a complete valid frame of 'type', or -1 */
static int rx_push(link_rx_t *rx, uint8_t byte, uint8_t type)
{
    if (rx->idx == 0u) {
        if (byte == LINK_SOF) {
            rx->buf[rx->idx++] = byte;
        }
        return -1;
    }
    rx->buf[rx->idx++] = byte;
    if (rx->idx == 3u) {
        if (rx->buf[2] > LINK_MAX_PAYLOAD) {
            rx->idx = 0u;
            return -1;
        }
        rx->need = (uint8_t)(rx->buf[2] + 5u);
    }
    if (rx->idx >= 3u && rx->idx == rx->need) {
        uint8_t len = rx->buf[2];
        uint16_t c = link_crc16(&rx->buf[1], (size_t)len + 2u);
        uint16_t got = (uint16_t)(((uint16_t)rx->buf[3u + len] << 8) | rx->buf[4u + len]);
        rx->idx = 0u;
        if (c == got && rx->buf[1] == type) {
            return (int)len;
        }
        return -1;
    }
    if (rx->idx >= LINK_MAX_FRAME) {
        rx->idx = 0u;
    }
    return -1;
}

bool link_rx_push_m2s(link_rx_t *rx, uint8_t byte, m2s_t *m)
{
    if (rx_push(rx, byte, LINK_T_M2S) != 8) {
        return false;
    }
    const uint8_t *p = &rx->buf[3];
    m->seq = p[0]; m->state = p[1]; m->dose_id = p[2]; m->cmd = p[3];
    m->auth_counts = get32(&p[4]);
    return true;
}

bool link_rx_push_s2m(link_rx_t *rx, uint8_t byte, s2m_t *s)
{
    if (rx_push(rx, byte, LINK_T_S2M) != 8) {
        return false;
    }
    const uint8_t *p = &rx->buf[3];
    s->seq_echo = p[0]; s->state = p[1]; s->dose_id = p[2]; s->trip = p[3];
    s->sup_count = (int32_t)get32(&p[4]);
    return true;
}
