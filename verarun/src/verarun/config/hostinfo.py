# $Id$
#------------------------------------------------------------------------
#       NAME:           hostinfo.py                                     -
#       HISTORY:                                                        -
#               2021-02-12      leerw@ornl.gov                          -
#         Added vera_prod_dirs property.
#               2020-11-10      leerw@ornl.gov                          -
#         Calling os.path.expandvars() when parsing vera_installs_dir
#               2020-09-06      leerw@ornl.gov                          -
#         Added HostInfo.mem_default_env property applied if pmem not
#         specified
#               2020-08-24      leerw@ornl.gov                          -
#         Added default_queue property.
#               2020-04-09      leerw@ornl.gov                          -
#         Converting assertions to exceptions.
#               2020-04-08      leerw@ornl.gov                          -
#         Resolving explicit vera_dir assignment, overrides everything.
#               2020-03-26      leerw@ornl.gov                          -
#         Modified create_vera_path() to handle unspecifed vera_dir.
#               2020-03-20      leerw@ornl.gov                          -
#         Added project_{default,env} and mpi_args properties.
#         Note for now only project_{arg,default} is used in other modules.
#               2020-03-05      leerw@ornl.gov                          -
#         PBS type now declared.
#               2019-10-06      leerw@ornl.gov                          -
#         Processing pmem as a float in resolve_env().
#               2019-03-27      leerw@ornl.gov                          -
#         Removed check for "vera" in a VERA installation directory name.
#         Renamed get_latest_vera_version() to more appropriate
#         get_working_vera_version().
#               2019-03-23      leerw@ornl.gov                          -
#         Cataloging missing files from each vera_installs_dir subdir.
#               2019-03-12      leerw@ornl.gov                          -
#         Added vera_default_version property, now returned by
#         get_latest_vera_version() if specified.
#               2019-01-25      leerw@ornl.gov                          -
#         Added "domain" and "pbs_env" properties,
#         removed "setenv" property.
#               2018-08-09      leerw@ornl.gov                          -
#         Reorganizing to have "VeraInstallsDir" a top level config
#         property with "env" as an array of commands.
#         Added setenv property.
#               2018-07-17      leerw@ornl.gov                          -
#               2018-07-17      leerw@ornl.gov                          -
#         Added host_config_file constructor param.
#               2018-07-13      leerw@ornl.gov                          -
#               2018-07-09      leerw@ornl.gov                          -
#------------------------------------------------------------------------
import logging, math, os, json, re, six, socket
from stat import ST_CTIME, ST_MTIME

import pdb


REGEX_COMMAS = re.compile( r',+' )


#------------------------------------------------------------------------
#       CLASS:          Specs                                           -
#------------------------------------------------------------------------
class Specs( dict ):
  """Total threads = nodes * sockets * units * hwthreads, where
sockets is sockets per node, units is units per socket,
hwthreads is cores per unit
"""
#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         __init__()                                      -
  #----------------------------------------------------------------------
  def __init__( self, values ):
    """
"""
    self.update( values )
    self._nprocs = self.nodes * self.units * self.sockets
    self._ppn = self.sockets * self.units
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         __str__()                                       -
  #----------------------------------------------------------------------
  def __str__( self ):
    """
"""
    fmt = \
        'nprocs={0:d},ppn={1:d},mem={2:d} ' + \
        '(nodes={3:d},sockets={4:d},units={5:d},hwthreads={6:d})'
    result = fmt.format(
        self.nprocs, self.ppn, self.mem,
        self.nodes, self.sockets, self.units, self.hwthreads
        )
    return  result
  #end __str__


#               -- Properties
#               --
  hwthreads = property( lambda self: self.get( 'hwthreads', 1 ) )
  """Threads per processor"""

  mem = property( lambda self: self.get( 'mem', 16 ) )
  """Per-node memory in GB"""

  nodes = property( lambda self: self.get( 'nodes', 1 ) )
  """Number of nodes"""

  nprocs = property( lambda self: self._nprocs )
  """Total number of processors = nodes * sockets * units"""

  ppn = property( lambda self: self._ppn )
  """Processors per node = sockets * units"""

  sockets = property( lambda self: self.get( 'sockets', 1 ) )
  """Sockets per node"""

  units = property( lambda self: self.get( 'units', 1 ) )
  """CPUs per socket"""

#end Specs


#------------------------------------------------------------------------
#       CLASS:          HostInfo                                        -
#------------------------------------------------------------------------
class HostInfo( object ):
  """
"""

  MSG_veraVersionInvalid = """
Error: VERA version is invalid:
  "{0}"
Check command-line arguments, environment, and host configuration
"""

  MSG_veraVersionNotInProdList = """
Error: VERA version is invalid or not in the production list:
  "{0}"
Check command-line arguments, environment, and host configuration
"""

  MSG_veraVersionNotSpecified = """Error: VERA directory not specified.
Check command-line arguments and host configuration.
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.__init__()                             -
  #----------------------------------------------------------------------
  def __init__( self,
      hostname = None,
      host_config_file = None,
      vera_installs_dir = None,
      vera_default_version = None
      ):
    """
    Args:
        hostname (str): optional override hostname, defaulting to local hostname
        host_config_file (str): path to override host config file
        vera_installs_dir (str): optional override path to 'vera_installs' dir
        vera_default_version (str): optional override to version default version
"""
#               -- Read host configuration JSON file
#               --
    self._hostname = None
    self._missing_files = {}

    if host_config_file:
      fpath = host_config_file
      if not os.path.exists( fpath ):
        raise Exception( 'Configuration file not found: "{0}"'.format( host_config_file ) )
    else:
      self._hostname = hostname  if hostname else  socket.gethostname()
      fpath = os.path.\
          join( os.path.dirname( __file__ ), self._hostname + '.json' )
      if not os.path.exists( fpath ):
        raise Exception( 'Configuration not found for host {0}'.format( self._hostname ) )

    #self._env_script = re.sub( r'\.json$', '.sh', fpath )

    json_obj = {}
    with open( fpath, 'rt' ) as fp:
      json_obj = json.load( fp )

    if not self._hostname:
      self._hostname = json_obj.get( 'hostname', socket.gethostname() )

#               -- vera_installs_dir
#               --
    #self._vera_installs_dir, envs, self._specs = self._read( json_obj )
    env_values = [
        os.environ.get( v )
        for v in ( 'VERA_BUILDS', 'VERA_BUILDS_DIR', 'VERA_INSTALLS_DIR' )
        ]
    env_values = list( filter( lambda v: v is not None, env_values ) )
    self._vera_installs_dir = os.path.expandvars(
        vera_installs_dir  if vera_installs_dir else \
        env_values[ 0 ]  if env_values else \
        json_obj.get( 'VeraInstallsDir', '/' )
        )

    if not os.path.isdir( self._vera_installs_dir ):
      raise Exception( 'VERA installs dir not found: ' + self._vera_installs_dir )

#               -- vera_default_version
#               --
    self._vera_default_version = \
        vera_default_version  if vera_default_version else \
        os.environ.get(
            'VERA_DEFAULT_VERSION',
            json_obj.get( 'VeraDefaultVersion' )
            )
    if self._vera_default_version:
      vera_def_path = os.path.\
          join( self._vera_installs_dir, self._vera_default_version )
      if not os.path.isdir( vera_def_path ):
        raise Exception( 'VERA version not found: ' + vera_def_path )

#               -- default_queue, domain, pbs_env, specs
#               --
    #self._account_default = json_obj.get( 'account_default', '' )
    #self._account_env = json_obj.get( 'account_env', '-A' )

    self._default_queue = json_obj.get( 'default_queue', 'batch' )
    self._domain = json_obj.get( 'domain', '' )
    if not self._domain:
      self._domain = self.infer_domain()

    self._env = os.linesep.join( json_obj.get( 'env', [] ) )
    self._email_env = os.linesep.join( json_obj.get( 'email_env', [] ) )
    self._mail_from = json_obj.get( 'mail_from', '' )
    self._mem_default_env = \
        os.linesep.join( json_obj.get( 'mem_default_env', [] ) )
    self._mpi_args = ' '.join( json_obj.get( 'mpi_args', [] ) )
    self._pbs = json_obj.get( 'pbs', 'Torque' )
    self._pbs_env = os.linesep.join( json_obj.get( 'pbs_env', [] ) )
    self._pmem_env = os.linesep.join( json_obj.get( 'pmem_env', [] ) )
    self._project_default = json_obj.get( 'project_default', '' )
    self._project_env = json_obj.get( 'project_env', '-A' )  # -P
    self._specs = Specs( json_obj.get( 'specs', {} ) )

#               -- Get VERA install dirs in descending date order
#               --
#   self._vera_dirs = []
#   entries = [
#       ( fn, os.path.join( self._vera_installs_dir, fn ) )
#       for fn in os.listdir( self._vera_installs_dir )
#       #if fn.lower().find( 'vera' ) >= 0
#       ]
#   valid_entries = [
#       ( fn, os.stat( fpath ) )
#       for fn, fpath in entries
#       if os.path.isdir( fpath ) and self.is_valid_vera_dir( fpath )
#       ]
#   valid_entries.sort( key = lambda x: x[ 1 ][ ST_CTIME ], reverse = True )
#   self._vera_dirs = [ x[ 0 ] for x in valid_entries ]
    self._vera_dirs = self.\
        check_valid_vera_versions( os.listdir( self._vera_installs_dir ), True )
#               -- Get VERA production install dirs
#               --
    self._vera_prod_dirs = None
    prods_env_value = os.environ.get( 'VERA_PROD_VERSIONS' )
    if prods_env_value:
      prod_dirs = REGEX_COMMAS.split( prods_env_value )
      self._vera_prod_dirs = self.check_valid_vera_versions( prod_dirs )

#               -- Method aliases
#               --
    self.get_latest_vera_version = self.get_working_vera_version
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.check_valid_vera_versions()            -
  #----------------------------------------------------------------------
  def check_valid_vera_versions( self, vera_dirs, sort_flag = False ):
    """
"""
    entries = [
        ( fn, os.path.join( self._vera_installs_dir, fn ) )
        for fn in vera_dirs
        ]
    valid_entries = [
        ( fn, os.stat( fpath ) )
        for fn, fpath in entries
        if os.path.isdir( fpath ) and self.is_valid_vera_dir( fpath )
        ]
    if sort_flag:
      valid_entries.sort( key = lambda x: x[ 1 ][ ST_CTIME ], reverse = True )

    results = [ x[ 0 ] for x in valid_entries ]
    return  results
  #end check_valid_vera_versions


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.check_working_vera_version()           -
  #----------------------------------------------------------------------
  def check_working_vera_version( self, allow_devs = False ):
    """Checks that the working VERA version is in the list of production
versions if specified.
    Args:
        allow_devs (bool): True to allow development or non-prod versions,
            False for prod only
    Returns:
        str: error message or None if no problem
"""
    error = None
    vera_version = self.get_working_vera_version()

    if not vera_version:
      error = HostInfo.MSG_veraVersionNotSpecified

    elif not (
        allow_devs or self._vera_prod_dirs is None or
        (vera_version in self._vera_prod_dirs)
        ):
#   elif not allow_devs and self._vera_prod_dirs is not None and \
#       (not vera_version in self._vera_prod_dirs):
      error = HostInfo.MSG_veraVersionNotInProdList.format( vera_version )

    elif self._vera_dirs and not (vera_version in self._vera_dirs):
      error = HostInfo.MSG_veraVersionInvalid.format( vera_version )

    return  error
  #end check_working_vera_version


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.create_vera_path()                     -
  #----------------------------------------------------------------------
  def create_vera_path( self, vera_version = None ):
    """
    Args:
        vera_version (str): name of vera_version, or None for the latest
"""
#   path = os.path.join(
#       self._vera_installs_dir,
#       vera_version  if vera_version else  self.get_working_vera_version()
#       )
    path = None
    cur_version = \
        vera_version if vera_version  else self.get_working_vera_version()
    if self._vera_installs_dir and cur_version:
      path = os.path.join( self._vera_installs_dir, cur_version )

    return  path
  #end create_vera_path


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.get_available_vera_versions()          -
  #----------------------------------------------------------------------
  def get_available_vera_versions( self, allow_devs = False ):
    """
    Args:
        allow_devs (bool): True to allow development or non-prod versions,
            False for prod only
"""
    #return  self._vera_prod_dirs if self._vera_prod_dirs  else self._vera_dirs
    return \
        self._vera_prod_dirs  if not allow_devs and self._vera_prod_dirs else \
        self._vera_dirs
  #end get_available_vera_versions


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.get_vera_prod_versions()               -
  #----------------------------------------------------------------------
  def get_vera_prod_versions( self ):
    """
"""
    return  self._vera_prod_dirs
  #end get_vera_prod_versions


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.get_vera_versions()                    -
  #----------------------------------------------------------------------
  def get_vera_versions( self ):
    """
"""
    return  self._vera_dirs
  #end get_vera_versions


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.get_working_vera_version()             -
  #----------------------------------------------------------------------
  def get_working_vera_version( self ):
    """Overridden by ``vera_default_version`` if that is specified
"""
    return \
        self._vera_default_version  if self._vera_default_version else \
        self._vera_prod_dirs[ -1 ]  if self._vera_prod_dirs else \
        self._vera_dirs[ 0 ]  if self._vera_dirs else \
        None
  #end get_working_vera_version


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.infer_domain()                         -
  #----------------------------------------------------------------------
  def infer_domain( self ):
    """
    Returns:
        str: domain name as determined from ``socket.getfqdn()`` and
            ``socket.gethostname()``.
"""
    domain = socket.getfqdn()
    host = socket.gethostname()
    ndx = domain.find( host )
    if ndx == 0:
      domain = domain[ ndx + len( host ) + 1 : ]

#   if not domain:
#     domain = 'ornl.gov'

    return  domain
  #end infer_domain


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.is_valid_vera_dir()                    -
  #----------------------------------------------------------------------
  def is_valid_vera_dir( self, vera_dir ):
    """Looks for bin/, lib/, and share/ subdirs.
    Args:
        vera_dir (str): Path to VERA installation directory
    Returns:
        boolean: True if `vera_dir` is a VERA directory, False otherwise
"""
    subdir = os.path.basename( vera_dir )
#   missing_list = self._missing_files.get( subdir )
#   if not missing_list:
#     missing_list = []
#     self._missing_files[ subdir ] = missing_list
    missing_list = []
    self._missing_files[ subdir ] = missing_list

    def check_dir( d ):
      ok = os.path.isdir( d )
      if not ok: missing_list.append( os.path.basename( d ) + os.sep )
      return  ok
    #end check_dir

    def check_file( d, f ):
      ok = os.path.exists( os.path.join( d, f ) )
      if not ok: missing_list.append( f )
      return  ok
    #end check_file

    bin_dir = os.path.join( vera_dir, 'bin' )
    lib_dir = os.path.join( vera_dir, 'lib' )
    share_dir = os.path.join( vera_dir, 'share', 'data' )

#               -- Subdirs must exist
#               --
    valid = True
    for d in ( bin_dir, lib_dir, share_dir ):
     valid &= check_dir( d )

#               -- Check sample of executables
#               --
    for f in ( 'load_env.sh', ):
      valid &= check_file( vera_dir, f )

    for f in (
        'MPACT.exe', 'react2xml.pl',
        'ThermalExpandXML.exe', 'vera_to_shift', 'xml2ctf'
        ):
      valid &= check_file( bin_dir, f )

    return  valid
  #end is_valid_vera_dir


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.resolve_env()                          -
  #----------------------------------------------------------------------
  def resolve_env( self, email, pmem, project ):
    """
    Args:
        email (str): email addresses string (comma-delimited)
        pmem (float): required per-process memory in GB
        project (str): optional project override, where "none" means override
            any default
"""
    result = self._pbs_env

#               -- Project
    cur_project = self._project_default
    if project:
      cur_project = '' if project.lower() == 'none'  else project

    if cur_project and self._project_env:
      result += os.linesep + self._project_env.format( project = cur_project )

#               -- Email
    if email:
      result += os.linesep + self._email_env.format( email_addrs = email )

#               -- Per-process memory
    if pmem:
      pmem_str = self.to_pmem_str( pmem )
      result += os.linesep + self._pmem_env.format( pmem = pmem_str )
#               -- Or default memory
    elif self._mem_default_env:  # and self._specs.mem
      nmem_str = self.to_pmem_str( self._specs.mem )
      result += os.linesep + self._mem_default_env.format( nmem = nmem_str )

    result += os.linesep + os.linesep + self._env

    return  result
  #end resolve_env


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo._resolve_env_with_pbs()                -
  #----------------------------------------------------------------------
  def _resolve_env_with_pbs( self, email, pmem, project, proj_env_func = None ):
    """@deprecated
    Args:
        email (str): email addresses string (comma-delimited)
        pmem (float): required per-process memory in GB
        project (str): optional project override, where "none" means override
            any default
        proj_env_func (func): function( project(str) ) for creating a
            project env string
"""
    result = self._pbs_env

#               -- Project
    cur_project = self._project_default
    if project:
      cur_project = '' if project.lower() == 'none'  else project

    if cur_project and proj_env_func and \
        hasattr( proj_env_func, '__call__' ):
      result += os.linesep + proj_env_func( cur_project )

#               -- Email
    if email:
      result += os.linesep + self._email_env.format( email_addrs = email )
#               -- Process memory
    if pmem:
      pmem_str = self.to_pmem_str( pmem )
      result += os.linesep + self._pmem_env.format( pmem = pmem_str )

    result += os.linesep + os.linesep + self._env

    return  result
  #end _resolve_env_with_pbs


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.to_pmem_str()                          -
  #----------------------------------------------------------------------
  def to_pmem_str( self, pmem ):
    """
"""
    units = 'gb'
    f, i = math.modf( pmem )
    if f != 0.0:
      units = 'mb'
      pmem *= 1000.0
      if pmem < 1.0:
        units = 'kb'
        pmem *= 1000.0

    return  '{0:d}{1}'.format( int( math.floor( pmem ) ), units )
  #end to_pmem_str


#               -- Properties
#               --


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.account_default                        -
  #----------------------------------------------------------------------
# account_default = property( lambda self: self._account_default )
# """Optional default account for jobs"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.account_env                            -
  #----------------------------------------------------------------------
# account_env = property( lambda self: self._account_env )
# """PBS directive to specify the job account"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.default_queue                          -
  #----------------------------------------------------------------------
  default_queue = property( lambda self: self._default_queue )
  """Default domain/partition"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.domain                                 -
  #----------------------------------------------------------------------
  domain = property( lambda self: self._domain )
  """Network domain name"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.email_env                              -
  #----------------------------------------------------------------------
  email_env = property( lambda self: self._email_env )
  """PBS directives and environment in a single string"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.env                                    -
  #----------------------------------------------------------------------
  env = property( lambda self: self._env )
  """PBS directives and environment in a single string"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.hostname                               -
  #----------------------------------------------------------------------
  hostname = property( lambda self: self._hostname )
  """Host name as reported by `hostname`"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.latest_vera_version                    -
  #----------------------------------------------------------------------
# latest_vera_version = property( get_latest_vera_version )
# """Most recent VERA install"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.mail_from                              -
  #----------------------------------------------------------------------
  mail_from = property( lambda self: self._mail_from )
  """Optional from address for summary and other job emails"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.mem_default_env                        -
  #----------------------------------------------------------------------
  mem_default_env = property( lambda self: self._mem_default_env )
  """PBS directives and environment in a single string for default memory"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.missing_files                          -
  #----------------------------------------------------------------------
  missing_files = property( lambda self: self._missing_files )
  """Dict of missing files by vera_installs_dir subdir"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.mpi_args                               -
  #----------------------------------------------------------------------
  mpi_args = property( lambda self: self._mpi_args )
  """Arguments to 'mpiexec' as a single string"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.pbs                                    -
  #----------------------------------------------------------------------
  pbs = property( lambda self: self._pbs )
  """PBS type ('Slurm', 'Torque')"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.pbs_env                                -
  #----------------------------------------------------------------------
  pbs_env = property( lambda self: self._pbs_env )
  """PBS directives and environment in a single string"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.pmem_env                               -
  #----------------------------------------------------------------------
  pmem_env = property( lambda self: self._pmem_env )
  """PBS directives and environment in a single string"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.project_default                        -
  #----------------------------------------------------------------------
  project_default = property( lambda self: self._project_default )
  """Optional default project for jobs"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.project_env                            -
  #----------------------------------------------------------------------
  project_env = property( lambda self: self._project_env )
  """PBS directive to specify the job project"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.specs                                  -
  #----------------------------------------------------------------------
  specs = property( lambda self: self._specs )
  """Specs instance"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.vera_default_version                   -
  #----------------------------------------------------------------------
  vera_default_version = property( lambda self: self._vera_default_version )
  """Default VERA version, if specified"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.vera_installs_dir                      -
  #----------------------------------------------------------------------
  vera_installs_dir = property( lambda self: self._vera_installs_dir )
  """Configured directory containing VERA installs"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.vera_prod_versions                     -
  #----------------------------------------------------------------------
  vera_prod_versions = property( get_vera_prod_versions )
  """List of paths to all production VERA versions"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.vera_versions                          -
  #----------------------------------------------------------------------
  vera_versions = property( get_vera_versions )
  """List of paths to all available VERA versions"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.working_vera_version                   -
  #----------------------------------------------------------------------
  working_vera_version = property( get_working_vera_version )
  """VERA install to use"""

#end HostInfo
