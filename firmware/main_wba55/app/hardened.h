/* Fault-injection hardening helpers (F-03): values stored with their complement, encoded booleans,
 * doubled checks separated by a random delay, and a control-flow counter.
 * These raise the cost of a single glitch or bit flip; they are not a proof of glitch resistance (C-07).
 */
#ifndef HARDENED_H
#define HARDENED_H

#include <stdbool.h>
#include <stdint.h>

typedef struct { uint32_t v; uint32_t nv; } hu32_t;

#define H_TRUE   0x5AA5C33Cu
#define H_FALSE  0xA55A3CC3u

static inline void hu32_set(volatile hu32_t *h, uint32_t v) { h->v = v; h->nv = ~v; }
static inline bool hu32_ok(const volatile hu32_t *h) { return (h->v ^ h->nv) == 0xFFFFFFFFu; }

/* Busy loop of 0..15 iterations so that two checks of the same condition do not fall at a fixed
 * distance in time from each other. */
static inline void h_jitter(uint32_t rnd)
{
    volatile uint32_t n = rnd & 0xFu;
    while (n != 0u) { n--; }
}

/* control-flow counter */
typedef struct { volatile uint32_t c; } hflow_t;
static inline void hflow_reset(hflow_t *f) { f->c = 0u; }
static inline void hflow_step(hflow_t *f, uint32_t k) { f->c += k; }
static inline bool hflow_check(const hflow_t *f, uint32_t expect) { return f->c == expect; }

#endif
