#ifndef __FLOWTABLE_H_
#define __FLOWTABLE_H_

#include <stdint.h>

#include "openflow.h"
#include "message.h"
#include "simplequeue.h"

#define OPENFLOW_MAX_FLOWTABLES            ((uint8_t) 10)
#define OPENFLOW_MAX_FLOWTABLE_ENTRIES     ((uint8_t) 10)
#define OPENFLOW_MAX_ACTIONS               ((uint8_t) 10)

typedef struct ofp_table_stats    openflow_flowtable_stats_type;
typedef struct ofp_flow_stats     openflow_flowtable_entry_stats_type;
typedef struct ofp_match          openflow_flowtable_match_type;
typedef struct ofp_action_header  openflow_flowtable_action_header_type;
typedef enum ofp_flow_wildcards   openflow_flowtable_wildcards;
typedef struct ofp_action_output  openflow_flowtable_action_output_type;

typedef struct {
    openflow_flowtable_action_header_type header;
    uint8_t action[4];
} openflow_flowtable_action_wrapper_type;

typedef struct {
    uint8_t active;
    openflow_flowtable_action_wrapper_type action;
} openflow_flowtable_action_type;

typedef struct {
    uint8_t active;
    openflow_flowtable_match_type match;
    uint32_t priority;
    openflow_flowtable_action_type actions[OPENFLOW_MAX_ACTIONS];
    openflow_flowtable_stats_type stats;
} openflow_flowtable_entry_type;

typedef struct {
    uint8_t active;
    openflow_flowtable_entry_type entries[OPENFLOW_MAX_FLOWTABLE_ENTRIES];
    openflow_flowtable_stats_type stats;
} openflow_flowtable_type;

extern openflow_flowtable_type *flowtables[OPENFLOW_MAX_FLOWTABLES];

void flowtable_init(simplequeue_t *classical_work_queue);
void flowtable_handle_packet(gpacket_t *packet,
                             simplequeue_t *output_queue);

#endif // ifndef __FLOWTABLE_H_
