#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		verain.py					-
#	HISTORY:							-
#		2018-07-16	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, os, re, six, socket, sys
from datetime import datetime
#from xml.dom import *
#from xml.dom.minidom import parse, parseString, Document
#import xpath
import xml.etree.ElementTree as ET

import pdb


#NS_vera = 'uid:xxx'
#NSDICT_all = \
#  {
#  'app': NS_app,
#  'atom': NS_atom,
#  'georss': NS_georss,
#  'pml': NS_pml,
#  'sp': NS_sp
#  }

FLOAT_KEYS = set([ 'walltime' ])

INT_KEYS = set([ 'pmem', 'ppn' ])


#------------------------------------------------------------------------
#	CLASS:		VeraInput					-
#------------------------------------------------------------------------
class VeraInput( dict ):
  """
"""

  MSG_excoreError = """
Error: For excore transport in forward mode, you must specify nprocs"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VeraInput.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, fpath = None ):
    """
    Args:
        fpath (str): path to inp file, if None, must call `read()`.
"""
    self._logger = logging.getLogger( 'root' )

    if fpath:
      self.read( fpath )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VeraInput.read()				-
  #----------------------------------------------------------------------
  def read( self, fpath ):
    """
    Args:
        fpath (str): path to inp file
"""
    assert os.path.exists( fpath ), 'File not found: "{0}"'.format( fpath )

#		-- Read until [RUN] block
#		--
    with open( fpath, 'rt' ) as fp:
      line = fp.readline()
      in_block = False
      while line:
        line = line.rstrip( '\r\n' ).lstrip( '\t ' )
        if line.find( '[RUN]' ) == 0:
	  in_block = True
	elif in_block:
	  if line.find( '[' ) == 0:
	    break
	  elif in_block and len( line ) > 0:
	    tokens = re.split( '\s+', line )
	    if len( tokens ) >= 2:
	      try:
	        self[ tokens[ 0 ] ] = \
	            float( tokens[ 1 ] )  if tokens[ 0 ] in FLOAT_KEYS else \
	            int( tokens[ 1 ] )  if tokens[ 0 ] in INT_KEYS else \
	            tokens[ 1 ]
	      except Exception as ex:
	        self.logger.exception( ex )
	#end elif in_block:

        line = fp.readline()
      #end while line
    #end with open( fpath, 'rt' ) as fp
  #end read

#end VeraInput


#------------------------------------------------------------------------
#	CLASS:		VeraInputXMLDoc					-
#------------------------------------------------------------------------
class VeraInputXMLDoc( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, fpath = None ):
    """
    Args:
        fpath (str): path to XML file, if None, must call `read()`.
"""
    self._logger = logging.getLogger( 'root' )
    self._document = None

    if fpath:
      self.read( fpath )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc._extract_attr_value()		-
  #----------------------------------------------------------------------
  def _extract_attr_value( self, node, expr = None ):
    """
    Args:
	node (xml.etree.ElementTree.Element): element from which to
	    extract the value
        expr (str): xpath expression to apply ``node``, or None to use
	    the ``node`` itself
    Returns:
        int,double,list,str: depending on 'type' attribute, or None if
	    not found
"""
    value = None
    if node is not None and expr:
      nodes = node.findall( expr )
      node = nodes[ 0 ]  if nodes else  None

    if node is not None:
      try:
	value_type = node.attrib.get( 'type', '' )
	value_str = node.attrib.get( 'value', '' )
	if value_type == 'double':
	  value = float( value_str )
	elif value_type == 'int':
	  value = int( value_str )
	elif value_type == 'Array(double)':
	  value = [ float( x ) for x in value_str[ 1 : -1 ].split( ',' ) ]
	elif value_type == 'Array(int)':
	  value = [ int( x ) for x in value_str[ 1 : -1 ].split( ',' ) ]
	elif value_type == 'Array(string)':
	  value = value_str[ 1 : -1 ].split( ',' )
	else:
	  value = value_str
      except Exception as ex:
        self._logger.exception( ex )

    return  value
  #end _extract_attr_value


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.find_assm_map()			-
  #----------------------------------------------------------------------
  def find_assm_map( self ):
    """
    Returns:
	list(int): None if not found
"""
    assert self._document is not None, 'No document'
    result = self._extract_attr_value(
	self._document.getroot(),
	expr = 'ParameterList[@name="CORE"]/Parameter[@name="assm_map"]'
        )
    return  result
  #end find_assm_map


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.find_axial_mesh()		-
  #----------------------------------------------------------------------
  def find_axial_mesh( self ):
    """
    Returns:
	list(float): None if not found
"""
    assert self._document is not None, 'No document'
    result = self._extract_attr_value(
	self._document.getroot(),
	'ParameterList[@name="MPACT"]' +
	'/ParameterList[@name="mesh"]' +
	'/Parameter[@name="axial_mesh"]'
        )
    return  result
  #end find_axial_mesh


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.find_core_height()		-
  #----------------------------------------------------------------------
  def find_core_height( self ):
    """
    Returns:
        float: core height in cm, None if not found
"""
    assert self._document is not None, 'No document'
    result = self._extract_attr_value(
	self._document.getroot(),
	'ParameterList[@name="CORE"]/Parameter[@name="height"]'
        )
    return  result
  #end find_core_height


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.find_core_size()		-
  #----------------------------------------------------------------------
  def find_core_size( self ):
    """
    Returns:
        int: core size, None if not found
"""
    assert self._document is not None, 'No document'
    result = self._extract_attr_value(
	self._document.getroot(),
	'ParameterList[@name="CORE"]/Parameter[@name="core_size"]'
        )
    return  result
  #end find_core_size


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.find_files()			-
  #----------------------------------------------------------------------
  def find_files( self, card_name ):
    """xxxxx Need an example.
    Args:
        card_name (str): name of input param
    Returns:
	list(str): list of filenames
"""
    assert self._document is not None, 'No document'

    result = None
    expr = 'ParameterList[@name="RESTART"]/Parameter[@name="{0}"]'.\
        format( card_name )
    nodes = self._document.getroot().findall( expr )
    if nodes:
      result = list( filter(
	  lambda x : len( x ) > 0,
	  [ node.attrib.get( 'value', '' ) for n in nodes ]
          ) )

    return  result
  #end find_files


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.find_param_blocks()		-
  #----------------------------------------------------------------------
  def find_param_blocks( self, *names ):
    """Finds the ParameterList blocks matching the name attribute
values in hierarchical order.
    Args:
        *names: block name attribute values in order
    Returns:
	list(xml.etree.ElementTree.Element): matching elements
"""
    assert self._document is not None, 'No document'
    result = None
    if names:
      expr = ''
      for name in names:
	if len( expr ) > 0:
	  expr += '/'
        expr += 'ParameterList[@name="{0}"]'.format( name )

      result = self._document.getroot().findall( expr )

    return  result
  #end find_param_blocks


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.find_run_params()		-
  #----------------------------------------------------------------------
  def find_run_params( self ):
    """
    Returns:
	dict: parameters in the RUN block (email, pmem, ppn, walltime)
"""
    assert self._document is not None, 'No document'

    params = {}

    nodes = self._document.getroot().\
        findall( 'ParameterList[@name="RUN"]/Parameter' )
    if nodes:
      for node in nodes:
        name = node.attrib.get( 'name' )
	val = self._extract_attr_value( node )
	if val and val != 'default':
	  params[ name ] = self._extract_attr_value( node )
    #end if nodes

#               -- nprocs not specified?
#               --
    if params.get( 'nprocs', 0 ) == 0:
#		        -- Calculate MPACT nprocs
#		        -- (MPACT/MPACT_exe/src/MPACT_get_ncore.f90)
      nodes = self._document.getroot().\
findall( 'ParameterList[@name="MPACT"]/ParameterList[@name="parallel_env"]' )
      if nodes:
        nprocs = None
        for name in ( 'num_angle', 'num_energy', 'num_space', 'num_threads' ):
	  expr = 'Parameter[@name="{0}"]'.format( name )
          val = self._extract_attr_value( nodes[ 0 ], expr = expr )
	  if val:
	    if nprocs is None:
	      nprocs = abs( val )
	    else:
	      nprocs *= abs( val )
        if nprocs is not None:
          params[ 'nprocs' ] = nprocs
      #end if nodes

#		        -- Add for Shift
#		        --
      excore_values = self.find_state_params( 'excore_transport' )
      if excore_values and 'on' in excore_values:
        problem_mode = self._extract_attr_value(
            self._document.getroot(),
expr = 'ParameterList[@name="SHIFT"]/Parameter[@name="problem_mode"]'
            )
        incr = 1
        cadis = 'cadis' == problem_mode
        nodes = None
        if cadis:
          nodes = self._document.getroot().findall(
  'ParameterList[@name="SHIFT"]/ParameterList[@name="hybrid_db"]/Parameter'
              )
        if nodes:
          for node in nodes:
            name = node.attrib.get( 'name' )
            if name in ( 'num_blocks_i', 'num_blocks_j' ):
              val = self._extract_attr_value( node )
              incr *= val
          #end for node in nodes

        nprocs = params.get( 'nprocs', 0 )
        nprocs += incr
        params[ 'nprocs' ] = nprocs
      #end if 'on' in excore_values
    #end if params.get( 'nprocs', 0 ) == 0

    return  params
  #end find_run_params


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.find_shift_param()		-
  #----------------------------------------------------------------------
  def find_shift_param( self, name ):
    """Retrieves the parameter value from the SHIFT ParameterList
    Args:
        name (str): parameter name
    Returns:
        int,double,list,str: depending on 'type' attribute, or None if
	    not found
"""
    assert self._document is not None, 'No document'

    result = None
    expr = \
        'ParameterList[@name="SHIFT"]/Parameter[@name="{0}"]'.\
	format( name )
    nodes = self._document.getroot().findall( expr )
    if nodes:
      result = self._extract_attr_value( nodes[ 0 ] )

    return  result
  #end find_shift_param


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.find_state_count()		-
  #----------------------------------------------------------------------
  def find_state_count( self ):
    """
    Returns:
        int: number of states or None if no STATES found
"""
    assert self._document is not None, 'No document'

    count = None
    nodes = self._document.getroot().\
        findall( 'ParameterList[@name="STATES"]/ParameterList' )
    if nodes:
      count = len( nodes )

    return  count
  #end find_state_count


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.find_state_params()		-
  #----------------------------------------------------------------------
  def find_state_params( self, name ):
    """Retrieves the parameter values for each state
    Args:
        name (str): parameter name
    Returns:
	list: values for each state or None if not found
"""
    assert self._document is not None, 'No document'

    result = None
    expr = \
        'ParameterList[@name="STATES"]/ParameterList/Parameter[@name="{0}"]'.\
	format( name )
    nodes = self._document.getroot().findall( expr )
    if nodes:
      result = []
      for n in nodes:
	result.append( self._extract_attr_value( n ) )

    return  result
  #end find_state_params


  #----------------------------------------------------------------------
  #	METHOD:		VeraInputXMLDoc.read()				-
  #----------------------------------------------------------------------
  def read( self, fpath ):
    """Sets the `document` property.
    Args:
        fpath (str): path to XML file
"""
    assert os.path.exists( fpath ), 'File not found: "{0}"'.format( fpath )
    self._document = ET.parse( fpath )
  #end read


#		-- Properties
#		--


  document = property( lambda x: x._document )
  """XML Document after input parse"""

  logger = property( lambda x: x._logger )
  """Logger instance"""

#end VeraInputXMLDoc
