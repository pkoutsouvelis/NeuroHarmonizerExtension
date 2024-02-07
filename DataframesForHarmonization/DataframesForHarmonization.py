import logging
import os
from typing import Annotated, Optional

import vtk, qt

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode


#
# DataframesForHarmonization
#


class DataframesForHarmonization(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("DataframesForHarmonization")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This module is responsible for creating features and covariates dataframes appropriate for MRI harmonization algorithms. The module is bundled in the NeuroHarmonization extension.
See more information in <a href="https://github.com/organization/projectname#DataframesForHarmonization">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Petros Koutsouvelis, Maastricht University.
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

    # DataframesForHarmonization1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="DataframesForHarmonization",
        sampleName="DataframesForHarmonization1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "DataframesForHarmonization1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="DataframesForHarmonization1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="DataframesForHarmonization1",
    )

    # DataframesForHarmonization2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="DataframesForHarmonization",
        sampleName="DataframesForHarmonization2",
        thumbnailFileName=os.path.join(iconsPath, "DataframesForHarmonization2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="DataframesForHarmonization2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="DataframesForHarmonization2",
    )


#
# DataframesForHarmonizationWidget
#


class DataframesForHarmonizationWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        self.uiWidget = slicer.util.loadUI(self.resourcePath("UI/DataframesForHarmonization.ui"))
        self.layout.addWidget(self.uiWidget)
        self.ui = slicer.util.childWidgetVariables(self.uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        self.uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = DataframesForHarmonizationLogic()

        # Connections

        # Buttons
        self.ui.addFilePathLineEdit.currentPathChanged.connect(self.onNewPathEntered) # File path line edit
        self.ui.addFileButton.clicked.connect(self.onAddFileButtonClicked) # Add file in path line edit
        self.ui.splitFileButton.clicked.connect(self.onSplitFileButtonClicked) # Split file in path line edit
        self.ui.createNewDataFrameCheckBox.toggled.connect(self.onCreateNewDataFrameCheckBoxToggled) # Enable creation of new DataFrames
        self.ui.covariateNameLineEdit.textChanged.connect(self.onCovariateInputTextsChanged) # Error checking on new covariate texts provided
        self.ui.covariateValuesLineEdit.textChanged.connect(self.onCovariateInputTextsChanged) # Error checking on new covariate texts provided
        self.ui.addCovariateButton.clicked.connect(self.onAddCovariateButtonClicked) # Add new covariate texts to covariates list
        self.ui.removeCovariateButton.clicked.connect(self.onRemoveCovariateButtonClicked) # Remove last covariate texts from covariates list
        self.ui.saveCovariatesButton.clicked.connect(self.onSaveCovariatesButtonClicked) # Finalize covariates selection
        self.ui.addFileGroupButton.clicked.connect(self.onAddFileGroupButtonClicked) # Add file groups for selected covariate combination
        self.ui.removeFileGroupButton.clicked.connect(self.onRemoveFileGroupButtonClicked) # Remove last added file group from files list
        self.ui.customNamesCheckBox.toggled.connect(self.onCustomNamesCheckBoxToggled) # Enable input of custom DataFrames names
        self.ui.saveDataFramesCheckBox.toggled.connect(self.onSaveDataFramesCheckBoxToggled) # Enable saving of DataFrames in a local path 
        self.ui.browseFoldersButton.clicked.connect(self.onBrowseFoldersButtonClicked)
        self.ui.applyButton.clicked.connect(self.onApplyButton)
        self.ui.goToComBatLinkButton.clicked.connect(self.onGoToComBatLinkButtonClicked)
    
    def onNewPathEntered(self, new): 
        if os.path.exists(new):
            self.addedPath = new # Process path only when it exists
            self.ui.addFileButton.enabled = True
            self.ui.splitFileButton.enabled = True
        else: 
            self.ui.addFileButton.enabled = False
            self.ui.splitFileButton.enabled = False

    def onAddFileButtonClicked(self):
        slicer.util.loadTable(self.addedPath)
    
    def onSplitFileButtonClicked(self):
        self.logic.splitFile(self.addedPath)
    
    def onCreateNewDataFrameCheckBoxToggled(self, data):
        # Reset all values when check box is toggled
        self.logic.resetCovars()
        self.logic.resetFiles()
        self.ui.covariateNameLineEdit.setText('')
        self.ui.covariateValuesLineEdit.setText('')
        self.ui.textEdit.clear()
        if data: 
            # Enable only first widgets related to dataframe creation (covariates)
            self.ui.inputsTypeLabel.enabled = True
            self.ui.inputsTypeComboBox.enabled = True
            self.ui.configureCovariatesLabel.enabled = True
            self.ui.covariateNameLineEdit.enabled = True
            self.ui.covariateValuesLineEdit.enabled = True
        else: 
            # Disable everything
            self.disableCreateDataFrameWidgets()
    
    def disableCreateDataFrameWidgets(self):
        # Disable all widgets related to dataframe creation
        self.ui.inputsTypeLabel.enabled = False
        self.ui.inputsTypeComboBox.enabled = False
        self.ui.configureCovariatesLabel.enabled = False
        self.ui.covariateNameLineEdit.enabled = False
        self.ui.covariateValuesLineEdit.enabled = False
        self.ui.addCovariateButton.enabled = False
        self.ui.removeCovariateButton.enabled = False
        self.ui.saveCovariatesButton.enabled = False
        self.ui.assignFilesLabel.enabled = False
        self.ui.covariatesSelector.enabled = False
        self.ui.addFileGroupButton.enabled = False
        self.ui.removeFileGroupButton.enabled = False
        self.ui.applyButton.enabled = False
    
    def onCovariateInputTextsChanged(self):
        # Covariate texts error-checking: Enable addition of covariate only if one name is provided and there are at least two values without comma or space being the last character.
        if self.ui.covariateNameLineEdit.displayText != '' and len(self.ui.covariateNameLineEdit.displayText.split(',')) == 1 and len(self.ui.covariateValuesLineEdit.displayText.split(', ')) > 1:
            if self.ui.covariateValuesLineEdit.displayText.split(',')[-1] != '' and self.ui.covariateValuesLineEdit.displayText.split(',')[-1] != ' ':
                self.ui.addCovariateButton.enabled = True
            else:
                self.ui.addCovariateButton.enabled = False
        else:
            self.ui.addCovariateButton.enabled = False
    
    def onAddCovariateButtonClicked(self):
        # Add covariate
        self.logic.addCovariate(self.ui.covariateNameLineEdit.displayText, self.ui.covariateValuesLineEdit.displayText.split(', '))
        self.covariatesToTextEdit()
        # Clear text and enable removal, saving
        self.ui.covariateNameLineEdit.setText('')
        self.ui.covariateValuesLineEdit.setText('')
        self.ui.covariatesSelector.clear()
        self.ui.removeCovariateButton.enabled = True
        self.ui.saveCovariatesButton.enabled = True
        # Reset file assignment since covariates list has changed
        self.ui.assignFilesLabel.enabled = False
        self.ui.covariatesSelector.enabled = False
        self.ui.addFileGroupButton.enabled = False
        self.ui.removeFileGroupButton.enabled = False
        self.ui.applyButton.enabled = False

    def onRemoveCovariateButtonClicked(self):
        # Remove last covariate
        self.logic.removeCovariate()
        self.covariatesToTextEdit()
        self.ui.covariateNameLineEdit.setText('')
        self.ui.covariateValuesLineEdit.setText('')
        self.ui.covariatesSelector.clear()
        # Disable further removal and saving when covariates list is empty
        if self.logic.checkCovariatesNum() == 0: 
            self.ui.removeCovariateButton.enabled = False
            self.ui.saveCovariatesButton.enabled = False
        # Reset file assignment since covariates list has changed
        self.ui.assignFilesLabel.enabled = False
        self.ui.covariatesSelector.enabled = False
        self.ui.addFileGroupButton.enabled = False
        self.ui.removeFileGroupButton.enabled = False
        self.ui.applyButton.enabled = False

    def covariatesToTextEdit(self): 
        # Fetch covariate inputs and display to text edit
        string = []
        for i, j in zip(self.logic.getCovariateNames(), self.logic.getCovariateValues()):
            string.append(f'{i} : {j}\n')
        string = "".join(string)
        self.ui.textEdit.setText(string)

    def onSaveCovariatesButtonClicked(self): 
        # Add all combinations of covariate values provided to the covariates selector
        import itertools
        self.ui.covariatesSelector.clear()
        if self.logic.checkCovariatesNum() == 1:
            # For better visibility, display without parenthesis if only one covariate is input
            for value in self.logic.getCovariateValues()[0]:
                self.ui.covariatesSelector.addItem(value)
        else:
            # Compute all combinations
            combinations = list(itertools.product(*self.logic.getCovariateValues()))
            for combination in combinations: 
                self.ui.covariatesSelector.addItem(str(combination))
        # Enable addition of files
        self.ui.assignFilesLabel.enabled = True
        self.ui.addFileGroupButton.enabled = True
        self.ui.covariatesSelector.enabled = True
        self.ui.textEdit.setText('Add files for each combination of covariates :\n')

    def onAddFileGroupButtonClicked(self):
        # Adjust file dialog filter based on expected input type
        if self.ui.inputsTypeComboBox.currentText == 'Features (*.csv)':
            filter = "Csv files (*.csv)"
        if self.ui.inputsTypeComboBox.currentText == 'Structural MRI (*.nii.gz)':
            filter = "NiFti files (*.nii.gz)"
        file_names = qt.QFileDialog.getOpenFileNames(self.uiWidget, "Select File", "", filter)
        # Add selected files with covariates to the arrays used for dataframes creation and display
        if file_names: 
            self.logic.addFilesWithCovariates(file_names, self.ui.covariatesSelector.currentText)
            self.filesToTextEdit()
        self.ui.removeFileGroupButton.enabled = True
        self._checkCanApply() # Enable/disable "Create DataFrames" button
    
    def onRemoveFileGroupButtonClicked(self):
        self.logic.removeFilesWithCovariates()
        self.filesToTextEdit()
        self._checkCanApply()

    def filesToTextEdit(self):
        string = []
        for i, j in zip(self.logic.getFileNames(), self.logic.getCovariatesList()):
            string.append(f'{i} : {j}\n')
        string = "".join(string)
        self.ui.textEdit.setText(string)

    def _checkCanApply(self, caller=None, event=None) -> None:
        # Error checking for provided files and covariates lists
        self.ui.applyButton.enabled = self.logic.checkCreatedDataFrames()

    def onCustomNamesCheckBoxToggled(self, data):
        # Reset all values when check box is toggled
        self.ui.covariatesDfNameLineEdit.setText('')
        self.ui.featuresDfNameLineEdit.setText('')
        if data: 
            # Enable all related widgets
            self.ui.covariatesDataFrameLabel.enabled = True
            self.ui.covariatesDfNameLineEdit.enabled = True
            self.ui.featuresDataFrameLabel.enabled = True
            self.ui.featuresDfNameLineEdit.enabled = True
        else: 
            # Disable widgets
            self.ui.covariatesDataFrameLabel.enabled = False
            self.ui.covariatesDfNameLineEdit.enabled = False
            self.ui.featuresDataFrameLabel.enabled = False
            self.ui.featuresDfNameLineEdit.enabled = False
    
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
    
    def onApplyButton(self) -> None:
        """Run processing when user clicks "Create DataFrame" button."""
        # Check if NifTi
        if self.ui.inputsTypeComboBox.currentText == 'Structural MRI (*.nii.gz)':
            isNifTi = True
        else:
            isNifTi = False
        # Check if custom name
        if self.ui.covariatesDfNameLineEdit.displayText != '' and self.ui.featuresDfNameLineEdit.displayText != '':
            covarsDfName = self.ui.covariatesDfNameLineEdit.displayText
            featuresDfName = self.ui.featuresDfNameLineEdit.displayText
        else:
            # Set covariates Df default name
            num = self.logic.getNumOfTableNodes()
            if num + 1 < 10:
                covarsDfName = f'covariatesDataFrame_0{num+1}'
            else:
                covarsDfName = f'covariatesDataFrame_{num+1}'
            # Same for files Df, different names if NiFti
            if isNifTi: 
                if num + 1 < 10:
                    featuresDfName = f'structuralMRIDataFrame_0{num+1}'
                else: 
                    featuresDfName = f'structuralMRIDataFrame_{num+1}'
            else:
                if num + 1 < 10:
                    featuresDfName = f'featuresDataFrame_0{num+1}'
                else: 
                    featuresDfName = f'featuresDataFrame_{num+1}'
        # Check if saving is enabled
        if self.ui.saveDataFramesCheckBox.isChecked():
            if os.path.exists(self.ui.directoryPathLineEdit.displayText) and self.ui.directoryPathLineEdit.displayText != '':
                savePath = self.ui.directoryPathLineEdit.displayText
            else: 
                savePath = ''
        else:
            savePath = ''
        # Call saving function
        summary_str = self.logic.process(isNifTi, covarsDfName, featuresDfName, savePath)
        
        self.ui.textEdit.setText(summary_str)
    
    def onGoToComBatLinkButtonClicked(self): 
        slicer.util.selectModule(slicer.modules.combatharmonization)

#
# DataframesForHarmonizationLogic
#

class DataframesForHarmonizationLogic(ScriptedLoadableModuleLogic):
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

    def splitFile(self, fileName):
        import pandas as pd

        directory = os.path.dirname(fileName)
        title_with_extension = os.path.basename(fileName)  # Removes the directory path, leaving filename
        title, _ = os.path.splitext(title_with_extension)  # Removes the file extension
        if not os.path.isdir(f'{directory}/Split Files'):
            os.mkdir(f'{directory}/Split Files')

        df = pd.read_csv(fileName)
        for i in range(len(df.iloc[0,:])):
            if i + 1 < 10:
                df.iloc[:, i].to_csv(f'{directory}/Split Files/{title}_0{i+1}.csv', index=False)
            else: 
                df.iloc[:, i].to_csv(f'{directory}/Split Files/{title}_{i+1}.csv', index=False)
    
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
    
    def removeCovariate(self): 
        self.resetFiles()
        if self.checkCovariatesNum() > 0:
            del self.covariateNames[-1]
            del self.covariateValues[-1]
    
    def checkCovariatesNum(self): 
        return len(self.covariateNames)
    
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
            
        if tests_passed: 
            print(f'Tests passed, DataFrames are ready to save.')
            return True
        else: 
            return False
    
    def find_duplicates(self, list): 
        # returns the indices of the duplicate files
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
    
    def saveCovariatesDataFrame(self, dfName, savePath):
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
        summary_str = ['Covariates DataFrame successfully created.\n']
        summary_str.append(f'Summary info :\n----------------------\nTotal number of files present : {files_num} \n\nTotal number of files present in each covariate value :\n\n')
        for i in covar_df.columns:
            value_counts = covar_df.groupby(i).size().reset_index(name='Count')
            summary_str.append(f'{value_counts}\n\n')
        summary_str = "".join(summary_str)

        self.addDataFrameToNode(covar_df, dfName)
        self.saveLocally(covar_df, dfName, savePath)
    
        return summary_str
    
    def saveFeaturesDataFrame(self, dfName, savePath):
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
            summary_str = 'Data DataFrame creation failed. Ensure all files have same dimensions.'
        else: 
            self.addDataFrameToNode(data_df, dfName)
            self.saveLocally(data_df, dfName, savePath)
            summary_str = 'Data DataFrame successfully created.'
        
        return summary_str

    def saveStructuralMRIDataFrame(self, dfName, savePath):
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
            summary_str = 'Data DataFrame creation failed. Ensure all files have same dimensions.'
        else: 
            self.addDataFrameToNode(data_df, dfName)
            self.saveLocally(data_df, dfName, savePath)
            summary_str = 'Data DataFrame successfully created.'

        return summary_str

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
        

    def process(self,
                isNifTi: bool,
                covarsDfName: str,
                featuresDfName: str,
                savePath: str):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param isNifTi: checks if files are NiFti
        :param covarsDfName: name of covariates DataFrame
        :param featuresDfName: name of features DataFrame
        :param savePath: path to save DataFrames
        """

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Save covariates DataFrame to Node and locally (if applicable)
        summary_str_1 = self.saveCovariatesDataFrame(covarsDfName, savePath)

        # Save NifTi DataFrame to Node and locally (if applicable)
        if isNifTi:
            summary_str_2 = self.saveStructuralMRIDataFrame(featuresDfName, savePath)
        else:
            summary_str_2 = self.saveFeaturesDataFrame(featuresDfName, savePath)

        summary_str =  f'{summary_str_1}\n{summary_str_2}'

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")

        print(summary_str)
        return summary_str


#
# DataframesForHarmonizationTest
#


class DataframesForHarmonizationTest(ScriptedLoadableModuleTest):
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
        self.test_DataframesForHarmonization1()

    def test_DataframesForHarmonization1(self):
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
        inputVolume = SampleData.downloadSample("DataframesForHarmonization1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = DataframesForHarmonizationLogic()

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
