##
# Class: the name tag for an object
class Tag:
    type="tag"

    ##
    # Constructor: Initial a name tag
    # @param x the x axis of the switch location on the canvas
    # @param y the y axis of the switch location on the canvas
    # @param re_y the relative y to the given y location. Because the name is at the top of a device on the canvas.
    # @param s_num the serial number of switch
    # @param t_num the serial number of the name tag
    def __init__(self, x, y, re_y, num, content):
	self.x=x
	self.y=y
	self.relative_y=re_y
	self.content=content
	self.num=num

	#the name is composed by the type of the device and a serial number
	self.name=self.type+str(num)

    ##
    # Update the tag with a new location
    # @param x the new x axis value
    # @param y the new y axis value
    def update_coord(self, x, y):
	self.x=x
	self.y=y

    ##
    # Get the location of the name tag
    # @return (x, y) the coordinates of the name tag on the canvas
    def get_coord(self):
	return (self.x, self.y, self.relative_y)

    ##
    # Get the name of the name tag
    # @return the name
    def get_name(self):
	return self.name

    ##
    # Get the serial number of the tag
    # @return the serial number
    def get_num(self):
	return self.num

    ##
    # Get the actual content of the name tag
    # @return the content of the name tag
    def get_content(self):
	return self.content

    ## 
    # Get the type of the name tag
    # @return the type
    def get_type(self):
	return self.type
