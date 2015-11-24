from Core.Connection import *
from Core.Interfaceable import *
from Core.globals import environ
from PyQt4.QtCore import QPoint

class OpenFlow_Controller(Interfaceable):
    device_type = "OpenFlow_Controller"

    def __init__(self):
        Interfaceable.__init__(self)

        self.lightPoint = QPoint(-10,-3)
