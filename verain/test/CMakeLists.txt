INCLUDE(TribitsAddExecutableAndTest)
INCLUDE(TribitsAddAdvancedTest)
INCLUDE(TribitsCopyFilesToBinaryDir)


#
# Test the Reactor-aware PL validator
#
TRIBITS_ADD_EXECUTABLE(
  ReactorAwareParameterListValidator_UnitTests
  SOURCES
    VERA_ReactorAwareParameterListValidator_UnitTests.cpp
    ${TEUCHOS_STD_UNIT_TEST_MAIN}
  #NUM_MPI_PROCS 1
  #STANDARD_PASS_OUTPUT
  )


#
# Function to copy test files and run test for a given test case
#
FUNCTION(ADD_REACTOR_AWARE_INPUT_PARSER_TEST FILE_NAME)
  ASSERT_DEFINED(VERAIn_SOURCE_DIR)
  TRIBITS_COPY_FILES_TO_BINARY_DIR(CopyScriptFiles_${FILE_NAME}
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}
    SOURCE_FILES
      ${FILE_NAME}.inp ${FILE_NAME}.xml.gold
    )
  TRIBITS_ADD_ADVANCED_TEST(
    react2xml_${FILE_NAME}
    OVERALL_WORKING_DIRECTORY TEST_NAME
    TEST_0
      CMND ${CMAKE_COMMAND}
      ARGS -E remove *.xml *.yml
    TEST_1
      CMND ${PERL_EXECUTABLE}
      ARGS
        ${VERAIn_SOURCE_DIR}/scripts/react2xml.pl
        ../${FILE_NAME}.inp  ${FILE_NAME}.xml
    TEST_2
      CMND diff ARGS ${FILE_NAME}.xml ../${FILE_NAME}.xml.gold
    )
ENDFUNCTION()


#
# Run the different test cases
#
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(pr4)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core)

