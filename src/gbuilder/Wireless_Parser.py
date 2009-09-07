#!/usr/bin/python
# Written by Daniel Ng

import os
import time
import readline

while(1):
    command = raw_input("WGINI $ ")               
    hardfile = "%s/bin/hardcopy.0" % os.environ["GINI_HOME"]
    command = command.strip()

    if command == "exit":
        os.system("killall gwcenter")
        break
    elif command == "quit":
        break  
    elif command.find("mac") == 0 or \
         command.find("mov") == 0 or \
         command.find("sys") == 0 or \
         command.find("ch") == 0 or \
         command.find("energy") == 0 or \
         command.find("about") == 0 or \
         command.find("halt") == 0 or \
         command.find("stats") == 0 or \
         command.find("wcard") == 0 or \
         command.find("ant") == 0:
        pass
    elif command.find("help") == 0:
        if command.find("help help") == 0:
            topic = "helphelp"
        else:
            topic = command.split("help ")[-1].strip()
        helpfile = "%s/bin/help/%s" % (os.environ["GINI_HOME"],topic)
        if os.access(helpfile, os.F_OK):
            os.system("screen -S VWAP_1 -X eval clear")
            os.system("less %s" % helpfile)
        else:
            print "Help for %s does not exist" % topic        
        #helpIn = open("%s/bin/help/%s" % (os.environ["GINI_HOME"],topic), "r")
        #for line in helpIn.readlines():
            #print line,
        #helpIn.close()
        continue
    else:
        os.system(command)
        continue

    os.system("screen -S WAP_1 -X eval 'stuff clear\\015'")                 
    os.system("screen -S WAP_1 -X eval 'stuff \"%s\"\\015'" % command)
    time.sleep(0.1)
    os.system("screen -S WAP_1 -X eval hardcopy")  
    time.sleep(0.1)

    hardIn = open(hardfile)
    lines = hardIn.readlines()   
    for i in range(1, len(lines)-1):
        if lines[i] != "\n" and lines[i] != "WGINI $\n":        
            print lines[i],
    hardIn.close()

