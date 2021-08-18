#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		verain_tests.py					-
#	HISTORY:							-
#		2017-07-19	leerw@ornl.gov				-
#------------------------------------------------------------------------
import json, os, sys, tempfile, traceback, unittest
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from verarun.verain import *


#------------------------------------------------------------------------
#	CLASS:		VeraInputXMLDocTests                            -
#------------------------------------------------------------------------
class VeraInputXMLDocTests( unittest.TestCase ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDocTests.setUp()			-
  #----------------------------------------------------------------------
  def setUp( self ):
    base_path = os.path.dirname( os.path.abspath( __file__ ) )
    self._baselineDir = os.path.join( base_path, 'baseline' )
    self._inputDir = os.path.join( base_path, 'input' )
  #end setUp


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDocTests.tearDown()			-
  #----------------------------------------------------------------------
  def tearDown( self ):
    pass
  #end tearDown


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDocTests.test_read1a()		-
  #----------------------------------------------------------------------
  def test_read1a( self ):
    test_fname = os.path.join( self._inputDir, '1a.xml' )
    assert os.path.exists( test_fname ), \
        'Test input not found: ' + test_fname

    doc = VeraInputXMLDoc( test_fname )
    #self.assertEqual( doc.find_assm_map(), [ '1' ] )
    self.assertEqual( doc.find_axial_mesh(), [ 1.0 ], 'axial_mesh' )
    self.assertEqual( doc.find_core_height(), 1.0, 'core_height' )
    self.assertEqual( doc.find_core_size(), 1, 'core_size' )
    self.assertEqual( doc.find_state_count(), 2, 'state_count' )

    nodes = doc.find_param_blocks( 'MPACT' )
    self.assertTrue( nodes is not None and len( nodes ) > 0, 'MPACT' )
    nodes = doc.find_param_blocks( 'MPACT', 'iteration_control' )
    self.assertTrue(
        nodes is not None and len( nodes ) > 0,
	'MPACT/iteration_control'
	)

    self.assertEqual( 
        doc.find_state_params( 'boron' ),
	[ 1300.0, 1300.0 ],
	'STATES/boron'
	)
    self.assertEqual( 
        doc.find_state_params( 'power' ),
	[ 0.0, 10.0 ],
	'STATES/power'
	)
    self.assertEqual( 
        doc.find_state_params( 'sym' ),
	[ 'qtr' ],
	'STATES/sym'
	)
  #end test_read1a

#end VeraInputXMLDocTests


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  #unittest.main()
  #suite = unittest.TestSuite()
  #suite.addTest( JobTests( 'test_CalcGeneralAverage1' ) )

#  tests = [ 'test_read1a', ]
#  suite = unittest.TestSuite( map( TestAverager, tests ) )

  suite = unittest.TestLoader().loadTestsFromTestCase( VeraInputXMLDocTests )
  unittest.TextTestRunner( verbosity = 2 ).run( suite )
