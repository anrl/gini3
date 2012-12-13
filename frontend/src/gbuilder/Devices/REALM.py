from Core.Connection import *
from Core.Interfaceable import *
from Core.globals import environ
from PyQt4.QtCore import QPoint
# import Core.datarev 

class REALM(Interfaceable):
    device_type="REALM"


    def __init__(self):

        Interfaceable.__init__(self)
        print "hooray i'm initting"

        self.setProperty("ipv4", "")
        self.setProperty("port", "")
        self.setProperty("mac", "")
        self.setProperty("filetype", "cow")
        self.setProperty("filesystem", "root_fs_beta2")
        self.hostIndex = 0
        self.properties["Hosts"] = ["default","change"]
        self.hostsproperty={"default":ConnectM("1","2","3","4"),"change":ConnectM("name","ip","mac","port")}
        self.lightPoint = QPoint(-10,3)

        name = []
        ip = []
        port = []
        
        datarev = "aaa"
        data = datarev.split('end')  
   
        for i in range(len(data)-1):
            name.append(data[i].split(',')[1])
            ip.append(data[i].split(',')[2])
            port.append(data[i].split(',')[3])
        print name
        for item in range(len(name)):
            self.properties["Hosts"] = [name[item]]
            self.hostsproperty={name[item]:ConnectM(name[item],ip[item],"",port[item])}


class ConnectM():
    def __init__ (self,name,ip,mac,port):
	self.name=name
	self.ip=ip
	self.mac=mac
	self.port=port



