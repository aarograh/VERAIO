#!/bin/bash
#
# Update 12/7/2012 - the command line parameters "--xml and --xslt" are no longer required, they are turned on by default
# Update 4/08/2013 - automatically include all *.inp files in testing instead of explicitly listing
#

LIST=$(ls *inp)

for CASE in $LIST; do
  CASE=$(echo $CASE | sed 's/\.inp$//')
  echo "========================================"
  echo "    Running case $CASE"
  echo "========================================"
# ../scripts/react2xml.pl --xml --xslt $CASE.inp $CASE.xml
  ../scripts/react2xml.pl $CASE.inp $CASE.xml
  diff $CASE.xml.gold $CASE.xml
done

echo "finished"

