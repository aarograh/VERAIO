

TRIBITS_PACKAGE_DECL(VERAIn)
TRIBITS_PROCESS_SUBPACKAGES()
TRIBITS_PACKAGE_DEF()

#
# The outer VERAIn SE package
#
# ToDo: Move all of this into a subpackage VERAIn_react2xml in subdir
# react2xml/
#

ADD_SUBDIRECTORY(src)

TRIBITS_ADD_TEST_DIRECTORIES(test)

# Install the reactor-aware ASCII input parser

INSTALL(
  PROGRAMS scripts/react2xml.pl
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
  DIRECTORY docs/
  DESTINATION "share/VERAIn/doc"
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


TRIBITS_PACKAGE_POSTPROCESS()
