#!/usr/bin/python2

"""gini_pid.py: Retrieves the OpenFlow controller PID and writes it to a
   file."""

from pox.core import core
import pox.lib.util as poxutil
import os

log = core.getLogger()

@poxutil.eval_args
def launch(pid_path):
    # Retrieve the PID of this instance of POX
    pid = os.getpid()
    log.info("pid: " + str(pid))

    # Write the PID to the specified file
    try:
        os.remove(pid_path)
    except OSError:
        pass
    pid_file = open(pid_path, "w")
    pid_file.write(str(pid))
    pid_file.close()
