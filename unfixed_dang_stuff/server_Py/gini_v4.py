# Echo client program
import socket
from time import sleep
import thread

HOST = '142.157.62.121'    # The remote host
PORT = 23456              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
datarev = ''
name = []
ip = []
port = []

def regreceiver():
    data_temp = ''
    
    while True:
        datau = s.recv(4096)
        if not datau: break
        print datau   
        if 'finish' in datau:
            print 'c'
            data = data_temp + datau
            data_temp = ''
            print 'd'
        else:
            print 'a'
            data_temp = data_temp + datau
            print 'b'
            continue
                    
        if data != 'assign accepted finish':
            #note: the following should be add in the processing part finally
            #datarev == data
            datarev = data.split('end')
    
            for i in range(len(datarev)-1):
                name.append(datarev[i].split(',')[1])
                ip.append(datarev[i].split(',')[2])
                port.append(datarev[i].split(',')[3])
            print name
            print ip
            print port
    s.close()

def main():

    thread.start_new_thread(regreceiver,())
    s.send('getinfo')
    sleep(5)
    s.send('assign,start,shiyiwei,999.999.999.999,9999,end')
    #s.close()
    #s.send('assign,start,'+hostname+','+ip_addr+','+mac_addr+','+'end')
    while True:
        pass

if __name__=='__main__':
    main()
