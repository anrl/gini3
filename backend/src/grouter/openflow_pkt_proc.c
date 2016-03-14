/**
 * openflow_pkt_proc.c - OpenFlow packet processing
 */

#include <pthread.h>

#include "grouter.h"
#include "ip.h"
#include "message.h"
#include "openflow.h"
#include "openflow_config.h"
#include "openflow_flowtable.h"
#include "packetcore.h"
#include "protocols.h"

#include "openflow_pkt_proc.h"

/**
 * Initializes the OpenFlow packet processor.
 */
void openflow_pkt_proc_init(void) {
	openflow_flowtable_init();
}

/**
 * Processes the specified packet using the OpenFlow packet processor.
 *
 * @param packet       The packet to be handled.
 * @param packet_core  The grouter packet core.
 */
void openflow_pkt_proc_handle_packet(gpacket_t *packet,
	pktcore_t *packet_core)
{
	if (ntohs(packet->data.header.prot) == IP_PROTOCOL)
	{
		ip_packet_t *ip_packet = (ip_packet_t *) &packet->data.data;
		if (!(ntohs(ip_packet->ip_frag_off) & 0x1fff) &&
			!(ntohs(ip_packet->ip_frag_off) & 0x2000))
		{
			// Fragmented IP packet
			uint16_t flags = ntohs(openflow_config_get_switch_config_flags());
			if (flags & OFPC_FRAG_DROP) {
				// Switch configured to drop fragmented IP packets
				free(packet);
				return;
			}
		}
	}

	uint32_t i;
	verbose(2, "[openflow_pkt_proc_handle_packet]:: Received packet.");
	openflow_flowtable_entry_type *matching_entry =
		openflow_flowtable_get_entry_for_packet(packet);

	if (matching_entry != NULL)
	{
		verbose(2, "[openflow_pkt_proc_handle_packet]:: Found matching entry.");

		uint8_t action_performed = 0;
		for (i = 0; i < OPENFLOW_MAX_ACTIONS; i++)
		{
			if (matching_entry->actions[i].active)
			{
				openflow_flowtable_perform_action(&matching_entry->actions[i],
					packet, packet_core);
				action_performed = 1;
			}
		}
		if (!action_performed)
		{
			verbose(2, "[openflow_pkt_proc_handle_packet]:: No actions executed"
					   " successfully for match. Dropping packet.");
		}
	}
	else
	{
		verbose(2, "[openflow_pkt_proc_handle_packet]:: No matching entry"
				   " found. Forwarding to controller.");
		openflow_ctrl_iface_send_packet_in(packet);
	}

	free(packet);
}

/**
 * Makes a copy of the specified packet and inserts it into the specified queue.
 *
 * @param packet The packet to insert into the queue.
 * @param queue  The queue to insert the packet into.
 */
static void openflow_pkt_proc_send_packet_to_queue(gpacket_t *packet,
	simplequeue_t *queue)
{
	gpacket_t *new_packet = malloc(sizeof(gpacket_t));
	memcpy(new_packet, packet, sizeof(gpacket_t));
	writeQueue(queue, new_packet, sizeof(gpacket_t));
}

/**
 * Forwards the specified packet to the specified output port.
 *
 * @param packet            The specified packet.
 * @param openflow_port_num The OpenFlow port number to send the packet to.
 * @param packet_core       The GNET packet core.
 * @param flood             Whether or not the packet is being sent as part of
 *                          a flood operation.
 */
void openflow_pkt_proc_forward_packet_to_port(gpacket_t *packet,
	uint16_t openflow_port_num, pktcore_t *packet_core, uint8_t flood)
{
	ofp_phy_port *port = openflow_config_get_phy_port(openflow_port_num);
	if (port == NULL)
	{
		// Port does not exist
		return;
	}

	uint32_t config = ntohl(port->config);
	if ((config & OFPPC_PORT_DOWN) || (flood && (config & OFPPC_NO_FLOOD)))
	{
		// Port is administratively down or packet is a flood packet but
		// flooding is disabled for this port
		return;
	}

	uint32_t state = ntohl(port->state);
	if (state & OFPPS_LINK_DOWN)
	{
		// Port is physically down
		return;
	}

	uint32_t gnet_port_num = openflow_config_of_to_gnet_port_num(
        openflow_port_num);
	packet->frame.dst_interface = gnet_port_num;
	packet->frame.openflow = 1;
	openflow_pkt_proc_send_packet_to_queue(packet, packet_core->outputQ);
}
