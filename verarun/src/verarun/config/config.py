# $Id$
#------------------------------------------------------------------------
#	NAME:		config.py					-
#	HISTORY:							-
#		2018-07-07	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, logging.config, os

IS_LOG_CONFIGURED = False

if not IS_LOG_CONFIGURED:
  USER_VERARUN_DIR = \
      os.path.join( os.environ.get( 'HOME', os.curdir ), '.verarun' )
  if not os.path.isdir( USER_VERARUN_DIR ):
    os.makedirs( USER_VERARUN_DIR )

  logging.config.fileConfig( os.path.join(
      os.path.dirname( os.path.abspath( __file__ ) ),
      'logging.conf'
      ) )
  IS_LOG_CONFIGURED = True
