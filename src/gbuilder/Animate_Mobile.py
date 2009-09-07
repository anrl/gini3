from math import *
from Wireless_Connection import *
from Mobile import *
import time
import pdb
import os



##
# Class: the module to animate the movement of all mobile devices
class Animate_Mobile:

    ##
    # Constructor: Initial the mobile animator
    # @param filename the file name of the network model, used to find the dir of data file for the mobiles
    # @param object_list the list of all devices on the canvas
    # @param canvas the canvas
    def __init__(self, filename, object_list, canvas):
        self.object_list=object_list
        self.canvas=canvas
        self.filename=filename

        #speed of the mobile device: pixel/sec
        self.speed=1 


    ##
    # Animate all mobile devices
    # @param mobile_list the list of all mobile devices
    def animation(self, mobile_list):

        #initialization before animation, first get the coordinates file for each mobile device
        device_data={}
        for d_id, device in mobile_list.iteritems():
            path=os.path.dirname(self.filename);
            data_filename=path+"/mobile_data/"+device.get_name()+".data"
            data=open(data_filename, "r")
            device_data[device]=(d_id, data)
            

        # start a loop to update all mobile devices to new place
        mobile_devices=mobile_list.copy()
        while len(mobile_devices) != 0:
            for d_id, device in mobile_list.iteritems():
                if mobile_devices.has_key(d_id):
                    data=device_data[device][1]
                    line=data.readline()
        
                    #remove the device if reach the end of file
                    if line == "":
                        del mobile_devices[d_id]

                    else:   
                        line=line.strip()
                        (newx,newy)=line.split(',')
                        newx=int(newx)
                        newy=int(newy)
                
                        #update the device to the new place
                        (lastx, lasty)=device.get_coord()
                        self.canvas.move(d_id, newx-lastx, newy-lasty)

                        #move the tag together
                        tag_id=self.canvas.find_withtag(device.get_tag().get_name())[0]
                        self.canvas.move(tag_id, newx-lastx, newy-lasty)
                        self.object_list[tag_id].update_coord(newx, newy)


                        #update the wireless connection
                        con_list=device.get_connection()
                        for con in con_list:

                            #back up the info of the connection
                            current_name=device.get_name()
                            c_name=con.get_name()
                            c_id=self.canvas.find_withtag(c_name)[0]
                            c_dev_s=con.get_start_device()
                            c_dev_e=con.get_end_device()
                            s_id=self.canvas.find_withtag(c_dev_s)[0]
                            e_id=self.canvas.find_withtag(c_dev_e)[0]
                            cx_e, cy_e=self.object_list[e_id].get_coord()
                            cx_s, cy_s=self.object_list[s_id].get_coord()  

                            #find out which end need to be updated and create a new connection
                            if current_name == c_dev_s:
                                self.object_list[c_id].update_start_point(newx, newy)
                                self.canvas.coords(c_id, newx,newy,cx_e,cy_e)
                    
                            else:
                                self.object_list[c_id].update_end_point(newx, newy)
                                self.canvas.coords(c_id,cx_s,cy_s,newx,newy)

                                   #self.s_canvas.resizescrollregion()

                            self.canvas.update()
                            device.update_coord(newx, newy)
            time.sleep(0.05)
        

