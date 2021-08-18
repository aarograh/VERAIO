#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		job_tests.py					-
#	HISTORY:							-
#		2017-07-19	leerw@ornl.gov				-
#------------------------------------------------------------------------
import json, os, sys, tempfile, traceback, unittest
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from verarun.job.verajob import *


#------------------------------------------------------------------------
#	CLASS:		JobTests					-
#------------------------------------------------------------------------
class JobTests( unittest.TestCase ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		JobTests.setUp()				-
  #----------------------------------------------------------------------
  def setUp( self ):
    base_path = os.path.dirname( os.path.abspath( __file__ ) )
    self._baselineDir = os.path.join( base_path, 'baseline' )
    self._inputDir = os.path.join( base_path, 'input' )
  #end setUp


  #----------------------------------------------------------------------
  #	METHOD:		JobTests.tearDown()				-
  #----------------------------------------------------------------------
  def tearDown( self ):
    pass
  #end tearDown


  #----------------------------------------------------------------------
  #	METHOD:		JobTests.test_writeRoss1()			-
  #----------------------------------------------------------------------
  def test_writeRoss1( self ):
    test_fname = os.path.join( self._inputDir, 'ross1.json' )
    assert os.path.exists( test_fname ), \
        'Test input not found: ' + test_fname

    with open( test_fname, 'rt' ) as fp:
      params_json = json.load( fp )
    params = VeraJobParams( **params_json )

#		-- Execute, storing in temp file
#		--
    fd, name = tempfile.mkstemp( '.pbs' )
    os.close( fd )
    #VeraJobScript( 'ross.ornl.gov' ).write( params, name )
    VeraJobScript().write( params, name )
    with open( name, 'rt' ) as fp:
      test_content = fp.read()
    os.remove( name )

#		-- Create baseline?
#		--
    fname = os.path.join( self._baselineDir, 'ross1.pbs' )
    if not os.path.exists( fname ):
      with open( fname, 'wt' ) as fp:
        fp.write( test_content )

#		-- Load and compare with baseline
#		--
    else:
      with open( fname, 'rt' ) as fp:
        base_content = fp.read()
      self.assertEqual( base_content, test_content, 'ross1 script matches' )
  #end test_writeRoss1

#end JobTests


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  #unittest.main()
  #suite = unittest.TestSuite()
  #suite.addTest( JobTests( 'test_CalcGeneralAverage1' ) )

#  tests = [ 'test_writeRoss1', ]
#  suite = unittest.TestSuite( map( TestAverager, tests ) )

  suite = unittest.TestLoader().loadTestsFromTestCase( JobTests )
  unittest.TextTestRunner( verbosity = 2 ).run( suite )
