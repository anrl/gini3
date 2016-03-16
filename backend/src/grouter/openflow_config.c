/**
 * openflow_config.c - OpenFlow switch configuration
 */

#include "openflow_config.h"

#include <arpa/inet.h>
#include <stdint.h>
#include <string.h>

#include "gnet.h"
#include "grouter.h"
#include "openflow.h"
#include "openflow_ctrl_iface.h"
#include "openflow_defs.h"

// OpenFlow switch configuration
static uint16_t switch_config_flags;

// OpenFlow physical port structs
static ofp_phy_port phy_ports[OPENFLOW_MAX_PHYSICAL_PORTS];
static ofp_port_stats phy_port_stats[OPENFLOW_MAX_PHYSICAL_PORTS];

/**
 * Converts the specified GNET port number to an OpenFlow port number.
 *
 * @param gnet_port_num The GNET port number.
 *
 * @return The corresponding OpenFlow port number.
 */
uint16_t openflow_config_get_of_port_num(uint16_t gnet_port_num)
{
	return gnet_port_num + 1;
}

/**
 * Converts the specified OpenFlow port number to an GNET port number.
 *
 * @param gnet_port_num The OpenFlow port number.
 *
 * @return The corresponding GNET port number.
 */
uint16_t openflow_config_get_gnet_port_num(uint16_t openflow_port_num)
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
		phy_ports[i].port_no = htons(
            openflow_config_get_of_port_num(i));
		sprintf(phy_ports[i].name, "Port %d",
			openflow_config_get_of_port_num(i));
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
 * Updates the specified OpenFlow physical port struct to match the state
 * of the corresponding GNET interface.
 *
 * @param The OpenFlow port number corresponding to the port to update.
 */
void openflow_config_update_phy_port(int32_t openflow_port_num)
{
	int32_t gnet_port_num = openflow_config_get_gnet_port_num(
			openflow_port_num);

	interface_t *iface = findInterface(gnet_port_num);
	if (iface == NULL)
	{
		memset(phy_ports[gnet_port_num].hw_addr, 0, OFP_ETH_ALEN);
		phy_ports[gnet_port_num].state |= htonl(OFPPS_LINK_DOWN);
	}
	else
	{
		COPY_MAC(phy_ports[gnet_port_num].hw_addr,
            iface->mac_addr);
	}

	openflow_ctrl_iface_send_port_status(&phy_ports[gnet_port_num],
			OFPPR_MODIFY);
}

/**
 * Gets the OpenFlow physical port struct corresponding to the specified
 * OpenFlow port number.
 *
 * @param openflow_port_num The specified OpenFlow port number.
 *
 * @return The OpenFlow physical port struct corresponding to the
 *         specified port number.
 */
ofp_phy_port *openflow_config_get_phy_port(uint16_t openflow_port_num)
{
	if (openflow_port_num >= 1 &&
		openflow_port_num <= OPENFLOW_MAX_PHYSICAL_PORTS)
	{
		return &phy_ports[openflow_config_get_gnet_port_num(
            openflow_port_num)];
	}
	else
	{
		return NULL;
	}
}

/**
 * Gets the OpenFlow ofp_port_stats struct corresponding to the specified
 * OpenFlow port number.
 *
 * @param openflow_port_num The specified OpenFlow port number.
 *
 * @return The OpenFlow ofp_port_stats struct corresponding to the
 *         specified port number.
 */
ofp_port_stats *openflow_config_get_port_stats(uint16_t openflow_port_num)
{
	if (openflow_port_num >= 1 &&
		openflow_port_num <= OPENFLOW_MAX_PHYSICAL_PORTS)
	{
		return &phy_port_stats[openflow_config_get_gnet_port_num(
            openflow_port_num)];
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
 * Sets the current switch configuration flags in network byte order.
 *
 * @param flags The switch configuration flags to set.
 */
void openflow_config_set_switch_config_flags(uint16_t flags)
{
    switch_config_flags = flags;
}

/**
 * Gets the OpenFlow switch features.
 *
 * @return The OpenFlow switch features.
 */
ofp_switch_features openflow_config_get_switch_features()
{
    ofp_switch_features switch_features;

	switch_features.datapath_id = 0;
	uint32_t i;
	for (i = 0; i < MAX_INTERFACES; i++)
	{
		interface_t *iface = findInterface(i);
		if (iface != NULL)
		{
			COPY_MAC(((uint8_t * )&switch_features.datapath_id) + 2,
			        iface->mac_addr);
			break;
		}
	}

	switch_features.n_buffers = htonl(0);
	switch_features.n_tables = 1;
	switch_features.capabilities = htonl(OFPC_FLOW_STATS |
        OFPC_TABLE_STATS | OFPC_PORT_STATS | OFPC_ARP_MATCH_IP);
	switch_features.actions = htonl(1 << OFPAT_OUTPUT |
        1 << OFPAT_SET_VLAN_VID | 1 << OFPAT_SET_VLAN_PCP |
        1 << OFPAT_STRIP_VLAN | 1 << OFPAT_SET_DL_SRC |
		1 << OFPAT_SET_DL_DST | 1 << OFPAT_SET_NW_SRC |
        1 << OFPAT_SET_NW_DST | 1 << OFPAT_SET_NW_TOS |
        1 << OFPAT_SET_TP_SRC | 1 << OFPAT_SET_TP_DST);

    return switch_features;
}
