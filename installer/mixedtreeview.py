#! /usr/bin/python

"""This example illustrates a way of specifying radiobuttons to be drawn on 
programmatically selected treeview items, using an ItemDelegate.
This example permits mixing of checkboxes and radiobuttons within the same 
parent while maintaining exclusivity with the radiobuttons."""

from PyQt4 import QtCore, QtGui

import treeitems

class MixedTreeModel(QtCore.QAbstractItemModel):
    """The model to be followed for showing data in the TreeView"""
    
    checkStateChangeRequest = QtCore.pyqtSignal(object, bool)
    
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.rootConfig = None
        self.rootItem = treeitems.TreeItem(None)
        self.rootItem.name = "Item"
        self.rootItem.summary = "Summary"

    def dataInit(self, data):
        self.rootConfig = data
        self.rootItem = data.rootItem()
        self.rootItem.name = "Item"
        self.rootItem.summary = "Summary"

    def columnCount(self, parent):
        return 2
        
    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == QtCore.Qt.DisplayRole:
            # Core wants text to display, depending on the column
            return item.data(index.column())
        
        elif role == QtCore.Qt.CheckStateRole:
            # Core wants checkstates
            if item.checkType is not None and index.column() == 0:
                if item.isChecked(): 
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked

        return None
            
    def setData(self, index, value, role):
        status = False
        
        if role == QtCore.Qt.CheckStateRole:
            item = index.internalPointer()
            
            self.checkStateChangeRequest.emit(item, not item.isChecked())
            
            status = True
            self.refreshList()
                
        return status

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        
        flags = QtCore.Qt.ItemIsEnabled
        item = index.internalPointer()
        
        if item.checkType is not None:
            flags |= QtCore.Qt.ItemIsUserCheckable
        
        return flags

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def refreshList(self):
        self.layoutChanged.emit()
    
    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()
        
        if parentItem == self.rootItem:
            return QtCore.QModelIndex()
        
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

class ItemDelegate(QtGui.QItemDelegate):
    """Provide base functionality to change the default decoration for the listitem"""
    
    def paint(self, painter, option, index):
        # Save the current item for later, to allow us to differentiate between
        # what kind of checkbox to draw.
        self.currentItem = index.internalPointer()
        super(self.__class__, self).paint(painter, option, index)

    def drawCheck( self, painter, option, rect, state ):
        if not rect.isValid(): 
            return

        option.rect = rect
        option.state &= ~QtGui.QStyle.State_HasFocus
        option.state |= {
            QtCore.Qt.Unchecked: QtGui.QStyle.State_Off,
            QtCore.Qt.PartiallyChecked: QtGui.QStyle.State_NoChange,
            QtCore.Qt.Checked: QtGui.QStyle.State_On
        }[ state ]

        style = QtGui.QApplication.style()
        
        # Decide if we draw a checkbox or radiobutton based on data provided in 
        # the current item.
        if self.currentItem.checkType == 2:
            style.drawPrimitive( QtGui.QStyle.PE_IndicatorRadioButton, option, painter)
        else:
            style.drawPrimitive( QtGui.QStyle.PE_IndicatorViewItemCheck, option, painter)
            
class MixedTreeView(QtGui.QTreeView):
    def __init__(self, *args):
        super(self.__class__, self).__init__(*args)
        
        self.model = MixedTreeModel()
        self.setModel(self.model)
        self.setMouseTracking(True)
        
        delegate = ItemDelegate()
        self.setItemDelegate(delegate)
        
    def parseData(self, data):
        return self.model.dataInit(data)    

if __name__ == "__main__":

    import sys

    app = QtGui.QApplication(sys.argv)
    widget = MixedTreeView()
    widget.show()
    sys.exit(app.exec_())