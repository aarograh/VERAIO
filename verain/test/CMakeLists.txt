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
  TRIBITS_COPY_FILES_TO_BINARY_DIR(ReactAware_CopyScriptFiles_${FILE_NAME}
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
        ${VERAIn_SOURCE_DIR}/scripts/react2xml.pl --xInit
        ../${FILE_NAME}.inp  ${FILE_NAME}.xml
    TEST_2
      CMND diff ARGS ${FILE_NAME}.xml ../${FILE_NAME}.xml.gold
    )
ENDFUNCTION()

#
# Run the different test cases
#
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(apr1400-cyc1)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-ge9)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-azixs)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-peach-1)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-peach-2)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-peach-3)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-peach-4)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-peach-5)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-peach-6)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-p6-test)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-thickthincb)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-plr)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr-axialvoid)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(ex7_bwr)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(bwr_jagged)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(chen_3x3)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(cross_w_baffle)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(ctf_convergence_terms)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(default_density_change)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(detector_edits)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(FAST_input_block)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(fast_3x3rod_HFP)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(fuel_options)
#ADD_REACTOR_AWARE_INPUT_PARSER_TEST(mamba1d_block)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(mamba_mass_bal)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(misc_options)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(MSED)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(mspc)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(mox1)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(p6a_sa_1300_vuq)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(par_cross)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(pwr-CE-2a)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(pwr-CE-2b)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(pwr_CE_single_16x16)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_3x3)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_3x3_multistate)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_7x7)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_fuelmix)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_maps)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_matmix)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_reflector)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_wsym_assm_even)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_wsym_even)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_wsym)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_wsym_state_assm)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_wsym_state_assm_matopt)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_wsym_state_dsym)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_full_core_wsym_state)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p3)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p3_mpact)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p3_unit_test)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p3_Anderson)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p4a_unit_test)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p4)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p4_mpact)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p6a)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p6a_multifuel)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p7)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p9_restart)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p9_shuffle)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_p9_jumpin)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Sample_qtr_core_wsym_3x3_standalone)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(Seabrook_5x5rod_HFP)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_Bison)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_Bison_standalone)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_BProd)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_HFP_2fuel)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_HFP_8g)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_HFP)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_HZP)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_3x3rod_IFBA)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_5cross_assem_3x3rod_HFP)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_multibundle)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_multibundle_par)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_qtr_core_3x3rod_HFP)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_singlerod_HFP_8gb)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_singlerod_HFP_8g)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(small_singlerod_HFP)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(disable_xml2ctf)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(smr-7x7)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(test_cobra_edits_inimat)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(test_cobra_edits)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(test-short)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(test_verashift_3a)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(test_verashift_3a_forward)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(test_verashift_3a_cadis)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(test_verashift_4mini_nonunique)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(with-dash)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(2a_LS)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(2a_LS_default)
ADD_REACTOR_AWARE_INPUT_PARSER_TEST(5cross_multiassem)
#===========================================================
#
#               Test for the expected faiures.
#
#===========================================================

FUNCTION(ADD_REACTOR_AWARE_INPUT_PARSER_FAIL_TEST FILE_NAME)
  ASSERT_DEFINED(VERAIn_SOURCE_DIR)
  TRIBITS_COPY_FILES_TO_BINARY_DIR(ReactAware_CopyScriptFiles_${FILE_NAME}
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}
    SOURCE_FILES ${FILE_NAME}.inp
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
        ${VERAIn_SOURCE_DIR}/scripts/react2xml.pl --xInit
        ../${FILE_NAME}.inp  ${FILE_NAME}.xml
      WILL_FAIL
    )
ENDFUNCTION()

ADD_REACTOR_AWARE_INPUT_PARSER_FAIL_TEST(front-dash)
ADD_REACTOR_AWARE_INPUT_PARSER_FAIL_TEST(decreasing-axial)
ADD_REACTOR_AWARE_INPUT_PARSER_FAIL_TEST(test_verashift_4mini_nonunique_bioshield)
ADD_REACTOR_AWARE_INPUT_PARSER_FAIL_TEST(test_verashift_small_core_bioshield_no_pv)
ADD_REACTOR_AWARE_INPUT_PARSER_FAIL_TEST(multi_scalar_error)

# copy temperature table files for Sample_full_core_wsym_state_assm
TRIBITS_COPY_FILES_TO_BINARY_DIR(Temp_Table_Files
  SOURCE_FILES
    g182_table_tavg_rev0.tab
    g185_table_tavg_rev0.tab
    u26_table_tavg_rev0.tab
    u31_table_tavg_rev0.tab
  SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}
  DEST_DIR
    ${CMAKE_CURRENT_BINARY_DIR}
  )


#===========================================================
#
#               Test the veradiff program!
#
#===========================================================


SET(VERAIn_TEST_DIR ${${PACKAGE_NAME}_SOURCE_DIR}/test)


TRIBITS_ADD_ADVANCED_TEST( veradiff_match
  TEST_0 CMND ${VERADIFF_EXE}
    ARGS ${VERAIn_TEST_DIR}/Sample_2a.h5 ${VERAIn_TEST_DIR}/Sample_2a.h5
    PASS_REGULAR_EXPRESSION_ALL
      "reading h5 file: .+/verain/test/Sample_2a.h5"
      "reading dataset: STATE_0001/keff"
      "keff1"
      "keff2"
      "diff .+ 0.00 pcm"
      "tol .+ 10.00 pcm"
      "PASS - eigenvalue difference is less than tolerance"
  OVERALL_NUM_MPI_PROCS 1
  )

TRIBITS_ADD_ADVANCED_TEST( veradiff_fail
  TEST_0 CMND ${VERADIFF_EXE}
    ARGS ${VERAIn_TEST_DIR}/Sample_2a.h5 ${VERAIn_TEST_DIR}/Sample_2b.h5
    PASS_REGULAR_EXPRESSION_ALL
      "reading h5 file: .+/verain/test/Sample_2a.h5"
      "reading h5 file: .+/verain/test/Sample_2b.h5"
      "reading dataset: STATE_0001/keff"
      "keff1"
      "keff2"
      "tol .+ 10.00 pcm"
      "FAIL - eigenvalue difference exceeds tolerance"
  OVERALL_NUM_MPI_PROCS 1
  )

#===========================================================
#
#            Test thermal expansion
#
#===========================================================

FUNCTION(ADD_THERMAL_EXPANSION_TEST FILE_NAME)
  ASSERT_DEFINED(VERAIn_SOURCE_DIR)
  TRIBITS_COPY_FILES_TO_BINARY_DIR(ThermalExpCopyScriptFiles_${FILE_NAME}
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}
    SOURCE_FILES
      ${FILE_NAME}.inp ${FILE_NAME}.xml.gold ${FILE_NAME}.xml2.gold
    )
  TRIBITS_ADD_ADVANCED_TEST(
    xmlthexp_${FILE_NAME}
    OVERALL_WORKING_DIRECTORY TEST_NAME
    OVERALL_NUM_MPI_PROCS 1
    TEST_0
      CMND ${CMAKE_COMMAND}
      ARGS -E remove *.xml *.yml *.xml2
    TEST_1
      CMND ${PERL_EXECUTABLE}
      ARGS
        ${VERAIn_SOURCE_DIR}/scripts/react2xml.pl --xInit
        ../${FILE_NAME}.inp  ${FILE_NAME}.xml
    TEST_2
      CMND diff ARGS ${FILE_NAME}.xml ../${FILE_NAME}.xml.gold
    TEST_3
      CMND ${XMLTHEXP_EXE}
      ARGS
       -3d ${FILE_NAME}.xml
    TEST_4
      CMND diff ARGS ../${FILE_NAME}.xml2.gold ${FILE_NAME}.xml2
    )
ENDFUNCTION()

#
# Run the thermal expansion test cases
#
ADD_THERMAL_EXPANSION_TEST(Sample_p6a)


#===========================================================
#
#               Test Latex file content
#
#===========================================================


SET(VERAIn_TEST_DIR ${${PACKAGE_NAME}_SOURCE_DIR})
#file(COPY yml2tex.py DESTINATION ${CMAKE_CURRENT_BINARY_DIR}/test/latex)

  TRIBITS_ADD_ADVANCED_TEST(testVERAInMan
    TEST_0
      CMND ${PYTHON_EXECUTABLE}
      ARGS ${VERAIn_TEST_DIR}/docs/Users_Manual/yml2tex.py ${VERAIn_TEST_DIR}/scripts/Templates/Directory.yml test.tex
      WORKING_DIRECTORY  ${CMAKE_CURRENT_BINARY_DIR}/latex
      SKIP_CLEAN_WORKING_DIRECTORY
      PASS_REGULAR_EXPRESSION_ALL
        "starting to build tex file"
      TIMEOUT 60
      OVERALL_NUM_TOTAL_CORES_USED 1
      CATEGORIES BASIC

  )

#===========================================================
#
#            Test automated excore generation
#
#===========================================================

FUNCTION(ADD_AUTO_EXCORE_TEST FILE_NAME)
  ASSERT_DEFINED(VERAIn_SOURCE_DIR)
  TRIBITS_COPY_FILES_TO_BINARY_DIR(ReactAware_CopyScriptFiles_${FILE_NAME}
    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}
    SOURCE_FILES
      ${FILE_NAME}.inp ${FILE_NAME}.xml.gold ${FILE_NAME}.omn.gold
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
    TEST_3
      CMND diff ARGS ${FILE_NAME}.omn ../${FILE_NAME}.omn.gold
    )
ENDFUNCTION()


#
# Run the automated excore test cases
#
ADD_AUTO_EXCORE_TEST(test_verashift_small_core_bioshield)
