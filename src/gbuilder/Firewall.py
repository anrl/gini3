import Connection
from Tag import *
from Router import *


##
# Class: the firewall class. Not fully implemented yet
class Firewall(Router):
    type="Firewall"

    ##
    # Constructor: Initial a firewall device
    # @param x the x axis of the device on the canvas
    # @param y the y axis of the device on the canvas
    # @param f_num the serial number of the firewall
    # @param t_num the serial number of the name tag     
    def __init__(self, x, y, f_num, t_num):
	self.x=x
	self.y=y
	self.num_interface=0
	self.interface=[]
	self.connection=[]
	self.con_int={}                         # the connection and interface pair
	self.num=f_num
	self.next_interface_number=0
	self.relative_y=-40

	#the default name is composed by the type of the device and a serial number
	self.name=self.type+"_"+str(f_num)

	#create a name tag
	self.tag=Tag(x, y, self.relative_y, t_num, self.name)

	#create two interface when the router create
	self.add_interface()
	self.add_interface()

    ##
    # The bolloon help info for this firewall
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

	
