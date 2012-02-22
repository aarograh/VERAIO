INCLUDE(TribitsAddExecutableAndTest)

TRIBITS_ADD_EXECUTABLE_AND_TEST(
  ReactorAwareParameterListValidator_UnitTests
  SOURCES
    VERA_ReactorAwareParameterListValidator_UnitTests.cpp
    ${TEUCHOS_STD_UNIT_TEST_MAIN}
  NUM_MPI_PROCS 1
  STANDARD_PASS_OUTPUT
  )
