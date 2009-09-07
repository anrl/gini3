
import Connection
from Tag import *
from Device import *

##
# Class: the hub device. Not fully implemented yet
class Hub(Device):
    type="Hub"

    ##
    # Constructor: Initial a hub device
    # @param x the x axis of the device on the canvas
    # @param y the y axis of the device on the canvas
    # @param s_num the serial number of the hub
    # @param t_num the serial number of the name tag
    def __init__(self, x, y, s_num, t_num):
	self.x=x
	self.y=y
	self.connection=[]
	self.relative_y=-30

	#the default name is composed by the type of the device and a serial number
    	#it could be changed by user later
	self.name=self.type+"_"+str(s_num)

	# the properties that are needed to start UML network
	#self.properties[id]=s_num
	self.id=s_num
	self.port=""
	self.monitor=""
	self.hub=1           # use hub mode by default

	#create a name tag
	self.tag=Tag(x, y, self.relative_y, t_num, self.name)


    ##
    # The bolloon help info for this hub
    def balloon_help(self):
	s="Screen Name: "+self.name
	"""
	for inter in self.interface:
	    s=s+"\nInterface "+inter.get_id()+": "
	    
	    # find out which device connects with this interface
	    con=inter.get_connection()
	    if self.name == con.get_start_device():
		s=s+"(Connect to "+con.get_end_device()+")"
	    else:
		s=s+"(Connect to "+con.get_start_device()+")"

	    s=s+"\n  IP:  "+inter.req_properties[ipv4]
	    s=s+"\n  MAC: "+inter.req_properties[mac]
	"""
	return s

