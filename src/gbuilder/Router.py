from Connection import *
from Tag import *
from Interface import *
from Device import *
import pdb

## 
# Class: the router device
class Router(Device):
    type="Router"    

    ##
    # Constructor: Initial a router device
    # @param x the x axis of the device on the canvas
    # @param y the y axis of the device on the canvas
    # @param r_num the serial number of the router
    # @param t_num the serial number of the name tag  
    def __init__(self, x, y, r_num, t_num):
	self.x=x
	self.y=y
	self.num_interface=0
	self.interface=[]
	self.connection=[]
	self.con_int={}                         # the connection and interface pair
	self.num=r_num
	self.relative_y=-30  			# the relative y position of name to the graph
	self.next_interface_number=0
	self.adjacent_subnet_list=[]
	self.adjacent_router_list=[]

	#the default name is composed by the type of the device and a serial number
	self.name=self.type+"_"+str(r_num)

	#create a name tag
	self.tag=Tag(x, y, self.relative_y, t_num, self.name)
 
    ##
    # Add a new connection to the router
    # @param c the new connection to add 
    def add_connection(self, c):
	self.connection.append(c)
	new_interface=self.add_interface(c)
	self.interface.append(new_interface)
	self.con_int[c]=new_interface

    ##
    # Delete a specified connection of the router
    # @param c the connection to delete  
    def delete_connection(self, c):
	self.connection.remove(c)
	self.interface.remove(self.con_int[c])
	del self.con_int[c]

    ##
    # Add a new interface to the router
    # @param con the connection on this interface
    def add_interface(self, con=None):
	self.next_interface_number+=1
	return Interface(con, self.next_interface_number)

    ##
    # Get all the interfaces of this router
    # @return a list of interfaces of this router
    def get_interface(self):
	return self.interface

    ##
    # Set the network mask and subnet for a given interface
    # @param con the connection in the interface
    # @param subnet the subnet to set
    # @param mask the mask to set
    def set_mask(self, con, subnet, mask):
	
	#find out which interface connects with the con
	for inter in self.interface:
	    if con == inter.get_connection():
		inter.set_subnet(subnet)
		inter.set_mask(mask)
		return

    ##
    # Get the subnet of a give connection
    # @param con the given connection
    # @return the subnet the connection belongs to
    def get_subnet(self, con):

	#find out which interface connects with the con
	for inter in self.interface:
	    if con == inter.get_connection():
		inter.get_subnet(subnet)

    ##
    # Clear the adjacent router list and adjacent subnet list
    def empty_adjacent_list(self):
	self.adjacent_router_list=[]
	self.adjacent_subnet_list=[]

    ##
    # Clear all routing tables for all interfaces of this router
    def empty_routing_entry(self):
	for inter in self.interface:
	    inter.empty_routing_entry()

    ##
    # Add an adjacent router to the adjacent router list
    # @param con the connection to start to find adjacent router
    # @param other_device the adjacent router
    # @param gateway the gateway to reach the adjacent router
    def add_adjacent_router(self, con, other_device, gateway):

	#find out which interface connects with the con
	for inter in other_device.get_interface():
	    if con == inter.get_connection():
		self.adjacent_router_list.append([gateway, inter.get_ip(), other_device])

    ##
    # Add one more adjacent router to the list
    # @param othet_device the adhacent router to be added
    # @param ip the op address of the interface that leads to the added router
    def add_adjacent_subnet(self, other_device, ip):
	self.adjacent_subnet_list.append([other_device, ip])

    ##
    # Get the adjacent routers
    # @return the list of all adjacent routers
    def get_adjacent_router(self):
	return self.adjacent_router_list

    ##
    # Get the adjacent subnet
    # @return the list of all adjacent subnets
    def get_adjacent_subnet(self):
	return self.adjacent_subnet_list

    ##
    # Computing routing table entry
    # @param subnet add an routing entry that leads to given subnet
    def add_routing_entry(self, subnet):
	
	#find out if this subnet is one of the adjacent. If yes, add routing entry with nexthop=0.0.0.0
	#Otherwise, perform a search to find which interface leads to it
	inter_ip=self.has_subnet(subnet)
	if  inter_ip != None:

            #find out which interface connects to the subnet
	    for interface in self.interface:
		if inter_ip == interface.get_ip():
		    new_entry=interface.add_entry()
		    new_entry.set_gateway("0.0.0.0")
		    new_entry.set_ip(subnet)
		    return

	else:
	    (interface, nexthop)=self.search_subnet(subnet)
	    if interface and nexthop:
		new_entry=interface.add_entry()
	        new_entry.set_gateway(nexthop)
	    	new_entry.set_ip(subnet)
	
	

    ##
    # Search the specified subnet in the whole network. 
    # Precondition: the adjacent_router_list and adjacent_subnet_list are already filled in
    # @param subnet the subnet to search 
    def search_subnet(self, subnet):
	#pdb.set_trace()
	router_list=self.adjacent_router_list[:]

	#save all found routers in the list, so that we should not visit a router twice
	found_list=[]
	for r in router_list:
	    found_list.append(r[2])

	while len(router_list)>0:
	    theOne=router_list.pop(0)
	    #print "this one is: ", theOne.get_name()
	    if theOne[2].has_subnet(subnet) != None:	
		return (theOne[0], theOne[1])
	    else:
		
		# add its adjacent router list to the list
		for inter,nexthop,router in theOne[2].get_adjacent_router():

		    # check if the router is already visited or in the to be visited list
		    if self.first_found(router, found_list): 
		        newOne=[theOne[0], theOne[1], router]
		        router_list.append(newOne)
			found_list.append(router)

	return (None, None)
	
    ##
    # Check if the specified subnet is in the adjacent list
    # @param subnet the given subnet to search in the adjacent subnet list
    # @return the ip address that leads to this subnet;
    #         Or return None if the subnet is not in the adjacent subnet list 
    def has_subnet(self, subnet):
	#pdb.set_trace()
	for sub,inter_ip in self.adjacent_subnet_list:
	    if sub.get_subnet() == subnet:  
		return inter_ip 
	return None 

    ##
    # Check if the specified router is in the found router list
    # @param router the router to verify if it is already found
    # @param found_list the list of all found routers
    # @return 0 if it is already found;
    #         1 if this is the first time that encounter this router 
    def first_found(self, router, found_list):
	if router in found_list:
	    return 0
	else:
            return 1

    ##
    # The bolloon help info for this router			
    def balloon_help(self):
	s="Screen Name: "+self.name
	for inter in self.interface:
	    s=s+"\n\nInterface "+str(inter.get_id())+": "
	    
	    # find out which device connects with this interface
	    con=inter.get_connection()
	    if self.name == con.get_start_device():
		s=s+"(Connect to "+con.get_end_device()+")"
	    else:
		s=s+"(Connect to "+con.get_start_device()+")"

	    s=s+"\n  IP\t: "+inter.req_properties["ipv4"]
	    s=s+"\n  MAC\t: "+inter.req_properties["mac"]
	    s=s+"\n  Name\t: "+inter.opt_properties["host_name"]
	return s

