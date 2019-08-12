#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#       NAME:           status.py                                       -
#       HISTORY:                                                        -
#               2019-04-04      leerw@ornl.gov                          -
#------------------------------------------------------------------------
from __future__ import print_function
#import argparse, getpass, logging, os, re
import argparse, getpass, logging, os, re, six, socket, sys
#import shutil, six, socket, subprocess, sys, time, traceback
from datetime import datetime
import pdb

import verarun.config
from .userdata import *


REGEX_JOB_ID = re.compile( r'^(\d+)(.*)$' )

REGEX_QSTAT_UNKNOWN_JOB = re.compile( r'qstat: Unknown Job[^\d]*([\d]+).*$' )

REGEX_WS = re.compile( r'[,\s]+' )


#------------------------------------------------------------------------
#       CLASS:          VeraStatus                                      -
#------------------------------------------------------------------------
class VeraStatus( object ):
  """
"""


#               -- Class Attributes
#               --

  DESCRIPTION = """Lists history of jobs submitted via 'verarun'."""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.__call__()                           -
  #----------------------------------------------------------------------
  def __call__( self, *args, **kwargs ):
    """
"""
    self.run( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.__init__()                           -
  #----------------------------------------------------------------------
  def __init__( self, **kwargs ):
    """
    Args:
        **kwargs (var args): parameters specified on the command line
            run_dir (str): optional run directory for filtering
            verbose (bool): True to provide more processing feedback
"""
    self._logger = logging.getLogger( 'root' )

    self._run_dir = kwargs.get( 'run_dir' )
    self._user_data = UserData()
    self._verbose = kwargs.get( 'verbose', False )
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.log()                                -
  #----------------------------------------------------------------------
  def log( self, *args, **kwargs ):
    """
"""
    is_log = self.logger.isEnabledFor( logging.INFO )
    if (is_log or self._verbose):
        #args and isinstance( args[ 0 ], six.string_types ):
      msg = args[ 0 ].format( *args[ 1 : ], **kwargs )
      if is_log:
        self.logger.info( msg )
      if self._verbose:
        print( '[verarun] ' + msg, file = sys.stderr )
  #end log


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.run()                                -
  #----------------------------------------------------------------------
  def run( self, *args, **kwargs ):
    """
"""
    filter_func = None
    if self._run_dir:
      filter_func = lambda x: self._run_dir == x.get( 'run_dir' )

    jobs = self._user_data.get_job_history( filter_func )
    self.write( jobs )
  #end run


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.write()                               -
  #----------------------------------------------------------------------
  def write( self, jobs, fp = sys.stdout ):
    """
Job id            Name             User              Time Use S Queue
----------------  ---------------- ----------------  -------- - -----
4613120.service2  beeler_lammps    beelbw            06:34:56 R general
4613121.service2  beeler_lammps    beelbw            05:45:37 R general
2019-12-31T23:59:59
Depend
"""
#               -- Prolog
#               --
#   print( 'Host:', socket.gethostname() )
#   print( 'User:', getpass.getuser() )
    print(
        'VERA job status: ' +
        '{0}@{1}'.format( getpass.getuser(), socket.gethostname() ) +
        os.linesep
        )

#               -- Find longest ID
#               --
    #name_len = max( [ len( x.get( 'job_name' ) ) for x in jobs ] + [ 16 ] )
    depend_len = \
        max( [ len( x.depend_job_id_str ) for x in jobs ] + [ 6 ] )
    name_len = max( [ len( x.job_id_str ) for x in jobs ] + [ 6 ] )
    fmt = '{job_id:<%ds} {depend_job:<%ds} {dtg:<19s} {run_dir:<32s}' % \
        ( name_len, depend_len )

    print( fmt.format(
        depend_job = 'Depend',
        dtg = 'Date/Time Submitted',
        job_id = 'Job ID',
        run_dir = 'Job Directory'
        ) )
    print( fmt.format(
        depend_job = '-' * depend_len,
        dtg = '-' * 19,
        job_id = '-' * name_len,
        run_dir = '-' * 32
        ) )

    #fmt = fmt.replace( 's', 'd', 2 )
    #print( os.linesep.join( [ fmt.format( **j ) for j in jobs ] ) )
    for j in jobs:
      print( fmt.format(
          depend_job = j.depend_job_id_str,
          dtg = j.dtg,
          job_id = j.job_id_str,
          run_dir = j.run_dir
          ) )
  #end write


#               -- Properties
#               --

  verbose = property( lambda x: x._verbose )
  """Flags more processing feedback"""


#               -- Static Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.get_depend_job_id()                  -
  #----------------------------------------------------------------------
  @staticmethod
  def get_depend_job_id( job ):
    """
    Args:
        job (dict): job dict with optional 'depend_job' key
    Returns:
        int: job id or 0 if none
"""
  #end get_depend_job_id


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.main()                               -
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
#               -- Parse command line
#               --
      parser = argparse.ArgumentParser(
          add_help = False,
          description = VeraStatus.DESCRIPTION,
          epilog = 'Version ' + verarun.config.__version__,
          prog = 'verastat'
          )

      #pgroup = parser.add_mutually_exclusive_group()
      parser.add_argument(
          '--verbose',
          action = 'store_true',
          help = 'turn on verbose messaging'
          )

#               -- Parse for basic args
#               --
      #parser.set_defaults( vera_installs_dir = None )
      args = parser.parse_args()

      kwargs = {}
      for name in dir( args ):
        if not name.startswith( '_' ):
          val = getattr( args, name )
          if val:
            kwargs[ name ] = val
      #end for name in dir( args )

      VeraStatus( **kwargs )()

    except AssertionError as ex:
      logging.exception( ex )
      print( '[verarun] ' + str( ex ), file = sys.stderr )

    except Exception as ex:
      #msg = str( ex )
      logging.exception( ex )
      #traceback.print_exc( file = sys.stderr )
      print( '[verarun] ' + str( ex ), file = sys.stderr )
  #end main

#end VeraStatus


#------------------------------------------------------------------------
#       NAME:           main()                                          -
#------------------------------------------------------------------------
if __name__ == '__main__':
  VeraStatus.main()
