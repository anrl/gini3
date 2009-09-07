from Core.Connection import *
from Core.Device import *
from Core.Interfaceable import Interfaceable

##
# Class: the Subnet
class Subnet(Device):
    type="Subnet"    

    def __init__(self):
        Device.__init__(self)
                
	self.num_interface=0
	self.setProperty("subnet", "")
	self.setProperty("mask", "")
	self.setProperty("bits", "")

    def addEdge(self, edge):
        Device.addEdge(self, edge)

        if len(self.edgeList) == 2:
            node1 = self.edgeList[0].getOtherDevice(self)
            node2 = self.edgeList[1].getOtherDevice(self)
            if isinstance(node1, Interfaceable):
                node1.addInterface(node2)
            if isinstance(node2, Interfaceable):
                node2.addInterface(node1)

    def removeEdge(self, edge):
        if len(self.edgeList) == 2:
            node1 = self.edgeList[0].getOtherDevice(self)
            node2 = self.edgeList[1].getOtherDevice(self)
            if isinstance(node1, Interfaceable):
                node1.removeInterface(node2)
            if isinstance(node2, Interfaceable):
                node2.removeInterface(node1)
            
        Device.removeEdge(self, edge)

    ##
    # Get the subnet of this subnet
    # @return the required property, subnet
    def get_subnet(self):
	return self.getProperty("subnet")

    ##
    # Get the subnet mask (overriden from Device)
    # @return the required property, mask
    def get_mask(self):
	return self.getProperty("mask")
    
    ##
    # Get the other connection of the Subnet given one
    # @param con the given connection
    # @return o_con the other connection of the device. 
    #         If there is no other connection, return None 
    def get_other_connection(self, con):
        for o_con in self.connection:
	    if o_con != con:
		return o_con
	return None

    def getTarget(self, node):
        for con in self.edges():
            other = con.getOtherDevice(self)
            if other != node:
                return other

    ##
    # The bolloon help info for this subnet
    def balloon_help(self):
	s="Screen Name: "+self.name
	s=s+"\n\nSubnet\t: "+self.req_properties["subnet"]
	s=s+"\nMask\t: "+self.req_properties["mask"]
	return s
