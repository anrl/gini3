#include "arp.h"
#include "gnet.h"
#include "grouter.h"
#include "message.h"
#include "icmp.h"
#include "ip.h"
#include "openflow.h"
#include "protocols.h"
#include "simplequeue.h"
#include "tcp.h"
#include "udp.h"

#include "of_flowtable.h"

// OpenFlow flowtables
openflow_flowtable_type *flowtables[OPENFLOW_MAX_FLOWTABLES];

// Reference to classical work queue to support NORMAL OpenFlow port
static simplequeue_t* classical_work_queue;

/**
 * Determines whether the specified OpenFlow match matches the specified packet.
 *
 * @param match  The match to test the packet against.
 * @param packet The packet to test.
 *
 * @return 1 if the packet matches the match, 0 otherwise.
 */
static uint8_t flowtable_match_packet(openflow_flowtable_match_type *match,
									  gpacket_t *packet)
{
	int8_t ip_len;

	// Default headers
	uint16_t in_port = packet->frame.src_interface;
	uint8_t dl_src[OFP_ETH_ALEN];
	uint8_t dl_dst[OFP_ETH_ALEN];
	uint16_t dl_vlan = 0;
	uint8_t dl_vlan_pcp = 0;
	uint16_t dl_type = packet->data.header.prot;
	uint8_t nw_tos = 0;
	uint8_t nw_proto = 0;
	uint32_t nw_src = 0;
	uint32_t nw_dst = 0;
	uint16_t tp_src = 0;
	uint16_t tp_dst = 0;
	memcpy(&dl_src, packet->data.header.src, OFP_ETH_ALEN);
	memcpy(&dl_dst, packet->data.header.dst, OFP_ETH_ALEN);
	verbose(2, "[flowtable_match_packet]:: Setting default headers.");

	// All field wildcard
	if (match->wildcards == OFPFW_ALL)
	{
		verbose(2, "[flowtable_match_packet]:: Packet matched (all field"
				   " wildcard).");
		return 1;
	}

	// Set headers for IEEE 802.1Q Ethernet frame
	if (packet->data.header.prot == IEEE_8021Q_ETHERTYPE) {
		verbose(2, "[flowtable_match_packet]:: Setting headers for IEEE 802.1Q"
				   " Ethernet frame.");
		pkt_data_vlan_t *vlan_data = (pkt_data_vlan_t *) &packet->data;
		dl_vlan = vlan_data->header.tci & 0xFFF;
		dl_vlan_pcp = vlan_data->header.tci >> 13;
		dl_type = vlan_data->header.prot;
	}

	// ARP packet
	if (ntohs(packet->data.header.prot) == ARP_PROTOCOL)
	{
		verbose(2, "[flowtable_match_packet]:: Setting headers for ARP.");
		arp_packet_t *arp_packet = (arp_packet_t *) &packet->data.data;
		nw_proto = arp_packet->arp_opcode & 0xFF;
		COPY_IP(&nw_src, &arp_packet->src_ip_addr);
		COPY_IP(&nw_dst, &arp_packet->dst_ip_addr);
	}

	// IP packet
	if (ntohs(packet->data.header.prot) == IP_PROTOCOL)
	{
		verbose(2, "[flowtable_match_packet]:: Setting headers for IP.");
		ip_packet_t *ip_packet = (ip_packet_t *) &packet->data.data;
		nw_proto = ip_packet->ip_prot;
		COPY_IP(&nw_src, &ip_packet->ip_src);
		COPY_IP(&nw_dst, &ip_packet->ip_dst);
		nw_tos = ip_packet->ip_tos;

		if ((ntohs(ip_packet->ip_frag_off) & 0x1fff == 0) &&
			!(ntohs(ip_packet->ip_frag_off) & 0x2000))
		{
			// IP packet is not fragmented
			verbose(2, "[flowtable_match_packet]:: IP packet is not"
					   " fragmented.");
			if (ip_packet->ip_prot == TCP_PROTOCOL)
			{
				// TCP packet
				verbose(2, "[flowtable_match_packet]:: Setting headers for"
						   " TCP.");
				uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
				tcp_packet_type *tcp_packet = (tcp_packet_type *)
					((uint8_t *) ip_packet + ip_header_length);
				tp_src = tcp_packet->src_port;
				tp_dst = tcp_packet->dst_port;
			}
			else if (ip_packet->ip_prot == UDP_PROTOCOL)
			{
				// UDP packet
				verbose(2, "[flowtable_match_packet]:: Setting headers for"
						   " TCP.");
				uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
				udp_packet_type *udp_packet = (udp_packet_type *)
					((uint8_t *) ip_packet + ip_header_length);
				tp_src = udp_packet->src_port;
				tp_dst = udp_packet->dst_port;
			}
			else if (ip_packet->ip_prot == ICMP_PROTOCOL)
			{
				int ip_header_length = ip_packet->ip_hdr_len * 4;
				icmphdr_t *icmp_packet = (icmphdr_t *)
					((uint8_t *) ip_packet + ip_header_length);
				tp_src = icmp_packet->type;
				tp_dst = icmp_packet->code;
			}
		}
	}

	// Match switch input port
	if ((match->wildcards & OFPFW_IN_PORT != OFPFW_IN_PORT) &&
		(in_port != match->in_port))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (switch"
				   " input port).");
		return 0;
	}
	// Match source MAC address
	if ((match->wildcards & OFPFW_DL_SRC != OFPFW_DL_SRC) &&
		(dl_src != match->dl_src))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (source MAC"
				   " address).");
		return 0;
	}
	// Match destination MAC address
	if ((match->wildcards & OFPFW_DL_DST != OFPFW_DL_DST) &&
		(dl_dst != match->dl_dst))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (destination"
				   " MAC address).");
		return 0;
	}
	// Match VLAN ID
	if ((match->wildcards & OFPFW_DL_VLAN != OFPFW_DL_VLAN) &&
		(dl_vlan != match->dl_vlan))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (VLAN"
				   " ID).");
		return 0;
	}
	// Match VLAN priority
	if ((match->wildcards & OFPFW_DL_VLAN_PCP != OFPFW_DL_VLAN_PCP) &&
		(dl_vlan_pcp != match->dl_vlan_pcp))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (VLAN"
				   " priority).");
		return 0;
	}
	// Match Ethernet frame type
	if ((match->wildcards & OFPFW_DL_TYPE != OFPFW_DL_TYPE) &&
		(dl_type != match->dl_type))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (Ethernet"
					" frame type).");
		return 0;
	}
	// Match IP type of service
	if ((match->wildcards & OFPFW_NW_TOS != OFPFW_NW_TOS) &&
		(nw_tos != match->nw_tos))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (IP"
				   " type of service).");
		return 0;
	}
	// Match IP protocol or ARP opcode
	if ((match->wildcards & OFPFW_NW_PROTO != OFPFW_NW_PROTO) &&
		(nw_proto != match->nw_proto))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (IP"
				   " protocol or ARP opcode).");
		return 0;
	}
	// Match IP source address
	ip_len = (OFPFW_NW_SRC_ALL >> OFPFW_NW_SRC_SHIFT) -
		((match->wildcards & OFPFW_NW_SRC_ALL) >> OFPFW_NW_SRC_SHIFT);
	if (ip_len > 0 && memcmp(&nw_src, &match->nw_src, ip_len))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (IP"
				   " source address).");
		return 0;
	}
	// Match IP destination address
	ip_len = (OFPFW_NW_DST_ALL >> OFPFW_NW_DST_SHIFT) -
		((match->wildcards & OFPFW_NW_DST_ALL) >> OFPFW_NW_DST_SHIFT);
	if (ip_len > 0 && memcmp(&nw_dst, &match->nw_dst, ip_len))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (IP"
				   " destination address).");
		return 0;
	}
	// Match TCP/UDP source port or ICMP type
	if ((match->wildcards & OFPFW_TP_SRC != OFPFW_TP_SRC) &&
		(tp_src != match->tp_src))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (TCP/UDP"
				   " source port or ICMP type).");
		return 0;
	}
	// Match TCP/UDP destination port or ICMP code
	if ((match->wildcards & OFPFW_TP_DST != OFPFW_TP_DST) &&
		(tp_dst != match->tp_dst))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (TCP/UDP"
				   " destination port or ICMP code).");
		return 0;
	}

	verbose(2, "[flowtable_match_packet]:: Packet matched.");
	return 1;
}

/**
 * Retrieves the matching flowtable entry for the specified packet.
 *
 * @param packet The specified packet.
 *
 * @return The matching flowtable entry.
 */
static openflow_flowtable_entry_type *flowtable_get_entry_for_packet(
	gpacket_t *packet)
{
	uint32_t i, j, current_priority = 0;
	uint8_t is_match;
	openflow_flowtable_entry_type *current_entry = NULL;
	openflow_flowtable_type *flowtable;
	openflow_flowtable_entry_type *entry;
	openflow_flowtable_match_type *match;

	for (i = 0; i < OPENFLOW_MAX_FLOWTABLES; i++) {
		if (flowtables[i] != NULL && flowtables[i]->active) {
			flowtable = flowtables[i];
			for (j = 0; j < OPENFLOW_MAX_FLOWTABLE_ENTRIES; j++)
			{
				if (flowtable->entries[j].active)
				{
					entry = &flowtable->entries[j];
					match = &entry->match;
					is_match = flowtable_match_packet(match, packet);
					if (is_match)
					{
						// Exact match
						if (match->wildcards == 0)
						{
							return entry;
						}
						// Possible wildcard match, but wait to see if there
						// are any other wildcard matches with higher priority
						else if (entry->priority >= current_priority)
						{
							current_entry = entry;
							current_priority = entry->priority;
						}
					}
				}
			}
		}
	}

	return current_entry;
}

/**
 * Makes a copy of the specified packet and inserts it into the specified queue.
 *
 * @param packet The packet to insert into the queue.
 * @param output_queue The queue to insert the packet into.
 */
void send_packet_to_queue(gpacket_t *packet, simplequeue_t *queue)
{
	gpacket_t *new_packet = malloc(sizeof(gpacket_t));
	memcpy(new_packet, packet, sizeof(gpacket_t));
	writeQueue(queue, new_packet, sizeof(gpacket_t));
}

static void flowtable_perform_action(openflow_flowtable_action_type *action,
									 gpacket_t *packet,
									 simplequeue_t *output_queue)
{
	int32_t i;

	if (action->action.header.type == OFPAT_OUTPUT)
	{
		// Send packet to output port
		verbose(2, "[flowtable_perform_action]:: Action is OFPAT_OUTPUT.");
		openflow_flowtable_action_output_type *output_action =
			(openflow_flowtable_action_output_type *) &action->action;
		if (output_action->port == OFPP_IN_PORT)
		{
			// Send packet to input interface
			verbose(2, "[flowtable_perform_action]:: Port is OFPP_IN_PORT."
					   " Sending to input interface %d...",
					packet->frame.src_interface);
			packet->frame.dst_interface = packet->frame.src_interface;
			send_packet_to_queue(packet, output_queue);
		}
		else if (output_action->port == OFPP_TABLE)
		{
			// TODO: Figure out what this output port means; isn't the packet
			// already being parsed by the OpenFlow pipeline at this point?
		}
		else if (output_action->port == OFPP_NORMAL)
		{
			// Normal router handling
			verbose(2, "[flowtable_perform_action]:: Port is OFPP_NORMAL."
					   " Forwarding to classical queue...");
			send_packet_to_queue(packet, classical_work_queue);
		}
		else if (output_action->port == OFPP_FLOOD)
		{
			for (i = 0; i < MAX_INTERFACES; i++)
			{
				if (findInterface(i) != NULL) {
					packet->frame.dst_interface = i;
					send_packet_to_queue(packet, output_queue);
				}
			}
		}
		else if (output_action->port == OFPP_ALL)
		{
			for (i = 0; i < MAX_INTERFACES; i++)
			{
				if (findInterface(i) != NULL && i !=
					packet->frame.src_interface)
				{
					packet->frame.dst_interface = i;
					send_packet_to_queue(packet, output_queue);
				}
			}
		}
		else if (output_action->port == OFPP_CONTROLLER)
		{
			// TODO: Send to controller
		}
		else if (output_action->port == OFPP_LOCAL)
		{
			// TODO: Send to local controller message processing
		}
		else if (output_action->port >= 1 &&
				 output_action->port <= MAX_INTERFACES &&
				  output_action->port <= OFPP_MAX)
		{
			// Send to specified interface
			if (findInterface(output_action->port - 1) != NULL) {
				packet->frame.dst_interface = output_action->port - 1;
				send_packet_to_queue(packet, output_queue);
			}
		}
	}
	else if (action->action.header.type == OFPAT_SET_VLAN_VID)
	{
		// TODO: Add VLAN support to GNET
	}
	else if (action->action.header.type == OFPAT_SET_VLAN_PCP)
	{
		// TODO: Add VLAN support to GNET
	}
	else if (action->action.header.type == OFPAT_STRIP_VLAN)
	{
		// TODO: Add VLAN support to GNET
	}
	else if (action->action.header.type == OFPAT_SET_DL_SRC)
	{
		// Modify Ethernet source MAC address
	}
	else if (action->action.header.type == OFPAT_SET_DL_SRC)
	{
		// Modify Ethernet destination MAC address
	}
	else if (action->action.header.type == OFPAT_SET_NW_SRC)
	{
		// Modify IP source address
	}
	else if (action->action.header.type == OFPAT_SET_NW_DST)
	{
		// Modify IP destination address
	}
	else if (action->action.header.type == OFPAT_SET_NW_TOS)
	{
		// Modify IP type of service
	}
	else if (action->action.header.type == OFPAT_SET_TP_SRC)
	{
		// Modify TCP/UDP source port
	}
	else if (action->action.header.type == OFPAT_SET_TP_DST)
	{
		// Modify TCP/UDP destination port
	}
	else if (action->action.header.type == OFPAT_ENQUEUE)
	{
		// TODO: Add queueing support
	}
}

void flowtable_init(simplequeue_t *classicalWorkQ)
{
	classical_work_queue = classicalWorkQ;

	// Default flowtable entry (send all packets to normal router processing)
	flowtables[0] = malloc(sizeof(openflow_flowtable_type));
	flowtables[0]->entries[0].active = 1;
	flowtables[0]->entries[0].match.wildcards = OFPFW_ALL;
	flowtables[0]->entries[0].priority = 1;
	flowtables[0]->entries[0].actions[0].active = 1;
	openflow_flowtable_action_output_type output_action;
	output_action.type = OFPAT_OUTPUT;
	output_action.len = 8;
	output_action.port = OFPP_NORMAL;
	memcpy(&flowtables[0]->entries[0].actions[0].action, &output_action,
		   sizeof(openflow_flowtable_action_output_type));
}

void flowtable_handle_packet(gpacket_t *packet, simplequeue_t *output_queue)
{
	int i;
	verbose(2, "[flowtable_handle_packet]:: Received packet.");
	openflow_flowtable_entry_type *matching_entry =
		flowtable_get_entry_for_packet(packet);

	if (matching_entry != NULL)
	{
		verbose(2, "[flowtable_handle_packet]:: Found matching entry.");
		uint8_t action_performed = 0;
		for (i = 0; i < OPENFLOW_MAX_ACTIONS; i++)
		{
			if (matching_entry->actions[i].active)
			{
				flowtable_perform_action(&matching_entry->actions[i], packet,
										 output_queue);
				action_performed = 1;
			}
		}
		if (!action_performed)
		{
			verbose(2, "[flowtable_handle_packet]:: No actions executed"
					   " successfully for match. Dropping packet.");
		}
	}
	else
	{
		verbose(2, "[flowtable_handle_packet]:: No matching entry found.");
		// TODO: Forward to controller when no match is found
	}

	free(packet);
}
