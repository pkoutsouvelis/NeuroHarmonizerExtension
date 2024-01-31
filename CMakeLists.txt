cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(NeuroHarmonizerExtension)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/NeuroHarmonizerExtension")
set(EXTENSION_CATEGORY "Learning")
set(EXTENSION_CONTRIBUTORS "Petros Koutsouvelis (Maastricht University)")
set(EXTENSION_DESCRIPTION "This extension is developed to perform MRI harmonization for multi-site MRI analysis. 

Current functionalities include ComBat based harmonization for cortical thickness measurements, originally proposed by: W. Evan Johnson and Cheng Li, Adjusting batch effects in microarray expression data using empirical Bayes methods. Biostatistics, 8(1):118-127, 2007, and implemented by https://github.com/Jfortin1/ComBatHarmonization.git in Python.

Future functionalities will include ComBat for DTI and fMRI, as well as voxel-based harmonization techniques for all MRI modalities. ")
set(EXTENSION_ICONURL "https://www.example.com/Slicer/Extensions/NeuroHarmonizerExtension.png")
set(EXTENSION_SCREENSHOTURLS "https://www.example.com/Slicer/Extensions/NeuroHarmonizerExtension/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(ComBatHarmonization)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
