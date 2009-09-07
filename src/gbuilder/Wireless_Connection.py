from Connection import *

##
# Class: the wireless connection
class Wireless_Connection(Connection):
    type="wireless_connection"

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
	self.device_s=device          #the starting device connected with this connection
	self.device_e=None	      #the ending device connected with this connection

        #the default name is composed by the type of the device and a serial number
    	#it could be changed by user later
	self.name=self.type+"_"+str(c_num)

	# create a name tag
	if c_num != 0:
	    self.tag=Tag(x1, y1, 0, t_num, self.name)

	# channel properties
	self.properties={}
	self.properties["propagation"]="Shadowing"
	self.properties["channel_type"]="AWGN"
	self.properties["pathloss"]="Normal"
	self.properties["deviation"]="Normal"
	self.properties["noise"]=-140
	self.properties["distance"]=1
	

    ##
    # Get the properties of the wireless connection
    # @return the list of all properties
    def get_properties(self):
	return self.properties

    
	
