# $Id$
#------------------------------------------------------------------------
#       NAME:           hostinfo.py                                     -
#       HISTORY:                                                        -
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
import logging, os, json, re, six, socket
from stat import ST_CTIME, ST_MTIME

import pdb


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
    self._nprocs = self.units * self.sockets * self.nodes
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
  mem = property( lambda self: self.get( 'mem', 16 ) )
  nodes = property( lambda self: self.get( 'nodes', 1 ) )
  nprocs = property( lambda self: self._nprocs )
  ppn = property( lambda self: self._ppn )
  sockets = property( lambda self: self.get( 'sockets', 1 ) )
  units = property( lambda self: self.get( 'units', 1 ) )

#end Specs


#------------------------------------------------------------------------
#       CLASS:          HostInfo                                        -
#------------------------------------------------------------------------
class HostInfo( object ):
  """
"""
#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.__init__()                             -
  #----------------------------------------------------------------------
  def __init__( self,
      hostname = None,
      host_config_file = None,
      vera_installs_dir = None
      ):
    """
    Args:
        hostname (str): optional override hostname, defaulting to local hostname
        host_config_file (str): path to override host config file
        vera_installs_dir (str): optional override path to 'vera_installs' dir
"""
#               -- Read host configuration JSON file
#               --
    self._hostname = None
    self._missing_files = {}

    if host_config_file:
      fpath = host_config_file
      assert os.path.exists( fpath ), \
          'Configuration file not found: "{0}"'.format( host_config_file )
    else:
      self._hostname = hostname  if hostname else  socket.gethostname()
      fpath = os.path.\
          join( os.path.dirname( __file__ ), self._hostname + '.json' )
      assert os.path.exists( fpath ), \
          'Configuration not found for host {0}'.format( self._hostname )

    #self._env_script = re.sub( r'\.json$', '.sh', fpath )

    json_obj = {}
    with open( fpath, 'rt' ) as fp:
      json_obj = json.load( fp )

    if not self._hostname:
      self._hostname = json_obj.get( 'hostname', socket.gethostname() )

#               -- vera_installs_dir
#               --
    #self._vera_installs_dir, envs, self._specs = self._read( json_obj )
    self._vera_installs_dir = \
        vera_installs_dir  if vera_installs_dir else \
        json_obj.get( 'VeraInstallsDir', '/' )

    assert os.path.isdir( self._vera_installs_dir ), \
        'VERA installs dir not found: ' + self._vera_installs_dir

#               -- vera_default_version
#               --
    self._vera_default_version = os.environ.\
        get( 'VERA_DEFAULT_VERSION', json_obj.get( 'VeraDefaultVersion' ) )
    if self._vera_default_version:
      vera_def_path = os.path.\
          join( self._vera_installs_dir, self._vera_default_version )
      assert os.path.isdir( vera_def_path ), \
          'Specified VERA default version not found: ' + vera_def_path

#               -- domain, pbs_env, specs
#               --
    #self._setenv = os.linesep.join( json_obj.get( 'env', [] ) )
    self._domain = json_obj.get( 'domain', '' )
    if not self._domain:
      self._domain = self.infer_domain()
    self._env = os.linesep.join( json_obj.get( 'env', [] ) )
    self._email_env = os.linesep.join( json_obj.get( 'email_env', [] ) )
    self._pbs_env = os.linesep.join( json_obj.get( 'pbs_env', [] ) )
    self._pmem_env = os.linesep.join( json_obj.get( 'pmem_env', [] ) )
    self._specs = Specs( json_obj.get( 'specs', {} ) )

#               -- Get VERA install dirs in descending date order
#               --
    self._vera_dirs = []
    entries = [
        ( fn, os.path.join( self._vera_installs_dir, fn ) )
        for fn in os.listdir( self._vera_installs_dir )
        #if fn.lower().find( 'vera' ) >= 0
        ]
    valid_entries = [
        ( fn, os.stat( fpath ) )
        for fn, fpath in entries
        if os.path.isdir( fpath ) and self.is_valid_vera_dir( fpath )
        ]

    valid_entries.sort( key = lambda x: x[ 1 ][ ST_CTIME ], reverse = True )
    assert valid_entries, \
        'No VERA installations found in ' + self._vera_installs_dir
    self._vera_dirs = [ x[ 0 ] for x in valid_entries ]

#       -- Method aliases
#       --
    self.get_latest_vera_version = self.get_working_vera_version
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.create_vera_path()                     -
  #----------------------------------------------------------------------
  def create_vera_path( self, vera_version = None ):
    """
    Args:
        vera_version (str): name of vera_version, or None for the latest
"""
    path = os.path.join(
        self._vera_installs_dir,
        vera_version  if vera_version else  self.get_working_vera_version()
        )
    return  path
  #end create_vera_path


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
#    return  self._vera_dirs[ 0 ]  if self._vera_dirs else  None
    return \
        self._vera_default_version  if self._vera_default_version else \
        self._vera_dirs[ 0 ]  if self._vera_dirs else \
        None
  #end get_working_vera_version


  #----------------------------------------------------------------------
  #     METHOD:         infer_domain()                                  -
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

    if not domain:
      domain = 'ornl.gov'

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
    missing_list = self._missing_files.get( subdir )
    if not missing_list:
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
#     valid &= os.path.isdir( d )
##    valid = reduce(
##        lambda x, y: x and y,
##        map( lambda d: os.path.isdir( d ), ( bin_dir, lib_dir, share_dir ) )
##        )

#               -- Check sample of executables
#               --
#   if valid:
#     for f in ( 'load_env.sh', ):
#       valid &= os.path.exists( os.path.join( vera_dir, f ) )
    for f in ( 'load_env.sh', ):
      valid &= check_file( vera_dir, f )

    for f in (
        'MPACT.exe', 'react2xml.pl',
        'ThermalExpandXML.exe', 'vera_to_shift', 'xml2ctf'
        ):
      valid &= check_file( bin_dir, f )
#     valid &= os.path.exists( os.path.join( bin_dir, f ) )

    return  valid
  #end is_valid_vera_dir


  #----------------------------------------------------------------------
  #     METHOD:         HostInfo.resolve_env()                          -
  #----------------------------------------------------------------------
  def resolve_env( self, email, pmem ):
    """
"""
    result = self._pbs_env
    if email:
      result += os.linesep + self._email_env.format( email_addrs = email )
    if pmem:
      result += os.linesep + self._pmem_env.format( pmem = pmem )

    result += os.linesep + os.linesep + self._env

    return  result
  #end resolve_env


#               -- Properties
#               --


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.env                                    -
  #----------------------------------------------------------------------
#  env = property( lambda self: self._env )
#  """Environment dict"""


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
  #     PROPERTY:       HostInfo.missing_files                          -
  #----------------------------------------------------------------------
  missing_files = property( lambda self: self._missing_files )
  """Dict of missing files by vera_installs_dir subdir"""


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
  #     PROPERTY:       HostInfo.setenv                                 -
  #----------------------------------------------------------------------
#  setenv = property( lambda self: self._setenv )
#  """Environment setup commands in a single string"""


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
  #     PROPERTY:       HostInfo.vera_versions                          -
  #----------------------------------------------------------------------
  vera_versions = property( get_vera_versions )
  """Most recent VERA install"""


  #----------------------------------------------------------------------
  #     PROPERTY:       HostInfo.working_vera_version                   -
  #----------------------------------------------------------------------
  working_vera_version = property( get_working_vera_version )
  """VERA install to use"""

#end HostInfo
