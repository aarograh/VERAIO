#!/bin/python

# This script re-blesses the ctf_regression preprocessor cases
# It generates the deck.inp file and replaces the old one

import os
import sys
import subprocess

filenames=['3x3_w_multistate',
           'mixing_coeff',
           'hdf5_convergence_edit',
           'modeling_plenums',
           'Sample_p6a_parallel',
           'bypass',
           'case5-00',
           'case5-01',
           'case5-02',
           'case5-03',
           'case5-04',
           'case5-05',
           'case5-06',
           'case5-07',
           'case5-08',
           'case5-09',
           'case5-10',
           'case5-11',
           'case5-12',
           'case5-13',
           'case5-14',
           'case5-15',
           'case5-16',
           'case5-17',
           'iapws_singlerod',
           'rotational_5cross',
           'stacked_singlerod_HFP',
           'test_cobra_edits',
           'inlet_temp',
           'inlet_flow',
           'inlet_bc_rot_sym',
           'Sample_qtr_core_inlet_bc',
           'w3_correlation']

verain_filenames=[
      'cross_w_baffle',
      'small_singlerod_HFP',
      'small_3x3rod_HFP',
      'Sample_p6a_multifuel',
      'small_3x3rod_HFP_2fuel',
      'small_5cross_assem_3x3rod_HFP',
      'small_qtr_core_3x3rod_HFP',
      'chen_3x3',
      'small_3x3rod_IFBA',
      'small_3x3rod_BProd',
      'grid_enhance',
      'VTK_on',
      'four_grid_types']
      

partests=['Sample_p7',
      'par_qtr_core_inlet_bc',
      'par_cross']

parfiles=[56,
      56,
      5]


if not len(sys.argv)==2:
   print('You must specify xml2ctf executable path as an argument')
   print('to the script.')
   exit(1)

preproc_path = sys.argv[1]

for name in filenames:
   print('===========================================================')
   print('Reblessing '+name)
   print('===========================================================')
   os.system(preproc_path+' --xmlfile='+name+".xml.gold")
   os.rename('deck.inp','gold/'+name+'.inp')

for name in verain_filenames:
   os.system('cp ../../test/'+name+'.xml.gold .')
   os.system(preproc_path+' --xmlfile='+name+".xml.gold")
   os.rename('deck.inp','gold/'+name+'.inp')

# loop over the cases with parallel output files
for index, name in enumerate(partests):

   print('===========================================================')
   print('Running: '+name)

   os.system(preproc_path+' --xmlfile='+name+".xml.gold")
   numfiles = parfiles[index]
   for n in range(numfiles):
       suffix = '.'+str(numfiles)+'.'+str(n+1)+'.inp'
       fname = 'pdeck'+suffix
       os.system('mv '+fname+' ./gold/'+name+suffix)
   os.system('mv pmaster.inp gold/'+name+'.master.inp')
