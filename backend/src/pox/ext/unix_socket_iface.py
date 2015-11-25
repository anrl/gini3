# Import some POX stuff
from pox.core import core                     # Main POX object
import pox.openflow.libopenflow_01 as of      # OpenFlow 1.0 library
import pox.lib.packet as pkt                  # Packet parsing/construction
from pox.lib.addresses import EthAddr, IPAddr # Address types
import pox.lib.util as poxutil                # Various util functions
import pox.lib.revent as revent               # Event library
import pox.lib.recoco as recoco               # Multitasking library

# Create a logger for this component
log = core.getLogger()
instance = None
socket_path = None

def _go_up (event):
    while len(core.of_01.sockets) == 0:
        pass

    socket = core.of_01.sockets[0].getsockname()[1]

    log.info(str(instance[0]) + ": port: " + str(socket))
    log.info(str(instance[0]) + ": path: " + socket_path)

@poxutil.eval_args
def launch (path, __INSTANCE__ = None):
    global socket_path
    socket_path = path

    global instance
    instance = __INSTANCE__
    if instance is None:
        instance = (1, 1, True)

    core.addListenerByName("UpEvent", _go_up)
