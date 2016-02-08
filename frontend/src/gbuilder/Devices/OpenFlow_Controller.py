from Core.Connection import *
from Core.Device import *
from Core.globals import environ
from PyQt4.QtCore import QPoint

class OpenFlow_Controller(Device):
    device_type = "OpenFlow_Controller"

    def __init__(self):
        Device.__init__(self)

        self.menu.addAction("Restart", self.restart)
        self.menu.addAction("Stop", self.terminate)

        self.lightPoint = QPoint(-10,-3)

    def attach(self):
        """
        Attach to corresponding device on backend.
        """

        base = "ssh -t " + options["username"] + "@" + options["server"]
        
        screen = " screen -r "
        if self.device_type == "Wireless_access_point":
            screen += "WAP_%d" % self.getID()
        else:
            name = self.getName()
            pid = mainWidgets["tm"].getPID(name)
            if not pid:
                return
            screen += pid + "." + name
            
        command = ""
        
        window_name = str(self.getProperty("name"))  # the strcast is necessary for cloning
        if(self.getName() != window_name):
            window_name += " (" + self.getName() + ")"
        if environ["os"] == "Windows":
            
            startpath = environ["tmp"] + self.getName() + ".start"
            try:
                outfile = open(startpath, "w")
                outfile.write(screen)
                outfile.close()
            except:
                mainWidgets["log"].append("Failed to write to start file!")
                return
            
            command += "putty -"
            if options["session"]:
                command += "load " + options["session"] + " -l " + options["username"] + " -t"
            else:
                command += base
            command += " -m \"" + startpath + "\""
        else:
            command += "xterm -T \"" + window_name + "\" -e \"" + base + screen + "\""

        self.shell = subprocess.Popen(str(command), shell=True)