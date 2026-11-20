/* PMD401 driver in servo mode (manual 150025-01 ch. 5): signed 16-bit SPI rate word, RS-485 queries.
 * The firmware never sends run/stop commands over RS-485: the manual says they disable servo mode. */
#ifndef PMD401_H
#define PMD401_H

#include <stdbool.h>
#include <stdint.h>

int16_t pmd_rate_to_word(int32_t rate_mhz);   /* milli-Hz waveform step rate -> SPI word, capped */

typedef enum { PQ_IDLE = 0, PQ_PENDING, PQ_SERVO_OK, PQ_NOT_SERVO, PQ_TIMEOUT } pmd_query_t;

void pmd_query_start(uint32_t now);
pmd_query_t pmd_query_poll(uint32_t now);
int pmd_last_y13(void);

#endif
