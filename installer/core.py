try:
    # Python 2.x
    import ConfigParser
except(ImportError):
    # Python 3.x
    import configparser as ConfigParser

import os
import collections

from treeitems import TreeItem, InstallItem, PresetItem

class InstallerDict(dict):
    def setChecked(self, id, value):
        for item in self.get(id):
            item.setChecked(value)
        
    def isChecked(self, id):
        return self.get(id)[0].isChecked()
    
    def deps(self, id):
        def getMoreDeps(id, prevdeps=None):
            deps = self.get(id)[0].depends
            
            if prevdeps is None:
                prevdeps = set()
                
            for dep in deps:
                prevdeps.add(dep)
                getMoreDeps(dep, prevdeps)
            
            return prevdeps
        
        return getMoreDeps(id)

class PresetDict(dict):
    pass

class Core(object):
    def __init__(self, installerfileext=".info", presetfileext=".preset"):
        self._treeitems = InstallerDict() # Simple dict of all items found
        self._presetitems = PresetDict()
        self._itemroot = TreeItem(None) # Heirarchy of items, in their respective categories
        self.categories = {} # Categories available
        self.installerfileext = installerfileext # File extension for info files
        self.presetfileext = presetfileext # File extension for info files
    
    def installerItems(self):
        return self._treeitems
    
    def rootItem(self):
        return self._itemroot
    
    def cleanUpItems(self):
        # Delete everything, so we can start from scratch
        del self._itemroot
        for item in self._treeitems:
            del item
            
        for item in self.categories:
            del item
            
        self._treeitems = InstallerDict()
        self._itemroot = TreeItem(None)
        self.categories = {}
    
    def getItems(self, searchdir):
        # Gather filenames matching a specific extension, for later processing
        self.cleanUpItems()
        self.installerdir = searchdir
        directory = os.path.abspath(self.installerdir)
        candidates = []
        
        for dir in os.walk(directory):
            # Find each and every file with desired extension
            
            curdir = dir[0]
            # dirs = dir[1]
            files = dir[2]
            
            for file in files:
                if file.endswith(self.installerfileext):
                    filename = os.path.abspath(os.path.join(curdir, file))
                    candidates.append((filename, curdir))
        
        for item, dir in candidates:
            self.gatherItemData(item, dir)
            
        self.parseItemData()
    
    def getOption(self, parser, section, option, rtn=None):
        # Allow getting an option, providing a default if it doesn't exist
        if parser.has_section(section):
            if parser.has_option(section, option):
                rtn = parser.get(section, option)

        return rtn
                
    def gatherItemData(self, item, dir):
        # Actively process data from the gathered filenames, creating items
        # where needed
        parser = ConfigParser.SafeConfigParser()
        
        try:
            parser.read(item)
    
        except:
            # Not a parsable file.
            return
        
        # Make sure the item has the very least needed to be displayed
        if not parser.has_section("Core"):
            return
        
        if not parser.has_option("Core","name"):
            return
        
        if not parser.has_option("Core","id"):
            return
        
        # Cache the data for the item
        itemname = self.getOption(parser, "Core", "name", "Unnamed item")
        itemsummary = self.getOption(parser, "Core", "summary")
        itemid = self.getOption(parser, "Core", "id")
        itemtooltip = self.getOption(parser, "Core", "tooltip")
        itemhelptext = self.getOption(parser, "Core", "helptext", "<i>No information is available for this item</i>")
        itemchecktype = int(self.getOption(parser, "Core", "checktype", TreeItem.CHECKBOXITEM))
        itemcommands = collections.OrderedDict()
        itemdepends = self.getOption(parser, "Core", "depends", [])
        
        if isinstance(itemdepends, str):
            itemdepends = [x.strip() for x in itemdepends.split(",")]
        else:
            itemdepends = [x.strip() for x in itemdepends]
            
        for name, cmd in parser.items("Commands"):
            if not name in itemcommands:
                itemcommands[name] = cmd
            else:
                raise(RuntimeError("Command %s for item with id %s already exists" % (name, itemid)))
        
        # Provide the ability to have items seem to inhabit multiple categories.
        # Due to how the treeview works, probably the only way to achieve this
        # is to create a copy of the item per category entry.
        cats = [x.strip() for x in self.getOption(parser, "Core", "categories", "Uncategorized").split(",")]
        
        for cat in cats:
            item = InstallItem(itemid)
            item.name = itemname
            item.summary = itemsummary
            item.category = cat
            item.tooltip = itemtooltip
            item.helptext = itemhelptext
            item.cwd = dir
            item.commands = itemcommands
            item.checkType = itemchecktype
            item.depends = itemdepends

            if not item.id in self._treeitems:
                self._treeitems[item.id] = [item,]
            else:
                self._treeitems[item.id].append(item)

    def parseItemData(self):
        # Make the categories that will be displayed. Allows for nested cats
        
        def makeCats(cats, curcat, curpath="/"):
            # Recursively parse a category path, creating category items as 
            # needed
            
            if not cats:
                # No more categories to walk
                return curcat
            
            catname = cats.pop(0)
            curpath = "%s/%s" % (curpath, catname)
            
            if not curpath in self.categories:
                # Make the current path exist, and allow for it to be used 
                # later as well
                
                cat = TreeItem(curpath)
                cat.name = catname
                cat.cwd = curpath
                
                self.categories[curpath] = cat
                curcat.appendChild(cat)
                cat.parentItem = curcat
            else:
                # Use pre-existing path
                cat = self.categories[curpath]
                
            return makeCats(cats, cat, curpath)

        # Parse each item, grab its category path, parse the path
        for itemgroup in self._treeitems.values():
            for item in itemgroup:
                cats = item.category.split("/")
                curcat = makeCats(cats, self._itemroot)
                item.parentItem = curcat
                curcat.appendChild(item)
                
                # Add item to its parents radiogroup if it's a radiobutton item
                if item.checkType == item.RADIOBUTTONITEM:
                    item.parentItem.radioGroup.append(item)
                    
                for dep in itemgroup[0].depends:
                        for x in self._treeitems[dep]:
                            x.dependedby.append(item.id)
    
    def getPresets(self, searchdir):
        self.presetdir = searchdir
        directory = os.path.abspath(self.presetdir)
        candidates = []
        
        for dir in os.walk(directory):
            # Find each and every file with desired extension
            
            curdir = dir[0]
            # dirs = dir[1]
            files = dir[2]
            
            for file in files:
                if file.endswith(self.presetfileext):
                    filename = os.path.abspath(os.path.join(curdir, file))
                    candidates.append((filename, curdir))
        
        for item, dir in candidates:
            self.gatherPresetData(item, dir)
        
    def gatherPresetData(self, item, dir):
        # Actively process data from the gathered filenames, creating items
        # where needed
        parser = ConfigParser.SafeConfigParser()
        
        try:
            parser.read(item)
    
        except:
            # Not a parsable file.
            return
        
        # Make sure the item has the very least needed to be displayed
        if not parser.has_section("Core"):
            return
        
        if not parser.has_option("Core","name"):
            return
        
        if not parser.has_option("Core","id"):
            return
        
        preset = PresetItem(self.getOption(parser, "Core", "id"))
        preset.name = self.getOption(parser, "Core", "name")
        preset.includes = self.getOption(parser, "Core", "includes", []) 
        if preset.includes == "":
            preset.includes = []
        else:
            if isinstance(preset.includes, str):
                preset.includes = [x.strip() for x in preset.includes.split(",")]
            else:
                preset.includes = [x.strip() for x in preset.includes]
                
        preset.excludes = self.getOption(parser, "Core", "excludes", [])
        if preset.excludes == "":
            preset.excludes = []
        else:
            if isinstance(preset.excludes, str):
                preset.excludes = [x.strip() for x in preset.excludes.split(",")]
            else:
                preset.excludes = [x.strip() for x in preset.excludes]
            
        if not preset.id in self._presetitems:
            self._presetitems[preset.id] = preset
        else:
            return
        
    def presetItems(self):
        return self._presetitems
        
if __name__ == "__main__":
    c = Core()
    c.getItems("..\Installers")
    c.getPresets("..\Presets")
    
    for key, itemgroup in c.installerItems().iteritems():
        #print key, "depends on", itemgroup[0].depends, "and is depended on by", itemgroup[0].dependedby
        print key, "depends on", c.installerItems().deps(key)
        
    for key, preset in c.presetItems().iteritems():
        print key, "has id", preset.id, "and includes", preset.includes, "but excludes", preset.excludes
