from Routing_Table_Entry import * 
from Interface import *

##
# Class: the wireless network interface 
class Wireless_Interface(Interface):
    type="wireless"

    ##
    # Constructor. Initial an wireless interface
    # @param con the connection that links with this interface
    # @param num the serial number of interface 	
    def __init__(self, con, num):

	self.id=num

	#required properties for an interface
	self.req_properties={}
	self.req_properties["mac"]=""
	self.req_properties["ipv4"]=""
	self.req_properties["subnet"]=""

	#optional properties for an interface
	self.opt_properties={}
	self.opt_properties["host_name"]=""

	self.con=con			    # the connection in this interface
	self.num_entry=0                    # the number of routing table entry
	self.mobile_list=[]	            # the list of wireless devices that connect to this wireless interface
	self.routing_table=[]		    # initialize routing table
	self.mask=""			    # the mask for this subnet
	self.gateway="0.0.0.0"		    # the gateway for this interface
	self.next_entry_num=0

    ##
    # Get the subnet of this interface
    # @return the subnet of this interface
    def get_subnet(self):
	return self.req_properties["subnet"]

    ## Add a wireless connection into the wireless interface
    # @param c the given wireless connection
    def add_connection(self, c):
	self.mobile_list.append(c)

    ## 
    # Delete a wireless connection
    # @param the given wireless connection to be deleted
    def del_connection(self, c):
	self.mobile_list.remove(c)

    ## 
    # Get all wireless connections on this wireless interface
    def get_shared_connections(self):
	return self.mobile_list

