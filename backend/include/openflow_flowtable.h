/**
 * openflow_flowtable.h - OpenFlow flowtable
 */

#ifndef __OPENFLOW_FLOWTABLE_H_
#define __OPENFLOW_FLOWTABLE_H_

#include <stdint.h>
#include <time.h>

#include "openflow_defs.h"
#include "message.h"
#include "packetcore.h"
#include "simplequeue.h"

/**
 * Initializes the flowtable.
 */
void openflow_flowtable_init(void);

/**
 * Retrieves the matching flowtable entry for the specified packet.
 *
 * @param packet    The specified packet.
 * @param emergency Whether the controller is in emergency mode.
 *
 * @return The matching flowtable entry.
 */
openflow_flowtable_entry_type *openflow_flowtable_get_entry_for_packet(
        gpacket_t *packet);

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

/**
 * Deletes all non-emergency entries in the OpenFlow flowtable.
 */
void openflow_flowtable_delete_non_emergency_entries();

/**
 * Gets the table statistics for the OpenFlow flowtable.
 *
 * @return The table statistics for the OpenFlow flowtable.
 */
ofp_table_stats *openflow_flowtable_get_table_stats();

/**
 * Gets the table statistics for the emergency entries in the OpenFlow
 * flowtable.
 *
 * @return The table statistics for the emergency entries in the OpenFlow
 *         flowtable.
 */
ofp_table_stats *openflow_flowtable_get_emerg_table_stats();

/**
 * Retrieves the flow statistics for the first matching flow.
 *
 * @param match             A pointer to the match to match entries against.
 *                          The flow statistics for the first matching entry
 *                          will be returned.
 * @param out_port          The output port which entries are required to have
 *                          an action for to be matched, in network byte order.
 * @param index             The index at which to begin searching the
 *                          flowtable.
 * @param match_index       A pointer to a variable used to store the index of
 *                          the matching entry, if any.
 * @param table_index       The index of the table to read from.
 * @param ptr_to_flow_stats A pointer to an ofp_flow_stats struct pointer. The
 *                          inner pointer will be replaced by a pointer to the
 *                          matching ofp_flow_stats struct if one is found.
 *
 * @return 1 if a match is found, 0 otherwise.
 */
int32_t openflow_flowtable_get_flow_stats(ofp_match *match, uint16_t out_port,
        uint32_t index, uint32_t *match_index, uint8_t table_index,
        ofp_flow_stats **ptr_to_flow_stats);

/**
 * Prints the OpenFlow flowtable to the console.
 */
void openflow_flowtable_print_entries();

#endif // ifndef __OPENFLOW_FLOWTABLE_H_
