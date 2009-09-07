# Revised by Daniel Ng

from tkMessageBox import *
from UML_machine import *
from Router import *
from Switch import *
from Bridge import *
from Hub import *
from Wireless_access_point import *
from Firewall import *
from Subnet import *
from Mobile import *
from Connection import *
from Wireless_Connection import *
import Pmw
import os
import re                 #regular expression
import pdb

# enable the auto computing routing table feature,
# if the module Routing is avaliable
try: 
    from Routing import *
except: 
    pass

##
# Class: the topology compiler
class TopologyCompiler:


    ##
    # Constructor: Initial the built-in compiler
    # @param device_list all devices in the topology
    # @param log the compile info window
    # @param filename the output compile file
    # @param support the list of supported devices
    # @param canvas the canvas in GUI
    # @param auto_r the switch to turn on or off the auto routing feature
    # @param dtd_filename the xml specification file
    # @param fs_filename the file system
    def __init__(self, device_list, log, filename, support, canvas, auto_r, dtd_filename, fs_filename, autogen):
        self.autogen = autogen
        self.device_list=device_list
        self.log=log
        self.canvas=canvas
        self.warn=0
        self.error=0
        self.sub_list=[]
        self.log.clear()
        self.filename=filename+".xml"
        self.auto_routing=auto_r
        self.dtd_filename=dtd_filename
        self.fs_filename=fs_filename
        self.output=open(self.filename, 'w')
        self.log.appendtext("Compiling...\n\n")

        #initialize compile device lists
        self.compile_list={}
        for d in support:
            if d[0].type != "tag" and d[0].type != "connection" and d[0].type != "wireless_connection":
                self.compile_list[d[0].type]=[]

        #sort all devices by type
        for o_id in self.device_list:
            if self.device_list[o_id].type != "tag" and self.device_list[o_id].type != "connection" \
                   and self.device_list[o_id].type != "wireless_connection":
                # print "type=",self.device_list[o_id].type
                self.compile_list[self.device_list[o_id].type].append(self.device_list[o_id])

            #built a list to contain all subnets
            if self.device_list[o_id].type == "Subnet":
                self.sub_list.append(self.device_list[o_id].get_subnet())
            elif self.device_list[o_id].type == "Wireless_access_point":
                self.sub_list.append(self.device_list[o_id].get_wireless_interface().get_subnet())


    ##
    # Compile the entire network
    def compile(self):
        self.output.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        if self.dtd_filename != "":
            self.output.write("<!DOCTYPE gloader SYSTEM \""+self.dtd_filename+"\">\n")
        else:
            self.output.write("<!DOCTYPE gloader SYSTEM \"./gloader.dtd\">\n")
        self.output.write("<gloader>\n\n")
        self.compile_subnet()

        #if auto computing feature is turned on, compute routing table for routers and wireless router
        if self.auto_routing == 1:
            self.routing_table_router()
            self.routing_table_Wireless_access_point()
            self.routing_table_entry()
            
        self.compile_router()        
        self.compile_Wireless_access_point()

        self.compile_switch()

        #if auto computing feature is turned on, compute routing table for UML machines
        if self.auto_routing == 1:
            self.routing_table_uml()
        self.compile_UML()

        #if auto computing feature is turned on, compute routing table for mobile device
        if self.auto_routing == 1:
            self.routing_table_mobile()
        self.compile_mobile()

        self.output.write("</gloader>\n")
        self.output.close()
        self.log.appendtext("\nCompile finshed with "+str(self.error)+\
                            " error(s) and "+str(self.warn)+" warning(s).\n")
        if self.error > 0:
            os.system("rm -f "+self.filename)

            

    ##
    # Compile all subnets 
    def compile_subnet(self):
        for obj in self.compile_list["Subnet"]:

            #required settings
            req_list=obj.get_req_properties()
            for opt in req_list:
                if opt == "bits":
                    try:
                        bits = int(req_list[opt])
                        if bits < 0 or bits > 32:
                            self.log.appendtext("Warning:\t"+obj.get_name()+"'s bit value should be between 0 and 32\n")
                            self.warn+=1    
                    except:
                        self.log.appendtext("Error!\t\t"+obj.get_name()+"'s "+opt+" is not an integer\n")
                        self.error+=1

                elif req_list[opt] == "" or self.valid_ip(req_list[opt]) == 0:
                    self.log.appendtext("Error!\t\t"+obj.get_name()+"'s "+opt+" is not specified or not valid\n")
                    self.error+=1

                #pass the subnet to the connected devices
                elif opt == "subnet":
                    self.pass_mask(obj, req_list[opt], req_list["mask"])

    ##
    # Compile all switchs
    def compile_switch(self):
        for obj in self.compile_list["Switch"]:
                
            #check the number of connections the switch has
            if len(obj.get_connection()) < 2 :
                self.log.appendtext("Warning:\t"+obj.get_name()+" is not connected properly!\n")
                self.warn+=1

            self.output.write("<vs name=\""+str(obj.get_name())+"\">\n")
                
            #optional settings
            opt_list=obj.get_opt_properties()
            for opt in opt_list:
                if opt_list[opt] != "":
                    self.output.write("\t<"+opt+">"+opt_list[opt]+"</"+opt+">\n")
            self.output.write("</vs>\n\n")

            #pass the subnet mask to the connected devices
            self.pass_mask(obj, obj.get_subnet(), obj.get_mask())


    ##
    # Compile all UMLs
    def compile_UML(self):
        #pdb.set_trace()
        for obj in self.compile_list["UML"]:
            self.output.write("<vm name=\""+obj.get_name()+"\">\n")
            if self.fs_filename != "":
                self.output.write("\t<filesystem type=\""+obj.get_filetype()+"\">"+self.fs_filename+"</filesystem>\n")
            else:
                self.output.write("\t<filesystem type=\""+obj.get_filetype()+"\">"+obj.get_filesystem()+"</filesystem>\n")

            #check each interface for every machine
            inters=obj.get_interface()
            if len(inters) < 1:
                self.log.appendtext("Warning:\t"+obj.get_name()+" is not connected properly!\n")
                self.warn+=1
            else:
                for inter in inters:
                    self.output.write("\t<if>\n")

                    # find out the linked device on this interface
                    self.output.write("\t\t<target>"+obj.get_target(inter, self.canvas, self.device_list)+"</target>\n")

                    # the network
                    self.output.write("\t\t<network>"+inter.get_subnet()+"</network>\n")

                    #required settings
                    req_list=inter.get_req_properties()
                    for req in req_list:
                        if req == "mac":
                            #generate the mac, if enabled
                            if self.autogen:
                                #get the number from the UML name
                                uml_name = obj.name.split("UML_")

                                if inter.get_connection().get_other_device(obj.name).find("Wireless_access_point") >= 0:
                                    num_mobiles = len(self.compile_list["Mobile"])
                                    newmac = "%06x" % (num_mobiles + 1)
                                    new_req = "fe:fd:00:%s:%s:%s" % (newmac[0:2], newmac[2:4], newmac[4:6])
                                else:                                    
                                    newmac = "%06x" % int(uml_name[1])                                        
                                    new_req = "fe:fd:02:%s:%s:%s" % (newmac[0:2], newmac[2:4], newmac[4:6])
                                
                                #give warning that auto gen overwrote old mac                                
                                if req_list[req] and req_list[req] != new_req:
                                    self.log.appendtext("Warning:\tUML_"+uml_name[1]+"'s manually entered mac address ("+req_list[req]+") was overwritten\n")
                                    self.warn+=1
                                req_list[req] = new_req                                                                        
                                self.output.write("\t\t<mac>"+req_list[req]+"</mac>\n")
                            #validate the format of mac address
                            elif req_list[req] == "" or self.valid_mac(req_list[req]) == 0:
                                self.log.appendtext("Error!\t\tThe mac of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not specified or not valid\n")
                                self.error+=1
                            else:
                                self.output.write("\t\t<mac>"+req_list[req]+"</mac>\n")
                        elif req == "ipv4":
                            if not self.auto_routing:
                                self.output.write("\t\t<ip> </ip>\n")  
                            #generate the ip, if enabled
                            elif self.autogen:
                                #get the number from the UML name
                                uml_name = obj.name.split("UML_")                               
                                #get the subnet to form new ip
                                if self.valid_ip(inter.get_subnet()):                                
                                    subnet = inter.get_subnet().split('.')

                                    if inter.get_connection().get_other_device(obj.name).find("Wireless_access_point") >= 0:
                                        new_req = subnet[0] + "." + subnet[1] + "." + subnet[2] + ".%d" % (len(self.compile_list["Mobile"]) + 2)
                                    else:
                                        new_req = subnet[0] + "." + subnet[1] + "." + subnet[2] + ".%d" % (int(uml_name[1])+1)
                                                                        
                                    #give warning that auto gen overwrote old ip
                                    if req_list[req] and req_list[req] != new_req and req_list[req][len(req_list[req])-1] != ".":
                                        self.log.appendtext("Warning:\tUML_"+uml_name[1]+"'s manually entered ip address ("+req_list[req]+") was overwritten\n")
                                        self.warn+=1
                                    req_list[req] = new_req                                
                                    self.output.write("\t\t<ip>"+req_list[req]+"</ip>\n")
                                else:
                                    self.log.appendtext("Error!\t\tThe subnet of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not valid\n")
                                    self.error+=1
                            #validate the format of ip address
                            elif req_list[req] == "" or self.valid_ip(req_list[req]) == 0:
                                self.log.appendtext("Error!\t\tThe ipv4 of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not specified or not valid\n")
                                self.error+=1
                            # check if the ip is valid in the specified subnet
                            else:
                                if self.valid_ip_subnet(req_list[req], inter.get_subnet(), inter.get_mask()) == 0:
                                    self.log.appendtext("Error!\t\tThe ipv4 of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not in the specified subnet\n")
                                    self.error+=1
                                else:
                                    self.output.write("\t\t<ip>"+req_list[req]+"</ip>\n")


                    #optional settings
                        #opt_list=obj.get_opt_properties()
                       #for opt in opt_list:
                            #if opt_list[opt] != "":

                    mask=inter.get_mask()
                    table=inter.get_table()
                    if self.valid_ip(mask) == 0 :
                        self.log.appendtext("Error!\t\tThe mask of interface "+str(inter.get_id())+" of "+obj.get_name()\
                                            +" is not valid\n")
                        self.error+=1

                    else:
                        #check each routing table entry
                        i=1
                        output_string = ""
                        if table:
                            for entry in table:
                                gw=entry.get_gateway()
                                if self.valid_ip(gw) == 0:
                                    self.log.appendtext("Error!\t\tThe gateway of routing table entry "+str(i)+" of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not valid\n")
                                    self.error+=1

                                ip=entry.get_ip()
                                if self.valid_ip(ip) == 0:
                                    self.log.appendtext("Error!\t\tThe ip of routing table entry "+str(i)+" of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not valid\n")
                                    self.error+=1
                                i+=1
                                
                                if inter.get_connection().get_other_device(obj.get_name()).find("Switch") >= 0 and \
                                   self.valid_ip_subnet(gw, ip, inter.get_mask()):
                                   
                                    self.output.write("\t\t<route type=\"net\" netmask=\""+mask+"\" gw=\"\"> </route>\n")
                                else:
                                    output_string += ("\t\t<route type=\"net\" netmask=\""+mask+"\" gw=\""+gw+"\">"+ip+"</route>\n")
                        self.output.write(output_string)                            

                    self.output.write("\t</if>\n")
            self.output.write("</vm>\n\n")
        

    ##
    # Compile all mobiles
    def compile_mobile(self):
        for obj in self.compile_list["Mobile"]:
            self.output.write("<vmb name=\""+obj.get_name()+"\">\n")
            if self.fs_filename != "":
                self.output.write("\t<filesystem type=\""+obj.get_filetype()+"\">"+self.fs_filename+"</filesystem>\n")
            else:
                self.output.write("\t<filesystem type=\""+obj.get_filetype()+"\">"+obj.get_filesystem()+"</filesystem>\n")

            #check each interface for every mobile
            for inter in obj.get_interface():
                self.output.write("\t<if>\n")
                
                # find out the linked device on this interface
                self.output.write("\t\t<target>"+obj.get_target(inter, self.canvas, self.device_list)+"</target>\n")

                # the network
                self.output.write("\t\t<network>"+inter.get_subnet()+"</network>\n")

                #required settings
                req_list=inter.get_req_properties()
                for req in req_list:
                    if req == "mac":
                        
                        #generate the mac, if enabled
                        if self.autogen:
                            #get the number from the UML name
                            mobile_name = obj.name.split("Mobile_")
                            newmac = "%06x" % int(mobile_name[1])                                        
                            new_req = "fe:fd:00:%s:%s:%s" % (newmac[0:2], newmac[2:4], newmac[4:6])
                            #give warning that auto gen overwrote old mac                                
                            if req_list[req] and req_list[req] != new_req:
                                self.log.appendtext("Warning:\tMobile_"+mobile_name[1]+"'s manually entered mac address ("+req_list[req]+") was overwritten\n")
                                self.warn+=1
                            req_list[req] = new_req                                                                        
                            self.output.write("\t\t<mac>"+req_list[req]+"</mac>\n")
                        #validate the format of mac address
                        elif req_list[req] == "" or self.valid_mac(req_list[req]) == 0:
                            self.log.appendtext("Error!\t\tThe mac of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not specified or not valid\n")
                            self.error+=1
                        else:
                            self.output.write("\t\t<mac>"+req_list[req]+"</mac>\n")
                    elif req == "ipv4":
                        if not self.auto_routing:
                            self.output.write("\t\t<ip> </ip>\n")  
                            #generate the ip, if enabled
                        elif self.autogen:
                            #get the number from the UML name
                            mobile_name = obj.name.split("Mobile_")                               
                            #get the subnet to form new ip                                
                            if self.valid_ip(inter.get_subnet()):
                                subnet = inter.get_subnet().split('.')
                                new_req = subnet[0] + "." + subnet[1] + "." + subnet[2] + ".%d" % (int(mobile_name[1])+1)
                                #give warning that auto gen overwrote old ip
                                if req_list[req] and req_list[req] != new_req and req_list[req][len(req_list[req])-1] != ".":
                                    self.log.appendtext("Warning:\tMobile_"+mobile_name[1]+"'s manually entered ip address ("+req_list[req]+") was overwritten\n")
                                    self.warn+=1
                                req_list[req] = new_req                                
                                self.output.write("\t\t<ip>"+req_list[req]+"</ip>\n")
                            else:
                                self.log.appendtext("Error!\t\tThe subnet of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not valid\n")
                                self.error+=1
                        #validate the format of ip address
                        elif req_list[req] == "" or self.valid_ip(req_list[req]) == 0:
                            self.log.appendtext("Error!\t\tThe ipv4 of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not specified or not valid\n")
                            self.error+=1

                        # check if the ip is valid in the specified subnet
                        else:
                            if self.valid_ip_subnet(req_list[req], inter.get_subnet(), inter.get_mask()) == 0:
                                self.log.appendtext("Error!\t\tThe ipv4 of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not in the specified subnet\n")
                                self.error+=1
                            else:
                                self.output.write("\t\t<ip>"+req_list[req]+"</ip>\n")


                mask=inter.get_mask()
                if self.valid_ip(mask) == 0 :
                    self.log.appendtext("Error!\t\tThe mask of interface "+str(inter.get_id())+" of "+obj.get_name()\
                                        +" is not valid\n")
                    self.error+=1

                else:
                    #check each rounting table entry
                    table=inter.get_table()
                    i=1
                    for entry in table:
                        gw=entry.get_gateway()
                        if self.valid_ip(gw) == 0:
                            self.log.appendtext("Error!\t\tThe gateway of rounting table entry "+str(i)+" of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not valid\n")
                            self.error+=1

                        ip=entry.get_ip()
                        if self.valid_ip(ip) == 0:
                            self.log.appendtext("Error!\t\tThe ip of rounting table entry "+str(i)+" of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not valid\n")
                            self.error+=1
                        i+=1
                        self.output.write("\t\t<route type=\"net\" netmask=\""+mask+"\" gw=\""+gw+"\">"+ip+"</route>\n")
                self.output.write("\t</if>\n")


                #output the location of the device
                self.output.write("\t<location>\n")
                x,y=obj.get_coord()
                self.output.write("\t\t<x>"+str(x)+"</x>\n")
                self.output.write("\t\t<y>"+str(y)+"</y>\n")
                self.output.write("\t</location>\n")

            self.output.write("</vmb>\n\n")


    ##
    # Computing routing table for routers. 
    # Step 1, built the adjacent subnet list and adjacent router list
    def routing_table_router(self):
        for obj in self.compile_list["Router"]:

            #clean the adjacent_list
            #pdb.set_trace()
            obj.empty_adjacent_list()

            #clean existing routing table entry
            obj.empty_routing_entry()

            #get adjacent subnets and routers
            for inter in obj.get_interface():
                routing=Routing(self.device_list, self.canvas)
                routing.subnet(obj, inter.get_connection(), inter.get_ip())
                routing.gateway(obj, inter.get_connection(), obj, inter)

            #print obj.get_adjacent_router()
            #print obj.get_adjacent_subnet()
            #for inter in obj.get_interface():
                #print inter.get_table()


    ##
    # Computing routing table for routers or wireless router. 
    # Step 2, computing the touring entries
    def routing_table_entry(self):

        # compute routing table for routers to get access to each subnet
        for obj in self.compile_list["Router"]:            
            for sub in self.sub_list:
                obj.add_routing_entry(sub)

        # compute routing table for wireless routers to get access to each subnet
        for obj in self.compile_list["Wireless_access_point"]:
            for sub in self.sub_list:
                obj.add_routing_entry(sub)

    ##
    # Computing routing table for wireless routers. 
    # Step 1, built the adjacent subnet list and adjacent router list
    def routing_table_Wireless_access_point(self):
        for obj in self.compile_list["Wireless_access_point"]:

            #clean the adjacent_list
            #pdb.set_trace()
            obj.empty_adjacent_list()

            #clean existing routing table entry
            obj.empty_routing_entry()

            #get adjacent subnets and routers
            for inter in obj.get_interface():
                if inter.type == "wire":
                    routing=Routing(self.device_list, self.canvas)
                    routing.subnet(obj, inter.get_connection(), inter.get_ip())
                    routing.gateway(obj, inter.get_connection(), obj, inter)
                else:
                    obj.add_adjacent_subnet(obj.get_wireless_interface(), inter.get_ip())


    ##
    # Computing routing table for mobiles if auto computing feature is enabled. 
    def routing_table_mobile(self):
        for obj in self.compile_list["Mobile"]:
        
            #clean the adjacent_list
            #pdb.set_trace()
            obj.empty_adjacent_list()

            #clean existing routing table entry
            obj.empty_routing_entry()

            #get adjacent subnets and routers
            for inter in obj.get_interface():
                routing=Routing(self.device_list, self.canvas)
                
                routing.subnet(obj, inter.get_connection(), inter.get_ip())
                #pdb.set_trace()
                routing.gateway(obj, inter.get_connection(), obj, inter)

        for obj in self.compile_list["Mobile"]:
            #pdb.set_trace()
            # compute routing table to get access to each subnet
            for sub in self.sub_list:
                
                #skip the adjacent subnet
                if obj.has_subnet(sub) == None:
                    obj.add_routing_entry(sub)


    ##
    # Computing routing table for UMLs if auto computing feature is enabled. 
    def routing_table_uml(self):
        for obj in self.compile_list["UML"]:

            #clean the adjacent_list
            #pdb.set_trace()
            obj.empty_adjacent_list()

            #clean existing routing table entry
            obj.empty_routing_entry()

            #get adjacent subnets and routers
            for inter in obj.get_interface():
                #if inter.get_connection().get_other_device(obj.name).find("Switch") >= 0:
                 #   continue
                routing=Routing(self.device_list, self.canvas)
                #pdb.set_trace()
                routing.subnet(obj, inter.get_connection(), inter.get_ip())
                routing.gateway(obj, inter.get_connection(), obj, inter)

        for obj in self.compile_list["UML"]:
            
            # compute routing table to get access to each subnet
            for sub in self.sub_list:
                #skip the adjacent subnet
                if obj.has_subnet(sub) == None:
                    obj.add_routing_entry(sub)


    ##
    # Compile all Routers
    def compile_router(self):
        for obj in self.compile_list["Router"]:

            self.output.write("<vr name=\""+str(obj.get_name())+"\">\n")

            #check each interface for every router
            inters=obj.get_interface()
            if len(inters) < 2:
                self.log.appendtext("Warning:\t"+obj.get_name()+" has less than two interfaces - an abnormal connection!\n")
                self.warn+=1
            else:
                for inter in inters:
                    self.output.write("\t<netif>\n")

                    # find out the linked device on this interface
                    self.output.write("\t\t<target>"+obj.get_target(inter, self.canvas, self.device_list)+"</target>\n")

                    # the network
                    self.output.write("\t\t<network>"+inter.get_subnet()+"</network>\n")

                    #required settings
                    req_list=inter.get_req_properties()
                    for req in req_list:
                        if req == "mac":

                            #generate the mac, if enabled
                            if self.autogen:
                                #get the number from the Router name
                                router_name = obj.name.split("Router_")
                                newmac_r = "%02x" % int(router_name[1])
                                newmac_i = "%04x" % int(inter.get_id())                                        
                                new_req = "fe:fd:03:%s:%s:%s" % (newmac_r[0:2], newmac_i[0:2], newmac_i[2:4])
                                #give warning that auto gen overwrote old mac, excluding generated addresses                                
                                if req_list[req] and req_list[req] != new_req:
                                    self.log.appendtext("Warning:\tRouter_"+router_name[1]+"'s manually entered mac address ("+req_list[req]+") was overwritten\n")
                                    self.warn+=1
                                req_list[req] = new_req                                                                        
                                self.output.write("\t\t<nic>"+req_list[req]+"</nic>\n")

                            #validate the format of mac address
                            elif req_list[req] == "" or self.valid_mac(req_list[req]) == 0:
                                self.log.appendtext("Error!\t\tThe mac of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not specified or not valid\n")
                                self.error+=1
                            else:
                                self.output.write("\t\t<nic>"+req_list[req]+"</nic>\n")
                        elif req == "ipv4":
                        
                            if not self.auto_routing:
                                self.output.write("\t\t<ip> </ip>\n")  
                            #generate the ip, if enabled
                            elif self.autogen:
                                #get the number from the Router name
                                router_name = obj.name.split("Router_")                               
                                #get the subnet to form new ip                                
                                if self.valid_ip(inter.get_subnet()):
                                    subnet = inter.get_subnet().split('.')
                                    new_req = subnet[0] + "." + subnet[1] + "." + subnet[2] + ".%d" % (int(router_name[1])+128)
                                    #give warning that auto gen overwrote old ip
                                    if req_list[req] and req_list[req] != new_req and req_list[req][len(req_list[req])-1] != ".":
                                        self.log.appendtext("Warning:\tRouter_"+router_name[1]+"'s manually entered ip address ("+req_list[req]+") was overwritten\n")
                                        self.warn+=1
                                    req_list[req] = new_req                                
                                    self.output.write("\t\t<ip>"+req_list[req]+"</ip>\n")
                                else:
                                    self.log.appendtext("Error!\t\tThe subnet of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not specified or not valid\n")
                                    self.error+=1
                            #validate the format of ip address
                            elif req_list[req] == "" or self.valid_ip(req_list[req]) == 0:
                                self.log.appendtext("Error!\t\tThe ipv4 of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not specified or not valid\n")
                                self.error+=1

                            # check if the ip is valid in the specified subnet
                            else:
                                if self.valid_ip_subnet(req_list[req], inter.get_subnet(), inter.get_mask()) == 0:
                                    self.log.appendtext("Error!\t\tThe ipv4 of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not in the specified subnet\n")
                                    self.error+=1
                                else:
                                    self.output.write("\t\t<ip>"+req_list[req]+"</ip>\n")

                    mask=inter.get_mask()
                    if self.valid_ip(mask) == 0 :
                        self.log.appendtext("Error!\t\tThe mask of interface "+str(inter.get_id())+" of "+obj.get_name()\
                                            +" is not specified or not valid\n")
                        self.error+=1

                    else:
                        #check each rounting table entry
                        table=inter.get_table()
                        i=1
                        for entry in table:
                            nh=entry.get_nexthop()
                            if self.valid_ip(nh) == 0:
                                self.log.appendtext("Error!\t\tThe nexthop of rounting table entry "+str(i)+" of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not valid\n")
                                #print "NextHop is:",nh
                                self.error+=1

                            ip=entry.get_ip()
                            if self.valid_ip(ip) == 0:
                                self.log.appendtext("Error!\t\tThe ip of rounting table entry "+str(i)+" of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not valid\n")
                                self.error+=1
                            i+=1
                            self.output.write("\t\t<rtentry netmask=\""+mask+"\" nexthop=\""+nh+"\">"+ip+"</rtentry>\n")
                    self.output.write("\t</netif>\n")            
            self.output.write("</vr>\n\n")


    ##
    # Compile all Wireless Router
    def compile_Wireless_access_point(self):
        for obj in self.compile_list["Wireless_access_point"]:

            self.output.write("<vwr name=\""+str(obj.get_name())+"\">\n")

            #check each interface for every router
            inters=obj.get_interface()
            for inter in inters:

                #set the mask for wireless interface
                if inter.type == "wireless":
                
                    f=split(inter.get_subnet(), '.')
                    mask=""
                    for chunk in f:
                        if chunk == "0":
                            m_chunk= "0"
                        else:
                            m_chunk="255"
                        if mask == "":
                            mask=m_chunk
                        else:
                            mask=mask+"."+m_chunk
                    inter.set_mask(mask)

                    for entry in inter.get_table():                        
                        entry.set_mask(mask)

                    #pass the subnet and mask to all connected mobiles
                    for con in inter.get_shared_connections():
                        
                        #find out the device at the other side of the connection
                        if con.get_start_device() == obj.get_name():
                            other_device=self.device_list[self.canvas.find_withtag(con.get_end_device())[0]]
                        else:
                            other_device=self.device_list[self.canvas.find_withtag(con.get_start_device())[0]]

                        other_device.set_mask(con, inter.get_subnet(), mask)
                    self.output.write("\t<netif_wireless>\n")

                else:
                    self.output.write("\t<netif>\n")

                    # find out the linked device on this interface
                    self.output.write("\t\t<target>"+obj.get_target(inter, self.canvas, self.device_list)+"</target>\n")

                # the network
                self.output.write("\t\t<network>"+inter.get_subnet()+"</network>\n")

                #required settings
                req_list=inter.get_req_properties()
                for req in req_list:
                    if req == "mac":
                        #generate the mac, if enabled
                        if self.autogen:
                            #get the number from the Router name
                            router_name = obj.name.split('Wireless_access_point_')
                            newmac_r = "%02x" % int(router_name[1])
                            newmac_i = "%04x" % int(inter.get_id())                                        
                            new_req = "fe:fd:01:%s:%s:%s" % (newmac_r[0:2], newmac_i[0:2], newmac_i[2:4])
                            #give warning that auto gen overwrote old mac, excluding generated addresses                                
                            if req_list[req] and req_list[req] != new_req:
                                self.log.appendtext("Warning:\tWireless_access_point_"+router_name[1]+"'s manually entered mac address ("+req_list[req]+") was overwritten\n")
                                self.warn+=1
                            req_list[req] = new_req                                                                        
                            self.output.write("\t\t<nic>"+req_list[req]+"</nic>\n")

                        #validate the format of mac address
                        elif req_list[req] == "" or self.valid_mac(req_list[req]) == 0:
                            self.log.appendtext("Error!\t\tThe mac of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not specified or not valid\n")
                            self.error+=1
                        else:
                            self.output.write("\t\t<nic>"+req_list[req]+"</nic>\n")
                    elif req == "ipv4":
                        #generate the ip, if enabled
                        if self.autogen:
                            #get the number from the UML name
                            router_name = obj.name.split('Wireless_access_point_')                           
                            #get the subnet to form new ip        
                            if self.valid_ip(inter.get_subnet()):
                                subnet = inter.get_subnet().split('.')
                                new_req = subnet[0] + "." + subnet[1] + "." + subnet[2] + ".1"
                                #give warning that auto gen overwrote old ip
                                if req_list[req] and req_list[req] != new_req and req_list[req][len(req_list[req])-1] != ".":
                                    self.log.appendtext("Warning:\tWireless_access_point_"+router_name[1]+"'s manually entered ip address ("+req_list[req]+") was overwritten\n")
                                    self.warn+=1
                                req_list[req] = new_req                                
                                self.output.write("\t\t<ip>"+req_list[req]+"</ip>\n")
                            else:
                                self.log.appendtext("Error!\t\tThe subnet of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not specified or not valid\n")
                                self.error+=1
                        #validate the format of ip address
                        elif req_list[req] == "" or self.valid_ip(req_list[req]) == 0:
                            self.log.appendtext("Error!\t\tThe ipv4 of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not specified or not valid\n")
                            self.error+=1

                        # check if the ip is valid in the specified subnet
                        else:
                            if self.valid_ip_subnet(req_list[req], inter.get_subnet(), inter.get_mask()) == 0:
                                self.log.appendtext("Error!\t\tThe ipv4 of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not in the specified subnet\n")
                                self.error+=1
                            else:
                                self.output.write("\t\t<ip>"+req_list[req]+"</ip>\n")
                    
                #output the wireless properties
                properties=obj.get_properties()
                p_types={}
                p_types["wireless_card"]=("w_type", "freq", "bandwidth", "Pt", "Pt_c", "Pr_c", "P_idle", "P_sleep", "P_off", "RX", "CS", "CP", "module")
                p_types["antenna"]=("a_type", "ant_h", "ant_g", "ant_l", "JAM")
                p_types["energy"]=("power", "PSM", "energy_amount")
                p_types["mobility"]=("m_type", "ran_max", "ran_min")
                p_types["mac_layer"]=("mac_type", "trans")
                
                for item in p_types:        
                    self.output.write("\t<"+item+">\n")
                    for p in p_types[item]:
                        self.output.write("\t\t<"+p+">"+str(properties[p])+"</"+p+">\n")
                        #print p, properties[p]
                    self.output.write("\t</"+item+">\n")

                mask=inter.get_mask()
                if self.valid_ip(mask) == 0 :
                    self.log.appendtext("Error!\t\tThe subnet of interface "+str(inter.get_id())+" of "+obj.get_name()\
                                        +" is not specified or not valid\n")
                    self.error+=1

                else:
                    #check each rounting table entry
                    table=inter.get_table()
                    i=1
                    for entry in table:
                        nh=entry.get_nexthop()
                        if self.valid_ip(nh) == 0:
                            self.log.appendtext("Error!\t\tThe nexthop of rounting table entry "+str(i)+" of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not valid\n")
                            self.error+=1

                        ip=entry.get_ip()
                        if self.valid_ip(ip) == 0:
                            self.log.appendtext("Error!\t\tThe ip of rounting table entry "+str(i)+" of interface "+str(inter.get_id())+" of "+obj.get_name()+" is not valid\n")
                            self.error+=1
                        i+=1
                        self.output.write("\t\t<rtentry netmask=\""+mask+"\" nexthop=\""+nh+"\">"+ip+"</rtentry>\n")

                if inter.type == "wireless":
                    #con=obj.get_wireless_interface().get_shared_connections()
                    #if len(con) >0:
                        #self.output.write("\t\t<Wireless_Channel>\n")
                        #properties=con[0].get_properties()
                        #for item, value in properties.iteritems():
                            #self.output.write("\t\t\t<"+item+">"+str(value)+"</"+item+">\n")
                        #self.output.write("\t\t</Wireless_Channel>\n")
                    self.output.write("\t</netif_wireless>\n")
                else:
                    self.output.write("\t</netif>\n")                     
            self.output.write("</vwr>\n\n")

    ##
    # Check if the ip is in valid format
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


    ##
    # Check if the ip is in the specified subnet
    # @param ip the ip to check
    # @param subnet the given subnet
    # @return 1 if the ip is in given subnet;
    #         Otherwise, return 0 
    def valid_ip_subnet(self, ip, subnet, mask):
        p=re.compile('\d+')
        ip_chunk=p.findall(ip)
        subnet_chunk=p.findall(subnet)
        mask_chunk=p.findall(mask)

        #check each chunk
        for i in range(len(subnet_chunk)):
            if mask_chunk[i] == "255":
                if ip_chunk[i] != subnet_chunk[i]:
                    return 0
            elif mask_chunk[i] == "0":
                if ip_chunk[i] == "0":
                    return 0
            else:
                mask_value = int(mask_chunk[i])
                ip_value = int(ip_chunk[i])
                subnet_value = int(subnet_chunk[i])
                print "TO BE FINISHED"                
                return 0
        return 1
                


    ##
    # Check if the mac is in valid format
    # @param mac the mac to validate
    # @return 1 if the mac is valid;
    #         Otherwise, return 0
    def valid_mac(self, mac):
        if re.match(r'^[a-f|0-9]{2}:[a-f|0-9]{2}:[a-f|0-9]{2}:[a-f|0-9]{2}:[a-f|0-9]{2}:[a-f|0-9]{2}$', mac) == None:
            return 0
        else:
            return 1


    ##
    # Propagate the mask and subnet to the entire subnet
    # @param obj the obj to start propagate
    # @param subnet the subnet to propagate
    # @param mask the mask to propagate
    def pass_mask(self, obj, subnet, mask):
        for con in obj.get_connection():

            #find out the device at the other side of the connection
            if con.get_start_device() == obj.get_name():
                other_device=self.device_list[self.canvas.find_withtag(con.get_end_device())[0]]
            else:
                other_device=self.device_list[self.canvas.find_withtag(con.get_start_device())[0]]
            if other_device.type != "Subnet":
                other_device.set_mask(con, subnet, mask)

