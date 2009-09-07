from Routing_Table_Entry import * 

##
# Class: the network interface 
class Interface:
    type="wire"
	
    ##
    # Constructor. Initial an interface
    # @param con the connection that links with this interface
    # @param num the serial number of interface 
    def __init__(self, con, num):

	self.id=num

	#required properties for an interface
	self.req_properties={}
	self.req_properties["mac"]=""
	self.req_properties["ipv4"]=""

	#optional properties for an interface
	self.opt_properties={}
	self.opt_properties["host_name"]=""

	self.con=con			    # the connection in this interface
	self.num_entry=0                    # the number of routing table entry
	self.routing_table=[]		    # initialize routing table
	self.subnet=""			    # the subnet ip of this subnet
	self.mask=""			    # the mask for this subnet
	self.gateway=""			    # the gateway for this interface
	self.next_entry_num=0

    ##
    # Get the required property list
    # @return all required properties 
    def get_req_properties(self):
	return self.req_properties


    ##
    # Get the optional property list
    # @return all optional properties
    def get_opt_properties(self):
	return self.opt_properties

    ##
    # Get the id of the interface
    # @return self.id the id of the interface
    def get_id(self):
	return self.id

    ##
    # Set the subnet property
    # @param subnet the subnet to set
    def set_subnet(self, subnet):
	self.subnet=subnet

    ##
    # Get the subnet of this interface
    # @return self.subnet the subnet of this interface
    def get_subnet(self):
	return self.subnet

    ##
    # Set the mask property
    # @param mask the mask to set
    def set_mask(self, mask):
	self.mask=mask

	#update all rounting entry in this interface
	for entry in self.routing_table:
	    entry.set_mask(mask)

    ##
    # Get the mask of this interface
    # @return self.mask the mask of this interface
    def get_mask(self):
	return self.mask

    ##
    # Set the gateway property
    # @param gateway the gateway to set
    # @param auto the flag for auto computing routing table
    #        If auto==1, delete all existing routing table entries
    def set_gateway(self, gateway, auto=0):
	self.gateway=gateway

	#if the gateway is set by auto computing feature
	#delete existing routing table entries, then create one
	if auto==1:
	    self.routing_table=[]
	    self.num_entry=0
	self.add_entry()


    ##
    # Set the ip address property
    # @param ip the ip address to set
    def set_ip(self, ip):
	
	#update all rounting entry in this interface
	for entry in self.routing_table:
	    entry.set_ip(ip)

    ##
    # Get the ip address of this interface
    # @return self.ip the ip address of this interface
    def get_ip(self):
	return self.req_properties["ipv4"]

    ## 
    # Get the index of next routing entry
    # @return self.next_entry_num the index of entry if add a new one
    def get_next_entry_num(self):
	return self.next_entry_num

    ##
    # Set the index of next routing entry
    # @param num the number to set
    def set_next_entry_num(self, num):
	self.next_entry_num=num

    ##
    # Get the index of next routing entry
    # @return self.num_entry the next routing entry
    def get_num_entry(self):
	return self.num_entry

    ##
    # Get the connection in this interface
    # @return self.con the connection in this interface
    def get_connection(self):
	return self.con

    ##
    # Add one more routing entry
    def add_entry(self):
	new_entry=Routing_Table_Entry(self.mask, self.gateway)
	self.routing_table.append(new_entry)
	self.num_entry+=1
	self.next_entry_num+=1
	return new_entry

    ##
    # Delete given routing entry
    # @param e the entry to delete
    def delete_entry(self, e):
	self.routing_table.remove(e)
	self.num_entry-=1

    ##
    # Clear all existing eouting entries
    def empty_routing_entry(self):
	self.routing_table=[]
	self.num_entry=0
	self.next_entry_num=0

    ##
    # Get the entire routing table of this interface
    # @return self.routing_table the routing table of this interface
    def get_table(self):
	return self.routing_table


