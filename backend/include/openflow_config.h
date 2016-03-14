/**
 * openflow_config.h - OpenFlow switch configuration
 */

#ifndef __OPENFLOW_CONFIG_H_
#define __OPENFLOW_CONFIG_H_

#include "openflow.h"
#include "openflow_ctrl_iface.h"
#include "gnet.h"

// OpenFlow constants
#define OPENFLOW_MAX_PHYSICAL_PORTS   MAX_INTERFACES

/**
 * Converts the specified GNET port number to an OpenFlow port number.
 *
 * @param gnet_port_num The GNET port number.
 *
 * @return The OpenFlow port number.
 */
uint16_t openflow_config_gnet_to_of_port_num(uint16_t gnet_port_num);

/**
 * Converts the specified OpenFlow port number to an GNET port number.
 *
 * @param gnet_port_num The OpenFlow port number.
 *
 * @return The GNET port number.
 */
uint16_t openflow_config_of_to_gnet_port_num(uint16_t openflow_port_num);

/**
 * Sets the OpenFlow physical port structs to their default values. These
 * values change depending on the current state of the GNET interfaces.
 */
void openflow_config_set_phy_port_defaults();

/**
 * Updates the specified OpenFlow physical port struct to match the state of
 * the corresponding GNET interface.
 *
 * @param The OpenFlow port number corresponing to the port to update.
 */
void openflow_config_update_phy_port(int32_t openflow_port_num);

/**
 * Gets the OpenFlow physical port struct coresponding to the specified
 * OpenFlow port number.
 *
 * @param openflow_port_num The specified OpenFlow port number.
 *
 * @return The OpenFlow physical port struct corresponding to the specified
 *         port number.
 */
ofp_phy_port *openflow_config_get_phy_port(uint16_t openflow_port_num);

/**
 * Gets the current switch configuration flags in network byte order.
 *
 * @return The current switch configuration flags.
 */
uint16_t openflow_config_get_switch_config_flags();

/**
 * Sets the current switch configuration flags in network byte order.
 *
 * @param flags The switch configuration flags to set.
 */
void openflow_config_set_switch_config_flags(uint16_t flags);

/**
 * Gets the current miss send length value in network byte order.
 *
 * @return The current miss send length value.
 */
uint16_t openflow_config_get_miss_send_len();

/**
 * Sets the current miss send length value in network byte order.
 *
 * @param len The miss send length value to set.
 */
void openflow_config_set_miss_send_len(uint16_t len);

/**
 * Gets the OpenFlow switch features.
 *
 * @return The OpenFlow switch features.
 */
ofp_switch_features openflow_config_get_switch_features();

/**
 * Determines if the switch is currently operating in emergency mode.
 *
 * @return 1 if the switch is currently operating in emergency mode, 0
 *         otherwise.
 */
uint8_t openflow_config_is_emergency();

#endif // ifndef __OPENFLOW_CONFIG_H_
