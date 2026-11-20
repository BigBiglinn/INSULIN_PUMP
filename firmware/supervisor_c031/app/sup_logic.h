/* Supervisor logic: it can only STOP. It grants 48 V and unparks the motor for one authorised dose at a
 * time, watches the heartbeat token, counts the encoder itself (S-07) and trips (veto ON + park, latched)
 * on any anomaly. Call sup_init() once and sup_tick() every 1 ms. */
#ifndef SUP_LOGIC_H
#define SUP_LOGIC_H

#include <stdbool.h>
#include <stdint.h>
#include "../../common/link_proto.h"

void sup_init(void);
void sup_tick(void);

sup_state_t sup_state(void);
trip_reason_t sup_trip(void);
int32_t sup_pos(void);
uint32_t sup_hour_counts(void);
const char *sup_trip_name(trip_reason_t t);

#endif
