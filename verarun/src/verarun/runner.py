#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#       NAME:           runner.py                                       -
#       HISTORY:                                                        -
#               2021-02-17      leerw@ornl.gov                          -
#         New thexp logic.
#               2021-02-12      leerw@ornl.gov                          -
#         New VERA_PROD_VERSIONS env variable and --dev flag.
#               2021-01-03      leerw@ornl.gov                          -
#         Passing head hostname to VeraJobParams.
#               2020-11-10      leerw@ornl.gov                          -
#         Appending input index to job name if one is specified with
#         -N and multiple input files are passed.
#               2020-09-06      leerw@ornl.gov                          -
#         Added HostInfo.mem_default_env property.
#               2020-08-24      leerw@ornl.gov                          -
#         Added -q/--partition/--queue
#               2020-04-09      leerw@ornl.gov                          -
#         Converting assertions to exceptions.
#               2020-04-08      leerw@ornl.gov                          -
#         Resolving explicit vera_dir assignment, overrides everything.
#         Added support for VERA_BUILDS|VERA_BUILDS_DIR|VERA_INSTALLS_DIR.
#               2020-03-26      leerw@ornl.gov                          -
#         Checking for missing vera_dir in main().
#               2020-03-20      leerw@ornl.gov                          -
#         New account, project, and mpi_args in HostInfo.
#               2020-03-05      leerw@ornl.gov                          -
#         PBS type declared in host config.
#               2020-03-03      leerw@ornl.gov                          -
#         Using PBSWrapper.
#               2019-10-23      leerw@ornl.gov                          -
#         Dumping job id on -O only.
#               2019-10-19      leerw@ornl.gov                          -
#         Dumping old name, dir, depend message on -O.
#               2019-10-17      leerw@ornl.gov                          -
#         At Andrew's request, echoing only the job id on -O.
#               2019-10-06      leerw@ornl.gov                          -
#         Allowing floating point pmem value.
#               2019-06-25      leerw@ornl.gov                          -
#         Added check for no extension on input_path parameter.
#         Changed email param (-e, --email-addrs) to be a comma-delmited
#         list of addresses instead of multiple arguments.
#               2019-04-22      leerw@ornl.gov                          -
#         Added resolve_vera_dir() and check for existence and validity
#         of the resolved VERA directory before executing.
#               2019-03-27      leerw@ornl.gov                          -
#         Added '-N' job_name param.
#               2019-03-15      leerw@ornl.gov                          -
#         Fixed bug in run() to store the last job only if not dry run
#         and a successful run.
#         Added -O.
#               2019-03-12      leerw@ornl.gov                          -
#               2019-03-11      leerw@ornl.gov                          -
#         Multiple input_path(s).
#               2019-03-07      leerw@ornl.gov                          -
#         Adding -d/--depend/--depend-jobid args.
#               2019-02-07      leerw@ornl.gov                          -
#         Allowing the input file to be pre-built XML file.
#               2019-02-06      leerw@ornl.gov                          -
#         Supporting SHIFT params for vera_to_shift.
#               2019-02-04      leerw@ornl.gov                          -
#         Added check for "nprocs" and "exe_mode", the latter to determine
#         run_multistate_cobra.
#               2019-01-25      leerw@ornl.gov                          -
#         New HostInfo.pbs_env property.
#               2018-12-13      leerw@ornl.gov                          -
#         Echoing VERARepoVersion.txt file if it exists.
#               2018-08-09      leerw@ornl.gov                          -
#         Added HostInfo.setenv property.
#               2018-07-31      leerw@ornl.gov                          -
#               2018-07-17      leerw@ornl.gov                          -
#         Added --host-config-file command-line argument.
#               2018-07-07      leerw@ornl.gov                          -
# stdout from qsub
# changes from falcon, panacea
#------------------------------------------------------------------------
from __future__ import print_function
#import argparse, getpass, logging, os, re
import argparse, logging, os, re
import shutil, six, socket, subprocess, sys, tempfile, time, traceback
from datetime import datetime

import verarun.config
from .config import config
from .config.hostinfo import *
#from verarun.job import *
from .job.verajob import *
from .pbs import create_instance
from .userdata import *
from .verain import *

import pdb


DEFAULT_SUBDIR = '_dtg_'

MESSAGE_NO_UPPER_EXT = '''File "{0}".
Upper case filename extensions are not supported.
Rename or copy the input file.'''

MESSAGE_UPPER_FNAME = '''File "{0}" not found.
"{1}" was found.  Rename or copy to file with "{2}" extension'''

REGEX_JOB_ID = re.compile( r'^(\d+)(.*)$' )
REGEX_WS = re.compile( r'[,\s]+' )


#class CustomArgsFormatter(
#    argparse.ArgumentDefaultsHelpFormatter,
#    argparse.RawDescriptionHelpFormatter
#    ):
#  pass


#------------------------------------------------------------------------
#       CLASS:          VeraRunner                                      -
#------------------------------------------------------------------------
class VeraRunner( object ):
  """
PBS operations
  command to execute:   qsub                    sbatch
  env:                  VERA_QSUB               ???
  dependency:           -W depend=afterok:{0}   --dependency=afterok:{0}
  command output:       NNNN.host.name          Submitted batch job NNNN
                        extract_job_id()
"""


#               -- Class Attributes
#               --

  DESCRIPTION = 'Creates and optionally submits machine-specific VERA jobs.'

  EPILOG = """
Verarun uses machine-specific characteristics to determine batch system
directives applied to a job script template.  Additional template parameters,
such as which models and utilities to execute, are determined from the VERA
input file (.inp).  Configurations are provided for machines commonly in the
VERA program.  In order to port 'verarun' to another environment it will be
necessary to create a machine spec file.

Execution
---------
There are two verarun usage modes:

* If the '-l' command-line argument is specified, available VERA installations
  are listed.  If '--verbose' is also specified, required files that are
  missing in each vera_installs_dir subdir are listed.

* If one or more VERA input files (.inp) are specified, a job script is created
  based on each input file.  Note pre-processed VERA input XML (.xml) may be
  also be specified.  If no file extension is given '.inp' is assumed.

By default the current directory will be used for all processing.
Alternatively, you may specify that a subdir in the current directory be
created and used as the working directory via the '-s' command-line argument.
Specifying a directory value of '.' will tell verarun to create a subdir with
name {input_name}_{datetime}, where {input_name] is the name of the input file
without the '.inp' or '.xml' extension, and {datetime} is the ISO 8601 extended
date format: yyyy-mm-ddThh:mm:ss.

A job script named with a '.pbs' extension is created in the working directory.
If the '-x' argument is not specified, the job is also submitted.  Output from
the job will be in a file with extension '.stdout' in the working directory.

Machine Specifications
----------------------
Machine specifications are stored in JSON ('.json') files under the verarun
Python package installation directory:

  ../lib/python2.7/site-packages/verarun-<version>-py2.7.egg/verarun/config/

It is also possible to specify a configuration file with the '-c' command-line
argument.

Job Script Template
-------------------
The Job template is a Bash script named 'vera.pbs' stored under the verarun
installation directory:

  ../lib/python2.7/site-packages/verarun-<version>-py2.7.egg/verarun/job/

Parameter values are substituted by name for curly-brace expressions in the
template (.e.g., {job_name}).

Environment Variables
---------------------
There are environment variables which can be set to override behavior.

* PBS_EMAIL: sets the email address to be used for PBS notifications,
  overridden by the '-e' (or '--email-addrs') parameter.

* PBS_PROJECT: sets the project for the job, overriding any default set in
  the host configuration but overridden by the '-p' (or '--project') parameter.

* VERA_BUILDS: path to the directory containing VERA builds or installs,
  overriding the "$(hostname).json" file but overridden by the
  '--vera-installs-dir' parameter.  May also be specified as
  VERA_BUILDS_DIR or VERA_INSTALLS_DIR.

* VERA_BUILDS_DIR: alternative name for VERA_BUILDS, where VERA_BUILDS has
  priority.

* VERA_DEFAULT_VERSION: names the default version of VERA to use, overriding
  what is specified in the host configuration file but overridden by the '-v'
  (or '--vera-version') parameter.

* VERA_INSTALLS_DIR: alternative name for VERA_BUILDS or VERA_BUILDS_DIR,
  priority order being VERA_BUILDS, VERA_BUILDS_DIR, then VERA_INSTALLS_DIR

* VERA_PROD_VERSIONS: comma-delimited list of allowed production VERA versions.

* VERA_QSUB: custom 'qsub' command to execute for hosts running Torque or
  PBS Pro.

* VERA_SBATCH: custom 'sbatch' command to execute for hosts running SLURM.

* VERARUN_HOST_CONFIG_FILE: path to a host configuration file to use,
  overriding the distributed "$(hostname).json" file but overridden by
  the '-c' parameter.
"""

  MSG_machineConfig = """Error: Machine configuration cannot support request:
  machine:   {0}
  requested: nprocs={1:d}, nodes={2:d}, pmem={3:f}
"""

  MSG_memoryWarning = """Warning: Requested memory and ppn exceed machine per-node memory:
  available:  mem={0:d} (per node)
  requested:  ppn={1:d}, pmem={2:f}
  changed to: ppn={3:d}
"""

  MSG_tooManyProcessors = """Error: Too many processors requested for this machine:
  available={0:d}, requested={1:d}
"""

  MSG_tooMuchMemory = """Error: Too much memory requested for nodes on this machine:
  available={0:d}, requested={1:f}
"""

  MSG_veraDirNotFound = """Error: VERA directory not found:
  "{0}"
Check command-line arguments and host configuration.
"""

  MSG_veraDirNotSpecified = """Error: VERA directory not specified.
Check command-line arguments and host configuration.
"""

  MSG_veraDirInvalid = """Error: Invalid VERA directory:
  "{0}"
Check command-line arguments and host configuration.
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.__call__()                           -
  #----------------------------------------------------------------------
  def __call__( self, *args, **kwargs ):
    """
"""
    self.run( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.__init__()                           -
  #----------------------------------------------------------------------
  def __init__( self, input_paths, **kwargs ):
    """
    Args:
        input_path (list(str)): paths to case input file
        **kwargs (var args): parameters specified on the command line

        chain_mode (bool): True to submit all jobs as a dependency chain
        dry_run (boolean): True to create script without submitting it
        email_addrs (list,str): List or comma-delimited string of addresses
        host_config_file (str): Path to override host configuration file
        hostname (str): Override hostname
        job_name (str): Optional explicit job name
        nprocs (int): Number of processors requested (defaults to 16)
        output_job_flag (bool): True to print to stdout the submitted
            job ids
        ppn (int): Number of processors per node, where None means to calculate
            it (defaults to None)
        proc_mem (int): Memory required per processor in GB (defaults to 16)
        queue (str): override for Torque queue or Slurm partition (defaults to None)
        restart (str): One of 'overwrite', 'readwrite', or None
        vera_dir (str): optional path to VERA installation, overrides `vera_installs_dir`
            and `vera_version` params
        vera_installs_dir (str): optional path to 'vera_installs' directory containing
            VERA versions
        vera_version (str): optional name of VERA version to use, where None means to
            use the latest available version
        verbose (bool): True to provide more processing feedback
        wait_job_id (str): optional ID of job to wait on before
            starting this job
        wait_last (bool): True to wait on the most recent job submitted via
            verarun
        walltime (float): wallclock execution time in hours
"""
    self._logger = logging.getLogger( 'root' )

#    self._cur_run_dir = None
    self._document = None

    self._chain_mode = kwargs.get( 'chain_mode', False )
    self._debug_mode = kwargs.get( 'debug', False )
    self._dry_run = kwargs.get( 'dry_run', False )
    #self._input_path = os.path.abspath( input_path )
    self._input_paths = [ os.path.abspath( i ) for i in input_paths ]
    self._job_name = kwargs.get( 'job_name' )
    self._output_job_flag = kwargs.get( 'output_job_flag', False )
#    self._job_id = -1
    self._subdir = kwargs.get( 'subdir' )
    self._user_data = UserData()
    self._verbose = kwargs.get( 'verbose', False )
    self._wait_job_id = kwargs.get( 'wait_job_id' )
    if kwargs.get( 'wait_last', False ):
      self._wait_job_id = 'last'

    for n in ( 'dry_run', 'subdir', 'verbose' ):
      if n in kwargs:  del kwargs[ n ]

    self._params = kwargs

    self._vera_dir = kwargs.get( 'vera_dir' )
    self._vera_installs_dir = kwargs.get( 'vera_installs_dir' )
    self._vera_version = kwargs.get( 'vera_version' )

    if self._vera_dir:
      self._vera_installs_dir = os.path.dirname( self._vera_dir )
      self._vera_version = os.path.basename( self._vera_dir )

    host_config_file = kwargs.get( 'host_config_file' )
    hostname = kwargs.get( 'hostname' )
    hi_args = dict(
        vera_installs_dir = self._vera_installs_dir,
        vera_default_version = self._vera_version
        )
    if host_config_file:
      hi_args[ 'host_config_file' ] = host_config_file
    else:
      hi_args[ 'hostname' ] = hostname
    self._hostinfo = HostInfo( **hi_args )
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner._extract_value()                     -
  #----------------------------------------------------------------------
  def _extract_value( self, expr, doc, def_ns = None, ns_dict = None ):
    """
"""
    value = None
    nodes = xpath.find(
        expr, doc,
        default_namespace = def_ns, namespaces = ns_dict
        )
    if nodes and nodes[ 0 ].nodeValue:
      values = nodes[ 0 ].nodeValue
    return  value
  #end _extract_value


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.log()                                -
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

#    if self.logger.isEnabledFor( logging.INFO ):
#      self.logger.info( msg )
#    if self._verbose:
#      print( '[verarun] ' + msg, file = sys.stderr )
  #end log


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner._read_input_doc()                    -
  #----------------------------------------------------------------------
  def _read_input_doc( self, input_path ):
    """
    Args:
        input_path (str): path to input ('.inp') or xml ('.xml') file;
            if the former ``react2xml.pl`` will be run to generate
            the XML file
    Returns:
        VeraInputXMLDoc: document instance
"""
    if input_path.endswith( '.xml' ):
      xml_output_file = input_path

    else:
      xml_output_file = re.sub( r'\.inp$', '.xml', input_path )
      if not( self._debug_mode and os.path.exists( xml_output_file ) ): 
        vera_dir = self.resolve_vera_dir()
        react2xml_path = os.path.join( vera_dir, 'bin', 'react2xml.pl' )
        self.log( 'creating "{0}"', xml_output_file )
        subprocess.check_call( [ react2xml_path, input_path ] )

    if not os.path.exists( xml_output_file ):
      raise Exception( 'XML file not found or not created: "{0}"'.format( xml_output_file ) )

    self.log( 'reading "{0}"', xml_output_file )
    return  VeraInputXMLDoc( xml_output_file )
  #end _read_input_doc


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.resolve_vera_dir()                   -
  #----------------------------------------------------------------------
  def resolve_vera_dir( self ):
    """Determine the working VERA installation/version directory from
properties
    Returns:
        str: path to directory
"""
    return \
        self._vera_dir  if self._vera_dir else \
        self._hostinfo.create_vera_path( self._vera_version )
  #end resolve_vera_dir


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner._resolve_params()                    -
  #----------------------------------------------------------------------
  def _resolve_params( self, doc, pbs, input_path, input_ndx, params ):
    """
    Args:
        doc (verain.VeraInputXMLDoc): document to consult
        pbs (pbs.PBS): pbs object
        input_path (str): required path to input file, either a VERAIn or
            VERA XML file
        input_ndx (int): 0-based input index/sequence
        params (dict): params specified on the command line, assumed not to
            be None
    Returns:
        verarun.job.VeraJobParams: job parameters instances
"""
    run_params = doc.find_run_params()
    #run_params.update( params )
    run_params.update({
        key: value
        for ( key, value ) in six.iteritems( params ) if value is not None
        })

    email = run_params.get( 'email' )
    if isinstance( email, list ):
      email = ','.join( email )
    if not email:
      email = os.environ.get( 'PBS_EMAIL' )
    #if not email:
      #email = getpass.getuser() + '@' + self._hostinfo.domain

    head_hostname = socket.gethostname()

    machine_nprocs = self._hostinfo.specs.nprocs
    mail_from = self._hostinfo.mail_from
    mpi_args = self._hostinfo.mpi_args
    nprocs = run_params.get( 'nprocs', machine_nprocs )
    pmem_str = run_params.get( 'pmem' )
    pmem = float( pmem_str )  if pmem_str else  None
    ppn = run_params.get( 'ppn' )

    project = run_params.get( 'project' )
    if not project:
      project = os.environ.get( 'PBS_PROJECT' )

    queue = run_params.get( 'queue', self._hostinfo.default_queue )
    restart = run_params.get( 'restart' )
    vera_version = run_params.get( 'vera_version' )
    walltime = run_params.get( 'walltime', 24.0 )

    ## if vera_shift, nprocs
    if nprocs > machine_nprocs:
      raise Exception( VeraRunner.MSG_tooManyProcessors.format( machine_nprocs, nprocs ) )

#               -- 1. Compute number of nodes based on specs
#               --
    if ppn:
      use_ppn = ppn
    else:
      use_ppn = self._hostinfo.specs.ppn

    nodes = (nprocs + use_ppn - 1) // use_ppn

#               -- 2. Rebalance - this appears to create a glitch on Lemhi?
#               --
#   if not ppn and nodes > 1:
#     use_ppn = (nprocs + nodes - 1) // nodes

#               -- 3. pmem
#               --
    if pmem:
#                       -- Check per-node memory required
      if pmem * use_ppn > self._hostinfo.specs.mem:
        new_ppn = int( self._hostinfo.specs.mem / pmem )
        print(
            VeraRunner.MSG_memoryWarning.format(
                self._hostinfo.specs.mem, use_ppn, pmem, new_ppn
                ),
            file = sys.stderr
            )
        use_ppn = new_ppn
        if use_ppn <= 0:
          raise Exception( VeraRunner.MSG_tooMuchMemory.format(
              self._hostinfo.specs.mem, pmem
              ) )
        nodes = (nprocs + use_ppn - 1) // use_ppn
    #end if pmem

    machine_nodes = self._hostinfo.specs.nodes
    if nodes > machine_nodes:
      raise Exception( VeraRunner.MSG_machineConfig.format(
          self._hostinfo.specs, nprocs, nodes, pmem
          ) )

#               -- Job params
#               --
    case_name, ext = os.path.splitext( os.path.basename( input_path ) )
    vera_path = \
        self._vera_dir  if self._vera_dir else \
        self._hostinfo.create_vera_path( self._vera_version )

#x  job_name = self._job_name  if self._job_name else  'VERA-' + case_name
    if self._job_name:
      job_name = self._job_name
      if len( self._input_paths ) > 1:
        job_name += '-{0:d}'.format( input_ndx )
    else:
      job_name = 'VERA-' + case_name

    feedback_values = doc.find_state_params( 'feedback' )
    run_ctf = feedback_values and 'on' in feedback_values
    run_mpact = True if doc.find_param_blocks( 'MPACT' ) else False

    run_multistate_cobra = run_params.get( 'exe_mode', '' ) == 'th'
    if run_multistate_cobra:
      run_mpact = False

    #excore_values = doc.find_state_params( 'excore_transport' )
    #run_shift = excore_values and 'on' in excore_values
    #run_shift = excore_values and excore_values[ 0 ] == 'on'
    excore_value = doc.find_single_state_param( 0, 'excore_transport' )
    run_shift = True if excore_value and excore_value == 'on'  else False

    excore_filename = doc.find_shift_param( 'excore_filename' )
    if excore_filename:
      if not excore_filename.endswith( '.excore.xml' ):
        excore_filename += '.excore.xml'
      #excore_omn_name = excore_filename[ : -11 ] + '.omn'

    #rt_values = doc.find_state_params( 'thexp' )
    #run_thermal_exp = rt_values and 'on' in rt_values and run_shift
    rt_value = doc.find_single_state_param( 0, 'thexp' )
    run_thermal_exp = \
        True if not( rt_value and rt_value == 'off' ) and run_shift \
        else False

    run_verain = not input_path.endswith( '.xml' )

#   pbs_env = self._hostinfo.resolve_env(
#       email, pmem, project,
#       pbs.create_project_directive
#       #lambda msg: print( '[verarun] ' + msg, file = sys.stderr )
#       )

    params = VeraJobParams(
        case_name, vera_path,
        #account = self._account,
        cores = nprocs,
        email_addrs = email,
        excore_filename = excore_filename,
        head_hostname = head_hostname,
        job_id_env = pbs.job_id_env,
        job_name = job_name,
        job_name_env = pbs.job_name_env,
        mail_from = mail_from,
        mpi_args = mpi_args,
        nodes = nodes,
        pbs_env = self._hostinfo.resolve_env( email, pmem, project ),
        ppn = use_ppn,
        queue = queue,
        restart = restart,
        run_ctf = run_ctf,
        run_mpact = run_mpact,
        run_multistate_cobra = run_multistate_cobra,
        run_shift = run_shift,
        run_thermal_exp = run_thermal_exp,
        run_verain = run_verain,
        walltime = walltime,
        work_dir_env = pbs.work_dir_env
        )
    return  params
  #end _resolve_params


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.run()                                -
  #----------------------------------------------------------------------
  def run( self, *args, **kwargs ):
    """
"""
#   def extract_job_id( name ):
#     ndx = name.find( '.' )
#     return  name if ndx < 0 else name[ 0 : ndx ]
#   #end extract_job_id

#               -- Get, assert on PBS
#               --
    #pbs = get_pbs( self.log )
    #assert pbs is not None, 'Error finding PBS (SLURM, Torque) commands'
    pbs_type = self._hostinfo.pbs
    try:
      pbs = create_instance( pbs_type, self.log )
    except:
      raise Exception( 'Error loading PBS "' + pbs_type + '"' )

    start_dt = datetime.now()
    start_str = start_dt.strftime( '%Y-%m-%dT%H:%M:%S' )
    if self.logger.isEnabledFor( logging.INFO ):
      self.logger.info( 'starting run at %s', start_str )

    last_mode = 'last' == self._wait_job_id
    wait_job_id = \
        self._user_data.last_job_id  if last_mode  else \
        self._wait_job_id  if self._wait_job_id  else \
        None

    submit_job_ids = []
    #submit_names = []

    input_ndx = 0
    for ipath in self._input_paths:
      job_info = self.run_case( pbs, ipath, input_ndx, wait_job_id )
      if job_info:
        #job_name = job_info.get( 'job_name' )
        #submit_names.append( job_name )
        job_id = job_info.job_id
        self._user_data.last_job_id = job_id
        submit_job_ids.append( job_id )

        if wait_job_id:
          job_info.depend_job_id = wait_job_id
        self._user_data.append_job_history( job_info )
        wait_job_id = job_id if self._chain_mode  else None
        #wait_job_id = job_id if last_mode or self._chain_mode  else None
      else:
        wait_job_id = None

      input_ndx += 1
    #end for ipath in self._input_paths

    if self._output_job_flag and not self._dry_run:
      print( ' '.join( submit_job_ids ) )

#Original
#   if self._output_job_flag and not self._dry_run:
#     print( os.linesep.join( submit_names ) )

#2nd intepretation
#   if not self._dry_run:
#     if self._output_job_flag:
#       print( os.linesep.join( submit_names ) )
#     else:
#       print( ' '.join( submit_job_ids ) )
  #end run


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.run_case()                           -
  #----------------------------------------------------------------------
  def run_case( self, pbs, input_path, input_ndx, wait_job_id ):
    """
    Args:
        pbs (PBSWrapper): PBS object
        input_path (str): required path to input file, either a VERAIn or
            VERA XML file
        input_ndx (int): 0-based input index/sequence
        wait_job_id (str): optional ID of job on which this case depends
    Returns:
        userdata.JobInfo: submitted job info or None if not submitted
"""
    start_dt = datetime.now()
    #start_str = start_dt.strftime( '%Y-%m-%dT%H:%M:%S' )
    start_str = start_dt.strftime( '%FT%T' )
    if self.logger.isEnabledFor( logging.INFO ):
      self.logger.info( 'running %s at %s', input_path, start_str )
    input_path_dir = os.path.abspath( os.path.dirname( input_path ) )
    input_path_base = os.path.basename( input_path )
    case_name, ext = os.path.splitext( input_path_base )

    pop_dir = None

#               -- If requested, create subdir and chdir to it
#               -- Subdir optionally named by base name and current time
    if self._subdir:
      cur_subdir = self._subdir
      if self._subdir == '.' or self._subdir == DEFAULT_SUBDIR:
        cur_subdir = case_name + '_' + start_str

      cur_rundir = os.path.join( os.getcwd(), cur_subdir )

      self.log( 'running in "{0}"', cur_rundir )
      if not os.path.isdir( cur_rundir ):
        os.mkdir( cur_rundir )

      pop_dir = os.getcwd()
      os.chdir( cur_rundir )

    else:
      cur_rundir = os.getcwd()

#               -- Copy VERAInput file if necessary, XML file if exists
#               --
    if input_path_dir != os.path.abspath( cur_rundir ):
      self.log( 'copying "{0}"', input_path )
      shutil.copy( input_path, cur_rundir )

      if not input_path.endswith( '.xml' ):
        xml_path = re.sub( r'\.inp$', '.xml', input_path )
        if os.path.exists( xml_path ):
          self.log( 'copying "{0}"', xml_path )
          shutil.copy( xml_path, cur_rundir )

#               -- Create XML input and parse it
    cur_input_path = os.path.join( cur_rundir, input_path_base )
    self._document = self._read_input_doc( cur_input_path )

#               -- Verify existence of restart and temptable files
    restart_fnames = self._document.find_files( 'restart_read' )
    if restart_fnames:
      missing = [ x for x in restart_fnames if not os.path.exists( x ) ]
      if len( missing ) > 0:
        raise Exception( 'Restart files not found: {0}'.format(
            ', '.join( missing )
            ) )
    temptable_fnames = self._document.find_files( 'temptable_filename' )
    if temptable_fnames:
      missing = [ x for x in temptable_fnames if not os.path.exists( x ) ]
      if len( missing ) > 0:
        raise Exception( 'Temptable files not found: {0}'.format(
            ', '.join( missing )
            ) )

#               -- Infer job parameters and create script
    params = self._resolve_params(
        self._document, pbs, input_path, input_ndx, self._params
        )
    if self._logger.isEnabledFor( logging.INFO ):
      self._logger.info(
          'creating job script with params:%s%s',
          os.linesep, str( params )
          )

    #x pbs.script_extension
    #job_fname = params.get( 'case', case_name ) + '.' + pbs.script_extension
    job_fname = params.get( 'case', case_name ) + '.pbs'
    job_pbs_path = os.path.join( cur_rundir, job_fname )
    self.log( 'creating {0}', job_pbs_path )
    #VeraJobScript( pbs.script_extension ).write( params, job_pbs_path )
    VeraJobScript( 'pbs' ).write( params, job_pbs_path )

    if not os.path.exists( job_pbs_path ):
      raise Exception( 'PBS script not created' )

#               -- Submit
    result = None
    if not self._dry_run:
      dependency_msg = ''
      if wait_job_id:
        dependency_msg = ', depend=' + str( wait_job_id )

      try:
        job_id, job_name = pbs.submit_job( job_fname, wait_job_id )

        msg = 'submitted job={0}, dir={1}{2}'.\
            format( job_name, cur_rundir, dependency_msg )
        self._logger.info( msg )
        print( '[verarun] ' + msg, file = sys.stderr )
        result = JobInfo(
            dtg = start_str,
            job_id = job_id, job_name = job_name,
            run_dir = cur_rundir
            )
      except Exception as ex:
        raise Exception( 'Error submitting job: ' + str( ex ) )

    if pop_dir:
      os.chdir( pop_dir )

    return  result
  #end run_case


#               -- Properties
#               --


#  cur_run_dir = property( lambda x: x._cur_run_dir )
#  """Path to current run directory"""

  document = property( lambda x: x._document )
  """XML Document after input parse"""

  hostinfo = property( lambda x: x._hostinfo )
  """config.hostinfo.HostInfo instance"""

  input_path = property( lambda x: x._input_path )
  """Path to input file"""

  job_id = property( lambda x: x._job_id )
  """Current job id, -1 if no current job"""

  logger = property( lambda x: x._logger )
  """Logger instance"""

  queue = property( lambda x: x._queue )
  """Override queue/partition name if specified"""

  vera_dir = property( lambda x: x._vera_dir )
  """Specified path to VERA installation"""

  vera_installs_dir = property( lambda x: x._vera_installs_dir )
  """Specified path to vera_installs directory"""

  vera_version = property( lambda x: x._vera_version )
  """Specified VERA version to use"""

  verbose = property( lambda x: x._verbose )
  """Flags more processing feedback"""

  wait_job_id = property( lambda x: x._wait_job_id )
  """Optional ID of job on which this job depends"""


#               -- Static Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.extant_input_file()                  -
  #----------------------------------------------------------------------
  @staticmethod
  def extant_input_file( fpath ):
    """
    Args:
        fpath (str): Input file path with .inp or .xml extension; if no
            extension '.inp' is assumed
    Returns:
        str: Existing file path, with '.inp' extension added if necessary
    Raises:
        argparse.ArgumentTypeError: If file not found
"""
#               -- No upper case extensions
#               --
    if fpath.endswith( '.INP' ) or fpath.endswith( '.XML' ):
      raise argparse.ArgumentTypeError( MESSAGE_NO_UPPER_EXT.format( fpath ) )

#               -- Check for missing extension
#               --
    exc_msg = None
    if not fpath.endswith( '.inp' ):
      name, ext = os.path.splitext( os.path.basename( fpath ) )
      if ext == '':
        fpath += '.inp'
      elif ext == '.':
        fpath = fpath[ : -1 ] + '.inp'

#               -- Check file existence
#               --
    if not os.path.exists( fpath ):
      #raise argparse.ArgumentTypeError( '"{0}" not found'.format( fpath ) )
      if VeraRunner.is_case_sensitive():
        if fpath.endswith( '.inp' ):
          f_upper = re.sub( r'\.inp$', '.INP', fpath )
          if os.path.exists( f_upper ):
            exc_msg = MESSAGE_UPPER_FNAME.format( fpath, f_upper, '.inp' )
        elif fpath.endswith( '.xml' ):
          f_upper = re.sub( r'\.xml$', '.XML', fpath )
          if os.path.exists( f_upper ):
            exc_msg = MESSAGE_UPPER_FNAME.format( fpath, f_upper, '.xml' )

      if not exc_msg:
        exc_msg = '"{0}" not found'.format( fpath )
      raise argparse.ArgumentTypeError( exc_msg )
    #end if not os.path.exists( f )

    return  fpath
  #end extant_input_file


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.is_case_sensitive()                  -
  #----------------------------------------------------------------------
  @staticmethod
  def is_case_sensitive():
    """
    Returns:
        bool: True if the filesystem is case-sensitive, False otherwise
"""
    with tempfile.NamedTemporaryFile( prefix = 'TmP' ) as tmp_file:
      return  not os.path.exists( tmp_file.name.lower() )
  #end is_case_sensitive


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.main()                               -
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
#               -- Parse command line
#               --
      def extant_dir( f ):
        if not os.path.isdir( f ):
          raise argparse.ArgumentTypeError( '"{0}" not found'.format( f ) )
        return  f
      #end extant_dir

#     def extant_inp_file( f ):
#       exc_msg = None
#       if not f.endswith( '.inp' ):
#         name, ext = os.path.splitext( os.path.basename( f ) )
#         if ext == '':
#           f += '.inp'
#       if not os.path.exists( f ):
#         raise argparse.ArgumentTypeError( '"{0}" not found'.format( f ) )
#       return  f
#     #end extant_file

#               -- Basic arguments
#               --
#     parser = argparse.ArgumentParser(
#         description = VeraRunner.DESCRIPTION,
#         epilog = VeraRunner.EPILOG,
#         formatter_class = CustomArgsFormatter,
#         prog = 'verarun'
#         )
      parser = argparse.ArgumentParser(
          add_help = False,
          description = VeraRunner.DESCRIPTION,
          epilog = 'Version ' + verarun.config.__version__,
          prog = 'verarun'
          )

      #pgroup = parser.add_mutually_exclusive_group()

      parser.add_argument(
          '--devs', '--allow-devs',
          action = 'store_true',
          dest = '_allow_devs',
          help = "override VERA_PROD_VERSIONS and allow development VERA versions"
          )
      parser.add_argument(
          '-x', '--dry-run',
          action = 'store_true',
          dest = 'dry_run',
          help = "dry run only, create but don't execute the PBS script"
          )
      #maybe make a single param with commas
      parser.add_argument(
          '-e', '--email-addrs',
          dest = 'email',
#         help = 'email address to notify of job completion, defaults to current user@ornl.gov',
          help = 'comma-delimited list of email addresses to notify of job completion, defaults to ${USER}@$(hostname)',
          metavar = 'email_addr'
#         nargs = '+'
          )
      parser.add_argument(
          '-h', '--help',
          action = 'store_true',
          dest = 'help_flag',
          help = 'print detailed help'
          )
      parser.add_argument(
          '-c', '--host-config-file',
          dest = 'host_config_file',
          help = 'override host configuration file, supercedes --hostname and --vera-installs-dir',
          metavar = 'config_file'
          )
      #pgroup.add_argument
      parser.add_argument(
          'input_path',
          #'-i', '--input',
          #dest = 'input_path',
          help = 'path to VERA input (.inp) or XML (.xml) files',
          nargs = '*',
          type = VeraRunner.extant_input_file
          )
      parser.add_argument(
          '-N', '--job-name',
          dest = 'job_name',
          help = 'name for the PBS job',
          metavar = 'job_name'
          )
      #pgroup.add_argument
      parser.add_argument(
          '-l', '--list-vera-versions',
          action = 'store_true',
          dest = 'list_vera_versions',
          help = 'list available VERA versions'
          )
      parser.add_argument(
          '-n', '--np', '--nprocs', '--num-procs',
          #default = 16,
          dest = 'nprocs',
          help = 'total number of processors need for the job (mpiexec -np param), defaults to value computed from input',
          metavar = 'nprocs',
          type = int
          )
      parser.add_argument(
          '-O', '--output-job-name',
          action = 'store_true',
          dest = 'output_job_flag',
          help = 'print the job id to stdout'
          )
      parser.add_argument(
          '--ppn', '--pnode',
          default = None,
          dest = 'ppn',
          help = 'specify processors per node, by default this is calculated',
          metavar = 'cpus_per_node',
          type = int
          )
      parser.add_argument(
          '-m', '--pmem', '--proc-memory',
          #default = 16,
          dest = 'pmem',
          help = 'specify memory required per processor in GB, defaults to undefined',
          metavar = 'mem_per_process',
          type = float
          )
      parser.add_argument(
          '-p', '--project',
          dest = 'project',
          help = 'optional project or account to specify for the job, overriding any default, where a value of "none" omits a project',
          metavar = 'project'
          )
      parser.add_argument(
          '-q', '--partition', '--queue',
          dest = 'queue',
          help = 'Torque queue or Slurm partition',
          metavar = 'queue'
          )
      parser.add_argument(
          '-s', '--subdir',
          dest = 'subdir',
          help = 'create subdir, a value of "." specifies automatically generated subdir name',
          metavar = 'subdir'
          )
      parser.add_argument(
          '-d', '--vera-dir',
          dest = 'vera_dir',
          help = 'path to VERA installation, superceding --vera-installs-dir, --vera-version, and the host configuration',
          metavar = 'vera_install_dir',
          type = extant_dir
          )
      parser.add_argument(
          '-v', '--vera-version',
          dest = 'vera_version',
          help = 'name of VERA version to use',
          metavar = 'vera_version'
          )
      parser.add_argument(
          '--verbose',
          action = 'store_true',
          help = 'turn on verbose messaging'
          )
      parser.add_argument(
          '-W',
          action = 'store_true',
          dest = 'wait_last',
          help = 'wait on job last submitted via verarun, overrides -w'
          )
      parser.add_argument(
          '-w', '--wait-job-id',
          #default = 'last',
          dest = 'wait_job_id',
          #help = 'before running any jobs wait for completion of a previously submitted job (value of "last") or a fully qualified job name',
          help = 'ID of job which must complete before starting this job',
          metavar = 'job_id'
          )
      parser.add_argument(
          '-t', '--wall-time',
          #default = '24.0',
          dest = 'walltime',
          help = 'wallclock execution time in floating point hours, defaults to 24.0',
          metavar = 'walltime',
          type = float
          )

#               -- Advanced arguments
#               --
      adv_group = parser.add_argument_group( 'advanced arguments' )
      adv_group.add_argument(
          '--chain', '--chain-jobs',
          action = 'store_true',
          dest = 'chain_mode',
          help = "each job depends on its predecessor"
          )
      adv_group.add_argument(
          '--debug',
          action = 'store_true',
          help = 'debug mode'
          )
      adv_group.add_argument(
          '--hostname',
          dest = 'hostname',
          help = 'force the hostname',
          metavar = 'host'
          )
      adv_group.add_argument(
          '-r', '--restart',
          choices = [ 'overwrite', 'readwrite' ],
          dest = 'restart',
          help = 'optional restart mode'
          )
      adv_group.add_argument(
          '--vera-installs-dir',
          dest = 'vera_installs_dir',
          help = 'path to vera_installs directory containing VERA versions',
          metavar = 'vera_installs_dir',
          type = extant_dir
          )

#               -- Parse for basic args
#               --
      #parser.set_defaults( vera_installs_dir = None )
      args = parser.parse_args()

#               -- Host config from environment?
#               --
      host_config_file = args.host_config_file
      if not host_config_file:
        host_config_file = os.environ.get( 'VERARUN_HOST_CONFIG_FILE' )

#               -- Long help?
#               --
      if args.help_flag:
        parser.print_help()
        print( VeraRunner.EPILOG )

#               -- List VERA versions
#               --
      elif args.list_vera_versions:
        vera_installs_dir = \
            os.path.dirname( args.vera_dir )  if args.vera_dir else \
            args.vera_installs_dir
        if host_config_file:
          hostinfo = HostInfo(
              host_config_file = host_config_file,
              vera_installs_dir = vera_installs_dir
              )
        else:
          hostinfo = HostInfo(
              args.hostname,
              vera_installs_dir = vera_installs_dir
              )

        working_version = hostinfo.get_working_vera_version()
        versions = map(
            lambda v: v + ' *' if v == working_version else v,
            hostinfo.get_available_vera_versions( args._allow_devs )
            #hostinfo.vera_versions
            )
        sep = os.linesep + '  '
        print(
            'Available VERA versions (newest to oldest, * for default):{0}{1}'.
            format( sep, sep.join( versions ) )
            )

        if args.verbose:
          print( file = sys.stderr )
          print( '[verarun] Missing Files in VERA Subdirs', file = sys.stderr )

          display_versions = hostinfo.missing_files.keys()
          if not( hostinfo.vera_prod_versions is None or args._allow_devs ):
            prod_dirs = REGEX_COMMAS.\
                split( os.environ.get( 'VERA_PROD_VERSIONS' ) )
            hostinfo.check_valid_vera_versions( prod_dirs )
            missing_keys = hostinfo.missing_files.keys()
            display_versions = list( filter(
                lambda v: v in missing_keys, prod_dirs
                ) )

          #for subdir in sorted( hostinfo.missing_files.keys() ):
          for subdir in sorted( display_versions ):
            files = hostinfo.missing_files.get( subdir )
            if files:
              print( subdir + os.sep + ':', file = sys.stderr )
              delim = os.linesep + '    '
              print(
                  '    ' + delim.join( sorted( files ) ),
                  file = sys.stderr
                  )
          #end for subdir

#               -- Execute
#               --
      elif args.input_path:
#        kwargs = {
#            name: getattr( args, name )
#            for name in dir( args )
#            if not( name.startswith( '_' ) or name == 'input_path' )
#            }
        kwargs = { 'host_config_file': host_config_file }
        for name in dir( args ):
          if not( name.startswith( '_' ) or name == 'input_path' ):
            val = getattr( args, name )
            if val:
              kwargs[ name ] = val
        #end for name in dir( args )

#                       -- Create runner
        runner = VeraRunner( args.input_path, **kwargs )

#                       -- Verify VERA directory
        error_msg = None
        vera_dir = runner.resolve_vera_dir()
        if not runner.vera_dir:  # i.e. not an explicit path CLI argument
          error_msg = runner.hostinfo.\
              check_working_vera_version( args._allow_devs )
        elif not vera_dir:
          error_msg = VeraRunner.MSG_veraDirNotSpecified
        elif not os.path.isdir( vera_dir ):
          error_msg = VeraRunner.MSG_veraDirNotFound.format( vera_dir )
        elif not runner.hostinfo.is_valid_vera_dir( vera_dir ):
          error_msg = VeraRunner.MSG_veraDirInvalid.format( vera_dir )

        if error_msg:
          print( error_msg, file = sys.stderr )
        else:
          runner()
#original
#       vera_dir = runner.resolve_vera_dir()
#       if not vera_dir:
#         print( VeraRunner.MSG_veraDirNotSpecified, file = sys.stderr )
#       elif not os.path.isdir( vera_dir ):
#         print(
#             VeraRunner.MSG_veraDirNotFound.format( vera_dir ),
#             file = sys.stderr
#             )
#       elif not runner.hostinfo.is_valid_vera_dir( vera_dir ):
#         print(
#             VeraRunner.MSG_veraDirInvalid.format( vera_dir ),
#             file = sys.stderr
#             )
#       else:
#         runner()
#original

#               -- Short help
#               --
      else:
        parser.print_help()

    except AssertionError as ex:
      logging.exception( ex )
      #print( '[verarun] ' + str( ex ), file = sys.stderr )
      print( 'Error: ' + str( ex ), file = sys.stderr )

    except Exception as ex:
      logging.exception( ex )
      #traceback.print_exc( file = sys.stderr )
      #print( '[verarun] ' + str( ex ), file = sys.stderr )
      print( 'Error: ' + str( ex ), file = sys.stderr )
  #end main

#end VeraRunner


#------------------------------------------------------------------------
#       NAME:           main()                                          -
#------------------------------------------------------------------------
if __name__ == '__main__':
  VeraRunner.main()
