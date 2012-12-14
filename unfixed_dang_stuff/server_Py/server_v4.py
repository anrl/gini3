# -*- coding: utf-8 -*-
# server program
import socket
import thread

aList = []  # for recording the register computer


c1,c2,c3,c4,c5,c6,c7,c8,c9,c10 = [0,0,0,0,0,0,0,0,0,0]
conn = [c1,c2,c3,c4,c5,c6,c7,c8,c9,c10]

def regreceiver(): # add register computer information

    HOST = 'localhost'    #'localhost'        # Symbolic name meaning all available interfaces
    PORT = 50007              # Arbitrary non-privileged port
    server_real = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_real.bind((HOST, PORT))
    server_real.listen(10)

    i = 0 
    while True:  
        print 'waiting for connection…'
        conn[i], addr = server_real.accept() 
        print 'Connected by', addr
        thread.start_new_thread(listener, (conn[i],addr))
        print i
        i = i + 1
        
        
def listener(conn,addr):        
    while True:
        data = conn.recv(1024)
        if not data: break
        conn.send('ok')
        if 'start' in data:
            aList.append(data)
        print aList     
    conn.close()

def regsender(): # send register info to gini

    HOST = 'localhost'    #'localhost'        # Symbolic name meaning all available interfaces
    PORT = 23456              # Arbitrary non-privileged port
    server_gini = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_gini.bind((HOST, PORT))
    server_gini.listen(5)
    togini, addr = server_gini.accept()
    print 'Connected by', addr

    while True:
        data = togini.recv(1024)
        if not data: break
        if 'getinfo' in data: #string.find
            for i in range(len(aList)):
                togini.send(aList[i])
            togini.send('finish')
        elif 'assign' in data:
            togini.send('assign accepted finish')
            print data
            data = data[len('assign')+1:]
            data_list = data.split(",",1)
            for index in range(len(aList)):
                if data_list[0] in aList[index]:
                    break
            if aList:
                conn[index].send(data)
                print index
        else:
            togini.send('bad command finish')    
    togini.close()
    
def main():
    print 'starting...'

    thread.start_new_thread(regreceiver, ())
    thread.start_new_thread(regsender, ())

    command = raw_input('> ')
    if command == 'quit':
        pass
    else:
        while True:
            pass
    
    print 'all done'

if __name__=='__main__':
    main()
    
