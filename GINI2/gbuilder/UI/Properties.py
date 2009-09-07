"""The properties window for display item properties"""

from PyQt4 import QtCore, QtGui
from UI.Configuration import mainWidgets
from Dockable import *

class PropertiesWindow(Dockable):
    def __init__(self, parent = None):
        """
        Create a properties window to display properties of selected items.
        """
        Dockable.__init__(self, parent=parent)
        self.createView()
        self.setWidget(self.sourceView)

    def createView(self):
        """
        Create the view and model of the window.
        """
        self.currentItem = None
        self.sourceView = QtGui.QTreeView()

        self.model = QtGui.QStandardItemModel(0, 2, self)
        self.model.setHeaderData(0, QtCore.Qt.Horizontal, QtCore.QVariant("Property"), QtCore.Qt.DisplayRole)
        self.model.setHeaderData(1, QtCore.Qt.Horizontal, QtCore.QVariant("Value"))
        
        self.sourceView.setEditTriggers(QtGui.QAbstractItemView.CurrentChanged)
        self.sourceView.setModel(self.model)
        
        self.connect(self,
                     QtCore.SIGNAL("topLevelChanged(bool)"),
                     self.dockChanged)
        self.connect(self.model, QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"), self.changed)
        
    def addProperty(self, prop, value):
        """
        Add a property to display in the window.
        """
        pr = QtGui.QStandardItem()
        pr.setData(QtCore.QVariant(prop), QtCore.Qt.DisplayRole)
        pr.setEditable(False)
            
        val = QtGui.QStandardItem()
        val.setData(QtCore.QVariant(value), QtCore.Qt.EditRole)

        if mainWidgets["main"].isRunning():
            val.setEditable(False)
            
        if prop == "Name":
            self.model.insertRow(0, [pr, val])
        else:
            self.model.appendRow([pr, val])
        
    def changed(self, index, index2):
        """
        Handle a change in the properties of the current item.
        """
        value = self.model.data(index)
        propertyIndex = self.model.index(index.row(), index.column()-1)
        prop = self.model.data(propertyIndex)
        if prop.toString() == "Name":
            name = str(value.toString())
            if name.find(self.currentItem.type + "_") == 0:
                try:
                    devType, index = name.split("_", 1)
                    index = int(index)
                    if index - 1 in range(126) and mainWidgets["canvas"].scene().findItem(name) == None:
                        self.currentItem.setIndex(index)
                        return
                except:
                    pass
                
            popup = mainWidgets["popup"]
            popup.setWindowTitle("Invalid Name Change")
            popup.setText("Only the index of the name can be changed!  The index must be unique and in the range 1-126.")
            popup.show()
        else:
            self.currentItem.setProperty(prop.toString(), value.toString())
        
    def dockChanged(self, floating):
        """
        Handle a change in the dock location or state.
        """
        if floating:
            self.setWindowOpacity(0.8)

    
    def setCurrent(self, item):
        """
        Set the current item.
        """
        self.currentItem = item
        self.display()
        
    def display(self):
        """
        Show the properties of the current item.
        """
        if not self.currentItem:
            return
        self.removeRows()
        for prop, value in self.currentItem.getProperties().iteritems():
            self.addProperty(prop, value)

    def clear(self):
        """
        Clear the properties window and release the current item.
        """
        self.currentItem = None
        self.removeRows()
                
    def removeRows(self):
        """
        Clear the rows of the properties window.
        """
        count = self.model.rowCount()
        if count:
            self.model.removeRows(0, count)

class InterfacesWindow(PropertiesWindow):
    def __init__(self, parent = None):
        """
        Create an interfaces window.
        """
        Dockable.__init__(self, parent=parent)
        self.createView()
         
        self.currentInterface = 1
        self.leftScroll = QtGui.QPushButton("<")
        self.rightScroll = QtGui.QPushButton(">")
        self.routesButton = QtGui.QPushButton("Routes")

        chooserLayout = QtGui.QHBoxLayout()
        chooserLayout.addWidget(self.leftScroll)
        chooserLayout.addWidget(self.routesButton)
        chooserLayout.addWidget(self.rightScroll)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.sourceView)
        mainLayout.addLayout(chooserLayout)

        self.widget = QtGui.QWidget()
        self.widget.setLayout(mainLayout)

        self.setWidget(self.widget)
        
        self.connect(self.leftScroll, QtCore.SIGNAL("clicked()"), self.scrollLeft)
        self.connect(self.rightScroll, QtCore.SIGNAL("clicked()"), self.scrollRight)
        
    def addProperty(self, prop, value):
        """
        Add a property to display in the window.
        """
        if prop == "routing":
            return
        elif prop == "target":
            value = value.getName()

        PropertiesWindow.addProperty(self, prop, value)
        
    def scrollLeft(self):
        """
        Scroll to the previous interface of the current item.
        """
        if not self.currentItem:
            return
        from Core.Interfaceable import Interfaceable
        if not isinstance(self.currentItem, Interfaceable):
            return
        
        if self.currentInterface == 1:
            return

        self.display(-1)

    def scrollRight(self):
        """
        Scroll to the next interface of the current item.
        """
        if not self.currentItem:
            return
        from Core.Interfaceable import Interfaceable
        if not isinstance(self.currentItem, Interfaceable):
            return
        
        if self.currentInterface == len(self.currentItem.getInterfaces()):
            return

        self.display(1)

    def display(self, inc=0):
        """
        Show the properties of the interface of the current item.
        Which interface is shown depends on inc, of which -1 is the previous,
        0 is the current, and 1 is the next.
        """
        if not self.currentItem:
            return
        from Core.Interfaceable import Interfaceable
        if not isinstance(self.currentItem, Interfaceable):
            return
        interfaces = self.currentItem.getInterfaces()
        if not interfaces:
            return

        self.removeRows()
        self.currentInterface += inc
        interface = interfaces[self.currentInterface-1]
        self.setWindowTitle("Interface %d" % self.currentInterface)
        for prop, value in interface.iteritems():
            self.addProperty(prop, value)

    def changed(self, index, index2):
        """
        Handle a change in the interface properties of the current item.
        """
        value = self.model.data(index)
        propertyIndex = self.model.index(index.row(), index.column()-1)
        prop = self.model.data(propertyIndex)
        interfaces = self.currentItem.getInterfaces()
        interfaces[self.currentInterface - 1][prop.toString()] = value.toString()

    def clear(self):
        """
        Clear the interfaces window and release the current item.
        """
        self.currentItem = None
        self.currentInterface = 1
        self.setWindowTitle("Interfaces")
        self.removeRows()

    def getCurrent(self):
        """
        Return the current item.
        """
        return self.currentItem

class RoutesWindow(InterfacesWindow):
    def __init__(self, interfacesWindow, parent = None):
        """
        Create a routes window.
        """
        InterfacesWindow.__init__(self, parent=parent)
        self.interfacesWindow = interfacesWindow
        self.currentInterface = 1
        self.currentRoute = 1
        
        self.connect(self.interfacesWindow.leftScroll, QtCore.SIGNAL("clicked()"), self.decInterface)
        self.connect(self.interfacesWindow.rightScroll, QtCore.SIGNAL("clicked()"), self.incInterface)
        self.connect(self.interfacesWindow.routesButton, QtCore.SIGNAL("clicked()"), self.show)

        self.routesButton.setVisible(False)

    def decInterface(self):
        """
        Handle the interfaces window changing to the previous interface.
        """
        if not self.currentItem:
            return
        from Core.Interfaceable import Interfaceable
        if not isinstance(self.currentItem, Interfaceable):
            return
        
        if self.currentInterface == 1:
            return

        self.currentRoute = 1
        self.display(-1)
        
    def incInterface(self):
        """
        Handle the interfaces window changing to the next interface.
        """
        if not self.currentItem:
            return
        from Core.Interfaceable import Interfaceable
        if not isinstance(self.currentItem, Interfaceable):
            return
        
        if self.currentInterface == len(self.currentItem.getInterfaces()):
            return

        self.currentRoute = 1
        self.display(1)

        
    def display(self, interfaceInc=0, routeInc=0):
        """
        Show the properties of the interface of the current item.
        Which interface is shown depends on inc, of which -1 is the previous,
        0 is the current, and 1 is the next.
        """
        if not self.currentItem:
            return
        from Core.Interfaceable import Interfaceable
        if not isinstance(self.currentItem, Interfaceable):
            return
        interfaces = self.currentItem.getInterfaces()
        if not interfaces:
            return

        self.removeRows()
        self.currentInterface += interfaceInc
        self.currentRoute += routeInc

        routes = interfaces[self.currentInterface-1][QtCore.QString("routing")]
        if not routes:
            return

        route = routes[self.currentRoute-1]
        self.setWindowTitle("Route %d" % self.currentRoute)
        for prop, value in route.iteritems():
            self.addProperty(prop, value)

    def scrollLeft(self):
        """
        Scroll to the previous route of the current item.
        """
        if not self.currentItem:
            return
        from Core.Interfaceable import Interfaceable
        if not isinstance(self.currentItem, Interfaceable):
            return

        if self.currentRoute == 1:
            return

        self.display(0, -1)

    def scrollRight(self):
        """
        Scroll to the next route of the current item.
        """
        if not self.currentItem:
            return
        from Core.Interfaceable import Interfaceable
        if not isinstance(self.currentItem, Interfaceable):
            return
        
        interfaces = self.currentItem.getInterfaces()
        if not interfaces:
            return

        routes = interfaces[self.currentInterface-1][QtCore.QString("routing")]
        if not routes:
            return
        
        if self.currentRoute == len(routes):
            return

        self.display(0, 1)

    def clear(self):
        """
        Clear the routes window and release the current item.
        """
        self.currentItem = None
        self.currentInterface = 1
        self.currentRoute = 1
        self.setWindowTitle("Routes")
        self.removeRows()

    def changed(self, index, index2):
        """
        Handle a change in the interface properties of the current item.
        """
        value = self.model.data(index)
        propertyIndex = self.model.index(index.row(), index.column()-1)
        prop = self.model.data(propertyIndex)

        interfaces = self.currentItem.getInterfaces()
        routes = interfaces[self.currentInterface-1][QtCore.QString("routing")]
        if not routes:
            return

        route = routes[self.currentRoute-1]
        route[prop.toString()] = value.toString()


"""Not being used"""
class ButtonDelegate(QtGui.QItemDelegate):
    def __init__(self, parent = None):
        QtGui.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        return QtGui.QPushButton("Table", parent)

    def setEditorData(self, spinBox, index):
        pass

    def setModelData(self, spinBox, model, index):
        pass

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class TreeView(QtGui.QTreeView):
    def __init__(self):
        QtGui.QTreeView.__init__(self)
        self.delegate = ButtonDelegate()
        self.setItemDelegate(self.delegate)
        
    def selectionChanged(self, selected, deselected):
        for index in selected.indexes():
            if self.model().data(index).toString() == "routing":
                self.edit(self.model().index(index.row(), index.column()+1))
            return

class CustomProxy(QtGui.QGraphicsProxyWidget):
    def __init__(self, parent=None, wFlags=0):
        QtGui.QGraphicsProxyWidget.__init__(self, parent, wFlags)

        self.popupShown = False
        self.timeLine = QtCore.QTimeLine(250, self)
        self.connect(self.timeLine, QtCore.SIGNAL("valueChanged(qreal)"), self.updateStep)
        self.connect(self.timeLine, QtCore.SIGNAL("stateChanged(QTimeLine::State)"), self.stateChanged)
        
    def boundingRect(self):
        return QtGui.QGraphicsProxyWidget.boundingRect(self).adjusted(0, 0, 10, 10)

    def paintWindowFrame(self, painter, option, widget):
        color = QtGui.QColor(0, 0, 0, 64)

        r = self.windowFrameRect()
        right = QtCore.QRectF(r.right(), r.top()+10, 10, r.height()-10)
        bottom = QtCore.QRectF(r.left()+10, r.bottom(), r.width(), 10)
        intersectsRight = right.intersects(option.exposedRect)
        intersectsBottom = bottom.intersects(option.exposedRect)
        if intersectsRight and intersectsBottom:
            path=QtGui.QPainterPath()
            path.addRect(right)
            path.addRect(bottom)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(color)
            painter.drawPath(path)
        elif intersectsBottom:
            painter.fillRect(bottom, color)
        elif intersectsRight:
            painter.fillRect(right, color)

        QtGui.QGraphicsProxyWidget.paintWindowFrame(self, painter, option, widget)

    def hoverEnterEvent(self, event):
        QtGui.QGraphicsProxyWidget.hoverEnterEvent(self, event)

        self.scene().setActiveWindow(self)
        if self.timeLine.currentValue != 1:
            self.zoomIn()

    def hoverLeaveEvent(self, event):
        QtGui.QGraphicsProxyWidget.hoverLeaveEvent(self, event)

        if not self.popupShown and (self.timeLine.direction() != QtCore.QTimeLine.Backward or self.timeLine.currentValue() != 0 ):
            self.zoomOut()

    def sceneEventFilter(self, watched, event):
        if watched.isWindow() and (event.type() == QtCore.QEvent.UngrabMouse or event.type() == QtCore.QEvent.GrabMouse):
            self.popupShown = watched.isVisible()
            if not self.popupShown and not self.isUnderMouse():
                self.zoomOut()

        return QtGui.QGraphicsProxyWidget.sceneEventFilter(self, watched, event)

    def itemChange(self, change, value):
        if change == self.ItemChildAddedChange or change == self.ItemChildRemovedChange :
            # how to translate this line to python?
            # QGraphicsItem *item = qVariantValue<QGraphicsItem *>(value);
            item = value
            try:
                if change == self.ItemChildAddedChange:
                    item.installSceneEventFilter(self)
                else:
                    item.removeSceneEventFilter(self)
            except:
                pass

        return QtGui.QGraphicsProxyWidget.itemChange(self, change, value)

    def updateStep(self, step):
        r=self.boundingRect()
        self.setTransform( QtGui.QTransform() \
                            .translate(r.width() / 4, r.height() / 4)\
                            .scale(1 + 1.25 * step, 1 + 1.25 * step)\
                            .translate(-r.width() / 4, -r.height() / 4))

    def stateChanged(self, state):
        if state == QtCore.QTimeLine.Running:
            if self.timeLine.direction() == QtCore.QTimeLine.Forward:
                self.setCacheMode(self.NoCache)
            elif state == QtCore.QTimeLine.NotRunning:
                if self.timeLine.direction() == QtCore.QTimeLine.Backward:
                    self.setCacheMode(self.DeviceCoordinateCache)

    def zoomIn(self):
        if self.timeLine.direction() != QtCore.QTimeLine.Forward:
            self.timeLine.setDirection(QtCore.QTimeLine.Forward)
        if self.timeLine.state() == QtCore.QTimeLine.NotRunning:
            self.timeLine.start()

    def zoomOut(self):
        if self.timeLine.direction() != QtCore.QTimeLine.Backward:
            self.timeLine.setDirection(QtCore.QTimeLine.Backward)
        if self.timeLine.state() == QtCore.QTimeLine.NotRunning:
            self.timeLine.start()
            
