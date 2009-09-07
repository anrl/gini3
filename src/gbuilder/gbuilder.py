#!/usr/bin/python
# Revised by Daniel Ng

title='GINI Builder 1.06'

from Tkinter import *
import Pmw
import os, signal, sys
import tkFileDialog
import pickle
import tkMessageBox
from UML_machine import *
from Router import *
from Switch import *
from Wireless_access_point import *
from Subnet import *
from Mobile import *
from Connection import *
from Wireless_Connection import *
from TopologyCompiler import *
from Routing import *

# Future plans
from Firewall import *
#from Bridge import *
#from Hub import *

# Unused (old modules)
#from Animate_Mobile import *
#from giniSuperviser3 import *
#import giniSuperviser3

import thread       # to do multithtreading : fisrt step
import time         # to differ starting
import threading    # class to do multithtreading

# Pyro used to communicate between gbuilder and taskmanager
import Pyro.core
from Pyro.errors import PyroError,NamingError

# enable auto computing route tables by default
auto_routing=1

# disable auto generating mac and ip addresses by default
autogen = False

# enable tips by default
tips = True

# current kernel used to run UMLs
uml_kernel = "linux-2.6.26.1"

################################################################################
# define connection rules
# only devices in the list are connectable
connection_rule={}
connection_rule[UML_machine.type]=(Switch.type, Subnet.type, Bridge.type, Hub.type, Wireless_access_point.type)
connection_rule[Router.type]=(Subnet.type, Wireless_access_point.type)
connection_rule[Switch.type]=(UML_machine.type, Subnet.type)
connection_rule[Bridge.type]=(UML_machine.type, Subnet.type)
connection_rule[Hub.type]=(UML_machine.type, Subnet.type)
connection_rule[Wireless_access_point.type]=(UML_machine.type, Mobile.type, Router.type)
connection_rule[Subnet.type]=(UML_machine.type, Switch.type, Router.type, Bridge.type, Hub.type, Firewall.type)
connection_rule[Mobile.type]=(Wireless_access_point.type)
connection_rule[Firewall.type]=(Subnet.type)
 
################################################################################

##
# Class: ControlPanel. Control GUI and respond to user input
class ControlPanel:
    
    ##
    # Constructor: create the the menu, the control pannel, the canvas, and the compile panel
    # @param master the root window of the GUI
    # @param basedir the current working dir
    def __init__(self, master, basedir):

        self.parent=master
        self.basedir=basedir
        self.balloon = Pmw.Balloon(master)  # create the balloon help
   
        menubar = Menu(master)  # create the menu 

        # the file menu
        filemenu=Menu(menubar, tearoff=0)
        filemenu.add_command(label="New     (Ctrl+N)", command=self.new)
        filemenu.add_command(label="Open... (Ctrl+O)", command=self.Open)
        filemenu.add_separator()
        filemenu.add_command(label="Save    (Ctrl+S)", command=self.save)
        filemenu.add_command(label="Save as...", command=self.save_as)
        filemenu.add_separator()
        filemenu.add_command(label="Close   (Ctrl+W)", command=self.close)

        # the clean menu within the file menu
        cleanMenu=Menu(filemenu, tearoff=0)
        cleanMenu.add_command(label="Clean XML", command=self.cleanXML)
        cleanMenu.add_command(label="Clean up", command=self.cleanUp)
        cleanMenu.add_command(label="Clean cow", command=self.cleanCow)
        cleanMenu.add_command(label="Clean mconsole", command=self.cleanUML_console)
                
        filemenu.add_cascade(label="Clean", menu=cleanMenu)
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)        
        
        # the compile menu
        compilemenu=Menu(menubar, tearoff=0)
        compilemenu.add_command(label="Compile (Ctrl+E)", command=self.compile)
        menubar.add_cascade(label="Compile", menu=compilemenu)
    
        # the build menu
        runmenu=Menu(menubar, tearoff=0)
        runmenu.add_command(label="Run     (Ctrl+R)", command=self.run)
        runmenu.add_command(label="Run remotely", command=self.run_remote)
        runmenu.add_command(label="Stop    (Ctrl+D)", command=self.stop)
        runmenu.add_command(label="Start Task Manager  (Ctrl+T)", command=self.manage)
        menubar.add_cascade(label="Run", menu=runmenu)
            
        # the Env config menu
        configmenu=Menu(menubar, tearoff=0)
        configmenu.add_command(label="Environment Configuration...", command=self.config)
        configmenu.add_command(label="Toggle IP/MAC Auto-gen  (Ctrl+A)", command=self.toggleAutogen)        
        configmenu.add_command(label="Toggle Auto-routing", command=self.toggleAutoroute)
        configmenu.add_command(label="Remote Distribution...", command=self.remote_dist)
        menubar.add_cascade(label="Config", menu=configmenu)
    
        # the help menu
        helpmenu=Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Toggle tips", command=self.toggle_tips)
        helpmenu.add_separator()
        helpmenu.add_command(label="About...", command=self.about)
        menubar.add_cascade(label="Help", menu=helpmenu)        

        master.config(menu=menubar)

        # pop out frame corresponding to mouse right click on a router
        self.pop_menu_Router=Menu(master, tearoff=0)
        self.pop_menu_Router.add_command(label="Delete", command=self.delete)
        self.pop_menu_Router.add_separator()
        self.pop_menu_Router.add_command(label="Restart", command=self.restart)
        self.pop_menu_Router.add_command(label="Stop", command=self.kill)
        self.pop_menu_Router.add_command(label="Graph", command=self.graph)
        self.pop_menu_Router.add_command(label="Wireshark", command=self.wireshark)
        self.pop_menu_Router.add_separator()    
        self.pop_menu_Router.add_command(label="Properties...", command=self.edit)
        
        # pop out frame corresponding to mouse right click on a WAP
        self.pop_menu_WAP=Menu(master, tearoff=0)
        self.pop_menu_WAP.add_command(label="Delete", command=self.delete)
        self.pop_menu_WAP.add_separator()
        self.pop_menu_WAP.add_command(label="Restart", command=self.restart)
        self.pop_menu_WAP.add_command(label="Stop", command=self.kill)
        self.pop_menu_WAP.add_separator()    
        self.pop_menu_WAP.add_command(label="Properties...", command=self.edit)

        # pop out frame corresponding to mouse right click on an UML
        self.pop_menu_UML=Menu(master, tearoff=0)
        self.pop_menu_UML.add_command(label="Delete", command=self.delete)
        self.pop_menu_UML.add_separator()
        self.pop_menu_UML.add_command(label="Reboot", command=self.restart)
        self.pop_menu_UML.add_command(label="Stop", command=self.kill)
        self.pop_menu_UML.add_separator()
        self.pop_menu_UML.add_command(label="Properties...", command=self.edit)

        # pop out frame corresponding to mouse right click : default case
        self.pop_menu_default=Menu(master, tearoff=0)
        self.pop_menu_default.add_command(label="Delete", command=self.delete)
        self.pop_menu_default.add_separator()
        self.pop_menu_default.add_command(label="Properties...", command=self.edit)

#------------------------------------------------------------------------------ 
        
        # a frame contains all supported UML components
        component_frame=Frame(master)
        component_frame.pack(side=TOP, expand=0, fill='x')
        c_label=Label(component_frame, text="Add component to UML topology:")
        c_label.pack(side=LEFT, padx=5, pady=3)

        # all the supported devices
        self.support_device=([UML_machine, self.add_UML], 
                             [Router, self.add_router], 
                             [Switch, self.add_switch], 
                             #[Bridge, self.add_bridge], 
                             #[Hub, self.add_hub], 
                             [Firewall, self.add_firewall], 
                             [Mobile, self.add_mobile], 
                             [Wireless_access_point, self.add_wireless], 
                             [Subnet, self.add_subnet], 
                             [Tag, None], 
                             [Connection, None], 
                             [Wireless_Connection, None])

        # define photos for different devices, both the thumbnail and the original,
        # then create a set of buttons for all supported devices 
        self.photos={}
        self.device_buttons={}

        for device in self.support_device:
            if device[0].type != "tag" and device[0].type != "connection" and device[0].type != "wireless_connection":
                thumbnail=PhotoImage(file=self.basedir+"/gif/"+device[0].type+"_b.gif")
                original=PhotoImage(file=self.basedir+"/gif/"+device[0].type+".gif")
                self.photos[device[0].type]=[thumbnail, original]
                self.device_buttons[device[0]]=Button(component_frame, image=self.photos[device[0].type][0], 
                                                      borderwidth=0, height=32, width=32, #bg="GRAY", 
                                                      activebackground="GRAY", 
                                                      command=device[1])
                self.device_buttons[device[0]].pack(side=LEFT, pady=3)

                # add help info to each button
                self.balloon.bind(self.device_buttons[device[0]], device[0].type)
        
        def printstats():
            print self.current_view.geometry()

#        Button(component_frame, command=printstats, text="debug").pack()

        # define all support possible modes
        self.modes={}
        self.modes[UML_machine.type]=1             # indicates adding UML machine mode
        self.modes[Router.type]=2                  # indicates adding router mode
        self.modes[Switch.type]=3                  # indicates adding switch mode
        self.modes[Connection.type]=4              # indicates adding connection mode
        self.modes["moving"]=5                     # indicates in moving mode
        self.modes["editing"]=6                    # indicates in editing mode
        self.modes[Bridge.type]=7                  # indicates adding bridge mode
        self.modes[Hub.type]=8                     # indicates adding hub mode
        self.modes[Firewall.type]=9                # indicates adding firewall mode
        self.modes[Wireless_access_point.type]=10        # indicates adding wireless router mode
        self.modes[Mobile.type]=11                 # indicates adding mobile mode
        self.modes[Subnet.type]=12                   # indicate adding subnet mode
        self.modes["select"]=0                     # indicates selecting object mode
        self.modes["screen"]=13                    # indicates xterm popup mode


        # create two panes
        self.pw = Pmw.PanedWidget(master, 
                                  orient='vertical', 
                                  hull_borderwidth = 2, 
                                  hull_relief = 'sunken', 
                                  hull_width=800, 
                                  hull_height=800)
        self.pw.pack(expand = 1, fill='both')
        self.canvas_pane=self.pw.add("canvaspane", min = 300, size = 600)
        self.log_pane=self.pw.add("logpane", min=50, size=150)

        # a verbose log field
        self.log=Pmw.ScrolledText(self.log_pane, text_state='disabled', borderframe=2, 
                                  usehullsize = 1, hull_width=800, hull_height=100)
        self.log.pack(expand=1, padx=5, pady=5, fill='both')

        sx = self.parent.winfo_screenwidth()
        sy = self.parent.winfo_screenheight()
        self.parent.geometry("+%d+%d" % ((sx-800)/2, (sy-800)/2))
        self.parent.update_idletasks()        

        # uris needed for pyro
        self.uri=""
        self.uri2=""

        self.remote = False         # to determine when running remotely
        self.running = False        # to determine when running
        
        # forces child windows to keep focus
        def focus_child(e):
            if self.current_view != None:
                self.current_view.focus_force()
                self.current_view.lift()
    
        self.current_view = None                    # keep track of current window
        self.parent.bind("<FocusIn>", focus_child)  # bind root focus to focus on child instead

        self.view_mobiles = {}          # holds the mobile stats pop-up windows
        self.current_mobile = None      # for interactive mobile info
        self.ready = False              # ready to show mobile stats         
        
        self.init_condition() 

        global tips        

        # read from tips file to see if they are enabled or disabled
        tipFile = "%s/etc/tips" % os.environ["GINI_HOME"]
        if os.access(tipFile, os.F_OK):
            tipsIn = open(tipFile, "r")
            if tipsIn.readline().strip() == "1":
                tips = True
            else:
                tips = False
        else:
            tipsIn = open(tipFile, "w")
            if tips:
                tipsIn.write("1")
            else:
                tipsIn.write("0")
        tipsIn.close()
        if tips:
            self.show_tips(self.parent, "To begin, choose the component of your choice by clicking once and place it on the canvas by clicking again.  You can place multiple instances of the same component until you choose another.  You can stop placing instances by right clicking once, and you can connect different instances by holding right click from one component and dragging to another component before releasing.  Components can always be moved whether they are connected or not by clicking and dragging while not in placing mode.  They can be configured through 'Properties' in the right click menu.")      


    ##
    # Initial system parameters
    def init_condition(self):

        self.object_list={}     #initialize the object list in the canvas
        self.connection_list=[] #the connection list, used to prevent duplicate connections        
        self.counter={}         #initialize the counter for each type of objects in canvas
        
        for obj in self.support_device:
            self.counter[obj[0].type]=1

        self.current_obj=None   #current object in canvas
        self.filename=""        #current file to work with, defined by save/load 
        self.rdfilename = ""    #current remote distribution file

        # default environment configurations
        giniEnv = os.environ["GINI_HOME"]
        self.dtd_filename="%s/etc/gloader.dtd" % giniEnv
        self.fs_filename="%s/root_fs_beta2" % giniEnv
        
        self.property_page={}                       #routing table properties page
        self.current_func=self.modes["select"]      #initial mode

        # a frame to contain the canvas
        self.s_canvas=Pmw.ScrolledCanvas(self.canvas_pane, borderframe=2, usehullsize = 1, 
                                         hull_width=800, hull_height=600)      
        self.s_canvas.pack(padx = 5, pady = 5, fill = 'both', expand = 1)
        self.canvas=self.s_canvas.interior()
        self.canvas.config(bg="WHITE")
        self.ping=self.canvas.create_arc(0, 0, 1, 1)

        self.bind_event()   # bind all events with canvas        
        self.log.clear()


    ##
    # Define all mouse and keyboard event and bind them to the canvas
    def bind_event(self):

        # all mouse events we handle
        self.canvas.bind("<Button-1>", self.button_1_down)
        self.canvas.bind("<Button-3>", self.button_3_down)
        self.canvas.bind("<ButtonRelease-1>", self.button_1_up)
        self.canvas.bind("<Double-Button-1>", self.screen_attach_popup)
        self.canvas.bind("<ButtonRelease-3>", self.button_3_up)
        self.canvas.bind("<B1-Motion>", self.button_1_drag)
        self.canvas.bind("<B3-Motion>", self.button_3_drag)
        self.canvas.bind("<Delete>", self.delete)
        self.canvas.bind("<Motion>", self.detect)

        self.parent.bind("<Control-s>", self.save)
        self.parent.bind("<Control-o>", self.Open)
        self.parent.bind("<Control-w>", self.close)
        self.parent.bind("<Control-e>", self.compile)
        self.parent.bind("<Control-r>", self.run)
        self.parent.bind("<Control-t>", self.manage)
        self.parent.bind("<Control-d>", self.stop)
        self.parent.bind("<Control-n>", self.new)
        self.parent.bind("<Control-a>", self.toggleAutogen)

    ##
    # unbind some mouse and keyboard event from the canvas
    def unbind_event(self):

        # disable mouse event
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<Button-3>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<ButtonRelease-3>")
        self.canvas.unbind("<Double-Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<B3-Motion>")
        self.canvas.unbind("<Delete>")


    ##    
    # Convert screen coordinates to canvas coordinates
    # @param x the x coordinate of the screen
    # @param y the y coordinate of the screen
    # @return (cx, cy) the corresponding coordinate in the canvas
    def convert(self, x, y):
        cx=self.canvas.canvasx(x)
        cy=self.canvas.canvasy(y)
        return (cx, cy)


    ##
    # Define the behaviour of draging left button of the mouse
    # @param event draging left button event
    def button_1_drag(self, event):        

        obj_id=self.find_by_range(event.x, event.y)

        #find the object pointed by mouse
        if self.current_func == self.modes["select"]:
            if obj_id != None:
                self.current_obj=(obj_id, self.object_list[obj_id])
                self.current_func=5
        
        if self.current_func== self.modes["moving"]:
        
            # only allow moving of Mobile devices
            if self.running and self.current_obj[1].type != "Mobile":
                return

            self.s_canvas.config(cursor='diamond_cross')
            id=self.current_obj[0]
        
            #drag the object to new position
            lastx, lasty=self.current_obj[1].get_coord()  
            cx, cy=self.convert(event.x, event.y)
            self.canvas.move(id, cx-lastx, cy-lasty)        
            self.object_list[id].update_coord(cx, cy)
            cx_n, cy_n=self.object_list[id].get_coord()
        
            #move the tag together
            tag_id=self.canvas.find_withtag(self.current_obj[1].get_tag().get_name())[0]
            self.canvas.move(tag_id, cx-lastx, cy-lasty)
            self.object_list[tag_id].update_coord(cx, cy)
        
            #move oval along with Mobile
            if self.running:
                gw = Pyro.core.getProxyForURI(self.uri)
                self.canvas.move(gw.getOval(self.current_obj[1].name), cx-lastx, cy-lasty)

            #update all connections that connect with this device
            con_list=self.current_obj[1].get_connection()[:]
    
            #special case: wireless router has two typies of connections
            if self.current_obj[1].type == "Wireless_access_point":
                con_list+=self.current_obj[1].get_wireless_connection()[:]    
            
            for con in con_list:
                
                #back up the info of the connection
                current_name=self.current_obj[1].get_name()
                c_id=self.canvas.find_withtag(con.get_name())[0]
                c_name=con.get_name()
                c_dev_s=con.get_start_device()
                c_dev_e=con.get_end_device()
                s_id=self.canvas.find_withtag(c_dev_s)[0]
                e_id=self.canvas.find_withtag(c_dev_e)[0]
                cx_e, cy_e=self.object_list[e_id].get_coord()
                cx_s, cy_s=self.object_list[s_id].get_coord()
                self.canvas.delete(c_id)    
                
                #find out which end need to be updated and create a new connection
                if current_name == c_dev_s:
                    if con.type == "wireless_connection":
                        obj_id=self.canvas.create_line(cx, cy, cx_e, cy_e, fill="GRAY", width=3, tag=c_name, dash=15)
                    else:
                        obj_id=self.canvas.create_line(cx, cy, cx_e, cy_e, fill="GRAY", width=3, tag=c_name)
                    self.object_list[c_id].update_start_point(cx, cy)
    
                else:
                    if con.type == "wireless_connection":
                        obj_id=self.canvas.create_line(cx_s, cy_s, cx, cy, fill="GRAY", width=3, tag=c_name, dash=15)
                    else:
                        obj_id=self.canvas.create_line(cx_s, cy_s, cx, cy, fill="GRAY", width=3, tag=c_name)
                    self.object_list[c_id].update_end_point(cx, cy)
    
                del self.object_list[c_id]
                self.object_list[obj_id]=con
                self.canvas.lower(obj_id)
            self.s_canvas.resizescrollregion()


    ##
    # Define the behaviour of mouse's left button down
    # @param event the left button down event
    def button_1_down(self, event):

        #add a UML machine 
        if self.current_func == self.modes[UML_machine.type]:
            cx, cy=self.convert(event.x, event.y)

            # create the machine and the tag
            t=UML_machine.type
            new_machine=UML_machine(cx, cy, self.counter[UML_machine.type], self.counter[Tag.type])

            # create them in the canvas
            self.draw_device(new_machine, cx, cy)
        
        #add a router
        elif self.current_func == self.modes[Router.type]:
            cx, cy=self.convert(event.x, event.y)

            # create the router and the tag
            new_router=Router(cx, cy, self.counter[Router.type], self.counter[Tag.type])
        
            # create them in the canvas
            self.draw_device(new_router, cx, cy)
        
        #add a switch
        elif self.current_func == self.modes[Switch.type]:
            cx, cy=self.convert(event.x, event.y)

            # create switch and tag
            new_switch=Switch(cx, cy, self.counter[Switch.type], self.counter[Tag.type])
        
            # draw them in the canvas
            self.draw_device(new_switch, cx, cy)
        
        #add a bridge
        elif self.current_func == self.modes[Bridge.type]:
            cx, cy=self.convert(event.x, event.y)
        
            # create switch and tag
            new_bridge=Bridge(cx, cy, self.counter[Bridge.type], self.counter[Tag.type])
        
            # draw them in the canvas
            self.draw_device(new_bridge, cx, cy)
        
        #add a hub
        elif self.current_func == self.modes[Hub.type]:
            cx, cy=self.convert(event.x, event.y)

            # create switch and tag
            new_hub=Hub(cx, cy, self.counter[Hub.type], self.counter[Tag.type])
        
            # draw them in the canvas
            self.draw_device(new_hub, cx, cy)
        
        #add a subnet
        elif self.current_func == self.modes[Subnet.type]:
            cx, cy=self.convert(event.x, event.y)
        
            # create switch and tag
            new_subnet=Subnet(cx, cy, self.counter[Subnet.type], self.counter[Tag.type])
        
            # draw them in the canvas
            self.draw_device(new_subnet, cx, cy)
        
        #add a firewall
        elif self.current_func == self.modes[Firewall.type]:
            cx, cy=self.convert(event.x, event.y)
        
            # create switch and tag
            new_firewall=Firewall(cx, cy, self.counter[Firewall.type], self.counter[Tag.type])
        
            # draw them in the canvas
            self.draw_device(new_firewall, cx, cy)
        
        #add a mobile
        elif self.current_func == self.modes[Mobile.type]:
            cx, cy=self.convert(event.x, event.y)

            # create switch and tag
            new_mobile=Mobile(cx, cy, self.counter[Mobile.type], self.counter[Tag.type])
            
            # draw them in the canvas
            self.draw_device(new_mobile, cx, cy)
        
        #add a wireless router
        elif self.current_func == self.modes[Wireless_access_point.type]:
            cx, cy=self.convert(event.x, event.y)
        
            # create switch and tag
            new_wireless=Wireless_access_point(cx, cy, self.counter[Wireless_access_point.type], self.counter[Tag.type])
        
            # draw them in the canvas
            self.draw_device(new_wireless, cx, cy)


    ##
    # draw a object on the canvas
    # @param obj the object to draw
    # @param x the x coordinate of the location to draw
    # @param y the y coordinate of the location to draw
    def draw_device(self, obj, x, y):

        # draw them on the canvas
        obj_tag=obj.get_name()
        object_id=self.canvas.create_image(x, y, image=self.photos[obj.type][1], tag=obj_tag)
        self.balloon.tagbind(self.canvas, object_id, obj.balloon_help())
        
        t_tag=obj.get_tag().get_name()
        cx, cy, re_y=obj.get_tag().get_coord()
        tag_id=self.canvas.create_text(cx, cy+re_y, text=obj_tag, tag=t_tag)
        self.s_canvas.resizescrollregion()
        
        # update counter
        self.counter[obj.type]+=1
        self.counter[Tag.type]+=1
        
        # add machine and tag into the canvas object list
        self.object_list[object_id]=obj 
        self.object_list[tag_id]=obj.get_tag()
              

    ##
    # Define the behaviour of mouse's right button down
    # @param event the right button down event
    def button_3_down(self, event):
        if self.current_func != self.modes["moving"] and self.current_func != self.modes["editing"]:
            self.current_func=self.modes["select"] 


    ##
    # Define the behaviour of mouse's left button up
    # @param event the left button up event
    def button_1_up(self, event):
        if self.current_func==self.modes["moving"]:
            if self.current_obj[1].type == "Mobile":
                mobile = self.current_obj[1]                
                if self.running:
                    wapIn = open("%s/data/mobile_data/Wireless_access_point_1.data" % os.environ["GINI_HOME"], "r")
                    line = wapIn.readline()
        
                    # scale the coordinates to match the wap
                    relx = int(line.split(",")[0]) / 4
                    rely = int(line.split(",")[1]) / 4
                    x = (mobile.x / 4) - relx
                    y = (mobile.y / 4) - rely 

                    # propogate the change to the real wireless_access_point
                    os.system("screen -S WAP_1 -X eval 'stuff \"mov set node %s location %d %d 0\"\\015'" \
                                % (mobile.name.split("Mobile_")[-1], x, y))
                # update the balloon popup
                self.balloon.tagbind(self.canvas, self.current_obj[0], mobile.balloon_help())
            self.current_func=self.modes["select"]
            self.current_obj=None
            self.s_canvas.config(cursor='')
            self.s_canvas.resizescrollregion()

    ##
    # Define the behaviour of mouse's right button up
    # @param event the right button up event
    def button_3_up(self, event):
        self.s_canvas.config(cursor='')        
        
        #if this is the end of drawing new connection, check if the connection is valid or not
        #if so, add it to the object list, finalize the connection
        #else, popup a window, and delete the connection
        if self.current_func==self.modes[Connection.type]:
        
            #find the object pointed by mouse, which is the ending device of the connection        
            obj_id=self.find_by_range(event.x, event.y)
            if obj_id != None:
                e_id=obj_id                                              # connection end at this device
                s_tag=self.current_obj[1].get_start_device()
                s_id=self.canvas.find_withtag(s_tag)[0]                  # connection start at this device

                if e_id != s_id:
    
                    #check if such connection is already exist
                    if [self.object_list[s_id], self.object_list[e_id]] in self.connection_list or \
                        [self.object_list[e_id], self.object_list[s_id]] in self.connection_list:
    
                        msg="Connection between "+self.object_list[s_id].get_name()+" and "+self.object_list[e_id].get_name()+" already exists!"
                        tkMessageBox.showerror("Duplicate connections", msg)
                        self.canvas.delete(self.current_obj[0])
                        del self.object_list[self.current_obj[0]]
                        self.current_obj=None
    
                    # check connection rule, connection two device only if it is allowed.
                    # otherwise, issue an error msg
                    elif not self.validate_connection(self.object_list[s_id].type, self.object_list[e_id].type):
                        msg="Can not directly link "+self.object_list[e_id].type+" with "+self.object_list[s_id].type+"!"
                        tkMessageBox.showerror("Connection Error", msg)
                        self.canvas.delete(self.current_obj[0])
                        del self.object_list[self.current_obj[0]]
                        self.current_obj=None
    
                    # For UML, only one connection is allowed. 
                    # Otherwise, issue an error msg
                    elif (self.object_list[s_id].type == "UML" and self.object_list[s_id].hasOne() == 1) or \
                        (self.object_list[e_id].type == "UML" and self.object_list[e_id].hasOne() == 1):
                        msg="UML only allows one interface for now!"
                        tkMessageBox.showerror("Connection Error", msg)
                        self.canvas.delete(self.current_obj[0])
                        del self.object_list[self.current_obj[0]]
                        self.current_obj=None
    
    
                    # For Subnet, only two connections are allowed. 
                    # Otherwise, issue an error msg
                    elif (self.object_list[s_id].type == "Subnet" and len(self.object_list[s_id].get_connection()) == 2) or \
                        (self.object_list[e_id].type == "Subnet" and len(self.object_list[e_id].get_connection()) == 2):
                        msg="Subnet only allows two interfaces!"
                        tkMessageBox.showerror("Connection Error", msg)
                        self.canvas.delete(self.current_obj[0])
                        del self.object_list[self.current_obj[0]]
                        self.current_obj=None
    
                    # For a switch, it can only links with one subnet
                    # Otherwise, issue an error msg
                    elif (self.object_list[s_id].type == "Switch" and \
                          self.object_list[e_id].type == "Subnet" and \
                          self.object_list[s_id].hasOne() == 1) or \
                          (self.object_list[e_id].type == "Switch" and \
                           self.object_list[s_id].type == "Subnet" and \
                           self.object_list[e_id].hasOne() == 1):
                        msg="Switch can only link with one Subnet!"
                        tkMessageBox.showerror("Connection Error", msg)
                        self.canvas.delete(self.current_obj[0])
                        del self.object_list[self.current_obj[0]]
                        self.current_obj=None
     
                    # Finalize the link
                    else:
                        s_object = self.object_list[s_id]
                        e_object = self.object_list[e_id]

                        s_type = s_object.type
                        e_type = e_object.type

                        #remove the old line, redraw a new one end at the center of the device
                        x_s, y_s=s_object.get_coord()
                        x_e, y_e=e_object.get_coord()
                        self.canvas.delete(self.current_obj[0])
                        del self.object_list[self.current_obj[0]]
                        
                        s_ismobile = s_type == "Mobile"
                        e_ismobile = e_type == "Mobile"

                        #create a wireless connection if any device is a mobile
                        if s_ismobile or e_ismobile:
    
                            new_connection=Wireless_Connection(x_s, y_s, x_e, y_e, s_tag,self.counter[Wireless_Connection.type], self.counter[Tag.type]) 
                            c_tag=new_connection.get_name()
                            object_id=self.canvas.create_line(x_s, y_s, x_e, y_e, tag=c_tag, dash=15)
                            self.object_list[object_id]=new_connection
                            self.current_obj=(object_id, new_connection)
                                
                        else:
                            c_tag=self.current_obj[1].get_name()
                            object_id=self.canvas.create_line(x_s, y_s, x_e, y_e, tag=c_tag)
                        
                            #update the ending point of the connection
                            self.object_list[object_id]=self.current_obj[1]
                            self.object_list[object_id].update_end_point(x_e, y_e)
    
                        e_tag=e_object.get_name()
                        self.object_list[object_id].set_end_device(e_tag)                        
                        self.canvas.itemconfig(object_id, fill="GRAY", width=3)
                        
                        self.canvas.lower(object_id)
                        self.current_obj=None
    
                        #update counter
                        if s_ismobile or e_ismobile:
                            self.counter[Wireless_Connection.type]+=1
                        else:
                            self.counter[Connection.type]+=1
                        self.counter[Tag.type]+=1
    
                        #add the connection the two device
                        s_object.add_connection(self.object_list[object_id])
                        e_object.add_connection(self.object_list[object_id])       
                        
                        #add the new connection to connection list
                        self.connection_list.append([s_object, e_object])
                
                        #if connection is between UML and Subnet, force UML's ip to have Subnet's base address
                        if (s_type == "UML" and e_type == "Subnet"):
                            self.force_ip(s_object, e_object, 1)                      
                        elif (e_type == "UML" and s_type == "Subnet"):
                            self.force_ip(e_object, s_object, 1)
                        elif (e_type == "Router" and s_type == "Subnet"):
                            self.force_ip(e_object, s_object, 2)
                        elif (s_type == "Router" and e_type == "Subnet"):
                            self.force_ip(s_object, e_object, 3)                                           
                        
                        #do the same for subnets and UMLs between switches
                        elif (e_type == "UML" and s_type == "Switch"):
                            self.force_ip(e_object, s_object, 4)
                        elif (s_type == "UML" and e_type == "Switch"):
                            self.force_ip(s_object, e_object, 5)
                        elif (e_type == "Switch" and s_type == "Subnet"):
                            self.force_ip(e_object, s_object, 6)
                        elif (s_type == "Switch" and e_type == "Subnet"):
                            self.force_ip(s_object, e_object, 6)  
                        
                        #do the same for wireless routers and mobiles
                        elif (s_type == "Wireless_access_point" and (e_type == "Mobile" or e_type == "UML")):
                            self.force_ip(e_object, s_object, 7)
                        elif (e_type == "Wireless_access_point" and (s_type == "Mobile" or s_type == "UML")):
                            self.force_ip(s_object, e_object, 8)

                        #force mac address of Mobiles to correspond to the implementation of Wireless Router
                        if s_ismobile:
                            for inter in s_object.get_interface():
                                inter.req_properties["mac"] = "fe:fd:00:00:00:%02x" % s_object.num
                        elif e_ismobile:
                            for inter in e_object.get_interface():
                                inter.req_properties["mac"] = "fe:fd:00:00:00:%02x" % e_object.num
                          
                        self.balloon.tagbind(self.canvas, s_id, s_object.balloon_help())
                        self.balloon.tagbind(self.canvas, e_id, e_object.balloon_help()) 

                else:
                    self.canvas.delete(self.current_obj[0])
                    del self.object_list[self.current_obj[0]]
                    self.current_obj=None
            else:
                self.canvas.delete(self.current_obj[0])
                del self.object_list[self.current_obj[0]]
                self.current_obj=None
            self.current_func=self.modes["select"]
    
        #if not in adding connection mode, show the popup menu if mouse points to an object
        else:
            obj=self.canvas.find_withtag(CURRENT)
            try:
                if obj and self.object_list[obj[0]].get_type() != "tag":
                    id=obj[0]
                    self.current_obj=(id, self.object_list[id])
    #------------------------------------------------------------------------------                
                    type = self.current_obj[1].get_type()
                    if type == "UML" or type == "Mobile":
                        self.pop_menu_UML.tk_popup(event.x_root, event.y_root)            
                    elif type == "Router":
                        self.pop_menu_Router.tk_popup(event.x_root, event.y_root)
                    elif type == "Wireless_access_point":
                        self.pop_menu_WAP.tk_popup(event.x_root, event.y_root)
                    else:
                        self.pop_menu_default.tk_popup(event.x_root, event.y_root)
            except:
                pass
    #------------------------------------------------------------------------------ 

    ##
    # Define the behaviour of dragging right button of the mouse
    # @param event the dragging right button event    
    def button_3_drag(self, event):

        if self.current_func != self.modes["editing"]:
        
            #find the object pointed by mouse
            if self.current_func != self.modes[Connection.type]:
                obj_id=self.find_by_range(event.x, event.y)

                if obj_id != None:
                    cx, cy=self.convert(event.x, event.y)
                    cx_s, cy_s=self.object_list[obj_id].get_coord()

                    # create a new connection
                    new_connection=Connection(cx_s, cy_s, cx, cy, self.object_list[obj_id].get_name(), self.counter[Connection.type], self.counter[Tag.type])
                    c_tag=new_connection.get_name()
                    object_id=self.canvas.create_line(cx_s, cy_s, cx, cy, tag=c_tag)
                    self.object_list[object_id]=new_connection
                    self.current_obj=(object_id, new_connection)
                    self.current_func=self.modes[Connection.type]
                
            elif self.current_func==self.modes[Connection.type]:
                self.s_canvas.config(cursor='pencil')
                
                #delete the old line, and redraw a new one
                x_s, y_s=self.current_obj[1].get_start_point()
                x_e, y_e=self.convert(event.x, event.y)
                self.canvas.delete(self.current_obj[0])
                del self.object_list[self.current_obj[0]]
                c_tag=self.current_obj[1].get_name()
                object_id=self.canvas.create_line(x_s, y_s, x_e, y_e, tag=c_tag)
                self.object_list[object_id]=self.current_obj[1]
            
                #update the ending point of the connection
                self.current_obj[1].update_end_point(x_e, y_e)
                self.current_obj=(object_id, self.current_obj[1])


    ##
    # Check if the connection is valid according to the connection rules we defined 
    # @param d1 the device 1 to connect
    # @param d2 the device 2 to connect
    # @return 1 If the connection is valid.  
    #         0 Otherwise.
    def validate_connection(self, d1, d2):
        if d2 in connection_rule[d1]:
            return 1
        else:
            return 0

    ##
    # Fine a device in a particular range around the specified position on the canvas
    # @param x the x position of the canvas to search
    # @param y the y position of the canvas to search
    # @return o_id the object id if found, otherwise, return None.
    #         If the device found is tag, or connection, or wireless connection, it is ignored 
    def find_by_range(self, x, y):
        cx, cy=self.convert(x, y)
        obj=self.canvas.find_enclosed(cx-50, cy-50, cx+50, cy+50)       
        if obj:
            for o_id in obj:
                if not self.object_list.has_key(o_id):
                    continue
                if o_id != self.ping:
                    if self.object_list[o_id].type != "tag" and \
                       self.object_list[o_id].type != "connection" and \
                       self.object_list[o_id].type != "wireless_connection":
                        return o_id
        return None


    ##
    # Set the mode of the system to be "Add UML"
    def add_UML(self):
        self.current_func=self.modes[UML_machine.type]
        self.s_canvas.config(cursor='cross')

    ##
    # Set the mode of the system to be "Add Router"
    def add_router(self):
        self.current_func=self.modes[Router.type]
        self.s_canvas.config(cursor='cross')

    ##
    # Set the mode of the system to be "Add Switch"
    def add_switch(self):
        self.current_func=self.modes[Switch.type]
        self.s_canvas.config(cursor='cross')

    def add_bridge(self):
        self.current_func=self.modes[Bridge.type]
        self.s_canvas.config(cursor='cross')

    ##
    # Set the mode of the system to be "Add Hub"
    def add_hub(self):
        self.current_func=self.modes[Hub.type]
        self.s_canvas.config(cursor='cross')

    ##
    # Set the mode of the system to be "Add Subnet"
    def add_subnet(self):
        self.current_func=self.modes[Subnet.type]
        self.s_canvas.config(cursor='cross')

    ##
    # Set the mode of the system to be "Add Firewall"
    def add_firewall(self):
        self.current_func=self.modes[Firewall.type]
        self.s_canvas.config(cursor='cross')

    ##
    # Set the mode of the system to be "Add Wireless Router"
    def add_wireless(self):
        self.current_func=self.modes[Wireless_access_point.type]
        self.s_canvas.config(cursor='cross')
        #print self.current_func

    ##
    # Set the mode of the system to be "Add Mobile"
    def add_mobile(self):
        self.current_func=self.modes[Mobile.type]
        self.s_canvas.config(cursor='cross')

    ##
    # Post the pipup menu when right-single-click is detected
    # @param event the right-single-click event
    def popup(self, event):
        type == self.current_obj[1].get_type()
        if type == "UML" or type == "Mobile":
            self.pop_menu_UML.post(event.x_root, event.y_root)            
        elif type == "Router":
            self.pop_menu_Router.post(event.x_root, event.y_root)
        elif type == "Wireless_access_point":
            self.pop_menu_WAP.post(event.x_root, event.y_root)
        else:
            self.pop_menu.post(event.x_root, event.y_root)
    ##    
    # Show the mobile stats pop-up
    # @param obj_id the id of the mobile to be displayed
    def show_mobile(self, obj_id):
        mobile = self.object_list[obj_id]
        currentview = self.view_mobiles[mobile.name]
        self.current_mobile = currentview
        currentview.iconify()           
        x = self.canvas.winfo_rootx()+mobile.x-250
        y = self.canvas.winfo_rooty()+mobile.y
        currentview.geometry("+%d+%d" % (x, y))

    ##
    # Determine if the mouse cursor reaches a running mobile
    # @param event binding of the mouse cursor
    def detect(self, event):
        if not self.running:
            return
        obj_id=self.find_by_range(event.x, event.y)
        
        # if cursor is not over any object        
        if not obj_id:
            # if mobile stats are showing
            if self.current_mobile:
                try:
                    # hide them
                    self.current_mobile.withdraw()
                except:
                    pass
                self.current_mobile = None
        # if there are no stats showing and the current object is a mobile 
        elif not self.current_mobile and self.object_list[obj_id].type == Mobile.type:          
            if not self.ready:
                self.current_mobile = 1
                return            
            thread.start_new(self.show_mobile, (obj_id,))                        

    ##
    # Open an existing network model by clicking "Open" in the menu
    def Open(self, event = None):
        global auto_routing
        if self.new() == "cancel":      # clean the canvas and return if loading a file was cancelled
            return        
        if (os.environ.has_key("GINI_HOME")):
            giniEnv = os.environ["GINI_HOME"]
            self.filename=tkFileDialog.askopenfilename(initialdir=giniEnv)
        else:
            self.filename=tkFileDialog.askopenfilename()
        if self.filename:
            self.f=open(self.filename, 'r')
            try:
                self.dtd_filename=pickle.load(self.f)
                self.fs_filename=pickle.load(self.f)
                self.object_list=pickle.load(self.f)
            except:
                msg = "This file did not load properly, check that you have selected the right file"
                self.log.appendtext(msg + "\n")
                print msg
                return
            try:
                auto_routing=int(pickle.load(self.f))            
            except:
                pass
            tmp={}
        
            if os.access(self.filename+"_rdist", os.F_OK):
                self.rdfilename = self.filename+"_rdist"
                
            # set up a counter to keep track the max num of screen name of each type of device
            max_counter={}
            for device in self.support_device:
                max_counter[device[0].type]=0
        
            #restore all objects in the canvas
            for id, obj in self.object_list.iteritems():

                if obj.get_type() == "tag":
                    cx, cy, re_y=obj.get_coord()
                    t_tag=obj.get_name()
                    t_name=obj.get_content()
                    new_id=self.canvas.create_text(cx, cy+re_y, text=t_name, tag=t_tag)
                                
                elif obj.get_type() == "connection":
                    x_s, y_s=obj.get_start_point()
                    x_e, y_e=obj.get_end_point()
                    c_tag=obj.get_name()
                    new_id=self.canvas.create_line(x_s, y_s, x_e, y_e, fill="GRAY", width=3, tag=c_tag)
                    self.canvas.lower(new_id)
                        
                elif obj.get_type() == "wireless_connection":
                    x_s, y_s=obj.get_start_point()
                    x_e, y_e=obj.get_end_point()
                    c_tag=obj.get_name()
                    new_id=self.canvas.create_line(x_s, y_s, x_e, y_e, fill="GRAY", width=3, tag=c_tag, dash=15)
                    self.canvas.lower(new_id)
        
                else:
                    cx, cy=obj.get_coord()            
                    obj_tag=obj.get_name()
                    new_id=self.canvas.create_image(cx, cy, image=self.photos[obj.type][1], tag=obj_tag)
        
                    self.balloon.tagbind(self.canvas, new_id, obj.balloon_help())

                #update the max number of each device
                num=obj.get_num()
                max_counter[obj.type]=max(max_counter[obj.type], num)
                
                #save to a tmp list and copy it back after the for loop
                tmp[new_id]=obj

            self.s_canvas.resizescrollregion() 
            self.object_list={}
            self.object_list=tmp.copy()
        
            # restore the connection list
            for o_id, obj in self.object_list.iteritems():
                if obj.type=="connection" or obj.type=="wireless_connection":
                    s_id=self.canvas.find_withtag(obj.get_start_device())[0]
                    e_id=self.canvas.find_withtag(obj.get_end_device())[0]
                    self.connection_list.append([self.object_list[s_id], self.object_list[e_id]])

            # restore the device counters
            for device in self.support_device:
                self.counter[device[0].type]=max_counter[device[0].type]+1

    ##
    # Start a new network model by clicking "New" in the menu
    def new(self, event = None):
        global auto_routing
        if len(self.object_list) > 0:
            answer = tkMessageBox._show("Save current?", "Do you want to save current topology?", icon=tkMessageBox.QUESTION, type=tkMessageBox.YESNOCANCEL)
            answer = str(answer)
            if answer == "yes":
                self.save()
            elif answer == "no":
                pass
            else:
                return "cancel"
        for id, obj in self.object_list.iteritems():
            self.canvas.delete(id)
        self.s_canvas.pack_forget()
        del self.s_canvas
        self.init_condition()
        auto_routing = 1
        
    ##
    # Save the network model on the canvas by clicking "Save" in the menu
    def save(self, event = None):
        global auto_routing
        #save all objects in the canvas to a file
        if self.filename == "" or not self.filename:
            self.save_as()
        else:
            self.f=open(self.filename, 'w') 
            pickle.dump(self.dtd_filename, self.f)
            pickle.dump(self.fs_filename, self.f)
            pickle.dump(self.object_list, self.f)
            pickle.dump(auto_routing, self.f)            
            self.f.close()
            self.log.appendtext("Saved successfully\n")
            print "Saved successfully\n"

    ##
    # Save the network model on the canvas to another file by clicking "Save as" in the menu
    def save_as(self):

        self.filename=tkFileDialog.asksaveasfilename()
        if self.filename:
            self.f=open(self.filename, 'w')
            pickle.dump(self.dtd_filename, self.f)
            pickle.dump(self.fs_filename, self.f)
            pickle.dump(self.object_list, self.f)
            self.f.close()
            print "Saved successfully\n"

    ##
    # Disable the canvas by click "Close" in the menu
    def close(self, event = None):
        #1.Stop the running topology if it is running
        if self.running:
            self.stop()
                
        #2. Close the current environment
        if self.new() != "cancel":
            self.canvas.pack_forget()
    
    def quit(self, arg1=None, arg2=None):
        if self.running:
            self.stop()        
        onCloseEventHandler()      

    ##
    # Remove all XML files 
    def cleanXML (self):
        if self.filename == "" or not self.filename:
            #1 Remove an XML file : user chose file if  no panel is running
            file = tkFileDialog.askopenfilename(title="Please select a XML file",\
                                                filetypes = [("Fichiers XML", "*.xml")])
            if (file != None):
                print "\nRemoving:"
                print file
                # Remove associated file
                (dir, fileName) = os.path.split(file) 
                (shortname, extension) = os.path.splitext(fileName) 
                os.unlink(os.path.join(dir, shortname))
                os.unlink(os.path.join(dir, fileName))                         

        #2. 
        else:
            answerClean=tkMessageBox.askyesno(title="Remove the current topology ?", \
                                 message="Do you want to remove the current topology %s ?" \
                                 %  self.filename)     
            if answerClean:     
                # 1. Stop the current topology
                self.log.appendtext("Stopping UML\n")
                self.stop() 
                print "\nConfiguration is stopped"
                self.log.appendtext("Removing the gini_setup file \n")             
                print "\nRemoving the gini_setup file"
                # 2. Removing gini_setup file
                if os.path.isfile("%s/gini_setup" % os.environ["GINI_HOME"]):
                    os.unlink("%s/gini_setup" % os.environ["GINI_HOME"])
                # 3. Removing the XML files
                self.log.appendtext("Removing the topology files \n")
                print "\nRemoving the topology files"                   
                (dir, fileToremove) = os.path.split(self.filename)
                (shortname, extension) = os.path.splitext(fileToremove) 
                os.unlink(os.path.join(os.getcwd(), shortname))
                os.unlink(os.path.join(os.getcwd(), "%s.xml" %fileToremove))

    ##
    # Remove all files created by gini except xml files
    def cleanUp (self):
        answerClean=tkMessageBox.askyesno(title="Remove all files created?",\
                             message="Do you want to remove all files and folders created by %s ?" \
                             %  self.filename)     
        if answerClean:     
            # 1. Stop the current topology
            if self.running:
                self.log.appendtext("Stopping UML\n")
                self.stop() 
                print "\nConfiguration is stopped"
            
            self.log.appendtext("Removing the gini_setup file \n")             
            print "\nRemoving the gini_setup file"
            # 2. Removing gini_setup file
            if os.path.isfile("%s/gini_setup" % os.environ["GINI_HOME"]):
                os.unlink("%s/gini_setup" % os.environ["GINI_HOME"])

            # 3. Removing the XML files
            self.log.appendtext("Removing the topology files \n")
            print "\nRemoving the topology files"                   
            (dir, fileToremove) = os.path.split(self.filename)
            (shortname, extension) = os.path.splitext(fileToremove) 
            os.unlink(os.path.join(os.getcwd(), shortname))
            os.unlink(os.path.join(os.getcwd(), "%s.xml" %fileToremove))

    ##
    # Clean the cow files of the UMLs
    def cleanCow(self):
        answerClean=tkMessageBox.askyesno(title="Remove all cow files?",message="Do you want to remove all UML cow files ?")
        if answerClean:
            # stop if running first
            if self.running:
                self.log.appendtext("Stopping UMLs\n")
                self.stop()
            oldDir = os.getcwd()
            os.chdir("%s/data" % os.environ["GINI_HOME"])
            os.system("rm -rf UML_* Mobile_*")
            os.chdir(oldDir)

    ##
    # Clean the uml_mconsole files associated with UMLs
    def cleanUML_console(self):
        answerClean=tkMessageBox.askyesno(title="Remove all uml_mconsole files?",message="Do you want to remove all uml_mconsole files ?")
        if answerClean:
            # stop if running first
            if self.running:
                self.log.appendtext("Stopping UMLs\n")
                self.stop()
            oldDir = os.getcwd()
            os.chdir("%s/.uml" % os.environ["HOME"])
            os.system("rm -rf *")
            os.chdir(oldDir)
             
    ##
    # Screen interaction on double click
    def screen_attach_popup(self, event):
        obj_id=self.find_by_range(event.x, event.y)
        if obj_id != None:
            self.current_obj=(obj_id, self.object_list[obj_id])
            #self.current_func=self.modes["screen"]
            device_name = self.current_obj[1].get_name()
            device_type = self.current_obj[1].get_type()
            if (device_type == Switch.type):
                tkMessageBox.showerror("Interacting: ", "Double click has no effect on Switch")
            # if it is a wap show the interpreter instead
            elif device_type == Wireless_access_point.type:
                scr_command = "screen -r VWAP_1"
                term_command = "xterm -T %s -e %s &" % (device_name, scr_command)
                os.system(term_command)
            else:
                scr_command = "screen -r -S %s" % device_name
                term_command = "xterm -T %s -e %s &" % (device_name, scr_command)
                os.system(term_command)
        return


    ##
    # Edit the mouse pointed device by clicking "Properties" in the popup menu
    def edit(self):      

        self.current_func=0

        # Create the toplevel to contain the main menubar.
        toplevel = Toplevel(self.parent)
        toplevel.title("Edit Properties")
        self.current_view = toplevel        
        wx = self.parent.winfo_rootx()
        wy = self.parent.winfo_rooty()

        try:
            (xco, yco) = self.current_obj[1].get_coord()
            toplevel.geometry("+%d+%d" % (xco+wx, yco+wy))
        except:
            pass

        #toplevel.resizable(0, 0)
        
        # check the type of current object
        if self.current_obj[1].type == "connection":
            def close():
                toplevel.destroy()
                self.current_view = None

            toplevel.protocol("WM_DELETE_WINDOW", close)
            dev_1=self.current_obj[1].get_start_device()
            dev_2=self.current_obj[1].get_end_device()
            s="connects "+dev_1+" with "+dev_2
            c_label=Label(toplevel, text=s)
            c_label.pack(padx=10, pady=10)
            c_button=Button(toplevel, text="OK", command=close)
            c_button.pack(pady=10)
        
        # config wireless connection
        elif self.current_obj[1].type == "wireless_connection":
            toplevel.protocol("WM_DELETE_WINDOW", lambda : self.exit_wireless_connection(toplevel))
            self.unbind_event()                        #disable canvas
        
            l=Label(toplevel, text="Properties for "+self.current_obj[1].get_name(), font=("Helvetica", 14))
            l.pack(padx=20, pady=10)
        
            dev_1=self.current_obj[1].get_start_device()
            dev_2=self.current_obj[1].get_end_device()
            s="connects "+dev_1+" with "+dev_2
            c_label=Label(toplevel, text=s)
            c_label.pack(padx=10, pady=10)
        
            #properties frame
            pro_frame=Frame(toplevel)
            pro_frame.pack(fill='x')
        
            g_propagation=Pmw.Group(pro_frame, tag_text='Propagation Model')
            g_propagation.pack(side=LEFT, padx=20, pady=10)
            g_p_select = Pmw.RadioSelect(g_propagation.interior(), 
                                            buttontype = 'radiobutton', 
                                            orient = 'vertical', 
                                            command = self.wireless_propagation)
            g_p_select.pack(padx=10, pady=10)
        
            # Add some buttons to the propagation group
            for text in ('Free Space', 'TwoRayGround', 'Shadowing'):
                g_p_select.add(text)
        
            g_fading=Pmw.Group(pro_frame, tag_text='Channel type')
            g_fading.pack(side=RIGHT, padx=20, pady=10, fill=BOTH, expand=1)
            g_f_select = Pmw.RadioSelect(g_fading.interior(), 
                                            buttontype = 'radiobutton', 
                                            orient = 'vertical')
        
            g_f_select.pack(padx=10, pady=10, fill='x')
        
            # Add some buttons to the Channel Type group
            for text in ('AWGN', 'Rayleigh Fading'):
                g_f_select.add(text)
        
            # Add noise box
            ctype_noise=Pmw.EntryField(g_fading.interior(), labelpos=W, label_text="Noise (dBm)")
            ctype_noise.configure(entry_width=6)
            ctype_noise.pack(padx=10, pady=5)
        
            # frame for shadowing
            self.shadow_frame=Frame(toplevel)
            #self.shadow_frame.pack(fill=BOTH, expand=1)
            self.shadow_frame.pack()
        
            g_sh=Pmw.Group(self.shadow_frame, tag_text='Sub_option for Shadowing', tagindent=80)
            g_sh.pack(padx=20, pady=10, expand=1, fill='x')
        
            g_path=Pmw.Group(g_sh.interior(), tag_text='PathLossExponent')
            g_path.pack(padx=20, pady=10, fill='x')
            g_path_select = Pmw.RadioSelect(g_path.interior(), 
                                               buttontype = 'radiobutton', 
                                               orient = 'vertical')
            g_path_select.pack(padx=20, pady=10, fill='x')
            
            # Add some buttons to the pathloss group
            for text in ('Good', 'Normal', 'Bad', 'User Specify'):
                g_path_select.add(text)
        
            g_deviation=Pmw.Group(g_sh.interior(), tag_text='ShadowingDeviation')
            g_deviation.pack(padx=20, pady=10, fill='x')
            g_deviation_select = Pmw.RadioSelect(g_deviation.interior(), 
                                                    buttontype = 'radiobutton', 
                                                    orient = 'vertical')
            g_deviation_select.pack(padx=20, pady=10, fill='x')
            
            # Add some buttons to the pathloss group
            for text in ('Good', 'Normal', 'Bad', 'User Specify'):
                g_deviation_select.add(text)
        
            # add reference distance
            g_ref_f=Pmw.Group(g_sh.interior(), tag_text='Reference Distance')
            g_ref_f.pack(padx=20, pady=10, expand=1, fill='x')
            ref_dist=Pmw.EntryField(g_ref_f.interior(), labelpos=W, label_text="Reference Distance (m)")
            ref_dist.pack(padx=5, pady=5)
                
            #initial state
            properties=self.current_obj[1].get_properties()
            g_path_select.invoke(properties["pathloss"])
            g_deviation_select.invoke(properties["deviation"])
            g_p_select.invoke(properties["propagation"])
            g_f_select.invoke(properties["channel_type"])
            ref_dist.setvalue(properties["distance"])
            ctype_noise.setvalue(properties["noise"])

            # some buttons
            buttons=Pmw.ButtonBox(toplevel)
            buttons.pack(side=BOTTOM, padx=10, pady=10, fill='x')
        
            buttons.add('Accept', command=lambda : self.save_wireless_connection(g_path_select, g_deviation_select, 
                                                                                     g_p_select, g_f_select, ctype_noise, 
                                                                                     ref_dist, properties, toplevel))
            buttons.add('Apply', command=lambda : self.update_wireless_connection(g_path_select, g_deviation_select, 
                                                                                     g_p_select, g_f_select, ctype_noise, 
                                                                                     ref_dist, properties))
            buttons.add('Cancel', command=lambda : self.exit_wireless_connection(toplevel))

        #config the subnet
        elif self.current_obj[1].type == "Subnet":
            toplevel.resizable(0, 0)
            toplevel.protocol("WM_DELETE_WINDOW", lambda : self.exit_subnet(toplevel))
            self.unbind_event()                        #disable canvas
        
            l=Label(toplevel, text="Properties for "+self.current_obj[1].get_name(), font=("Helvetica", 14))
            l.pack(padx=20, pady=10)
        
            req_list={}
            opt_list={}
            tmp_list=[]
        
            # the required part
            req_p=self.current_obj[1].get_req_properties()
            if len(req_p) > 0:
                g_required=Pmw.Group(toplevel, tag_text='Required')
                g_required.pack(padx=10, pady=10)
                ipFrame = Frame(g_required.interior())                
                ipFrame.pack(side=TOP, padx=0, pady=0)
                for entry in req_p:
                    if entry == "subnet":
                        s_id=Pmw.EntryField(ipFrame, labelpos=W, label_text=entry, value=req_p[entry])
                        s_id.pack(side=LEFT, padx=5, pady=5)
                        req_list[entry]=s_id
                        tmp_list.append(s_id)
                    
                    elif entry == "mask":
                        s_mask=Pmw.EntryField(g_required.interior(), labelpos=W, label_text=entry, value=req_p[entry], entry_state=DISABLED)
                        s_mask.pack(side=LEFT, padx=5, pady=5)
                        req_list[entry]=s_mask
                        tmp_list.append(s_mask)
                   
                    else:
                        maskbits=Pmw.EntryField(ipFrame, labelpos=W, label_text="/", value=req_p[entry], entry_width=2, validate = {'max' : 2})
                        maskbits.pack(side=RIGHT, padx=5, pady=5)
                        req_list[entry]=maskbits
                            
            # the optional part
            opt_p=self.current_obj[1].get_opt_properties()
            if len(opt_p) > 0:
                g_optional=Pmw.Group(toplevel, tag_text='Optional')
                g_optional.pack(padx=10, pady=10)
                for entry in opt_p:
                    s_id=Pmw.EntryField(g_optional.interior(), labelpos=W, label_text=entry, value=opt_p[entry])
                    s_id.pack(padx=5, pady=5)
                    opt_list[entry]=s_id
                    tmp_list.append(s_id)
        
            Pmw.alignlabels(tmp_list)
        
            buttons=Pmw.ButtonBox(toplevel)
            buttons.pack(padx=10, pady=10, fill='x')
            buttons.add('Accept', command=lambda : self.save_subnet(req_list, opt_list, toplevel))
            buttons.add('Apply', command=lambda : self.update_subnet(req_list, opt_list))
            buttons.add('Cancel', command=lambda : self.exit_subnet(toplevel))


        #config the switch
        elif self.current_obj[1].get_type() == "Switch":
            toplevel.protocol("WM_DELETE_WINDOW", lambda : self.exit_switch(toplevel))
            self.unbind_event()                        #disable canvas
        
            l=Label(toplevel, text="Properties for "+self.current_obj[1].get_name(), font=("Helvetica", 14))
            l.pack(padx=20, pady=10)
            
            req_list={}
            opt_list={}
            tmp_list=[]
        
            # the required part
            req_p=self.current_obj[1].get_req_properties()
            if len(req_p) > 0:
                g_required=Pmw.Group(toplevel, tag_text='Required')
                g_required.pack(padx=10, pady=10)
                for entry in req_p:
                    s_id=Pmw.EntryField(g_required.interior(), labelpos=W, label_text=entry, value=req_p[entry])
                    s_id.pack(padx=5, pady=5)
                    req_list[entry]=s_id
                    tmp_list.append(s_id)

            # the optional part
            opt_p=self.current_obj[1].get_opt_properties()
            if 0:
                g_optional=Pmw.Group(toplevel, tag_text='Optional')
                g_optional.pack(padx=10, pady=10)
                for entry in opt_p:
                    s_id=Pmw.EntryField(g_optional.interior(), labelpos=W, label_text=entry, value=opt_p[entry])
                    s_id.pack(padx=5, pady=5)
                    opt_list[entry]=s_id
                    tmp_list.append(s_id)

            g_subnet=Pmw.Group(toplevel, tag_text='Subnet')
            g_subnet.pack(padx=10, pady=10)
            Pmw.EntryField(g_subnet.interior(), labelpos=W, value=self.current_obj[1].get_subnet(), entry_state=DISABLED).pack(padx=5, pady=5)
            

            Pmw.alignlabels(tmp_list)

            buttons=Pmw.ButtonBox(toplevel)
            buttons.pack(padx=10, pady=10, fill='x')
            buttons.add('Accept', command=lambda : self.save_switch(req_list, opt_list, toplevel))
            buttons.add('Apply', command=lambda : self.update_switch(req_list, opt_list))
            buttons.add('Cancel', command=lambda : self.exit_switch(toplevel))
        
        #config the uml machine, router and mobile
        elif self.current_obj[1].type == "UML" or \
             self.current_obj[1].type == "Router" or \
             self.current_obj[1].type == "Mobile" or \
             self.current_obj[1].type == "Wireless_access_point" :
            global auto_routing
            
            l=Label(toplevel, text="Properties for "+self.current_obj[1].get_name(), font=("Helvetica", 14))
            l.pack(padx=20, pady=10)
            page_list={}
            self.property_page[self.current_obj[1]]=[]                
            toplevel.protocol("WM_DELETE_WINDOW", lambda : self.clean_UML(toplevel, page_list))
            self.unbind_event()                        #disable canvas

            if self.current_obj[1].type != "Wireless_access_point" and not auto_routing:            
                self.show_routing_table('Yes')
                #self.s_auto.invoke('Yes')
            else:
                self.show_routing_table('No')
                
               #self.s_auto.invoke('No')
                #s_auto.forget()
            
            if self.current_obj[1].get_type() == "UML" or self.current_obj[1].get_type() == "Mobile":
            
                # add select widget to choose file type and file system
                select_frame=Frame(toplevel)
                select_frame.pack()
                f_type=('cow', 'direct')
                filetype_menu = Pmw.ComboBox (select_frame, 
                                                labelpos = 'w', 
                                                label_text = 'file type:', 
                                                scrolledlist_items = f_type)

                filetype_menu.pack(side=LEFT, padx=20, pady=5)
                filetype_menu.component('entry').configure(width=12)
                filetype_menu.component('entry').insert(0, self.current_obj[1].get_filetype())
            
                f_system=('root_fs_beta2',)
                filesystem_menu = Pmw.ComboBox (select_frame, 
                                                      labelpos = 'w', 
                                                      label_text = 'file system:', 
                                                      scrolledlist_items = f_system)

                filesystem_menu.pack(side=LEFT, padx=10, pady=5)
                filesystem_menu.component('entry').configure(width=12)
                filesystem_menu.component('entry').insert(0, self.current_obj[1].get_filesystem())
    
            notebook = Pmw.NoteBook(toplevel)
            notebook.pack(fill = 'both', expand = 1, padx = 10, pady = 20)

            # add a page for each interface
            for interface in self.current_obj[1].get_interface():
            
                page=notebook.add("Interface "+str(interface.get_id()))
                
                #find out the device at the other side
                con=interface.get_connection()

                if con == None:
                    group = Pmw.Group(page, tag_text = "Wireless & Wired connection point", tagindent=65)
                    oldpage = page
                elif self.current_obj[1].get_name() == con.get_start_device():
                    group = Pmw.Group(page, tag_text = "Connect to "+con.get_end_device(), tagindent=105)
                else:
                    group = Pmw.Group(page, tag_text = "Connect to "+con.get_start_device(), tagindent=105)
                
                group.pack(padx=5, pady=10, expand=0, fill='x')
                
                # create the required and optional group
                required_g=Pmw.Group(group.interior(), tag_text = "Required")
#                optional_g=Pmw.Group(group.interior(), tag_text = "Optional")
                required_g.pack(padx=20, pady=10, fill='x')
#                optional_g.pack(padx=20, pady=15, fill='x')
                
                # some data structures to save the your input values
                inter_required={}
                inter_optional={}
                inter_entry={}
                tmp_list=[]

                # show the required properties
                properties=interface.get_req_properties()
                for entry in properties:
                    if self.current_obj[1].get_type() == "Mobile" and entry == "mac":
                        field = field=Pmw.EntryField(required_g.interior(), labelpos=W, label_text=entry, value=properties[entry], entry_state=DISABLED)
                    else:
                        field=Pmw.EntryField(required_g.interior(), labelpos=W, label_text=entry, value=properties[entry])
                    inter_required[entry]=field        
                    tmp_list.append(field)
                
                # show the optional properties
#                properties=interface.get_opt_properties()
#                for entry in properties:
#                    field=Pmw.EntryField(optional_g.interior(), labelpos=W, label_text=entry, value=properties[entry])
#                    inter_optional[entry]=field
#                    tmp_list.append(field)
                
                for field in tmp_list:
                    field.pack(padx=5, pady=5)
                Pmw.alignlabels(tmp_list)
                    
                # a frame contians routing table entry and button
                rt_frame=Frame(page)
                self.property_page[self.current_obj[1]].append(rt_frame)
                
                if auto_routing:
                    pass#rt_frame.pack_forget()                
                else:
                    rt_frame.pack()

                # Create the ScrolledFrame.
                if self.current_obj[1].type == "UML":
                    sf = Pmw.ScrolledFrame(rt_frame, labelpos = 'n', hull_width = 395, hull_height = 205, 
                                                   label_text = 'Routing Table\n\nmask\t      gateway\tdestination\t\t', usehullsize = 1)
                else:
                    sf = Pmw.ScrolledFrame(rt_frame, labelpos = 'n', hull_width = 395, hull_height = 205, 
                                                   label_text = 'Routing Table\n\nmask\t      nexthop\tdestination\t\t', usehullsize = 1)
                sf.pack(padx = 5, pady = 5, fill = 'both', expand = 1)
                routing_table_frame = sf.interior()

                # show each routing table entry
                my_row=0
                for entry in interface.get_table():
                    self.show_entry(routing_table_frame, interface, entry, my_row, inter_entry)
                    my_row+=1
                interface.set_next_entry_num(my_row)
                
                buttons=Pmw.ButtonBox(rt_frame)
                buttons.pack(padx=10, pady=10, fill='x')
                self.UML_control_button(buttons, routing_table_frame, interface, inter_entry)
                page_list[interface]=[inter_required, inter_optional, inter_entry]

                notebook.setnaturalsize()
                
            # specify more properties for mobile device
            if self.current_obj[1].type == "Wireless_access_point":

                toplevel.minsize(width=400, height=500)

                def show_properties():

                    def focus_prop(e):
                        toplevel2.focus_force()
                        toplevel2.lift()

                    def exit_wprop(e = None):
                        toplevel.unbind("<FocusIn>")
                        toplevel2.destroy()
    
                    toplevel2 = Toplevel(toplevel)
                    toplevel2.minsize(width=400, height=600)
                    toplevel2.title("Edit Properties")
                    toplevel2.protocol('WM_DELETE_WINDOW', exit_wprop)

                    self.parent.update_idletasks()
                    toplevel.bind("<FocusIn>", focus_prop)

                    notebook2 = Pmw.NoteBook(toplevel2)
                    notebook2.pack(fill = 'both', expand = 1, padx = 10, pady = 20)

                    # add page for wireless card
                    card_page=notebook2.add("Wireless Card")
                    g_card=Pmw.Group(card_page, tag_text='Card Type', tagindent=165)
                    g_card.pack(padx=10, pady=10, expand=0, fill='x')

                    g_card_select = Pmw.RadioSelect(g_card.interior(), 
                                                    buttontype = 'radiobutton', 
                                                    orient = 'vertical', 
                                                    command=self.wireless_card)
                    g_card_select.pack(padx=20, pady=10, fill='x')

                    # Add some buttons to the group
                    for text in ('Demo TSCard (not implemented yet)', 
                                 'Demo TUCard (not implemented yet)', 
                                 'Demo TTCard (not implemented yet)', 
                                 'Sample Card', 
                                 'User Specified Card'):
                        g_card_select.add(text)

                    #sub option for user defined card
                    self.default_frame=Pmw.ScrolledFrame(card_page, usehullsize = 1, hull_width = 395, hull_height = 320)
                    self.default_frame.pack(padx=10, pady=5, fill='x')
                
                    default_card=Pmw.Group(self.default_frame.interior(), tag_text='Sub option for user specified card', tagindent=50)
                    default_card.pack(padx=10, pady=10, expand=1, fill='x')
                    fre=Pmw.EntryField(default_card.interior(), labelpos=W, label_text="Frequency (Hz)")
                    band=Pmw.EntryField(default_card.interior(), labelpos=W, label_text="Bandwidth (Mbps)")
                    fre.pack(padx=5, pady=5)
                    band.pack(padx=5, pady=5)
                    tmp_list1=[fre, band]

                    power=Pmw.Group(default_card.interior(), tag_text='Power')
                    power.pack(padx=10, pady=10, fill='x')
                    pt=Pmw.EntryField(power.interior(), labelpos=W, label_text="Pt (W)")
                    pt_con=Pmw.EntryField(power.interior(), labelpos=W, label_text="Pt_consume (W)")
                    pr_con=Pmw.EntryField(power.interior(), labelpos=W, label_text="Pr_consume (W)")
                    p_idle=Pmw.EntryField(power.interior(), labelpos=W, label_text="P_idle (W)")
                    p_sleep=Pmw.EntryField(power.interior(), labelpos=W, label_text="P_sleep (W)")
                    p_off=Pmw.EntryField(power.interior(), labelpos=W, label_text="P_off (W)")
                    tmp_list2=[pt, pt_con, pr_con, p_idle, p_sleep, p_off]
                    for item in tmp_list2:
                        item.pack(padx=5, pady=5)
                
                    threshold=Pmw.Group(default_card.interior(), tag_text='Threshold')
                    threshold.pack(padx=10, pady=10, fill='x')
                    rx=Pmw.EntryField(threshold.interior(), labelpos=W, label_text="RXThresh (W)")
                    cs=Pmw.EntryField(threshold.interior(), labelpos=W, label_text="CSThresh (W)")
                    cp=Pmw.EntryField(threshold.interior(), labelpos=W, label_text="CPThresh (dB)")
                    tmp_list3=[rx, cs, cp]
                    for item in tmp_list3:
                        item.pack(padx=5, pady=5)
                    Pmw.alignlabels(tmp_list1+tmp_list2+tmp_list3)
                
                    module=Pmw.Group(default_card.interior(), tag_text='Modulation method')
                    module.pack(padx=10, pady=10, fill='x')
                    module_select = Pmw.RadioSelect(module.interior(), 
                                                    buttontype = 'radiobutton', 
                                                    orient = 'vertical')
                    module_select.pack(padx=5, pady=5, fill='x')
            
                    # Add some buttons to the group
                    for text in ('DSSS', 'FHSS (not implemented yet)'):
                        module_select.add(text)
        
                    #initial state for page wireless card
                    properties=self.current_obj[1].get_properties()
                    g_card_select.invoke(properties["w_type"])
                    module_select.invoke(properties["module"])
                    fre.setvalue(properties["freq"])
                    band.setvalue(properties["bandwidth"])
                    pt.setvalue(properties["Pt"])
                    pt_con.setvalue(properties["Pt_c"])
                    pr_con.setvalue(properties["Pr_c"])
                    p_idle.setvalue(properties["P_idle"])
                    p_sleep.setvalue(properties["P_sleep"])
                    p_off.setvalue(properties["P_off"])
                    rx.setvalue(properties["RX"])
                    cs.setvalue(properties["CS"])
                    cp.setvalue(properties["CP"])
                
                    #disable card types that are not implemented
                    for f in g_card_select.components():
                        if f is 'Demo TSCard (not implemented yet)' \
                           or f is 'Demo TUCard (not implemented yet)' \
                           or f is 'Demo TTCard (not implemented yet)':
                            w = g_card_select.component(f)
                            w.configure(state='disabled')
                    
                    for f in module_select.components():
                        if f is 'FHSS':
                            w = module_select.component(f)
                            w.configure(state='disabled') 
                    
                    #add page for antenna
                    antenna_page=notebook2.add("Antenna")
                    g_antenna=Pmw.Group(antenna_page, tag_text='Antenna Type', tagindent=165)
                    g_antenna.pack(padx=10, pady=10, expand=0, fill='x')

                    g_antenna_select = Pmw.RadioSelect(g_antenna.interior(), 
                                                       buttontype = 'radiobutton', 
                                                       orient = 'vertical')
                    g_antenna_select.pack(padx=10, pady=10, fill='x')
            
                    # Add some buttons to the group
                    for text in ('Omni Directional Antenna', 
                                 'Switched Beam Antenna (not implemented yet)', 
                                 'Adaptive Array Antenna (not implemented yet)'):
                        g_antenna_select.add(text)
                
                    # add a group for specific antenna
                    spec=Pmw.Group(antenna_page, tag_text='Specific Antenna', tagindent=165)
                    spec.pack(padx=10, pady=10, fill='x')
                    height=Pmw.EntryField(spec.interior(), labelpos=W, label_text="Height (M)")
                    gain=Pmw.EntryField(spec.interior(), labelpos=W, label_text="Gain (dBi)")
                    sys=Pmw.EntryField(spec.interior(), labelpos=W, label_text="System Loss")
                    tmp_list4=[height, gain, sys]
                    for item in tmp_list4:
                        item.pack(padx=20, pady=5, fill='x')
                    Pmw.alignlabels(tmp_list4)
                
                    # add a group for malicious
                    malicious=Pmw.Group(antenna_page, tag_text='Malicious', tagindent=165)
                    malicious.pack(padx=10, pady=10, fill='x')
                    mali_select = Pmw.RadioSelect(malicious.interior(), 
                                                  buttontype = 'radiobutton', 
                                                  orient = 'vertical')
                    mali_select.pack(padx=10, pady=10, fill='x')
            
                    # Add some buttons to the group
                    for text in ('on', 
                                 'off'):
                        mali_select.add(text)
            
                    #initial state for page antenna
                    g_antenna_select.invoke(properties["a_type"])
                    height.setvalue(properties["ant_h"])
                    gain.setvalue(properties["ant_g"])
                    sys.setvalue(properties["ant_l"])
                    mali_select.invoke(properties["JAM"])

                    #disable antenna types that are not implemented
                    for f in g_antenna_select.components():
                        if f is 'Switched Beam Antenna (not implemented yet)' \
                           or f is 'Adaptive Array Antenna (not implemented yet)':
                            w = g_antenna_select.component(f)
                            w.configure(state='disabled')

                          
                    #add page for energy
                    energy_page=notebook2.add("Energy")
                    g_power=Pmw.Group(energy_page, tag_text='Power Switch', tagindent=165)
                    g_power.pack(padx=10, pady=10, expand=0, fill='x')
                    g_power_select = Pmw.RadioSelect(g_power.interior(), 
                                                     buttontype = 'radiobutton', 
                                                     orient = 'vertical')
                    g_power_select.pack(padx=10, pady=10, fill='x')
                
                    # Add some buttons to the group
                    for text in ('ON', 'OFF'):
                        g_power_select.add(text)
                
                    g_psm=Pmw.Group(energy_page, tag_text='PSM', tagindent=175)
                    g_psm.pack(padx=10, pady=10, expand=0, fill='x')
                    g_psm_select = Pmw.RadioSelect(g_psm.interior(), 
                                                       buttontype = 'radiobutton', 
                                                       orient = 'vertical')
                    g_psm_select.pack(padx=10, pady=10, fill='x')

                    # Add some buttons to the group
                    for text in ('ON', 'OFF'):
                        g_psm_select.add(text)

                    # add entry field for total energy
                    t_power_f=Pmw.Group(energy_page, tag_text='Total Energy', tagindent=165)
                    t_power_f.pack(padx=10, pady=10, expand=0, fill='x')
                    t_power=Pmw.EntryField(t_power_f.interior(), labelpos=W, label_text="Total Power (w)")
                    t_power.pack(padx=5, pady=5, fill='x')
                
                    #initial state for page energy
                    g_power_select.invoke(properties["power"])
                    g_psm_select.invoke(properties["PSM"])
                    t_power.setvalue(properties["energy_amount"])
                
                
                    #add page for mobility
                    mobility_page=notebook2.add("Mobility")
                    g_mob=Pmw.Group(mobility_page, tag_text='Mobility Type', tagindent=160)
                    g_mob.pack(padx=10, pady=10, expand=0, fill='x')
                    g_mob_select = Pmw.RadioSelect(g_mob.interior(), 
                                                   buttontype = 'radiobutton', 
                                                   command=self.mobility_mode, 
                                                   orient = 'vertical')
                    g_mob_select.pack(padx=10, pady=10, fill='x')

                    # Add some buttons to the group
                    for text in ('Random Waypoint', 
                                 'Trajectory Based (not implemented yet)', 
                                 'Pseudo Linear (not implemented yet)', 
                                 'Manual (not implemented yet)'):
                        g_mob_select.add(text)

                    #sub option for random waypoint
                    self.random_frame=Frame(mobility_page)
                    self.random_frame.pack(padx=10, pady=5, fill='x')
                
                    speed_limit=Pmw.Group(self.random_frame, tag_text='Random speed limitation', tagindent=130)
                    speed_limit.pack(pady=10, expand=1, fill='x')
                    s_max=Pmw.EntryField(speed_limit.interior(), labelpos=W, label_text="Max Speed (m/s)")
                    s_min=Pmw.EntryField(speed_limit.interior(), labelpos=W, label_text="Min Speed (m/s)")
                    s_max.pack(padx=5, pady=5, fill='x')
                    s_min.pack(padx=5, pady=5, fill='x')
                    Pmw.alignlabels([s_max, s_min])
                
                    #initial state for page mobility
                    g_mob_select.invoke(properties["m_type"])
                    s_max.setvalue(properties["ran_max"])
                    s_min.setvalue(properties["ran_min"])
                
                    #disable mobility types that are not implemented
                    for f in g_mob_select.components():
                        if f is 'Trajectory Based (not implemented yet)' \
                           or f is 'Pseudo Linear (not implemented yet)' \
                           or f is 'Manual (not implemented yet)':
                            w = g_mob_select.component(f)
                            w.configure(state='disabled')

                
                    #add page for mac type
                    mac_page=notebook2.add("MAC")
                    g_mac=Pmw.Group(mac_page, tag_text='MAC Type', tagindent=165)
                    g_mac.pack(padx=10, pady=10, expand=0, fill='x')
                    g_mac_select = Pmw.RadioSelect(g_mac.interior(), 
                                                   buttontype = 'radiobutton', 
                                                   command=self.mac_mode, 
                                                   orient = 'vertical')
                    g_mac_select.pack(padx=10, pady=10, fill='x')
                
                    # Add some buttons to the group
                    for text in ('None', 'CSMA', 'MAC 802.11 DCF', 'MAC 802.11 DCF & PCF (not implemented yet)'):
                        g_mac_select.add(text)
                
                    #sub option for CSMA
                    self.CSMA_frame=Frame(mac_page)
                    self.CSMA_frame.pack(padx=10, pady=5, fill='x')
                    trans_p=Pmw.Group(self.CSMA_frame, tag_text='Transmission Probability', tagindent=130)
                    trans_p.pack(pady=10, expand=1, fill='x')
                    t_p=Pmw.EntryField(trans_p.interior(), labelpos=W, label_text="Transmission Probability (%)")
                    t_p.pack(padx=5, pady=5, fill='x')
                
                    #initial state for page mac
                    g_mac_select.invoke(properties["mac_type"])
                    t_p.setvalue(properties["trans"])
                
                    #disable mac types that are not implemented
                    for f in g_mac_select.components():
                        if f is 'MAC 802.11 DCF & PCF (not implemented yet)':
                            w = g_mac_select.component(f)
                            w.configure(state='disabled')
                
                    # build a list mobile property list 
                    mobile_list={"w_type": g_card_select, "module": module_select, 
                                 "freq": fre, "bandwidth": band, 
                                 "Pt": pt, "Pt_c": pt_con, 
                                 "Pr_c": pr_con, "P_idle": p_idle, 
                                 "P_sleep": p_sleep, "P_off": p_off, 
                                 "RX": rx, "CS": cs, 
                                 "CP": cp, "a_type": g_antenna_select, 
                                 "ant_h": height, "ant_g": gain, 
                                 "ant_l": sys, "JAM": mali_select, 
                                 "power": g_power_select, "PSM": g_psm_select, 
                                 "energy_amount": t_power, "m_type": g_mob_select, 
                                 "ran_max": s_max, "ran_min": s_min, 
                                 "mac_type": g_mac_select, "trans": t_p}
                  
                    def update_wprop(mobile = None):        
                        # update mobile properties
                        if mobile != None:
                            properties=self.current_obj[1].get_properties()
                        for entry, value in properties.iteritems():
                            properties[entry]=mobile[entry].getvalue()
                    
                    def save_wprop(mobile = None):
                        update_wprop(mobile)
                        exit_wprop()

                    buttons3=Pmw.ButtonBox(toplevel2)
                    buttons3.pack(padx=10, pady=10, fill='x')
                    buttons3.add('Accept', command=lambda : save_wprop(mobile_list))
                    buttons3.add('Apply', command=lambda : update_wprop(mobile_list))
                    buttons3.add('Cancel', command=exit_wprop)

                buttons2=Pmw.ButtonBox(oldpage)
                buttons2.pack(padx=10, pady=10, fill='x')
                buttons2.add('Wireless Properties', command=show_properties)  

            buttons=Pmw.ButtonBox(toplevel)
            buttons.pack(padx=10, pady=10, fill='x')

            if self.current_obj[1].get_type() == "UML" or self.current_obj[1].get_type() == "Mobile":
                buttons.add('Accept', command=lambda : self.save_UML(page_list, toplevel, filetype_menu.get(), 
                                                                         filesystem_menu.get()))
                buttons.add('Apply', command=lambda : self.update_UML(page_list, filetype_menu.get(), 
                                                                         filesystem_menu.get()))
            else:
                buttons.add('Accept', command=lambda : self.save_UML(page_list, toplevel))
                buttons.add('Apply', command=lambda : self.update_UML(page_list))
            buttons.add('Cancel', command=lambda : self.clean_UML(toplevel, page_list))
            

    ##
    # add an routing table entry
    # @param b the button to click
    # @param t the routing table frame
    # @param i the interface to add routing entry
    # @param entry_list the list of all routing entries
    def UML_control_button(self, b, t, i, entry_list):
        b.add('Add an entry', command=lambda : self.add_entry(t, i, entry_list))   

    ##
    # Update the required property list and optinal property list for switch with user input
    # @param req_p required property list
    # @param opt_p optional property list
    def update_switch(self, req_p, opt_p):        
        req_list=self.current_obj[1].get_req_properties()
        for entry in req_list:
            req_list[entry]=req_p[entry].getvalue()
        
        opt_list=self.current_obj[1].get_opt_properties()
        for entry in opt_list:
            opt_list[entry]=opt_p[entry].getvalue()

    ##
    # Update the required property list and optinal property list for switch with user input, then exit
    # @param req_p required property list
    # @param opt_p optional property list
    def save_switch(self, req_p, opt_p, parent):
        self.update_switch(req_p, opt_p)
        self.exit_switch(parent)

    ##
    # Update the required property list and optinal property list for subnet with user input
    # @param req_p required property list
    # @param opt_p optional property list
    def update_subnet(self, req_p, opt_p):        
        req_list=self.current_obj[1].get_req_properties()
        for entry in req_list:
            req_list[entry]=req_p[entry].getvalue()
        
            if not req_list[entry]:
                continue
        
            #check for valid network address
            if entry == "subnet":
                subnet = req_p[entry].getvalue().split(".")
                try:
                    if subnet[3] != "0":
                        tkMessageBox.showwarning("Invalid Subnet", "Subnet address should end with 0, changed")
                        subnet[3] = "0"                        
                        req_list[entry] = ".".join(subnet)
                        req_p[entry].setvalue(req_list[entry]) 
                except:
                    pass
            #compute mask from number of bits input
            elif entry == "bits":
                bits = int(req_p[entry].getvalue())

                remain = bits % 8
                counter = 0
                newmask = ["","","",""]

                if bits >= 0 and bits < 32:
                    while bits >= 8:
                        newmask[counter] = "255"
                        counter = counter + 1
                        bits = bits - 8

                    if remain:
                            newmask[counter] = "%d" % (256 - 2**(8-bits))
                    else:
                            newmask[counter] = "0"

                    counter = counter + 1

                    while counter < 4:
                            newmask[counter] = "0"
                            counter = counter + 1         
                    
                    req_list["mask"] = newmask[0] +"."+ newmask[1] +"."+ newmask[2] +"."+ newmask[3]
                
                else:
                    tkMessageBox.showwarning("Invalid number of bits", "The number of bits should be between 0 and 31 (inclusive).  Selecting default value of 24.")
                    req_list["mask"] = "255.255.255.0"
                    req_list["bits"] = "24"

        opt_list=self.current_obj[1].get_opt_properties()
        for entry in opt_list:
            opt_list[entry]=opt_p[entry].getvalue()

        #force ip base for connections between Subnet and UML, Router or Switch
        for con in self.current_obj[1].get_connection():
            s_con = con.get_start_device()
            e_con = con.get_end_device()

            if s_con.find("Subnet") >= 0 and e_con.find("UML") >= 0:
                target_device=self.object_list[self.canvas.find_withtag(e_con)[0]]
                self.force_ip(target_device, self.current_obj[1], 1)
            elif s_con.find("UML") >= 0 and e_con.find("Subnet") >= 0:
                target_device=self.object_list[self.canvas.find_withtag(s_con)[0]]        
                self.force_ip(target_device, self.current_obj[1], 1)
            elif s_con.find("Subnet") >= 0 and e_con.find("Router") >= 0:
                target_device=self.object_list[self.canvas.find_withtag(e_con)[0]]
                self.force_ip(target_device, self.current_obj[1], 2)
            elif s_con.find("Router") >= 0 and e_con.find("Subnet") >= 0:
                target_device=self.object_list[self.canvas.find_withtag(s_con)[0]]        
                self.force_ip(target_device, self.current_obj[1], 3)
            elif s_con.find("Subnet") >= 0 and e_con.find("Switch") >= 0:
                target_device=self.object_list[self.canvas.find_withtag(e_con)[0]]
                self.force_ip(target_device, self.current_obj[1], 6)
            elif s_con.find("Switch") >= 0 and e_con.find("Subnet") >= 0:
                target_device=self.object_list[self.canvas.find_withtag(s_con)[0]]        
                self.force_ip(target_device, self.current_obj[1], 6)
        
        self.balloon.tagbind(self.canvas, self.current_obj[0], self.current_obj[1].balloon_help())        
        self.current_view.lift()

    ##
    # Update the required property list and optinal property list for subnet with user input, then exit
    # @param req_p required property list
    # @param opt_p optional property list
    def save_subnet(self, req_p, opt_p, parent):
        self.update_subnet(req_p, opt_p)
        self.exit_subnet(parent)
        self.current_view = None

    ##
    # Control the visibility of the routing table.
    # @param tag the switch to control if the routing table is visible or not
    def show_routing_table(self, tag):        

        global auto_routing
        if tag == 'Yes':
        
            #check if the auto computing feature is enabled
            if auto_routing == 0:
            
                #routing table is not visiable
                for page in self.property_page[self.current_obj[1]]:
                    page.pack()
            else:
                pass
        else:

            #routing table is visiable
            for page in self.property_page[self.current_obj[1]]:
                page.pack_forget()

    ##
    # Show each routing table entry in the routing table frame
    # @param parent the parent window to show the entry visually
    # @param inter the interface that contains this routing table
    # @param item the index of the new entry in the table
    # @param num the serial number of the new entry in the table
    # @param entry_list the list of all entries so far
    def show_entry(self, parent, inter, item, num, entry_list):
        m_e=Label(parent, relief=SUNKEN, text=item.get_mask(), width=13, borderwidth=3, font = "DejaVu\ Sans 9 bold")
        m_e.grid(row=num)
        n_e=Entry(parent, width=13, font = "DejaVu\ Sans 9 bold")
        n_e.insert(END, item.get_gateway())
        n_e.grid(row=num, column=1)
        i_e=Entry(parent, width=13, font = "DejaVu\ Sans 9 bold")
        i_e.insert(END, item.get_ip())
        i_e.grid(row=num, column=2)
        entry_list[num]=[m_e, n_e, i_e]
        d_b=Button(parent, text="Delete", command=lambda : self.delete_entry(inter, 
                                                     item, num, m_e, n_e, i_e, d_b, entry_list))
        d_b.grid(row=num, column=3)


    ##
    # Add new routing entry to a routing table
    # @param parent the parent window to show the entry visually
    # @param inter the interface that contains this routing table
    # @param entry_list the list of all entries
    def add_entry(self, parent, inter, entry_list):
        new_entry=inter.add_entry()
        self.show_entry(parent, inter, new_entry, inter.get_next_entry_num(), entry_list)


    ##
    # Delete an routing table entry from the routing table
    # @param inter the interface that contains this routing table
    # @param item the index of the new entry in the table
    # @param num the serial number of the new entry in the table
    # @param m the mask field of the entry
    # @param n the nexthop field of the entry
    # @param i the ip address field of the entry
    # @param d the delete button
    # @param entry_list the list of all entries so far    
    def delete_entry(self, inter, item, num, m, n, i, d, entry_list):
        m.destroy()
        n.destroy()
        i.destroy()
        d.destroy()
        inter.delete_entry(item)
        del entry_list[num]


    ##
    # Delete the mouse pointed device
    #        If the pointed object is tag, omit it.
    #        If the pointed object is a connection or a wireless connection. Delete it.
    #        Otherwise, delete the pointed device and all connections associated with it.
    # @param cur Optinal. The current object 
    def delete(self, cur=None):
        
        if cur != None:

            #find the current device pointed by pointer
            o_id=self.canvas.find_withtag(CURRENT)
            if o_id and self.object_list[o_id[0]].get_type() != "tag" :
                self.current_obj=(o_id[0], self.object_list[o_id[0]])
            else:
                return

        if self.running:
            name = self.current_obj[1].name
            gw = Pyro.core.getProxyForURI(self.uri)
            state = gw.getState(name)
            if state != None:
                tkMessageBox.showinfo("Deleting a running device", "Cannot delete a running device")
                return
        
        #check the type of the device we want to delete 
        if self.current_obj[1].type == "connection" or self.current_obj[1].type == "wireless_connection":
        
            # need to update the devices connected by this connection
            c_dev_s=self.current_obj[1].get_start_device()
            c_dev_e=self.current_obj[1].get_end_device()
            c_dev_s_id=self.canvas.find_withtag(c_dev_s)[0]
            c_dev_e_id=self.canvas.find_withtag(c_dev_e)[0]
            self.object_list[c_dev_s_id].delete_connection(self.current_obj[1])
            self.object_list[c_dev_e_id].delete_connection(self.current_obj[1])
            self.balloon.tagbind(self.canvas, c_dev_e_id, self.object_list[c_dev_e_id].balloon_help())
            self.balloon.tagbind(self.canvas, c_dev_s_id, self.object_list[c_dev_s_id].balloon_help())
            
            # delete this connection
            del self.object_list[self.current_obj[0]]
            self.canvas.delete(self.current_obj[0])
            
            # update the connection list
            self.connection_list.remove([self.object_list[c_dev_s_id], self.object_list[c_dev_e_id]])
        
        else:
        
                # delete the tag associated with this device
            d_tag=self.current_obj[1].get_tag().get_name()
            tag_id=self.canvas.find_withtag(d_tag)[0]
            del self.object_list[tag_id]
            self.canvas.delete(tag_id)
            
            # delete all connections connection with this device
            con_list=self.current_obj[1].get_connection()[:]
            
            #special case: wireless router has two typies of connections
            if self.current_obj[1].type == "Wireless_access_point":
                con_list+=self.current_obj[1].get_wireless_connection()[:]
            
            for con in con_list:
                c_dev_s=con.get_start_device()
                c_dev_e=con.get_end_device()
                c_dev_s_id=self.canvas.find_withtag(c_dev_s)[0]
                c_dev_e_id=self.canvas.find_withtag(c_dev_e)[0]
                self.object_list[c_dev_s_id].delete_connection(con)
                self.object_list[c_dev_e_id].delete_connection(con)
                self.balloon.tagbind(self.canvas, c_dev_e_id, self.object_list[c_dev_e_id].balloon_help())
                self.balloon.tagbind(self.canvas, c_dev_s_id, self.object_list[c_dev_s_id].balloon_help())
                
                c_tag=con.get_name()
                c_tag_id=self.canvas.find_withtag(c_tag)[0]
                del self.object_list[c_tag_id]
                self.canvas.delete(c_tag_id)
        
            # delete this device
            del self.object_list[self.current_obj[0]]
            self.canvas.delete(self.current_obj[0])
        
        self.current_obj=None
        self.current_func=0
        

    ##
    # Compile the network topology
    def compile(self, event = None):
        global auto_routing
        global autogen
        
        #compile file handeler
        if self.filename == "" or not self.filename:
            msg="Please save model first!"
            tkMessageBox.showerror("Error", msg)
        else:
            if autogen:
                answer = tkMessageBox.askyesno("Continue?", "Auto-generating ip/mac addresses is currently enabled.  Any addresses you entered manually for UMLs will be overwritten, continue?")
                if not answer:
                    return
            self.save();
            comp=TopologyCompiler(self.object_list, self.log, self.filename, self.support_device, self.canvas, 
                                        auto_routing, self.dtd_filename, self.fs_filename, autogen)
            comp.compile()
                
            #update balloons for any generated information
            for obj_id, obj in self.object_list.iteritems():
                if obj.type == "Router" or obj.type == "UML" or obj.type == "Mobile" or obj.type == "Wireless_access_point":                         
                    self.balloon.tagbind(self.canvas, obj_id, obj.balloon_help()) 
    ##
    # screens need to be attached for the first time for them to receive outside commands    
    #TODO find a better solution
    def screen_test(self):
        time.sleep(0.5)       
        print "Testing screen...\t", 
        if os.system("screen -d WAP_1") == 0:
            print "[OK]"
        else:
            print "failed"
    
    ##
    # Retrieve stats from wap and insert into pop-up windows
    # @param mobile_list list of mobiles to refresh
    def refresh_mobiles(self, mobile_list):
        self.screen_test()
        texts = {}
        
        # make sure these windows don't get closed
        def donothing():
            pass

        # make a pop-up window for every mobile and hide them
        for key, mobile in mobile_list.iteritems():            
            toplevel = Toplevel(self.parent)
            toplevel.geometry("200x100")
            toplevel.title("%s" % mobile.name)
            toplevel.protocol('WM_DELETE_WINDOW', donothing)
            self.parent.update_idletasks()
            toplevel.withdraw()
            texts[mobile.name] = Text(toplevel)
            texts[mobile.name].pack()
            self.view_mobiles[mobile.name] = toplevel
                
        s_time = 1 - len(mobile_list) * 0.2
        if s_time < 0:
            s_time = 0

        # keep going until topology is stopped
        while self.running:
            # if no stats windows are showing, no need to compute
            if not self.current_mobile:
                time.sleep(1)
                continue
            # make the pop-up wait
            self.ready = False            
            for key, mobile in mobile_list.iteritems():
                # tell the real wap to display stats on screen
                os.system("screen -S WAP_1 -X eval 'stuff \"stats show node %s interface\"\\015' > /dev/null" % mobile.name.split("Mobile_")[-1])
                time.sleep(0.1)
                # tell screen to write stats to a file        
                os.system("screen -S WAP_1 -X eval hardcopy > /dev/null")             
                time.sleep(0.1)
                # copy stats to local folder                
                if os.system("cp $GINI_HOME/bin/hardcopy.0 $GINI_HOME/data/mobile_data/%s.stats 2> /dev/null" % mobile.name) != 0:
                    print "%s stats are not available" % mobile.name
                    continue             
                try:
                    # read stats
                    statsIn = open("%s/data/mobile_data/%s.stats" % (os.environ["GINI_HOME"], mobile.name), "r")
                except:
                    print "%s stats are not available" % mobile.name
                    continue 
               
                tx = ""
                rx = ""
                fer = ""                           
                for line in statsIn.readlines():
                    stats = line.split(":")
                    if line.find("TX packets") >= 0:
                        tx = stats[1].strip()
                    elif line.find("RX packets") >= 0:
                        rx = stats[1].strip()
                    elif line.find("Fading error rate") >= 0:
                        fer = stats[1].strip()
                # insert data into corresponding text box
                texts[mobile.name].delete(1.0, END)
                texts[mobile.name].insert(END, "TX packets: %s\n" % tx)
                texts[mobile.name].insert(END, "RX packets: %s\n" % rx)
                texts[mobile.name].insert(END, "Fading error rate: %s" % fer)
            self.ready = True
            time.sleep(s_time)
        os.system("rm -rf %s/data/mobile_data/*" % os.environ["GINI_HOME"])

    ##  
    # Actually start all devices in the network
    def run(self, event = None):
        
        # cannot run if already running
        if self.running:
            self.log.appendtext("\nAn instance is already running, please stop it first\n")
            return

        # cannot run without xml file
        if not os.access("%s.xml" % self.filename, os.F_OK):
            print "There is no xml file, please compile first"
            return                

        self.log.clear()
        self.log.appendtext("Starting configuration...\t")

        # clear old uml_mconsole files
        os.system("rm -rf ./.uml/*")

        # make data dir if necessary
        ghome = os.environ["GINI_HOME"]
        datadir = ghome+"/data"
        if not os.access(datadir,os.F_OK):
            os.mkdir(datadir, 0755)

        oldDir = os.getcwd()
        os.chdir(datadir)

        # make mobile_data dir if necessary
        if not os.access("mobile_data", os.F_OK):
            os.system("mkdir mobile_data")
        os.chdir("mobile_data")

        mobile_list={}
        # get coordinates for each wireless device
        for d_id, d_device in self.object_list.iteritems():
            if d_device.type == "Mobile":
                mobile_list[d_id]=d_device
                dataOut = open(d_device.name+".data", "w")
                x, y = d_device.get_coord()
                dataOut.write("%d,%d" % (x,y))
                dataOut.close()
            elif d_device.type == "Wireless_access_point":
                dataOut = open(d_device.name+".data", "w")
                x, y = d_device.get_coord()
                dataOut.write("%d,%d" % (x,y))
                dataOut.close()

        # retrieve canvas coordinates for wireless use
        if mobile_list:
            canvasOut = open("canvas.data", "w")
            canvasOut.write("%d,%d" % (self.canvas.winfo_width(), self.canvas.winfo_height()))
            canvasOut.close()

        os.chdir(oldDir)        

        #2. run the gloader
        command = "gloader -c %s.xml -s %s -r %s -u %s" % (self.filename, datadir, datadir, datadir)
#        command += " | tee gloader.out&"
        if os.system(command) == 0:   
            self.remote = False
            self.running = True            

#            while not os.access("gloader.out", os.F_OK):
#                time.sleep(0.5)

#            lines = ""
#            while not lines:
#                gloaderIn = open("gloader.out", "r")
#                lines = gloaderIn.readlines()
#                gloaderIn.close()
#            os.remove("gloader.out")

#           for line in lines:
#                self.log.appendtext(line)
#            gloaderIn.close()
            self.log.appendtext("OK\nDouble-click the components to interact\n")
            self.log.appendtext("Right-click for more options\n")
            tm = Pyro.core.getProxyForURI(self.uri2)
            tm.set_initialized(True)    
            if mobile_list:
                thread.start_new(self.refresh_mobiles, (mobile_list, ))
                os.system("screen -r WAP_1") 
        else:
#            while not os.access("gloader.out", os.F_OK):
#                time.sleep(0.5)

#            lines = ""
#            while not lines:
#                gloaderIn = open("gloader.out", "r")
#                lines = gloaderIn.readlines()
#                gloaderIn.close()
#            os.remove("gloader.out")
#            for line in lines:
#                self.log.appendtext(line)
            self.log.appendtext("failed\n")

    ##
    # Run topology remotely 
    def run_remote(self):
        
        # cannot run if already running
        if self.running:
            self.log.appendtext("An instance is already running, please stop it first\n")
            return

        # cannot run without xml file
        if not os.access("%s.xml" % self.filename, os.F_OK):
            print "There is no xml file, please compile first"
            return 

        self.log.clear()
        # clear old uml_mconsole files
        os.system("rm -rf ./.uml/*")

        # cannot run without _rdist configuration
        if not self.rdfilename:
            self.rdfilename = self.filename + "_rdist"           
        if os.access(self.rdfilename, os.F_OK):
            self.log.appendtext("Starting configuration remotely...\t")

            # run gdist
            command = "gdist -x %s.xml -i %s" % (self.filename, self.rdfilename)
#            command += " | tee gloader.out&"
            if os.system(command) == 0:
                self.remote = True
                self.running = True
                tm = Pyro.core.getProxyForURI(self.uri2)
                tm.set_initialized(True)

#                while os.system("killall -q -u %s -0 gdist" % os.getenv("USER")) == 0:
#                    time.sleep(0.5)

#                lines = ""
#                while not lines:
#                    gloaderIn = open("gloader.out", "r")
#                    lines = gloaderIn.readlines()
#                    gloaderIn.close()
#                os.remove("gloader.out")

#                for line in lines:
#                    self.log.appendtext(line)

                self.log.appendtext("OK\nDouble-click the components to interact\n")
                self.log.appendtext("Right-click on status to get the status of a component\n")             
            else:

#                while not os.access("gloader.out", os.F_OK):
#                    time.sleep(0.5)

#                lines = ""
#                while not lines:
#                    gloaderIn = open("gloader.out", "r")
#                    lines = gloaderIn.readlines()
#                    gloaderIn.close()
#                os.remove("gloader.out")

#                for line in lines:
#                    self.log.appendtext(line)

                self.log.appendtext("failed\n")
        else:
            self.log.appendtext("Error: please configure remote distribution first\n")

    ##
    # Stop a running topology
    def stop(self, event = None):
        global uml_kernel

        self.log.clear()

        # show task manager
        tm = Pyro.core.getProxyForURI(self.uri2)        
        if tm.get_state():
            tm.set_focus_requested(True)
        else:        
            tm.set_state(True)

        # cannot stop if nothing is running
        if not self.running:
            # kill any survivors from last run
            os.system("killall -u %s -q glinux uswitch grouter Graph_Stats" % os.getenv("USER"))
            self.log.appendtext("\nNothing is running\n")
            return
        #Stop the running devices
        if self.remote:
            command = "gdist -y %s.xml -i %s" % (self.filename, self.rdfilename)
            self.remote = False       
        else:
            command = "gloader -d"
            time.sleep(0.5)            
            tkMessageBox.showinfo("Stopping", "Press OK to stop now.  Please wait until this popup disappears before doing anything else.")
        
        self.log.appendtext("\nStopping the topology...\t")
#        command += " | tee gloader.out"       
        returnvalue = os.system(command)

#        gloaderIn = open("gloader.out", "r")
#        for line in gloaderIn.readlines():
#            self.log.appendtext(line)
#        gloaderIn.close()
#        os.remove("gloader.out")            

        if returnvalue == 0:
            self.log.appendtext("OK\n")
        else:
            self.log.appendtext("failed\n")
            return

        self.running = False        
	os.system("killall -u %s -q uswitch Graph_Stats %s" % (os.getenv("USER"), uml_kernel))
        tm = Pyro.core.getProxyForURI(self.uri2)

        # send signal that state lights can be removed
        tm.set_initialized(False)
        # send signal to close task manager
        tm.set_close_requested(True)
   
#        def clean():                        
#            time.sleep(5)
#            os.system("rm -rf ~/.uml/* ")
#        thread.start_new(clean, ())

        #os.system("killall -q glinux uswitch grouter")

    ##
    # some environment configuration
    def config(self):
    
        if self.current_view != None:
            self.current_view.focus_force()
            self.current_view.lift()
            return
    
        def close():
            self.current_view = None
            toplevel.destroy()

        # Create the toplevel to contain the env config window.
        toplevel = Toplevel(self.parent)
        toplevel.title("Environment Configuration")
        toplevel.protocol('WM_DELETE_WINDOW', close)
        #toplevel.resizable(0, 0)
        self.current_view = toplevel

        locationx = self.parent.winfo_rootx()
        locationy = self.parent.winfo_rooty()
        sizex = self.parent.winfo_width()
        sizey = self.parent.winfo_height()
        toplevel.geometry("+%d+%d" % (locationx+sizex/2-380, locationy+sizey/2-175))
        self.parent.update_idletasks()  

        env_g=Pmw.Group(toplevel, tag_text='Select File_System and XML Specification')
        env_g.pack(padx = 10, pady = 10, fill = 'both', expand = 1)

        #dtd frame
        dtd_f=Frame(env_g.interior())
        dtd_f.pack()
        self.dtd = Pmw.EntryField(dtd_f, labelpos = 'w', label_text = 'Select DTD File:')
        self.dtd.component('entry').configure(width=50)
        self.dtd.setvalue(self.dtd_filename)
        self.dtd.pack(side=LEFT, fill='x', expand=1, padx=10, pady=5)
        self.dtd_button = Button(dtd_f, text="Browse", command=self.select_dtd)
        self.dtd_button.pack(side=LEFT, padx=12, pady=5)

        #file system frame
        fs_f=Frame(env_g.interior())
        fs_f.pack()
        self.fs = Pmw.EntryField(fs_f, labelpos = 'w', label_text = 'Select File System:')
        self.fs.component('entry').configure(width=50)
        self.fs.setvalue(self.fs_filename)
        self.fs.pack(side=LEFT, fill='x', expand=1, padx=10, pady=5)
        self.fs_button = Button(fs_f, text="Browse", command=self.select_fs)
        self.fs_button.pack(side=LEFT, padx=12, pady=5)

        Pmw.alignlabels((self.dtd, self.fs))

        #add some buttons
        buttons=Pmw.ButtonBox(toplevel)
        buttons.pack(padx=10, pady=10, fill='x')
        
        buttons.add('Save', command=lambda : self.get_env(toplevel))
        buttons.add('Cancel', command=close)   

    ##
    # get the setting for file system and dtd
    # @param parent the window that contains the properties
    def get_env(self, parent):
        self.dtd_filename=self.dtd.getvalue()
        self.fs_filename=self.fs.getvalue()
        self.current_view = None
        parent.destroy() 

    ##
    # Select the dtd file
    def select_dtd(self):
        dtd_filename=tkFileDialog.askopenfilename()
        if dtd_filename:
            self.dtd.setvalue(dtd_filename)

    ##
    # Select the file system
    def select_fs(self):
        fs_filename=tkFileDialog.askopenfilename()
        if fs_filename:
            self.fs.setvalue(fs_filename)

    ##
    # Show the usage document
    def usage(self):
        os.system("firefox-3.0 "+self.basedir+"/doc/User_Guide.html &")

    ##
    # Show the about page
    def about(self):
    
        if self.current_view != None:
            self.current_view.focus_force()
            self.current_view.lift()
            return

        def close():
            self.current_view = None
            toplevel.destroy()

        # Create the toplevel to contain the about info.
        toplevel = Toplevel(self.parent)
        toplevel.title("About UML Topology Generator")
        toplevel.protocol('WM_DELETE_WINDOW', close)
        #toplevel.resizable(0, 0)
        self.current_view = toplevel

        locationx = self.parent.winfo_rootx()
        locationy = self.parent.winfo_rooty()
        sizex = self.parent.winfo_width()
        sizey = self.parent.winfo_height()
        toplevel.geometry("450x450+%d+%d" % (locationx+sizex/2-225, locationy+sizey/2-285))
        self.parent.update_idletasks()  

        #add a lab to contain the image
        #photo = PhotoImage(file="./gif/about.gif")
        frame=Frame(toplevel, width=50)
        frame.pack()
        self.photo = PhotoImage(file=self.basedir+"/gif/about.gif")
        about_c=Pmw.ScrolledCanvas(frame, borderframe=2, usehullsize = 1,
                                   hull_width=400, hull_height=190)      
        about_c.pack(padx = 10, pady = 10, fill = 'both', expand = 1)
        canvas=about_c.interior()
        canvas.config(bg="WHITE")
        canvas.create_image(195, 90, image=self.photo)


        #add a text frame
        text=Pmw.ScrolledText(frame, text_state='disabled', borderframe=1, 
                                  usehullsize = 1, hull_width=400, hull_height=200, text_wrap='word')
        text.pack(padx=10, pady=5)
        
        #add content
        text.appendtext("gBuilder is the GUI for the GINI toolkit. Both of them were developed in Advanced Network Research Lab (ANRL) of McGill University. See http://www.cs.mcgill.ca/~anrl/projects/gini/ for details.\n\nCredits:\n    Supervisor: Prof. Muthucumaru Maheswaran\n    Programmer: Song Gu\n    Tester: PhD. Balasubramaneyam MANIYMARAN\n    Revisor: Daniel Ng\n")
        
        #add a close button
        c_button=Button(toplevel, text="Close", command=close)
        c_button.pack(pady=5)
        c_button.focus()

    ##
    # Restart a specific device
    def restart(self):
        # cannot restart if nothing is running
        if not self.running:
            self.log.appendtext("Topology is not running\n")
            return
          
        name= self.current_obj[1].get_name()
        dtype = self.current_obj[1].get_type()
        gw = Pyro.core.getProxyForURI(self.uri)
        state = gw.getState(name)

        if not self.remote:
            oldDir = os.getcwd()

            # Restart router
            if dtype == "Router":
                print "\nRestarting Router %s...\t" % name,
                sys.stdout.flush()
                routerDir=os.environ["GINI_HOME"] +"/data/%s" %name
                success = True
                # Check if the config file still exist
                if (os.access(routerDir, os.F_OK)):
                    configFile = "%s/grouter.conf" % (routerDir)
                    if (os.access(configFile, os.F_OK)):
                        os.chdir(routerDir)
                        if os.access("startit.sh", os.F_OK):
                            # kill first if still alive
                            if state == "Attached" or state == "Detached":
                                pidIn = open("%s.pid" % name, "r")
                                pid = pidIn.readline().strip()
                                pidIn.close()
                                os.kill(int(pid),signal.SIGTERM)
                                time.sleep(1)                        
                            os.system("./startit.sh")
                            os.chdir(oldDir)
                            print "[OK]"
                            return
                os.chdir(oldDir)
                print "failed"

            # Restart UML
            elif  dtype == "UML" or dtype == "Mobile":
                # if device hasn't been run by gloader
                if state == None:
                    print "Cannot restart this device"
                    return
                mac = self.current_obj[1].get_interface()[0].req_properties["mac"]
                os.system("cp %s/tmp/UML_bak/%s.sh %s/tmp" % (os.environ["GINI_HOME"],mac.upper(),os.environ["GINI_HOME"]))
                print "\nRestarting UML %s...\t" % name,

                # kill first if still alive
                if state == "Attached" or state == "Detached": 
                    cmd="uml_mconsole " + name + " reboot"
                    os.system(cmd + " > /dev/null")
                else:
                    if os.access("%s/data/%s" % (os.environ["GINI_HOME"], name), os.F_OK):
                        os.chdir("%s/data/%s" % (os.environ["GINI_HOME"], name))
                        os.system("./startit.sh")
                        os.chdir(oldDir)
                    else:
                        print "failed"
                        return
                print "[OK]"               

            # Restart WAP
            elif dtype == "Wireless_access_point":
                num = name.split("Wireless_access_point_")[-1]
                # kill first if still alive
                if state == "Attached" or state == "Detached": 
                    os.system("screen -S WAP_%s -X eval quit" % num)
                    os.system("screen -S VWAP_%s -X eval quit" % num)
                oldDir = os.getcwd()
                os.chdir("%s/bin" % os.environ["GINI_HOME"])
                os.system("screen -d -m -L -S VWAP_%s Wireless_Parser" % num)
                os.system("./WAP%s_start.sh" % num)
                thread.start_new(self.screen_test, ())
                os.system("screen -r WAP_1")                
                os.chdir(oldDir)
                print "\nRestarting WAP %s...\t[OK]" % name
            else :
                self.log.appendtext("restarting the device has no effect for now\n")

        # remote case
        else:
            # Restart router or UML
            if dtype == "Router" or dtype == "UML":
                print "\nRestarting %s %s...\t" % (dtype, name),
                sys.stdout.flush()

                rdistIn = open(self.filename+"_rdist", "r")
                for line in rdistIn.readlines():
                    if line.find(name) >= 0:
                       parts = line.split(",")
                       host, path = parts[2].split(":")
                       break
                rdistIn.close()

                mconsole = False
                if state == "Attached" or state == "Detached": 
                    if dtype == "Router":
                        os.system("screen -S %s -X eval quit" % name)
                        time.sleep(1.5)
                    else:
                        mconsole = True

                if dtype == "Router":
                    retval = os.system("screen -d -m -L -S %s ssh %s -t %s/GINI/%s/./router.sh" % (name, host, path, name))
                else:
                    current_uml = self.object_list[self.current_obj[0]]
                    for inter in current_uml.get_interface():
                        mac = inter.req_properties["mac"]
                        break
                    retval = os.system("ssh %s cp '$GINI_HOME'/tmp/UML_bak/%s.sh '$GINI_HOME'/tmp" % (host, mac.upper()))
                    if mconsole:
                        retval += os.system("ssh %s uml_mconsole %s reboot > /dev/null" % (host, name))
                    else:
                        retval += os.system("screen -d -m -L -S %s ssh %s -t %s/GINI/%s/./startit.sh" % (name, host, path, name))
                if retval == 0:
                    print "[OK]"
                else:
                    print "failed"
                 
    ##
    # Kill a running device (Router, UML or WAP) 
    def kill(self):
        if not self.running:
            self.log.appendtext("Topology is not running\n")
            return

        name= self.current_obj[1].get_name()
        dtype = self.current_obj[1].get_type()

        if not self.remote:

            #1. kill a running UML
            if dtype == "UML" or dtype == "Mobile":
                cmd="uml_mconsole " + name + " cad"
                if os.system(cmd + " > /dev/null") == 0:
                    print "\nStopping UML %s...\t[OK]" % name
                else:
                    print "Stopping failed"
            #2. kill a running router
            elif dtype == "Router":
                #2.1 get the pid file in the gini_home
                if (os.environ.has_key("GINI_HOME")):            
                    giniEnv = os.environ["GINI_HOME"]               
                    if (giniEnv[len(giniEnv)-1] == '/'):
                        giniEnv = giniEnv[:len(giniEnv)-1]
                    pidFile = "%s/data/%s/%s.pid" % (giniEnv,name,name)
                    #2.2 Check the validity of the pid file
                    pidFileFound = True
                    if (os.access(pidFile, os.R_OK)):
                        # kill the router
                        fileIn = open(pidFile)
                        lines = fileIn.readlines()
                        fileIn.close()
                        os.kill(int(lines[0].strip()), signal.SIGTERM)
                        print "\nStopping router %s...\t[OK]" % name 
                    else:
                        pidFileFound = False
                        print "pidFile was not found" 

                    if not (pidFileFound):
                        print "Stopping router %s failed" % name
                        command = "screen -S %s -X eval " % name
                        os.system(command + "'stuff halt\\015'")
                        os.system(command + "'stuff yes\\015'")
                        print "The router %s was killed manually" % name
            
            elif dtype == "Wireless_access_point":
                os.system("screen -S WAP_%s -X eval quit" % self.current_obj[1].num)
                os.system("screen -S VWAP_%s -X eval quit" % self.current_obj[1].num)
                print "\nStopping wireless_access_point %s...\t[OK]" % name
            #4. Others devices    
            else :
                self.log.appendtext("\nNot implemented yet\n")
        # remote case
        else:
            if dtype == "Router" or dtype == "UML":
                print "\nStopping %s %s...\t" % (dtype, name),
                sys.stdout.flush()

                if dtype == "Router":
                    if os.system("screen -S %s -X eval quit" % name) == 0:
                        print "[OK]"
                    else:
                        print "failed"
                    return

                rdistIn = open(self.filename+"_rdist", "r")
                for line in rdistIn.readlines():
                    if line.find(name) >= 0:
                       parts = line.split(",")
                       host, path = parts[2].split(":")
                       break
                rdistIn.close()
                
                if os.system("ssh %s uml_mconsole %s cad > /dev/null" % (host, name)) == 0:
                    print "[OK]"
                else:
                    print "failed"

    ##
    # Control the visibility of the properties of wireless card for a mobile device
    # @param tag the switch to flip the visibility
    def wireless_card(self, tag):
        if tag == "User Specified Card":
            self.default_frame.pack(padx=10, pady=5, fill='x')
        else:
            self.default_frame.pack_forget()

    ##
    # Control the visibility of the properties of mobile mode for a mobile device    
    # @param tag the switch to flip the visibility
    def mobility_mode(self, tag):
        if tag == "Random Waypoint":
            self.random_frame.pack(padx=10, pady=5, fill='x')
        else:
            self.random_frame.pack_forget()

    ##
    # Control the visibility of the properties of mac mode for a mobile device    
    # @param tag the switch to flip the visibility
    def mac_mode(self, tag):
        if tag == "CSMA":
            self.CSMA_frame.pack(padx=10, pady=5, fill='x')
        else:
            self.CSMA_frame.pack_forget()

    ##
    # Control the visibility of the properties of mac mode for a mobile device    
    # @param tag the switch to flip the visibility
    def wireless_propagation(self, tag):
        if tag == "Shadowing":
            self.shadow_frame.pack(fill='x')
        else:
            self.shadow_frame.pack_forget()

    ##
    # Update the properties for wireless connection with user input
    # @param g_path property pathloss
    # @param g_dev property deviation
    # @param g_pro property propagation
    # @param g_fad property channel_type
    # @param c_n property noise
    # @param ref_d property distance
    # @param properties the property list
    def update_wireless_connection(self, g_path, g_dev, g_pro, g_fad, c_n, ref_d, properties):
        properties["propagation"]=g_pro.getvalue()
        properties["channel_type"]=g_fad.getvalue()
        properties["pathloss"]=g_path.getvalue()
        properties["deviation"]=g_dev.getvalue()
        properties["noise"]=c_n.getvalue()
        properties["distance"]=ref_d.getvalue()


    ##
    # Update the properties for wireless connection with user input, then exit
    # @param g_path property pathloss
    # @param g_dev property deviation
    # @param g_pro property propagation
    # @param g_fad property channel_type
    # @param c_n property noise
    # @param ref_d property distance
    # @param properties the property list
    # @param parent the parent window of the wirelss property window
    def save_wireless_connection(self, g_path, g_dev, g_pro, g_fad, c_n, ref_d, properties, parent):
        self.update_wireless_connection(g_path, g_dev, g_pro, g_fad, c_n, ref_d, properties)
        self.exit_wireless_connection(parent)

    ##
    # Exit from the wireless property window
    # @param parent the parent window of the wirelss property window
    def exit_wireless_connection(self, parent):
        parent.destroy()
        self.current_view = None
        # enable mouse event again for canvas
        self.bind_event()

    ##
    # Exit from the switch property window
    # @param parent the parent window of the switch property window
    def exit_switch(self, parent):
        parent.destroy()
        self.current_view = None    
        # enable mouse event again for canvas
        self.bind_event()

    ##
    # Exit from the subnet property window
    # @param parent the parent window of the subnet property window
    def exit_subnet(self, parent):
        parent.destroy()
        self.current_view = None
        # enable mouse event again for canvas
        self.bind_event()

    ## 
    # Update the UML machine or mobile properties with user input
    # @param page_list the list of interface pages
    # @param parent the parent window that contians this property window
    # @param ft property file type
    # @param fs property file system
    # @param mobile the flag to indicate if this device is a UML machine or a mobile device
    def save_UML(self, page_list, parent, ft="", fs=""):
        self.update_UML(page_list, ft, fs)
        self.clean_UML(parent, page_list)


    ## 
    # Update the UML machine or mobile properties with user input
    # @param page_list the list of interface pages
    # @param ft property file type
    # @param fs property file system
    # @param mobile the flag to indicate if this device is a UML machine or a mobile device
    def update_UML(self, page_list, ft="", fs=""):
        global auto_routing
       
        # save all user input for each interface
        for interface in self.current_obj[1].get_interface():
            
            has_subnet = False
            # save user input for the required properties
            properties=interface.get_req_properties()
            for entry in properties:
                if entry == "subnet":
                    has_subnet = True
                properties[entry]=page_list[interface][0][entry].get()
            
            if has_subnet:    
                for con in interface.get_shared_connections():
                    if con.get_start_device().find("Mobile") >= 0 or con.get_start_device().find("UML") >= 0:
                        target_device=self.object_list[self.canvas.find_withtag(con.get_start_device())[0]]
                        self.force_ip(target_device, self.current_obj[1], 8)
                    elif con.get_end_device().find("Mobile") >= 0 or con.get_end_device().find("UML") >= 0:                        
                        target_device=self.object_list[self.canvas.find_withtag(con.get_end_device())[0]]
                        self.force_ip(target_device, self.current_obj[1], 7)

            # save user input for the optional properties
#            properties=interface.get_opt_properties()
#            for entry in properties:
#                properties[entry]=page_list[interface][1][entry].get()
        
            # save user input for routing table entries
            i=0
            for entry in page_list[interface][2]:
                table=interface.get_table()
                #table[i].set_mask(page_list[interface][2][entry][0].get())
                table[i].set_gateway(page_list[interface][2][entry][1].get())
                table[i].set_ip(page_list[interface][2][entry][2].get())
                i+=1
        self.balloon.tagunbind(self.canvas, self.current_obj[0])
        self.balloon.tagbind(self.canvas, self.current_obj[0], self.current_obj[1].balloon_help())

        # update the file type and file system
        if fs != "" and ft != "":
            self.current_obj[1].set_filetype(ft)
            self.current_obj[1].set_filesystem(fs)
        

    ##
    # Delete user input routing table entry if it has empty gateway or ip field
    # @param parent the parent frame to show the routing entry
    # @param page_list the list of all interface pages        
    def clean_UML(self, parent, page_list):
        for interface in self.current_obj[1].get_interface():
        
            # clean invalid routing table entries
            table=interface.get_table()[:]
            for entry in table:
                if entry.get_mask() == "" or entry.get_gateway() == "" or entry.get_ip() == "":
                    interface.delete_entry(entry)
        parent.destroy()
        self.current_view = None
        # enable mouse event again for canvas
        self.bind_event()

    ##
    # Toggle the state of auto_routing (enabled or disabled)
    def toggleAutoroute(self):
        global auto_routing
        
        if auto_routing:
            auto_routing = 0
            self.log.appendtext("\nAuto-routing is disabled\n")
        else:
            auto_routing = 1
            self.log.appendtext("\nAuto-routing is enabled\n")

        if self.current_view and (self.current_obj[1].type == "UML" or self.current_obj[1].type == "Router"):
            if auto_routing:
                self.show_routing_table('No')
            else:
                self.current_view.geometry("500x670")
                self.show_routing_table('Yes') 

    ##
    # Toggle the state of autogen (enabled or disabled)
    def toggleAutogen(self, event = None):
        global autogen
        
        if autogen:
            autogen = False
            self.log.appendtext("\nAuto-generating ip/mac addresses is disabled\n")
        else:
            autogen = True
            self.log.appendtext("\nAuto-generating ip/mac addresses is enabled\n")
            self.log.appendtext("Please note that this feature is meant for simple topologies with 24-bit subnet masks\n")

    ##
    # Toggle the state of showing tips
    def toggle_tips(self):
        global tips

        if tips:
            tips = False
            tipsIn = open("%s/etc/tips" % os.environ["GINI_HOME"], "w")
            tipsIn.write("0")
            tipsIn.close()
            self.log.appendtext("\nShowing tips is disabled\n")
        else:
            tips = True            
            tipsIn = open("%s/etc/tips" % os.environ["GINI_HOME"], "w")
            tipsIn.write("1")
            tipsIn.close()
            self.log.appendtext("\nShowing tips is enabled\n")

    ##
    # Show tips if enabled
    def show_tips(self, parent, message):
        global tips
        v = IntVar()
        intermediate = False    # determines if there is a window between the root and tips    

        def close():
            if v.get():
                self.toggle_tips()
            if intermediate:
                self.current_view.unbind("<FocusIn>")
            else:
                self.current_view = None
            toplevel.destroy()

        def focus_child(e):
            toplevel.focus_force()
            toplevel.lift()        
               
        toplevel = Toplevel(parent)
        
        if self.current_view == None:
            self.current_view = toplevel
        else:
            self.current_view.bind("<FocusIn>", focus_child)
            intermediate = True                       

        bframe = Frame(toplevel)
        bframe.pack(side=BOTTOM, expand=1, fill='x')

        Checkbutton(bframe, variable=v, text="Do not show tips again").pack(side=LEFT, anchor='w')

        closebutton = Button(bframe, text="Close", command=close)
        closebutton.pack(side=RIGHT, anchor='e')
        closebutton.focus()
        
        text = Text(toplevel, wrap=WORD)
        text.pack()
        text.insert(END, message)
        text.config(state=DISABLED)

        locationx = self.parent.winfo_rootx()
        locationy = self.parent.winfo_rooty()
        sizex = self.parent.winfo_width()
        sizey = self.parent.winfo_height()
        toplevel.protocol('WM_DELETE_WINDOW', close)
        toplevel.geometry("500x250+%d+%d" % (locationx+sizex/2-250, locationy+sizey/2-175))
        self.parent.update_idletasks()    
                    

    ##
    # Force the ip of target_obj to match the subnet and mask
    # @param target_obj object to generate forced ip for
    # @param sub_obj subject that supplies subnet and mask to generate ip
    # @param mode determines the order of connections between the objects
    def force_ip(self, target_obj, sub_obj, mode):
        if mode >= 7:
            sub = sub_obj.get_wireless_interface().get_subnet()
            sub_obj.get_wireless_interface().set_mask("255.255.255.0")
            mask = sub_obj.get_wireless_interface().get_mask().split('.')
        else:
            sub = sub_obj.get_subnet()
            mask = sub_obj.get_mask().split('.')
        if self.valid_ip(sub):
            if mode == 6:
                #set subnet and mask of Switch object to that of Subnet object 
                target_obj.set_mask(sub_obj.get_connection(), sub, sub_obj.get_mask())
                for con in target_obj.get_connection():
                    uml_name = con.get_other_device(target_obj.get_name())
                    
                    #propogate change to connected UMLs
                    if uml_name.find("UML") >= 0:
                        uml_target = self.object_list[self.canvas.find_withtag(uml_name)[0]]
                        next_mode = 4                            
                        if uml_target.get_connection()[0].get_start_device() == uml_name:
                            next_mode = 5
                        self.force_ip(uml_target, target_obj, next_mode)
            else:
                for inter in target_obj.get_interface():
                    if mode == 1:
                        req_p = inter.get_req_properties()
                        break
                    elif mode == 2 or mode == 7:
                        if inter.get_connection().get_start_device() == sub_obj.get_name():
                            req_p = inter.get_req_properties()
                            break
                    elif mode == 3 or mode == 8:
                        if inter.get_connection().get_end_device() == sub_obj.get_name():
                            req_p = inter.get_req_properties()
                            break
                    elif mode == 4:
                        if inter.get_connection().get_start_device() == sub_obj.get_name():
                            req_p = inter.get_req_properties()
                    elif mode == 5:
                        if inter.get_connection().get_end_device() == sub_obj.get_name():            
                            req_p = inter.get_req_properties()
                try:
                    forced_ip = sub.split('.')
                    new_ipv4 = ""
                    
                    #generate forced part of ip according to mask
                    for i in range(3):
                        if mask[i] == "255":
                            new_ipv4 += forced_ip[i] + "."
                        else:
                            break
                  
                    #do not replace with new address if a full one is already specified and is valid
                    if req_p["ipv4"].find(new_ipv4) < 0 or req_p["ipv4"][len(req_p["ipv4"])-1] == ".":
                        req_p["ipv4"] = new_ipv4                
                except:
                    self.log.appendtext("Forcing ip failed with mode %d and start device %s\n" % (mode, inter.get_connection().get_start_device()))
                
            #update balloon info
            (xco, yco) = target_obj.get_coord()	
            self.balloon.tagbind(self.canvas, self.find_by_range(xco, yco), target_obj.balloon_help()) 

    ##
    # Bring up the task manager
    def manage(self, event = None):
        tm = Pyro.core.getProxyForURI(self.uri2)        
        if tm.get_state():
            tm.set_focus_requested(True)
        else:        
            tm.set_state(True)
        return

        if tm.get_state():
            return

    ##
    # Bring up the remote distribution window
    def remote_dist(self):                    
    
        global tips
   
        if self.current_view != None:
            self.current_view.focus_force()
            self.current_view.lift()
            return

        # make sure there is a save file first
        if not self.filename:
            msg="Please save model first!"
            showerror("Error", msg)
            return        
            
        h_width = 200
        h_height = 250
        devices = []
        m1 = []         #machine lists
        m2 = []
        m3 = []
        m4 = []
        m5 = []
        v1 = IntVar()   #enable checks
        v2 = IntVar()
        v3 = IntVar()
        v4 = IntVar()
        v5 = IntVar()

        combined = []
        
        hostnames = ["","","","",""]
        mlists = [m1,m2,m3,m4,m5]
        vargroup = [v1, v2, v3, v4, v5]

        # send a device to a machine or back to the list
        def send(source, destination):
            value = source.getvalue()
            # get and remove from source list
            currentlist_s = list(source.get())
            currentlist_s.remove(value[0])
            source.setlist(currentlist_s)
            
            # get and add to destination list
            currentlist_d = list(destination.get())
            currentlist_d.append(value[0])
            destination.setlist(currentlist_d)

        # send all specified devices of a machine back to the list
        def clearall(machine):
            currentlist = list(machine.get())
            machine.clear()
            newlist = list(allbox.get())
            newlist.extend(currentlist)
            allbox.setlist(newlist)        
        
        # bind right click to show menu for sending
        def right_click(event, machine):
            listbox = event.widget
            index = listbox.nearest(event.y)
            value = machine.get(index)
            if value:
                machine.setvalue(value)

                pop_menu_rdist=Menu(self.parent, tearoff=0)
                pop_menu_rdist.add_command(label="Send to All Devices", command=lambda: send(machine, allbox))

                # add enabled machines to right click destination choices
                if v1.get():
                    pop_menu_rdist.add_command(label="Send to M1", command=lambda: send(machine, machine1))
                if v2.get():
                    pop_menu_rdist.add_command(label="Send to M2", command=lambda: send(machine, machine2))
                if v3.get():
                    pop_menu_rdist.add_command(label="Send to M3", command=lambda: send(machine, machine3))
                if v4.get():
                    pop_menu_rdist.add_command(label="Send to M4", command=lambda: send(machine, machine4))
                if v5.get():
                    pop_menu_rdist.add_command(label="Send to M5", command=lambda: send(machine, machine5))
                
                pop_menu_rdist.add_separator()
                pop_menu_rdist.add_command(label="Clear All", command=lambda: clearall(machine))
                pop_menu_rdist.tk_popup(event.x_root, event.y_root)

        # auto assign devices to enabled machines
        def auto_assign():
            machinegroup2 = []
            # find which machines are enabled to distribute to
            for i in range(5):
                if vargroup[i].get():
                    machinegroup2.append(machinegroup[i])
            # if no machines available
            if not machinegroup2:
                # if there are actual devices to distribute
                if allbox.get():    
                    tkMessageBox.showerror("Assignment Error", "There are no specified machines to place these devices")
                    self.current_view.lift()
                else:
                    return
            else:
                i = 0
                for item in allbox.get():
                    currentlist = list(machinegroup2[i].get())
                    currentlist.append(item)
                    machinegroup2[i].setlist(currentlist)
                    i += 1
                    if i >= len(machinegroup2):
                        i = 0
                allbox.clear()        

        # test remote ssh
        def test():
            tkMessageBox.showinfo("Starting Test...", "Testing each machine remotely.  If the program stops responding, you may have been prompted for your password.  Press OK to start now")
            for i in range(5):
                if vargroup[i].get():
                    if os.system("ssh " + fieldgroup[i].getvalue().split(":")[0] + " exit") == 0:
                        tkMessageBox.showinfo("Success", "Remote machine %s connected successfully" % fieldgroup[i].getvalue())
                    else:
                        tkMessageBox.showerror("Failed", "Remote machine %s failed to connect" % fieldgroup[i].getvalue())
            self.current_view.lift()
              
        # save configuration      
        def save_rconf():
                        
            checks = vargroup
            fields = fieldgroup
            lists = mlists                       

            for i in range(5):
                lists[i] = machinegroup[i].get()

            error = 0
            if allbox.get():
                tkMessageBox.showerror("Distribution Error", "There are still devices to be placed")
                error = 1

            for i in range(5):
                if not checks[i].get() and lists[i]:
                    tkMessageBox.showerror("Distribution Error", "M%d has devices listed but is not enabled" % (i + 1))
                    error = 1
                elif checks[i].get() and not fields[i].getvalue():
                    tkMessageBox.showerror("Distribution Error", "M%d hostname not specified" % (i + 1))
                    error = 1

            if error:
                self.current_view.lift()
                return error

            r_file = open(r_path, "w")
            for i in range(5):
                r_file.write("m%d,%s,%s,%s\n" % (i+1, checks[i].get(), fields[i].getvalue(), ",".join(lists[i])))            
            r_file.close()        
            self.rdfilename = r_path
        
            return 0        

        # close handle
        def close():
            self.current_view = None
            toplevel.destroy()

        # OK button press
        def done():
            if save_rconf() == 0:        
                close()        
                
        r_path = self.filename + "_rdist"

        # if remote config already exists, load it
        if os.access(r_path, os.F_OK):
            r_file = open(r_path, "r")
            for line in r_file.readlines():
                parts = line.strip().split(",")
                
                for i in range(5):
                    if parts[0].find("m%d" % (i+1)) >= 0:
                        vargroup[i].set(int(parts[1]))
                        hostnames[i] = parts[2]
                        if parts[3]:
                            for j in range(3,len(parts)):
                                mlists[i].append(parts[j])       
                        break

            for i in range(5):
                combined.extend(mlists[i])

        else:
            r_file = None

        toplevel = Toplevel(self.parent)
        toplevel.title("Remote Distribution")        
        self.current_view = toplevel
        toplevel.protocol('WM_DELETE_WINDOW', close)
        #toplevel.resizable(0, 0)
        topframe = Frame(toplevel)
        bottomframe = Frame(toplevel)

        f0 = Frame(topframe)
        f1 = Frame(topframe)
        f2 = Frame(topframe)
        f3 = Frame(bottomframe)
        f4 = Frame(bottomframe)
        f5 = Frame(bottomframe)
        framegroup = [f1,f2,f3,f4,f5]
    
        # set up a dictionary to check for deleted elements
        present = {}
        for obj in combined:
            present[obj] = False

        for k, v in self.object_list.iteritems():
            # only show specified device types in list
            if v.type == "UML" or v.type == "Router" or v.type == "Switch":
                if combined.count(v.name):
                    present[v.name] = True
                    continue
                devices.append(v.name)
            
        # remove deleted elements from distribution
        for k, v in present.iteritems():
            if not v:
                for i in range(5):
                    try:
                        mlists[i].remove(k)
                        break
                    except:
                        continue                           

        allbox = Pmw.ScrolledListBox(f0, items = devices, usehullsize=1, hull_width=h_width, hull_height=h_height)
        machine1 = Pmw.ScrolledListBox(f1, items = m1, usehullsize=1, hull_width=h_width, hull_height=h_height)
        machine2 = Pmw.ScrolledListBox(f2, items = m2, usehullsize=1, hull_width=h_width, hull_height=h_height)
        machine3 = Pmw.ScrolledListBox(f3, items = m3, usehullsize=1, hull_width=h_width, hull_height=h_height)
        machine4 = Pmw.ScrolledListBox(f4, items = m4, usehullsize=1, hull_width=h_width, hull_height=h_height)
        machine5 = Pmw.ScrolledListBox(f5, items = m5, usehullsize=1, hull_width=h_width, hull_height=h_height)
        machinegroup = [machine1, machine2, machine3, machine4, machine5]        

        fieldgroup = []
        for i in range(5):
            fieldgroup.append(Pmw.EntryField(framegroup[i], value = hostnames[i], labelpos = 'w', label_text = 'M%d:' % (i+1), entry_width=18))        

        checkgroup = []
        for i in range(5):
            checkgroup.append(Checkbutton(framegroup[i], variable=vargroup[i]))            


        allbox.component('listbox').bind("<ButtonRelease-3>", lambda event: right_click(event, allbox)) 
        machine1.component('listbox').bind("<ButtonRelease-3>", lambda event: right_click(event, machine1))        
        machine2.component('listbox').bind("<ButtonRelease-3>", lambda event: right_click(event, machine2))
        machine3.component('listbox').bind("<ButtonRelease-3>", lambda event: right_click(event, machine3))
        machine4.component('listbox').bind("<ButtonRelease-3>", lambda event: right_click(event, machine4))
        machine5.component('listbox').bind("<ButtonRelease-3>", lambda event: right_click(event, machine5))

        all_label = Label(f0, text="All Devices")
        auto_button = Button(f0, text="Auto-Assign", command=auto_assign)
        ok_button = Button(toplevel, text="OK", command=done)
        apply_button = Button(toplevel, text="Apply", command=save_rconf)
        cancel_button = Button(toplevel, text="Cancel", command=close)        
        test_button = Button(toplevel, text="Test Remote Machines", command=test)

        topframe.pack(side=TOP)        
        bottomframe.pack(side=TOP)
        allbox.pack(side=BOTTOM, padx=5, pady=5)
        all_label.pack(side=LEFT, anchor=W, padx=2)
        auto_button.pack(side=RIGHT, anchor=E, padx=4)
        cancel_button.pack(side=RIGHT, anchor=SE, padx=15)
        apply_button.pack(side=RIGHT, anchor=S, padx=15)
        ok_button.pack(side=RIGHT, anchor=SW, padx=15)
        test_button.pack(side=RIGHT, anchor=SW, padx=15)
        
        f0.pack(side=LEFT, pady=4)

        for i in range(5):        
            machinegroup[i].pack(side=BOTTOM, padx=5, pady=5)
            checkgroup[i].pack(side=LEFT, padx=8)
            fieldgroup[i].pack(side=LEFT)
            framegroup[i].pack(side=LEFT)
        
        locationx = self.parent.winfo_rootx()
        locationy = self.parent.winfo_rooty()
        sizex = self.parent.winfo_width()
        sizey = self.parent.winfo_height()

        self.parent.update_idletasks()

        tsizex = toplevel.winfo_width()
        tsizey = toplevel.winfo_height()    
        toplevel.geometry("+%d+%d" % (locationx+(sizex-tsizex)/2, locationy+(sizey-tsizey)/2))

        self.parent.update_idletasks()

        if tips:
            self.show_tips(toplevel, "The All Devices list contains those that need to be placed.  To place a device, simply right click on the targeted device and send it wherever the options allow you to (based on which machines are enabled).  To specify a host, use the format [username]@[hostname]:[directory].  If a directory is not specified, one will be specified for you.  Otherwise, do NOT specify the $GINI_HOME directory as it may erase some important GINI files.  You can test that your machine is connecting properly to others by clicking Test Remote Machines.  If ssh keys are not set up properly, you should look at the terminal that you ran gbuilder in for a password prompt.")

    ##
    # Check if the ip is in valid format (from TopologyCompiler)
    # @param ip the ip to validate
    # @return 1 if the ip is valid;
    #         Otherwise, return 0
    def valid_ip(self, ip):

        #validate the formate
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', ip) == None:
            return 0

        p=re.compile('\d+')
        res=p.findall(ip)

        #each chunk shoule be >=0 and <256
        for chunk in res:
            if int(chunk) > 255:
                return 0
        return 1

    def get_attributes(self, name):
        for i in self.object_list: 
            #1. Look for the UML
            if name == self.object_list[i].get_name():
                #2. Get its coordinates
                x, y=self.object_list[i].get_coord()
                type = self.object_list[i].get_type()
                #3. Convert and exit from loop if found
                cx, cy = self.convert(x,y)
                break
            else :
                cx= 0
                cy= 0
        
        return cx, cy, type
  
    ##
    # Graph the data from a given router
    def graph(self):
        if not self.running:
            self.log.appendtext("Please run topology first\n")
            return
        if self.remote:
            self.log.appendtext("Graphing is only available for local running\n")
            return
        router=self.current_obj[1].get_name() 
        gw = Pyro.core.getProxyForURI(self.uri)
        state = gw.getState(router)
        if state == "killed":
            self.log.appendtext("This router is not running\n")    
            return
        
        def run():
            os.system("Graph_Stats %s" % router)
        thread.start_new(run, ())
              
    ##
    # Open wireshark with the given router 
    def wireshark(self):
        if not self.running:
            self.log.appendtext("Please run topology first\n")
            return
        if self.remote:
            self.log.appendtext("Wireshark is only available for local running\n")
            return
        router = self.current_obj[1].get_name()
        if os.fork() == 0:
            if os.system("wireshark -S -k -l -i %s/data/%s/%s.port" % (os.environ["GINI_HOME"], router, router)) != 0:
                print "Starting wireshark failed, or was terminated unexpectedly.  Please check that wireshark is installed or is working properly"
                os._exit(1) 
            os._exit(0)
#------------------------------------------------------------------------------ 
# Use Pyro to share data between TaskManager and gbuilder
#------------------------------------------------------------------------------

##
# Class to write on the panel  
# @param controlPanel : panel lauched with gbuilder
# @param list_obj : list of object present on the panel 
class GiniWriter(Pyro.core.ObjBase):
    
    ##
    # Constructor : 
    #1. Get the current onstance of controlPanel
    #2. Create an empty list to store a history for each element of the topology
    def __init__(self, controlPanel):
        Pyro.core.ObjBase.__init__(self)
        self.controlPanel=controlPanel
        self.list_obj=[]
        self.new_ovals = []
        self.old_ovals = []
        self.states = {}

    def cleanOvals(self):
        for oval in self.old_ovals:
            self.controlPanel.canvas.delete(oval)
        del self.old_ovals[:]

    def shiftOvals(self):
        self.old_ovals.extend(self.new_ovals)
        del self.new_ovals[:]
  
    def setState(self, name, state):
        self.states[name] = state
    
    def cleanStates(self):
        self.states.clear()                    

    def getState(self, name):
        try:
            if name.find("Wireless_access_point") >= 0:
                wap = "WAP_" + name.split("Wireless_access_point_")[-1]            
                return self.states[wap][0]
            else:
                return self.states[name][0]
        except:
            return None

    def getOval(self, name):
        if name.find("Wireless_access_point") >= 0:
            wap = "WAP_" + name.split("Wireless_access_point_")[-1]            
            return self.states[wap][1]
        else:
            return self.states[name][1]

    ##
    # Add a colored spot near an element of the topology
    # @param name : name of the element   
    # @param state : determines the color of the element    
    def createMsgStatus(self,name,state):
        try:                                   
            # Determine color from state
            if state == "Detached":
                color = "orange"
            elif state == "Attached":
                color = "green"
            else:
                color = "red"

            if self.states.has_key(name):
                (old_state, oval) = self.states[name]
                if state == old_state:
                    self.old_ovals.remove(oval)
                    self.new_ovals.append(oval)
                    return
                else:
                    [l1,l2,l3,l4] = self.controlPanel.canvas.coords(oval)
                
            else:
                # Look for a element in the topology and get its position
                if name.find("VWAP") == 0:
                    return
                elif name.find("WAP") >= 0:
                    (x_canvas,y_canvas, type)= self.controlPanel.get_attributes("Wireless_access_point_%s" % name.split("WAP_")[-1])            
                else:
                    (x_canvas,y_canvas, type)= self.controlPanel.get_attributes(name)
            
                # Paint the spot according to device
                if type == "UML":
                    l1 = x_canvas-13 
                    l2 = y_canvas+7
                    l3 = x_canvas-4 
                    l4 = y_canvas-2
                elif type == "Mobile":
                    l1 = x_canvas-9
                    l2 = y_canvas+23
                    l3 = x_canvas
                    l4 = y_canvas+14
                elif type == "Router":
                    l1 = x_canvas-21
                    l2 = y_canvas+5
                    l3 = x_canvas-12
                    l4 = y_canvas-4
                elif type == "Wireless_access_point":
                    l1 = x_canvas-16
                    l2 = y_canvas+21
                    l3 = x_canvas-7
                    l4 = y_canvas+12
                #For the moment, the other elements don't have states.
                else :
                    return
   
            oval = self.controlPanel.canvas.create_oval(l1,l2,l3,l4,fill= color)
            self.new_ovals.append(oval)
            self.states[name] = (state,oval)
        except Exception, inst:
            print name, state
            print type(inst)
            print inst
            print inst.args

##
# Class to manage running devices in GINI
class TaskManager(Pyro.core.ObjBase):
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
        self.procdic = {}           # this procdic is used to notify the task manager of switches and remote devices
        self.state = False          # state defines if the task manager window is open
        self.initialized = False    # initialized defines if the TM is ready to refresh the task list 
        self.focus_requested = False
        self.close_requested = False

    def get_focus_requested(self):
        return self.focus_requested

    def set_focus_requested(self, focus):
        self.focus_requested = focus

    def get_close_requested(self):
        return self.close_requested

    def set_close_requested(self, close):
        self.close_requested = close

    def get_procdic(self):
        return self.procdic

    def set_procdic(self, procdic):
        self.procdic = procdic
                        
    def notify(self, name, pid, host):
        self.procdic[name] = (pid, host)
    
    def set_state(self, state):
        self.state = state

    def set_initialized(self, initialized):
        self.initialized = initialized

    def get_state(self):
        return self.state

    # used to be accessed for ginisuperviser
    def get_initialized(self):
        return self.initialized

##
#Class to launch the server for remote control objects  
class GbuilderServer(threading.Thread):
    ##
    # Constructor : 
    # inherit from threading class
    # use the attribute controlPanel for GiniWriter
    def __init__(self, controlPanel):
        threading.Thread.__init__(self) 
        self.controlPanel=controlPanel
        
    def run(self):
        sys.stdout = open("/dev/null", "w")
        #1. initialize Pyro before using the server program
        Pyro.core.initServer()
        #2. Create a Pyro Daemon : necessary for accepting incoming requests
        # host="127.0.0.1" use the loopback in case the physical machine 
        # is not connected to a network
        # port =9000 but if it is busy,try the next higher port, and so on
        try:
            self.daemon = Pyro.core.Daemon(host="127.0.0.1", port=9000)
            #self.daemon2 = Pyro.core.Daemon(host="127.0.0.1", port=9001)
        except NamingError:
            pass

        #3. Create object instance of GiniWriter
        uri=self.daemon.connect(GiniWriter(self.controlPanel),"giniServerInstance")
        uri2=self.daemon.connect(TaskManager(), "tm")
        print "The daemon runs on port:",self.daemon.port
        print "The giniwriter object's uri is:",uri
        print "The taskmanager object's uri is:",uri2
        uriOut = open("%s/tmp/pyro_uris" % os.environ["GINI_HOME"], "w")
        uriOut.write("%s\n" % uri)
        uriOut.write("%s\n" % uri2)
        uriOut.close()
        sys.stdout = sys.__stdout__      

        #4. Put uri in attibute of controlPanel in order to synchronise 
        #   the server and the client
        self.controlPanel.uri = uri
        self.controlPanel.uri2 = uri2
        
        try:
            self.daemon.requestLoop()
        finally:
            self.daemon.shutdown(True)
#------------------------------------------------------------------------------

def onCloseEventHandler():
    global uml_kernel
       
    if len(app.object_list) > 0:
        answer = tkMessageBox._show("Save current?", "Do you want to save current topology?", icon=tkMessageBox.QUESTION, type=tkMessageBox.YESNOCANCEL)             
        answer = str(answer)        
        if answer == "yes":
            app.save()
        elif answer == "cancel":
            return        

        if app.remote:
            app.stop()

        for id, obj in app.object_list.iteritems():
            app.canvas.delete(id)
        app.s_canvas.pack_forget()
        del app.s_canvas
        app.init_condition()
       
    os.system("killall -u %s -q  TaskManager Graph_Stats Wireless_Parser" % os.getenv("USER")) 
    os.system("rm -f %s/tmp/pyro_uris" % os.environ["GINI_HOME"])
    os.system("rm -f %s/tmp/UML_bak/*.sh" % os.environ["GINI_HOME"])
    os.system("rm -f %s/bin/*.0" % os.environ["GINI_HOME"])
    os.system("killall -u %s -q gloader uswitch glinux grouter gwcenter %s" % (os.getenv("USER"), uml_kernel)) 
    sys.exit(0)
    
#### -------------- MAIN Loop ----------------####
if __name__ == '__main__':
    
    if not os.environ.has_key("GINI_HOME"):
        print "environment variable $GINI_HOME not set, please set it for GINI to run properly"
        sys.exit(1)

    path = os.environ["GINI_HOME"] + "/share/gbuilder"

    #1. Lauching the frame 
    root = Tk()
    root.protocol('WM_DELETE_WINDOW', onCloseEventHandler)
    Pmw.initialise(root)
    root.minsize(600, 480)
    root.title(title)
    root.option_add("*font", "DejaVu\ Sans 10 bold")

    app = ControlPanel(root, path)
    signal.signal(signal.SIGINT, app.quit)
        
    # 2. Launching the server 
    GbuilderServer(app).start()
    # 3. Launching the client : TaskManager as soon as Pyro server has started
    while app.uri=="":
         pass
    taskmanager=os.fork()
    if taskmanager == 0:
        os.system("TaskManager")
        sys.exit(0)
    else:
        root.mainloop()
        app.close()

