from Connection import *
from Tag import *
from Interface import *
from Device import *
import pdb

##
# Class: a module to compute routing table
class Routing:

    ##
    # Constructor: Initial the routing module
    # @param devices all devices in the network topology
    # @param canvas the canvas that contians all devices
    def __init__(self, devices, canvas):
	self.device_list=devices
	self.canvas=canvas


    ##
    # Get the adjacent routers for specified device on a given connection
    # @param myself the device to search for adjacent routers
    # @param con the connection that leads to the adjacent routers
    # @param device the device the start search for adjacent routers
    # @param inter the interface that contains the given connection
    def gateway(self, myself, con, device, inter):

	#find out the device at the other side of the connection
	other_device=self.device_list[self.canvas.find_withtag(con.get_other_device(device.get_name()))[0]]
	#pdb.set_trace()
	

	if other_device.type == "Router" or other_device.type == "Wireless_access_point":
	    #pdb.set_trace()
	    myself.add_adjacent_router(con, other_device, inter)
	    #print "I am ",myself
	    #print "my neighbours are: ",myself.get_adjacent_router()

	elif other_device.type == "UML" or other_device.type == "Mobile":
	    pass
	    
	else:

	    # follow the connection to find another device
	    connection_list=other_device.get_connection()
	    for c in connection_list:
		if con != c:
		    self.gateway(myself, c, other_device, inter)


    ##
    # Find adjacent subnet connected with this device on a given connection
    # @param myself the device to search for adjacent subnet
    # @param con the connection that leads to the adjacent routers
    # @param ip the ip address of the interface that contains the given connection    
    def subnet(self, myself, con, ip):

	#find out the device at the other side of the connection
	other_device=self.device_list[self.canvas.find_withtag(con.get_other_device(myself.get_name()))[0]]
	#pdb.set_trace()
	

	if other_device.type == "Subnet":
	    myself.add_adjacent_subnet(other_device, ip)
	    # print "I am ",myself
	    # print "my subnets are: ",myself.get_adjacent_subnet()
	elif other_device.type == "Wireless_access_point":
	    myself.add_adjacent_subnet(other_device.get_wireless_interface(), ip)
	#elif other_device.type == "Switch":
	#    myself.add_adjacent_subnet(other_device, ip)
	    


