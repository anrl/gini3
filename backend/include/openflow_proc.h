/**
 * openflow_proc.h - OpenFlow packet processing
 *
 * Author: Michael Kourlas
 * Date: November 27, 2015
 */

#ifndef __OPENFLOW_PROC_H_
#define __OPENFLOW_PROC_H_

#include "grouter.h"
#include "packetcore.h"

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
	uint16_t openflow_port_num, pktcore_t *packet_core, uint8_t flood);

#endif // ifndef __OPENFLOW_PROC_H_
