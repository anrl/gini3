"""A device that can be attached to"""

from Device import *

class Attachable(Device):
    def __init__(self):
        """
        Create a device that can be attached to.
        """
        Device.__init__(self)

        self.menu.addAction("Restart", self.restart)
        self.menu.addAction("Stop", self.terminate)

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
        
        window_name = str(self.getProperty("Name"))  # the strcast is necessary for cloning
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