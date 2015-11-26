#!/usr/bin/python2

"""gini_tcp.py: Retrieves the OpenFlow controller TCP port number and writes it to a file."""

from pox.core import core
import pox.lib.util as poxutil
import time
import os

log = core.getLogger()

def go_up(event):
    # Wait until initial OpenFlow controller socket has been created
    while len(core.of_01.sockets) == 0:
        time.sleep(1)

    # Get port number from OpenFlow controller socket
    port_num = core.of_01.sockets[0].getsockname()[1]
    log.info("port: " + str(port_num))

    # Write the port number to the specified file
    try:
        os.remove(tcp_path_g)
    except OSError:
        pass
    tcp_file = open(tcp_path_g, "w")
    tcp_file.write(str(port_num))
    tcp_file.close()

@poxutil.eval_args
def launch(tcp_path):
    global tcp_path_g
    tcp_path_g = tcp_path

    core.addListenerByName("UpEvent", go_up)
