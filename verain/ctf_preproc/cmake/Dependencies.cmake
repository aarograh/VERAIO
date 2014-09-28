TRIBITS_PACKAGE_DEFINE_DEPENDENCIES(
  LIB_REQUIRED_PACKAGES  VERAIn_XML
     COBRA_TFUtils  COBRA_TFPreproc  COBRA_TFCore
     TeuchosParameterList  TeuchosComm
  )
# NOTE: Above we have to put in a required dependence on COBRA_TFCore because
# the COBRA_TF package currently will not even configure if COBRA_TF is not
# enabled.  I need to get with Bob S. and Kevin C. to figure out what the
# dependencies are supposed to be.

TRIBITS_ALLOW_MISSING_EXTERNAL_PACKAGES(
  COBRA_TFUtils COBRA_TFPreproc)
