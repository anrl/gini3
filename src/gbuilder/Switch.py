import Connection
from string import *
from Tag import *
from Device import *

## 
# Class: the switch class
class Switch(Device):
    type="Switch"

    ##
    # Constructor: Initial a switch
    # @param x the x axis of the switch location on the canvas
    # @param y the y axis of the switch location on the canvas
    # @param s_num the serial number of switch
    # @param t_num the serial number of the name tag
    def __init__(self, x, y, s_num, t_num):
	self.x=x
	self.y=y
	self.connection=[]
	self.relative_y=-30
	self.num=s_num
	self.mask=""
	self.subnet=""
	self.link_subnet=0

	#the default name is composed by the type of the device and a serial number
    	#it could be changed by user later
	self.name=self.type+"_"+str(s_num)

	#required properties for a switch
	self.req_properties={}

	#optional properties for an interface
	self.opt_properties={}	
	self.opt_properties["port"]=""
	self.opt_properties["monitor"]=""

	#create a name tag
	self.tag=Tag(x, y, self.relative_y, t_num, self.name)

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
