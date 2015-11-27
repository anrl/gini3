/**
 * openflow_config.c - OpenFlow switch configuration
 *
 * Author: Michael Kourlas
 * Date: November 27, 2015
 */

#include "gnet.h"
#include "message.h"
#include "openflow.h"
#include "openflow_ctrl_iface.h"
#include "packetcore.h"
#include "simplequeue.h"

#include "openflow_config.h"

// OpenFlow switch configuration
static uint16_t switch_config_flags;
static uint16_t miss_send_len;

// OpenFlow physical port structs
static ofp_phy_port phy_ports[OPENFLOW_MAX_PHYSICAL_PORTS];

/**
 * Converts the specified GNET port number to an OpenFlow port number.
 *
 * @param gnet_port_num The GNET port number.
 *
 * @return The OpenFlow port number.
 */
uint16_t openflow_config_gnet_to_of_port_num(uint16_t gnet_port_num)
{
	return gnet_port_num + 1;
}

/**
 * Converts the specified OpenFlow port number to an GNET port number.
 *
 * @param gnet_port_num The OpenFlow port number.
 *
 * @return The GNET port number.
 */
uint16_t openflow_config_of_to_gnet_port_num(uint16_t openflow_port_num)
{
	return openflow_port_num - 1;
}

/**
 * Sets the OpenFlow physical port structs to their default values. These
 * values change depending on the current state of the GNET interfaces.
 */
void openflow_config_set_phy_port_defaults()
{
	uint32_t i;
	for (i = 0; i < OPENFLOW_MAX_PHYSICAL_PORTS; i++)
	{
		phy_ports[i].port_no = htons(openflow_config_gnet_to_of_port_num(i));
		sprintf(phy_ports[i].name, "Port %d",
			openflow_config_gnet_to_of_port_num(i));
		phy_ports[i].config = htonl(0);
		phy_ports[i].state = htonl(0);
		phy_ports[i].curr = htonl(0);
		phy_ports[i].advertised = htonl(0);
		phy_ports[i].supported = htonl(0);
		phy_ports[i].peer = htonl(0);

		interface_t *iface = findInterface(i);
		if (iface == NULL)
		{
			memset(phy_ports[i].hw_addr, 0, OFP_ETH_ALEN);
			phy_ports[i].state |= htonl(OFPPS_LINK_DOWN);
		}
		else
		{
			COPY_MAC(phy_ports[i].hw_addr, iface->mac_addr);
		}
	}
}

/**
 * Updates the specified OpenFlow physical port struct to match the state of
 * the corresponding GNET interface.
 *
 * @param The OpenFlow port number corresponing to the port to update.
 */
void openflow_config_update_phy_port(int32_t openflow_port_num)
{
	interface_t *iface = findInterface(openflow_port_num - 1);
	if (iface == NULL)
	{
		memset(phy_ports[openflow_port_num - 1].hw_addr, 0, OFP_ETH_ALEN);
		phy_ports[openflow_port_num - 1].state |= htonl(OFPPS_LINK_DOWN);
	}
	else
	{
		COPY_MAC(phy_ports[openflow_port_num - 1].hw_addr, iface->mac_addr);
	}

	// TODO: Send port update message.
}

/**
 * Gets the OpenFlow physical port struct coresponding to the specified
 * OpenFlow port number.
 *
 * @param openflow_port_num The specified OpenFlow port number.
 *
 * @return The OpenFlow physical port struct corresponding to the specified
 *         port number.
 */
ofp_phy_port *openflow_config_get_phy_port(uint16_t openflow_port_num)
{
	if (openflow_port_num >= 1 &&
		openflow_port_num <= OPENFLOW_MAX_PHYSICAL_PORTS)
	{
		return &phy_ports[openflow_config_of_to_gnet_port_num(openflow_port_num)];
	}
	else
	{
		return NULL;
	}
}

/**
 * Gets the current switch configuration flags in network byte order.
 *
 * @return The current switch configuration flags.
 */
uint16_t openflow_config_get_switch_config_flags()
{
    return switch_config_flags;
}

/**
 * Gets the current miss send length value in network byte order.
 *
 * @return The current miss send length value.
 */
uint16_t openflow_config_get_miss_send_len()
{
    return miss_send_len;
}

/**
 * Gets the OpenFlow switch features.
 *
 * @return The OpenFlow switch features.
 */
ofp_switch_features openflow_config_get_switch_features()
{
    ofp_switch_features switch_features;

	// TODO: Fix datapath ID.
	switch_features.datapath_id = 0;
	switch_features.n_buffers = htonl(0);
	switch_features.n_tables = 1;
	switch_features.capabilities = htonl(OFPC_FLOW_STATS | OFPC_TABLE_STATS |
        OFPC_PORT_STATS | OFPC_ARP_MATCH_IP);
	switch_features.actions = htonl(1 << OFPAT_OUTPUT |
        1 << OFPAT_SET_VLAN_VID | 1 << OFPAT_SET_VLAN_PCP |
        1 << OFPAT_STRIP_VLAN | 1 << OFPAT_SET_DL_SRC |
		1 << OFPAT_SET_DL_DST | 1 << OFPAT_SET_NW_SRC |
        1 << OFPAT_SET_NW_DST | 1 << OFPAT_SET_NW_TOS |
        1 << OFPAT_SET_TP_SRC | 1 << OFPAT_SET_TP_DST);

    return switch_features;
}

/**
 * Determines if the switch is currently operating in emergency mode.
 *
 * @return 1 if the switch is currently operating in emergency mode, 0
 *         otherwise.
 */
uint8_t openflow_config_is_emergency()
{
	return openflow_ctrl_iface_get_conn_state();
}
