from Router import *
from PyQt4 import QtCore

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
    def __init__(self):
        Device.__init__(self)

        self.interface = []
        self.num_interface=0
        self.connection=[]
        self.con_int={}                         # the connection and interface pair
        self.wireless_con_list=[]                # the list of wireless devices that share this wireless connection
        self.next_interface_number=0

        # by default, auto compute routing table is off
        self.auto=0

        #wireless properties
        self.properties[QtCore.QString("w_type")]="Sample Card"
        self.properties[QtCore.QString("freq")]="2400000000"
        self.properties[QtCore.QString("bandwidth")]="2000000.0"
        self.properties[QtCore.QString("Pt")]="0.2818"
        self.properties[QtCore.QString("Pt_c")]="0.660"
        self.properties[QtCore.QString("Pr_c")]="0.395"
        self.properties[QtCore.QString("P_idle")]="0.0"
        self.properties[QtCore.QString("P_sleep")]="0.130"
        self.properties[QtCore.QString("P_off")]="0.043"
        self.properties[QtCore.QString("RX")]="2.818e-9"
        self.properties[QtCore.QString("CS")]="1.409e-9"
        self.properties[QtCore.QString("CP")]="10"
        self.properties[QtCore.QString("module")]="DSSS"
        self.properties[QtCore.QString("a_type")]="Omni Directional Antenna"
        self.properties[QtCore.QString("ant_h")]="1"
        self.properties[QtCore.QString("ant_g")]="1"
        self.properties[QtCore.QString("ant_l")]="1"
        self.properties[QtCore.QString("JAM")]="off"
        self.properties[QtCore.QString("power")]="ON"
        self.properties[QtCore.QString("PSM")]="OFF"
        self.properties[QtCore.QString("energy_amount")]="100"
        self.properties[QtCore.QString("m_type")]="Random Waypoint"
        self.properties[QtCore.QString("ran_max")]="15"
        self.properties[QtCore.QString("ran_min")]="5"
        self.properties[QtCore.QString("mac_type")]="MAC 802.11 DCF"
        self.properties[QtCore.QString("trans")]="0.1"

        self.interfaces.append({
            QtCore.QString("subnet"):QtCore.QString(""),
            QtCore.QString("mask"):QtCore.QString(""),
            QtCore.QString("ipv4"):QtCore.QString(""),
            QtCore.QString("mac"):QtCore.QString(""),
            QtCore.QString("routing"):[]})

        self.lightPoint = QPoint(-14,15)

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
        
