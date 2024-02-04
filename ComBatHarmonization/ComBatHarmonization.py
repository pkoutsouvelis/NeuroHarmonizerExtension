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
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#ComBatHarmonization">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
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
        self.harmonizationSelector = 'Cortical thickness measurements'
        self.referenceBatch = None

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
        self.ui.comBatSelector.currentTextChanged.connect(self.onHarmonizationSelectorChanged)
        self.ui.addDataFramePathLineEdit.currentPathChanged.connect(self.onNewPathEntered)
        self.ui.splitFileCheckBox.toggled.connect(self.onSplitFileToggled)
        self.ui.createNewDataFrameButton.toggled.connect(self.onCustomDataFrameButtonToggled)
        self.ui.covariatesNames.textChanged.connect(self.onCovariatesInputTextsChanged)
        self.ui.covariatesValues.textChanged.connect(self.onCovariatesInputTextsChanged)
        self.ui.addCovariateButton.clicked.connect(self.onAddCovariateButtonClicked)
        self.ui.removeCovariateButton.clicked.connect(self.onRemoveCovariateButtonClicked)
        self.ui.saveCovariatesButton.clicked.connect(self.onSaveCovariatesButtonClicked)
        self.ui.covariatesSelector.currentTextChanged.connect(self.onCovariatesSelectorChanged)
        self.ui.addFileGroupButton.clicked.connect(self.onAddFileGroupButtonClicked)
        self.ui.removeFileGroupButton.clicked.connect(self.onRemoveFileGroupButtonClicked)
        self.ui.saveDataFrameButton.clicked.connect(self.onSaveDataFrameButtonClicked)
        self.ui.dataFrameSelector1.currentNodeChanged.connect(self.onFeaturesFileChanged)
        self.ui.dataFrameSelector2.currentNodeChanged.connect(self.onCovariatesFileChanged)
        self.ui.referenceBatchComboBox.currentTextChanged.connect(self.onReferenceBatchChanged)
        self.ui.runComBatButton.clicked.connect(self.onRunComBatButtonClicked)
        self.ui.showResultsButton.clicked.connect(self.onShowResultsButtonClicked)
        self.ui.saveResultsButton.clicked.connect(self.onSaveResultsButtonClicked)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()
        self.setupReferenceBatchSelector()
    #
    # Slots and additional class functions
    #
    def onHarmonizationSelectorChanged(self, new):
        self.harmonizationSelector = new
    
    def onNewPathEntered(self, new): 
        if os.path.exists(new):
            self._parameterNode.featuresDataFrame = slicer.util.loadTable(new)
            self.addedPath = new
    
    def onSplitFileToggled(self, data): 
        if data and os.path.exists(self.addedPath):
            self.logic.splitFile(self.addedPath)

    def onCustomDataFrameButtonToggled(self, data): 
        if data: 
            self.ui.covariatesNames.enabled = True
            self.ui.covariatesValues.enabled = True
            self.onCovariatesInputTextsChanged()
        else: 
            self.ui.covariatesNames.setText('')
            self.ui.covariatesValues.setText('')
            self.ui.textEdit.clear()
            self.ui.covariatesNames.enabled = False
            self.ui.covariatesValues.enabled = False
            self.ui.addCovariateButton.enabled = False
            self.ui.removeCovariateButton.enabled = False
            self.ui.saveCovariatesButton.enabled = False
            self.ui.addFileGroupLabel.enabled = False
            self.ui.covariatesSelector.enabled = False
            self.ui.addFileGroupButton.enabled = False
            self.ui.removeFileGroupButton.enabled = False
            self.ui.saveDataFrameButton.enabled = False

    def onCovariatesInputTextsChanged(self):
        if self.ui.covariatesNames.displayText != '' and len(self.ui.covariatesValues.displayText.split(', ')) > 1:
            if self.ui.covariatesValues.displayText.split(', ')[1] != '':
                self.ui.addCovariateButton.enabled = True

    def onAddCovariateButtonClicked(self):
        self.logic.addCovariate(self.ui.covariatesNames.displayText, self.ui.covariatesValues.displayText.split(', '))
        self.covariatesToTextEdit()
        self.ui.covariatesNames.setText('')
        self.ui.covariatesValues.setText('')
        self.ui.covariatesSelector.clear()
        self.ui.addCovariateButton.enabled = False
        self.ui.removeCovariateButton.enabled = True
        self.ui.saveCovariatesButton.enabled = True
        self.ui.addFileGroupLabel.enabled = False
        self.ui.covariatesSelector.enabled = False
        self.ui.addFileGroupButton.enabled = False
        self.ui.removeFileGroupButton.enabled = False
        self.ui.saveDataFrameButton.enabled = False

    def onRemoveCovariateButtonClicked(self):
        self.logic.removeCovariate()
        self.covariatesToTextEdit()
        self.ui.covariatesNames.setText('')
        self.ui.covariatesValues.setText('')
        self.ui.covariatesSelector.clear()
        if self.logic.checkCovariatesNum() == 0: 
            self.ui.addCovariateButton.enabled = False
            self.ui.removeCovariateButton.enabled = False
            self.ui.saveCovariatesButton.enabled = False
            self.ui.addFileGroupLabel.enabled = False
        self.ui.covariatesSelector.enabled = False
        self.ui.addFileGroupButton.enabled = False
        self.ui.removeFileGroupButton.enabled = False
        self.ui.saveDataFrameButton.enabled = False

    def covariatesToTextEdit(self): 
        string = []
        for i, j in zip(self.logic.getCovariateNames(), self.logic.getCovariateValues()):
            string.append(f'{i} : {j}\n')
        string = "".join(string)
        self.ui.textEdit.setText(string)
    
    def onSaveCovariatesButtonClicked(self): 
        import itertools
        self.ui.covariatesSelector.clear()
        if self.logic.checkCovariatesNum() == 1:
            for value in self.logic.getCovariateValues()[0]:
                self.ui.covariatesSelector.addItem(value)
        else:
            combinations = list(itertools.product(*self.logic.getCovariateValues()))
            for combination in combinations: 
                self.ui.covariatesSelector.addItem(str(combination))
        self.ui.addFileGroupLabel.enabled = True
        self.ui.covariatesSelector.enabled = True
        self.ui.textEdit.setText('Add files for each combination of covariates :\n')

    def onCovariatesSelectorChanged(self): 
        self.ui.addFileGroupButton.enabled = True

    def onAddFileGroupButtonClicked(self):
        if self.harmonizationSelector == 'Cortical thickness measurements':
            filter = "Csv files (*.csv)"
        if self.harmonizationSelector == 'Structural MRI data (not recommended)':
            filter = "NiFti files (*.nii.gz)"
        file_names = qt.QFileDialog.getOpenFileNames(self.uiWidget, "Select File", "", filter)
        if file_names:  # if a file is selected
            self.logic.addFilesWithCovariates(file_names, self.ui.covariatesSelector.currentText)
            self.filesToTextEdit()
        self.ui.removeFileGroupButton.enabled = True
        self.ui.saveDataFrameButton.enabled = self.logic.checkCreatedDataFrames()

    def onRemoveFileGroupButtonClicked(self):
        self.logic.removeFilesWithCovariates()
        self.filesToTextEdit()
        self.ui.saveDataFrameButton.enabled = self.logic.checkCreatedDataFrames()
    
    def filesToTextEdit(self):
        string = []
        for i, j in zip(self.logic.getFileNames(), self.logic.getCovariatesList()):
            string.append(f'{i} : {j}\n')
        string = "".join(string)
        self.ui.textEdit.setText(string)

    def onSaveDataFrameButtonClicked(self):
        summary_str = self.logic.saveCovariatesDataFrame()
        if self.harmonizationSelector == 'Cortical thickness measurements':
            self.logic.saveCorticalThicknessDataFrame()
        if self.harmonizationSelector == 'Structural MRI data (not recommended)':
            self.logic.saveStructuralMRIDataFrame()
        
        self.ui.textEdit.setText(summary_str)

    def onFeaturesFileChanged(self, new):
        self._parameterNode.featuresDataFrame = new

    def onCovariatesFileChanged(self, new):
        self._parameterNode.covariatesDataFrame = new #TO DO: apply error checking for imported files
        self.setupReferenceBatchSelector()

    def setupReferenceBatchSelector(self):
        self.ui.referenceBatchComboBox.clear()
        self.ui.referenceBatchComboBox.addItem('None')
        covar_df = slicer.util.dataframeFromTable(self._parameterNode.covariatesDataFrame)
        unique_sites = covar_df.iloc[:, 0].unique()
        for site in unique_sites:
            self.ui.referenceBatchComboBox.addItem(site)
        self.ui.referenceBatchLabel.enabled = True
        self.ui.referenceBatchComboBox.enabled = True

    def onReferenceBatchChanged(self, new):
        self.referenceBatch = new

    def onRunComBatButtonClicked(self):
        self.ui.statusLineEdit.setText('ComBat harmonization started.')
        fileNumber = self.logic.getNumberFromEnd(str(self._parameterNode.covariatesDataFrame.GetName()))
        tableNode, output = self.logic.process(self._parameterNode.covariatesDataFrame, self._parameterNode.featuresDataFrame, self.referenceBatch, fileNumber)
        self._parameterNode.harmonizedDataFrame = tableNode
        self.ui.statusLineEdit.setText(output)
        self.ui.showResultsButton.enabled = True
        self.ui.saveResultsButton.enabled = True

    def onShowResultsButtonClicked(self):
        names = [self._parameterNode.featuresDataFrame.GetName(), self._parameterNode.harmonizedDataFrame.GetName()]
        self.logic.plotDataFrames([self._parameterNode.featuresDataFrame, self._parameterNode.harmonizedDataFrame], names)

    def onSaveResultsButtonClicked(self):
        print('yes')
    
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
        self.resetFiles()

    def getParameterNode(self):
        return ComBatHarmonizationParameterNode(super().getParameterNode())
    
    def splitFile(self, fileName):
        import pandas as pd

        directory = os.path.dirname(fileName)
        title_with_extension = os.path.basename(fileName)  # Removes the directory path, leaving filename
        title, _ = os.path.splitext(title_with_extension)  # Removes the file extension

        df = pd.read_csv(fileName)
        for i in range(len(df.iloc[0,:])):
            df.iloc[:, i].to_csv(f'{directory}/{title}_{i+1}.csv', index=False)
    
    def resetCovars(self): 
        self.covariateNames = []
        self.covariateValues = []
    
    def resetFiles(self):
        self.filesList = []
        self.covariatesList = []
    
    def addCovariate(self, name, values): 
        self.resetFiles()
        self.covariateNames.append(name)
        self.covariateValues.append(values)

    def checkCovariatesNum(self): 
        return len(self.covariateNames)
    
    def removeCovariate(self): 
        self.resetFiles()
        if self.checkCovariatesNum() > 0:
            del self.covariateNames[-1]
            del self.covariateValues[-1]

    def getCovariateNames(self): 
        return self.covariateNames
    
    def getCovariateValues(self):
        return self.covariateValues
    
    def addFilesWithCovariates(self, fileNames, covariates):
        self.sum = len(fileNames)
        for i in fileNames:
            self.filesList.append(i)
            self.covariatesList.append(covariates.split(', '))

    def removeFilesWithCovariates(self):
        if len(self.filesList) >= self.sum:
            del self.filesList[-self.sum:]
            del self.covariatesList[-self.sum:]

    def getFileNames(self):
        return self.filesList
    
    def getCovariatesList(self):
        return self.covariatesList
    
    def checkCreatedDataFrames(self):
        # check enough files exist per covariate combination
        duplicates, indices = self.find_duplicates(self.covariatesList)
        if len(duplicates) < (len(self.covariatesList))/2:
            print(f"Insufficient data provided!\n\n Please ensure that there are at least 2 files for each combination of covariates.")
            tests_passed = 0
        else: 
            tests_passed = 1
        
        # check if all covariate combinations are provided
        unused = []
        for i in range(len(self.covariateNames)): 
            for j in self.covariateValues[i]:
                flag = 0
                for k in range(len(self.covariatesList)):
                    if j in self.covariatesList[k]:
                        flag = 1
                if flag  == 0: 
                    unused.append(j)
        if len(unused) > 0: 
            print(f"Warning!\n\n Covariate values {unused} are not used. You can still run the application but the effect of those covariates will be ignored!")
        # Passing this test is not needed here since it is just a warning
            
        if tests_passed: return True
        else: return False
    
    def find_duplicates(self, list): # returns the indices of the duplicate files
        seen = []
        duplicates = []
        indices = []
        for index, i in enumerate(list):
            if i in seen:
                duplicates.append(i)
                indices.append(index)
            else:
                seen.append(i)
        return duplicates, indices
    
    def getNumOfTableNodes(self):
        return slicer.mrmlScene.GetNodesByClass('vtkMRMLTableNode').GetNumberOfItems()
    
    def saveCovariatesDataFrame(self):
        import pandas as pd
        import numpy as np
        # Prepare covars array in correct format 
        all_covars = [] # numpy array so that it can be transposed
        for i in self.covariatesList: 
            all_covars.append(i)
        all_covars = np.transpose(np.array(all_covars))

        # Create dict and df
        covars_dict = {}
        for i, name in enumerate(self.covariateNames):
            covars_dict[name] = all_covars[i]
        covar_df = pd.DataFrame(covars_dict)

        # Compute some info
        files_num = covar_df.shape[0]
        summary_str = [f'Summary info :\n----------------------\nTotal number of files present : {files_num} \n\nTotal number of files present in each covariate value :\n\n']
        for i in covar_df.columns:
            value_counts = covar_df.groupby(i).size().reset_index(name='Count')
            summary_str.append(f'{value_counts}\n\n')
        summary_str = "".join(summary_str)

        self.NumOfNodes = self.getNumOfTableNodes()
        self.addDataFrameToNode(covar_df, 'covariatesDataFrame', True)
    
        return summary_str
    
    def saveCorticalThicknessDataFrame(self):
        import pandas as pd
        import numpy as np
        
        data_dict = {}
        for i, name in enumerate(self.filesList): 
            df = pd.read_csv(name)
            featuresArray = np.array(df.iloc[:, 0])
            data_dict[f'Column {i}'] = featuresArray
        try:     
            data_df = pd.DataFrame(data_dict)
        except ValueError:
            data_df = pd.DataFrame({})
        
        if len(data_df) == 0:
            print('Data DataFrame creation failed. Ensure all files have same dimensions.')
        else: 
            self.addDataFrameToNode(data_df, 'corticalThicknessDataFrame', True)

    def saveStructuralMRIDataFrame(self):
        import pandas as pd
        
        data_dict = {}
        for i, name in enumerate(self.filesList): 
            # First, load the volume into Slicer
            volumeNode = slicer.util.loadVolume(name)
            # Then, get the numpy array from the volume node
            voxelArray = slicer.util.arrayFromVolume(volumeNode)
            voxelArray = voxelArray.reshape(voxelArray.shape[0] * voxelArray.shape[1] * voxelArray.shape[2]) # convert to 1d
            data_dict[f'Column {i}'] = voxelArray
        try:     
            data_df = pd.DataFrame(data_dict)
        except ValueError:
            data_df = pd.DataFrame({})
        
        if len(data_df) == 0:
            print('Data DataFrame creation failed. Ensure all files have same dimensions.')
        else: 
            self.addDataFrameToNode(data_df, 'structuralMRIDataFrame', True)

    def addDataFrameToNode(self, df, name, addNum):
        # Create a new table node in Slicer or get an existing one
        tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
        if addNum:
            tableNode.SetName(f'{name}_{self.NumOfNodes}')
        else:
            tableNode.SetName(f'{name}')

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
        
        return tableNode

    def getNumberFromEnd(self, string):
        import re
        match = re.search(r'\d+$', string)
        return int(match.group()) if match else None
    
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
                covariatesDataFrame: vtkMRMLTableNode,
                featuresDataFrame: vtkMRMLTableNode,
                refBatch: str,
                number: int) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not covariatesDataFrame or not featuresDataFrame:
            raise ValueError("Input data or covariates are invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Prepare input data
        data_df = slicer.util.dataframeFromTable(featuresDataFrame)
        covars_df = slicer.util.dataframeFromTable(covariatesDataFrame)
        batch_col = covars_df.columns[0]
        if len(covars_df.columns) > 1:
            categorical_cols = []
            for index, col in enumerate(covars_df.columns): 
                if index != 0:
                    categorical_cols.append(col)
        else:
            categorical_cols = None
        ref_batch = refBatch
        
        # Set default values
        continuous_cols = None
        eb = True
        parametric = True
        mean_only = False

        data_combat = self.runNeuroCombat(data_df, covars_df, batch_col, categorical_cols, continuous_cols, eb, parametric, mean_only, ref_batch)

        data_combat = self.numpy2Df(data_combat)
        
        stopTime = time.time()

        if len(data_combat) == 0:
            return_str = f'ComBat harmonization failed. See log for error messages.'
        else:
            return_str = f'ComBat harmonization completed in {stopTime-startTime:.2f} seconds.'
            tableNode = self.addDataFrameToNode(data_combat, f'harmonizedDataFrame_{number}', False)

        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")

        return tableNode, return_str
    
    def numpy2Df(self, arr):
        import pandas as pd

        arr_dict = {}
        for index, col in enumerate(arr.transpose()):
            arr_dict[f'Column{index+1   }'] = col
        df = pd.DataFrame(arr_dict)
        return df



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
