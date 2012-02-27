INCLUDE(TribitsAddExecutableAndTest)

TRIBITS_ADD_EXECUTABLE_AND_TEST(
  ReactorAwareParameterListValidator_UnitTests
  SOURCES
    VERA_ReactorAwareParameterListValidator_UnitTests.cpp
    ${TEUCHOS_STD_UNIT_TEST_MAIN}
  NUM_MPI_PROCS 1
  STANDARD_PASS_OUTPUT
  )


TRIBITS_COPY_FILES_TO_BINARY_DIR(CopyScriptFiles
  SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}
  SOURCE_FILES
    sample_input_pr1.inp sample_input_pr1.xml.gold
    sample_input_pr2.inp
    WEC_PWR4_cycle1_r0.inp
  )


ASSERT_DEFINED(VERAIn_SOURCE_DIR)

TRIBITS_ADD_ADVANCED_TEST(
  first_pass_inc_simple_input_pr1
  TEST_0
    CMND ${PERL_EXECUTABLE}
    ARGS -I ${VERAIn_SOURCE_DIR}/scripts
      ${VERAIn_SOURCE_DIR}/scripts/first_pass_inc.pl 
      sample_input_pr1.inp  sample_input_pr1.xml
  TEST_1
#    CMND ${CMAKE_COMMAND}
#    ARGS -E compare_files sample_input_pr1.xml sample_input_pr1.xml.gold
     CMND diff ARGS sample_input_pr1.xml sample_input_pr1.xml.gold
  )
