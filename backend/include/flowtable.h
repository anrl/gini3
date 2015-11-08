#ifndef __FLOWTABLE_H_
#define __FLOWTABLE_H_

#include <stdint.h>

#include "openflow.h"

#define OPENFLOW_MAX_FLOWTABLE_ENTRIES     ((int32_t) 10)
#define OPENFLOW_MAX_ACTIONS               ((int32_t) 10)

typedef struct ofp_table_stats    openflow_flowtable_stats_type;
typedef struct ofp_flow_stats     openflow_flowtable_entry_stats_type;
typedef struct ofp_match          openflow_flowtable_match_type;
typedef struct ofp_action_header  openflow_flowtable_action_header_type;
typedef enum ofp_flow_wildcards   openflow_flowtable_wildcards;

typedef struct {
    openflow_flowtable_action_header_type header;
    uint8_t action[8];
} openflow_flowtable_action_type;

typedef struct {
    uint8_t active;
    openflow_flowtable_match_type match;
    uint32_t priority;
    openflow_flowtable_action_type actions[OPENFLOW_MAX_ACTIONS];
    openflow_flowtable_stats_type stats;
} openflow_flowtable_entry_type;

typedef struct {
    openflow_flowtable_entry_type entries[OPENFLOW_MAX_FLOWTABLE_ENTRIES];
    openflow_flowtable_stats_type stats;
} openflow_flowtable_type;

extern openflow_flowtable_type *flowtable;

void flowtable_handle_packet(gpacket_t *packet);

#endif // ifndef __FLOWTABLE_H_
