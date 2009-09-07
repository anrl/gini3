from Connection import *
from Tag import *
from Interface import *
from Device import *

##
# Class: the Subnet
class Subnet(Device):
    type="Subnet"    

    ##
    # Constructor: Initial a subnet
    # @param x the x axis of the device on the canvas
    # @param y the y axis of the device on the canvas
    # @param c_num the serial number of the subnet
    # @param t_num the serial number of the name tag  
    def __init__(self, x, y, c_num, t_num):
	self.x=x
	self.y=y
	self.num_interface=0
	self.connection=[]
	self.num=c_num
	self.relative_y=-25  			# the relative y position of name to the graph

	#the default name is composed by the type of the device and a serial number
    	#it could be changed by user later
	self.name=self.type+"_"+str(c_num)

	#create a name tag
	self.tag=Tag(x, y, self.relative_y, t_num, self.name)

	#required properties for a switch
	self.req_properties={}
	self.req_properties["subnet"]=""
	self.req_properties["mask"]=""
	self.req_properties["bits"]=""

	#optional properties for an interface
	self.opt_properties={}	


    ##
    # Get the subnet of this subnet
    # @return the required property, subnet
    def get_subnet(self):
	return self.req_properties["subnet"]

    ##
    # Get the subnet mask (overriden from Device)
    # @return the required property, mask
    def get_mask(self):
	return self.req_properties["mask"]
    
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


    ##
    # The bolloon help info for this subnet
    def balloon_help(self):
	s="Screen Name: "+self.name
	s=s+"\n\nSubnet\t: "+self.req_properties["subnet"]
	s=s+"\nMask\t: "+self.req_properties["mask"]
	return s
