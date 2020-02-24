#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#       NAME:           runner.py                                       -
#       HISTORY:                                                        -
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
import shutil, six, subprocess, sys, tempfile, time, traceback
from datetime import datetime

import verarun.config
from .config import config
from .config.hostinfo import *
#from verarun.job import *
from .job.verajob import *
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
There are three environment variables which can be set to override behavior.

* PBS_EMAIL: sets the email address to be used for PBS notifications,
  overridden by the '-e' parameter.

* VERA_DEFAULT_VERSION: names the default version of VERA to use, overriding
  what is specified in the host configuration file but overridden by the '-v'
  parameter.

* VERA_QSUB: custom 'qsub' command to execute.

* VERARUN_HOST_CONFIG_FILE: path to a host configuration file to use,
  overriding the distributed "$(hostname).json" file but overriddent by
  the '-c' parameter.
"""

  MSG_machineConfig = """
Error: Machine configuration cannot support request:
  machine:   {0}
  requested: nprocs={1:d}, pmem={2:d}
"""

  MSG_memoryWarning = """
Warning: Requested memory and ppn exceed machine per-node memory:
  available: pmem={0:d}
  requested: ppn={1:d}, pmem={2:d}
"""

  MSG_tooManyProcessors = """
Error: Too many processors requested for this machine:
  available={0:d}, requested={1:d}
"""

  MSG_tooMuchMemory = """
Error: Too much memory requested for nodes on this machine:
  available={0:d}, requested={1:d}
"""

  MSG_veraDirNotFound ="""[verarun] VERA directory not found: "{0}"
Check command-line arguments and host configuration.
"""

  MSG_veraDirInvalid ="""[verarun] Invalid VERA directory: "{0}"
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
            job name
        ppn (int): Number of processors per node, where None means to calculate
            it (defaults to None)
        proc_mem (int): Memory required per processor in GB (defaults to 16)
        restart (str): One of 'overwrite', 'readwrite', or None
        vera_dir (str): optional path to VERA installation, overrides `vera_installs_dir`
            and `vera_version` params
        vera_installs_dir (str): optional path to 'vera_installs' directory containing
            VERA versions
        vera_version (str): optional name of VERA version to use, where None means to
            use the latest available version
        verbose (bool): True to provide more processing feedback
        wait_job_name (str): optional fully-qualified name of job
            (e.g., "id.hostpbsname") for which to wait on completion
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
#    self._job_suffix = ''
    self._subdir = kwargs.get( 'subdir' )
    self._user_data = UserData()
    self._verbose = kwargs.get( 'verbose', False )
    self._wait_job_name = kwargs.get( 'wait_job_name' )
    if kwargs.get( 'wait_last', False ):
      self._wait_job_name = 'last'

    for n in ( 'dry_run', 'subdir', 'verbose' ):
      if n in kwargs:  del kwargs[ n ]

    self._params = kwargs

    self._vera_dir = kwargs.get( 'vera_dir' )
    self._vera_installs_dir = kwargs.get( 'vera_installs_dir' )
    self._vera_version = kwargs.get( 'vera_version' )

    host_config_file = kwargs.get( 'host_config_file' )
    hostname = kwargs.get( 'hostname' )
    self._hostinfo = \
        HostInfo( host_config_file = host_config_file ) \
        if host_config_file else \
        HostInfo( hostname, vera_installs_dir = self._vera_installs_dir )

#    self._email_addrs = None
#    if isinstance( email_addrs, list ):
#      self._email_addrs = ','.join( email_addrs )
#    elif email_addrs:
#      self._email_addrs = re.sub( r'\s*', '', email_addrs )

#    self._nprocs = nprocs
#    self._ppn = ppn
#    self._proc_mem = proc_mem
#    self._vera_dir = vera_dir
#    self._vera_version = vera_version
#    self._walltime = walltime
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

    assert os.path.exists( xml_output_file ), \
        'XML file not found or not created: "{0}"'.format( xml_output_file )

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
  def _resolve_params( self, doc, input_path, params ):
    """
    Args:
        doc (verain.VeraInputXMLDoc): document to consult
        input_path (str): required path to input file, either a VERAIn or
            VERA XML file
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
    # future no email PBS directive
    #if not email:
      #email = getpass.getuser() + '@' + self._hostinfo.domain

#x    nprocs = run_params.get( 'nprocs', 1 )
#x    pmem = int( run_params.get( 'pmem', 8 ) )
    nprocs = run_params.get( 'nprocs', self._hostinfo.specs.nprocs )
    pmem_str = run_params.get( 'pmem' )
    pmem = int( pmem_str )  if pmem_str else  None
    ppn = run_params.get( 'ppn' )
    restart = run_params.get( 'restart' )
    vera_version = run_params.get( 'vera_version' )
    walltime = run_params.get( 'walltime', 24.0 )

    ## if vera_shift, nprocs
    machine_nprocs = self._hostinfo.specs.nprocs
    assert nprocs <= machine_nprocs, \
        VeraRunner.MSG_tooManyProcessors.format( machine_nprocs, nprocs )

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
    machine_mem = self._hostinfo.specs.mem
    if pmem:
      if pmem * use_ppn > machine_mem:
        print(
            VeraRunner.MSG_memoryWarning.format( machine_mem, use_ppn, pmem ),
            file = sys.stderr
            )
        use_ppn = self._hostinfo.specs.mem // pmem
        assert use_ppn > 0, \
          VeraRunner.MSG_tooMuchMemory.\
              format( self._hostinfo.specs.mem, pmem )
        nodes = (nprocs + use_ppn - 1) // use_ppn
    #end if pmem

    machine_nodes = self._hostinfo.specs.nodes
    assert nodes <= machine_nodes, \
        VeraRunner.MSG_machineConfig.\
            format( self._hostinfo.specs, nprocs, pmem )

#               -- Job params
#               --
    case_name, ext = os.path.splitext( os.path.basename( input_path ) )
    vera_path = \
        self._vera_dir  if self._vera_dir else \
        self._hostinfo.create_vera_path( self._vera_version )

    job_name = self._job_name  if self._job_name else  'VERA-' + case_name

    feedback_values = doc.find_state_params( 'feedback' )
    run_ctf = feedback_values and 'on' in feedback_values
    run_mpact = True if doc.find_param_blocks( 'MPACT' ) else False

    run_multistate_cobra = run_params.get( 'exe_mode', '' ) == 'th'
    if run_multistate_cobra:
      run_mpact = False

    excore_values = doc.find_state_params( 'excore_transport' )
    run_shift = excore_values and 'on' in excore_values

    excore_filename = doc.find_shift_param( 'excore_filename' )
    if excore_filename:
      if not excore_filename.endswith( '.excore.xml' ):
        excore_filename += '.excore.xml'
      #excore_omn_name = excore_filename[ : -11 ] + '.omn'

    rt_values = doc.find_state_params( 'thexp' )
    run_thermal_exp = rt_values and 'on' in rt_values and run_shift
    run_verain = not input_path.endswith( '.xml' )

    params = VeraJobParams(
        case_name, vera_path,
        #account = self._account,
        cores = nprocs,
        email_addrs = email,
        excore_filename = excore_filename,
        job_name = job_name,
        nodes = nodes,
#x        pbs_env = self._hostinfo.pbs_env,
#x        pmem = pmem,
        pbs_env = self._hostinfo.resolve_env( email, pmem ),
        ppn = use_ppn,
        restart = restart,
        run_ctf = run_ctf,
        run_mpact = run_mpact,
        run_multistate_cobra = run_multistate_cobra,
        run_shift = run_shift,
        run_thermal_exp = run_thermal_exp,
        run_verain = run_verain,
        walltime = walltime
        )
    return  params
  #end _resolve_params


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.run()                                -
  #----------------------------------------------------------------------
  def run( self, *args, **kwargs ):
    """
"""
    start_dt = datetime.now()
    start_str = start_dt.strftime( '%Y-%m-%dT%H:%M:%S' )
    if self.logger.isEnabledFor( logging.INFO ):
      self.logger.info( 'starting run at %s', start_str )

    last_mode = 'last' == self._wait_job_name
    wait_job_name = \
        self._user_data.last_job_name  if last_mode  else \
        self._wait_job_name  if self._wait_job_name  else \
        None

    submit_names = []

    for ipath in self._input_paths:
#x    job_name, job_id, run_dir = self.run_case( ipath, wait_job_name )
#x    if job_name and job_name[ 0 ]:
#x      self._user_data.last_job_name = job_name
#x      submit_names.append( job_name )
      job_info = self.run_case( ipath, wait_job_name )
      if job_info:
        job_name = job_info.get( 'job_name' )
        self._user_data.last_job_name = job_name
        submit_names.append( job_name )

        if wait_job_name:
          job_info.depend_job = wait_job_name
          #job_info[ 'depend_job' ] = wait_job_name
        self._user_data.append_job_history( job_info )
        wait_job_name = job_name if last_mode or self._chain_mode  else None
      else:
        wait_job_name = None
    #end for ipath in self._input_paths

    if self._output_job_flag and not self._dry_run:
      print( os.linesep.join( submit_names ) )
  #end run


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunner.run_case()                           -
  #----------------------------------------------------------------------
  def run_case( self, input_path, wait_job_name ):
    """
    Args:
        input_path (str): required path to input file, either a VERAIn or
            VERA XML file
        wait_job_name (str): optional name of job on which this case depends
    Returns:
        userdata.JobInfo: submitted job info or None if not submitted
#x      dict: submitted job properties or None if not submitted
#x          job_name (str): job_name
#x          job_id (int): job_id
#x          run_dir (str): run directory
#x          dtg (str): time of submission
#x      tuple(str,int,str): ( job_name, job_id, run_dir, dtg ) or
#x          ( '',-1,'','' ) if not submitted
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

#               -- Copy input file if necessary
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

#               -- Verify existence of restart files
    restart_fnames = self._document.find_files( 'restart_read' )
    if restart_fnames:
      missing = [ x for x in restart_fnames if not os.path.exists( x ) ]
      assert len( missing ) == 0, \
          'Restart files not found: {0}'.format( ', '.join( missing ) )

#               -- Infer job parameters and create script
    #params = params.VeraJobParams
    params = self._resolve_params( self._document, input_path, self._params )
    if self._logger.isEnabledFor( logging.INFO ):
      self._logger.info(
          'creating job script with params:%s%s',
          os.linesep, str( params )
          )

    job_fname = params.get( 'case', case_name ) + '.pbs'
    job_pbs_path = os.path.join( cur_rundir, job_fname )
    self.log( 'creating {0}', job_pbs_path )
    VeraJobScript().write( params, job_pbs_path )

    assert os.path.exists( job_pbs_path ), 'Job PBS script not created'

#               -- Submit
#x  result = '', -1, '', ''
    result = None
    if not self._dry_run:
#      self.log( 'submitting job' )
#      output = subprocess.check_output( [ 'qsub', job_fname ] )
#      m = REGEX_JOB_ID.match( output )
#      #assert m, 'Job not submitted'
#      self._job_id = int( m.group( 1 ) ) if m else -1

      args = [ 'qsub' ]
#      if 'VERA_QSUB' in os.environ:
#        args = REGEX_WS.split( os.environ.get( 'VERA_QSUB' ).lstrip( '\t ' ) )
      vera_qsub = os.environ.get( 'VERA_QSUB', '' )
      if vera_qsub:
        args = REGEX_WS.split( vera_qsub.lstrip( '\t ' ) )

      dependency_msg = ''
      if wait_job_name:
        args.append( '-W' )
        args.append( 'depend=afterok:{0}'.format( wait_job_name ) )
        dependency_msg = ', depend=' + wait_job_name
      args.append( job_fname )
      self.log( 'submitting job: ' + str( args ) )
      job_name = subprocess.check_output( args )
      job_name = job_name.rstrip( '\r\n' )
      self.log( 'job name: ' + job_name )
      m = REGEX_JOB_ID.match( job_name )
      job_id = int( m.group( 1 ) ) if m  else -1

#      msg = 'submitted job id={0:d}, dir={1}'.\
#          format( self._job_id, self._cur_run_dir )
      msg = 'submitted job={0}, dir={1}{2}'.\
          format( job_name, cur_rundir, dependency_msg )
      self._logger.info( msg )
      print( '[verarun] ' + msg, file = sys.stderr )
      result = JobInfo(
          job_name = job_name, job_id = job_id,
          dtg = start_str, run_dir = cur_rundir
          )
#x    result = job_name, job_id, cur_rundir
#x    result = dict(
#x        job_name = job_name, job_id = job_id,
#x        run_dir = cur_rundir, dtg = start_str
#x        )

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

  job_suffix = property( lambda x: x._job_suffix )
  """Job suffix string for qstat output"""

  logger = property( lambda x: x._logger )
  """Logger instance"""

  vera_dir = property( lambda x: x._vera_dir )
  """Specified path to VERA installation"""

  vera_installs_dir = property( lambda x: x._vera_installs_dir )
  """Specified path to vera_installs directory"""

  vera_version = property( lambda x: x._vera_version )
  """Specified VERA version to use"""

  verbose = property( lambda x: x._verbose )
  """Flags more processing feedback"""

  wait_job_name = property( lambda x: x._wait_job_name )
  """Optional job name on which this job depends"""


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
          help = 'print the job name to stdout'
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
          type = int
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
          help = 'wait on job last submitted via verarun, overrides -W'
          )
      parser.add_argument(
          '-w', '--wait-job-id',
          #default = 'last',
          dest = 'wait_job_name',
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
          help = "each case depends on its predecessor"
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
        if host_config_file:
          hostinfo = HostInfo(
              host_config_file = host_config_file,
              vera_installs_dir = args.vera_installs_dir
              )
        else:
          hostinfo = HostInfo(
              args.hostname,
              vera_installs_dir = args.vera_installs_dir
              )

        working_version = hostinfo.working_vera_version
        versions = map(
            lambda v: v + ' *' if v == working_version else v,
            hostinfo.vera_versions
            )
        sep = os.linesep + '  '
        print(
            'Available VERA versions (newest to oldest, * for default):{0}{1}'.
            format( sep, sep.join( versions ) )
            )

        if args.verbose:
          print( file = sys.stderr )
          print( '[verarun] Missing Files in VERA Subdirs', file = sys.stderr )
          for subdir in sorted( hostinfo.missing_files.keys() ):
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
        #VeraRunner( args.input_path, **kwargs )()
        runner = VeraRunner( args.input_path, **kwargs )

#                       -- Verify VERA directory
        vera_dir = runner.resolve_vera_dir()
        if not os.path.isdir( vera_dir ):
          print(
              VeraRunner.MSG_veraDirNotFound.format( vera_dir ),
              file = sys.stderr
              )
        elif not runner.hostinfo.is_valid_vera_dir( vera_dir ):
          print(
              VeraRunner.MSG_veraDirInvalid.format( vera_dir ),
              file = sys.stderr
              )
        else:
          runner()

#               -- Short help
#               --
      else:
        parser.print_help()

    except AssertionError as ex:
      logging.exception( ex )
      print( '[verarun] ' + str( ex ), file = sys.stderr )

    except Exception as ex:
      #msg = str( ex )
      logging.exception( ex )
      #traceback.print_exc( file = sys.stderr )
      print( '[verarun] ' + str( ex ), file = sys.stderr )
  #end main

#end VeraRunner


#------------------------------------------------------------------------
#       NAME:           main()                                          -
#------------------------------------------------------------------------
if __name__ == '__main__':
  VeraRunner.main()
