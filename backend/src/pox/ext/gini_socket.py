#!/usr/bin/python2

"""gini_socket.py"""

from pox.core import core
import pox.lib.util as poxutil
import socket
import time
import os

log = core.getLogger()

def go_up(event):
    # Wait until initial OpenFlow controller socket has been created
    while len(core.of_01.sockets) == 0:
        time.sleep(1)

    # Get port number from socket
    port_num = core.of_01.sockets[0].getsockname()[1]
    log.info("instance " + str(instance_g[0]) + ": port: " + str(port_num))
    log.info("instance " + str(instance_g[0]) + ": path: " + socket_path_g)

    # TODO: Implement TCP interface in GINI, then access it here and pass the
    # data to the OpenFlow controller

    # Open Unix socket
    # client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    # client.connect(socket_path_g)

@poxutil.eval_args
def launch(socket_path, __INSTANCE__ = None):
    # Set __INSTANCE__ to defaults if there is only one instance
    if __INSTANCE__ is None:
        __INSTANCE__ = (1, 1, True)

    global instance_g
    instance_g = __INSTANCE__

    global socket_path_g
    socket_path_g = socket_path

    core.addListenerByName("UpEvent", go_up)
