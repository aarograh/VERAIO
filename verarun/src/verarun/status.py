#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#       NAME:           status.py                                       -
#       HISTORY:                                                        -
#               2020-04-16      leerw@ornl.gov                          -
#         Adding jobid param, -p/--path, and -c/--clear.
#               2020-03-03      leerw@ornl.gov                          -
#         Accounting for job IDs as int and str.
#               2019-04-04      leerw@ornl.gov                          -
#------------------------------------------------------------------------
from __future__ import print_function
import argparse, getpass, logging, os, re, six, socket, subprocess, sys
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
  #def __call__( self, *args, **kwargs ):
  def __call__( self ):
    """
"""
    return  self.run()
  #end __call__


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.__init__()                           -
  #----------------------------------------------------------------------
  def __init__( self, **kwargs ):
    """
    Args:
        is_clear (boolean): clear job history
        is_full (boolean): show job details if available
        is_path (boolean): show only the job path
        job_id (int): id of job to display
        last_count (int): count of last jobs to show
"""
    self._logger = logging.getLogger( 'root' )

    self._is_clear = kwargs.get( 'is_clear' )
    self._is_full = kwargs.get( 'is_full' )
    self._is_path = kwargs.get( 'is_path' )
    self._job_id = kwargs.get( 'job_id', -1 )
    self._last_count = kwargs.get( 'last_count', -1 )
    #self._run_dir = kwargs.get( 'run_dir' )
    #self._verbose = kwargs.get( 'verbose', False )

    self._user_data = UserData()
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.exec_job_status_command()            -
  #----------------------------------------------------------------------
  def exec_job_status_command( self, job_id_str ):
    """
    Args:
        job_id_str (str):
    Returns:
        int: exit status
            0: okay
            1: job status is no longer available
            2: neither scontrol nor qstat were found
"""
#               -- Try SLURM first
#               --
    status = 0

    output = ''
    not_found = 0
    return_code = 0

    cmd = [ 'scontrol', 'show', 'job', job_id_str ]
    try:
      output = subprocess.check_output( cmd, stderr = subprocess.STDOUT )
    except subprocess.CalledProcessError as ex:
      output = ex.output
      return_code = ex.returncode
    except:
      not_found += 1
      return_code = -999

#               -- Then Torque
#               --
    if return_code != 0:
      cmd = [ 'qstat', '-f' , job_id_str ]
      try:
        output = subprocess.check_output( cmd, stderr = subprocess.STDOUT )
        return_code = 0
      except subprocess.CalledProcessError as ex:
        output = ex.output
        return_code = ex.returncode
      except:
        not_found += 1
        return_code = -999

    if not_found >= 2:
      print( 'Error: neither scontrol nor qstat were found', file = sys.stderr )
      status = 2

    else:
      if isinstance( output, bytes ):
        output = output.decode( 'utf-8' )

      if return_code == 0:
        print( output )
      else:
        print( output, file = sys.stderr )
        status = 1

    return  status
  #end exec_job_status_command


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.exec_job_status_command_python3()    -
  #----------------------------------------------------------------------
  def exec_job_status_command_python3( self, job_id_str ):
    """
    Args:
        job_id_str (str):
    Returns:
        int: exit status
            0: okay
            1: job status is no longer available
            2: neither scontrol nor qstat were found
"""
#               -- Try SLURM first
#               --
    status = 0
    proc = None
    cmd = [ 'scontrol', 'show', 'job', job_id_str ]
    try:
      proc = subprocess.run( cmd, capture_output = True, encoding = 'utf-8' )
    except:
      pass

#               -- Then Torque
#               --
    if proc is None or proc.returncode != 0:
      cmd = [ 'qstat', '-f' , job_id_str ]
      try:
        proc = subprocess.run( cmd, capture_output = True, encoding = 'utf-8' )
      except:
        pass

    if proc is None:
      print( 'Error: neither scontrol nor qstat were found', file = sys.stderr )
      status = 2

    elif proc.returncode == 0:
      print( proc.stdout )
      print( proc.stderr )

    else:
      print( 'job status for {0} has been lost'.format( job_id_str ) )
      status = 1

    return  status
  #end exec_job_status_command_python3


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
  #def run( self, *args, **kwargs ):
  def run( self ):
    """
    Returns:
        int: exit status
            0: okay
            1: job status is no longer available
            2: neither scontrol nor qstat were found
"""
    status = 0
#               -- Clear?
#               --
    if self._is_clear:
      self._user_data.clear_job_history()

    elif self._job_id < 0:
      jobs = self._user_data.get_job_history()
      if self._last_count > 0:
        jobs = jobs[ -self._last_count : ]
      self.write( jobs )

    else:
      jobs = self._user_data.get_job_history()
      job_id_str = str( self._job_id )
      cur_jobs = list( [ j for j in jobs if str( j.job_id ) == job_id_str ] )

      if not cur_jobs:
        print( 'Job {0:d} not found'.format( self._job_id ) )

      elif self._is_path:
        print( cur_jobs[ 0 ].run_dir )

      elif self._is_full:
        self.write( cur_jobs[ : 1 ] )
        print()
        status = self.exec_job_status_command( str( cur_jobs[ 0 ].job_id ) )

      else:
        self.write( cur_jobs[ : 1 ] )
    #end else: not if self._is_clear or self._job_id < 0

    return  status
  #end run


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.run_0()                              -
  #----------------------------------------------------------------------
  def run_0( self, *args, **kwargs ):
    """
"""
    filter_func = None
    if self._run_dir:
      filter_func = lambda x: self._run_dir == x.get( 'run_dir' )

    jobs = self._user_data.get_job_history( filter_func )
    self.write( jobs )
  #end run_0


  #----------------------------------------------------------------------
  #     METHOD:         VeraStatus.write()                               -
  #----------------------------------------------------------------------
  def write( self, jobs, fp = sys.stdout ):
    """
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
        max( [ len( x.depend_job_id ) for x in jobs ] + [ 6 ] )
    name_len = max( [ len( str( x.job_id ) ) for x in jobs ] + [ 6 ] )
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

    for j in jobs:
      print( fmt.format(
          depend_job = str( j.depend_job_id ),
          dtg = j.dtg,
          job_id = str( j.job_id ),
          run_dir = j.run_dir
          ) )
  #end write


#               -- Properties
#               --

# verbose = property( lambda x: x._verbose )
# """Flags more processing feedback"""


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

      parser.add_argument(
          'job_id',
          #default = [],
          help = 'job identifier',
          metavar = 'job_id',
          nargs = '?',
          type = int
          )
      parser.add_argument(
          '-h', '--help',
          action = 'store_true',
          dest = 'is_help'
          )

      flag_group = parser.add_mutually_exclusive_group()
      flag_group.add_argument(
          '-c', '--clear', '--clear-job-history',
          action = 'store_true',
          dest = 'is_clear',
          help = 'clear all job history, all other arguments ignored'
          )

      flag_group.add_argument(
          '-f', '--full', '--show-full-status',
          action = 'store_true',
          dest = 'is_full',
          help = 'if job_id specified, show full job details if available'
          )

      flag_group.add_argument(
          '-l', '--last', '--show-latest-jobs',
          default = -1,
          dest = 'last_count',
          help = 'show only the last N jobs, ignored if job_id specified',
          metavar = 'N',
          type = int
          )

      flag_group.add_argument(
          '-p', '--path', '--show-job-path',
          action = 'store_true',
          dest = 'is_path',
          help = 'if job_id specified, print only the path to the job directory'
          )

#               -- Parse for basic args
#               --
      #parser.set_defaults( vera_installs_dir = None )
      args = parser.parse_args()
      if args.is_help:
        parser.print_help()

      else:
        kwargs = {}
        for name in dir( args ):
          if not name.startswith( '_' ):
            val = getattr( args, name )
            if val:
              kwargs[ name ] = val
        #end for name in dir( args )

        sys.exit( VeraStatus( **kwargs )() )
      #end else: not args.is_help

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
