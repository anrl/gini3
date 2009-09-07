import pdb

##
# Class: the general abstract class for network device
class Device:

    ##
    # Update the location of the device
    # @param x the x axis of new location
    # @param y the y axis of new location
    def update_coord(self, x, y):
	self.x=x	
	self.y=y
	self.tag.update_coord(x,y)

    ##
    # Get the location of the device
    # @return (x, y) the coordinate of the device
    def get_coord(self):
	return (self.x, self.y)

    ##
    # Get the type of the device
    # @return the type	
    def get_type(self):
	return self.type

    ##  
    # Get the serial number of the device
    # @return serial number
    def get_num(self):
	return self.num

    ##
    # Add connection to the device
    # @param c the connection to add
    def add_connection(self, c):
	self.connection.append(c)

    ##
    # Delete a specified connection from the device
    # @param c the connection to delete
    def delete_connection(self, c):
	self.connection.remove(c)

    ##
    # Get all the connections of the device
    # @return the list of all connections
    def get_connection(self):
	return self.connection

    ##
    # Get all require properties
    # @return the list of required properties
    def get_req_properties(self):
	return self.req_properties

    ##
    # Get all optional properties
    # @return the list of optional properties    
    def get_opt_properties(self):
	return self.opt_properties

    ##
    # Get the name of the device
    # @return the device's name	
    def get_name(self):
	return self.name

    ##
    # Set the mask and subnet
    # @param con the connection that pass the mask and subnet
    # @param subnet the subnet to set
    # @param mask the mask to set
    def set_mask(self, con, subnet, mask):
	self.subnet=subnet
	self.mask=mask

    ##
    # Get the mask of the device
    # @return the mask
    def get_mask(self):
	return self.mask

    ##
    # Get the subnet if the device
    # @return the subnet
    def get_subnet(self):
	return self.subnet

    ##
    # Get the name tag of the device
    # @return name tag
    def get_tag(self):
	return self.tag

    ##
    # The bolloon help info for this device    
    def balloon_help(self):
	s="Screen Name: "+self.name
	s=s+"\nSubnet: "+self.get_subnet()
	return s

    ##
    # Get the linked device give an interface
    # @param inter the specified interface for given device
    # @param canvas the canvas that contains all devices
    # @param device_list the list of all devices on the canvas
    # @return dev the linked device on the given interface. 
    #         Subnet is not a device, so ignored.
    def get_target(self, inter, canvas, device_list):
	#pdb.set_trace()
	con=inter.get_connection()
	d_id=canvas.find_withtag(con.get_other_device(self.get_name()))[0]
	if d_id:
	    dev=device_list[d_id]
	    if dev.type == "Subnet":
	        n_con=dev.get_other_connection(con)
		if n_con:
	            n_dev=n_con.get_other_device(dev.get_name())
		    return n_dev
		else:
		    return ""
	    else:
	        return dev.get_name()
	
