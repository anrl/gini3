from UML import *
from PyQt4.QtCore import QPoint

class Mobile(UML):
    type="Mobile"
 
    def __init__(self):
        Device.__init__(self)
        
        self.con_int={}                         # the connection and interface pair
        self.next_interface_number=0
        self.adjacent_router_list=[]
        self.adjacent_subnet_list=[]
        
        self.setProperty("filetype", "cow")
	self.setProperty("filesystem", "root_fs_beta2")

        self.lightPoint = QPoint(-4,16)

    def addEdge(self, edge):
        Device.addEdge(self, edge)

        node = edge.getOtherDevice(self)
        self.addInterface(node)

    def removeEdge(self, edge):
        Device.removeEdge(self, edge)

        node = edge.getOtherDevice(self)
        self.removeInterface(node)

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
