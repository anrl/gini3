from Tag import *

##
# Class: The wire connection between two devices

class Connection:
    type="connection"

    ##
    # Constructor
    # @param x1 the x coordinate of starting point of the connection
    # @param y1 the y coordinate of starting point of the connection
    # @param x2 the x coordinate of ending point of the connection
    # @param y2 the y coordinate of ending point of the connection  
    # @param device Optional, the name of the device that contain this connection
    # @param c_num Optional, the index of this connection
    # @param t_num Optional, the index of the tag of the connection  
    def __init__(self,x1,y1,x2,y2,device="",c_num=0,t_num=0):
	self.x_s=x1
	self.y_s=y1
	self.x_e=x2
	self.y_e=y2
	self.num=c_num
	self.device_s=device          
	self.device_e=None	      
	self.name=self.type+"_"+str(c_num)

	# create a name tag
	if c_num != 0:
	    self.tag=Tag(x1, y1, 0, t_num, self.name)

    ##
    # Get the coordinates of the starting point of this connection
    # @return the coordinate (x, y)
    def get_start_point(self):
	return (self.x_s, self.y_s)

    ##
    # Get the coordinates of the ending point of this connection
    # @return the coordinate (x, y)
    def get_end_point(self):
	return (self.x_e, self.y_e)

    ##
    # Get the index of this connection
    # @return the index, an integer number
    def get_num(self):
	return self.num

    ##
    # update the coordinates of the ending point of the connection
    # @param x the x coordinate of the ending point
    # @param y the y coordinate of the ending point
    def update_end_point(self, x, y):
	self.x_e=x
	self.y_e=y

    ##
    # update the coordinates of the starting point of the connection
    # @param x the x coordinate of the starting point
    # @param y the y coordinate of the starting point
    def update_start_point(self, x, y):
	self.x_s=x
	self.y_s=y

    ##
    # get the type of this class
    # @return the type
    def get_type(self):
	return self.type

    ##
    # Get the device at the starting point of this connection
    # @return the device at the starting point
    def get_start_device(self):
	return self.device_s

    ##
    # Set the device at the starting point of this connection
    # @param device the device at the starting point
    def set_start_device(self, device):
	self.device_s=device

    ##
    # Get the device at the endinging point of this connection
    # @return the device at the ending point
    def get_end_device(self):
	return self.device_e

    ##
    # Set the device at the ending point of this connection
    # @param device the device at the ending point
    def set_end_device(self, device):
	self.device_e=device

    ##
    # Get the name of this connection
    # @return the name 
    def get_name(self):
	return self.name

    ##
    # update the name of this connection
    # @param n the new name of this connection
    def update_name(self, n):
	self.name=n

    ##
    # Get the tag of this connection
    # @return the tag
    def get_tag(self):
	return self.tag

    ##
    # Set the tag of this connection
    # @param t the tag of this connection
    def set_tag(self, t):
	self.tag=t

    ##
    # Get the device on the other side of the given device
    # @param device the given device
    # @return the device at the other side
    def get_other_device(self, device):
	if self.device_s == device:
	    return self.device_e
	else:
	    return self.device_s
