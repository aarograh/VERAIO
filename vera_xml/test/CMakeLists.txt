INCLUDE(TribitsAddAdvancedTest)

SET(FD ${CMAKE_CURRENT_SOURCE_DIR})
TRIBITS_ADD_ADVANCED_TEST(TableDiff_SimplePass
  TEST_0 
    CMND ${FD}/tablediff.py 
    ARGS ${FD}/R1 ${FD}/G1 ${FD}/O1
)

TRIBITS_ADD_ADVANCED_TEST(TableDiff_OmitPass
  TEST_0 
    CMND ${FD}/tablediff.py 
    ARGS ${FD}/R2 ${FD}/G2 ${FD}/O2
)

TRIBITS_ADD_ADVANCED_TEST(TableDiff_FailingDifferenceOmit
  TEST_0 
    CMND ${FD}/tablediff.py 
    ARGS ${FD}/R2 ${FD}/G2 ${FD}/O2.f
    PASS_REGULAR_EXPRESSION_ALL 
      "Error 1.0 exceeds tolerance 0 on case 1 at field Field4"
      "Error 3.0 exceeds tolerance 0 on case 2 at field Field4"
      "End Result: TEST FAILED"
)

TRIBITS_ADD_ADVANCED_TEST(TableDiff_OmitPass
  TEST_0 
    CMND ${FD}/tablediff.py 
    ARGS ${FD}/R2 ${FD}/G2 ${FD}/O2
)

TRIBITS_ADD_ADVANCED_TEST(TableDiff_FailingOutput
  TEST_0 
    CMND ${FD}/tablediff.py 
    ARGS ${FD}/R1 ${FD}/G1 ${FD}/O1.f
    PASS_REGULAR_EXPRESSION_ALL 
      "Mis-match between reference and output on case 1 at field Field2"
      "Error 1.0 exceeds tolerance 0 on case 1 at field Field3"
      "Error converting tokens to floating point on case 2 at field Field3"
      "Error 2.0 exceeds tolerance 1 on case 2 at field Field4"
      "End Result: TEST FAILED"
)

TRIBITS_ADD_ADVANCED_TEST(TableDiff_FailingOutputMissingTokens
  TEST_0 
    CMND ${FD}/tablediff.py 
    ARGS ${FD}/R1 ${FD}/G1 ${FD}/O1.ff
    PASS_REGULAR_EXPRESSION_ALL 
      "Output missing fields/lines on line 2"
      "Error 1.0 exceeds tolerance 0 on case 2 at field Field3"
      "End Result: TEST FAILED"
)

TRIBITS_ADD_ADVANCED_TEST(TableDiff_FailingOutputMissingLines
  TEST_0 
    CMND ${FD}/tablediff.py 
    ARGS ${FD}/R1 ${FD}/G1 ${FD}/O1.fff
    PASS_REGULAR_EXPRESSION_ALL 
      "Output missing fields/lines on line 2"
      "Output missing fields/lines on line 3"
      "End Result: TEST FAILED"
)

TRIBITS_ADD_ADVANCED_TEST(TableDiff_FailRulesHeader
  TEST_0 
    CMND ${FD}/tablediff.py 
    ARGS ${FD}/R1.fff ${FD}/G1 ${FD}/O1
    PASS_REGULAR_EXPRESSION_ALL 
          "End Result: TEST FAILED" 
          "Rule file missing header line"
)

TRIBITS_ADD_ADVANCED_TEST(TableDiff_FailRulesHeader
  TEST_0 
    CMND ${FD}/tablediff.py 
    ARGS ${FD}/R1.ff ${FD}/G1 ${FD}/O1
    PASS_REGULAR_EXPRESSION_ALL 
          "End Result: TEST FAILED" 
          "Rule file missing rules"
)

TRIBITS_ADD_ADVANCED_TEST(TableDiff_FailRulesMismatch
  TEST_0 
    CMND ${FD}/tablediff.py 
    ARGS ${FD}/R1.f ${FD}/G1 ${FD}/O1
    PASS_REGULAR_EXPRESSION_ALL 
          "End Result: TEST FAILED" 
          "Number of rules does not match number of fields in rule file"
)

TRIBITS_ADD_ADVANCED_TEST(FilterCommentsWhitespace_Pass
  TEST_0 
    CMND ${FD}/filter_comments_whitespace.py 
    ARGS ${FD}/text1 ${FD}/text2
    PASS_REGULAR_EXPRESSION_ALL 
          "Files are the same"
)

TRIBITS_ADD_ADVANCED_TEST(FilterCommentsWhitespace_Fail
  TEST_0 
    CMND ${FD}/filter_comments_whitespace.py 
    ARGS ${FD}/text1 ${FD}/text3
    PASS_REGULAR_EXPRESSION_ALL 
          "--- 1,2 ----"
          "Hello World"
          " blah"
          "Files are NOT the same"
)
