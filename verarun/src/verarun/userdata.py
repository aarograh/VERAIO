#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#       NAME:           userdata.py                                     -
#       HISTORY:                                                        -
#               2019-04-04      leerw@ornl.gov                          -
#               2019-03-11      leerw@ornl.gov                          -
#------------------------------------------------------------------------
from __future__ import print_function
import json, logging, os, re, sys, time
import pdb


REGEX_JOB_ID = re.compile( r'^(\d+)(.*)$' )


#------------------------------------------------------------------------
#       CLASS:          JobInfo                                         -
#------------------------------------------------------------------------
class JobInfo( dict ):
  """
"""


  #----------------------------------------------------------------------
  #     METHOD:         JobInfo.__init__()                              -
  #----------------------------------------------------------------------
  #def __init__( self, job_name, job_id, dtg, run_dir, depend_job = None ):
  def __init__( self, **kwargs ):
    """
    Args:
        **kwargs (dict):
            job_name (str): job name
            job_id (int): job ID
            dtg (str): time of submission
            run_dir (str): run directory
            depend_job (str): optional name of dependent job
"""
    #super( dict, self ).__init__( **kwargs )
    if isinstance( kwargs, dict ):
      self.update( kwargs )

    if 'job_id' in self:
      self[ 'job_id' ] = int( self[ 'job_id' ] )
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         JobInfo.create_sort_key()                       -
  #----------------------------------------------------------------------
  def create_sort_key( self ):
    """
"""
    return  '{0}:{1}:{2}'.format( self.dtg, self.job_name, self.run_dir )
  #end create_sort_key


  #----------------------------------------------------------------------
  #     METHOD:         JobInfo.get_depend_job_id()                     -
  #----------------------------------------------------------------------
  def get_depend_job_id( self ):
    """
"""
    depend_id = -1
    depend_job = self.get( 'depend_job' )
    if depend_job:
      m = REGEX_JOB_ID.match( depend_job )
      if m:
        depend_id = int( m.group( 1 ) )

    return  depend_id
  #end get_depend_job_id


  #----------------------------------------------------------------------
  #     METHOD:         JobInfo.get_depend_job_id_str()                 -
  #----------------------------------------------------------------------
  def get_depend_job_id_str( self ):
    """
"""
    depend_id = self.get_depend_job_id()
    return  ('%d' % depend_id)  if depend_id >= 0  else ''
  #end get_depend_job_id_str


  #----------------------------------------------------------------------
  #     METHOD:         JobInfo.get_job_id_str()                        -
  #----------------------------------------------------------------------
  def get_job_id_str( self ):
    """
"""
    job_id = int( self.get( 'job_id', -1 ) )
    return  ('%d' % job_id)  if job_id >= 0  else ''
  #end get_job_id_str


  #----------------------------------------------------------------------
  #     METHOD:         JobInfo._set_depend_job()                       -
  #----------------------------------------------------------------------
  def _set_depend_job( self, value ):
    """
"""
    self[ 'depend_job' ] = value
  #end _set_depend_job


#               -- Properties
#               --

  depend_job = property( lambda x: x.get( 'depend_job', '' ), _set_depend_job )
  """Name of job for which this job depends"""

  depend_job_id = property( get_depend_job_id )
  """ID (int) of job for which this job depends"""

  depend_job_id_str = property( get_depend_job_id_str )
  """ID (str) of job for which this job depends"""

  dtg = property( lambda x: x.get( 'dtg', '' ) )
  """Start date/time"""

  job_id = property( lambda x: x.get( 'job_id', -1 ) )
  """Job ID int"""

  job_id_str = property( get_job_id_str )
  """Job ID str"""

  job_name = property( lambda x: x.get( 'job_name', '' ) )
  """Job name"""

  run_dir = property( lambda x: x.get( 'run_dir', '' ) )
  """Run directory"""

#end JobInfo


#------------------------------------------------------------------------
#       CLASS:          LockedFile                                      -
#------------------------------------------------------------------------
class LockedFile( object ):
  """
"""


  #----------------------------------------------------------------------
  #     METHOD:         LockedFile.__enter__()                          -
  #----------------------------------------------------------------------
  def __enter__( self ):
    """
"""
    lock_path = self._path + '.lock'
    while os.path.exists( lock_path ):
      time.sleep( 0.1 )
    open( lock_path, 'w' ).close()
    self._fp = open( self._path, self._mode )
    return  self._fp
  #end __enter__


  #----------------------------------------------------------------------
  #     METHOD:         LockedFile.__exit__()                           -
  #----------------------------------------------------------------------
  def __exit__( self, etype = None, evalue = None, tb = None ):
    """
"""
    self._fp.close()
    os.remove( self._path + '.lock' )
  #end __exit__


  #----------------------------------------------------------------------
  #     METHOD:         LockedFile.__init__()                           -
  #----------------------------------------------------------------------
  def __init__( self, path, mode ):
    """
"""
    self._mode = mode
    self._path = path
  #end __init__

#end LockedFile


#------------------------------------------------------------------------
#       CLASS:          UserData                                        -
#------------------------------------------------------------------------
class UserData( object ):
  """
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         UserData.__init__()                             -
  #----------------------------------------------------------------------
  def __init__( self, user_home = None ):
    """
"""
    if not user_home:
      user_home = os.environ.get( 'HOME', os.curdir )

    self._verarun_dir = os.path.join( user_home, '.verarun' )
    if not os.path.isdir( self._verarun_dir ):
      os.makedirs( self._verarun_dir )

    self._params_path = os.path.join( self._verarun_dir, 'params.json' )
    self._params = {}
    self._read()
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         append_job_history()                            -
  #----------------------------------------------------------------------
  def append_job_history( self, job_info ):
    """
    Args:
        job_info (dict or JobInfo): job properties
            depend_job (str): name of dependent job
            dtg (str): time of submission
            job_name (str): job_name
            job_id (int): job_id
            run_dir (str): run directory
"""
    if job_info and 'job_name' in job_info and 'job_id' in job_info and \
        'run_dir' in job_info and 'dtg' in job_info:
      history = self._params.get( 'job_history' )
      if history is None:
        history = []
        self._params[ 'job_history' ] = history

      if isinstance( job_info, JobInfo ):
        history.append( job_info )
      else:
        history.append( JobInfo( job_info ) )

      self._write()
  #end append_job_history


  #----------------------------------------------------------------------
  #     METHOD:         get_job_history()                               -
  #----------------------------------------------------------------------
  def get_job_history( self, filter_by = None ):
    """
    Args:
        filter_by (func): optional filtering function
    Returns:
        list(JobInfo): list of JobInfo records
"""
#   def create_key( item ):
#     return  item.get( 'dtg' ) + item.get( 'job_name' ) + item.get( 'run_dir' )

    items = self._params.get( 'job_history', [] )
    if items:
      if filter_by:
        items = filter( filter_by, items )
      items = sorted( items, key = lambda x: x.create_sort_key(), reverse = True )

    return  items
  #end get_job_history


  #----------------------------------------------------------------------
  #     METHOD:         get_last_job_name()                             -
  #----------------------------------------------------------------------
  def get_last_job_name( self ):
    """
"""
    return  self._params.get( 'last_job_name' )
  #end get_last_job_name


  #----------------------------------------------------------------------
  #     METHOD:         _read()                                         -
  #----------------------------------------------------------------------
  def _read( self ):
    """
"""
    if os.path.exists( self._params_path ):
      with LockedFile( self._params_path, 'r' ) as fp:
        self._params = json.load( fp )

      job_infos = self._params.get( 'job_history' )
      if job_infos:
        self._params[ 'job_history' ] = [ JobInfo( **x ) for x in job_infos ]
    #end if os.path.exists( self._params_path )
  #end _read


  #----------------------------------------------------------------------
  #     METHOD:         set_last_job_name()                             -
  #----------------------------------------------------------------------
  def set_last_job_name( self, value ):
    """
"""
    self._params[ 'last_job_name' ] = value
    self._write()
  #end set_last_job_name


  #----------------------------------------------------------------------
  #     METHOD:         _write()                                        -
  #----------------------------------------------------------------------
  def _write( self ):
    """
"""
    #with open( self._params_path, 'wt' ) as fp:
    with LockedFile( self._params_path, 'w' ) as fp:
      json.dump( self._params, fp, indent = 2 )
  #end _write


#               -- Properties
#               --

  job_history = property( get_job_history )
  """List of job history records"""

  last_job_name = property( get_last_job_name, set_last_job_name )
  """Last job name"""

#end UserData
