/**
 * openflow_pkt_proc.h - OpenFlow packet processing
 */

#ifndef __OPENFLOW_PKT_PROC_H_
#define __OPENFLOW_PKT_PROC_H_

#include "grouter.h"
#include "packetcore.h"

/**
 * Initializes the OpenFlow packet processor.
 */
void openflow_pkt_proc_init(void);

/**
 * Processes the specified packet using the OpenFlow packet processor.
 *
 * @param packet       The packet to be handled.
 * @param packet_core  The grouter packet core.
 */
void openflow_pkt_proc_handle_packet(gpacket_t *packet,
	pktcore_t *packet_core);

/**
 * Forwards the specified packet to the specified port.
 *
 * @param packet            The specified packet.
 * @param openflow_port_num The OpenFlow port number to send the packet to.
 * @param packet_core       The GNET packet core.
 * @param flood             Whether or not the packet is being sent as part of
 *                          a flood operation.
 */
void openflow_pkt_proc_forward_packet_to_port(gpacket_t *packet,
	uint16_t openflow_port_num, pktcore_t *packet_core, uint8_t flood);

#endif // ifndef __OPENFLOW_PKT_PROC_H_
