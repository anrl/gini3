#ifndef __OPENFLOW_PORTS_H_
#define __OPENFLOW_PORTS_H_

#include "gnet.h"
#include "openflow.h"

// Must be less than or equal to OFPP_MAX
#define OPENFLOW_MAX_PHYSICAL_PORTS		MAX_INTERFACES

typedef struct ofp_phy_port		ofp_phy_port;

ofp_phy_port *openflow_get_physical_port(uint16_t port_num);
uint16_t openflow_get_openflow_port_num(uint16_t gnet_port_num);
uint16_t openflow_get_gnet_port_num(uint16_t openflow_port_num);

#endif // ifndef __OPENFLOW_PORTS_H_
