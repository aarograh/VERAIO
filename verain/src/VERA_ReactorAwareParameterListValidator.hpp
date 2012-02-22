#ifndef VERA_REACTOR_AWARE_PARAMETER_LIST_VALIDATOR_HPP
#define VERA_REACTOR_AWARE_PARAMETER_LIST_VALIDATOR_HPP


#include "Teuchos_ParameterList.hpp"


namespace VERA {


/** \brief . */
class ReactorAwareParameterListValidator {
public:

  /** \brief . */
  bool validateReactorAwarePL(const Teuchos::ParameterList &reactorAwarePL) const;

};


} // namespace VERA


#endif // VERA_REACTOR_AWARE_PARAMETER_LIST_VALIDATOR_HPP
