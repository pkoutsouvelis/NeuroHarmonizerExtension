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

    harmonizationSetting: vtkMRMLTextNode
    covariatesNames: vtkMRMLTableNode
    covariatesValues: vtkMRMLTableNode
    filePaths: vtkMRMLTableNode
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

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)
        
        #
        # Define first collabsible button
        #
        self.parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        self.parametersCollapsibleButton.text = "Input Parameters"
        self.layout.addWidget(self.parametersCollapsibleButton)

        # Layout within the dummy collapsible button
        parametersFormLayout = qt.QFormLayout(self.parametersCollapsibleButton)

        # Input selection combo box
        self.harmonizationSelector = qt.QComboBox()
        self.harmonizationSelector.name = "harmonizationSelector"
        self.harmonizationSelector.addItem("Cortical thickness measurements")
        self.harmonizationSelector.addItem("Diffusion tensor imaging")
        self.harmonizationSelector.addItem("Functional connectivity")
        self.harmonizationSelector.currentTextChanged.connect(self.onHarmonizationSelectorChanged)
        parametersFormLayout.addRow("ComBat Harmonization Task: ", self.harmonizationSelector)

        # Add separator
        separator = qt.QFrame()
        parametersFormLayout.addRow(separator)

        # Input features DataFrame
        self.newDataFrameButton = qt.QPushButton("Add file")
        self.newDataFrameButton.name = "newDataFrameButton"
        self.newDataFrameButton.setToolTip("Select .csv or .txt file with features x samples")
        self.newDataFrameButton.clicked.connect(self.onNewDataFrameButtonClicked)
        parametersFormLayout.addRow("Add new DataFrame :", self.newDataFrameButton)

        # Add separator
        separator = qt.QFrame()
        parametersFormLayout.addRow(separator)

        # Create custom DataFrame checkbox
        self.customDataFrameButton = qt.QCheckBox()
        self.customDataFrameButton.name = "customDataFrameButton"
        self.customDataFrameButton.setToolTip("Click to create custom features and covariates dataframes")
        self.customDataFrameButton.toggled.connect(self.onCustomDataFrameButtonToggled)
        parametersFormLayout.addRow("Create custom DataFrames : ", self.customDataFrameButton)

        # Create empty adjustable widget 
        self.dynamicWidget = qt.QWidget()
        self.dynamicWidgetLayout = qt.QVBoxLayout()
        self.dynamicWidget.setLayout(self.dynamicWidgetLayout)
        parametersFormLayout.addRow(self.dynamicWidget)

        # Add separator
        separator = qt.QFrame()
        parametersFormLayout.addRow(separator)

        # Add separator with line
        separator = qt.QFrame()
        separator.setFrameShape(qt.QFrame.HLine) # Horizontal line
        parametersFormLayout.addRow(separator)

        # Add separator
        separator = qt.QFrame()
        parametersFormLayout.addRow(separator)

        # Choose existing features DataFrame
        self.featuresFileSelector = slicer.qMRMLNodeComboBox()
        self.featuresFileSelector.name = "featuresFileSelector"
        self.featuresFileSelector.nodeTypes = ["vtkMRMLTableNode"]
        self.featuresFileSelector.selectNodeUponCreation = False
        self.featuresFileSelector.addEnabled = False
        self.featuresFileSelector.removeEnabled = False
        self.featuresFileSelector.noneEnabled = False
        self.featuresFileSelector.showHidden = False
        self.featuresFileSelector.showChildNodeTypes = False
        self.featuresFileSelector.setMRMLScene( slicer.mrmlScene )
        self.featuresFileSelector.setToolTip( "Choose an existing features file" )
        self.featuresFileSelector.currentNodeChanged.connect(self.onFeaturesFileChanged)
        parametersFormLayout.addRow("Features file : ", self.featuresFileSelector)

        # Choose existing covariates DataFrame
        self.covariatesFileSelector = slicer.qMRMLNodeComboBox()
        self.covariatesFileSelector.name = "covariatesFileSelector"
        self.covariatesFileSelector.nodeTypes = ["vtkMRMLTableNode"]
        self.covariatesFileSelector.selectNodeUponCreation = False
        self.covariatesFileSelector.addEnabled = False
        self.covariatesFileSelector.removeEnabled = False
        self.covariatesFileSelector.noneEnabled = False
        self.covariatesFileSelector.showHidden = False
        self.covariatesFileSelector.showChildNodeTypes = False
        self.covariatesFileSelector.setMRMLScene( slicer.mrmlScene )
        self.covariatesFileSelector.setToolTip( "Choose an existing covariates file" )
        self.covariatesFileSelector.currentNodeChanged.connect(self.onCovariatesFileChanged)
        parametersFormLayout.addRow("Covariates file : ", self.covariatesFileSelector)

        # Add separator
        separator = qt.QFrame()
        parametersFormLayout.addRow(separator)

        # Add separator with line
        separator = qt.QFrame()
        separator.setFrameShape(qt.QFrame.HLine) # Horizontal line
        parametersFormLayout.addRow(separator)

        # Add to layout
        self.layout.addWidget(self.parametersCollapsibleButton)
        self.ui = slicer.util.childWidgetVariables(self.parametersCollapsibleButton)

        # Add vertical spacer
        self.layout.addStretch(1)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        #uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = ComBatHarmonizationLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    #
    # Slots and additional class functions
    #
    def onHarmonizationSelectorChanged(self, new):
        self._parameterNode.harmonizationSetting = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTextNode")
        self._parameterNode.harmonizationSetting.SetText(new)
        print(self._parameterNode.harmonizationSetting.GetText())
    
    def onNewDataFrameButtonClicked(self): 
        filter = "Text files (*.txt)" + "Csv files (*.csv)"
        self.file_name = qt.QFileDialog.getOpenFileName(self.parametersCollapsibleButton, "Select File", "", filter)
        if self.file_name:  # if a file is selected
            self._parameterNode.featuresDataFrame = slicer.util.loadTable(self.file_name)

    def onFeaturesFileChanged(self):
        print('test')

    def onCovariatesFileChanged(self):
        print('test')

    def onCustomDataFrameButtonToggled(self, data):
        if data: 
            self.createDynamicWidget()
        else: 
            self.emptyDynamicWidget()
    
    def createDynamicWidget(self): 
        self.dynamicWidgetSeparator = qt.QFrame()
        dynamicWidget_covariatesNamesLabel = qt.QLabel("Enter covariate name :")
        dynamicWidget_covariatesNamesText = qt.QLineEdit()
        dynamicWidget_nextValueButton = qt.QPushButton('Next')
        
        self.dynamicWidget_covariatesHorizontalLayout = qt.QHBoxLayout()
        self.dynamicWidget_covariatesHorizontalLayout.addWidget(dynamicWidget_covariatesNamesLabel)
        self.dynamicWidget_covariatesHorizontalLayout.addWidget(dynamicWidget_covariatesNamesText)
        self.dynamicWidget_covariatesHorizontalLayout.addWidget(dynamicWidget_nextValueButton)

        self.dynamicWidgetLayout.addWidget(self.dynamicWidgetSeparator)
        self.dynamicWidgetLayout.addLayout(self.dynamicWidget_covariatesHorizontalLayout)

    def emptyDynamicWidget(self):
        self.dynamicWidgetLayout.removeItem(self.dynamicWidget_covariatesHorizontalLayout)
        self.dynamicWidgetSeparator.hide()
    
        # Properly delete or hide all widgets in the horizontal layout
        for i in reversed(range(self.dynamicWidget_covariatesHorizontalLayout.count())): 
            widget = self.dynamicWidget_covariatesHorizontalLayout.itemAt(i).widget()
            if widget is not None: 
                # Hide the widget
                widget.hide()
        
        # Remove the separator from the layout and delete it
        self.dynamicWidgetLayout.removeWidget(self.dynamicWidgetSeparator)
        self.dynamicWidgetSeparator.hide()

            
    
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
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

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
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
            self.ui.applyButton.toolTip = _("Compute output volume")
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = _("Select input and output volume nodes")
            self.ui.applyButton.enabled = False

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            # Compute output
            self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
                               self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

            # Compute inverted output (if needed)
            if self.ui.invertedOutputSelector.currentNode():
                # If additional output volume is selected then result with inverted threshold is written there
                self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
                                   self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)


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

    def getParameterNode(self):
        return ComBatHarmonizationParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")


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
