

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
  DIRECTORY scripts/Packages scripts/Templates
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

TRIBITS_PACKAGE_POSTPROCESS()
