#!/bin/bash

LIST="Sample_full_core sample_input_pr2 Sample_p3 Sample_p4a Sample_p4 Sample_p6a small_3x3rod_HFP small_3x3rod_HZP"
#  sample_input_pr1

for CASE in $LIST; do
  echo "========================================"
  echo "    Running case $CASE"
  echo "========================================"
  ../scripts/react2xml.pl --xml --xslt $CASE.inp $CASE.xml
  diff $CASE.xml.gold $CASE.xml
done

echo "finished"

