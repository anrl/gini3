#!/usr/bin/python

# Written by Daniel Ng

from Tkinter import *        # The Tk package
import Pmw                   # The Python MegaWidget package
import thread
import os
import time
import signal
import sys

vector = [0,0,0,0,0]

vector2 = [0,0,0,0,0]

#def animate():
    # This function is completely pointless, but demonstrates
    # that it's easy to update a graph "runtime".
#    thread.start_new(run, ())

def animate():
    x = 0
    #i = 0
    toggle = False
    while 1:                                 
        vector_x.delete(0)
        vector_x.append(x*2)

        vector_y[0][0].delete(0)                     
        vector_y[0][0].append(vector[0])
        vector_y[1][0].delete(0)                     
        vector_y[1][0].append(vector2[0])

        for i in range(ncurves):        
            vector_y[2][i].delete(0)                     
            vector_y[2][i].append(vector[i+1])
            vector_y[3][i].delete(0)                     
            vector_y[3][i].append(vector2[i+1])
            #vector_y[i][1].delete(0)       
            #vector_y[i][1].append(vector2[i])

        time.sleep(2)       
        master.update_idletasks()   # update screen
            
        x+=1
        #if i == 7:
            #i = 0
            #toggle = not toggle
        #    pass        
        #else:
        #    i+=1

def symbolsOnOff():
    global symbols
    symbols = not symbols

    for curvename in g.element_show():
        if symbols:
            g.element_configure(curvename, symbol='diamond')
        else:
            g.element_configure(curvename, symbol='')
            

def smooth():
    global smoothing
    
    if smoothing == 'linear': smoothing='quadratic'
    elif smoothing == 'quadratic': smoothing='natural'
    elif smoothing == 'natural': smoothing='step'
    else: smoothing = 'linear'

    for curvename in g.element_show():
        g.element_configure(curvename, smooth=smoothing)

def transformer(event):
    (x,y) = (event.x, event.y)
    print "(%d,%d)" %(x,y),

    # inversetransform clicked pos to get axis-coordinates.
    (x,y) = (g.xaxis_invtransform(x), g.yaxis_invtransform(y))
    print "--> (%f,%f)" %(x,y),

    # transform back to get original window-coordinates.
    # (not always exact because of round-off errors.)
    (x,y) = (g.xaxis_transform(x), g.yaxis_transform(y))
    print "--> (%d,%d)" %(x,y)

def exit(arg1 = None, arg2 = None):
    global router
    os.system("ps -u %s -ao pid,command | grep \"cat %s.info\" > cat.pid" % (os.getenv("USER"), router))
    pidIn = open("cat.pid", "r")
    for line in pidIn.readlines():
        if line.find("grep ") >= 0:
            continue
        parts = line.strip().split(" ")
#        print parts[0]
        os.system("kill %s" % parts[0])
    pidIn.close()
    os.remove("cat.pid")
    sys.exit(0)

def runstats():
    global vector, vector2, router
    os.chdir("%s/data/%s" % (os.environ["GINI_HOME"], router))
    routernum = router.split("_")[-1]
    os.system("cat %s.info > Router%s.info &" % (router, routernum))
    inqueues = []
    while 1:

        try:
            infoIn = open("Router%s.info" % routernum, "r")
        except:
            print "\nGraphing no longer available\n"
            sys.exit(1)
            
        lines = infoIn.readlines()
        while not lines:
            time.sleep(0.5)
            lines = infoIn.readlines()

        for line in lines:
            if line.find("//") == 0 or line.find("\x00") == 0:
                continue
            try:
                (date,queue,size,rate) = line.strip().split("\t")
            except:
                print "exception caught"
                print line                
            if queue.find("outputQueue") >= 0:
                vector[0] = rate
                vector2[0] = size
            else:
                try:
                    index = inqueues.index(queue) + 1
                except:
                    inqueues.append(queue)
                    index = inqueues.index(queue) + 1
                    g3.element_configure("inputQ%d" % index, label = queue)
                    g4.element_configure("inputQ%d" % index, label = queue)
            
                vector[index] = rate
                vector2[index] = size 
#                vector[2] = float(rate) + 1000
#                vector2[2] = float(size) + 50             
#                vector[3] = float(rate) + 2000
#                vector2[3] = float(size) + 100
#                vector[4] = float(rate) + 3000
#                vector2[4] = float(size) + 150

        infoIn.close()
        open("Router%s.info" % routernum, "w").close()    
        time.sleep(2)

def resize():
    global size
    if size == "Large":        
        sizeButton.config(text=size)
        size = "Small"
        for graph in graphs:
            graph.configure(width="3i", height="2.5i")
    else:        
        sizeButton.config(text=size)
        size = "Large"        
        for graph in graphs:
            graph.configure(width="5i", height="4i")
  

try:
    router = sys.argv[1]
except:
    print "need router name as argument"
    sys.exit(1)

master = Tk()                # build Tk-environment
f1 = Frame(master)
f2 = Frame(master)

ncurves = 4                  # draw 4 curves
npoints = 4                  # use  8 points on each curve
smoothing='quadratic'
symbols  = 0
size = "Small"

# In this example we use Pmw.Blt.Vectors. These can mostly be used like 
# a normal list, but changes will be updated in the graph automatically.
# Using Pmw.Blt.Vectors is often slower, but in this case very convenient.
vector_x = Pmw.Blt.Vector()   
vector_y = []

for i in range(4):
    vector_y.append([])
    for y in range(ncurves):
        vector_y[i].append(Pmw.Blt.Vector())          # make vector for y-axis
        if i < 2:
            break

for x in range(npoints):                      # for each point...
    vector_x.append(x)                     # make an x-value

    # fill vectors with cool graphs
    for i in range(4):
        for c in range(ncurves):                   # for each curve...
            vector_y[i][c].append(0)   # make an y-value
            if i < 2:
                break

g = Pmw.Blt.Graph(f1)                     # make a new graph area
g2 = Pmw.Blt.Graph(f1)
g3 = Pmw.Blt.Graph(f2)
g4 = Pmw.Blt.Graph(f2)
#g.bind("<ButtonPress>", transformer)
graphs = [g,g2,g3,g4]
g.pack(side=LEFT, expand=1, fill='both')
g2.pack(side=LEFT, expand=1, fill='both')
g3.pack(side=LEFT, expand=1, fill='both')
g4.pack(side=LEFT, expand=1, fill='both')
f1.pack(side=TOP)
f2.pack(side=TOP)

g.line_create("outputQ",                   # and create the graph
               xdata=vector_x,              # with x data,
               ydata=vector_y[0][0],           # and  y data
               dashes=0,                    # and no dashed line
               linewidth=2,                 # and 2 pixels wide
               symbol='')                   # ...and no disks

g2.line_create("outputQ",                   # and create the graph
               xdata=vector_x,              # with x data,
               ydata=vector_y[1][0],           # and  y data
               dashes=0,                    # and no dashed line
               linewidth=2,                 # and 2 pixels wide
               symbol='')                   # ...and no disks

for c in range(ncurves):                      # for each curve...
    g3.line_create("inputQ%d" % (c+1),                   # and create the graph
                   xdata=vector_x,              # with x data,
                   ydata=vector_y[2][c],           # and  y data
                   dashes=0,                    # and no dashed line
                   linewidth=2,                 # and 2 pixels wide
                   symbol='')                   # ...and no disks

    g4.line_create("inputQ%d" % (c+1),                   # and create the graph
                   xdata=vector_x,              # with x data,
                   ydata=vector_y[3][c],           # and  y data
                   dashes=0,                    # and no dashed line
                   linewidth=2,                 # and 2 pixels wide
                   symbol='')                   # ...and no disks

for graph in graphs:
    graph.configure(plotbackground="black", borderwidth=2, relief="raised", rightmargin=15, width="3i", height="2.5i")   
    graph.axis_configure("x", title="Time (seconds)")
    graph.axis_configure("y", title="Queue Rate", min="0")
    graph.legend_configure(position="plotarea", anchor="ne")

# enter a title       
g.configure(title='Throughput')
g.element_configure("outputQ", color="green", smooth=smoothing)       

g2.configure(title='Queue Size')
g2.element_configure("outputQ", color="green", smooth=smoothing)
g2.axis_configure("y", title="Queue Size")

g3.configure(title='Throughput')
g4.configure(title='Queue Size')
g4.axis_configure("y", title="Queue Size") 

colors = ["red", "blue", "white", "orange"]
for c in range(ncurves):
    g3.element_configure("inputQ%d" % (c+1), color=colors[c], smooth=smoothing)
    g4.element_configure("inputQ%d" % (c+1), color=colors[c], smooth=smoothing)

# make s row of buttons
buttons = Pmw.ButtonBox(master, labelpos='n', label_text='Options')
buttons.pack(side=TOP, anchor=CENTER)

#buttons.add('Grid',       command=g.grid_toggle)
#buttons.add('Symbols',    command=symbolsOnOff)
#buttons.add('Smooth',     command=smooth)
#buttons.add('Animate',    command=animate)
sizeButton = buttons.add('Large',      command=resize)
buttons.add('Quit',       command=exit)

master.protocol('WM_DELETE_WINDOW', exit)
master.title('Graph for %s' % router)
thread.start_new(runstats, ())
thread.start_new(animate, ())
master.mainloop()                              # ...and wait for input




