/**
 * openflow_ctrl_iface.h - OpenFlow controller-switch interface
 */

#ifndef __OPENFLOW_CTRL_IFACE_H_
#define __OPENFLOW_CTRL_IFACE_H_

#include <stdint.h>

#include "message.h"

#define OPENFLOW_CTRL_IFACE_SEND_TIMEOUT       10
#define OPENFLOW_ERROR_MSG_SIZE                12

#define OPENFLOW_CTRL_IFACE_ERR_UNKNOWN        ((int32_t)-1)
#define OPENFLOW_CTRL_IFACE_ERR_CONN_CLOSED    ((int32_t)-2)
#define OPENFLOW_CTRL_IFACE_ERR_SEND_TIMEOUT   ((int32_t)-3)
#define OPENFLOW_CTRL_IFACE_ERR_OPENFLOW       ((int32_t)-3)

// OpenFlow struct typedefs
typedef struct ofp_header ofp_header;
typedef struct ofp_hello ofp_hello;
typedef struct ofp_error_msg ofp_error_msg;
typedef struct ofp_switch_features ofp_switch_features;
typedef struct ofp_phy_port	ofp_phy_port;
typedef struct ofp_switch_config ofp_switch_config;
typedef struct ofp_flow_mod ofp_flow_mod;

/**
 * Gets the current controller connection state.
 *
 * @return The current controller connection state.
 */
uint8_t openflow_ctrl_iface_get_conn_state();

/**
 * Parses a packet as though it came from the OpenFlow controller.
 *
 * @param packet The packet to parse.
 */
void openflow_ctrl_iface_parse_packet(gpacket_t *packet);

/**
 * Sends a packet to the OpenFlow controller via a packet in message.
 *
 * @param packet The packet to send the OpenFlow controller.
 */
void openflow_ctrl_iface_send_to_ctrl(gpacket_t *packet);

/**
 * OpenFlow controller thread. Connects to controller and passes incoming
 * packets to handlers.
 *
 * @param pn Pointer to the controller TCP port number.
 */
void openflow_ctrl_iface(void *pn);

/**
 * Initializes the OpenFlow controller-switch interface.
 *
 * @param port_num The TCP port number of the OpenFlow controller.
 *
 * @return The thread associated with the controller interface.
 */
pthread_t openflow_ctrl_iface_init(int32_t port_num);

#endif // ifndef __OPENFLOW_CTRL_IFACE_H_
