/**
 * openflow_flowtable.c - OpenFlow flowtable
 */

#include <inttypes.h>
#include <time.h>

#include "arp.h"
#include "gnet.h"
#include "grouter.h"
#include "message.h"
#include "icmp.h"
#include "ip.h"
#include "openflow.h"
#include "openflow_config.h"
#include "openflow_ctrl_iface.h"
#include "openflow_pkt_proc.h"
#include "protocols.h"
#include "simplequeue.h"
#include "tcp.h"
#include "udp.h"

#include "openflow_flowtable.h"

// OpenFlow flowtable
static openflow_flowtable_type *flowtable;
static pthread_mutex_t flowtable_mutex;

// Router configuration
extern router_config rconfig;

/**
 * Creates a new packet identical to the specified packet but with a VLAN
 * header.
 *
 * @param packet The packet to add a VLAN header to.
 *
 * @return The packet with the VLAN header.
 */
static gpacket_t openflow_flowtable_add_vlan_header_to_packet(gpacket_t *packet)
{
	gpacket_t new_packet;
	new_packet.frame = packet->frame;
	pkt_data_vlan_t vlan_data;
	COPY_MAC(&vlan_data.header.src, &packet->data.header.src);
	COPY_MAC(&vlan_data.header.dst, &packet->data.header.dst);
	vlan_data.header.tpid = htons(ETHERTYPE_IEEE_802_1Q);
	vlan_data.header.tci = 0;
	vlan_data.header.prot = packet->data.header.prot;
	memcpy(&vlan_data.data, &packet->data.data, DEFAULT_MTU);
	memcpy(&new_packet.data, &vlan_data, sizeof(vlan_data));
	return new_packet;
}

/**
 * Creates a new packet identical to the specified packet but without a VLAN
 * header.
 *
 * @param packet The packet to remove the VLAN header from.
 *
 * @return The packet without the VLAN header.
 */
static gpacket_t openflow_flowtable_remove_vlan_header_from_packet(
		gpacket_t *packet)
{
	gpacket_t new_packet;
	new_packet.frame = packet->frame;
	pkt_data_vlan_t *vlan_data = (pkt_data_vlan_t *) &packet->data;
	COPY_MAC(&new_packet.data.header.src, &vlan_data->header.src);
	COPY_MAC(&new_packet.data.header.dst, &vlan_data->header.dst);
	new_packet.data.header.prot = vlan_data->header.prot;
	memcpy(&new_packet.data.data, &vlan_data->data, DEFAULT_MTU);
	return new_packet;
}

/**
 * Updates the IP (and, if applicable, the TCP or UDP) checksums in a packet.
 *
 * @param packet The packet with the checksums to be updated.
 */
static void openflow_flowtable_update_checksums(ip_packet_t *ip_packet) {
	// IP packet
	ip_packet->ip_cksum = 0;
	ip_packet->ip_cksum = htons(checksum((void *)ip_packet,
		ip_packet->ip_hdr_len * 2));

	if (ip_packet->ip_prot == TCP_PROTOCOL)
	{
		// TCP packet
		uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
		tcp_packet_type *tcp_packet = (tcp_packet_type *)
			((uint8_t *) ip_packet + ip_header_length);
		tcp_packet->checksum = tcp_checksum(ip_packet);
	}
	else if (ip_packet->ip_prot == UDP_PROTOCOL)
	{
		// UDP packet
		uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
		udp_packet_type *udp_packet = (udp_packet_type *)
			((uint8_t *) ip_packet + ip_header_length);
		udp_packet->checksum = udp_checksum(ip_packet);
	}
}

/**
 * Compares two IP addresses.
 *
 * @param ip_1   The first IP address to compare.
 * @param ip_2   The second IP address to compare.
 * @param ip_len The number of bits in the IP address to compare.
 *
 * @return 1 if the IP addresses are the same, 0 otherwise.
 */
static uint8_t openflow_flowtable_ip_compare(uint32_t ip_1, uint32_t ip_2,
	uint8_t ip_len)
{
	return (ip_1 >> ((OFPFW_NW_DST_ALL >> OFPFW_NW_DST_SHIFT) - ip_len)) ==
			(ip_2 >> ((OFPFW_NW_DST_ALL >> OFPFW_NW_DST_SHIFT) - ip_len))
			? 1 : 0;
}

/**
 * Determines whether the specified OpenFlow match matches the specified packet.
 *
 * @param match  The match to test the packet against.
 * @param packet The packet to test.
 *
 * @return 1 if the packet matches the match, 0 otherwise.
 */
static uint8_t openflow_flowtable_match_packet(ofp_match *match,
	gpacket_t *packet)
{
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

	// Accept match if all fields wildcard is present in match
	if (ntohl(match->wildcards) == OFPFW_ALL)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Packet matched (all"
			" field wildcard).");
		return 1;
	}

	// Set headers for IEEE 802.3 Ethernet frame
	if (ntohs(packet->data.header.prot) < OFP_DL_TYPE_ETH2_CUTOFF)
	{
		if (packet->data.data[0] == IEEE_802_2_DSAP_SNAP)
		{
			// SNAP
			if (packet->data.data[2] & IEEE_802_2_CTRL_8_BITS) {
				// 8-bit control field
				uint32_t oui;
				memcpy(&oui, &packet->data.data[3], sizeof(uint8_t) * 3);
				if (ntohl(oui) == 0)
				{
					memcpy(&dl_type, &packet->data.data[6],
						sizeof(uint8_t) * 2);
				}
				else
				{
					dl_type = htons(OFP_DL_TYPE_NOT_ETH_TYPE);
				}

			}
			else
			{
				// 16-bit control field
				uint32_t oui;
				memcpy(&oui, &packet->data.data[4], sizeof(uint8_t) * 3);
				if (ntohl(oui) == 0)
				{
					memcpy(&dl_type, &packet->data.data[7],
						sizeof(uint8_t) * 2);
				}
				else
				{
					dl_type = htons(OFP_DL_TYPE_NOT_ETH_TYPE);
				}
			}
		}
		else
		{
			// No SNAP
			dl_type = htons(OFP_DL_TYPE_NOT_ETH_TYPE);
		}
	}

	// Set headers for IEEE 802.1Q Ethernet frame
	if (ntohs(packet->data.header.prot) == ETHERTYPE_IEEE_802_1Q)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Setting headers for"
			" IEEE 802.1Q Ethernet frame.");
		pkt_data_vlan_t *vlan_data = (pkt_data_vlan_t *) &packet->data;
		dl_vlan = htons(ntohs(vlan_data->header.tci) & 0xFFF);
		dl_vlan_pcp = htons(ntohs(vlan_data->header.tci) >> 13);
		dl_type = vlan_data->header.prot;
	}
	else
	{
		dl_vlan = ntohs(OFP_VLAN_NONE);
	}

	// Set headers for ARP packet
	if (ntohs(packet->data.header.prot) == ARP_PROTOCOL)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Setting headers for"
			" ARP.");
		arp_packet_t *arp_packet = (arp_packet_t *) &packet->data.data;
		nw_proto = htons(ntohs(arp_packet->arp_opcode) & 0xFF);
		COPY_IP(&nw_src, &arp_packet->src_ip_addr);
		COPY_IP(&nw_dst, &arp_packet->dst_ip_addr);
	}

	// Set headers for IP packet
	if (ntohs(packet->data.header.prot) == IP_PROTOCOL)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Setting headers for"
			" IP.");
		ip_packet_t *ip_packet = (ip_packet_t *) &packet->data.data;
		nw_proto = ip_packet->ip_prot;
		COPY_IP(&nw_src, &ip_packet->ip_src);
		COPY_IP(&nw_dst, &ip_packet->ip_dst);
		nw_tos = ip_packet->ip_tos;

		if (!(ntohs(ip_packet->ip_frag_off) & 0x1fff) &&
			!(ntohs(ip_packet->ip_frag_off) & 0x2000))
		{
			// IP packet is not fragmented
			verbose(2, "[openflow_flowtable_match_packet]:: IP packet is not"
				" fragmented.");
			if (ip_packet->ip_prot == TCP_PROTOCOL)
			{
				// TCP packet
				verbose(2, "[openflow_flowtable_match_packet]:: Setting"
					" headers for TCP.");
				uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
				tcp_packet_type *tcp_packet = (tcp_packet_type *)
					((uint8_t *) ip_packet + ip_header_length);
				tp_src = tcp_packet->src_port;
				tp_dst = tcp_packet->dst_port;
			}
			else if (ip_packet->ip_prot == UDP_PROTOCOL)
			{
				// UDP packet
				verbose(2, "[openflow_flowtable_match_packet]:: Setting"
					" headers for UDP.");
				uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
				udp_packet_type *udp_packet = (udp_packet_type *)
					((uint8_t *) ip_packet + ip_header_length);
				tp_src = udp_packet->src_port;
				tp_dst = udp_packet->dst_port;
			}
			else if (ip_packet->ip_prot == ICMP_PROTOCOL)
			{
				// ICMP packet
				verbose(2, "[openflow_flowtable_match_packet]:: Setting"
					" headers for ICMP.");
				int ip_header_length = ip_packet->ip_hdr_len * 4;
				icmphdr_t *icmp_packet = (icmphdr_t *)
					((uint8_t *) ip_packet + ip_header_length);
				tp_src = icmp_packet->type;
				tp_dst = icmp_packet->code;
			}
		}
	}

	// Reject match on input port
	if (!(ntohl(match->wildcards) & OFPFW_IN_PORT) && in_port != match->in_port)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Packet not matched"
			" (switch input port).");
		return 0;
	}

	// Reject match on Ethernet source MAC address
	if (!(ntohl(match->wildcards) & OFPFW_DL_SRC) && dl_src != match->dl_src)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Packet not matched"
			" (source MAC address).");
		return 0;
	}

	// Reject match on Ethernet destination MAC address
	if (!(ntohl(match->wildcards) & OFPFW_DL_DST) && dl_dst != match->dl_dst)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Packet not matched"
			" (destination MAC address).");
		return 0;
	}

	// Reject match on Ethernet VLAN ID
	if (!(ntohl(match->wildcards) & OFPFW_DL_VLAN) && dl_vlan != match->dl_vlan)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Packet not matched"
			" (VLAN ID).");
		return 0;
	}

	// Reject match on Ethernet VLAN priority
	if (!(ntohl(match->wildcards) & OFPFW_DL_VLAN) &&
			!(ntohl(match->wildcards) & OFPFW_DL_VLAN_PCP) &&
			dl_vlan_pcp != match->dl_vlan_pcp)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Packet not matched"
			" (VLAN priority).");
		return 0;
	}

	// Reject match on Ethernet frame type
	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE) && dl_type != match->dl_type)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Packet not matched"
			" (Ethernet frame type).");
		return 0;
	}

	// Reject match on IP type of service
	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE) &&
			ntohs(match->dl_type) == IP_PROTOCOL &&
			!(ntohl(match->wildcards) & OFPFW_NW_TOS) &&
			nw_tos != match->nw_tos)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Packet not matched"
			" (IP type of service).");
		return 0;
	}

	// Reject match on IP protocol or ARP opcode
	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE) &&
			(ntohs(match->dl_type) == IP_PROTOCOL ||
					ntohs(match->dl_type) == ARP_PROTOCOL) &&
					!(ntohl(match->wildcards) & OFPFW_NW_PROTO) &&
					nw_proto != match->nw_proto)
	{
		verbose(2, "[openflow_flowtable_match_packet]:: Packet not matched"
			" (IP protocol or ARP opcode).");
		return 0;
	}

	// Reject match on IP source address
	uint8_t ip_src_len = (OFPFW_NW_SRC_ALL >> OFPFW_NW_SRC_SHIFT) -
		((ntohl(match->wildcards) & OFPFW_NW_SRC_MASK) >> OFPFW_NW_SRC_SHIFT);
	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE) &&
				(ntohs(match->dl_type) == IP_PROTOCOL ||
						ntohs(match->dl_type) == ARP_PROTOCOL))
	{
		if (ip_src_len > 0 && !openflow_flowtable_ip_compare(ntohl(nw_src),
				ntohl(match->nw_src), ip_src_len))
			{
				verbose(2, "[openflow_flowtable_match_packet]:: Packet not"
						" matched (IP source address).");
				return 0;
			}
	}

	// Reject match on IP destination address
	uint8_t ip_dst_len = (OFPFW_NW_DST_ALL >> OFPFW_NW_DST_SHIFT) -
		((ntohl(match->wildcards) & OFPFW_NW_DST_MASK) >> OFPFW_NW_DST_SHIFT);
	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE) &&
				(ntohs(match->dl_type) == IP_PROTOCOL ||
						ntohs(match->dl_type) == ARP_PROTOCOL))
	{
		if (ip_dst_len > 0 && !openflow_flowtable_ip_compare(ntohl(nw_dst),
				ntohl(match->nw_dst), ip_dst_len))
			{
				verbose(2, "[openflow_flowtable_match_packet]:: Packet not"
						" matched (IP destination address).");
				return 0;
			}
	}

	// Reject match on TCP/UDP source port or ICMP type
	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE) &&
			ntohs(match->dl_type) == IP_PROTOCOL)
	{
		if (!(ntohl(match->wildcards) & OFPFW_NW_PROTO) &&
				(match->nw_proto == ICMP_PROTOCOL ||
						match->nw_proto == TCP_PROTOCOL ||
						match->nw_proto == UDP_PROTOCOL))
		{
			if (!(ntohl(match->wildcards) & OFPFW_TP_SRC) &&
					tp_src != match->tp_src)
			{
				verbose(2, "[openflow_flowtable_match_packet]:: Packet not"
						" matched (TCP/UDP source port or ICMP type).");
				return 0;
			}
		}
	}

	// Reject match on TCP/UDP destination port or ICMP code
	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE) &&
			ntohs(match->dl_type) == IP_PROTOCOL)
	{
		if (!(ntohl(match->wildcards) & OFPFW_NW_PROTO) &&
				(match->nw_proto == ICMP_PROTOCOL ||
						match->nw_proto == TCP_PROTOCOL ||
						match->nw_proto == UDP_PROTOCOL))
		{
			if (!(ntohl(match->wildcards) & OFPFW_TP_DST) &&
					tp_dst != match->tp_dst)
			{
				verbose(2, "[openflow_flowtable_match_packet]:: Packet not"
						" matched (TCP/UDP destination port or ICMP code).");
				return 0;
			}
		}
	}

	verbose(2, "[openflow_flowtable_match_packet]:: Packet matched.");
	return 1;
}

/**
 * Retrieves the matching flowtable entry for the specified packet.
 *
 * @param packet    The specified packet.
 * @param emergency Whether the controller is in emergency mode.
 *
 * @return The matching flowtable entry.
 */
openflow_flowtable_entry_type *openflow_flowtable_get_entry_for_packet(
	gpacket_t *packet)
{
	pthread_mutex_lock(&flowtable_mutex);

	uint32_t current_priority = 0;
	openflow_flowtable_entry_type *current_entry = NULL;
	uint32_t i;
	for (i = 0; i < OPENFLOW_MAX_FLOWTABLE_ENTRIES; i++)
	{
		if (flowtable->entries[i].active)
		{
			openflow_flowtable_entry_type *entry = &flowtable->entries[i];
			ofp_match *match = &entry->match;
			uint8_t is_match = openflow_flowtable_match_packet(match, packet);
			if (is_match)
			{
				uint8_t emergency = !openflow_ctrl_iface_get_conn_state();
				if ((emergency && (ntohs(entry->flags) & OFPFF_EMERG)) ||
					(!emergency && !(ntohs(entry->flags) & OFPFF_EMERG)))
				{
					// Match consistent with emergency mode state
					if (match->wildcards == 0)
					{
						// Exact match
						verbose(2, "[openflow_flowtable_get_entry_for_packet]::"
							" Found exact match at index %" PRIu32 ".", i);
						pthread_mutex_unlock(&flowtable_mutex);
						return entry;
					}
					else if (entry->priority >= current_priority)
					{
						// Possible wildcard match, but wait to see if there
						// are any other wildcard matches with higher priority
						verbose(2, "[openflow_flowtable_get_entry_for_packet]::"
							" Found possible match at index %" PRIu32 ".", i);
						current_entry = entry;
						current_priority = entry->priority;
					}
				}
				else
				{
					if (emergency)
					{
						verbose(2, "[openflow_flowtable_get_entry_for_packet]::"
							" Found matching non-emergency entry at index"
							" %" PRIu32 ", but switch is in emergency"
							" mode.", i);
					}
					else
					{
						verbose(2, "[openflow_flowtable_get_entry_for_packet]::"
							" Found matching emergency entry at index"
							" %" PRIu32 ", but switch is not in emergency"
							" mode.", i);
					}
				}
			}
		}
	}

	if (current_entry == NULL)
	{
		verbose(2, "[openflow_flowtable_get_entry_for_packet]::"
			" No entry found.");
	}

	pthread_mutex_unlock(&flowtable_mutex);
	return current_entry;
}

/**
 * Performs the specified action on the specified packet.
 *
 * @param action       The specified action.
 * @param packet       The specified packet.
 * @param packet_core  The grouter packet core.
 */
void openflow_flowtable_perform_action(
	openflow_flowtable_action_type *action, gpacket_t *packet,
	pktcore_t *packet_core)
{
	pthread_mutex_lock(&flowtable_mutex);

	int32_t i;
	uint16_t header_type = ntohs(action->action.header.type);
	if (header_type == OFPAT_OUTPUT)
	{
		// Send packet to output port
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
			" OFPAT_OUTPUT.");
		ofp_action_output *output_action =
			(ofp_action_output *) &action->action;
		uint16_t port = ntohs(output_action->port);
		if (port == OFPP_IN_PORT)
		{
			// Send packet to input interface
			uint16_t openflow_port_num =
				openflow_config_gnet_to_of_port_num(
					packet->frame.src_interface);
			verbose(2, "[openflow_flowtable_perform_action]:: Port is"
				" OFPP_IN_PORT. Sending to physical port number %" PRIu16 ".",
				openflow_port_num);
			openflow_pkt_proc_forward_packet_to_port(packet, openflow_port_num,
				packet_core, 0);
		}
		else if (port == OFPP_TABLE)
		{
			// OpenFlow pipeline handling
			verbose(2, "[openflow_flowtable_perform_action]:: Port is"
				" OFPP_TABLE. Forwarding attached packet to OpenFlow"
				" packet processor.");
			openflow_pkt_proc_handle_packet(packet, packet_core);
		}
		else if (port == OFPP_NORMAL)
		{
			// Normal router handling
			verbose(2, "[openflow_flowtable_perform_action]:: Port is"
				" OFPP_NORMAL. Forwarding to normal packet processor.");
			gpacket_t *new_packet = malloc(sizeof(gpacket_t));
			memcpy(new_packet, packet, sizeof(gpacket_t));
			enqueuePacket(packet_core, new_packet, sizeof(gpacket_t), 0);
		}
		else if (port == OFPP_FLOOD)
		{
			// Forward packet to all ports with flooding enabled except source
			// port
			verbose(2, "[openflow_flowtable_perform_action]:: Port is"
				" OFPP_FLOOD. Sending to all physical ports with flooding"
				" enabled except input port.");
			for (i = 1; i <= OPENFLOW_MAX_PHYSICAL_PORTS; i++)
			{
				uint16_t gnet_port_num = openflow_config_of_to_gnet_port_num(i);
				if (gnet_port_num != packet->frame.src_interface)
				{
					openflow_pkt_proc_forward_packet_to_port(packet, i,
						packet_core, 1);
				}
			}
		}
		else if (port == OFPP_ALL)
		{
			// Forward packet to all ports except source port
			verbose(2, "[openflow_flowtable_perform_action]:: Port is"
				" OFPP_ALL. Sending to all physical ports except input port.");
			for (i = 1; i <= OPENFLOW_MAX_PHYSICAL_PORTS; i++)
			{
				uint16_t gnet_port_num = openflow_config_of_to_gnet_port_num(i);
				if (gnet_port_num != packet->frame.src_interface)
				{
					openflow_pkt_proc_forward_packet_to_port(packet, i,
						packet_core, 0);
				}
			}
		}
		else if (port == OFPP_CONTROLLER)
		{
			// Forward packet to controller
			verbose(2, "[openflow_flowtable_perform_action]:: Port is"
				" OFPP_CONTROLLER. Sending to controller.");
			openflow_ctrl_iface_send_packet_in(packet);
		}
		else if (port == OFPP_LOCAL)
		{
			// Forward packet to controller packet processing
			verbose(2, "[openflow_flowtable_perform_action]:: Port is"
				" OFPP_LOCAL. Sending to controller processing.");
			openflow_ctrl_iface_parse_packet(packet);
		}
		else
		{
			// Forward packet to specified port
			verbose(2, "[openflow_flowtable_perform_action]:: Port is"
				" %" PRIu16 ". Sending to that physical port number.", port);
			openflow_pkt_proc_forward_packet_to_port(packet, port,
					packet_core, 0);
		}
	}
	else if (header_type == OFPAT_SET_VLAN_VID)
	{
		// Modify VLAN ID
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
				   " OFPAT_SET_VLAN_VID.");
		ofp_action_vlan_vid *vlan_vid_action =
			(ofp_action_vlan_vid *) &action->action;
		if (ntohs(packet->data.header.prot) == ETHERTYPE_IEEE_802_1Q)
		{
			// Existing VLAN header
			pkt_data_vlan_t *vlan_data = (pkt_data_vlan_t *) &packet->data;
			vlan_data->header.tci = vlan_vid_action->vlan_vid;
		}
		else
		{
			// No VLAN header
			gpacket_t new_packet =
				openflow_flowtable_add_vlan_header_to_packet(packet);
			memcpy(packet, &new_packet, sizeof(gpacket_t));
			pkt_data_vlan_t *vlan_data = (pkt_data_vlan_t *) &packet->data;
			vlan_data->header.tci = vlan_vid_action->vlan_vid;
		}
	}
	else if (header_type == OFPAT_SET_VLAN_PCP)
	{
		// Modify VLAN priority
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
				   " OFPAT_SET_VLAN_PCP.");
		ofp_action_vlan_pcp *vlan_pcp_action =
			(ofp_action_vlan_pcp *) &action->action;
		if (ntohs(packet->data.header.prot) == ETHERTYPE_IEEE_802_1Q)
		{
			// Existing VLAN header
			pkt_data_vlan_t *vlan_data = (pkt_data_vlan_t *) &packet->data;
			vlan_data->header.tci = htons(ntohs(
				vlan_data->header.tci) & 0x1fff);
			vlan_data->header.tci = htons((ntohs(
				vlan_pcp_action->vlan_pcp) << 13) |
				ntohs(vlan_data->header.prot));
		}
		else
		{
			// No VLAN header
			gpacket_t new_packet =
				openflow_flowtable_add_vlan_header_to_packet(packet);
			memcpy(packet, &new_packet, sizeof(gpacket_t));
			pkt_data_vlan_t *vlan_data = (pkt_data_vlan_t *) &packet->data;
			vlan_data->header.tci = htons(ntohs(
				vlan_pcp_action->vlan_pcp) << 13);
		}
	}
	else if (header_type == OFPAT_STRIP_VLAN)
	{
		// Remove VLAN header
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
				   " OFPAT_STRIP_VLAN.");
		if (ntohs(packet->data.header.prot) == ETHERTYPE_IEEE_802_1Q)
		{
			gpacket_t new_packet =
				openflow_flowtable_remove_vlan_header_from_packet(packet);
			memcpy(packet, &new_packet, sizeof(gpacket_t));
		}
	}
	else if (header_type == OFPAT_SET_DL_SRC)
	{
		// Modify Ethernet source MAC address
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
				   " OFPAT_SET_DL_SRC.");
		ofp_action_dl_addr *dl_addr_action =
			(ofp_action_dl_addr *) &action->action;
		COPY_MAC(&packet->data.header.dst, &dl_addr_action->dl_addr);
	}
	else if (header_type == OFPAT_SET_DL_DST)
	{
		// Modify Ethernet destination MAC address
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
				   " OFPAT_SET_DL_DST.");
		ofp_action_dl_addr *dl_addr_action =
			(ofp_action_dl_addr *) &action->action;
		COPY_MAC(&packet->data.header.dst, &dl_addr_action->dl_addr);
	}
	else if (header_type == OFPAT_SET_NW_SRC)
	{
		// Modify IP source address
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
				   " OFPAT_SET_NW_SRC.");
		ofp_action_nw_addr *nw_addr_action =
			(ofp_action_nw_addr *) &action->action;
		if (ntohs(packet->data.header.prot) == IP_PROTOCOL)
		{
			ip_packet_t *ip_packet = (ip_packet_t *) &packet->data.data;
			if (!(ntohs(ip_packet->ip_frag_off) & 0x1fff) &&
				!(ntohs(ip_packet->ip_frag_off) & 0x2000))
			{
				// IP packet is not fragmented
				COPY_IP(&ip_packet->ip_src, &nw_addr_action->nw_addr);
				openflow_flowtable_update_checksums(ip_packet);
			}
		}
	}
	else if (header_type == OFPAT_SET_NW_DST)
	{
		// Modify IP destination address
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
				   " OFPAT_SET_NW_DST.");
		ofp_action_nw_addr *nw_addr_action =
			(ofp_action_nw_addr *) &action->action;
		if (ntohs(packet->data.header.prot) == IP_PROTOCOL)
		{
			ip_packet_t *ip_packet = (ip_packet_t *) &packet->data.data;
			if (!(ntohs(ip_packet->ip_frag_off) & 0x1fff) &&
				!(ntohs(ip_packet->ip_frag_off) & 0x2000))
			{
				// IP packet is not fragmented
				COPY_IP(&ip_packet->ip_dst, &nw_addr_action->nw_addr);
				openflow_flowtable_update_checksums(ip_packet);
			}
		}
	}
	else if (header_type == OFPAT_SET_NW_TOS)
	{
		// Modify IP type of service
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
				   " OFPAT_SET_NW_TOS.");
		ofp_action_nw_tos *nw_tos_action =
			(ofp_action_nw_tos *) &action->action;
		if (ntohs(packet->data.header.prot) == IP_PROTOCOL)
		{
			ip_packet_t *ip_packet = (ip_packet_t *) &packet->data.data;
			if (!(ntohs(ip_packet->ip_frag_off) & 0x1fff) &&
				!(ntohs(ip_packet->ip_frag_off) & 0x2000))
			{
				// IP packet is not fragmented
				ip_packet->ip_tos = nw_tos_action->nw_tos;
				openflow_flowtable_update_checksums(ip_packet);
			}
		}
	}
	else if (header_type == OFPAT_SET_TP_SRC)
	{
		// Modify TCP/UDP source port
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
				   " OFPAT_SET_TP_SRC.");
		ofp_action_tp_port *tp_port_action =
			(ofp_action_tp_port *) &action->action;
		if (ntohs(packet->data.header.prot) == IP_PROTOCOL)
		{
			ip_packet_t *ip_packet = (ip_packet_t *) &packet->data.data;
			if (!(ntohs(ip_packet->ip_frag_off) & 0x1fff) &&
				!(ntohs(ip_packet->ip_frag_off) & 0x2000))
			{
				// IP packet is not fragmented
				if (ip_packet->ip_prot == TCP_PROTOCOL)
				{
					uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
					tcp_packet_type *tcp_packet = (tcp_packet_type *)
						((uint8_t *) ip_packet + ip_header_length);
					tcp_packet->src_port = tp_port_action->tp_port;
					openflow_flowtable_update_checksums(ip_packet);
				}
				else if (ip_packet->ip_prot == UDP_PROTOCOL)
				{
					uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
					udp_packet_type *udp_packet = (udp_packet_type *)
					((uint8_t *) ip_packet + ip_header_length);
					udp_packet->src_port = tp_port_action->tp_port;
					openflow_flowtable_update_checksums(ip_packet);
				}
			}

		}
	}
	else if (header_type == OFPAT_SET_TP_DST)
	{
		// Modify TCP/UDP destination port
		verbose(2, "[openflow_flowtable_perform_action]:: Action is"
				   " OFPAT_SET_TP_DST.");
		ofp_action_tp_port *tp_port_action =
			(ofp_action_tp_port *) &action->action;
		if (ntohs(packet->data.header.prot) == IP_PROTOCOL)
		{
			ip_packet_t *ip_packet = (ip_packet_t *) &packet->data.data;
			if (!(ntohs(ip_packet->ip_frag_off) & 0x1fff) &&
				!(ntohs(ip_packet->ip_frag_off) & 0x2000))
			{
				// IP packet is not fragmented
				if (ip_packet->ip_prot == TCP_PROTOCOL)
				{
					uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
					tcp_packet_type *tcp_packet = (tcp_packet_type *)
						((uint8_t *) ip_packet + ip_header_length);
					tcp_packet->dst_port = tp_port_action->tp_port;
					openflow_flowtable_update_checksums(ip_packet);
				}
				else if (ip_packet->ip_prot == UDP_PROTOCOL)
				{
					uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
					udp_packet_type *udp_packet = (udp_packet_type *)
					((uint8_t *) ip_packet + ip_header_length);
					udp_packet->dst_port = tp_port_action->tp_port;
					openflow_flowtable_update_checksums(ip_packet);
				}
			}
		}
	}
	else
	{
		verbose(2, "[openflow_flowtable_perform_action]:: Unrecognized"
			" action %" PRIu16 ".", header_type);
	}

	pthread_mutex_unlock(&flowtable_mutex);
}

/**
 * Set flowtable defaults.
 */
static void openflow_flowtable_set_defaults(void) {
	// Default flowtable entry (send all packets to normal router processing)
	flowtable->entries[0].active = 1;
	flowtable->entries[0].match.wildcards = htonl(OFPFW_ALL);
	flowtable->entries[0].priority = htonl(1);
	flowtable->entries[0].flags = htons(OFPFF_EMERG);
	flowtable->entries[0].actions[0].active = 1;
	ofp_action_output output_action;
	output_action.type = htons(OFPAT_OUTPUT);
	output_action.len = htons(8);
	output_action.port = htons(OFPP_NORMAL);
	memcpy(&flowtable->entries[0].actions[0].action, &output_action,
		sizeof(ofp_action_output));
}

/**
 * Initializes the flowtable.
 */
void openflow_flowtable_init(void)
{
	pthread_mutex_lock(&flowtable_mutex);

	flowtable = malloc(sizeof(openflow_flowtable_type));
	memset(flowtable, 0, sizeof(openflow_flowtable_type));
	openflow_flowtable_set_defaults();

	pthread_mutex_unlock(&flowtable_mutex);
}

/**
 * Determines whether there is an entry in the flowtable that overlaps the
 * specified entry. An entry overlaps another entry if a single packet may
 * match both, and both entries have the same priority.
 *
 * @param flow_mod A pointer to an ofp_flow_mod struct containing the specified
 *                 entry.
 * @param index    A pointer to a variable used to store the index of the
 *                 overlapping entry, if any.
 *
 * @return 1 if a match is found, 0 otherwise.
 */
static uint8_t openflow_flowtable_find_overlapping_entry(ofp_flow_mod *flow_mod,
	uint32_t *index)
{
	uint32_t i;
	for (i = 0; i < OPENFLOW_MAX_FLOWTABLE_ENTRIES; i++)
	{
		openflow_flowtable_entry_type *entry = &flowtable->entries[i];

		// Reject overlap if priorities are not the same
		if (entry->priority != flow_mod->priority)
		{
			continue;
		}

		ofp_match *flow_mod_match = &flow_mod->match;
		ofp_match *entry_match = &entry->match;

		// Accept overlap if either entry uses the all fields wildcard
		if (ntohl(flow_mod_match->wildcards) == OFPFW_ALL ||
				ntohl(entry_match->wildcards) == OFPFW_ALL)
		{
			*index = i;
			return 1;
		}

		// In general, reject overlap if both entries do not use a wildcard
		// and have differing values for a particular field

		// Reject overlap on input port
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_IN_PORT) &&
				!(ntohl(entry_match->wildcards) & OFPFW_IN_PORT))
		{
			if (flow_mod_match->in_port != entry_match->in_port)
			{
				continue;
			}
		}

		// Reject overlap on Ethernet source MAC address
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_SRC) &&
				!(ntohl(entry_match->wildcards) & OFPFW_DL_SRC))
		{
			if (flow_mod_match->dl_src != entry_match->dl_src)
			{
				continue;
			}
		}

		// Reject overlap on Ethernet destination MAC address
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_DST) &&
				!(ntohl(entry_match->wildcards) & OFPFW_DL_DST))
		{
			if (flow_mod_match->dl_dst != entry_match->dl_dst)
			{
				continue;
			}
		}

		// Reject overlap on Ethernet VLAN ID
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_VLAN) &&
				!(ntohl(entry_match->wildcards) & OFPFW_DL_VLAN))
		{
			if (flow_mod_match->dl_vlan != entry_match->dl_vlan)
			{
				continue;
			}
		}

		// Reject overlap on Ethernet VLAN priority
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_VLAN) &&
				!(ntohl(entry_match->wildcards) & OFPFW_DL_VLAN))
		{
			if (ntohs(flow_mod_match->dl_vlan) != OFP_VLAN_NONE &&
					ntohs(entry_match->dl_vlan) != OFP_VLAN_NONE)
			{
				// In addition to general rules, reject overlap only if
				// both entries do not use a wildcard or the value
				// OFP_VLAN_NONE for VLAN IDs
				if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_VLAN_PCP) &&
						!(ntohl(entry_match->wildcards) & OFPFW_DL_VLAN_PCP))
				{
					if (flow_mod_match->dl_vlan_pcp != entry_match->dl_vlan_pcp)
					{
						continue;
					}
				}
			}
		}

		// Reject overlap on Ethernet frame type
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_TYPE) &&
				!(ntohl(entry_match->wildcards) & OFPFW_DL_TYPE))
		{
			if (flow_mod_match->dl_type != entry_match->dl_type)
			{
				continue;
			}
		}

		// Reject overlap on IP type of service
		if (ntohs(flow_mod_match->dl_type) == IP_PROTOCOL &&
				flow_mod_match->dl_type == entry_match->dl_type)
		{
			// In addition to general rules, reject overlap only if
			// both entries match the IP protocol
			if (!(ntohl(flow_mod_match->wildcards) & OFPFW_NW_TOS) &&
					!(ntohl(entry_match->wildcards) & OFPFW_NW_TOS))
			{
				if (flow_mod_match->nw_tos != entry_match->nw_tos)
				{
					continue;
				}
			}
		}

		// Reject overlap on IP protocol or ARP opcode
		if ((ntohs(flow_mod_match->dl_type) == IP_PROTOCOL ||
				ntohs(flow_mod_match->dl_type) == ARP_PROTOCOL) &&
				flow_mod_match->dl_type == entry_match->dl_type)
		{
			// In addition to general rules, reject overlap only if
			// both entries match the IP or ARP protocol
			if (!(ntohl(flow_mod_match->wildcards) & OFPFW_NW_TOS) &&
					!(ntohl(entry_match->wildcards) & OFPFW_NW_TOS))
			{
				if (flow_mod_match->nw_tos != entry_match->nw_tos)
				{
					continue;
				}
			}
		}

		// Match on IP source address
		if ((ntohs(flow_mod_match->dl_type) == IP_PROTOCOL ||
				ntohs(flow_mod_match->dl_type) == ARP_PROTOCOL) &&
				flow_mod_match->dl_type == entry_match->dl_type)
		{
			// In addition to general rules, reject overlap only if
			// both entries match the IP or ARP protocol
			uint8_t ip_len_flow = (OFPFW_NW_SRC_ALL >> OFPFW_NW_SRC_SHIFT) -
					((ntohl(flow_mod_match->wildcards) & OFPFW_NW_SRC_MASK) >>
							OFPFW_NW_SRC_SHIFT);
			uint8_t ip_len_entry = (OFPFW_NW_SRC_ALL >>
					OFPFW_NW_SRC_SHIFT) - ((ntohl(entry_match->wildcards) &
							OFPFW_NW_SRC_MASK) >> OFPFW_NW_SRC_SHIFT);
			if (ip_len_flow > 0 && ip_len_entry > 0)
			{
				// For the purposes of checking whether the IP source addresses
				// differ, only compare the bits that are not wildcarded by
				// either entry
				if (!openflow_flowtable_ip_compare(
						ntohl(flow_mod_match->nw_src),
						ntohl(entry_match->nw_src),
						ip_len_flow < ip_len_entry ?
								ip_len_flow : ip_len_entry))
				{
					continue;
				}
			}
		}

		// Match on IP destination address
		if ((ntohs(flow_mod_match->dl_type) == IP_PROTOCOL ||
				ntohs(flow_mod_match->dl_type) == ARP_PROTOCOL) &&
				flow_mod_match->dl_type == entry_match->dl_type)
		{
			// In addition to general rules, reject overlap only if
			// both entries match the IP or ARP protocol
			uint8_t ip_len_flow = (OFPFW_NW_DST_ALL >> OFPFW_NW_DST_SHIFT) -
					((ntohl(flow_mod_match->wildcards) & OFPFW_NW_DST_MASK) >>
							OFPFW_NW_DST_SHIFT);
			uint8_t ip_len_entry = (OFPFW_NW_DST_ALL >>
					OFPFW_NW_DST_SHIFT) - ((ntohl(entry_match->wildcards) &
							OFPFW_NW_DST_MASK) >> OFPFW_NW_DST_SHIFT);
			if (ip_len_flow > 0 && ip_len_entry > 0)
			{
				// For the purposes of checking whether the IP destination
				// addresses differ, only compare the bits that are not
				// wildcarded by either entry
				if (!openflow_flowtable_ip_compare(
						ntohl(flow_mod_match->nw_dst),
						ntohl(entry_match->nw_dst),
						ip_len_flow < ip_len_entry ?
								ip_len_flow : ip_len_entry))
				{
					continue;
				}
			}
		}

		// Reject overlap on TCP/UDP source port or ICMP type
		if (ntohs(flow_mod_match->dl_type) == IP_PROTOCOL &&
				flow_mod_match->dl_type == entry_match->dl_type)
		{
			if ((flow_mod_match->nw_proto == ICMP_PROTOCOL ||
					flow_mod_match->nw_proto == TCP_PROTOCOL ||
					flow_mod_match->nw_proto == UDP_PROTOCOL) &&
					flow_mod_match->nw_proto == entry_match->nw_proto)
			{
				// In addition to general rules, reject overlap only if
				// both entries match the IP protocol, as well as either the
				// ICMP, TCP, or UDP protocol
				if (!(ntohl(flow_mod_match->wildcards) & OFPFW_TP_SRC) &&
						!(ntohl(entry_match->wildcards) & OFPFW_TP_SRC))
				{
					if (flow_mod_match->tp_src != entry_match->tp_src)
					{
						continue;
					}
				}
			}
		}

		// Reject overlap on TCP/UDP destination port or ICMP code
		if (ntohs(flow_mod_match->dl_type) == IP_PROTOCOL &&
				flow_mod_match->dl_type == entry_match->dl_type)
		{
			if ((flow_mod_match->nw_proto == ICMP_PROTOCOL ||
					flow_mod_match->nw_proto == TCP_PROTOCOL ||
					flow_mod_match->nw_proto == UDP_PROTOCOL) &&
					flow_mod_match->nw_proto == entry_match->nw_proto)
			{
				// In addition to general rules, reject overlap only if
				// both entries match the IP protocol, as well as either the
				// ICMP, TCP, or UDP protocol
				if (!(ntohl(flow_mod_match->wildcards) & OFPFW_TP_DST) &&
						!(ntohl(entry_match->wildcards) & OFPFW_TP_DST))
				{
					if (flow_mod_match->tp_dst != entry_match->tp_dst)
					{
						continue;
					}
				}
			}
		}

		*index = i;
		return 1;
	}

	return 0;
}

/**
 * Determines whether there is an entry in the flowtable that matches the
 * specified entry. An entry matches another entry if the ofp_match struct in
 * the second entry is identical to or more specific than the ofp_match struct
 * in the second entry.
 *
 * @param flow_mod    A pointer to an ofp_flow_mod struct containing the
 * 					  specified entry.
 * @param index       A pointer to a variable used to store the index of the
 *                    matching entry, if any.
 * @param start_index The index at which to begin matching comparisons.
 * @param out_port    The output port which entries are required to have an
 *                    action for to be matched.
 *
 * @return 1 if a match is found, 0 otherwise.
 */
static uint8_t openflow_flowtable_find_matching_entry(ofp_flow_mod* flow_mod,
	uint32_t *index, uint32_t start_index, uint16_t out_port)
{
	uint32_t i, j;
	ofp_match *flow_mod_match = &flow_mod->match;
	for (i = start_index; i < OPENFLOW_MAX_FLOWTABLE_ENTRIES; i++)
	{
		// Reject match for inactive entries
		if (!flowtable->entries[i].active)
		{
			continue;
		}

		// Verify that this entry contains an output action for the specified
		// port, if one was specified; if there is no such action, then we can
		// reject the match
		uint8_t out_port_match = 0;
		if (out_port != OFPP_NONE)
		{
			for (j = 0; j < OPENFLOW_MAX_ACTIONS; j++)
			{
				if (flowtable->entries[i].actions[j].active)
				{
					ofp_action_output *action = (ofp_action_output *)
						&flowtable->entries[i].actions[j].action;
					if (ntohs(action->type) == OFPAT_OUTPUT &&
						ntohs(action->port) == out_port)
					{
						out_port_match = 1;
						break;
					}
				}
			}
		}
		if (out_port != OFPP_NONE && !out_port_match)
		{
			continue;
		}

		// In general, reject the match if the specified field is not
		// wildcarded in the query and either the query does not match the
		// entry or the field is wildcarded in the entry

		ofp_match *entry_match = &flowtable->entries[i].match;

		// Accept match if query entry has the all fields wildcard
		if (ntohl(flow_mod_match->wildcards) == OFPFW_ALL)
		{
			*index = i;
			return 1;
		}

		// Reject match on input port
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_IN_PORT))
		{
			if ((ntohl(entry_match->wildcards) & OFPFW_IN_PORT) ||
					entry_match->in_port != flow_mod_match->in_port) {
				continue;
			}
		}

		// Reject match on Ethernet source MAC address
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_SRC))
		{
			if ((ntohl(entry_match->wildcards) & OFPFW_DL_SRC) ||
					entry_match->dl_src != flow_mod_match->dl_src) {
				continue;
			}
		}

		// Reject match on Ethernet destination MAC address
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_DST))
		{
			if ((ntohl(entry_match->wildcards) & OFPFW_DL_DST) ||
					entry_match->dl_dst != flow_mod_match->dl_dst) {
				continue;
			}
		}

		// Reject match on Ethernet VLAN ID
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_VLAN))
		{
			if ((ntohl(entry_match->wildcards) & OFPFW_DL_VLAN) ||
					entry_match->dl_vlan != flow_mod_match->dl_vlan) {
				continue;
			}
		}

		// Reject match on Ethernet VLAN priority
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_VLAN))
		{
			if (ntohs(flow_mod_match->dl_vlan) != OFP_VLAN_NONE)
			{
				// In addition to general rule, reject match only if VLAN
				// ID is not wildcarded in the query entry and the VLAN ID
				// is not set to OFP_VLAN_NONE in the query entry
				if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_VLAN_PCP))
				{
					if ((ntohl(entry_match->wildcards) & OFPFW_DL_VLAN) ||
							ntohs(entry_match->dl_vlan) == OFP_VLAN_NONE ||
							(ntohl(entry_match->wildcards) &
									OFPFW_DL_VLAN_PCP) ||
									entry_match->dl_vlan_pcp !=
											flow_mod_match->dl_vlan_pcp)
					{
						// In addition to general rule, reject match if VLAN ID
						// is wildcarded in the entry or if VLAN ID is set to
						// OFP_VLAN_NONE in the entry
						continue;
					}
				}
			}
		}

		// Reject match on Ethernet frame type
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_TYPE))
		{
			if ((ntohl(entry_match->wildcards) & OFPFW_DL_TYPE) ||
					entry_match->dl_type != flow_mod_match->dl_type)
			{
				continue;
			}
		}

		// Reject match on IP type of service
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_NW_TOS))
		{
			if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_TYPE) &&
					ntohs(flow_mod_match->dl_type) == IP_PROTOCOL)
			{
				// In addition to general rule, reject match only if the query
				// entry matches the IP protocol
				if ((ntohl(entry_match->wildcards) & OFPFW_NW_TOS) ||
						entry_match->nw_tos != flow_mod_match->nw_tos ||
						(ntohl(entry_match->wildcards) & OFPFW_DL_TYPE) ||
						entry_match->dl_type != flow_mod_match->dl_type)
				{
					// In addition to general rule, reject match if the entry
					// does not match the query entry protocol
					continue;
				}
			}
		}

		// Reject match IP protocol or ARP opcode
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_NW_PROTO))
		{
			if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_TYPE) &&
					(ntohs(flow_mod_match->dl_type) == IP_PROTOCOL ||
					ntohs(flow_mod_match->dl_type) == ARP_PROTOCOL))
			{
				// In addition to general rule, reject match only if the query
				// entry matches the IP or ARP protocol
				if ((ntohl(entry_match->wildcards) & OFPFW_NW_PROTO) ||
						entry_match->nw_proto != flow_mod_match->nw_proto ||
						(ntohl(entry_match->wildcards) & OFPFW_DL_TYPE) ||
						entry_match->dl_type != flow_mod_match->dl_type)
				{
					// In addition to general rule, reject match if the entry
					// does not match the query entry protocol
					continue;
				}
			}
		}

		// Reject match on IP source address
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_TYPE) &&
				(ntohs(flow_mod_match->dl_type) == IP_PROTOCOL ||
				ntohs(flow_mod_match->dl_type) == ARP_PROTOCOL))
		{
			// In addition to general rule, reject match only if the query
			// entry matches the IP or ARP protocol
			uint8_t ip_len_flow = (OFPFW_NW_SRC_ALL >> OFPFW_NW_SRC_SHIFT) -
					((ntohl(flow_mod_match->wildcards) & OFPFW_NW_SRC_MASK) >>
							OFPFW_NW_SRC_SHIFT);
			if (ip_len_flow > 0)
			{
				uint8_t ip_len_entry = (OFPFW_NW_SRC_ALL >>
						OFPFW_NW_SRC_SHIFT) - ((ntohl(entry_match->wildcards) &
								OFPFW_NW_SRC_MASK) >> OFPFW_NW_SRC_SHIFT);
				// In addition to general rule, reject match if the entry
				// does not match the query entry protocol or if the query
				// entry has fewer wildcarded bits than the entry
				if ((ntohl(entry_match->wildcards) & OFPFW_DL_TYPE) ||
						entry_match->dl_type != flow_mod_match->dl_type ||
						ip_len_entry < ip_len_flow ||
						!openflow_flowtable_ip_compare(
								ntohl(entry_match->nw_src),
								ntohl(flow_mod_match->nw_src),
								ip_len_flow))
				{
					// For the purposes of checking whether the IP source
					// addresses differ, compare the bits that are not
					// wildcarded by the query entry
					continue;
				}
			}
		}

		// Reject match on IP destination address
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_TYPE) &&
				(ntohs(flow_mod_match->dl_type) == IP_PROTOCOL ||
				ntohs(flow_mod_match->dl_type) == ARP_PROTOCOL))
		{
			// In addition to general rule, reject match only if the query
			// entry matches the IP or ARP protocol
			uint8_t ip_len_flow = (OFPFW_NW_DST_ALL >> OFPFW_NW_DST_SHIFT) -
					((ntohl(flow_mod_match->wildcards) & OFPFW_NW_DST_MASK) >>
							OFPFW_NW_DST_SHIFT);
			if (ip_len_flow > 0)
			{
				uint8_t ip_len_entry = (OFPFW_NW_DST_ALL >>
						OFPFW_NW_DST_SHIFT) - ((ntohl(entry_match->wildcards) &
								OFPFW_NW_DST_MASK) >> OFPFW_NW_DST_SHIFT);
				// In addition to general rule, reject match if the entry
				// does not match the query entry protocol or if the query
				// entry has fewer wildcarded bits than the entry
				if ((ntohl(entry_match->wildcards) & OFPFW_DL_TYPE) ||
						entry_match->dl_type != flow_mod_match->dl_type ||
						ip_len_entry < ip_len_flow ||
						!openflow_flowtable_ip_compare(
								ntohl(entry_match->nw_dst),
								ntohl(flow_mod_match->nw_dst),
								ip_len_flow))
				{
					// For the purposes of checking whether the IP destination
					// addresses differ, compare the bits that are not
					// wildcarded by the query entry
					continue;
				}
			}
		}

		// Reject match on TCP/UDP source port or ICMP type
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_TP_SRC))
		{
			if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_TYPE) &&
					ntohs(flow_mod_match->dl_type) == IP_PROTOCOL &&
					!(ntohl(flow_mod_match->wildcards) & OFPFW_NW_PROTO) &&
					(flow_mod_match->nw_proto == ICMP_PROTOCOL ||
							flow_mod_match->nw_proto == TCP_PROTOCOL ||
							flow_mod_match->nw_proto == UDP_PROTOCOL))
			{
				// In addition to general rule, reject match only if the query
				// entry matches the IP protocol, as well as the ICMP, TCP or
				// UDP protocol
				if ((ntohl(entry_match->wildcards) & OFPFW_DL_TYPE) ||
						entry_match->dl_type != flow_mod_match->dl_type ||
						(ntohl(entry_match->wildcards) & OFPFW_NW_PROTO) ||
						entry_match->nw_proto != flow_mod_match->nw_proto ||
						(ntohl(entry_match->wildcards) & OFPFW_TP_SRC) ||
						entry_match->tp_src != flow_mod_match->tp_src)
				{
					// In addition to general rule, reject match if the entry
					// does not match the query entry protocol
					continue;
				}
			}
		}

		// Reject match on TCP/UDP destination port or ICMP code
		if (!(ntohl(flow_mod_match->wildcards) & OFPFW_TP_DST))
		{
			if (!(ntohl(flow_mod_match->wildcards) & OFPFW_DL_TYPE) &&
					ntohs(flow_mod_match->dl_type) == IP_PROTOCOL &&
					!(ntohl(flow_mod_match->wildcards) & OFPFW_NW_PROTO) &&
					(flow_mod_match->nw_proto == ICMP_PROTOCOL ||
							flow_mod_match->nw_proto == TCP_PROTOCOL ||
							flow_mod_match->nw_proto == UDP_PROTOCOL))
			{
				// In addition to general rule, reject match only if the query
				// entry matches the IP protocol, as well as the ICMP, TCP or
				// UDP protocol
				if ((ntohl(entry_match->wildcards) & OFPFW_DL_TYPE) ||
						entry_match->dl_type != flow_mod_match->dl_type ||
						(ntohl(entry_match->wildcards) & OFPFW_NW_PROTO) ||
						entry_match->nw_proto != flow_mod_match->nw_proto ||
						(ntohl(entry_match->wildcards) & OFPFW_TP_DST) ||
						entry_match->tp_dst != flow_mod_match->tp_dst)
				{
					// In addition to general rule, reject match if the entry
					// does not match the query entry protocol
					continue;
				}
			}
		}

		*index = i;
		return 1;
	}

	return 0;
}

/**
 * Determines whether there is an entry in the flowtable that is identical to
 * the specified entry. An entry is identical to another entry if they share
 * the same priority and have identical header fields.
 *
 * @param flow_mod An ofp_flow_mod struct containing the specified entry.
 * @param index    A pointer to a variable used to store the index of the
 *                 identical entry, if any.
 *
 * @return 1 if a match is found, 0 otherwise.
 */
static uint8_t openflow_flowtable_find_identical_entry(ofp_flow_mod* flow_mod,
	uint32_t *index)
{
	uint32_t i;
	for (i = 0; i < OPENFLOW_MAX_FLOWTABLE_ENTRIES; i++)
	{
		// Check if the entries' priorities are the same and whether their
		// header fields are identical (i.e. they have identical matches)
		if (flowtable->entries[i].priority == flow_mod->priority &&
			!memcmp(&flowtable->entries[i].match, &flow_mod->match,
				sizeof(ofp_match)))
		{
			*index = i;
			return 1;
		}
	}

	return 0;
}

/**
 * Applies the specified flow modification to the flowtable entry at the
 * specified index.
 *
 * @param flow_mod  The struct containing the flow modification.
 * @param index     The index of the flowtable entry to modify.
 * @param error_msg A pointer to an empty ofp_error_msg struct that will be
 *                  populated if an error occurs.
 * @param reset     If 1, resets the statistics associated with the entry.
 */
static int32_t openflow_flowtable_modify_entry_at_index(ofp_flow_mod *flow_mod,
	uint32_t index, ofp_error_msg *error_msg, uint8_t reset)
{
	openflow_flowtable_action_wrapper_type actions[OPENFLOW_MAX_ACTIONS];
	uint32_t i;

	if ((ntohs(flow_mod->flags) & OFPFF_EMERG) &&
		(ntohs(flow_mod->idle_timeout) != 0 ||
		ntohs(flow_mod->hard_timeout) != 0))
	{
		verbose(2, "[openflow_flowtable_modify_entry_at_index]:: Emergency"
			" entry has non-zero timeout. Not modifying entry.");
		error_msg->type = htons(OFPET_FLOW_MOD_FAILED);
		error_msg->code = htons(OFPFMFC_BAD_EMERG_TIMEOUT);
		return -1;
	}

	uint16_t action_block_index = sizeof(ofp_flow_mod);
	uint16_t actions_index = 0;

	ofp_action_header *action_header;
	while (action_block_index < ntohs(flow_mod->header.length))
	{
		// Use temporary pointer to increment pointer address by bytes
		char *tmp_ptr = (char *)flow_mod;
		tmp_ptr += action_block_index;
		action_header = (ofp_action_header *)tmp_ptr;

		memcpy(&actions[actions_index], action_header,
			ntohs(action_header->len));

		if (ntohs(actions[actions_index].header.type) == OFPAT_ENQUEUE)
		{
			verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
				" OFPAT_ENQUEUE action not supported. Not modifying entry.");
			error_msg->type = htons(OFPET_FLOW_MOD_FAILED);
			error_msg->code = htons(OFPFMFC_UNSUPPORTED);
			return -1;
		}
		if (ntohs(actions[actions_index].header.type) == OFPAT_VENDOR)
		{
			verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
				" OFPAT_VENDOR action not supported. Not modifying entry.");
			error_msg->type = htons(OFPET_FLOW_MOD_FAILED);
			error_msg->code = htons(OFPFMFC_UNSUPPORTED);
			return -1;
		}
		if ((ntohs(actions[actions_index].header.type) > OFPAT_ENQUEUE) &&
			(ntohs(actions[actions_index].header.type) < OFPAT_VENDOR))
		{
			verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
				" Unrecognized action. Not modifying entry.");
			error_msg->type = htons(OFPET_BAD_ACTION);
			error_msg->code = htons(OFPBAC_BAD_TYPE);
			return -1;
		}

		if (ntohs(actions[actions_index].header.type) == OFPAT_OUTPUT)
		{
			ofp_action_output *output_action =
				(ofp_action_output *) action_header;
			if (ntohs(output_action->len) != 8) {
				verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
					" OFPAT_OUTPUT action not of length 8. Not modifying"
					" entry.");
				error_msg->type = htons(OFPET_BAD_ACTION);
				error_msg->code = htons(OFPBAC_BAD_LEN);
				return -1;
			}
			if (ntohs(output_action->port) > OPENFLOW_MAX_PHYSICAL_PORTS &&
				ntohs(output_action->port) < OFPP_IN_PORT) {
				verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
					" OFPAT_OUTPUT action uses invalid port. Not modifying"
					" entry.");
				error_msg->type = htons(OFPET_BAD_ACTION);
				error_msg->code = htons(OFPBAC_BAD_OUT_PORT);
				return -1;
			}
		}
		else if (ntohs(actions[actions_index].header.type) ==
			OFPAT_SET_VLAN_VID)
		{
			if (ntohs(actions[actions_index].header.len) != 8) {
				verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
					" OFPAT_SET_VLAN_VID action not of length 8. Not"
					" modifying entry.");
				error_msg->type = htons(OFPET_BAD_ACTION);
				error_msg->code = htons(OFPBAC_BAD_LEN);
				return -1;
			}
		}
		else if (ntohs(actions[actions_index].header.type) ==
			OFPAT_SET_VLAN_PCP)
		{
			if (ntohs(actions[actions_index].header.len) != 8) {
				verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
					" OFPAT_SET_VLAN_PCP action not of length 8. Not"
					" modifying entry.");
				error_msg->type = htons(OFPET_BAD_ACTION);
				error_msg->code = htons(OFPBAC_BAD_LEN);
				return -1;
			}
		}
		else if (ntohs(actions[actions_index].header.type) ==
			OFPAT_SET_DL_SRC ||
			ntohs(actions[actions_index].header.type) == OFPAT_SET_DL_DST)
		{
			if (ntohs(actions[actions_index].header.len) != 16) {
				verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
					" OFPAT_SET_DL_SRC or OFPAT_SET_DL_DST action not of"
					" length 16. Not modifying entry.");
				error_msg->type = htons(OFPET_BAD_ACTION);
				error_msg->code = htons(OFPBAC_BAD_LEN);
				return -1;
			}
		}
		else if (ntohs(actions[actions_index].header.type) ==
			OFPAT_SET_NW_SRC ||
			ntohs(actions[actions_index].header.type) == OFPAT_SET_NW_DST)
		{
			if (ntohs(actions[actions_index].header.len) != 8) {
				verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
					" OFPAT_SET_NW_SRC or OFPAT_SET_NW_DST action not of"
					" length 8. Not modifying entry.");
				error_msg->type = htons(OFPET_BAD_ACTION);
				error_msg->code = htons(OFPBAC_BAD_LEN);
				return -1;
			}
		}
		else if (ntohs(actions[actions_index].header.type) == OFPAT_SET_NW_TOS)
		{
			if (ntohs(actions[actions_index].header.len) != 8) {
				verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
					" OFPAT_SET_NW_TOS action not of length 8. Not modifying"
					" entry.");
				error_msg->type = htons(OFPET_BAD_ACTION);
				error_msg->code = htons(OFPBAC_BAD_LEN);
				return -1;
			}
		}
		else if (ntohs(actions[actions_index].header.type) ==
			OFPAT_SET_TP_SRC ||
			ntohs(actions[actions_index].header.type) == OFPAT_SET_TP_DST)
		{
			if (ntohs(actions[actions_index].header.len) != 8) {
				verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
					" OFPAT_SET_TP_SRC or OFPAT_SET_TP_DST action not of"
					" length 8. Not modifying entry.");
				error_msg->type = htons(OFPET_BAD_ACTION);
				error_msg->code = htons(OFPBAC_BAD_LEN);
				return -1;
			}
		}

		action_block_index += ntohs(action_header->len);
		actions_index += 1;
		if (actions_index > OPENFLOW_MAX_ACTIONS) {
			verbose(2, "[openflow_flowtable_modify_entry_at_index]::"
				" Too many actions. Not modifying entry.");
			error_msg->type = htons(OFPET_BAD_ACTION);
			error_msg->code = htons(OFPBAC_TOO_MANY);
			return -1;
		}
	}

	flowtable->entries[index].active = 1;
	flowtable->entries[index].match = flow_mod->match;
	flowtable->entries[index].cookie = flow_mod->cookie;
	time(&flowtable->entries[index].last_modified);
	flowtable->entries[index].idle_timeout = flow_mod->idle_timeout;
	flowtable->entries[index].hard_timeout = flow_mod->hard_timeout;
	flowtable->entries[index].priority = flow_mod->priority;
	flowtable->entries[index].flags = flow_mod->flags;
	for (i = 0; i < OPENFLOW_MAX_ACTIONS; i++)
	{
		if (i < actions_index)
		{
			flowtable->entries[index].actions[i].active = 1;
			flowtable->entries[index].actions[i].action = actions[i];
		}
		else
		{
			flowtable->entries[index].actions[i].active = 0;
		}
	}
	if (reset)
	{
		memset(&flowtable->entries[index].stats, 0, sizeof(ofp_flow_stats));
	}

	verbose(2, "[openflow_flowtable_modify_entry_at_index]:: Modified entry"
		" at index %" PRIu32 ".", index);

	return 0;
}

/**
 * Adds the specified entry to the flowtable.
 *
 * @param flow_mod  The struct containing the entry to add to the flowtable.
 * @param error_msg A pointer to an empty ofp_error_msg struct that will be
 *                  populated if an error occurs.
 *
 * @return 0 if no error occurred, -1 otherwise.
 */
static int32_t openflow_flowtable_add(ofp_flow_mod* flow_mod,
	ofp_error_msg* error_msg)
{
	uint32_t i;
	uint16_t flags = ntohs(flow_mod->flags);

	if (flags & OFPFF_CHECK_OVERLAP)
	{
		verbose(2, "[openflow_flowtable_add]:: OFPFF_CHECK_OVERLAP flag set.");
		if (openflow_flowtable_find_overlapping_entry(flow_mod, &i))
		{
			verbose(2, "[openflow_flowtable_add]:: Overlapping entry found at"
				" index %" PRIu32 ". Not adding to table.", i);
			error_msg->type = htons(OFPET_FLOW_MOD_FAILED);
			error_msg->code = htons(OFPFMFC_OVERLAP);
			return -1;
		}
	}

	if (openflow_flowtable_find_identical_entry(flow_mod, &i))
	{
		verbose(2, "[openflow_flowtable_add]:: Replacing flowtable entry at"
			" index %" PRIu32 ".", i);
		memset(&flowtable->entries[i], 0,
			sizeof(openflow_flowtable_entry_type));
		return openflow_flowtable_modify_entry_at_index(flow_mod, i,
			error_msg, 0);
	}

	for (i = 0; i < OPENFLOW_MAX_FLOWTABLE_ENTRIES; i++)
	{
		if (!flowtable->entries[i].active)
		{
			verbose(2, "[openflow_flowtable_add]:: Adding flowtable entry at"
				" index %" PRIu32 ".", i);
			memset(&flowtable->entries[i], 0,
				sizeof(openflow_flowtable_entry_type));
			return openflow_flowtable_modify_entry_at_index(flow_mod, i,
				error_msg, 1);
		}
	}

	verbose(2, "[openflow_flowtable_add]:: No room in flowtable to add entry.");
	error_msg->type = htons(OFPET_FLOW_MOD_FAILED);
	error_msg->code = htons(OFPFMFC_ALL_TABLES_FULL);
	return -1;
}

/**
 * Modifies the specified entry in the flowtable.
 *
 * @param flow_mod  The struct containing the entry to edit in the flowtable.
 * @param error_msg A pointer to an empty ofp_error_msg struct that will be
 *                  populated if an error occurs.
 *
 * @return 0 if no error occurred, -1 otherwise.
 */
static int32_t openflow_flowtable_edit(ofp_flow_mod *flow_mod,
	ofp_error_msg *error_msg)
{
	uint32_t i;
	uint32_t start_index = 0;

	uint8_t found_match = 0;
	while (start_index < OPENFLOW_MAX_FLOWTABLE_ENTRIES)
	{
		if (openflow_flowtable_find_matching_entry(flow_mod, &i, start_index,
			OFPP_NONE))
		{
			verbose(2, "[openflow_flowtable_edit]:: Editing flowtable entry at"
				" index %" PRIu32 ".", i);
			int32_t ret = openflow_flowtable_modify_entry_at_index(flow_mod, i,
				error_msg, 0);
			if (ret < 0)
			{
				return ret;
			}
			start_index = i + 1;
			found_match = 1;
		}
		else
		{
			break;
		}
	}

	if (!found_match)
	{
		return openflow_flowtable_add(flow_mod, error_msg);
	}
	else
	{
		return 0;
	}
}

/**
 * Strictly modifies the specified entry in the flowtable.
 *
 * @param flow_mod  The struct containing the entry to edit in the flowtable.
 * @param error_msg A pointer to an empty ofp_error_msg struct that will be
 *                  populated if an error occurs.
 *
 * @return 0 if no error occurred, -1 otherwise.
 */
static int32_t openflow_flowtable_edit_strict(ofp_flow_mod *flow_mod,
	ofp_error_msg *error_msg)
{
	uint32_t i;

	if (openflow_flowtable_find_identical_entry(flow_mod, &i))
	{
		verbose(2, "[openflow_flowtable_edit_strict]:: Editing flowtable entry"
			" at index %" PRIu32 ".", i);
		return openflow_flowtable_modify_entry_at_index(flow_mod, i,
			error_msg, 0);
	}

	return openflow_flowtable_add(flow_mod, error_msg);
}

/**
 * Deletes the specified entry or entries in the flowtable.
 *
 * @param flow_mod  The struct containing the entry to edit in the flowtable.
 * @param error_msg A pointer to an empty ofp_error_msg struct that will be
 *                  populated if an error occurs.
 *
 * @return 0 if no error occurred, -1 otherwise.
 */
static int32_t openflow_flowtable_delete(ofp_flow_mod *flow_mod,
	ofp_error_msg *error_msg)
{
	uint32_t i;
	uint32_t start_index = 0;

	uint8_t found_match = 0;
	while (start_index < OPENFLOW_MAX_FLOWTABLE_ENTRIES)
	{
		if (openflow_flowtable_find_matching_entry(flow_mod, &i, start_index,
			ntohs(flow_mod->out_port)))
		{
			verbose(2, "[openflow_flowtable_delete]:: Deleting flowtable entry"
				" at index %" PRIu32 ".", i);

			if (ntohs(flowtable->entries[i].flags) & OFPFF_SEND_FLOW_REM)
			{
				openflow_ctrl_iface_send_flow_removed(flowtable->entries[i],
									OFPRR_DELETE);
			}

			memset(&flowtable->entries[i], 0,
				sizeof(openflow_flowtable_entry_type));
			start_index = i + 1;
		}
		else
		{
			break;
		}
	}

	return 0;
}

/**
 * Strictly deletes the specified entry or entries in the flowtable.
 *
 * @param flow_mod  The struct containing the entry to edit in the flowtable.
 * @param error_msg A pointer to an empty ofp_error_msg struct that will be
 *                  populated if an error occurs.
 *
 * @return 0 if no error occurred, -1 otherwise.
 */
static int32_t openflow_flowtable_delete_strict(ofp_flow_mod *flow_mod,
	ofp_error_msg *error_msg)
{
	uint32_t i;

	if (openflow_flowtable_find_identical_entry(flow_mod, &i))
	{
		verbose(2, "[openflow_flowtable_edit_strict]:: Deleting flowtable"
			" entry at index %" PRIu32 ".", i);

		if (ntohs(flowtable->entries[i].flags) & OFPFF_SEND_FLOW_REM)
		{
			openflow_ctrl_iface_send_flow_removed(flowtable->entries[i],
					OFPRR_DELETE);
		}

		memset(&flowtable->entries[i], 0,
			sizeof(openflow_flowtable_entry_type));
	}

	return 0;
}

/**
 * Applies the specified modification to the flowtable.
 *
 * @param modify_info The modification to apply to the flowtable.
 * @param error_msg   A pointer to an empty ofp_error_msg struct that will be
 *                    populated if an error occurs.
 *
 * @return 0 if no error occurred, -1 otherwise.
 */
int32_t openflow_flowtable_modify(ofp_flow_mod *flow_mod,
	ofp_error_msg *error_msg)
{
	pthread_mutex_lock(&flowtable_mutex);

	uint16_t command = ntohs(flow_mod->command);
	int32_t status;
	if (command == OFPFC_ADD)
	{
		verbose(2, "[openflow_flowtable_modify]:: Modify command is"
			" OFPFC_ADD.");
		status = openflow_flowtable_add(flow_mod, error_msg);
	}
	else if (command == OFPFC_MODIFY)
	{
		verbose(2, "[openflow_flowtable_modify]:: Modify command is"
			" OFPFC_MODIFY.");
		status = openflow_flowtable_edit(flow_mod, error_msg);
	}
	else if (command == OFPFC_MODIFY_STRICT)
	{
		verbose(2, "[openflow_flowtable_modify]:: Modify command is"
			" OFPFC_MODIFY_STRICT.");
		status = openflow_flowtable_edit_strict(flow_mod, error_msg);
	}
	else if (command == OFPFC_DELETE)
	{
		verbose(2, "[openflow_flowtable_modify]:: Modify command is"
			" OFPFC_DELETE.");
		status = openflow_flowtable_delete(flow_mod, error_msg);
	}
	else if (command == OFPFC_DELETE_STRICT)
	{
		verbose(2, "[openflow_flowtable_modify]:: Modify command is"
			" OFPFC_DELETE_STRICT.");
		status = openflow_flowtable_delete_strict(flow_mod, error_msg);
	}
	else
	{
		verbose(2, "[openflow_flowtable_modify]:: Modify command not"
			" recognized.");
		error_msg->type = htons(OFPET_FLOW_MOD_FAILED);
		error_msg->code = htons(OFPFMFC_BAD_COMMAND);
		status = -1;
	}

	pthread_mutex_unlock(&flowtable_mutex);
	return status;
}

/**
 * Prints the specified match to the console.
 *
 * @param match A pointer to the match to print.
 */
static void openflow_flowtable_print_wildcards(uint32_t wildcards)
{
	if (ntohl(wildcards) == OFPFW_ALL)
	{
		printf("\t\tAll fields\n");
		return;
	}

	if (ntohl(wildcards) & OFPFW_IN_PORT)
	{
		printf("\t\tInput port\n");
	}

	if (ntohl(wildcards) & OFPFW_DL_SRC)
	{
		printf("\t\tEthernet source MAC address\n");
	}

	if (ntohl(wildcards) & OFPFW_DL_DST)
	{
		printf("\t\tEthernet destination MAC address\n");
	}

	if (ntohl(wildcards) & OFPFW_DL_VLAN)
	{
		printf("\t\tEthernet VLAN ID\n");
	}
	else if ((ntohl(wildcards) & OFPFW_DL_VLAN_PCP))
	{
		printf("\t\tEthernet VLAN priority\n");
	}

	if (ntohl(wildcards) & OFPFW_DL_TYPE)
	{
		printf("\t\tEthernet frame type\n");
	}
	else
	{
		if (ntohl(wildcards) & OFPFW_NW_TOS)
		{
			printf("\t\tIP type of service\n");
		}

		if (ntohl(wildcards) & OFPFW_NW_PROTO)
		{
			printf("\t\tIP protocol or ARP opcode\n");
		}

		uint8_t ip_src_len = (ntohl(wildcards) & OFPFW_NW_DST_MASK) >>
				OFPFW_NW_SRC_SHIFT;
		printf("\t\tIP source address wildcard bit count: %" PRIu8 " LSBs\n",
				ip_src_len);

		uint8_t ip_dst_len = (ntohl(wildcards) & OFPFW_NW_DST_MASK) >>
				OFPFW_NW_DST_SHIFT;
		printf("\t\tIP destination address wildcard bit count: %" PRIu8
				" LSBs\n", ip_dst_len);

		if (!(ntohl(wildcards) & OFPFW_NW_PROTO))
		{
			if (ntohl(wildcards) & OFPFW_TP_SRC)
			{
				printf("\t\tTCP/UDP source port or ICMP type\n");
			}

			if (ntohl(wildcards) & OFPFW_TP_DST)
			{
				printf("\t\tTCP/UDP destination port or ICMP code\n");
			}
		}
	}
}

/**
 * Prints the specified match to the CLI.
 *
 * @param match A pointer to the match to print.
 */
static void openflow_flowtable_print_match(ofp_match *match)
{
	printf("\tWildcards: %" PRIX32 "\n", ntohl(match->wildcards));
	openflow_flowtable_print_wildcards(match->wildcards);

	if (!(ntohl(match->wildcards) & OFPFW_IN_PORT))
	{
		printf("\tInput port: %" PRIu16 "\n", ntohs(match->in_port));
	}

	if (!(ntohl(match->wildcards) & OFPFW_DL_SRC))
	{
		char dl_src[50];
		MAC2Colon(dl_src, match->dl_src);
		printf("\tEthernet source MAC address: %s\n", dl_src);
	}

	if (!(ntohl(match->wildcards) & OFPFW_DL_DST))
	{
		char dl_dst[50];
		MAC2Colon(dl_dst, match->dl_dst);
		printf("\tEthernet destination MAC address: %s\n", dl_dst);
	}

	if (!(ntohl(match->wildcards) & OFPFW_DL_VLAN))
	{
		printf("\tEthernet VLAN ID: %" PRIu16 "\n", ntohs(match->dl_vlan));

		if (match->dl_vlan != OFP_VLAN_NONE &&
				!(ntohl(match->wildcards) & OFPFW_DL_VLAN_PCP))
		{
			printf("\tEthernet VLAN priority: %" PRIu8 "\n",
					match->dl_vlan_pcp);
		}
	}

	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE))
	{
		if (ntohs(match->dl_type) == IP_PROTOCOL)
		{
			printf("\tEthernet frame type: IP\n");
		}
		else if (ntohs(match->dl_type) == ARP_PROTOCOL)
		{
			printf("\tEthernet frame type: ARP\n");
		}
		else
		{
			printf("\tEthernet frame type: %" PRIu16 "\n",
					ntohs(match->dl_type));
		}
	}

	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE) &&
			ntohs(match->dl_type) == IP_PROTOCOL)
	{
		if (!(ntohl(match->wildcards) & OFPFW_NW_TOS))
		{
			printf("\tIP type of service: %" PRIu8 "\n", match->nw_tos);
		}
	}

	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE) &&
			(ntohs(match->dl_type) == IP_PROTOCOL ||
					ntohs(match->dl_type) == ARP_PROTOCOL))
	{
		if (!(ntohl(match->wildcards) & OFPFW_NW_PROTO))
		{
			if (match->nw_proto == ICMP_PROTOCOL)
			{
				printf("\tIP protocol: ICMP\n");
			}
			else if (match->nw_proto == TCP_PROTOCOL)
			{
				printf("\tIP protocol: TCP\n");
			}
			else if (match->nw_proto == UDP_PROTOCOL)
			{
				printf("\tIP protocol: UDP\n");
			}
			else
			{
				printf("\tIP protocol or ARP opcode: %" PRIu8 "\n",
						match->nw_proto);
			}
		}

		uint8_t ip_src_len = (ntohl(match->wildcards) & OFPFW_NW_SRC_MASK) >>
				OFPFW_NW_SRC_SHIFT;
		if (ip_src_len < OFPFW_NW_SRC_ALL >> OFPFW_NW_SRC_SHIFT)
		{
			char nw_src[50];
			uint32_t nw_src_raw = ntohl(match->nw_src);
			IP2Dot(nw_src, (uint8_t *)&nw_src_raw);
			printf("\tIP source address: %s\n", nw_src);
		}

		uint8_t ip_dst_len = (ntohl(match->wildcards) & OFPFW_NW_DST_MASK) >>
						OFPFW_NW_DST_SHIFT;
		if (ip_dst_len < OFPFW_NW_DST_ALL >> OFPFW_NW_DST_SHIFT)
		{
			char nw_dst[50];
			uint32_t nw_dst_raw = ntohl(match->nw_dst);
			IP2Dot(nw_dst, (uint8_t *)&nw_dst_raw);
			printf("\tIP destination address: %s\n", nw_dst);
		}
	}

	if (!(ntohl(match->wildcards) & OFPFW_DL_TYPE) &&
			ntohs(match->dl_type) == IP_PROTOCOL)
	{
		if (!(ntohl(match->wildcards) & OFPFW_NW_PROTO) &&
				match->nw_proto == TCP_PROTOCOL)
		{
			if (!(ntohl(match->wildcards) & OFPFW_TP_SRC))
			{
				printf("\tTCP source port: %" PRIu16 "\n",
						ntohs(match->tp_src));
			}
			if (!(ntohl(match->wildcards) & OFPFW_TP_DST))
			{
				printf("\tTCP destination port: %" PRIu16 "\n",
						ntohs(match->tp_dst));
			}
		}
		else if (!(ntohl(match->wildcards) & OFPFW_NW_PROTO) &&
				match->nw_proto == UDP_PROTOCOL)
		{
			if (!(ntohl(match->wildcards) & OFPFW_TP_SRC))
			{
				printf("\tUDP source port: %" PRIu16 "\n",
						ntohs(match->tp_src));
			}
			if (!(ntohl(match->wildcards) & OFPFW_TP_DST))
			{
				printf("\tUDP destination port: %" PRIu16 "\n",
						ntohs(match->tp_dst));
			}
		}
		else if (!(ntohl(match->wildcards) & OFPFW_NW_PROTO) &&
				match->nw_proto == ICMP_PROTOCOL)
		{
			if (!(ntohl(match->wildcards) & OFPFW_TP_SRC))
			{
				printf("\tICMP type: %" PRIu16 "\n", ntohs(match->tp_src));
			}
			if (!(ntohl(match->wildcards) & OFPFW_TP_DST))
			{
				printf("\tICMP code: %" PRIu16 "\n", ntohs(match->tp_dst));
			}
		}
	}
}

/**
 * Prints the specified action to the CLI.
 */
static void openflow_flowtable_print_action(
		openflow_flowtable_action_wrapper_type *action)
{
	if (ntohs(action->header.type) == OFPAT_OUTPUT)
	{
		printf("\t\tType: OFPAT_OUTPUT\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
		uint16_t port = ntohs(((ofp_action_output *) action)->port);
		if (port == OFPP_IN_PORT)
		{
			printf("\t\tOutput port: OFPP_IN_PORT\n");
		}
		else if (port == OFPP_NORMAL)
		{
			printf("\t\tOutput port: OFPP_NORMAL\n");
		}
		else if (port == OFPP_FLOOD)
		{
			printf("\t\tOutput port: OFPP_FLOOD\n");
		}
		else if (port == OFPP_ALL)
		{
			printf("\t\tOutput port: OFPP_ALL\n");
		}
		else if (port == OFPP_CONTROLLER)
		{
			printf("\t\tOutput port: OFPP_CONTROLLER\n");
		}
		else if (port == OFPP_LOCAL)
		{
			printf("\t\tOutput port: OFPP_LOCAL\n");
		}
		else
		{
			printf("\t\tOutput port: %" PRIu16 "\n", port);
		}
		printf("\t\tMaximum length to send to controller (bytes): %"
				PRIu16 "\n", ntohs(((ofp_action_output *) action)->max_len));
	}
	else if (ntohs(action->header.type) == OFPAT_SET_VLAN_VID)
	{
		printf("\t\tType: OFPAT_SET_VLAN_VID\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
		printf("\t\tEthernet VLAN ID: %" PRIu16 "\n",
				ntohs(((ofp_action_vlan_vid *) action)->vlan_vid));
	}
	else if (ntohs(action->header.type) == OFPAT_SET_VLAN_PCP)
	{
		printf("\t\tType: OFPAT_SET_VLAN_PCP\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
		printf("\t\tEthernet VLAN priority: %" PRIu16 "\n",
				ntohs(((ofp_action_vlan_pcp *) action)->vlan_pcp));
	}
	else if (ntohs(action->header.type) == OFPAT_STRIP_VLAN)
	{
		printf("\t\tType: OFPAT_STRIP_VLAN\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
	}
	else if (ntohs(action->header.type) == OFPAT_SET_DL_SRC)
	{
		printf("\t\tType: OFPAT_SET_DL_SRC\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
		char dl_src[50];
		MAC2Colon(dl_src, ((ofp_action_dl_addr *) action)->dl_addr);
		printf("\t\tEthernet source MAC address: %s\n", dl_src);
	}
	else if (ntohs(action->header.type) == OFPAT_SET_DL_DST)
	{
		printf("\t\tType: OFPAT_SET_DL_DST\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
		char dl_dst[50];
		MAC2Colon(dl_dst, ((ofp_action_dl_addr *) action)->dl_addr);
		printf("\t\tEthernet destination MAC address: %s\n", dl_dst);
	}
	else if (ntohs(action->header.type) == OFPAT_SET_NW_SRC)
	{
		printf("\t\tType: OFPAT_SET_NW_SRC\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
		char nw_src[50];
		uint32_t nw_src_raw = ntohl(((ofp_action_nw_addr *) action)->nw_addr);
		IP2Dot(nw_src, (uint8_t *)&nw_src_raw);
		printf("\t\tIP source address: %s\n", nw_src);
	}
	else if (ntohs(action->header.type) == OFPAT_SET_NW_DST)
	{
		printf("\t\tType: OFPAT_SET_NW_DST\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
		char nw_dst[50];
		uint32_t nw_dst_raw = ntohl(((ofp_action_nw_addr *) action)->nw_addr);
		IP2Dot(nw_dst, (uint8_t *)&nw_dst_raw);
		printf("\t\tIP source address: %s\n", nw_dst);
	}
	else if (ntohs(action->header.type) == OFPAT_SET_NW_TOS)
	{
		printf("\t\tType: OFPAT_SET_NW_TOS\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
		printf("\t\tIP type of service: %" PRIu8 "\n",
				((ofp_action_nw_tos *) action)->nw_tos);
	}
	else if (ntohs(action->header.type) == OFPAT_SET_TP_SRC)
	{
		printf("\t\tType: OFPAT_SET_TP_SRC\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
		printf("\t\tTCP/UDP source port or ICMP type: %" PRIu16 "\n",
				ntohs(((ofp_action_tp_port *) action)->tp_port));
	}
	else if (ntohs(action->header.type) == OFPAT_SET_TP_DST)
	{
		printf("\t\tType: OFPAT_SET_TP_DST\n");
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
		printf("\t\tTCP/UDP destination port or ICMP code: %" PRIu16 "\n",
				ntohs(((ofp_action_tp_port *) action)->tp_port));
	}
	else
	{
		printf("\t\tType: %" PRIu16 "\n", ntohs(action->header.type));
		printf("\t\tLength: %" PRIu16 "\n", ntohs(action->header.len));
	}
}

/**
 * Prints the OpenFlow flowtable entries to the CLI.
 */
void openflow_flowtable_print_entries()
{
	pthread_mutex_lock(&flowtable_mutex);

	if (!rconfig.openflow)
	{
		printf("OpenFlow not enabled\n");
		pthread_mutex_unlock(&flowtable_mutex);
		return;
	}
	uint32_t i;

	for(i = 0; i < OPENFLOW_MAX_FLOWTABLE_ENTRIES; i++)
	{
		openflow_flowtable_entry_type entry = flowtable->entries[i];
		if (entry.active) {
			printf("\n");
			printf("=========\n");
			printf("Entry %d\n", i);
			printf("=========\n");
			printf("\n");

			printf("Match:\n");
			openflow_flowtable_print_match(&entry.match);

			printf("Cookie: %" PRIu64 "\n", entry.cookie);

			char last_matched_str[100];
			struct tm *last_matched = localtime(&entry.last_matched);
			strftime(last_matched_str, 100, "%Y-%m-%d %H:%M:%S", last_matched);
			printf("Last matched time: %s\n", last_matched_str);

			char last_modified_str[100];
			struct tm *last_modified = localtime(&entry.last_modified);
			strftime(last_modified_str, 100, "%Y-%m-%d %H:%M:%S",
					last_modified);
			printf("Last modified time: %s\n", last_modified_str);

			if (!(ntohs(entry.flags) & OFPFF_EMERG))
			{
				printf("Last matched timeout (seconds): %" PRIu16 "\n",
									ntohs(entry.idle_timeout));

				printf("Last modified timeout (seconds): %" PRIu16 "\n",
						ntohs(entry.hard_timeout));
			}

			printf("Priority: %" PRIu32 "\n", ntohs(entry.hard_timeout));

			printf("Entry flags: %" PRIu16 "\n", ntohs(entry.flags));
			if (ntohs(entry.flags) & OFPFF_SEND_FLOW_REM)
			{
				printf("\tOFPFF_SEND_FLOW_REM\n");
			}
			if (ntohs(entry.flags) & OFPFF_CHECK_OVERLAP)
			{
				printf("\tOFPFF_CHECK_OVERLAP\n");
			}
			if (ntohs(entry.flags) & OFPFF_EMERG)
			{
				printf("\tOFPFF_EMERG\n");
			}

			printf("Actions:\n");
			uint32_t i;
			for (i = 0; i < OPENFLOW_MAX_ACTIONS; i++)
			{
				if (entry.actions[i].active) {
					printf("\tAction %" PRIu32 ":\n", i);
					openflow_flowtable_print_action(&entry.actions[i].action);
				}
			}
		}
	}

	pthread_mutex_unlock(&flowtable_mutex);
}
