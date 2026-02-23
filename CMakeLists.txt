
project(VERAIO C CXX Fortran)
set(${PROJECT_NAME}_TRIBITS_DIR "" CACHE PATH "Path to TriBITS/tribits")
cmake_minimum_required(VERSION 3.10)
enable_testing()


if (${PROJECT_NAME}_TRIBITS_DIR STREQUAL "")
  message(FATAL_ERROR "Set TRIBITS_DIR to the TriBITS 'tribits' directory.")
endif()

if (NOT EXISTS "${${PROJECT_NAME}_TRIBITS_DIR}/TriBITS.cmake")
  message("${${PROJECT_NAME}_TRIBITS_DIR}/TriBITS.cmake")
  message(FATAL_ERROR "TriBITS.cmake not found in ${PROJECT_NAME}_TRIBITS_DIR='${${PROJECT_NAME}_TRIBITS_DIR}'.")
endif()

set(TRIBITS_BASE_DIR "${${PROJECT_NAME}_TRIBITS_DIR}")
include("${TRIBITS_BASE_DIR}/TriBITS.cmake")

TRIBITS_PROJECT()
