from Core.Device import *

class Switch(Device):
    type="Switch"
    
    def __init__(self):
        Device.__init__(self)

        self.setProperty("mask", "")
        self.setProperty("subnet", "")
        self.setProperty("link_subnet", "0")
	self.setProperty("port", "")
	self.setProperty("monitor", "")

    def addEdge(self, edge):
        Device.addEdge(self, edge)

        node = edge.getOtherDevice(self)
        if node.type == "UML":
            node.addInterface(self)

    def removeEdge(self, edge):
        Device.removeEdge(self, edge)

        node = edge.getOtherDevice(self)
        if node.type == "UML":
            node.removeInterface(self)
    
    ##
    # Add a new connection to the switch
    # @param c the new connection to add 
    def add_connection(self, c):
	self.connection.append(c)
	s_d=c.get_start_device()
	e_d=c.get_end_device()
	#print "link ", s_d, "with", e_d
	#print "1:", find(s_d,"Subnet"), "2:", find(e_d,"Subnet") 

	# check if the device it links to is subnet
	if find(s_d,"Subnet") != -1 or find(e_d,"Subnet") != -1 :
	    self.link_subnet=1

    ##
    # Delete a specified connection of the switch
    # @param c the connection to delete 
    def delete_connection(self, c):
	self.connection.remove(c)
	s_d=c.get_start_device()
	e_d=c.get_end_device()

	# check if the device it links to is subnet
	if find(s_d,"Subnet") != -1 or find(e_d,"Subnet") != -1 :
	    self.link_subnet=0

    ## 
    # Return the number of connected subnet of this switch. Currently, only one is allowed
    # @return an integer
    def hasOne(self):
	return self.link_subnet

    def getTarget(self, node):
        for con in self.edges():
            other = con.getOtherDevice(self)
            if other != node and other.type == "Subnet":
                return other.getTarget(self)
