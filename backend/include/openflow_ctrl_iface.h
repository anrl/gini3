/**
 * openflow_ctrl_iface.h - OpenFlow controller interface
 *
 * Author: Michael Kourlas
 * Date: November 26, 2015
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

pthread_t openflow_ctrl_iface_init(int port_num);

uint8_t openflow_ctrl_iface_get_conn_state();

void openflow_ctrl_iface_send_to_ctrl(gpacket_t *packet);

void openflow_ctrl_iface_parse_packet(gpacket_t *packet);

#endif // ifndef __OPENFLOW_CTRL_IFACE_H_
