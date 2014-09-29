

#===========================================================
#
#            Test the perl VERA input parser
#
#===========================================================

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

#===========================================================
#
#            Test the perl VERA input parser
#
#===========================================================

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
    OVERALL_NUM_MPI_PROCS 1
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
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(misc_options)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_fuelmix)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_maps)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_matmix)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_reflector)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_wsym_assm_even)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_wsym)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p3_mpact)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p3_unit_test)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p3)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p4a_unit_test)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p4_mpact)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p4)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p6a_multifuel)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p6a)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p7)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_3x3)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_7x7)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_HFP_2fuel)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_HFP)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_HZP)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_Peregrine)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_multibundle)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_singlerod_HFP_8g)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_singlerod_HFP)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(test-short)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_wsym_even)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(smr-7x7)


#===========================================================
#
#               Test the verdiff program!
#
#===========================================================


SET(WEEKLY_TEST_DIR ${${PACKAGE_NAME}_SOURCE_DIR}/weekly_testing)


TRIBITS_ADD_ADVANCED_TEST( veradiff_match
  TEST_0 CMND ${VERADIFF_EXE}
    ARGS ${WEEKLY_TEST_DIR}/2a.h5.gold ${WEEKLY_TEST_DIR}/2a.h5.gold
    PASS_REGULAR_EXPRESSION_ALL
      "reading h5 file: .+/verain/weekly_testing/2a.h5.gold"
      "reading dataset: keff"
      "keff1"
      "keff2"
      "diff .+ 0.00 pcm"
      "tol .+ 10.00 pcm"
      "PASS - eigenvalue difference is less than tolerance"
  OVERALL_NUM_MPI_PROCS 1
  )

TRIBITS_ADD_ADVANCED_TEST( veradiff_fail
  TEST_0 CMND ${VERADIFF_EXE}
    ARGS ${WEEKLY_TEST_DIR}/2a.h5.gold ${WEEKLY_TEST_DIR}/2b.h5.gold
    PASS_REGULAR_EXPRESSION_ALL
      "reading h5 file: .+/verain/weekly_testing/2a.h5.gold"
      "reading h5 file: .+/verain/weekly_testing/2b.h5.gold"
      "reading dataset: keff"
      "keff1"
      "keff2"
      "tol .+ 10.00 pcm"
      "FAIL - eigenvalue difference exceeds tolerance"
  OVERALL_NUM_MPI_PROCS 1
  )
