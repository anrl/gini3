# Echo client program
import socket

HOST = '142.157.62.121'   #'localhost'    # The remote host
PORT = 50007              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))


data = raw_input('> ')
s.send(data)
    
while True:    
    datarev = s.recv(1024)
    print 'Received', repr(datarev)

s.close()
