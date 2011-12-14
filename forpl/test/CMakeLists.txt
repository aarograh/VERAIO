INCLUDE(TribitsAddExecutableAndTest)
INCLUDE(TribitsLibraryMacros)
INCLUDE(AddSubdirectories)

TRIBITS_ADD_EXECUTABLE_AND_TEST(
  ForPL_UnitTests
  SOURCES
    ForPL_FUnitTests.F90
    ForPL_UnitTests.cpp
    ${TEUCHOS_STD_UNIT_TEST_MAIN}
  NUM_MPI_PROCS 1
  )
