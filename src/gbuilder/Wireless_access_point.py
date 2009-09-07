from Router import *
from Wireless_Interface import *

##
# Class: the wireless router class
class Wireless_access_point(Router):
    type="Wireless_access_point" 

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
        self.wireless_con_list=[]                # the list of wireless devices that share this wireless connection
        self.num=r_num
        self.relative_y=-40                          # the relative y position of name to the iamge
        self.next_interface_number=0

        # by default, auto compute routing table is off
        self.auto=0

        #the default name is composed by the type of the device and a serial number
            #it could be changed by user later
        self.name=self.type+"_"+str(r_num)

        #create a name tag
        self.tag=Tag(x, y, self.relative_y, t_num, self.name)

        #create a wireless connection point, all wireless devices will share the connection
        self.wireless_interface=self.add_wireless_interface()
        self.interface.append(self.wireless_interface)

        #wireless properties
        self.properties={}
        self.properties["w_type"]="Sample Card"
        self.properties["freq"]=2400000000
        self.properties["bandwidth"]=2000000.0
        self.properties["Pt"]=0.2818
        self.properties["Pt_c"]=0.660
        self.properties["Pr_c"]=0.395
        self.properties["P_idle"]=0.0
        self.properties["P_sleep"]=0.130
        self.properties["P_off"]=0.043
        self.properties["RX"]=2.818e-9
        self.properties["CS"]=1.409e-9
        self.properties["CP"]=10
        self.properties["module"]="DSSS"
        self.properties["a_type"]="Omni Directional Antenna"
        self.properties["ant_h"]=1
        self.properties["ant_g"]=1
        self.properties["ant_l"]=1
        self.properties["JAM"]="off"
        self.properties["power"]="ON"
        self.properties["PSM"]="OFF"
        self.properties["energy_amount"]=100
        self.properties["m_type"]="Random Waypoint"
        self.properties["ran_max"]=15
        self.properties["ran_min"]=5
        self.properties["mac_type"]="MAC 802.11 DCF"
        self.properties["trans"]=0.1
        

    ##
    # Get the wireless specific properties
    # @return the list of wireless properties
    def get_properties(self):
        return self.properties

    ##
    # Add the wireless interface
    # @param con Optional. The connection that in the wireless interface
    # @return the wirelss interface just added
    def add_wireless_interface(self, con=None):
        self.next_interface_number+=1
        self.wireless_interface=Wireless_Interface(con, self.next_interface_number)
        return self.wireless_interface

    ##
    # Add a new connection to the router
    # @param c the new connection to add 
    def add_connection(self, c):
        #if c.type == "wireless_connection":
        self.wireless_interface.add_connection(c)
        self.con_int[c]=self.wireless_interface
        #else:
            #self.connection.append(c)
            #new_interface=self.add_interface(c)
            #self.interface.append(new_interface)
            #self.con_int[c]=new_interface

    ##
    # Delete a specified connection of the router
    # @param c the connection to delete 
    def delete_connection(self, c):
        #if c.type == "wireless_connection":
        self.wireless_interface.del_connection(c)
        #else:
            #self.connection.remove(c)
            #self.interface.remove(self.con_int[c])
        del self.con_int[c]

    ##
    # Get all connections on the wireless interface
    # @return the list of wireless connections
    def get_wireless_connection(self):
        return self.wireless_interface.get_shared_connections()

    ## Get the wireless interface
    # @return the wireless interface of the wirelss router
    def get_wireless_interface(self):
        return self.wireless_interface

    ##
    # The bolloon help info for this router
    def balloon_help(self):
        s="Screen Name: "+self.name
        for inter in self.interface:
            if inter == self.wireless_interface:
                s=s+"\n\nInterface "+str(inter.get_id())+":(Wireless connection point)"
                s=s+"\n  IP\t: "+inter.req_properties["ipv4"]
                s=s+"\n  MAC\t: "+inter.req_properties["mac"]
                s=s+"\n  Subnet\t: "+inter.req_properties["subnet"]
                s=s+"\n  Name\t: "+inter.opt_properties["host_name"]
            else:
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
        
