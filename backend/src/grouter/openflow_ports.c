#include "openflow_ports.h"

#include "message.h"
#include "simplequeue.h"
#include "packetcore.h"
#include "gnet.h"

static ofp_phy_port openflow_ports[OPENFLOW_MAX_PHYSICAL_PORTS];

/**
 * Makes a copy of the specified packet and inserts it into the specified queue.
 *
 * @param packet The packet to insert into the queue.
 * @param queue  The queue to insert the packet into.
 */
static void openflow_send_packet_to_queue(gpacket_t *packet,
    simplequeue_t *queue)
{
	gpacket_t *new_packet = malloc(sizeof(gpacket_t));
	memcpy(new_packet, packet, sizeof(gpacket_t));
	writeQueue(queue, new_packet, sizeof(gpacket_t));
}

ofp_phy_port *openflow_get_physical_port(uint16_t openflow_port_num)
{
	if (openflow_port_num >= 1 &&
		openflow_port_num <= OPENFLOW_MAX_PHYSICAL_PORTS)
	{
		return &openflow_ports[openflow_get_gnet_port_num(openflow_port_num)];
	}
	else
	{
		return NULL;
	}
}

void openflow_forward_packet_to_port(gpacket_t *packet,
	uint16_t openflow_port_num, pktcore_t *packet_core, uint8_t flood)
{
	ofp_phy_port *port = openflow_get_physical_port(openflow_port_num);
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

	uint32_t gnet_port_num = openflow_get_gnet_port_num(openflow_port_num);
	packet->frame.dst_interface = gnet_port_num;
	openflow_send_packet_to_queue(packet, packet_core->outputQ);
}

uint16_t openflow_get_openflow_port_num(uint16_t gnet_port_num)
{
	return gnet_port_num + 1;
}

uint16_t openflow_get_gnet_port_num(uint16_t openflow_port_num)
{
	return openflow_port_num - 1;
}
