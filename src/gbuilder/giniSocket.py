##===============================================================================
## gbuilder will create sockets: if a router is restarted, it will use the old 
## socket and not a new one.
##===============================================================================
#import socket
#import thread           # to do multithtreading : fisrt step
#import time             # to differ starting
#import threading        # class to do multithtreading
#
#HOST = ''               # Symbolic name meaning the local host
#
###
##Class to launch the server for remote control objects  
#class giniSocket(threading.Thread):
#    ##
#    # Constructor : 
#    # inherit from threading class
#    # use the attribute controlPanel for GiniWriter
#    def __init__(self, controlPanel):
#        threading.Thread.__init__(self) 
#        self.controlPanel=controlPanel
#    ##
#    # Create server socket
#    def serverSocket():
#        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        s.bind((HOST, PORT))
#        s.listen(1)
#        conn, addr = s.accept()
#        print 'Connected by', addr
#        while 1:
#            data = conn.recv(1024)
#            if not data: break
#            conn.send(data)
#        conn.close()
#        
#    ##
#    # Create Client socket
#    def clientSocket():
#        # Echo client program
#        
#        HOST = 'localhost'        # The remote host
#        PORT = 9008              # The same port as used by the server
#        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        s.connect((HOST, PORT))
#        s.send('Hello, world')
#        data = s.recv(1024)
#        s.close()
#        print 'Received', repr(data)

