from Core.Device import *

class Switch(Device):
    device_type = "OpenFlow Controller"

    def __init__(self):
        Device.__init__(self)

    def addEdge(self, edge):
        Device.addEdge(self, edge)

        node = edge.getOtherDevice(self)
        if node.device_type == "Router":
            node.addInterface(self)

    def removeEdge(self, edge):
        Device.removeEdge(self, edge)

        node = edge.getOtherDevice(self)
        if node.device_type == "Router":
            node.removeInterface(self)
