#!/usr/bin/env python
#------------------------------------------------------------------------
#       NAME:           test_verarun.py                                 -
#       HISTORY:                                                        -
#               2020-11-10      leerw@ornl.gov                          -
#               2020-10-13      leerw@ornl.gov                          -
#         Added run_error_test() and more tests.
#               2020-09-16      leerw@ornl.gov                          -
#------------------------------------------------------------------------
from __future__ import print_function
import inspect, os, re, shutil, six, subprocess, sys
import tempfile, traceback, unittest
import pdb  # set_trace()

#BASELINES_DIR = os.path.join( os.path.dirname( __file__ ), 'baselines' )
BASELINES_DIR = os.path.join( os.getcwd(), 'baselines' )

#FILES_DIR = os.path.join( os.path.dirname( __file__ ), 'files' )
FILES_DIR = os.path.join( os.getcwd(), 'files' )

PYTHON_PATH = os.path.join( os.getcwd(), os.pardir, 'src' )
#   join( os.path.dirname( __file__ ), os.pardir, 'src' )

#SCRIPTS_DIR = os.path.join( os.path.dirname( __file__ ), 'scripts' )
SCRIPTS_DIR = os.path.join( os.getcwd(), 'scripts' )

TEST_ROOT_DIR = os.getcwd()

VERARUN = os.path.join( os.getcwd(), os.pardir, 'bin', 'verarun' )
#   join( os.path.dirname( __file__ ), os.pardir, 'bin', 'verarun' )

sys.path.insert( 0, PYTHON_PATH )


#------------------------------------------------------------------------
#       FUNCTION:       create_temp_dir()                               -
#------------------------------------------------------------------------
if six.PY2:
  from contextlib import contextmanager
  @contextmanager
  def create_temp_dir():
    dir_path = tempfile.mkdtemp()
    try:
      yield  dir_path
    finally:
      shutil.rmtree( dir_path )

else:
  def create_temp_dir():
    return  tempfile.TemporaryDirectory()


#------------------------------------------------------------------------
#       CLASS:          VeraRunTests                                    -
#------------------------------------------------------------------------
class VeraRunTests( unittest.TestCase ):
  """
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunTests.run_error_test()                   -
  #----------------------------------------------------------------------
  def run_error_test(
      self, tag,
      config_name, xml_name,
      params, baseline_error_regex
      ):
    """
    Args:
        tag (str): test message tag
        config_name (str): name of host configuration file
        xml_name (str): name of XML input file
        params (list): additional arguments
        baseline_error_regex (str): optional regex with which to match
            stderr content
"""
    config_path = os.path.join( FILES_DIR, config_name )
    xml_path = os.path.join( FILES_DIR, xml_name )

    #with tempfile.TemporaryDirectory() as temp_path:
    with create_temp_dir() as temp_path:
      try:
        if os.path.exists( xml_path ):
          shutil.copy( xml_path, temp_path )

        cur_dir = os.getcwd()
        os.chdir( temp_path )

#               -- Execute
#               --
        run_args = [ VERARUN, '-c', config_path ]
        if params:
          run_args.extend( params )
        run_args.append( xml_name )

        test_output = subprocess.\
            check_output( run_args, stderr = subprocess.STDOUT )
        if isinstance( test_output, bytes ):
          test_output = test_output.decode( 'utf-8' )

#               -- Check error
#               --
        self.assertIsNotNone(
            re.match( baseline_error_regex, test_output, re.DOTALL ),
            msg = tag + ': stderr'
            )
#       self.assertMultiLineEqual(
#           baseline_output, test_output,
#           msg = tag + ': stdout'
#           )

      except subprocess.CalledProcessError as ex:
        self.fail( '{0}: exit code={1:d}'.format( tag, ex.returncode ) )

      finally:
        os.chdir( cur_dir )
    #end with temp_path
  #end run_error_test


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunTests.run_fail_test()                    -
  #----------------------------------------------------------------------
  def run_fail_test(
      self, tag,
      config_name, xml_name,
      params, baseline_error_regex
      ):
    """
    Args:
        tag (str): test message tag
        config_name (str): name of host configuration file
        xml_name (str): name of XML input file
        params (list): additional arguments
        baseline_error_regex (str): optional regex with which to match
            stderr content
"""
    config_path = os.path.join( FILES_DIR, config_name )
    xml_path = os.path.join( FILES_DIR, xml_name )

    with create_temp_dir() as temp_path:
      try:
        if os.path.exists( xml_path ):
          shutil.copy( xml_path, temp_path )

        cur_dir = os.getcwd()
        os.chdir( temp_path )

#               -- Execute
#               --
        run_args = [ VERARUN, '-c', config_path ]
        if params:
          run_args.extend( params )
        run_args.append( xml_name )

        test_output = subprocess.\
            check_output( run_args, stderr = subprocess.STDOUT )
#       if isinstance( test_output, bytes ):
#         test_output = test_output.decode( 'utf-8' )

      except subprocess.CalledProcessError as ex:
        test_output = ex.output
        if isinstance( test_output, bytes ):
          test_output = test_output.decode( 'utf-8' )
        self.assertIsNotNone(
            re.match( baseline_error_regex, test_output, re.DOTALL ),
            msg = tag + ': stderr'
            )

      finally:
        os.chdir( cur_dir )
    #end with temp_path
  #end run_fail_test


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunTests.run_multi_test()                   -
  #----------------------------------------------------------------------
  def run_multi_test(
      self, tag,
      config_name, xml_names,
      params, baseline_name, test_subdir = None,
      baseline_output_regex = None,
      baseline_error_regex = None
      ):
    """
    Args:
        tag (str): test message tag
        config_name (str): name of host configuration file
        xml_names (list(str)): names of XML input files
        params (list): additional arguments
        baseline_name (str): base name of baseline/expected PBS results
        test_subdir (str): optional subdir in which to find test PBS files
        baseline_output_regex (str): optional regex with which to match
            stdout content
        baseline_error_regex (str): optional regex with which to match
            stderr content
"""
    config_path = os.path.join( FILES_DIR, config_name )
    xml_paths = [ os.path.join( FILES_DIR, n ) for n in xml_names ]
    pbs_names = [ n.replace( '.xml', '.pbs' ) for n in xml_names ]
    fail_msg = None

    #with tempfile.TemporaryDirectory() as temp_path:
    with create_temp_dir() as temp_path:
      stderr_fp = None
      if not baseline_error_regex:
        stderr_fp = open( os.path.join( os.getcwd(), 'tests.err' ), 'at' )

      try:
        for n in xml_paths:
          shutil.copy( n, temp_path )

        cur_dir = os.getcwd()
        os.chdir( temp_path )

#               -- Execute
#               --
        run_args = [ VERARUN, '-c', config_path ]
        if params:
          run_args.extend( params )
        run_args.extend( xml_names )

        if baseline_error_regex:
          test_output = subprocess.\
              check_output( run_args, stderr = subprocess.STDOUT )
        else:
          test_output = subprocess.check_output( run_args, stderr = stderr_fp )
        if isinstance( test_output, bytes ):
          test_output = test_output.decode( 'utf-8' )

#               -- Check stdout
#               --
        if baseline_output_regex:
          self.assertIsNotNone(
              re.match( baseline_output_regex, test_output, re.DOTALL ),
              msg = tag + ': stdout'
              )
        elif baseline_error_regex:
          self.assertIsNotNone(
              re.match( baseline_error_regex, test_output, re.DOTALL ),
              msg = tag + ': stdout'
              )

#               -- Write baseline?
#               --
        for pbs_name in pbs_names:
          baseline_path = \
              os.path.join( BASELINES_DIR, baseline_name + '.' + pbs_name )
          test_path = \
              os.path.join( test_subdir, pbs_name )  if test_subdir else \
              pbs_name
          if not self._is_baseline_mode:
            if not os.path.exists( baseline_path ):
              fail_msg = 'baseline file not found: "{0}"'.format( baseline_path )
            elif not os.path.exists( test_path ):
              fail_msg = 'test result not found: "{0}"'.format( test_path )
            else:
              with open( baseline_path, 'rt' ) as base_fp:
                with open( test_path, 'rt' ) as test_fp:
                  base_content = base_fp.read()
                  test_content = test_fp.read()
              self.assertMultiLineEqual(
                  base_content, test_content,
                  msg = tag + ': PBS file ' + pbs_name
                  )

          elif os.path.exists( test_path ):
            shutil.copyfile( test_path, baseline_path )
        #end for pbs_name

      except subprocess.CalledProcessError as ex:
        self.fail( '{0}: exit code={1:d}'.format( tag, ex.returncode ) )

      finally:
        if stderr_fp is not None:
          stderr_fp.close()
        os.chdir( cur_dir )

      if fail_msg:
        self.fail( tag + ': ' + fail_msg )
    #end with temp_path
  #end run_multi_test


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunTests.run_output_test()                  -
  #----------------------------------------------------------------------
  def run_output_test(
      self, tag,
      config_name, params,
      baseline_output_regex = None,
      baseline_error_regex = None
      ):
    """
    Args:
        tag (str): test message tag
        config_name (str): name of host configuration file
        params (list): additional arguments
        baseline_output_regex (str): optional regex with which to match
            stdout content
        baseline_error_regex (str): optional regex with which to match
            stderr content
"""
    config_path = os.path.join( FILES_DIR, config_name )
    fail_msg = None

    #with tempfile.TemporaryDirectory() as temp_path:
    with create_temp_dir() as temp_path:
      stderr_fp = None
      if not baseline_error_regex:
        stderr_fp = open( os.path.join( os.getcwd(), 'tests.err' ), 'at' )

      try:
        cur_dir = os.getcwd()
        os.chdir( temp_path )

#               -- Execute
#               --
        run_args = [ VERARUN, '-c', config_path ]
        if params:
          run_args.extend( params )

        if baseline_error_regex:
          test_output = subprocess.\
              check_output( run_args, stderr = subprocess.STDOUT )
        else:
          test_output = subprocess.check_output( run_args, stderr = stderr_fp )
        if isinstance( test_output, bytes ):
          test_output = test_output.decode( 'utf-8' )

#               -- Check stdout
#               --
        if baseline_output_regex:
          self.assertIsNotNone(
              re.match( baseline_output_regex, test_output, re.DOTALL ),
              msg = tag + ': stdout'
              )
        elif baseline_error_regex:
          self.assertIsNotNone(
              re.match( baseline_error_regex, test_output, re.DOTALL ),
              msg = tag + ': stdout'
              )

      except subprocess.CalledProcessError as ex:
        self.fail( '{0}: exit code={1:d}'.format( tag, ex.returncode ) )

      finally:
        if stderr_fp is not None:
          stderr_fp.close()
        os.chdir( cur_dir )

      if fail_msg:
        self.fail( tag + ': ' + fail_msg )
    #end with temp_path
  #end run_output_test


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunTests.run_test()                         -
  #----------------------------------------------------------------------
  def run_test(
      self, tag,
      config_name, xml_name,
      params, baseline_fname, test_fname,
      baseline_output_regex = None,
      baseline_error_regex = None
      ):
    """
    Args:
        tag (str): test message tag
        config_name (str): name of host configuration file
        xml_name (str): name of XML input file
        params (list): additional arguments
        baseline_fname (str): name of baseline/expected results
        test_fname (str): relative path to PBS file resulting from the
            test
        baseline_output_regex (str): optional regex with which to match
            stdout content
        baseline_error_regex (str): optional regex with which to match
            stderr content
"""
    config_path = os.path.join( FILES_DIR, config_name )
    xml_path = os.path.join( FILES_DIR, xml_name )
    fail_msg = None

    #with tempfile.TemporaryDirectory() as temp_path:
    with create_temp_dir() as temp_path:
      stderr_fp = None
      if not baseline_error_regex:
        stderr_fp = open( os.path.join( os.getcwd(), 'tests.err' ), 'at' )

      try:
        shutil.copy( xml_path, temp_path )

        cur_dir = os.getcwd()
        os.chdir( temp_path )

#               -- Execute
#               --
        run_args = [ VERARUN, '-c', config_path ]
        if params:
          run_args.extend( params )
        run_args.append( xml_name )

        if baseline_error_regex:
          test_output = subprocess.\
              check_output( run_args, stderr = subprocess.STDOUT )
        else:
          test_output = subprocess.check_output( run_args, stderr = stderr_fp )
        if isinstance( test_output, bytes ):
          test_output = test_output.decode( 'utf-8' )

#               -- Check stdout
#               --
        if baseline_output_regex:
          self.assertIsNotNone(
              re.match( baseline_output_regex, test_output, re.DOTALL ),
              msg = tag + ': stdout'
              )
        elif baseline_error_regex:
          self.assertIsNotNone(
              re.match( baseline_error_regex, test_output, re.DOTALL ),
              msg = tag + ': stdout'
              )

#               -- Write baseline?
#               --
        baseline_path = os.path.join( BASELINES_DIR, baseline_fname )
        if not self._is_baseline_mode:
          if not os.path.exists( baseline_path ):
            fail_msg = 'baseline file not found: "{0}"'.format( baseline_fname )
          elif not os.path.exists( test_fname ):
            fail_msg = 'test result not found: "{0}"'.format( test_fname )
          else:
            with open( baseline_path, 'rt' ) as base_fp:
              with open( test_fname, 'rt' ) as test_fp:
                base_content = base_fp.read()
                test_content = test_fp.read()
            self.assertMultiLineEqual(
                base_content, test_content,
                msg = tag + ': PBS file'
                )

        elif os.path.exists( test_fname ):
          shutil.copyfile( test_fname, baseline_path )

      except subprocess.CalledProcessError as ex:
        self.fail( '{0}: exit code={1:d}'.format( tag, ex.returncode ) )

      finally:
        if stderr_fp is not None:
          stderr_fp.close()
        os.chdir( cur_dir )

      if fail_msg:
        self.fail( tag + ': ' + fail_msg )
    #end with temp_path
  #end run_test


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunTests.setUp()                            -
  #----------------------------------------------------------------------
  def setUp( self ):
    self._is_baseline_mode = os.environ.get( 'VeraRunTests_baseLineMode' )
    os.environ[ 'VeraRunTestsRootDir' ] = os.getcwd()
  #end setUp


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunTests.tearDown()                         -
  #----------------------------------------------------------------------
  def tearDown( self ):
    pass
  #end tearDown


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunTests.test0001_subdir_torque()           -
  #----------------------------------------------------------------------
  def test0001_subdir_torque( self ):
    self.run_test(
        #'test0001_subdir_torque',
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-s', 'test1', '-x' ],
        baseline_fname = 'test0001.pbs',
        test_fname = os.path.join( 'test1', 'p6.pbs' )
        )
  #end test0001_subdir_torque


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunTests.test0002_subdir_slurm()            -
  #----------------------------------------------------------------------
  def test0002_subdir_slurm( self ):
    self.run_test(
        #'test0002_subdir_slurm',
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = [ '-s', 'test1', '-x' ],
        baseline_fname = 'test0002.pbs',
        test_fname = os.path.join( 'test1', 'p6.pbs' )
        )
  #end test0002_subdir_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0003_job_id_pmem_nodes_ppn_version_torque()  -
  #----------------------------------------------------------------------
  def test0003_job_id_pmem_nodes_ppn_version_torque( self ):
    self.run_test(
        #'test0003_job_id_pmem_nodes_ppn_version_torque',
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = \
[ '-O', '-m', '40.5', '-n', '20', '--ppn', '2', '-v', 'vera-3.7.0' ],
        baseline_fname = 'test0003.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
  #end test0003_job_id_pmem_nodes_ppn_version_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0004_job_id_pmem_nodes_ppn_version_slurm()  -
  #----------------------------------------------------------------------
  def test0004_job_id_pmem_nodes_ppn_version_slurm( self ):
    self.run_test(
        #'test0004_job_id_pmem_nodes_ppn_version_slurm',
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = \
[ '-O', '-m', '40.5', '-n', '20', '--ppn', '2', '-v', 'vera-3.7.0' ],
        baseline_fname = 'test0004.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
  #end test0004_job_id_pmem_nodes_ppn_version_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0005_explicit_vera_dir_torque()        -
  #----------------------------------------------------------------------
  def test0005_explicit_vera_dir_torque( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = \
[
  '-O',
  '-d', os.path.join( os.getcwd(), 'files', 'vera_installs', 'vera-cs-3.8.0' ),
  '-m', '40.5', '-n', '20', '--ppn', '2'
],
        baseline_fname = 'test0005.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
  #end test0005_explicit_vera_dir_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0006_explicit_vera_dir_slurm()         -
  #----------------------------------------------------------------------
  def test0006_explicit_vera_dir_slurm( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = \
[
  '-O',
  '-d', os.path.join( os.getcwd(), 'files', 'vera_installs', 'vera-cs-3.8.0' ),
  '-m', '40.6', '-n', '20', '--ppn', '2'
],
        baseline_fname = 'test0006.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
  #end test0006_explicit_vera_dir_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0007_explicit_vera_dir_subdir_torque() -
  #----------------------------------------------------------------------
  def test0007_explicit_vera_dir_subdir_torque( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = \
[
  '-O',
  '-d', os.path.join( os.getcwd(), 'files', 'vera_installs', 'vera-cs-3.8.0' ),
  '-m', '40.5', '-n', '20', '--ppn', '2', '-s', 'mysub'
],
        baseline_fname = 'test0007.pbs',
        test_fname = os.path.join( 'mysub', 'p6.pbs' ),
        baseline_output_regex = '^\d+$'
        )
  #end test0007_explicit_vera_dir_subdir_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0008_explicit_vera_dir_subdir_slurm()  -
  #----------------------------------------------------------------------
  def test0008_explicit_vera_dir_subdir_slurm( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = \
[
  '-O',
  '-d', os.path.join( os.getcwd(), 'files', 'vera_installs', 'vera-cs-3.8.0' ),
  '-m', '40.5', '-n', '20', '--ppn', '2', '-s', 'mysub'
],
        baseline_fname = 'test0008.pbs',
        test_fname = os.path.join( 'mysub', 'p6.pbs' ),
        baseline_output_regex = '^\d+$'
        )
  #end test0008_explicit_vera_dir_subdir_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0009_explicit_vera_dir_env_nodes_ppn_torque() -
  #----------------------------------------------------------------------
  def test0009_explicit_vera_dir_env_nodes_ppn_torque( self ):
    os.environ[ 'VERA_DEFAULT_VERSION' ] = 'vera-cs-3.8.0'
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-O', '-m', '24', '-n', '10', '--ppn', '4'  ],
        baseline_fname = 'test0009.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
    del os.environ[ 'VERA_DEFAULT_VERSION' ]
  #end test0009_explicit_vera_dir_env_nodes_ppn_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0010_explicit_vera_dir_env_nodes_ppn_slurm() -
  #----------------------------------------------------------------------
  def test0010_explicit_vera_dir_env_nodes_ppn_slurm( self ):
    os.environ[ 'VERA_DEFAULT_VERSION' ] = 'vera-cs-3.8.0'
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = [ '-O', '-m', '24', '-n', '10', '--ppn', '4'  ],
        baseline_fname = 'test0010.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
    del os.environ[ 'VERA_DEFAULT_VERSION' ]
  #end test0010_explicit_vera_dir_env_nodes_ppn_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0011_explicit_vera_dir_env_ppn_torque() -
  #----------------------------------------------------------------------
  def test0011_explicit_vera_dir_env_ppn_torque( self ):
    os.environ[ 'VERA_DEFAULT_VERSION' ] = 'vera-cs-3.8.0'
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-O', '-m', '24', '--ppn', '8' ],
        baseline_fname = 'test0011.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
  #end test0011_explicit_vera_dir_env_ppn_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0012_explicit_vera_dir_env_ppn_slurm() -
  #----------------------------------------------------------------------
  def test0012_explicit_vera_dir_env_ppn_slurm( self ):
    os.environ[ 'VERA_DEFAULT_VERSION' ] = 'vera-cs-3.8.0'
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = [ '-O', '-m', '24', '--ppn', '8' ],
        baseline_fname = 'test0012.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
    del os.environ[ 'VERA_DEFAULT_VERSION' ]
  #end test0012_explicit_vera_dir_env_ppn_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0013_project_override_torque()         -
  #----------------------------------------------------------------------
  def test0013_project_override_torque( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-O', '-m', '30', '-p', 'bubba', '--ppn', '4' ],
        baseline_fname = 'test0013.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
  #end test0013_project_override_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0014_project_override_slurm()          -
  #----------------------------------------------------------------------
  def test0014_project_override_slurm( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = [ '-O', '-m', '30', '-p', 'bubba', '--ppn', '4' ],
        baseline_fname = 'test0014.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
  #end test0014_project_override_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0015_project_version_override_torque() -
  #----------------------------------------------------------------------
  def test0015_project_version_override_torque( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params =
[ '-O', '-m', '30', '-p', 'gump', '--ppn', '4', '-v', 'vera-cs-3.8.0' ],
        baseline_fname = 'test0015.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
  #end test0015_project_version_override_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0016_project_version_override_slurm() -
  #----------------------------------------------------------------------
  def test0016_project_version_override_slurm( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params =
[ '-O', '-m', '30', '-p', 'gump', '--ppn', '4', '-v', 'vera-cs-3.8.0' ],
        baseline_fname = 'test0016.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
  #end test0016_project_version_override_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0017_env_project_version_override_torque() -
  #----------------------------------------------------------------------
  def test0017_env_project_version_override_torque( self ):
    cur_value = os.environ.get( 'PBS_PROJECT' )
    os.environ[ 'PBS_PROJECT' ] = 'projeckein'

    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-O', '-m', '30', '--ppn', '4', '-v', 'vera-cs-3.8.0' ],
        baseline_fname = 'test0017.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )

    if cur_value:
      os.environ[ 'PBS_PROJECT' ] = cur_value
    else:
      del os.environ[ 'PBS_PROJECT' ]
  #end test0017_env_project_version_override_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0018_env_project_version_override_slurm() -
  #----------------------------------------------------------------------
  def test0018_env_project_version_override_slurm( self ):
    cur_value = os.environ.get( 'PBS_PROJECT' )
    os.environ[ 'PBS_PROJECT' ] = 'projeckein'

    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = [ '-O', '-m', '30', '--ppn', '4', '-v', 'vera-cs-3.8.0' ],
        baseline_fname = 'test0018.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )

    if cur_value:
      os.environ[ 'PBS_PROJECT' ] = cur_value
    else:
      del os.environ[ 'PBS_PROJECT' ]
  #end test0018_env_project_version_override_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0019_env_project_option_override_torque() -
  #----------------------------------------------------------------------
  def test0019_env_project_option_override_torque( self ):
    cur_value = os.environ.get( 'PBS_PROJECT' )
    os.environ[ 'PBS_PROJECT' ] = 'projeckein'

    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params =
[ '-O', '-m', '30', '-p', 'zwei', '--ppn', '4', '-v', 'vera-cs-3.8.0' ],
        baseline_fname = 'test0019.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )

    if cur_value:
      os.environ[ 'PBS_PROJECT' ] = cur_value
    else:
      del os.environ[ 'PBS_PROJECT' ]
  #end test0019_env_project_option_override_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0020_env_project_version_override_slurm() -
  #----------------------------------------------------------------------
  def test0020_env_project_option_override_slurm( self ):
    cur_value = os.environ.get( 'PBS_PROJECT' )
    os.environ[ 'PBS_PROJECT' ] = 'projeckein'

    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params =
[ '-O', '-m', '30', '-p', 'zwei', '--ppn', '4', '-v', 'vera-cs-3.8.0' ],
        baseline_fname = 'test0020.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )

    if cur_value:
      os.environ[ 'PBS_PROJECT' ] = cur_value
    else:
      del os.environ[ 'PBS_PROJECT' ]
  #end test0020_env_project_option_override_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0021_no_job_id_torque()                -
  #----------------------------------------------------------------------
  def test0021_no_job_id_torque( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params =
[ '-m', '30', '-p', 'zwei', '--ppn', '4', '-v', 'vera-cs-3.8.0' ],
        baseline_fname = 'test0021.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = ''
        )
  #end test0021_no_job_id_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0022_no_job_id_slurm()                -
  #----------------------------------------------------------------------
  def test0022_no_job_id_slurm( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params =
[ '-m', '30', '-p', 'zwei', '--ppn', '4', '-v', 'vera-cs-3.8.0' ],
        baseline_fname = 'test0022.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = ''
        )
  #end test0022_no_job_id_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0023_invalid_vera_dir()                -
  #----------------------------------------------------------------------
  def test0023_invalid_vera_dir( self ):
    self.run_error_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-v', 'vera-3.8.0' ],
        baseline_error_regex = '^Error: Invalid VERA directory:.*$'
        )
  #end test0023_invalid_vera_dir


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0024_default_version_not_found()       -
  #----------------------------------------------------------------------
  def test0024_default_version_not_found( self ):
    self.run_error_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-v', 'vera-3.6.0' ],
        baseline_error_regex = '^Error: Specified VERA default version not found:.*vera-3.6.0$'
        )
  #end test0024_default_version_not_found


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0025_memory_ppn_exceeds_torque()       -
  #----------------------------------------------------------------------
  def test0025_memory_ppn_exceeds_torque( self ):
    self.run_error_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-m', '164', '-n', '20', '--ppn', '2', '-v', 'vera-3.7.0' ],
        baseline_error_regex = '^Warning: Requested memory and ppn exceed machine per-node memory:.*$'
        )
  #end test0025_memory_ppn_exceeds_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0026_memory_ppn_exceeds_slurm()        -
  #----------------------------------------------------------------------
  def test0026_memory_ppn_exceeds_slurm( self ):
    self.run_error_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = [ '-m', '164', '-n', '20', '--ppn', '2', '-v', 'vera-3.7.0' ],
        baseline_error_regex = '^Warning: Requested memory and ppn exceed machine per-node memory:.*$'
        )
  #end test0026_memory_ppn_exceeds_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0027_too_much_memory_torque()          -
  #----------------------------------------------------------------------
  def test0027_too_much_memory_torque( self ):
    self.run_error_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-m', '164', '-n', '20', '--ppn', '2', '-v', 'vera-3.7.0' ],
        baseline_error_regex = '^Warning: Requested memory and ppn exceed machine per-node memory:.*Error: Error: Too much memory requested.*$'
        )
  #end test0027_too_much_memory_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0028_too_much_memory_slurm()          -
  #----------------------------------------------------------------------
  def test0028_too_much_memory_slurm( self ):
    self.run_error_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = [ '-m', '164', '-n', '20', '--ppn', '2', '-v', 'vera-3.7.0' ],
        baseline_error_regex = '^Warning: Requested memory and ppn exceed machine per-node memory:.*Error: Error: Too much memory requested.*$'
        )
  #end test0028_too_much_memory_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0029_set_job_name_torque()             -
  #----------------------------------------------------------------------
  def test0029_set_job_name_torque( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-N', 'myjob' ],
        baseline_fname = 'test0029.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = ''
        )
  #end test0029_set_job_name_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0030_set_job_name_slurm()              -
  #----------------------------------------------------------------------
  def test0030_set_job_name_slurm( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = [ '-N', 'myjob' ],
        baseline_fname = 'test0030.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = ''
        )
  #end test0030_set_job_name_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0031_uppercase_extension_torque()      -
  #----------------------------------------------------------------------
  def test0031_uppercase_extension_torque( self ):
    self.run_fail_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p18.XML',
        params = [ '-N', 'myjob' ],
        baseline_error_regex = '^.*Upper case filename extensions are not supported.*$'
        )
  #end test0031_uppercase_extension_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0032_uppercase_extension_slurm()      -
  #----------------------------------------------------------------------
  def test0032_uppercase_extension_slurm( self ):
    self.run_fail_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p18.XML',
        params = [ '-N', 'myjob' ],
        baseline_error_regex = '^.*Upper case filename extensions are not supported.*$'
        )
  #end test0032_uppercase_extension_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0033_no_job_id_torque()                -
  #----------------------------------------------------------------------
  def test0033_no_job_id_torque( self ):
    self.run_multi_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_names = [ 'p5.xml', 'p6.xml' ],
        params = [ '-s', 'test1' ],
        baseline_name = 'test0033',
        test_subdir = 'test1'
        )
  #end test0033_no_job_id_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0034_no_job_id_slurm()                 -
  #----------------------------------------------------------------------
  def test0034_no_job_id_slurm( self ):
    self.run_multi_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_names = [ 'p5.xml', 'p6.xml' ],
        params = [ '-s', 'test1' ],
        baseline_name = 'test0034',
        test_subdir = 'test1'
        )
  #end test0034_no_job_id_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0035_dependent_job_torque()            -
  #----------------------------------------------------------------------
  def test0035_dependent_job_torque( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p5.xml',
        params = [ '-N', 'testjob1', '-w', '123456' ],
        baseline_fname = 'test0035.pbs',
        test_fname = 'p5.pbs',
        baseline_error_regex = '^.*submitted job.*depend=123456.*$'
        )
  #end test0035_dependent_job_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0036_dependent_job_slurm()             -
  #----------------------------------------------------------------------
  def test0036_dependent_job_slurm( self ):
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p5.xml',
        params = [ '-N', 'testjob1', '-w', '123456' ],
        baseline_fname = 'test0036.pbs',
        test_fname = 'p5.pbs',
        baseline_error_regex = '^.*submitted job.*depend=123456.*$'
        )
  #end test0036_dependent_job_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0037_chain_torque()                    -
  #----------------------------------------------------------------------
  def test0037_chain_torque( self ):
    self.run_multi_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_names = [ 'p5.xml', 'p6.xml', 'p7.xml', 'p8.xml' ],
        params = [ '-w', '123456' ],
        baseline_name = 'test0037',
        baseline_error_regex = '^.*submitted job.*depend=123456.*$'
        )
  #end test0037_chain_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0038_chain_slurm()                     -
  #----------------------------------------------------------------------
  def test0038_chain_slurm( self ):
    self.run_multi_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_names = [ 'p5.xml', 'p6.xml', 'p7.xml', 'p8.xml' ],
        params = [ '-w', '123456' ],
        baseline_name = 'test0038',
        baseline_error_regex = '^.*submitted job.*depend=123456.*$'
        )
  #end test0038_chain_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0039_multi_job_named_torque()          -
  #----------------------------------------------------------------------
  def test0039_multi_job_named_torque( self ):
    self.run_multi_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_names = [ 'p5.xml', 'p6.xml', 'p7.xml', 'p8.xml' ],
        params = [ '-N', 'testing', '-e', 'bubba@nowhere.gov,leeroy@nowhere.com' ],
        baseline_name = 'test0039'
        )
  #end test0039_multi_job_named_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0040_multi_job_named_slurm()           -
  #----------------------------------------------------------------------
  def test0040_multi_job_named_slurm( self ):
    self.run_multi_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_names = [ 'p5.xml', 'p6.xml', 'p7.xml', 'p8.xml' ],
        params = [ '-N', 'testing', '-e', 'bubba@nowhere.gov,leeroy@nowhere.com' ],
        baseline_name = 'test0040'
        )
  #end test0040_multi_job_named_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0041_explicit_vera_builds_dir_torque() -
  #----------------------------------------------------------------------
  def test0041_explicit_vera_builds_dir_torque( self ):
    os.environ[ 'VERA_BUILDS' ] = os.path.\
        join( TEST_ROOT_DIR, 'files', 'vera_installs' )
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        xml_name = 'p6.xml',
        params = [ '-O', '-m', '24', '-n', '10', '--ppn', '4'  ],
        baseline_fname = 'test0041.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
    del os.environ[ 'VERA_BUILDS' ]
  #end test0041_explicit_vera_builds_dir_torque


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0042_explicit_vera_builds_dir_slurm()  -
  #----------------------------------------------------------------------
  def test0042_explicit_vera_builds_dir_slurm( self ):
    os.environ[ 'VERA_BUILDS' ] = os.path.\
        join( TEST_ROOT_DIR, 'files', 'vera_installs' )
    self.run_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'slurm-host.json',
        xml_name = 'p6.xml',
        params = [ '-O', '-m', '24', '-n', '10', '--ppn', '4'  ],
        baseline_fname = 'test0042.pbs',
        test_fname = 'p6.pbs',
        baseline_output_regex = '^\d+$'
        )
    del os.environ[ 'VERA_BUILDS' ]
  #end test0042_explicit_vera_builds_dir_slurm


  #----------------------------------------------------------------------
  #     METHOD: VeraRunTests.test0043_list_versions_torque()            -
  #----------------------------------------------------------------------
  def test0043_list_versions_torque( self ):
    self.run_output_test(
        inspect.currentframe().f_code.co_name,
        config_name = 'test-host.json',
        params = [ '-l' ],
        baseline_output_regex = 'Available VERA versions.*(?:vera-\\d\\.\\d\\.\\d\\W*)+'
        )
  #end test0043_list_versions_torque


#               -- Class Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         VeraRunTests.setUpClass()                       -
  #----------------------------------------------------------------------
  @classmethod
  def setUpClass( cls ):
    os.environ[ 'PATH' ] = SCRIPTS_DIR + ':' + os.environ[ 'PATH' ]
    os.environ[ 'PYTHONPATH' ] = PYTHON_PATH
  #end setUpClass


#               -- Static Methods
#               --

#end VeraRunTests


#------------------------------------------------------------------------
#       NAME:           main()                                          -
#------------------------------------------------------------------------
if __name__ == '__main__':
  #unittest.main()

  #suite = unittest.TestSuite()
  #suite.addTest( VeraRunTests( 'test_CalcGeneralAverage1' ) )

#  tests = [
#      'test_CalcGeneralAverage1DAxial',
#      'test_CalcGeneralAverage2DAssy',
#      'test_CalcGeneralAverage2DPin',
#      'test_CalcGeneralAverage3DAssy',
#      'test_CalcGeneralAverageScalar'
#      ]
#  suite = unittest.TestSuite( map( TestAverager, tests ) )

  suite = unittest.TestLoader().loadTestsFromTestCase( VeraRunTests )
  unittest.TextTestRunner( verbosity = 2 ).run( suite )
