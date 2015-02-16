
FUNCTION(XML2CTF_PARALLEL_TEST DIR TEST_NAME NUM_DECKS)
  
   # The TEST_BLOCKS variable will be used to house the commands
   # for the Tribits advanced test.  It is initialized here.
   SET(TEST_BLOCKS "")

   SET(TRIBITS_NAME xml2ctf_parallel_${TEST_NAME})
   SET(WORKDIR ${CMAKE_CURRENT_BINARY_DIR}/${PACKAGE_NAME}_${TRIBITS_NAME})
   SET(GOLDDIR ${DIR})

   # Add the copy procedures to the TEST_BLOCKS variable for the
   # file names that are always present.
   SET(TEST_BLOCKS ${TEST_BLOCKS}
    TEST_0
      MESSAGE "Running XML Parser...."
      CMND ${PERL_EXECUTABLE}
      ARGS
        ${VERAIn_SOURCE_DIR}/scripts/react2xml.pl ${VERAIn_SOURCE_DIR}/test/${TEST_NAME}.inp ${TEST_NAME}.xml
    TEST_1
       CMND ${PYTHON_EXECUTABLE}
       ARGS ${COBRA_TF_SOURCE_DIR}/utils/par_file_copy.py
            ${NUM_DECKS} ${TEST_NAME}  ${GOLDDIR} ${WORKDIR} .gold
    TEST_2
      MESSAGE "Running xml2ctf..."
      CMND ${CMAKE_CURRENT_BINARY_DIR}/../src/xml2ctf
      ARGS --xmlfile=${TEST_NAME}.xml --inpfile=${TEST_NAME}.inp
    TEST_3
      CMND ${PYTHON_EXECUTABLE}
      ARGS ${COBRA_TF_SOURCE_DIR}/utils/par_file_diff.py
              ${NUM_DECKS} ${TEST_NAME} ${COBRA_TF_SOURCE_DIR}/utils/filter_comments.py
   )

   # Finally, run the Tibits test
   TRIBITS_ADD_ADVANCED_TEST(
      ${TRIBITS_NAME}
      OVERAL_NUM_MPI_PROCS 1
      OVERALL_WORKING_DIRECTORY TEST_NAME
      ${TEST_BLOCKS}
      )

ENDFUNCTION()

FUNCTION(XML2CTF_SERIAL_TEST VERAINDIR GOLDDIR TEST_NAME OPTS)
  TRIBITS_ADD_ADVANCED_TEST(
    xml2ctf_serial_${TEST_NAME}
    OVERALL_WORKING_DIRECTORY TEST_NAME
    OVERALL_NUM_MPI_PROCS 1
    TEST_0
      CMND ${PERL_EXECUTABLE}
      ARGS
        ${VERAIn_SOURCE_DIR}/scripts/react2xml.pl ${OPTS} ${VERAINDIR}/${TEST_NAME}.inp ${TEST_NAME}.xml
    TEST_1
      CMND diff 
      ARGS ${VERAINDIR}/${TEST_NAME}.xml.gold ${TEST_NAME}.xml
    TEST_2
      EXEC xml2ctf NOEXEPREFIX NOEXESUFFIX
      DIRECTORY ../src/
      ARGS --xmlfile=${TEST_NAME}.xml --inpfile=${TEST_NAME}.inp
    TEST_3
      CMND ${PYTHON_EXECUTABLE}
      ARGS ${VERAIn_XML_SOURCE_DIR}/test/filter_comments_whitespace.py
           ${TEST_NAME}.inp ${GOLDDIR}/${TEST_NAME}.inp
    )
ENDFUNCTION()

IF (${PROJECT_NAME}_ENABLE_VERAIn)
   SET(CTF_REGRESSION ${COBRA_TF_SOURCE_DIR}/test_matrix/ctf_regression)
   SET(PREPROC_REGRESSION ${COBRA_TF_SOURCE_DIR}/test_matrix/preproc_regression)
   SET(VERAIN ${VERAIn_SOURCE_DIR}/test)
   SET(GOLD ${CMAKE_CURRENT_SOURCE_DIR}/gold)

   XML2CTF_PARALLEL_TEST  (${PREPROC_REGRESSION} par_cross 5)
   XML2CTF_PARALLEL_TEST  (${CMAKE_CURRENT_SOURCE_DIR} Sample_p7 56)
   XML2CTF_SERIAL_TEST    (${VERAIN}                   ${GOLD}     cross_w_baffle                 "")
   XML2CTF_SERIAL_TEST    (${VERAIN}                   ${GOLD}     small_singlerod_HFP            "")
   XML2CTF_SERIAL_TEST    (${VERAIN}                   ${GOLD}     small_3x3rod_HFP               "")
   XML2CTF_SERIAL_TEST    (${VERAIN}                   ${GOLD}     Sample_p6a_multifuel           "")
   XML2CTF_SERIAL_TEST    (${VERAIN}                   ${GOLD}     small_3x3rod_HFP_2fuel         "")
   XML2CTF_SERIAL_TEST    (${VERAIN}                   ${GOLD}     small_5cross_assem_3x3rod_HFP  "")
   XML2CTF_SERIAL_TEST    (${VERAIN}                   ${GOLD}     small_qtr_core_3x3rod_HFP      "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-00                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-01                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-02                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-03                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-04                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-05                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-06                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-07                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-08                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-09                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-10                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-11                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-12                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-13                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-14                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-15                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-16                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     case5-17                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     stacked_singlerod_HFP          "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     modeling_plenums               "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     3x3_w_multistate               "--multistate")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     test_cobra_edits               "")
   XML2CTF_SERIAL_TEST    (${VERAIN}                   ${GOLD}     chen_3x3                       "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     iapws_singlerod                "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     mixing_coeff                   "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     hdf5_convergence_edit "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     Sample_p6a_parallel "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     bypass "")
   XML2CTF_SERIAL_TEST    (${VERAIN}                   ${GOLD}     small_3x3rod_IFBA "")
   XML2CTF_SERIAL_TEST    (${VERAIN}                   ${GOLD}     small_3x3rod_BProd "")
   XML2CTF_SERIAL_TEST    (${CMAKE_CURRENT_SOURCE_DIR} ${GOLD}     Sample_qtr_core_inlet_bc"")


ENDIF()
