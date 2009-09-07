from UML_machine import *
from Wireless_Interface import *

## 
# Class: the mobile device
class Mobile(UML_machine):
    type="Mobile"
    
    ##
    # Constructor: Initial a mobile device
    # @param x the x axis of the device on the canvas
    # @param y the y axis of the device on the canvas
    # @param m_num the serial number of the mobile
    # @param t_num the serial number of the name tag    
    def __init__(self, x, y, m_num, t_num):
        self.x=x
        self.y=y
        self.connection=[]
        self.interface=[]
        self.con_int={}                         # the connection and interface pair
        self.num=m_num
        self.relative_y=-40                     # the relative y position of name to the graph
        self.next_interface_number=0
        self.adjacent_router_list=[]
        self.adjacent_subnet_list=[]
        
        #required properties for a UML
        self.filetype="cow"                 
        self.filesystem="root_fs_beta2"


        #the default name is composed by the type of the device and a serial number
        self.name=self.type+"_"+str(m_num)

        #create a name tag
        self.tag=Tag(x, y, self.relative_y, t_num, self.name)

    ##
    # Add an adjacent router to the adjacent router list
    # @param con the connection to start to find adjacent router
    # @param other_device the adjacent router
    # @param gateway the gateway to reach the adjacent router
    def add_adjacent_router(self, con, other_device, gateway):

        #find out which interface connects with the con
        for inter in other_device.get_interface():
            if inter.type == "wireless":
                if con in inter.get_shared_connections():
                    self.adjacent_router_list.append([gateway, inter.get_ip(), other_device])
            else:
                if con == inter.get_connection():
                    self.adjacent_router_list.append([gateway, inter.get_ip(), other_device])

    ##
    # The bolloon help info for this UML
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
            s=s+"\n  Coordinates\t: (%d, %d)" % (self.x, self.y)
        return s
