/* Dose state machine (F-02): IDLE -> REQUEST -> RAIL_UP -> UNPARK -> MOVE -> SETTLE -> PARKING -> IDLE,
 * FAULT reachable from every state. Closed-loop position control on the LL06 encoder to an absolute
 * target, approached from one side only (D-09). Talks to the supervisor every 20 ms. */
#ifndef DOSE_CTRL_H
#define DOSE_CTRL_H

#include <stdbool.h>
#include <stdint.h>
#include "../../common/link_proto.h"

typedef enum {
    FLT_NONE = 0,
    FLT_LINK_LOST, FLT_SUP_TRIP, FLT_SUP_STATE, FLT_GRANT_TIMEOUT,
    FLT_PGOOD_TIMEOUT, FLT_PGOOD_LOST, FLT_PMD_BOOT_TIMEOUT, FLT_PMD_NOT_SERVO,
    FLT_READY_TIMEOUT, FLT_PMD_FAULT, FLT_PMD_NOT_READY,
    FLT_OCCLUSION, FLT_STALL, FLT_DOSE_ERROR, FLT_MOVE_TIMEOUT, FLT_INTEGRITY, FLT_OVERSPEED,
    FLT__COUNT
} fault_t;

typedef enum { RES_NONE = 0, RES_DONE, RES_ABORTED, RES_FAULT } dose_result_t;

typedef struct {
    uint8_t dose_id;
    uint32_t req_mu;
    uint32_t target_counts;
    int32_t delivered_counts;
    uint32_t delivered_mu;
    dose_result_t result;
    fault_t fault;
    uint32_t t_start, t_end;
} dose_record_t;

void dose_init(void);
void dose_tick(void);                    /* call every 1 ms */
bool dose_start(uint32_t mu);            /* caller has already run limits_check(); false if not idle */
void dose_abort(void);                   /* user STOP or low battery: stop cleanly, not a fault */
void dose_clear_fault(void);

main_state_t dose_state(void);
fault_t dose_fault(void);
const char *dose_fault_name(fault_t f);
bool dose_link_alive(void);
sup_state_t dose_sup_state(void);
uint8_t dose_sup_trip(void);
int32_t dose_position(void);
int32_t dose_sup_count(void);
bool dose_last(dose_record_t *r);        /* returns true once per completed dose (consumes it) */

#ifdef PUMP_TEST
void dose_test_runaway(int16_t word);    /* FT-02: command a fixed SPI word in MOVE, ignoring the target */
void dose_test_skip_link(bool skip);     /* FT-04: stop sending heartbeat frames */
void dose_test_corrupt_target(void);     /* FT-12 */
#endif

#endif
