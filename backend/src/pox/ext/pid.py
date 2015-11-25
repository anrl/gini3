# Import some POX stuff
from pox.core import core                     # Main POX object
import pox.openflow.libopenflow_01 as of      # OpenFlow 1.0 library
import pox.lib.packet as pkt                  # Packet parsing/construction
from pox.lib.addresses import EthAddr, IPAddr # Address types
import pox.lib.util as poxutil                # Various util functions
import pox.lib.revent as revent               # Event library
import pox.lib.recoco as recoco               # Multitasking library
import os

# Create a logger for this component
log = core.getLogger()

@poxutil.eval_args
def launch(path):
    pid = os.getpid()
    log.info("pid: " + str(pid))

    try:
        os.remove(path)
    except OSError:
        pass

    pid_file = open(path, "w")
    pid_file.write(str(pid))
    pid_file.close()
