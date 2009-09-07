#===============================================================================
# giniSuperviser.py (GINI Superviser)
# Version 4:Uses Pyro for the communnication between gbuilder and ginisuperviser
#===============================================================================
 
import sys, os, signal, time

###############  TODO   ###############################
# Determine User    a remplacer par getlogin() !!!!!!!!!!!
# getuid(      ) ????
def whoAmI():
    cmd = "whoami > GINI_TMP_name.txt" 
    os.system(cmd)
    inFile = open("GINI_TMP_name.txt", "r")
    line = inFile.readline()
    lineParts = line.split()
    name =lineParts[0]
    os.remove("GINI_TMP_name.txt") 
    return name

############### End TODO   ###############################

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
def searchUML(userName):
    #1. Grep all UML 
    command = "ps -eo pid,user,command |grep vmlinux > GINI_TMP_SUPERVISER_UML" 
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
def searchRouter(username):
    # 1. Grep all running routers  
    cmd="ps -eo pid,user,command |grep grouter > GINI_TMP_SUPERVISER_Router" 
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
                        ListOfRouter.append(InfoRouter)
 
        # Next line        
        line = inFile.readline()   
    #2.2 Close file
    inFile.close()
    #3. Clean up
    os.remove("GINI_TMP_SUPERVISER_Router")  
    return ListOfRouter

##
# Send a signal to gbuilder if there is a new router of if a router died
def checkRouter(CurrentListOfRouter, username, ppid, tubeGiniSuperviserW):
    OldListOfRouter = CurrentListOfRouter
    time.sleep(1)
    ListOfRouter = searchRouter(username)
    newElements = False
    #1. Modification detected 
    # 1.1 configuration is already running 
    if OldListOfRouter: 
        if ListOfRouter:
            if len(OldListOfRouter)!= len(ListOfRouter):   
                msgFromRouter ="\n"    
                # 1.1.1 A process was killed
                if len(OldListOfRouter) > len(ListOfRouter):
                    for i in range(0, len(OldListOfRouter) -1):
                        if not (OldListOfRouter[i][0] in ListOfRouter):
                            s = " \t\tRouter : %s name: %s ... was killed " \
                            %(OldListOfRouter[i][0] , OldListOfRouter[i][1])
                            print s
                            msgFromRouter = msgFromRouter + s 
                            newElements = True  
                # 1.1.2 A new process has arrived
                elif len(OldListOfRouter) < len(ListOfRouter):
                    for i in range(0, len(ListOfRouter) -1):
                        if ListOfRouter[i][0] in OldListOfRouter:
                            t = "\t\tNew Router : %s ... \n" % (ListOfRouter[i][1])
                            print t 
                            msgFromRouter = msgFromRouter + t
                            newElements = True       
            
        # 1.1.3 All routers were killed
        else :
            newElements = True 
            if len(OldListOfRouter) ==1 :
                msgFromRouter = "\n\tRouter : %s ... was killed\n" \
                % (OldListOfRouter[0][1])
                print msgFromRouter
            else :
                for i in range(0, len(OldListOfRouter) -1):
                    print "\t\tRouter :", OldListOfRouter[i][1], "... was killed"  
                    msgFromRouter ="\n\tRouter : %s ... was killed\n"\
                     % (OldListOfRouter[i][1])
                      
    else :
        #1.2  Configuration has started 
        if ListOfRouter:
            if len(ListOfRouter) == 1 :
                t = "\n\t\tNew Router : %s ... \n" % (ListOfRouter[0][1])
                print t
                msgFromRouter = t
                newElements = True     
             
            else:   
                for i in range(0, len(ListOfRouter) -1):
                    t = "\n\t\tNew Router : %s ... \n" % (ListOfRouter[i][1])
                    print t
                    msgFromRouter = t
                    newElements = True     
        # No modififications
        else :
            newElements = True 
            msgFromRouter= "\t\tNo router is running\n"

    # Refresh interface of gbuilder if new elemetns are detected
    if newElements == True:
        os.write(tubeGiniSuperviserW, msgFromRouter)   
        #os.kill(ppid, signal.SIGUSR2)
    
    #2. Send the new list of elements 
    return ListOfRouter


def checkUML(CurrentListOfUMLs,ListumlAlive,userName, ppid, tubeGiniSuperviserW):   
    OldListOfUML = CurrentListOfUMLs
    oldListumlAlive = ListumlAlive
    time.sleep(2)
    (ListOfUML, umlAlive)= searchUML(userName)
    buflist=[]
    modification = False   
    string ="\n"
    # 1 Some process were already Running       
    if OldListOfUML: 
        #1.1 Some process are already Running   
        if ListOfUML:
            # Analyse the difference between the two lists       
            # 1.1.1 Analyse the new processes
            for i in range(0, len(ListOfUML)-1):
                if not ListOfUML[i][2] in OldListOfUML:
                    ##### Type of  process ######
                    UMLassociated =ListOfUML[i][0]
                    proc =ListOfUML[i][1]
                    # When a UML starts, the  process initlog appears once
                    if proc =="/sbin/initlog":
                        if (ListOfUML[i][2] == minPID(proc,ListOfUML,ListOfUML[i][0])):
                            print "\tUML :", UMLassociated, " ... UML is Booting :Determine its settings ... Please wait\n"
                            string = string +"\t\tUML : %s  ... UML is Booting :Determine its settings ... Please wait\n" % (UMLassociated)
                            modification =True
                    # When a UML has started, it launch the process agetty to log
                    if proc =="/sbin/agetty":
                        firstTime = True
                        for k in range(0, len(OldListOfUML) -1):
                            if (OldListOfUML[k][1]  == "/sbin/agetty") and(UMLassociated == OldListOfUML[k][0]):
                                firstTime = False
                                break
                        if firstTime :                       
                            print "\tUML :", UMLassociated, " ... UML is Running : Please enter password for Root access ...\n"
                            string = string +"\t\tUML : %s  ...UML is Running : Pease enter password for Root access ... \n" % (UMLassociated)
                            modification =True
                    # Login is started when a user is logged
                    if proc =="/bin/login":
                        logged = False
                        for k in range(0, len(OldListOfUML) -1):
                            if (OldListOfUML[k][1]  == "/sbin/agetty")  and (UMLassociated == OldListOfUML[k][0]) :
                                logged = True
                                break  
                        if logged:
                            print "\tUML :", UMLassociated, " ... UML is Running :User is logged ...\n"
                            string = string + "\t\tUML : %s ... UML is Running : User is logged\n" % (UMLassociated)
                            modification =True
                    # A UML has crashed 
                    if proc =="sulogin":
                        print "\tUML :", UMLassociated, " ... UML has crashed ...\n"
                        string =string + "\t\tUML : %s ... UML has crashed :You need to enter log as root and do fsck and then exit\n" % (UMLassociated)
                        modification =True
                        
            # 1.1.2 Analyse the missing processes
            for i in range(0, len(OldListOfUML)-1):            
                if not OldListOfUML[i][2] in  ListOfUML:            
                    ##### Type of  process ######
                    value =OldListOfUML[i][1] 
                    if value =="/sbin/initlog":
                        # Sometimes, two process initlog can be started for 
                        # the same UML , in order not to post the information 
                        # twice, the process initlog with the lowest pid 
                        #is selected
                        if (OldListOfUML[i][2] == minPID(value,OldListOfUML,OldListOfUML[i][0])):
                            print "\tUML :", OldListOfUML[i][0], " ... UML has booted \n"
                            string = string + "\t\tUML :%s ... UML has booted\n" % (OldListOfUML[i][0])
                            modification =True
                    if value =="/usr/sbin/sshd": 
                        print "\tUML :", OldListOfUMListumlAliveL[i][0], "... UML is Running : End of communication via ssh between UML and host\n"
                        string = string +"\t\tUML :%s ... UML is Running :End of communication via ssh between UML and host\n" %(OldListOfUML[i][0])
                        modification =True  
                        
            # 1.1.3 Analyse the running UML     
            # check : compare the current and the old list of UML
            for k in range(0, len(oldListumlAlive)-1):
                # Post on the interface "UML was killed" only once:
                if not (oldListumlAlive[k] in umlAlive):
                    if not (oldListumlAlive[k] in buflist):
                        print "\tUML :", ListumlAlive[k] , "was killed"
                        string = string +"\t\tUML :%s was killed\n"% (oldListumlAlive[k])   
                        modification =True
                    else :     
                        buflist.append(oldListumlAlive[k])  
                     
        # No UML is runing  : New list of UML is empty
        else:
            for k in range(0, len(oldListumlAlive) -1):
                if not (oldListumlAlive[k] in umlAlive):
                    print "\tUML :", ListumlAlive[k] , "was killed"
                    string = string +"\t\tUML :%s was killed \n" % (oldListumlAlive[k])   
                    modification =True   

    # No UML is  running 
    else :
        string = string+"\n\t\tNo UML is Running\n"
        modification = True
    # 2. Alarm  gbuilder of asynchrous events       
    if modification : 
        #2.1. Write in the pipe 
        os.write(tubeGiniSuperviserW, string)
        #2.2.  Send a signal to gbuilder to refresh its interface 
        #os.kill(ppid, signal.SIGUSR2) 
    #3. return the new list 
    return ListOfUML,umlAlive
    
#### -------------- MAIN start ----------------####
# 1. Check if UML or Router are still running [OK]
# 2. Indicate their status to the interface   [KO] duplicated msgs 
#    and uml dying is not implemented

def start(tubeGiniSuperviserW):
    #0. Test / Infos
    
    pid=os.getpid()
    print "\nPid du superviser NUMBER 2! [", pid , "]"
    ppid =os.getppid()
    username=whoAmI()
    print "username: ", username, "\n"
    inFile = open("PidGiniSuperviser.txt", "w")
    inFile.write(str(os.getpid()))
    inFile.close()    
    
    #signal.signal(signal.SIGUSR1, handler)  
    #1. Initialization 
    CurrentListOfRouter = []
    CurrentListOfUML = []
    ListumlAlive=[]
    #### TO DO crreer une fonction init a la place de start pour separer 
    #  init de gini superviser et  le demarrage de la surveillance
    time.sleep(5)
  
    # Loop  : superviser
    while 1:
        CurrentListOfRouter=checkRouter(CurrentListOfRouter, username, ppid, \
                                        tubeGiniSuperviserW) 
        (CurrentListOfUML, ListumlAlive)=checkUML(CurrentListOfUML,\
                                                  ListumlAlive,username, ppid,\
                                                  tubeGiniSuperviserW)        

        

    