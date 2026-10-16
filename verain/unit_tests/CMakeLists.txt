#===========================================================
#
# CTest tests for the verain Python package
#
# These tests correspond to what 'pytest tests/' would discover.
# Each pytest test file becomes a separate ctest test.
#
#===========================================================

FIND_PACKAGE(Python3 COMPONENTS Interpreter QUIET)

IF(NOT Python3_EXECUTABLE)
  MESSAGE(STATUS "Python3 interpreter not found; skipping verain pytest tests.")
  RETURN()
ENDIF()

# Verify pytest is available; if not, warn but still register the tests so
# ctest surfaces the failure with a meaningful message rather than silently
# skipping.

SET(VERAIN_PYTEST_FILES
  test_basic
  test_directory_processor
  test_directory_processor_merge
  test_input_parser
  test_input_parser_plugin
  test_integration
  test_plugin_registry
  test_react2xml
  test_react2xml_plugins
  test_setvar_resolve
  test_validation_engine
  test_validation_errors
  test_validation_integration
  test_xml_generator
  test_xml_generator_plugin
)

FOREACH(TEST_FILE ${VERAIN_PYTEST_FILES})
  TRIBITS_ADD_ADVANCED_TEST(
    pytest_${TEST_FILE}
    OVERALL_WORKING_DIRECTORY TEST_NAME
    OVERALL_NUM_MPI_PROCS 1
    TEST_0
      CMND "${Python3_EXECUTABLE}"
      ARGS -m pytest "${CMAKE_CURRENT_SOURCE_DIR}/${TEST_FILE}.py" -v
  )
ENDFOREACH()

# Code-quality checks — run black (format) and pylint (lint) over the package

SET(VERAIN_PACKAGE_SRC "${CMAKE_CURRENT_SOURCE_DIR}/../verain")

TRIBITS_ADD_ADVANCED_TEST(
  black_format_check
  OVERALL_WORKING_DIRECTORY TEST_NAME
  OVERALL_NUM_MPI_PROCS 1
  TEST_0
    CMND "${Python3_EXECUTABLE}"
    ARGS -m black --check --target-version py311 "${VERAIN_PACKAGE_SRC}"
)

TRIBITS_ADD_ADVANCED_TEST(
  pylint_check
  OVERALL_WORKING_DIRECTORY TEST_NAME
  OVERALL_NUM_MPI_PROCS 1
  TEST_0
    CMND "${Python3_EXECUTABLE}"
    ARGS -m pylint
      --rcfile "${CMAKE_CURRENT_SOURCE_DIR}/../pyproject.toml"
      "${VERAIN_PACKAGE_SRC}"
)
