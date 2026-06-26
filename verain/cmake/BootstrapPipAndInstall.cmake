# BootstrapPipAndInstall.cmake
#
# Called via cmake -P with:
#   -D PYTHON_EXE=<path>
#   -D VERAIN_SOURCE_DIR=<path>
#
# 1. Ensures pip is available using ensurepip (no-op if pip already present).
# 2. Installs verain[dev] into the user site directory so pytest/black/pylint
#    are available for ctest regardless of whether cmake --install is run.

IF(NOT PYTHON_EXE)
  MESSAGE(FATAL_ERROR "PYTHON_EXE must be set.")
ENDIF()
IF(NOT VERAIN_SOURCE_DIR)
  MESSAGE(FATAL_ERROR "VERAIN_SOURCE_DIR must be set.")
ENDIF()

# Step 1: bootstrap pip via ensurepip (safe no-op if pip is already present)
EXECUTE_PROCESS(
  COMMAND "${PYTHON_EXE}" -m ensurepip --upgrade
  RESULT_VARIABLE _ensurepip_result
  OUTPUT_VARIABLE _ensurepip_output
  ERROR_VARIABLE  _ensurepip_error
)
IF(NOT _ensurepip_result EQUAL 0)
  MESSAGE(STATUS "ensurepip returned ${_ensurepip_result} (may already be bootstrapped): ${_ensurepip_error}")
ENDIF()

# Step 2: install verain[dev]
# --user avoids permission errors and "externally-managed-environment" errors
# on Python 3.11+ systems with a system Python.
# However, --user is disallowed inside virtual environments (spack, venv,
# conda, etc.) where site-packages are already writable.  Detect the case
# and omit --user when running inside a venv.
# --force-reinstall ensures the current source is always installed even when
# the version number hasn't changed (prevents stale cached installs in CI).
EXECUTE_PROCESS(
  COMMAND "${PYTHON_EXE}" -c
    "import sys; print('1' if sys.prefix != sys.base_prefix else '0')"
  OUTPUT_VARIABLE _in_venv
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
# Check for PYTHONNOUSERSITE (any non-empty value counts as "disabled")
set(_no_user_site OFF)
if(_in_venv STREQUAL "1")
  set(_no_user_site ON)
elseif(DEFINED ENV{PYTHONNOUSERSITE})
  if(NOT "$ENV{PYTHONNOUSERSITE}" STREQUAL "")
    set(_no_user_site ON)
  endif()
endif()

if(_no_user_site)
  set(_pip_user_flag "")
else()
  set(_pip_user_flag "--user")
endif()

EXECUTE_PROCESS(
  COMMAND "${PYTHON_EXE}" -m pip install ${_pip_user_flag} --force-reinstall "${VERAIN_SOURCE_DIR}[dev]"
  RESULT_VARIABLE _pip_result
  OUTPUT_VARIABLE _pip_output
  ERROR_VARIABLE  _pip_error
)
IF(NOT _pip_result EQUAL 0)
  MESSAGE(FATAL_ERROR "verain pip install failed (exit ${_pip_result}):\n${_pip_error}")
ELSE()
  MESSAGE(STATUS "verain pip install (with dev extras) succeeded.")
ENDIF()
