#===============================================================================
# giniSuperviser.py (GINI Superviser)
# GINI Superviser check the status of routers and UML 
#   1. Post a colored spot next to the element
#   2. Create a history for each element 
# Version 4:Uses Pyro for the communnication between gbuilder and ginisuperviser
#===============================================================================
 
# Revised by Daniel Ng

import sys, os, signal, time
from time import gmtime, strftime   # used to get the time in the history
#------------------------------------------------------------------------------ 
# used to communicate between gbuilder and ginisuperviser
import Pyro.naming, Pyro.core
import Pyro.util
#------------------------------------------------------------------------------ 

dev_dic = {}
hosts = ["localhost"]
remote_mode = False
verbose_mode = 1

##
# Determine the lowest pid among a list of process with the same name
#@param process: name of the process 
#@param list: list [0][1][2]: UML, process, pid
#@param name: Name of the UML
def minPID(process,list,name):
    min = 0
    buf=[]
    if list:
        for i in range(0, len(list) -1):
            # if the process and the name are equals then 
            # store this process in the list buf
            if (process == list[i][1]) and (name == list[i][0]):
                # store pid
                buf.append(list[i][2])
        if buf:
            buf.sort()
            min = buf[0]
    return min
               
##
# List the running UML
# @param userName used to selecte the UML run by this user
# @return: ListOfUML is the list of all processes limked with UML
# @return: umlAlive is a list of all UML running
def searchUML(userName):

    #1. Grep all UML
    open("GINI_TMP_SUPERVISER_UML", "w").close()
    for host in hosts:
	if host == "localhost":
	    remote_string = ""
	else:
   	    remote_string = "ssh " + host 
        command = "%s ps -eo pid,user,command |grep vmlinux >> GINI_TMP_SUPERVISER_UML" % remote_string 
    	os.system(command)

    ListOfUML=[]
    umlAlive=[]
    #2. Get their name, pid, and the command
    inFile = open("GINI_TMP_SUPERVISER_UML", "r")
    #2.1 Read the file line per line
    line = inFile.readline()
    while (line):
        if (line.find(userName) != -1):
            # don't consider others users
            if (line.find("grep") == -1):
            # don't consider the "grep" line
                if (line.find("[vmlinux]") == -1):
                    # don't consider the "[vmlinux]" line : start vmlinux
                    if (line.find("sh") == -1):
                        # don't consider the "sh" line
                        if (line.find("defunct") == -1):
                            # don't consider the defunct process (zombie)
                            if (line.find("SCREEN") == -1):
                            # don't consider the SCREEN line 
                                lineParts = line.split()
                                InfoUML=[]
                                # Name : ListOfUML[i][0]
                                name =lineParts[3]
                                InfoUML.append(name.strip("()"))
                                # Process : ListOfUML[i][1]
                                process=lineParts[4]
                                InfoUML.append(process.strip("[]"))
                                # pid : ListOfUML[i][2]
                                InfoUML.append(lineParts[0])
                                # UserName but never used for the moment
                                InfoUML.append(lineParts[1]) 
				if remote_mode:
				    InfoUML.append(dev_dic[name.strip("()")])                
				else:
				    InfoUML.append("localhost")                                
				ListOfUML.append(InfoUML)
                            else:
                                #if SCREEN -d -m -S UML_1 vmlinux umid=UML_1 etc
                                # this live means that UML_1 is running
                                linePart = line.split()
                                if (linePart[2] =="SCREEN"): 
                                    umlAlive.append(linePart[6])
        # Next line      
        line = inFile.readline()      
    #2.2 Close file
    inFile.close()
    #3. Clean up
    os.remove("GINI_TMP_SUPERVISER_UML")   
    return ListOfUML,umlAlive      
 
##       
# List the running routers 
# @param username used to selecte the routers run by this user
# @return: ListOfRouter is the list of all processes linked with routers
def searchRouter(username):

    # 1. Grep all running routers
    open("GINI_TMP_SUPERVISER_Router", "w").close()
    for host in hosts:
	if host == "localhost":
	    remote_string = ""
	else:
	    remote_string = "ssh " + host
	cmd="%s ps -eo pid,user,command |grep grouter >> GINI_TMP_SUPERVISER_Router" % remote_string 
	os.system(cmd)

    ListOfRouter=[]
    #  2. Get their name and pid
    inFile = open("GINI_TMP_SUPERVISER_Router", "r")
    #2.1 Read the file line per line
    line = inFile.readline()
    while (line):
        if (line.find(username) != -1):
            # don't consider others users
            if (line.find("grep") == -1):
                 # don't consider the "grep" lines
                if (line.find("sh") == -1):
                # don't consider the "sh" line
                    if (line.find("SCREEN") == -1):
                        # don't consider the "SCREEN" line
                        lineParts = line.split()
                        InfoRouter=[]
                        # pid
                        InfoRouter.append(lineParts[0])        
                        # name
                        InfoRouter.append(lineParts[5])
                        # user : never used for the moment
                        InfoRouter.append(lineParts[1])
			if remote_mode:
			    InfoRouter.append(dev_dic[lineParts[5]])
                        else:
			    InfoRouter.append("localhost")
			ListOfRouter.append(InfoRouter)
 
        # Next line        
        line = inFile.readline()   
    #2.2 Close file
    inFile.close()
    #3. Clean up
    os.remove("GINI_TMP_SUPERVISER_Router")
    return ListOfRouter

##
# Analyse all events linked with routers : alive? killed? ... 
# @param username used to select the routers run by this user
# @param CurrentListOfRouter is the old list of processes linked with routers
# @param gwriter is the instance of GiniWriter
# @return: ListOfRouter the new list of processes 
def checkRouter(CurrentListOfRouter, username,gwriter):
    #time.sleep(1)
    ListOfRouter = searchRouter(username)
    newElements = False
    msgFromRouter="\n"
    # 1. Configuration is running
    if CurrentListOfRouter: 
        if ListOfRouter:
        # 1.1 new routers
            for i in range(len(ListOfRouter)):
                new =True
                for j in range(len(CurrentListOfRouter)):
                    if ListOfRouter[i][1] == CurrentListOfRouter[j][1]:
                        new =False
                if new:
                    gwriter.createMsgStatus(ListOfRouter[i][1],"green")
                    gwriter.addHistory(ListOfRouter[i][1],\
                                       "\n\t\t%s: %s is running ... "\
                                        % (strftime("%Hh%M ", gmtime())\
                                           ,ListOfRouter[i][1]))
            
            # 1.2 Routers killed 
            for i in range(len(CurrentListOfRouter)):
                killed =True 
                for j in range(len(ListOfRouter)):
                    if CurrentListOfRouter[i][1] ==ListOfRouter[j][1]:
                        killed =False
                if killed:
                    gwriter.createMsgStatus(CurrentListOfRouter[i][1],"red")
                    gwriter.addHistory(CurrentListOfRouter[i][1],\
                                       "\n\t\t%s: %s... was killed. "\
                                        % (strftime("%Hh%M ", gmtime()),\
                                           CurrentListOfRouter[i][1]))
        #2. the new list is empty : configuration was stopped 
        else:
            for i in range(len(CurrentListOfRouter)):
                gwriter.createMsgStatus(CurrentListOfRouter[i][1],"red")
                gwriter.addHistory(CurrentListOfRouter[i][1],\
                                   "\n\t\t%s: %s ... was killed. " \
                                   %(strftime("%Hh%M ", gmtime()),\
                                     CurrentListOfRouter[i][1]))
    else:
        #3.  Configuration has started 
        if ListOfRouter:
            for i in range(len(ListOfRouter)):
                gwriter.createMsgStatus(ListOfRouter[i][1],"green")
                t = strftime("%Hh%M ", gmtime())
                gwriter.addHistory(ListOfRouter[i][1],"\n\t\t%s: %s is running... "\
                            % (strftime("%Hh%M ", gmtime()),ListOfRouter[i][1]))

        # No modififications
        else :
            #newElements = True 
            msgFromRouter= "\n\t\tNo router is running.\n"

    # Refresh interface of gbuilder if new elements are detected
    if newElements == True:
        gwriter.postOnInterface(msgFromRouter)
    #2. Send the new list of elements
    return ListOfRouter


##
# Analyse all events linked with UML : alive? killed? crashed? logged? ... 
# @param CurrentListOfUMLs : list of prpcesses linked with UML
# @param ListumlAlive : list of UML 
# @param userName used to select the UML run by this user
# @param gwriter is the instance of GiniWriter
# @return: ListOfUML, umlAlive : return new lists
def checkUML(CurrentListOfUMLs,ListumlAlive,userName,gwriter):   
    #time.sleep(2)   # Wait delay between checking alive UML
    (ListOfUML, umlAlive)= searchUML(userName)
    buflist=[]      # Used to make a list of killed UML
    modification = False   
    string ="\n"
    # 1 Some process were already Running       
    if CurrentListOfUMLs: 
        #1.1 Some process are already Running   
        if ListOfUML:
            # Analyse the difference between the two lists       
            # 1.1.1 Analyse the new processes
            for i in range(len(ListOfUML)):
                #if not (ListOfUML [i][2] in CurrentListOfUMLs ):
                #1.1.1.1 Check if a new process has arrived (look for new pid) 
                new = True
                for j in range (len(CurrentListOfUMLs)):
                    if (ListOfUML[i][2] == CurrentListOfUMLs[j][2]):
                        new = False
                if new :
                    ##### Type of process ######
                    UMLassociated =ListOfUML[i][0]
                    proc =ListOfUML[i][1]
                    # When a UML starts, the process initlog appears once
                    if proc =="/sbin/initlog":
                            gwriter.createMsgStatus(UMLassociated,"yellow")
                            gwriter.addHistory(UMLassociated,\
                                               "\t\t%s: %s is Booting :Determine its settings ... Please wait.\n" \
                                               % (strftime("%Hh%M ", gmtime()),\
                                                  UMLassociated))
                    # When a UML has started, it launch the process agetty to log
                    if proc =="/sbin/agetty":
                        firstTime = True
                        for k in range(len(CurrentListOfUMLs)):
                            if (CurrentListOfUMLs[k][1] == "/sbin/agetty") and \
                            (UMLassociated == CurrentListOfUMLs[k][0]):
                                firstTime = False
                        if firstTime :
                            gwriter.createMsgStatus(UMLassociated,"orange")
                            gwriter.addHistory(UMLassociated,\
                                               "\t\t%s: %s is Running : Please enter password for Root access ... \n"\
                                                % (strftime("%Hh%M ", gmtime()),\
                                                   UMLassociated))
                    # Login is started when a user is logged
                    if proc =="/bin/login":
                        logged = False
                        #gwriter.createMsgStatus(UMLassociated,"green")
                        for k in range(len(CurrentListOfUMLs)):
                            if (CurrentListOfUMLs[k][1] == "/sbin/agetty") and \
                            (UMLassociated == CurrentListOfUMLs[k][0]) :
                                logged = True
                                #break  
                        if logged:
                            gwriter.createMsgStatus(UMLassociated,"green")
                            gwriter.addHistory(UMLassociated,\
                                               "\t\t%s: %s is Running : User is logged.\n" \
                                               % (strftime("%Hh%M ", gmtime()),\
                                                  UMLassociated))
                    # A UML has crashed 
                    if proc =="sulogin":
                        gwriter.createMsgStatus(UMLassociated,"red")
                        gwriter.addHistory(UMLassociated,\
                                           "\t\t%s: %s has crashed :You need to enter log as root, then fsck and at least exit.\n" \
                                           % (strftime("%Hh%M ", gmtime()),\
                                              UMLassociated))
                        
            # 1.1.2 Analyse the missing processes
            for i in range(len(CurrentListOfUMLs)):
                dead =True
                for j in range(len(ListOfUML)):
                     if (ListOfUML[j][2] == CurrentListOfUMLs[i][2]):
                        dead = False
                if dead:
                    ##### Type of  process ######
                    value =CurrentListOfUMLs[i][1] 
                    if value =="/sbin/initlog":
                        # Sometimes, two process initlog can be started for 
                        # the same UML , in order not to post the information 
                        # twice, the process initlog with the lowest pid 
                        #is selected
                        if (CurrentListOfUMLs[i][2] == minPID(value,\
                                                    CurrentListOfUMLs,\
                                                    CurrentListOfUMLs[i][0])):
                            gwriter.addHistory(CurrentListOfUMLs[i][0],\
                                               "\t\t%s: %s has booted.\n" \
                                               % (strftime("%Hh%M ", gmtime()),\
                                                  CurrentListOfUMLs[i][0]))
                    if value =="/usr/sbin/sshd": 
                        gwriter.addHistory(CurrentListOfUMLs[i][0],"\t\t%s UML is Running :End of communication via ssh between UML and host\n" %(CurrentListOfUMLs[i][0]))

            # 1.1.3 Analyse the running UML     
            # check : compare the current and the old list of UML
            for k in range(len(ListumlAlive)):
                # Post on the interface "UML was killed" only once:
                if umlAlive:
                    if not (ListumlAlive[k] in umlAlive):
                        if not (ListumlAlive[k] in buflist):
                            gwriter.createMsgStatus(ListumlAlive[k],"red")
                            gwriter.addHistory(ListumlAlive[k],\
                                               "\t\t%s: %s was killed.\n" \
                                               % (strftime("%Hh%M ", gmtime()),\
                                                  ListumlAlive[k]))
                        else :
                            buflist.append(ListumlAlive[k])
                else:
                   gwriter.createMsgStatus(ListumlAlive[k],"red")
                   gwriter.addHistory(ListumlAlive[k],"\t\t%s: %s was killed.\n" \
                                      % (strftime("%Hh%M ", gmtime()),\
                                         ListumlAlive[k]))
                     
        # No UML is runing  : New list of UML is empty 
        else:
            for k in range(len(ListumlAlive)):
                gwriter.createMsgStatus(ListumlAlive[k],"red")   
                gwriter.addHistory(ListumlAlive[k],"\t\t%s: %s was killed. \n" \
                                   % (strftime("%Hh%M ", gmtime()),\
                                      ListumlAlive[k]))
            


    else :
        #1.2.1 No UML is  running : the old list and the new list are empty
        string = string+"\n\t\tNo UML is Running.\n"
        if ListumlAlive:
            for k in range(len(ListumlAlive)):
                gwriter.createMsgStatus(ListumlAlive[k],"red")
                gwriter.addHistory(ListumlAlive[k],"\n\t\tNo UML is Running.\n")
        #1.2.2 the old list is empty and the new list is not empty : 
        #       topology has started
        new = True
        for j in range (len(ListOfUML)):
            # When a UML starts, the  process initlog appears once
            if ListOfUML[j][1] =="/sbin/initlog":
                            gwriter.createMsgStatus(ListOfUML[j][0],"yellow")
                            gwriter.addHistory(ListOfUML[j][0],\
                                               "\t\t%s: %s is Booting :Determine its settings ... Please wait.\n" \
                                               % (strftime("%Hh%M ", gmtime()),\
                                                  ListOfUML[j][0]))
    # 2. Alarm  gbuilder of asynchrous events : write onthe interface of gbuilder    
    if modification:
        gwriter.postOnInterface(string)
    
    #3. return the new list 
    return ListOfUML,umlAlive 
 
#### -------------- MAIN start ----------------####
# 1. Check if UML or Router are still running [OK]
# 2. Indicate their status to the interface   [OK] 
# 3. Post the history of an element when the user
#    click on status                          [OK]

def start(uri, uri2):
    #0. Test / Infos
    #time.sleep(5)
    print "\nGini superviser PID [", os.getpid() , "]"
    # Check which one suit best for gini superviser username=os.getlogin() or getuid()
    username=os.getlogin()
    print "Username: ", username, "\n"
    inFile = open("PidGiniSuperviser", "w")
    inFile.write(str(os.getpid()))
    inFile.close()    
    #1. Initialization 
    #1.1 start pyro 
    Pyro.core.initClient()
    #1.2 initalize the list
    CurrentListOfRouter = []
    CurrentListOfUML = []
    ListumlAlive=[]


    #gwriter = Pyro.core.getProxyForURI("PYROLOC://localhost:9000/giniServerInstance") 
    gwriter = Pyro.core.getProxyForURI(uri)
    tm = Pyro.core.getProxyForURI(uri2)
 
    #2. Main loop
    while 1:
        #2.1 Supervise router events
        CurrentListOfRouter=checkRouter(CurrentListOfRouter, username,gwriter)       
	#2.2 Refresh the list of all events in Control Panel
        time.sleep(1)
        gwriter.refreshHisory()
        #2.3 Supervise UML events
        (CurrentListOfUML, ListumlAlive)=checkUML(CurrentListOfUML,ListumlAlive,username,gwriter)
	pidic = createDict(CurrentListOfRouter, CurrentListOfUML)
	tm.update_list(pidic)
	remote_check(tm, CurrentListOfRouter, CurrentListOfUML)

def remote_check(tm, CurrentListOfRouter, CurrentListOfUML):
    global dev_dic
    global hosts
    global remote_mode

    if tm.get_remote():
	if not tm.get_accessed() and tm.get_filename():
	    remote_mode = True
	    rdist_file = tm.get_filename() + "_rdist"
	    if os.access(rdist_file, os.F_OK):
	    	dev_dic = {}
	    	hosts = []
	    	rdhandle = open(rdist_file, "r")
	    	for line in rdhandle.readlines():
	    	    parts = line.strip().split(",")
		
		    if int(parts[1]):
			newhost = parts[2].split(":")[0]
		    	if hosts.count(newhost):
			    pass
		    	else:
			    hosts.append(newhost)
		    	for i in range(3, len(parts)):
			    dev_dic[parts[i]] = newhost

	    	rdhandle.close()
		if verbose_mode:		
		    print dev_dic
		    print hosts
		    pass
		tm.set_accessed(True)
    else:
	remote_mode = False
	hosts = ["localhost"]
	#for router in CurrentListOfRouter:
	#    dev_dic[router[1]] = "localhost"
	#for uml in CurrentListOfUML:
	#    dev_dic[uml[0]] = "localhost"

def createDict(routers, umls):
    newdict = {}
    for router in routers:
	newdict[router[1]] = [(router[0], router[3])]
	    
    for uml in umls:
	try:
	    currentlist = newdict[uml[0]]
	    currentlist.append((uml[2], uml[4]))
	except:
	    currentlist = [(uml[2], uml[4])]
	    newdict[uml[0]] = currentlist
    if verbose_mode:
	#print newdict
	 pass
    return newdict
                                            
def terminateAll():
    os.system("killall -q uswitch gbuilder screen") 
  
