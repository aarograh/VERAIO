#include "VERA_ReactorAwareParameterListValidator.hpp"

#include "Teuchos_UnitTestHarness.hpp"


namespace VERA {


TEUCHOS_UNIT_TEST( ReactorAwareParameterListValidator, validate_1 )
{
  ReactorAwareParameterListValidator raplv;
  Teuchos::RCP<Teuchos::ParameterList> rapl; // ToDo: Read in test PL
  TEST_ASSERT(raplv.validateReactorAwarePL(*rapl));
}


} // namespace VERA
