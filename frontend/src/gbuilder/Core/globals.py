""" Various global variables """
import os

PROG_NAME = "gBuilder"
PROG_VERSION  = "2.1.0"

GINI_ROOT = os.environ["GINI_ROOT"]
GINI_HOME = os.environ["GINI_HOME"]

environ = {"os":"Windows",
           "path":GINI_ROOT+"/",
           "remotepath":"./",
           "images":os.environ["GINI_SHARE"] +"/gbuilder/images/",
           "config":GINI_HOME+"/etc/",
           "sav":GINI_HOME+"/sav/",
           "tmp":GINI_HOME+"/tmp/",
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
           "graphing":True, "username":"root",
           "server":"localhost", "session":"GINI", "autoconnect":True,
           "localPort":"10001", "remotePort":"10000",
           "restore":True,
           "moveAlert":True, "wserver":"192.168.54.121", "wlocalPort":"60001","wremotePort":"60000"}

mainWidgets = {"app":None,
               "main":None,
               "canvas":None,
               "tab":None,
               "popup":None,
	       "inputDialog":None,
               "log":None,
               "tm":None,
               "properties":None,
               "interfaces":None,
               "routes":None,
               "drop":None,
               "client":None,
	       "wgini_client":None}

defaultOptions = {"palette":None}

yRouters = {}		# indexed by yun ID
availableyRouters = []
usedyRouters = {}	# indexed by topology index
