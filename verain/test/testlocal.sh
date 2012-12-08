#!/bin/bash
#
# Update 12/7/2012 - the command line parameters "--xml and --xslt" are no longer required, they are turned on by default
#


LIST="Sample_full_core Sample_p3 Sample_p3_mpact Sample_p3_unit_test Sample_p4a Sample_p4a_unit_test Sample_p4 Sample_p6a small_3x3rod_HFP small_3x3rod_HZP small_singlerod_HFP small_singlerod_HZP"

for CASE in $LIST; do
  echo "========================================"
  echo "    Running case $CASE"
  echo "========================================"
# ../scripts/react2xml.pl --xml --xslt $CASE.inp $CASE.xml
  ../scripts/react2xml.pl $CASE.inp $CASE.xml
  diff $CASE.xml.gold $CASE.xml
done

echo "finished"

