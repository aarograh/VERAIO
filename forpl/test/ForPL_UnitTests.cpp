

#include "Teuchos_UnitTestHarness.hpp"


extern "C" {


#define TEST_FORPL_SET_GET_INT_F77 \
  F77_FUNC_(test_forpl_set_get_int, TEST_FORPL_SET_GET_INT)

void TEST_FORPL_SET_GET_INT_F77(const bool &verbose, int & result_flag_out);


} // extern "C" 


namespace {


TEUCHOS_UNIT_TEST( ForPL, SetGetInt )
{
  typedef Teuchos::UnitTestRepository UTR;
  ECHO(int result = -1);
  ECHO(TEST_FORPL_SET_GET_INT_F77(UTR::verboseUnitTests(), result));
  TEST_EQUALITY_CONST(result, 0);
}


} // namespace
