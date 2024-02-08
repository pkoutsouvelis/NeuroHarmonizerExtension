import logging
import os
from typing import Annotated, Optional

import vtk, qt, ctk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode, vtkMRMLTableNode, vtkMRMLTextNode

slicer.util.pip_install('neuroCombat')

#
# ComBatHarmonization
#


class ComBatHarmonization(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("ComBatHarmonization")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Petros Koutsouvelis (Maastricht University)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is module can be used to run ComBat Harmonization algorithms, bundled in the NeuroHarmonization extension.
See more information in <a href="https://github.com/organization/projectname#ComBatHarmonization">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally created by Petros Koutsouvelis, Maastricht University.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # ComBatHarmonization1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="ComBatHarmonization",
        sampleName="ComBatHarmonization1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "ComBatHarmonization1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="ComBatHarmonization1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="ComBatHarmonization1",
    )

    # ComBatHarmonization2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="ComBatHarmonization",
        sampleName="ComBatHarmonization2",
        thumbnailFileName=os.path.join(iconsPath, "ComBatHarmonization2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="ComBatHarmonization2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="ComBatHarmonization2",
    )


#
# ComBatHarmonizationParameterNode
#


@parameterNodeWrapper
class ComBatHarmonizationParameterNode:
    """
    The parameters needed by module.

    harmonizationSetting - Type of harmonization to perform
    covariateNames - Names of all the different covariates to preserve; e.g. scanner, gender
    covariateValues - Possible values each covariate can take; e.g. scanner a, scanner b
    filePaths - List of all filepaths with individual cortical thickness measurements
    covariateDataFrame - DataFrame with covariate values per file with shape (samples, len(covariateNames))
    featuresDataFrame - DataFrame of all cortical thickness measurements with shape (features, samples)
    harmonizedDataFrame - DataFrame of all harmonized cortical thickness measurements with shape (features, samples)
    """

    featuresDataFrame: vtkMRMLTableNode
    covariatesDataFrame: vtkMRMLTableNode
    harmonizedDataFrame: vtkMRMLTableNode


#
# ComBatHarmonizationWidget
#


class ComBatHarmonizationWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None
        self.batchColumn = None
        self.referenceBatch = None
        self.categorical_cols = None
        self.continuous_cols = None
        self.remaining_cols = None
        self.eb = True
        self.parametric = True
        self.mean_only = False

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)
        
        self.uiWidget = slicer.util.loadUI(self.resourcePath("UI/ComBatHarmonization.ui"))

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        self.uiWidget.setMRMLScene(slicer.mrmlScene)

        self.layout.addWidget(self.uiWidget)

        self.ui = slicer.util.childWidgetVariables(self.uiWidget)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = ComBatHarmonizationLogic()

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

         # Connections
        self.ui.addDataFramePathLineEdit.currentPathChanged.connect(self.onNewPathEntered) # Add path of existing csv
        self.ui.addDataFrameButton.clicked.connect(self.onAddDataFrameButtonClicked) # Add csv as a vtkMRMLTableNode
        self.ui.createNewDataFrameButton.toggled.connect(self.onCreateNewDataFrameButtonToggled) # Allow going to the dataframe creation module
        self.ui.goToDfModuleLinkButton.clicked.connect(self.onGoToDfModuleLinkButtonClicked) # Go to the DataFrame dataframe module
        self.ui.dataFrameSelector1.currentNodeChanged.connect(self.onFeaturesFileChanged) # Load vtkMRMLTableNode for features and perform error checking
        self.ui.dataFrameSelector2.currentNodeChanged.connect(self.onCovariatesFileChanged) # Load vtkMRMLTableNode for covariates and perform error checking
        self.ui.batchColumnComboBox.currentTextChanged.connect(self.onBatchColumnChanged) # Update batch column and initialize reference batch combo box
        self.ui.referenceBatchComboBox.currentTextChanged.connect(self.onReferenceBatchChanged) # Update reference batch combobox based on new covariates file added
        self.ui.customNamesCheckBox.toggled.connect(self.onCustomNamesCheckBoxToggled) # Enable input of custom DataFrames names
        self.ui.saveDataFrameCheckBox.toggled.connect(self.onSaveDataFramesCheckBoxToggled) # Enable saving of DataFrames in a local path 
        self.ui.browseFoldersButton.clicked.connect(self.onBrowseFoldersButtonClicked) # Open file dialog to choose directory and get the path
        self.ui.assignColumnsCheckBox.toggled.connect(self.onAssignColumnsCheckBoxToggled) # Allow editing categorical and continuous columns
        self.ui.categoricalColumnsLineEdit.textChanged.connect(self.onCategoricalColumnsLineEditChanged) # Update categorical columns
        self.ui.continuousColumnsLineEdit.textChanged.connect(self.onContinuousColumnsLineEditChanged) # Update continuous columns
        self.ui.applyButton.clicked.connect(self.onRunComBatButtonClicked) # Run ComBat and automatically save to vtkMRMLTableNode and locally if applicable

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()
        self.handleFirstInputs()
    #
    # Slots and additional class functions
    #
    def onNewPathEntered(self, new): 
        if os.path.exists(new) and new[-4:] == '.csv':
            self.addedPath = new # Process path only when it exists and is a csv file
            self.ui.addDataFrameButton.enabled = True
        else: 
            self.ui.addDataFrameButton.enabled = False
    
    def onAddDataFrameButtonClicked(self):
        slicer.util.loadTable(self.addedPath)

    def onCreateNewDataFrameButtonToggled(self, data): 
        # Enable related widget only when checkbox clicked
        if data: 
            self.ui.goToDfModuleLinkButton.enabled = True
        else: 
            self.ui.goToDfModuleLinkButton.enabled = False
    
    def onGoToDfModuleLinkButtonClicked(self):
        slicer.util.selectModule(slicer.modules.dataframesforharmonization)

    def onFeaturesFileChanged(self, new):
        self.ui.applyButton.enabled = self.logic.newFilesDf(new) # Error checking
        self._parameterNode.featuresDataFrame = new # Update input parameter

    def onCovariatesFileChanged(self, new):
        self.ui.applyButton.enabled = self.logic.newCovariatesDf(new) # Error checking
        self._parameterNode.covariatesDataFrame = new # Update input parameter
        self.setupBatchColumnSelector() # Update batch column combo box
    
    def setupBatchColumnSelector(self):
        self.ui.batchColumnComboBox.clear() # Clear every time new covariates file is entered
        covar_df = slicer.util.dataframeFromTable(self._parameterNode.covariatesDataFrame)
        names = covar_df.columns
        for name in names: # Enter covariate (columns) names
            self.ui.batchColumnComboBox.addItem(name)
        self.ui.batchColumnLabel.enabled = True # Enable widgets
        self.ui.batchColumnComboBox.enabled = True
        self.setupReferenceBatchSelector(self.ui.batchColumnComboBox.currentIndex) # Initialize reference batch combobox with current index
        self.setupCategoricalAndContinuousColumnsLineEdit(self.ui.batchColumnComboBox.currentText) # Initialize categorical and continuous LineEdits with current index

    def onBatchColumnChanged(self):
        self.batchColumn = self.ui.batchColumnComboBox.currentText # Set current combobox value
        self.setupReferenceBatchSelector(self.ui.batchColumnComboBox.currentIndex) # Update reference batch combobox with current index
        self.setupCategoricalAndContinuousColumnsLineEdit(self.ui.batchColumnComboBox.currentText) # Update categorical and continuous LineEdits with current index

    def setupReferenceBatchSelector(self, currentIndex):
        self.ui.referenceBatchComboBox.clear() # Clear and enter default every time new covariates file is entered
        self.ui.referenceBatchComboBox.addItem('None (default)')
        self.referenceBatch = self.ui.referenceBatchComboBox.currentText # Set current combobox value
        covar_df = slicer.util.dataframeFromTable(self._parameterNode.covariatesDataFrame)
        unique_sites = covar_df.iloc[:, currentIndex].unique() # Find unique elements in batch column
        for site in unique_sites: # Add elements to combobox
            self.ui.referenceBatchComboBox.addItem(site)
        self.ui.referenceBatchLabel.enabled = True # Enable widgets
        self.ui.referenceBatchComboBox.enabled = True

    def onReferenceBatchChanged(self, new):
        self.referenceBatch = new

    def onAssignColumnsCheckBoxToggled(self, data):
        if data: # Enable related widgets
            self.ui.categoricalColumnsLabel.enabled = True 
            self.ui.categoricalColumnsLineEdit.enabled = True
            self.ui.continuousColumnsLabel.enabled = True
            self.ui.continuousColumnsLineEdit.enabled = True
        else: # Disable widgets
            self.ui.categoricalColumnsLabel.enabled = False 
            self.ui.categoricalColumnsLineEdit.enabled = False
            self.ui.continuousColumnsLabel.enabled = False
            self.ui.continuousColumnsLineEdit.enabled = False

    def setupCategoricalAndContinuousColumnsLineEdit(self, batch):
        covar_df = slicer.util.dataframeFromTable(self._parameterNode.covariatesDataFrame)
        names = covar_df.columns
        string = []
        self.remaining_cols = []
        if len(names)  > 1:
            for name in names: # Enter covariate (columns) names except batch
                if name != batch:
                    self.remaining_cols.append(name)
                    if name == names[-1]:
                        string.append(f'{name}') # Don't add comma to last covariate
                    else:
                        string.append(f'{name}, ')
            string = "".join(string)
            self.ui.categoricalColumnsLineEdit.setText(string) # Set categorical columns
        else: 
            self.ui.categoricalColumnsLineEdit.setText('None')
        self.ui.continuousColumnsLineEdit.setText('None') # Set default continuous columns
    
    def onCategoricalColumnsLineEditChanged(self):
        self.categorical_cols = []
        for col in self.ui.categoricalColumnsLineEdit.displayText.split(', '): 
            self.categorical_cols.append(col)
        self.ui.applyButton.enabled = self.logic.checkCategoricalAndContinuousCols(self.categorical_cols, self.continuous_cols, self.remaining_cols)
    
    def onContinuousColumnsLineEditChanged(self):
        self.continuous_cols = []
        for col in self.ui.continuousColumnsLineEdit.displayText.split(', '): 
            self.continuous_cols.append(col)
        self.ui.applyButton.enabled = self.logic.checkCategoricalAndContinuousCols(self.categorical_cols, self.continuous_cols, self.remaining_cols)
    

    def onCustomNamesCheckBoxToggled(self, data):
        # Reset all values when check box is toggled
        self.ui.harmonizedDfNameLineEdit.setText('')
        if data: 
            # Enable all related widgets
            self.ui.harmonizedDataFrameLabel.enabled = True
            self.ui.harmonizedDfNameLineEdit.enabled = True
        else: 
            # Disable widgets
            self.ui.harmonizedDataFrameLabel.enabled = False
            self.ui.harmonizedDfNameLineEdit.enabled = False
    
    def onSaveDataFramesCheckBoxToggled(self, data):
        # Reset all values when check box is toggled
        #self.ui.directoryPathLineEdit.setText('') # Don't reset because the user may want to switch often
        if data: 
            # Enable all related widgets
            self.ui.savePathLabel.enabled = True
            self.ui.directoryPathLineEdit.enabled = True
            self.ui.browseFoldersButton.enabled = True
        else: 
            # Disable widgets
            self.ui.savePathLabel.enabled = False
            self.ui.directoryPathLineEdit.enabled = False
            self.ui.browseFoldersButton.enabled = False
    
    def onBrowseFoldersButtonClicked(self):
        # Opens a dialog to select a single file.
        save_file_path = qt.QFileDialog.getExistingDirectory(self.uiWidget, "Select Directory", "")
        if save_file_path: 
            self.ui.directoryPathLineEdit.setText(save_file_path)
    
    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

       # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.featuresDataFrame:
            featuresDf = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLTableNode")
            if featuresDf:
                self._parameterNode.featuresDataFrame = featuresDf

        if not self._parameterNode.covariatesDataFrame:
            covariatesDf = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLTableNode")
            if covariatesDf:
                self._parameterNode.covariatesDataFrame = covariatesDf

        if not self._parameterNode.harmonizedDataFrame:
            harmonizedDf = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLTableNode")
            if harmonizedDf:
                self._parameterNode.harmonizedDataFrame = harmonizedDf

    def setParameterNode(self, inputParameterNode: Optional[ComBatHarmonizationParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            #self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
    
    def handleFirstInputs(self): # Initialize when loading the module with current node
        self.onFeaturesFileChanged(self.ui.dataFrameSelector1.currentNode())
        self.onCovariatesFileChanged(self.ui.dataFrameSelector2.currentNode())

    def onRunComBatButtonClicked(self):
        self.ui.statusLineEdit.setText('ComBat harmonization started.') # Initialize in-widget status line
        if self.ui.harmonizedDfNameLineEdit.displayText != '': # Check if custom name
            harmonizedDfName = self.ui.harmonizedDfNameLineEdit.displayText
        else: # Set default names
            fileNumber = self.logic.getNumberFromEnd(str(self._parameterNode.covariatesDataFrame.GetName()))
            if fileNumber < 10:
                harmonizedDfName = f'harmonizedDataFrame_0{fileNumber}'
            else:
                harmonizedDfName = f'harmonizedDataFrame_{fileNumber}'
        if self.ui.saveDataFrameCheckBox.isChecked(): # Check if saving is enabled
            if os.path.exists(self.ui.directoryPathLineEdit.displayText) and self.ui.directoryPathLineEdit.displayText != '':
                savePath = self.ui.directoryPathLineEdit.displayText
            else: 
                savePath = ''
        else:
            savePath = ''
        
        return_str = self.logic.process(featuresDataFrame = self._parameterNode.featuresDataFrame, 
                           covariatesDataFrame = self._parameterNode.covariatesDataFrame, 
                           batch_col = self.batchColumn, 
                           ref_batch = self.referenceBatch,
                           categorical_cols = self.categorical_cols,
                           continuous_cols = self.continuous_cols, 
                           eb = self.ui.ebComboBox.currentText, 
                           parametric = self.ui.parametricComboBox.currentText,
                           mean_only = self.ui.mean_onlyComboBox.currentText, 
                           dfName = harmonizedDfName,
                           savePath = savePath) # Process inputs and run ComBat algorithm
        
        self.ui.statusLineEdit.setText(return_str)

#
# ComBatHarmonizationLogic
#

class ComBatHarmonizationLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)
        
        self.resetCovars()
        self.resetVars()

    def getParameterNode(self):
        return ComBatHarmonizationParameterNode(super().getParameterNode())
    
    def resetCovars(self): 
        self.covariateNames = []
        self.covariateValues = []
        self.covariatesList = []
    
    def resetVars(self):
        self.numFiles = 0
        self.filesTest = 1
        self.sizesTest = 1
        self.filesPerCovTest = 0
        self.colsTest = 1

    def checkCovariatesNum(self): 
        return len(self.covariateNames)

    def getCovariateNames(self): 
        return self.covariateNames
    
    def getCovariateValues(self):
        return self.covariateValues
    
    def getCovariatesList(self):
        return self.covariatesList
    
    def newCovariatesDf(self, covariatesTableNode):
        # Convert vtkMRMLTableNode to dataframe
        covars_df = slicer.util.dataframeFromTable(covariatesTableNode)
        self.covariateNames = covars_df.columns # get covariates names
        for col in self.covariateNames: # get covariate values
            self.covariateValues.append(covars_df[col].unique()) 
        self.covariatesList = []
        for i in range(len(covars_df.iloc[:, 0])): # get covariates list
            tmp = []
            for j in range(len(covars_df.iloc[0, :])):
                tmp.append(covars_df.iloc[i, j])
            self.covariatesList.append(tmp)
        return self.checkCreatedDataFrames() # Check if dataframes are ready for ComBat

    
    def newFilesDf(self, featuresTableNode):
        self.filesTest = 1
        features_df = slicer.util.dataframeFromTable(featuresTableNode)
        self.numFiles = len(features_df.columns)
        refLen = len(features_df[features_df.columns[0]])
        # Check if features have same len, not a new function to avoid loading the df twice
        for col in features_df.columns:
            if len(features_df[col]) != refLen:
                print('Error : All features in the DataFrame must have the same dimensions.')
                self.filesTest = 0
                break
        return self.checkCreatedDataFrames() # Check if dataframes are ready for ComBat  
    
    def compareCovarsWithFiles(self): # Check if covariates match features
        self.sizesTest = 1
        if self.numFiles != len(self.covariatesList):
            self.sizesTest = 0
    
    def checkCovarsPerFile(self): 
        # Check enough files exist per covariate combination
        self.filesPerCovTest = 0
        duplicates = self.find_duplicates(self.covariatesList)
        if len(duplicates) < (len(self.covariatesList))/2:
            print(f"Insufficient data provided!\n\n Please ensure that there are at least 2 files for each combination of covariates.")
        else: 
            self.filesPerCovTest = 1
        
    def find_duplicates(self, list): 
        # returns the indices of the duplicate files
        seen = []
        duplicates = []
        for i in list:
            if i in seen:
                duplicates.append(i)
            else:
                seen.append(i)
        return duplicates
    
    def checkCategoricalAndContinuousCols(self, categorical, continuous, remaining): # Not called here
        self.colsTest = 1
        if categorical == ['None'] and continuous == ['None']:
            if len(remaining) != 0: # check if correctly set to None
                self.colsTest = 0
        elif categorical == ['None'] and continuous != ['None']:
            if continuous != remaining: # check if correct columns are put
                self.colsTest = 0
        elif categorical != ['None'] and continuous == ['None']:
            if categorical != remaining: # check if correct columns are put
                self.colsTest = 0
        else: # Both values not None
            if len(remaining) != len(categorical) + len(continuous): # check if number of columns is correct
                self.colsTest = 0
            for col in continuous:
                if col not in remaining: # check if valid columns are included
                    self.colsTest = 0
            for col in categorical:
                if col not in remaining: # check if valid columns are included
                    self.colsTest = 0
            duplicates = self.find_duplicates(categorical) # check for duplicates
            if len(duplicates) > 0:
                self.colsTest = 0
            duplicates = self.find_duplicates(continuous)
            if len(duplicates) > 0:
                self.colsTest = 0
        return self.checkCreatedDataFrames() # Check again

    def checkCreatedDataFrames(self):
        # Check everything
        self.compareCovarsWithFiles()
        self.checkCovarsPerFile()
        if self.filesTest and self.sizesTest and self.filesPerCovTest and self.colsTest:
            print('All tests successfully passed, data is ready for harmonization.')
            return True
        else: 
            return False
    
    def getNumOfTableNodes(self):
        return slicer.mrmlScene.GetNodesByClass('vtkMRMLTableNode').GetNumberOfItems()

    def addDataFrameToNode(self, df, dfName):
        # Create a new table node in Slicer or get an existing one
        tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
        tableNode.SetName(f'{dfName}')

        # Add columns to the table node for each DataFrame column
        for col in df.columns:
            column = tableNode.AddColumn()
            column.SetName(col)

        # Ensure the table has the same number of rows as the DataFrame
        table = tableNode.GetTable()
        for _ in range(len(df)):
            table.InsertNextBlankRow()

        # Fill the table node with data from the DataFrame
        for rowIndex in range(len(df)):
            for colIndex, colName in enumerate(df.columns):
                tableNode.SetCellText(rowIndex, colIndex, str(df.iloc[rowIndex, colIndex]))

    def saveLocally(self, df, dfName, savePath):
        if savePath != '':
            df.to_csv(f'{savePath}/{dfName}.csv', index=False)

    def getNumberFromEnd(self, string):
        import re
        match = re.search(r'\d+$', string)
        return int(match.group()) if match else None
    
    def numpy2Df(self, arr):
        import pandas as pd

        arr_dict = {}
        for index, col in enumerate(arr.transpose()):
            arr_dict[f'Column{index+1   }'] = col
        df = pd.DataFrame(arr_dict)
        return df
    
    def runNeuroCombat(self, data_df, covars_df, batch_col, categorical_cols, continuous_cols, eb, parametric, mean_only, ref_batch):
        from neuroCombat import neuroCombat
        try: 
            data_combat = neuroCombat(dat=data_df,
            covars=covars_df,
            batch_col=batch_col,
            categorical_cols=categorical_cols,
            continuous_cols=continuous_cols,
            eb=eb,
            parametric=parametric,
            mean_only=mean_only,
            ref_batch=ref_batch)['data']
        
        except ValueError:
            data_combat = []

        return data_combat
    
    def plotDataFrames(self, tableNodesArr, names):
        import matplotlib.pyplot as plt
        import numpy as np

        """
         # switch to a layout containing a chart viewer
        lm = slicer.app.layoutManager()
        lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalPlotView)  # Adjusted for new version
        """

        allPlots = []
        for sample in tableNodesArr:    
            # initialize table MRML node for each sample list
            tableNodes = []
            sample_df = slicer.util.dataframeFromTable(sample)
            # Compute x and y axis from input tables
            for col in range(len(sample_df.columns)):
                # Extract data from each dataframe column
                data = []
                for j in sample_df.iloc[:,col]:
                    data.append(float(j))
                data = np.array(data)
                # Compute axis values
                mean_value = np.mean(data)
                std_deviation = np.std(data)
                x = np.linspace(min(data), max(data), 1000) 
                pdf = (1 / (std_deviation * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean_value) / std_deviation)**2)

                # Add each plot to new tablenode
                tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
                table = tableNode.GetTable()

                # Add columns for x, y, and optional error values
                table.AddColumn(vtk.vtkFloatArray())
                table.AddColumn(vtk.vtkFloatArray())

                # Set column names (if needed)
                table.GetColumn(0).SetName("X")
                table.GetColumn(1).SetName("Y")

                nDataPoints = len(x)
                table.SetNumberOfRows(nDataPoints)
                for i in range(nDataPoints):
                    table.SetValue(i, 0, x[i])
                    table.SetValue(i, 1, pdf[i]) 
                
                tableNodes.append(tableNode)
            
            allPlots.append(tableNodes)

        # create a new chart node
        chartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode")

        for i, name in enumerate(names):
            for j, tableNode in enumerate(allPlots[i]):
                
                """
                if j == 0: # Show label only once
                    plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", f'{name}')
                else: 
                    plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode")
                """
                plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", f'{name}_{j+1}')

                
                plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
                plotSeriesNode.SetXColumnName("X")
                plotSeriesNode.SetYColumnName("Y")

                # format
                plotSeriesNode.SetLineWidth(5)
                if i == 0: plotSeriesNode.SetColor(1, 0, 0) # red for first plot
                else: plotSeriesNode.SetColor(0, 1, 0) # green for other plots

                chartNode.AddAndObservePlotSeriesNodeID(plotSeriesNode.GetID())
        
        # Get or create a plot view node
        pvNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLPlotViewNode')
        pvNodes.SetReferenceCount(pvNodes.GetReferenceCount()-1)
        pvNodes.InitTraversal()
        plotViewNode = pvNodes.GetNextItemAsObject() or slicer.mrmlScene.AddNewNodeByClass('vtkMRMLPlotViewNode')
        
        # Set plot chart ID in plot view node
        plotViewNode.SetPlotChartNodeID(chartNode.GetID())

        return
                
            
    def process(self,
                featuresDataFrame: vtkMRMLTableNode,
                covariatesDataFrame: vtkMRMLTableNode,
                batch_col: str,
                ref_batch: str,
                categorical_cols = list,
                continuous_cols = list,
                eb = str,
                parametric = str,
                mean_only = str,
                dfName = str,
                savePath = str):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        TODO: Enter description of parameters
        """

        if not covariatesDataFrame or not featuresDataFrame:
            raise ValueError("Input data or covariates are invalid")

        import time
        print(categorical_cols, continuous_cols)
        startTime = time.time()
        logging.info("Processing started")

        # Prepare input data
        data_df = slicer.util.dataframeFromTable(featuresDataFrame)
        covars_df = slicer.util.dataframeFromTable(covariatesDataFrame)
        if ref_batch == 'None (default)':
            ref_batch = None
        if categorical_cols == ['None']:
            categorical_cols = None
        if continuous_cols == ['None']:
            continuous_cols = None
        if eb == 'True (default)':
            eb = True
        if parametric == 'True (default)':
            parametric = True
        if mean_only == 'False (default)':
            mean_only = False
        
        print(categorical_cols, continuous_cols)

        # Run ComBat Harmonizartion using neuroComBat. 
        """
        Original repository from Jfortin1 in Github: 
        https://github.com/Jfortin1/neuroCombat/blob/ac82a067412078680973ddf72bd634d51deae735/neuroCombat/neuroCombat.py
        """
        data_combat = self.runNeuroCombat(data_df=data_df, covars_df=covars_df, batch_col=batch_col, 
                                          categorical_cols=categorical_cols, continuous_cols=continuous_cols, 
                                          eb=eb, parametric=parametric, mean_only=mean_only, ref_batch=ref_batch)
        stopTime = time.time()
        
        if len(data_combat) == 0:
            return_str = f'ComBat harmonization failed. See log for error messages.'
        else:
            return_str = f'ComBat harmonization completed in {stopTime-startTime:.2f} seconds.'
            data_combat = self.numpy2Df(data_combat) # Convert to Pandas DataFrame
            self.addDataFrameToNode(data_combat, dfName) # Add DataFrame to vtkMRMLTableNode
            self.saveLocally(data_combat, dfName, savePath) # Save DataFrame locally if selected
       
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")

        return return_str
    



#
# ComBatHarmonizationTest
#


class ComBatHarmonizationTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):  
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_ComBatHarmonization1()

    def test_ComBatHarmonization1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("ComBatHarmonization1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = ComBatHarmonizationLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
