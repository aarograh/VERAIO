
INCLUDE(TribitsLibraryMacros)

#
# A) Package-specific configuration options
#

#TRIBITS_CONFIGURE_FILE(${PACKAGE_NAME}_Config.h)

#
# B) Define the header and source files (and directories)
#

SET(HEADERS "")
SET(SOURCES "")

SET_AND_INC_DIRS(DIR ${CMAKE_CURRENT_SOURCE_DIR})
APPEND_GLOB(SOURCES ${DIR}/*.F90)

# Must glob the binary src dir last to get all of the generated modules
SET_AND_INC_DIRS(DIR ${CMAKE_CURRENT_BINARY_DIR})

#
# C) Define the targets for package's library(s)
#

TRIBITS_ADD_LIBRARY(
  forpl
  HEADERS ${HEADERS}
  SOURCES ${SOURCES}
  )
