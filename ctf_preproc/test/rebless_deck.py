#!/bin/python

# This script re-blesses the ctf_regression preprocessor cases
# It generates the deck.inp file and replaces the old one

import os
import sys
import subprocess

if not len(sys.argv)==2:
   print 'You must specify xml2ctf executable path as an argument'
   print 'to the script.'
   exit(1)

preproc_path = sys.argv[1]

filename="modeling_plenums"
os.system(preproc_path+' --xmlfile='+filename+".xml.gold")
os.rename('deck.inp','../../../../../COBRA-TF/cobra_tf/test_matrix/preproc_regression/'+filename+'.inp')

filename="3x3_w_multistate"
os.system(preproc_path+' --xmlfile='+filename+".xml.gold")
os.rename('deck.inp','gold/'+filename+'.inp')

filename="mixing_coeff"
os.system(preproc_path+' --xmlfile='+filename+".xml.gold")
os.rename('deck.inp','gold/'+filename+'.inp')

filename="hdf5_convergence_edit"
os.system(preproc_path+' --xmlfile='+filename+".xml.gold")
os.rename('deck.inp','gold/'+filename+'.inp')

filename="test_cobra_edits"
os.system(preproc_path+' --xmlfile='+filename+".xml.gold")
os.rename('deck.inp','gold/'+filename+'.inp')
