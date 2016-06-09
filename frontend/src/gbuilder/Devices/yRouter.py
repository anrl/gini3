from Router import *
from PyQt4 import QtCore

class yRouter(Router):
    device_type="yRouter"

    def __init__(self):
	Interfaceable.__init__(self)
	self.setProperty("WLAN", "False")
	self.setProperty("mac_type", "MAC 802.11 DCF")
        self.lightPoint = QPoint(-14,15)

#    def generateToolTip(self):
#        """
#        Add subnet IP address to the tool tip for easier lookup.
#        """
#        tooltip = self.getName()
#        interface = self.getInterface()
#        tooltip += "\n\nSubnet: " + interface[QtCore.QString("subnet")] + "\n"
#        tooltip += "IP: " + interface[QtCore.QString("ipv4")]          
#        self.setToolTip(tooltip)
