if __name__ == "__main__":
    import sys, os
    
    from PyQt4 import QtCore, QtGui
    
    from installer.core import Core
    
    if not hasattr(sys, "frozen"):
        from PyQt4 import uic
        form_class, base_class = uic.loadUiType(r"installer\gui_main.ui")
    else:
        from installer.gui_main import Ui_Wizard as form_class
    
    def makeDirExist(dir):
        if os.path.exists(dir):
            if os.path.isdir(dir):
                return True
            else:
                return False
        else:
            try:
                os.makedirs(dir)
                return True
            except:
                return False
    
    class MainForm(QtGui.QWizard, form_class):
        def __init__(self, core, parent=None):
            super(self.__class__, self).__init__(parent)
            self.setupUi(self)
            
            self.core = core
            
            self.installerTreeView.clicked.connect(self.itemClicked)
            self.installerTreeView.entered.connect(self.itemEntered)
            self.installerTreeView.model.checkStateChangeRequest.connect(self.itemChecked)
            
            self.introPage.setPixmap(QtGui.QWizard.WatermarkPixmap,
                    QtGui.QPixmap(':/App/images/watermark1.png'))
            
            self.btnLoadPreset.clicked.connect(self.loadPreset)
            
        def itemClicked(self, item):
            i = item.internalPointer()
            self.helpPanel.setHtml(i.helptext)
            
        def itemEntered(self, item):
            i = item.internalPointer()
            pass
            
        def itemChecked(self, thisitem, newstate, forcemissing=False, 
                        forceorphaning=False):
            docheck = True
            missingdeps = []
            dependedby = []
            disableddeps = []
            
            if newstate == True:
                for dep in thisitem.depends:
                    if not dep in self.core.installerItems():
                        missingdeps.append(dep)
                        docheck = False
            else:
                for dep in thisitem.dependedby:
                    if self.core.installerItems().isChecked(dep):
                        dependedby.append(dep)
                        docheck = False
                    
            if docheck:
                if thisitem.depends:
                    if newstate == True:
                        for dep in thisitem.depends:
                            if not self.core.installerItems().isChecked(dep):
                                disableddeps.append(dep)
                                
                        if disableddeps:
                            if not forcemissing:
                                q = QtGui.QMessageBox.question(self, "Required dependencies!", 
                                   "Do you wish to check the following dependencies?\n\n%s" %
                                   ", ".join(disableddeps), "No", "Yes", "Ignore")
                                
                                if q == 1: # Yes
                                    for dep in disableddeps:
                                        self.core.installerItems().setChecked(dep, True)
                                elif q == 0:
                                    docheck = False
                            else:
                                docheck = True
                if docheck: 
                    self.core.installerItems().setChecked(thisitem.id, newstate)
                
                
            else:
                if newstate == True:
                    QtGui.QMessageBox.critical(self, "Missing dependencies!", 
                       "Can't install this item due to the\nfollowing missing dependencies:\n\n%s" %
                       ", ".join(missingdeps))
                else:
                    if not forceorphaning:
                        q = QtGui.QMessageBox.question(self, "Orphaned dependencies!", 
                           "Unchecking will uncheck the following dependents:\n\n%s\n\nContinue?" %
                           ", ".join(dependedby), "No", "Yes", "Ignore")
                        
                        if q == 1 or q == 2: # Yes or Ignore
                            if q == 1: # Yes
                                for dep in dependedby:
                                    self.core.installerItems().setChecked(dep, False)
                    
                    self.core.installerItems().setChecked(thisitem.id, False)
                                
        def parseConfig(self):
            self.installerTreeView.parseData(self.core)
            for key, value in self.core.presetItems().iteritems():
                self.cmbPresets.addItem(value.name, key)
                
            if "default" in self.core.presetItems():
                self.btnLoadPreset.click()
    
        def loadPreset(self):
            presetid = str(self.cmbPresets.itemData(self.cmbPresets.currentIndex()).toString())
            preset = self.core.presetItems()[presetid]
            
            for x in preset.includes:
                item = self.core.installerItems().setChecked(x, True)
                
            for x in preset.excludes:
                item = self.core.installerItems().setChecked(x, False)
                
    app = QtGui.QApplication(sys.argv)
    
    makeDirExist("Installers")
    makeDirExist("Presets")
    
    core = Core()
    core.getItems("Installers")
    core.getPresets("Presets")
    
    myapp = MainForm(core)
    myapp.parseConfig()
    myapp.show()
    
    sys.exit(app.exec_())