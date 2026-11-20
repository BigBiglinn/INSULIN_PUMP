#include "pmd401.h"
#include "pump_config.h"
#include "pump_port.h"

int16_t pmd_rate_to_word(int32_t rate_mhz)
{
    /* firmware speed cap (K-15) applied before scaling */
    const int32_t cap = CFG_RATE_CAP_HZ * 1000;
    if (rate_mhz > cap) { rate_mhz = cap; }
    if (rate_mhz < -cap) { rate_mhz = -cap; }
    int64_t w = ((int64_t)rate_mhz * CFG_PMD_SPI_FULLSCALE) / ((int64_t)CFG_PMD_MAX_RATE_HZ * 1000);
    return (int16_t)w;
}

static pmd_query_t q_state = PQ_IDLE;
static uint32_t q_start, q_last_tx;
static int q_y13 = -1;

void pmd_query_start(uint32_t now)
{
    char drain[32];
    while (port_rs485_get_line(drain, sizeof drain)) { }   /* discard stale input */
    q_state = PQ_PENDING; q_start = now; q_last_tx = now - CFG_PMD_QUERY_PERIOD_MS; q_y13 = -1;
}

/* parse "...Y13:<n>" */
static int parse_y13(const char *s)
{
    for (; s[0] != '\0'; s++) {
        if (s[0] == 'Y' && s[1] == '1' && s[2] == '3' && s[3] == ':') {
            const char *p = s + 4; int v = 0, digits = 0;
            while (*p >= '0' && *p <= '9' && digits < 4) { v = v * 10 + (*p - '0'); p++; digits++; }
            return digits ? v : -1;
        }
    }
    return -1;
}

pmd_query_t pmd_query_poll(uint32_t now)
{
    if (q_state != PQ_PENDING) { return q_state; }
    char line[48];
    while (port_rs485_get_line(line, sizeof line)) {
        int v = parse_y13(line);
        if (v >= 0) {
            q_y13 = v;
            q_state = (v == 3 || !CFG_PMD_REQUIRE_SERVO) ? PQ_SERVO_OK : PQ_NOT_SERVO;
            return q_state;
        }
    }
    if ((now - q_start) >= CFG_PMD_BOOT_TIMEOUT_MS) {
        q_state = PQ_TIMEOUT;
        return q_state;
    }
    if ((now - q_last_tx) >= CFG_PMD_QUERY_PERIOD_MS) {
        q_last_tx = now;
        port_rs485_send("X0Y13\r");     /* read encoder-type setting; 3 = servo (SPI slave) */
    }
    return q_state;
}

int pmd_last_y13(void) { return q_y13; }
