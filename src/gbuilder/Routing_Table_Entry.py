##
# Class: the routing table entry 
class Routing_Table_Entry:

    ##
    # Constructor: initial an routing entry
    # @param mask the mask of the entry
    # @param gateway the gateway of the entry
    def __init__(self, mask, gateway):
	self.mask=mask
	self.gateway=gateway
	self.nexthop=""
	self.ip=""

    ##
    # Set the mask with a new value
    # @param mask the new mask to set
    def set_mask(self, mask):
	self.mask=mask

    ##
    # Set the gateway with a new value
    # @param gw the new gateway to set    
    def set_gateway(self, gw):
	self.gateway=gw

    ##
    # Set the ip address with a new value
    # @param ip the new ip address to set
    def set_ip(self, ip):
	self.ip=ip

    ##
    # Get the mask of the entry
    # @return the mask of the entry
    def get_mask(self):
	return self.mask

    ##
    # Get the gateway of the entry
    # @return the gateway of the entry
    def get_gateway(self):
	return self.gateway

    ##
    # Get the ip address of the entry
    # @return the ip address of the entry
    def get_ip(self):
	return self.ip

    ##
    # Set the nexthop with a new value
    # @param gw the new nexthop to set
    def set_nexthop(self, gw):
	self.nexthop=gw

    ##
    # Get the nexthop of the entry
    # @return the nexthop of the entry
    def get_nexthop(self):
	return self.gateway
