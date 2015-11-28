#ifndef __OPENFLOW_FLOWTABLE_H_
#define __OPENFLOW_FLOWTABLE_H_

#include <stdint.h>
#include <time.h>

#include "openflow.h"
#include "openflow_config.h"
#include "message.h"
#include "packetcore.h"
#include "simplequeue.h"

// OpenFlow constants
#define OPENFLOW_NUM_TABLES					((uint32_t) 1)
#define OPENFLOW_MAX_FLOWTABLE_ENTRIES		((uint32_t) 10)
#define OPENFLOW_MAX_ACTIONS				((uint32_t) 10)
#define OPENFLOW_MAX_ACTION_SIZE			((uint32_t) 16)

// Ethernet constants not used anywhere else
#define IEEE_802_2_DSAP_SNAP	0xAA
#define IEEE_802_2_CTRL_8_BITS	0x03
#define ETHERTYPE_IEEE_802_1Q	0x8100

// OpenFlow struct typedefs
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

/**
 * Represents an OpenFlow action. This struct wraps the ofp_action_header and
 * associated data.
 */
typedef struct
{
	// Action header
	ofp_action_header header;
	// The rest of the OpenFLow action; this wrapper struct should be cast
	// to something else to get at this data
	uint8_t	action[OPENFLOW_MAX_ACTION_SIZE - sizeof(ofp_action_header)];
} openflow_flowtable_action_wrapper_type;

/**
 * Represents an OpenFlow action.
 */
typedef struct
{
	// 1 if this entry is active (i.e. not empty), 0 otherwise
	uint8_t									active;
	// The actual OpenFlow action (ofp_action_header and associated data)
	openflow_flowtable_action_wrapper_type	action;
} openflow_flowtable_action_type;

/**
 * Represents an entry in an OpenFlow flowtable.
 */
typedef struct
{
	// 1 if this entry is active (i.e. not empty), 0 otherwise
	uint8_t active;
	// Match headers
	ofp_match match;
	// Cookie (opaque data) from controller
	uint64_t cookie;
	// The last time this entry was matched against a packet
	time_t last_matched;
	// The last time this entry was modified by the controller
	time_t last_modified;
	// Number of seconds since last match before expiration of this entry;
	// stored in network byte format
	uint16_t idle_timeout;
	// Number of seconds since last modification before expiration of this
	// entry; stored in network byte format
	uint16_t hard_timeout;
	// Entry priority (only relevant for wildcards); stored in network byte
	// format
	uint32_t priority;
	// Entry flags (see ofp_flow_mod_flags); stored in network byte format
	uint16_t flags;
	// Entry actions
	openflow_flowtable_action_type actions[OPENFLOW_MAX_ACTIONS];
	// Entry stats
	ofp_flow_stats stats;
} openflow_flowtable_entry_type;

/**
 * Represents an OpenFlow flowtable.
 */
typedef struct
{
	// Table entries
	openflow_flowtable_entry_type	entries[OPENFLOW_MAX_FLOWTABLE_ENTRIES];
	// Table stats
	ofp_table_stats					stats;
} openflow_flowtable_type;

/**
 * Initializes the flowtable.
 */
void openflow_flowtable_init(void);

/**
 * Processes the specified packet using the OpenFlow pipeline.
 *
 * @param packet       The packet to be handled.
 * @param packet_core  The grouter packet core.
 */
void openflow_flowtable_handle_packet(gpacket_t *packet,
	pktcore_t *packet_core);

/**
* Applies the specified modification to the flowtables.
*
* @param modify_info The modification to apply to the flowtables.
* @param error_msg   A pointer to an empty ofp_error_msg struct that will be
*                    populated if an error occurs.
*
* @return 0 if no error occurred, -1 otherwise.
*/
int32_t openflow_flowtable_modify(ofp_flow_mod *flow_mod,
	ofp_error_msg *error_msg);

#endif // ifndef __OPENFLOW_FLOWTABLE_H_
