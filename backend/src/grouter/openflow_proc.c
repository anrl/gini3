/**
 * openflow_proc.c - OpenFlow packet processing
 *
 * Author: Michael Kourlas
 * Date: November 27, 2015
 */

#include "grouter.h"
#include "openflow.h"
#include "openflow_config.h"
#include "packetcore.h"

/**
 * Makes a copy of the specified packet and inserts it into the specified queue.
 *
 * @param packet The packet to insert into the queue.
 * @param queue  The queue to insert the packet into.
 */
static void openflow_proc_send_packet_to_queue(gpacket_t *packet,
	simplequeue_t *queue)
{
	gpacket_t *new_packet = malloc(sizeof(gpacket_t));
	memcpy(new_packet, packet, sizeof(gpacket_t));
	writeQueue(queue, new_packet, sizeof(gpacket_t));
}

/**
 * Forwards the specified packet to the specified port.
 *
 * @param packet            The specified packet.
 * @param openflow_port_num The OpenFlow port number to send the packet to.
 * @param packet_core       The GNET packet core.
 * @param flood             Whether or not the packet is being sent as part of
 *                          a flood operation.
 */
void openflow_proc_forward_packet_to_port(gpacket_t *packet,
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

	uint32_t gnet_port_num = openflow_config_of_to_gnet_port_num(openflow_port_num);
	packet->frame.dst_interface = gnet_port_num;
	openflow_proc_send_packet_to_queue(packet, packet_core->outputQ);
}
