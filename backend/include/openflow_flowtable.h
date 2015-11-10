#ifndef __FLOWTABLE_H_
#define __FLOWTABLE_H_

#include <stdint.h>
#include <time.h>

#include "openflow.h"
#include "message.h"
#include "simplequeue.h"

#define OPENFLOW_MAX_FLOWTABLES            ((uint32_t) 10)
#define OPENFLOW_MAX_FLOWTABLE_ENTRIES     ((uint32_t) 10)
#define OPENFLOW_MAX_ACTIONS               ((uint32_t) 10)

typedef struct ofp_action_header	ofp_action_header;
typedef struct ofp_action_output	ofp_action_output;
typedef struct ofp_action_vlan_vid	ofp_action_vlan_vid;
typedef struct ofp_action_vlan_pcp	ofp_action_vlan_pcp;
typedef struct ofp_action_dl_addr	ofp_action_dl_addr;
typedef struct ofp_action_nw_addr	ofp_action_nw_addr;
typedef struct ofp_action_tp_port	ofp_action_tp_port;
typedef struct ofp_action_nw_tos	ofp_action_nw_tos;
typedef struct ofp_table_stats		ofp_table_stats;
typedef struct ofp_flow_stats		ofp_flow_stats;
typedef struct ofp_match			ofp_match;
typedef struct ofp_flow_mod			ofp_flow_mod;
typedef struct ofp_error_msg		ofp_error_msg;

typedef struct
{
	ofp_action_header	header;
	uint8_t				action[8];
} openflow_flowtable_action_wrapper_type;

typedef struct
{
	uint8_t									active;
	openflow_flowtable_action_wrapper_type	action;
} openflow_flowtable_action_type;

typedef struct
{
	uint8_t							active;
	openflow_flowtable_match_type	match;
	time_t							last_matched;
	time_t							last_modified;
	uint16_t						idle_timeout;
	uint16_t						hard_timeout;
	uint32_t						priority;
	uint16_t						flags;
	openflow_flowtable_action_type	actions[OPENFLOW_MAX_ACTIONS];
	ofp_flow_stats					stats;
} openflow_flowtable_entry_type;

typedef struct
{
	openflow_flowtable_entry_type	entries[OPENFLOW_MAX_FLOWTABLE_ENTRIES];
	ofp_table_stats					stats;
} openflow_flowtable_type;

extern openflow_flowtable_type *flowtable;

/**
 * Initializes the flowtable.
 *
 * @param classical_work_queue A pointer to the work queue used for classical
 *                             packet processing. This is used when Forwarding
 *                             packets to the OpenFlow NORMAL port.
 */
void openflow_flowtable_init(simplequeue_t *classical_work_queue);

/**
 * Processes the specified packet using the OpenFlow pipeline.
 *
 * @param packet       The packet to be handled.
 * @param output_queue The output queue of the packet core.
 */
void openflow_flowtable_handle_packet(gpacket_t *packet,
	simplequeue_t *output_queue)

/**
* Applies the specified modification to the flowtables.
*
* @param modify_info The modification to apply to the flowtables.
* @param error_msg   A pointer to an empty ofp_error_msg struct that will be
*                    populated if an error occurs.
*
* @return 0 if no error occurred, -1 otherwise.
*/
uint8_t openflow_flowtable_modify(ofp_flow_mod* flow_mod,
	ofp_error_msg* error_msg)

#endif // ifndef __FLOWTABLE_H_
