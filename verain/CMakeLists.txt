

TRIBITS_PACKAGE_DECL(VERAIn)
TRIBITS_PACKAGE_DEF()

#
# The outer VERAIn SE package
#
# ToDo: Move all of this into a subpackage VERAIn_react2xml in subdir
# react2xml/
#

ADD_SUBDIRECTORY(src)

TRIBITS_ADD_TEST_DIRECTORIES(regression_tests)
TRIBITS_ADD_TEST_DIRECTORIES(unit_tests)

# Install the reactor-aware ASCII input parser

INSTALL(
  PROGRAMS scripts/react2xml.pl
  DESTINATION "${${PROJECT_NAME}_INSTALL_RUNTIME_DIR}"
  COMPONENT ${PACKAGE_NAME}
  )

# Install Python script as alternative entry point
INSTALL(
  PROGRAMS scripts/react2xml.py
  DESTINATION "${${PROJECT_NAME}_INSTALL_RUNTIME_DIR}"
  COMPONENT ${PACKAGE_NAME}
  )

INSTALL(
  DIRECTORY scripts/Packages scripts/Templates scripts/Init
  DESTINATION "${${PROJECT_NAME}_INSTALL_RUNTIME_DIR}"
  COMPONENT ${PACKAGE_NAME}
  )

# Install documentation

INSTALL(
  FILES install/README.VERAIn
  DESTINATION "."
  COMPONENT ${PACKAGE_NAME}
  )

# Install Progression Problems

INSTALL(
  DIRECTORY Progression_Problems/
  DESTINATION "share/VERAIn/Progression_Problems"
  COMPONENT ${PACKAGE_NAME}
  )

# Install BWR Progression Problems

INSTALL(
  DIRECTORY BWR_Progression_Problems/
  DESTINATION "share/VERAIn/BWR_Progression_Problems"
  COMPONENT ${PACKAGE_NAME}
  )

# Install Plant Models

INSTALL(
  DIRECTORY plant_models/
  DESTINATION "share/VERAIn/plant_models"
  COMPONENT ${PACKAGE_NAME}
  )


# Install COBRA-TF/VERAIn examples

#IF (${PACKAGE_NAME}_ENABLE_VERAIn_CTF)
#
#  INSTALL(
#    FILES test/small_singlerod_HFP.inp
#    DESTINATION "share/COBRA-TF/example/small_singlerod_HFP"
#    COMPONENT ${PACKAGE_NAME}
#  )
#  # NOTE: We have to install the VERA input parser examples for COBRA-TF here
#  # because the COBRA_TF packages does not know anything about the VERAIn
#  # input parser.
#
#ENDIF()


# Install the verain Python package (with dev extras) via pip.
# Uses cmake/BootstrapPipAndInstall.cmake which:
#   1. Runs ensurepip to ensure pip is present (no-op if already installed).
#   2. Runs pip install --user <src>[dev] to get pytest/black/pylint.
# Build-time target ensures deps are present before ctest runs (even when
# cmake --install is never called, as in CI).
FIND_PACKAGE(Python3 COMPONENTS Interpreter QUIET)
IF(Python3_EXECUTABLE)
  SET(_verain_pip_script "${CMAKE_CURRENT_SOURCE_DIR}/cmake/BootstrapPipAndInstall.cmake")

  # Build-time: runs on every cmake --build, before ctest
  ADD_CUSTOM_TARGET(verain_pip_dev_install ALL
    COMMAND "${CMAKE_COMMAND}"
      -D PYTHON_EXE=${Python3_EXECUTABLE}
      -D VERAIN_SOURCE_DIR=${CMAKE_CURRENT_SOURCE_DIR}
      -P "${_verain_pip_script}"
    COMMENT "Bootstrapping pip and installing verain dev dependencies"
    VERBATIM
  )

  # Install-time: also run during cmake --install
  INSTALL(CODE "
    EXECUTE_PROCESS(
      COMMAND \"${CMAKE_COMMAND}\"
        -D PYTHON_EXE=${Python3_EXECUTABLE}
        -D VERAIN_SOURCE_DIR=${CMAKE_CURRENT_SOURCE_DIR}
        -P \"${_verain_pip_script}\"
    )
  ")
ELSE()
  MESSAGE(STATUS "Python3 interpreter not found; skipping verain pip install.")
ENDIF()

TRIBITS_PACKAGE_POSTPROCESS()
