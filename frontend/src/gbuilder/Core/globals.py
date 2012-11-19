""" Various global variables """
import os

from Core.paths import GINI_HOME, GINI_ROOT

PROG_NAME = "gBuilder"
PROG_VERSION  = "2.0.1"

environ = {"os":"Windows",
           "path":GINI_ROOT+"/",
           "remotepath":"./",
           "images":GINI_ROOT+"/share/gbuilder/images/",
           "config":GINI_ROOT+"/etc/",
           "sav":GINI_ROOT+"/sav/",
           "tmp":GINI_ROOT+"/tmp/",
           "doc":GINI_ROOT+"/doc/"}

options = {"names":True,
           "systray":False,
           "elasticMode":False, "keepElasticMode":False,
           "smoothing":True, "glowingLights":True, "style":"Plastique",
           "grid":True, "gridColor":"(240,240,240)",
           "background":environ["images"] + "background.jpg",
           "windowTheme":environ["images"] + "background2.jpg",
           "baseTheme":environ["images"] + "background3.jpg",
           "autorouting":True, "autogen":True, "autocompile":True,
           "graphing":True, "username":"",
           "server":"localhost", "session":"GINI", "autoconnect":True,
           "localPort":"10001", "remotePort":"10000",
           "restore":True,
           "moveAlert":True}

mainWidgets = {"app":None,
               "main":None,
               "canvas":None,
               "tab":None,
               "popup":None,
               "log":None,
               "tm":None,
               "properties":None,
               "interfaces":None,
               "routes":None,
               "drop":None,
               "client":None}

defaultOptions = {"palette":None}
