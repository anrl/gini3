#include "flowtable.h"
#include "message.h"
#include "ip.h"
#include "tcp.h"
#include "udp.h"
#include "arp.h"
#include "grouter.h"
#include "protocols.h"

openflow_flowtable_type* flowtable;

int32_t flowtable_ip_wildcard_compare(uint8_t *addr, uint8_t *addr_cmp,
								      uint32_t wildcards, uint8_t src) {
	if (src)
	{
		wildcards = (wildcards & OFPFW_NW_DST_ALL) >> OFPFW_NW_SRC_SHIFT;
	}
	else
	{
		wildcards = (wildcards & OFPFW_NW_DST_ALL) >> OFPFW_NW_DST_SHIFT;
	}
	return memcmp(addr, addr_cmp, wildcards);
}

/**
 * Determines whether the specified OpenFlow match matches the specified packet.
 *
 * @param match  The match to test the packet against.
 * @param packet The packet to test.
 *
 * @return 1 if the packet matches the match, 0 otherwise.
 */
uint8_t flowtable_match_packet(openflow_flowtable_match_type *match,
							   gpacket_t *packet)
{
	uint8_t tmpbuf[MAX_TMPBUF_LEN];

	// All field wildcard
	if (match->wildcards == OFPFW_ALL)
	{
		verbose(2, "[flowtable_match_packet]:: Packet matched (all field"
				   " wildcard)");
		return 1;
	}

	// Switch input port
	if ((match->wildcards & OFPFW_IN_PORT != OFPFW_IN_PORT) &&
		(packet->frame.src_interface != match->in_port))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (switch input"
				   " port)");
		return 0;
	}
	// Source MAC address
	if ((match->wildcards & OFPFW_DL_SRC != OFPFW_DL_SRC) &&
		(packet->data.header.src != match->dl_src))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (source MAC"
				   " address");
		return 0;
	}
	// Destination MAC address
	if ((match->wildcards & OFPFW_DL_DST != OFPFW_DL_DST) &&
		(packet->data.header.dst != match->dl_dst))
	{
		verbose(2, "[flowtable_match_packet]:: Packet not matched (destination"
				   " MAC address");
		return 0;
	}
	// VLAN ID
	if ((match->wildcards & OFPFW_DL_VLAN != OFPFW_DL_VLAN) && 0)
	{
		// VLAN ID is not yet supported
		// TODO: Add VLAN support to GNET and add a VLAN tag field to gpacket_t
		verbose(2, "[flowtable_match_packet]:: Packet not matched (VLAN ID");
		return 0;
	}
	// VLAN priority
	if ((match->wildcards & OFPFW_DL_VLAN_PCP != OFPFW_DL_VLAN_PCP) && 0)
	{
		// VLAN priority is not yet supported
		// TODO: Add VLAN support to GNET and add a VLAN tag field to gpacket_t
		verbose(2, "[flowtable_match_packet]:: Packet not matched (VLAN"
				   " priority");
		return 0;
	}
	// Ethernet frame type
	if ((match->wildcards & OFPFW_DL_TYPE != OFPFW_DL_TYPE) &&
		(packet->data.header.prot != match->dl_type))
	{
		// TODO: Add 802.13 support to GNET; right now we are technically doing
		// something wrong as the prot field may actually be the frame Length
		// under an earlier but valid standard
		verbose(2, "[flowtable_match_packet]:: Packet not matched (Ethernet"
					" frame type");
		return 0;
	}

	// IP packet
	if (ntohs(packet->data.header.prot) == IP_PROTOCOL)
	{
		ip_packet_t *ip_packet = (ip_packet_t *) &packet->data.data;
		// IP type of service
		if ((match->wildcards & OFPFW_NW_TOS != OFPFW_NW_TOS) &&
			(ip_packet->ip_tos != match->nw_tos))
		{
			verbose(2, "[flowtable_match_packet]:: Packet not matched (IP"
					   " type of service)");
			return 0;
		}
		// IP protocol
		if ((match->wildcards & OFPFW_NW_PROTO != OFPFW_NW_PROTO) &&
			(ip_packet->ip_prot != match->nw_proto))
		{
			verbose(2, "[flowtable_match_packet]:: Packet not matched (IP"
					   " protocol)");
			return 0;
		}
		// IP source address
		if (flowtable_ip_wildcard_compare(gNtohl(tmpbuf, ip_packet->ip_src),
									 	  (uint8_t *) match->nw_src,
										  match->wildcards, 1))
		{
			verbose(2, "[flowtable_match_packet]:: Packet not matched (IP"
					   " source address)");
			return 0;
		}
		// IP destination address
		if (flowtable_ip_wildcard_compare(gNtohl(tmpbuf, ip_packet->ip_dst),
									      (uint8_t *) match->nw_dst,
										  match->wildcards, 0))
		{
			verbose(2, "[flowtable_match_packet]:: Packet not matched (IP"
					   " destination address)");
			return 0;
		}

		// TCP packet
		if (ip_packet->ip_prot == TCP_PROTOCOL) {
			tcp_packet_type *tcp_packet = (tcp_packet_type *) ip_packet + 1;
			// TCP source port
			if ((match->wildcards & OFPFW_TP_SRC != OFPFW_TP_SRC) &&
				(tcp_packet->src_port != match->tp_src))
			{
				verbose(2, "[flowtable_match_packet]:: Packet not matched (TCP"
						   " source port)");
				return 0;
			}
			// TCP destination port
			if ((match->wildcards & OFPFW_TP_DST != OFPFW_TP_DST) &&
				(tcp_packet->dst_port != match->tp_dst))
			{
				verbose(2, "[flowtable_match_packet]:: Packet not matched (TCP"
						   " destination port)");
				return 0;
			}
		}

		// UDP packet
		if (ip_packet->ip_prot == UDP_PROTOCOL) {
			udp_packet_type *udp_packet = (udp_packet_type *) ip_packet + 1;
			// UDP source port
			if ((match->wildcards & OFPFW_TP_SRC != OFPFW_TP_SRC) &&
				(udp_packet->src_port != match->tp_src))
			{
				verbose(2, "[flowtable_match_packet]:: Packet not matched (UDP"
						   " source port)");
				return 0;
			}
			// UDP destination port
			if ((match->wildcards & OFPFW_TP_DST != OFPFW_TP_DST) &&
				(udp_packet->dst_port != match->tp_dst))
			{
				verbose(2, "[flowtable_match_packet]:: Packet not matched (UDP"
						   " destination port)");
				return 0;
			}
		}
	}

	// ARP packet
	if (ntohs(packet->data.header.prot) == ARP_PROTOCOL)
	{
		arp_packet_t *arp_packet = (arp_packet_t *) &packet->data.data;
		// ARP opcode
		if ((match->wildcards & OFPFW_NW_PROTO != OFPFW_NW_PROTO) &&
			(arp_packet->arp_opcode & 0xFF != match->nw_proto))
		{
			verbose(2, "[flowtable_match_packet]:: Packet not matched (ARP"
					   " opcode)");
			return 0;
		}
	}

	return 1;
}

openflow_flowtable_entry_type *flowtable_get_match_packet(gpacket_t *packet)
{
	uint32_t i, current_priority = 0;
	openflow_flowtable_entry_type *current_entry = NULL;
	for (i = 0; i < OPENFLOW_MAX_FLOWTABLE_ENTRIES; i++)
	{
		if (flowtable->entries[i].active)
		{
			openflow_flowtable_entry_type *entry = &flowtable->entries[i];
			openflow_flowtable_match_type *match = &entry->match;
			uint8_t is_match = flowtable_match_packet(match, packet);
			if (is_match)
			{
				// Exact match
				if (match->wildcards == 0)
				{
					return entry;
				}
				// Possible wildcard match, but wait to see if there are any
				// other wildcard matches with higher priority
				else if (entry->priority >= current_priority)
				{
					current_entry = entry;
					current_priority = entry->priority;
				}
			}
		}
	}

	return current_entry;
}

void flowtable_init(void)
{
	flowtable = malloc(sizeof(openflow_flowtable_type));
}

void flowtable_handle_packet(gpacket_t *packet)
{
	verbose(2, "[flowtable_handle_packet]:: Received packet, dropping...");
	free(in_pkt);
}
