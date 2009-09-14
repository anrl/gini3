from Core.Connection import *
from Core.Interfaceable import *
from UI.Configuration import environ
from PyQt4.QtCore import QPoint

class UML(Interfaceable):
    type="UML"
    
    def __init__(self):
        Interfaceable.__init__(self)

        self.setProperty("filetype", "cow")
        self.setProperty("filesystem", "root_fs_beta2")

        self.lightPoint = QPoint(-10,3)

