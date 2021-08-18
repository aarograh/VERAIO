# $Id$
#------------------------------------------------------------------------
#       NAME:           verajob.py                                      -
#       HISTORY:                                                        -
#               2021-01-07      leerw@ornl.gov                          -
#         Added mail_from
#               2021-01-03      leerw@ornl.gov                          -
#         Passing head hostname to VeraJobParams.
#               2020-03-20      leerw@ornl.gov                          -
#         Added mpi_args.
#               2020-03-02      leerw@ornl.gov                          -
#         Passing PBS script extension.
#               2019-01-25      leerw@ornl.gov                          -
#         Replaced {setenv} with {pbs_env}, single job script template.
#               2018-08-09      leerw@ornl.gov                          -
#         Added setenv param.
#               2018-07-31      leerw@ornl.gov                          -
#               2018-07-12      leerw@ornl.gov                          -
#------------------------------------------------------------------------
import getpass, logging, math, os, json, six, sys
import pdb

#from verarun.config.hostinfo import *
#import verarun.config.sixmore
from verarun.config import sixmore


#------------------------------------------------------------------------
#       CLASS:          VeraJobParams                                   -
#------------------------------------------------------------------------
class VeraJobParams( dict ):
  """
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         VeraJobParams.__init__()                        -
  #----------------------------------------------------------------------
  def __init__( self,
      case, vera_path,
      #account = 'NSED',
      cores = 1,
      email_addrs = None,
      excore_filename = None,
      head_hostname = '',
      job_id_env = 'PBS_JOBID',
      job_name = 'VCS',
      job_name_env = 'PBS_JOBNAME',
      mail_from = '',
      mpi_args = '',
      nodes = 1,
      pbs_env = None,
      pmem = 4,
      ppn = 1,
      queue = 'batch',
      restart = None,
      run_ctf = False,
      run_mpact = False,
      run_multistate_cobra = False,
      run_shift = False,
      run_thermal_exp = False,
      run_verain = True,
      #setenv = None,
      walltime = 24.0,
      work_dir_env = 'PBS_O_WORKDIR'
      ):
    """
    Args:
        #account (str): account name, defaults to NSED
        case (str): case name, for which we expect a file with a
            '.inp' extension
        vera_path (str): path to VERA version installation (with '/bin/',
            '/lib', '/data', and other subdirs)
        cores (int): total cores needed for the job (MPI -np param),
            defaults to 1
        email_addrs (list or str): list or comma-delimited string with
            addresses, defaults to current userid'@ornl.gov'
        head_hostname (str): socket.gethostname() on head node
        job_name (str): job name or label, defaults to 'VCS'
        mail_from (str): job email from address
        mpi_args (str): optional arguments to 'mpiexec'
        nodes (int): cluster nodes required (PBS resource), defaults to 1
        pbs_env (str): PBS directrives and environment setup
        ppn (int): virtual processors per node (PBS resource), defaults to 1
        pmem (int): max memory for any process in GB (PBS resource),
            defaults to 4
        queue (str): queue name, defaults to 'batch'
        restart (str): One of 'overwrite', 'readwrite', or None
        run_ctf (bool): flags need to run xml2ctf
        run_thermal_exp (bool): flags need to run ThermalExpandXML
        run_mpact (bool): flags need to run MPACT
        run_multistate_cobra (bool): flags need to run multistate_cobra
        run_shift (bool): flags need to run Shift
        run_verain (bool): flags need to run react2xml.pl, defaults to True
        #setenv (str): commands to setup environment
        walltime (float): total runtime in hours, defaults to 24.0
        work_dir_env (str): name of work directory environment variable
"""
    if not email_addrs:
      email_addrs = getpass.getuser() + '@ornl.gov'
    elif isinstance( email_addrs, list ):
      email_addrs = ','.join( email_addrs )

    mailfrom = '-r {0}'.format( mail_from ) if mail_from  else ''

    wt_hrs, rem = divmod( float( walltime ), 1.0 )
    rem *= 60.0
    rem, wt_min = math.modf( rem )
    wt_sec = int( rem * 60.0 )
    walltime_str = '{0:02d}:{1:02d}:{2:02d}'.\
        format( int( wt_hrs ), int( wt_min ), int( wt_sec ) )

    super( VeraJobParams, self ).__init__(
        #account = account,
        case = case,
        cores = int( cores ),
        email_addrs = email_addrs,
        excore_filename = '' if excore_filename is None else excore_filename,
        head_hostname = head_hostname,
        job_id_env = job_id_env,
        job_name = job_name,
        job_name_env = job_name_env,
        mailfrom = mailfrom,
        mpi_args = mpi_args,
        nodes = int( nodes ),
        pbs_env = '' if pbs_env is None else pbs_env,
        pmem = int( pmem ),
        ppn = int( ppn ),
        queue = queue,
        restart = '' if restart is None else restart,
        run_ctf = 'true' if run_ctf else '',
        run_mpact = 'true' if run_mpact else '',
        run_multistate_cobra = 'true' if run_multistate_cobra else '',
        run_shift = 'true' if run_shift else '',
        run_thermal_exp = 'true' if run_thermal_exp else '',
        run_verain = 'true' if run_verain else '',
        vera_path = vera_path,
        walltime = walltime_str,
        work_dir_env = work_dir_env
        )
  #end __init__


#               -- Properties
#               --

  #account = property( lambda self: self.get( 'account' ) )
  case = property( lambda self: self.get( 'case' ) )
  cores = property( lambda self: self.get( 'cores' ) )
  email_addrs = property( lambda self: self.get( 'email_addrs' ) )
  excore_filename = property( lambda self: self.get( 'excore_filename' ) )
  head_hostname = property( lambda self: self.get( 'head_hostname' ) )
  job_id_env = property( lambda self: self.get( 'job_id_env' ) )
  job_name = property( lambda self: self.get( 'job_name' ) )
  job_name_env = property( lambda self: self.get( 'job_name_env' ) )
  mailfrom = property( lambda self: self.get( 'mailfrom' ) )
  mpi_args = property( lambda self: self.get( 'mpi_args' ) )
  nodes = property( lambda self: self.get( 'nodes' ) )
  pbs_env = property( lambda self: self.get( 'pbs_env' ) )
  pmem = property( lambda self: self.get( 'pmem' ) )
  ppn = property( lambda self: self.get( 'ppn' ) )
  queue = property( lambda self: self.get( 'queue' ) )
  restart = property( lambda self: self.get( 'restart' ) )
  run_ctf = property( lambda self: self.get( 'run_ctf' ) )
  run_thermal_exp = property( lambda self: self.get( 'run_thermal_exp' ) )
  run_mpact = property( lambda self: self.get( 'run_mpact' ) )
  run_multistate_cobra = property( lambda self: self.get( 'run_multistate_cobra' ) )
  run_shift = property( lambda self: self.get( 'run_shift' ) )
  run_verain = property( lambda self: self.get( 'run_verain' ) )
  vera_path = property( lambda self: self.get( 'vera_path' ) )
  walltime = property( lambda self: self.get( 'walltime' ) )
  work_dir_env = property( lambda self: self.get( 'work_dir_env' ) )

#end VeraJobParams


#------------------------------------------------------------------------
#       CLASS:          VeraJobScript                                   -
#------------------------------------------------------------------------
class VeraJobScript( object ):
  """
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         VeraJobScript.__init__()                        -
  #----------------------------------------------------------------------
  #def __init__( self, hostname ):
  def __init__( self, script_ext = 'pbs' ):
    """
    Args:
        script_ext (str): script extension
"""
    self._logger = logging.getLogger( 'job' )
    self._script = None

    #fpath = os.path.join( os.path.dirname( __file__ ), 'vera.pbs' )
    fpath = os.path.join( os.path.dirname( __file__ ), 'vera.' + script_ext )

    with open( fpath, 'rt' ) as fp:
      self._script = fp.read()
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         VeraJobScript.create()                          -
  #----------------------------------------------------------------------
  def create( self, params ):
    """Two step process.  Apply pbs_env to get intermediate template.
    Args:
        params (VeraJobParams): job script template parameters
    Returns:
        str: PBS job script
"""
    pbs_env = params.get( 'pbs_env' )
    if pbs_env:
      del params[ 'pbs_env' ]
      params[ 'pbs_env' ] = pbs_env.format( **params )
    return  self._script.format( **params )
  #end create


  #----------------------------------------------------------------------
  #     METHOD:         VeraJobScript.write()                           -
  #----------------------------------------------------------------------
  def write( self, params, output = sys.stdout ):
    """
    Args:
        params (VeraJobParams): job script template parameters
        output (file or str): file or name of file to write
"""
    content = self.create( params )

    if sixmore.is_file( output ):
      output.write( content )
    else:
      with open( str( output ), 'wt' ) as fp:
        fp.write( content )
  #end write


#               -- Properties
#               --


  #----------------------------------------------------------------------
  #     PROPERTY:       VeraJobScript.logger                            -
  #----------------------------------------------------------------------
  logger = property( lambda self: self._logger )
  """Logger instance"""


  #----------------------------------------------------------------------
  #     PROPERTY:       VeraJobScript.script                            -
  #----------------------------------------------------------------------
  script = property( lambda self: self._script )
  """PBS script content"""

#end VeraJobScript
