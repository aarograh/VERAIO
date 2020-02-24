#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#       NAME:           pbs_utility.py                                  -
#       HISTORY:                                                        -
#               2019-02-08      leerw@ornl.gov                          -
#------------------------------------------------------------------------
import argparse, logging, os, re
import six, subprocess, sys, time, traceback
from datetime import datetime

import pdb


DEFAULT_SUBDIR = '_dtg_'
REGEX_JOB_ID = re.compile( r'^(\d+).*$' )


#------------------------------------------------------------------------
#       CLASS:          PBSUtility                                      -
#------------------------------------------------------------------------
class PBSUtility( object ):
  """
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         PBSUtility.__call__()                           -
  #----------------------------------------------------------------------
  def __call__( self, *args, **kwargs ):
    """
"""
    self.run( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #     METHOD:         PBSUtility.__init__()                           -
  #----------------------------------------------------------------------
  def __init__( self, job_id ):
    """
    Args:
        job_id (str): job id
"""
    self._jobId = job_id
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         PBSUtility._read_input_doc()                    -
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
        vera_dir = \
            self._vera_dir  if self._vera_dir else \
            self._hostinfo.create_vera_path( self._vera_version )
        react2xml_path = os.path.join( vera_dir, 'bin', 'react2xml.pl' )
        self.log( 'creating "{0}"', xml_output_file )
        subprocess.check_call( [ react2xml_path, input_path ] )

    assert os.path.exists( xml_output_file ), \
        'XML file not found or not created: "{0}"'.format( xml_output_file )

    self.log( 'reading "{0}"', xml_output_file )
    return  VeraInputXMLDoc( xml_output_file )
  #end _read_input_doc


  #----------------------------------------------------------------------
  #     METHOD:         PBSUtility.run()                                -
  #----------------------------------------------------------------------
  def run( self, *args, **kwargs ):
    """
"""
    start_dt = datetime.now()
    start_str = start_dt.strftime( '%Y-%m-%dT%H:%M:%S' )
    if self.logger.isEnabledFor( logging.INFO ):
      self.logger.info( 'starting at %s', start_str )

    input_path_dir = os.path.abspath( os.path.dirname( self._input_path ) )

#               -- If requested, create subdir and chdir to it
#               -- Subdir optionally named by base name and current time
    if self._subdir:
      if self._subdir == '.' or self._subdir == DEFAULT_SUBDIR:
        base_name, ext = \
            os.path.splitext( os.path.basename( self._input_path ) )
        #base_dir = os.path.dirname( self._input_path )
        self._subdir = base_name + '_' + start_str

      self._cur_run_dir = os.path.join( os.getcwd(), self._subdir )

      self.log( 'using subdir "{0}"', self._subdir )
      if not os.path.isdir( self._cur_run_dir ):
        os.mkdir( self._cur_run_dir )

      os.chdir( self._cur_run_dir )

    else:
      self._cur_run_dir = os.getcwd()

#               -- Copy input file if necessary
#               --
    if input_path_dir != os.path.abspath( self._cur_run_dir ):
      self.log( 'copying "{0}"', self._input_path )
      shutil.copy( self._input_path, self._cur_run_dir )

      xml_path = re.sub( r'\.inp$', '.xml', self._input_path )
      if os.path.exists( xml_path ):
        self.log( 'copying "{0}"', xml_path )
        shutil.copy( xml_path, self._cur_run_dir )

    working_input_path = os.path.join(
        self._cur_run_dir,
        os.path.basename( self._input_path )
        )

#               -- Create XML input and parse it
    self._document = self._read_input_doc( working_input_path )

#               -- Verify existence of restart files
    restart_fnames = self._document.find_files( 'restart_read' )
    if restart_fnames:
      missing = [ x for x in restart_fnames if not os.path.exists( x ) ]
      assert len( missing ) == 0, \
          'Restart files not found: {0}'.format( ', '.join( missing ) )

#               -- Infer job parameters and create script
    #params = params.VeraJobParams
    params = self._resolve_params( self._document, self._params )
    if self._logger.isEnabledFor( logging.INFO ):
      self._logger.info(
          'creating job script with params:%s%s',
          os.linesep, str( params )
          )

    #job_pbs_path = os.path.join( self._cur_run_dir, 'job.pbs' )
    job_fname = params.get( 'case', 'job' ) + '.pbs'
    job_pbs_path = os.path.join( self._cur_run_dir, job_fname )
    self.log( 'creating {0}', job_pbs_path )
    VeraJobScript().write( params, job_pbs_path )

    assert os.path.exists( job_pbs_path ), 'Job PBS script not created'

#               -- Submit
    if not self._dry_run:
      self.log( 'submitting job' )
      output = subprocess.check_output( [ 'qsub', job_fname ] )
      m = REGEX_JOB_ID.match( output )
      #assert m, 'Job not submitted'
      self._job_id = int( m.group( 1 ) ) if m else -1

      msg = 'submitted job id={0:d}, dir={1}'.\
          format( self._job_id, self._cur_run_dir )
      self._logger.info( msg )
      six.print_( '[verarun] ' + msg )
  #end run


#               -- Properties
#               --


  cur_run_dir = property( lambda x: x._cur_run_dir )
  """Path to current run directory"""

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

  vera_dir = property( lambda x: x._vera_dir )
  """Specified path to VERA installation"""

  vera_installs_dir = property( lambda x: x._vera_installs_dir )
  """Specified path to vera_installs directory"""

  vera_version = property( lambda x: x._vera_version )
  """Specified VERA version to use"""


#               -- Static Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         PBSUtility.main()                               -
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

      def extant_inp_file( f ):
        if not f.endswith( '.inp' ):
          name, ext = os.path.splitext( os.path.basename( f ) )
          if ext == '':
            f += '.inp'
        if not os.path.exists( f ):
          raise argparse.ArgumentTypeError( '"{0}" not found'.format( f ) )
        return  f
      #end extant_file

      parser = argparse.ArgumentParser(
          description = PBSUtility.DESCRIPTION,
          epilog = PBSUtility.EPILOG,
          formatter_class = CustomArgsFormatter,
          prog = 'verarun'
          )

      pgroup = parser.add_mutually_exclusive_group()

      parser.add_argument(
          '--debug',
          action = 'store_true',
          help = 'debug mode'
          )
      parser.add_argument(
          '-x', '--dry-run',
          action = 'store_true',
          dest = 'dry_run',
          help = "dry run only, create but don't execute the PBS script"
          )
      parser.add_argument(
          '-e', '--email', '--email-addrs',
          dest = 'email',
          help = 'email addresss to notify of job completion, defaults to current user@ornl.gov',
          nargs = '+'
          )
      parser.add_argument(
          '-c', '--host-config-file',
          dest = 'host_config_file',
          help = 'override host configuration file, supercedes --hostname and --vera-installs-dir'
          )
      parser.add_argument(
          '--hostname',
          dest = 'hostname',
          help = 'force the hostname'
          )
      pgroup.add_argument(
          'input_path',
          #'-i', '--input',
          #dest = 'input_path',
          help = 'path to VERA input (.inp) or XML (.xml) file',
          nargs = '?',
          type = extant_inp_file
          )
      pgroup.add_argument(
          '-l', '--list-versions', '--list-vera-versions',
          action = 'store_true',
          dest = 'list_vera_versions',
          help = 'list available VERA versions'
          )
      parser.add_argument(
          '-n', '--np', '--nprocs', '--num-procs',
          #default = 16,
          dest = 'nprocs',
          help = 'total number of processors need for the job (mpiexec -np param), defaults to value computed from input',
          type = int
          )
      parser.add_argument(
          '--ppn', '--pnode',
          default = None,
          dest = 'ppn',
          help = 'specify processors per node, by default this is calculated',
          type = int
          )
      parser.add_argument(
          '-m', '--pmem', '--proc-memory',
          #default = 16,
          dest = 'pmem',
          help = 'specify memory required per processor in GB, defaults to 8',
          type = int
          )
      parser.add_argument(
          '-r', '--restart',
          choices = [ 'overwrite', 'readwrite' ],
          dest = 'restart',
          help = 'optional restart mode'
          )
#      parser.add_argument(
#          '-s', '--subdir',
#          action = 'store',
#          const = DEFAULT_SUBDIR,
#          default = None,
#          dest = 'subdir',
#          help = 'create subdir with results with optional subdir name',
#          nargs = '?'
#          )
      parser.add_argument(
          '-s', '--subdir',
          dest = 'subdir',
          help = 'create subdir, a value of "." specifies automatically generated subdir name'
          )
      parser.add_argument(
          '-d', '--vera-dir',
          dest = 'vera_dir',
          help = 'path to VERA installation, superceding --vera-installs-dir, --vera-version, and the host configuration',
          type = extant_dir
          )
      parser.add_argument(
          '--vera-installs-dir',
          dest = 'vera_installs_dir',
          help = 'path to vera_installs directory containing VERA versions',
          type = extant_dir
          )
      parser.add_argument(
          '-v', '--vera-version',
          dest = 'vera_version',
          help = 'name of VERA version to use'
          )
      parser.add_argument(
          '--verbose',
          action = 'store_true',
          help = 'turn on verbose messaging'
          )
      parser.add_argument(
          '-t', '--wt', '--time', '--wall-time',
          #default = '24.0',
          dest = 'walltime',
          help = 'wallclock execution time in floating point hours, defaults to 24.0',
          type = float
          )

      args = parser.parse_args()

#                       -- Just list VERA versions
#                       --
      if args.list_vera_versions:
        sep = os.linesep + '  '
        if args.host_config_file:
          hostinfo = HostInfo(
              host_config_file = args.host_config_file,
              vera_installs_dir = args.vera_installs_dir
              )
        else:
          hostinfo = HostInfo(
              args.hostname,
              vera_installs_dir = args.vera_installs_dir
              )
        six.print_(
            'Available VERA versions:{0}{1}'.
            format( sep, sep.join( hostinfo.get_vera_versions() ) )
            )

#                       -- Execute
#                       --
      elif args.input_path:
        kwargs = {}
        for name in dir( args ):
          if not( name.startswith( '_' ) or name == 'input_path' ):
            val = getattr( args, name )
            if val:
              kwargs[ name ] = val
        #end for name in dir( args )

        PBSUtility( args.input_path, **kwargs )()

      else:
        parser.print_help()

    except AssertionError as ex:
      logging.exception( ex )
      six.print_( '[verarun] ' + str( ex ), file = sys.stderr )

    except Exception as ex:
      #msg = str( ex )
      logging.exception( ex )
      #traceback.print_exc( file = sys.stderr )
      six.print_( '[verarun] ' + str( ex ), file = sys.stderr )
  #end main

#end PBSUtility


#------------------------------------------------------------------------
#       NAME:           main()                                          -
#------------------------------------------------------------------------
if __name__ == '__main__':
  PBSUtility.main()
