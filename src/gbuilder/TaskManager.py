#!/usr/bin/python
# Written by Daniel Ng

from Tkinter import *
from tkMessageBox import *
import Pmw
import Pyro.core
import sys
import thread
import time
import os
import signal 

procdic = {}
last_selected = None
iconified = False
focused = False

# handle the X on the window
def tmcloseHandle():
    global iconified
    sys.stdout = open("/dev/null", "w")
    tm = Pyro.core.getProxyForURI(uri2)
    sys.stdout = sys.__stdout__ 
    #set the state of the Task Manager to closed
    tm.set_state(False)
    iconified = False
    root.withdraw()

# remember last selected value
def set_last_selected():
    global last_selected
    last_selected = pidbox.getvalue()

def attach(value):
    parts = value.split(' ')
    if parts[0].find("WAP") >= 0:
        parts[0] = "V" + parts[0]
    scr_command = "screen -r -S %s" % parts[0]
    term_command = "xterm -T %s -e %s &" % (parts[0], scr_command)
    os.system(term_command)

def detach(value):
    parts = value.split(' ')
    if parts[0].find("WAP") >= 0:
        parts[0] = "V" + parts[0]    
    os.system("screen -d %s" % parts[0])

# handles right click event in task list
def right_click(event):
    global focused
  
    index = pidbox.nearest(event.y)
    value = pidbox.get(index)
    if value:
        pidbox.setvalue([value])
        pop_menu = Menu(root, tearoff=0)
        pop_menu.add_command(label="Kill", command = kill_task)
        if not value.find("Switch") >= 0:
            pop_menu.add_command(label="Attach", command = lambda: attach(value))        
            pop_menu.add_command(label="Detach", command = lambda: detach(value))
        pop_menu.tk_popup(event.x_root, event.y_root)
        thread.start_new(keep_focused, ())
        set_last_selected()
    

# handles double click event in task list
def kill_task():
    global focused

    try:
        #get the device name from the list
        name = pidbox.getvalue()[0].split(' ')[0]
    except:
        return 

    thread.start_new(keep_focused, ())
    answer = askyesno("kill?", name)
    if answer:    
        proc = procdic[name]
        #kill according to if it is run locally or remotely
        if not name.find("Switch") >= 0:
            os.kill(int(proc[0]), signal.SIGTERM)
            #kill the interpreter as well            
            if name.find("WAP") >= 0:
                try:
                    os.kill(int(procdic["V"+name][0]), signal.SIGTERM)
                except:
                    pass
        else:
            if proc[1] == os.getenv("USER") or proc[1] == "localhost":
                command = "kill %s" % (proc[0])
            else:
                command = "ssh %s kill %s" % (proc[1], proc[0])
            os.system(command)

def kill_all():
    answer = askyesno("Kill All?", "Do you really want to kill everything?")
    if answer:
        for name,proc in procdic.iteritems():
            if not name.find("Switch") >= 0:
                os.kill(int(proc[0]), signal.SIGTERM)
                #kill the interpreter as well            
                if name.find("WAP") >= 0:
                    try:
                        os.kill(int(procdic["V"+name][0]), signal.SIGTERM)
                    except:
                        pass
            else:
                if proc[1] == os.getenv("USER") or proc[1] == "localhost":
                    command = "kill %s" % (proc[0])
                else:
                    command = "ssh %s kill %s" % (proc[1], proc[0])
                os.system(command)                 

# changes the painted lights on devices according to state 
def refresh_state(device, new_state):
    sys.stdout = open("/dev/null", "w")
    gw = Pyro.core.getProxyForURI(uri)
    sys.stdout = sys.__stdout__     
    state = new_state.strip("()")
    gw.createMsgStatus(device, state)
#    gw.setState(device, state)

# refreshes the task manager for processes associated with the topology
def refresh_tm():
    global last_selected
    global iconified
    global focused

    #keep Pyro initialization quiet
    sys.stdout = open("/dev/null", "w")
    gw = Pyro.core.getProxyForURI(uri)
    tm = Pyro.core.getProxyForURI(uri2)
    sys.stdout = sys.__stdout__ 
    #to keep track of processes that might have been killed outside of gbuilder    
    proclist = []
    proc_checked = {}
    proc_hosts = {}
    proc_killed = {}
    proc_filter = ["WAP_","VWAP_","UML_","Router_","Mobile_"]

    while 1:           
        #find processes from screen's manager            
        os.system("screen -wipe > screenPID")
        screenIn = open("screenPID", "r")
        lines = screenIn.readlines()
        screenIn.close()
        os.system("rm screenPID")  
      
        # shift new ovals into old ovals
        gw.shiftOvals()       

        for i in range(1, len(lines)-2):
            line = lines[i].split()
            parts = line[0].split(".")
            if len(parts) != 2:
                continue
            # check that it is a gini component
            found = False
            for ele in proc_filter:
                if parts[1].find(ele) >= 0:
                    found = True
                    break
            if not found:
                continue

            if not proc_hosts.has_key(parts[1]):
                proc_hosts[parts[1]] = "localhost"
            #input entries into process dictionary in the format procdic[device name] = (PID, host)
            procdic[parts[1]] = (parts[0], proc_hosts[parts[1]])
                
            #refresh the state of the lights
#            refresh_state(parts[1], line[1])
            try:
                gw.createMsgStatus(parts[1], line[1].strip("()"))
            except Exception, inst:
                print type(inst)
                print inst
                print inst.args
            proc_checked[parts[1]] = True
            
        #find processes that did not get checked, most likely killed from outside
        for key, value in proc_checked.iteritems():
            if not proc_checked[key]:
                proc_killed[key] = procdic[key]
                del procdic[key]
            elif proc_killed.has_key(key):
                del proc_killed[key]
        
        for key, value in proc_killed.iteritems():
#            refresh_state(key, "killed")  
            gw.createMsgStatus(key, "killed")
                        

        # get rid of the old ones after new ones are painted
        gw.cleanOvals()

        #print tm.get_initialized()             
        other_proc = tm.get_procdic()
        #check if uswitches are still alive and update hosts of other devices
        for key, value in tm.get_procdic().iteritems():
            if key.find("Switch") >= 0:
                if value[1] == "localhost":            
                    # see if the switch is still alive                    
                    try:
                        os.kill(int(value[0]), 0)
                    except Exception, inst:
                        try:
                            del other_proc[key]
                            del procdic[key]
                        except:
                            pass
                else:
                    # see if the switch is still alive
                    if os.system("ssh %s kill -0 %s 2> /dev/null" % (value[1], value[0])) != 0:
                        try:
                            del other_proc[key]
                            del procdic[key]
                        except:
                            pass
            else:
                proc_hosts[key] = value[1]                    
                del other_proc[key]
                    
        #update the dictionary of other processes
        tm.set_procdic(other_proc)
        #append other processes to current process dictionary        
        procdic.update(other_proc)

        proc_checked.clear()
        for key, value in procdic.iteritems():
            #switches are already checked separately
            if key.find("Switch") >= 0:
                proclist.append("%s%s%s" % (key.ljust(15), value[1].ljust(27), value[0].ljust(10)))
            #dont display WAP interpreter process
            elif key.find("VWAP") >= 0:
                proc_checked[key] = False
                continue
            else:
                proc_checked[key] = False
                if value[1] == "localhost":
                    proclist.append("%s%s%s" % (key.ljust(15), value[1].ljust(27), value[0].ljust(10)))
                else:
                    proclist.append("%s%s%s" % (key.ljust(15), value[1].ljust(27), (value[0]+" (local)").ljust(10)))
      
        # if task manager is open
        if tm.get_state():
            # if not already showing, show
            if not iconified:
                root.deiconify()
                iconified = True
            elif tm.get_focus_requested():
                root.focus_force()
                tm.set_focus_requested(False)
                
            # refresh the list of tasks       
            pidbox.setlist(proclist) 
            if focused:
                try:
                    # try selecting the same pid as before the refresh
                    if last_selected:
                        pidbox.setvalue(last_selected)
                except Exception, inst:
                    last_selected = None

            if tm.get_close_requested():
                if not proclist:
                    time.sleep(1)
                    tmcloseHandle()
                    tm.set_close_requested(False)        

        del proclist[:]

        # if topology is stopped  
        if not tm.get_initialized():
            gw.cleanStates()
            if proc_hosts:
                proc_hosts.clear()
            elif proc_killed:
                proc_killed.clear()              
        time.sleep(1)

def check_umls():
    umldir = "$HOME/.uml/"
    while 1:
        udirs = os.listdir(umldir)
        for udir in udirs:
            if os.access(umldir+udir+"", os.F_OK):
                pass
            
def set_focused(focus):
    global focused
    focused = focus

def keep_focused():
    time.sleep(0.1)
    set_focused(True)

def unselect(event = None):
    global last_selected
    last_selected = None
    pidbox.selection_clear()


#get uris for Pyro 
uriIn = open("%s/tmp/pyro_uris" % os.environ["GINI_HOME"], "r")
uri = uriIn.readline().strip()
uri2 = uriIn.readline().strip()
uriIn.close()

root = Tk()
Pmw.initialise(root)    
root.minsize(400, 500)
root.title("Task Manager")
root.protocol('WM_DELETE_WINDOW', tmcloseHandle)

pidbox = Pmw.ScrolledListBox(root, labelpos='nw', label_text="%s%s%s" % ("Device Name".ljust(19), "Host".ljust(45), "PID".ljust(15)), usehullsize = 1, hull_width = 400, hull_height = 475, dblclickcommand=kill_task, selectioncommand=set_last_selected)
pidbox.component("listbox").configure(font="monospace 10")
pidbox.component('listbox').bind("<ButtonRelease-3>", right_click)
pidbox.pack()

#root.protocol('WM_TAKE_FOCUS', set_focused)
root.bind("<FocusIn>", lambda e: set_focused(True))
root.bind("<FocusOut>", lambda e: set_focused(False))

buttons=Pmw.ButtonBox(root)
buttons.pack()
buttons.add("kill", command=kill_task)
buttons.add("killall", command=kill_all)

root.withdraw()
thread.start_new(refresh_tm, ())
#thread.start_new(check_umls, ())
root.mainloop()
    
