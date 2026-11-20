/* Main MCU <-> supervisor link (heartbeat) protocol. Shared by both firmwares.
 *
 * Physical link: WBA55 LPUART1 (PB5 TX / PA1 RX) <-> C031 USART2 (PA3 RX / PA2 TX), 115200 8N1.
 * The main MCU sends one M2S frame every LINK_PERIOD_MS; the supervisor answers each valid frame
 * with one S2M frame. The heartbeat is a changing token (F-09): the main sequence number must advance
 * by exactly one per frame, so a stuck line, a replayed frame or a frozen main loop is not a heartbeat.
 *
 * Frame: 0xA5 | type | len | payload[len] | crc16_hi | crc16_lo   (CRC-16/CCITT-FALSE over type..payload)
 *
 * BENCH-ONLY PROTOTYPE: water or saline, never on a person or an animal.
 */
#ifndef LINK_PROTO_H
#define LINK_PROTO_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define LINK_SOF            0xA5u
#define LINK_T_M2S          0x01u
#define LINK_T_S2M          0x02u
#define LINK_MAX_PAYLOAD    16u
#define LINK_MAX_FRAME      (LINK_MAX_PAYLOAD + 5u)
#define LINK_PERIOD_MS      20u     /* main sends a frame every 20 ms */
#define LINK_TIMEOUT_MS     100u    /* no valid frame for this long = link lost */

/* Main MCU state as reported to the supervisor */
typedef enum {
    MST_IDLE = 0,       /* nothing moving, 48 V off */
    MST_REQUEST = 1,    /* asking permission for dose dose_id of auth_counts counts */
    MST_RAIL_UP = 2,    /* 48 V enable driven, waiting for FLY_PGOOD and PMD401 boot */
    MST_UNPARK_REQ = 3, /* rail good, asks the supervisor to unpark */
    MST_MOVE = 4,
    MST_SETTLE = 5,
    MST_PARKING = 6,    /* dose finished or aborted: please park and veto */
    MST_FAULT = 7
} main_state_t;

/* Supervisor state as reported to the main MCU */
typedef enum {
    SST_SAFE = 0,       /* veto ON, motor parked */
    SST_GRANTED = 1,    /* veto OFF (48 V allowed), motor still parked */
    SST_RUN = 2,        /* veto OFF, motor unparked */
    SST_TRIP = 3        /* latched: veto ON, parked; needs CLEAR from the main MCU */
} sup_state_t;

typedef enum {
    TRIP_NONE = 0,
    TRIP_LINK_LOST = 1,
    TRIP_SEQ_ERROR = 2,
    TRIP_RATE = 3,          /* encoder speed above the supervisor limit (S-06 backstop) */
    TRIP_OVERTRAVEL = 4,    /* travel beyond the authorised counts */
    TRIP_REVERSE = 5,
    TRIP_TIMEOUT = 6,
    TRIP_MAIN_FAULT = 7,
    TRIP_UNEXPECTED_MOTION = 8,
    TRIP_BAD_REQUEST = 9    /* request over the per-dose or rolling-hour limit */
} trip_reason_t;

#define M2S_CMD_NONE        0u
#define M2S_CMD_CLEAR_TRIP  0xC1u

typedef struct {
    uint8_t seq;            /* +1 per frame (token) */
    uint8_t state;          /* main_state_t */
    uint8_t dose_id;        /* 1..255, changes for every new dose */
    uint8_t cmd;            /* M2S_CMD_* */
    uint32_t auth_counts;   /* encoder counts requested for this dose */
} m2s_t;

typedef struct {
    uint8_t seq_echo;       /* echo of the last valid main seq */
    uint8_t state;          /* sup_state_t */
    uint8_t dose_id;        /* dose the state refers to */
    uint8_t trip;           /* trip_reason_t (latched) */
    int32_t sup_count;      /* supervisor's own encoder position */
} s2m_t;

uint16_t link_crc16(const uint8_t *p, size_t n);
size_t link_encode_m2s(const m2s_t *m, uint8_t *out);
size_t link_encode_s2m(const s2m_t *s, uint8_t *out);

/* Byte-wise receiver. link_rx_push() returns true when a complete, CRC-valid frame of the
 * expected type has been received; the decoded frame is then in *m2s or *s2m. */
typedef struct {
    uint8_t buf[LINK_MAX_FRAME];
    uint8_t idx;
    uint8_t need;
} link_rx_t;

void link_rx_init(link_rx_t *rx);
bool link_rx_push_m2s(link_rx_t *rx, uint8_t byte, m2s_t *m2s);
bool link_rx_push_s2m(link_rx_t *rx, uint8_t byte, s2m_t *s2m);

#endif
