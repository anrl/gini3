#!/usr/bin/python2

from pox.core import core
import pox.lib.util as poxutil
import os

log = core.getLogger()

@poxutil.eval_args
def launch(pid_path):
    # Retrieve the PID of this instance of POX
    pid = os.getpid()
    log.info("pid: " + str(pid))

    try:
        os.remove(pid_path)
    except OSError:
        pass

    # Write the PID to the specified file
    pid_file = open(pid_path, "w")
    pid_file.write(str(pid))
    pid_file.close()
