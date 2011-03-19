import collections

class PresetItem(object):
    def __init__(self, id=None):
        self.id = id
        self.parentid = None
        self.name = None
        self.includes = []
        self.excludes = []

class TreeItem(object):
    """An item displayed within the TreeView"""
    REGULARITEM = None
    CHECKBOXITEM = 1
    RADIOBUTTONITEM = 2
    
    def __init__(self, id=None):
        self.parentID = None # ID of parent item
        self.parentItem = None # Instance of parent item
        self.id = id # Internal identifier (string)
        self.childItems = []
        
        self.name = None # Human-friendly name (string)
        self.summary = None # Small quip about the object
        self.tooltip = None # String
        self.helptext = "<i>No information is available for this item.</i>" # Longer explanation of this entry
        self.cwd = None # Absolute directory for this entry
        self.depends = []
        self.dependedby = []
        
        self.checkType = None
        self.checkState = False
        self.radioGroup = [] # Used for childItems to add themselves to parents
    
    def printChildren(self, level=1):
        for child in self.childItems:
            child.printChildren(level + 1)
            
    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return 2

    def data(self, column):
        if column == 0:
            return self.name
        elif column == 1:
            return self.summary

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem and self in self.parentItem.childItems:
            return self.parentItem.childItems.index(self)

        return 0
    
    def isChecked(self):
        return self.checkState
    
    def _setCheckState(self, state):
        self.checkState = state
        return True
        
    def setChecked(self, state, force=False):
        # Set the checked state of this item, and if it's part of a radiogroup,
        # and it's a radiobutton, clear the other items in the group.
        
        if not self.checkType or self.checkState == state:
            # No change needed
            return
        
        # The 'force' param is only used internal to TreeItem, here. All other
        # code must ignore it.
        if self.checkType is 2:
            # Enforce 'exclusivity' in radiogroups
            if state == True:
                # Uncheck any other items in the parent's radiogroup
                self.parentItem.clearRadioSelections(self)
            elif not force:
                return False

        return self._setCheckState(state)

    def clearRadioSelections(self, ignore=None):
        for item in self.radioGroup:
            if item is ignore:
                continue
            # 'Exclusive' implementation for radiobuttons
            item.setChecked(False, True)
    
class InstallItem(TreeItem):
    def __init__(self, id):
        super(self.__class__, self).__init__(id)
        self.commands = collections.OrderedDict() # { 0: "cmd", 1: "cmd2", ... }