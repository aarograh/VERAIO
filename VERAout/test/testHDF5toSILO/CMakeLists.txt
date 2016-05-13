#-------------------------------------------------------------------------------
# This test simply runs the hdf5tosilocc executable and verifies a silo file
# is produced.
#-------------------------------------------------------------------------------
#
TRIBITS_ADD_ADVANCED_TEST(
  test_hdf5tosilo
  #remove old files
  TEST_0
    CMND ${CMAKE_COMMAND} 
    ARGS -E remove
    vera.h5 vera_0001.silo vera_0002.silo vera_0003.silo vera_0004.silo vera_0005.silo vera_0006.silo vera_0007.silo vera_0008.silo
    NUM_MPI_PROCS 1
  #copy input file
  TEST_1
    CMND ${CMAKE_COMMAND} 
    ARGS -E copy
    ${CMAKE_CURRENT_SOURCE_DIR}/vera.h5 vera.h5
    NUM_MPI_PROCS 1
  #Execute the program
  TEST_2
    EXEC hdf5tosilocc
    NOEXEPREFIX
    NOEXESUFFIX
    DIRECTORY ${VERAout_BINARY_DIR}/src
    ARGS vera.h5
    NUM_MPI_PROCS 1
  #Verify the output file matches
  TEST_3
    CMND ${CMAKE_COMMAND} 
    ARGS -E copy
    vera_0008.silo ifitcanbecopieditmustexist.silo
    NUM_MPI_PROCS 1
)

