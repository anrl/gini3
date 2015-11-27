#ifndef __OPENFLOW_CONFIG_H_
#define __OPENFLOW_CONFIG_H_

#include "openflow.h"
#include "gnet.h"

// Must be less than or equal to OFPP_MAX
#define OPENFLOW_MAX_PHYSICAL_PORTS MAX_INTERFACES

typedef struct ofp_switch_features ofp_switch_features;
typedef struct ofp_phy_port	ofp_phy_port;

ofp_phy_port *openflow_get_physical_port(uint16_t port_num);
uint16_t openflow_get_openflow_port_num(uint16_t gnet_port_num);
uint16_t openflow_get_gnet_port_num(uint16_t openflow_port_num);

uint8_t openflow_config_is_emergency();

uint16_t openflow_config_get_flags();

#endif // ifndef __OPENFLOW_CONFIG_H_
