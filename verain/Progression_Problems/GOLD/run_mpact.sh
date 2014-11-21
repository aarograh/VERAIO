#!/bin/bash

# Script to run all problem 1 and 2 cases on Fissile-4 machines


BUILD=/localhome/pmy/BUILDS/CHECKIN/MPI_DEBUG
 VERA=/localhome/pmy/VERA

# set executables
MPACT=$BUILD/MPACT/MPACT_Drivers/examples/MPACT/MPACT.exe
VERADIFF=$BUILD/VERAInExt/verain/src/veradiff
PARSER=$VERA/VERAInExt/verain/scripts/react2xml.pl

export MPACT_DATA=$VERA/SCALE/test_data

CLIST="1a 1b 1c 1d 1e 2a 2b 2c 2d 2e 2f 2g 2h 2i 2j 2k 2l 2m 2n 2o 2p 2q"
NCORE=8  

DATE1=$(date)

#===================================
# Test everything
#===================================


if [ ! -f "$PARSER" ]; then
  echo $PARSER
  echo "ERROR: ASCII Input parser does not exist"
  exit 1
fi
if [ ! -f "$MPACT" ]; then
  echo "$MPACT"
  echo "ERROR: MPACT executable does not exist"
  exit 1
fi
if [ ! -f "$VERADIFF" ]; then
  echo "$VERADIFF"
  echo "ERROR: VERADIFF executable does not exist"
  exit 1
fi
if [ ! -d "$MPACT_DATA" ]; then
  echo "$MPACT_DATA"
  echo "ERROR: MPACT_DATA directory does not exist"
  exit 1
fi

echo executable = $MPACT
echo data = $MPACT_DATA

#===================================
# loop over cases
#===================================

for CASE in $CLIST; do

  echo "============================================="
  echo "  Running CASE = $CASE"
  echo "============================================="
  date

  # parse input 
  rm -f $CASE.xml
  perl $PARSER --init ../$CASE.inp $CASE.xml
  ls -l $CASE.xml
  date

  # run MPACT 
  echo "============================================="
  echo "   Running MPACT Job on $NCORE cores"
  echo "============================================="
  mpirun -n $NCORE $MPACT $CASE.xml
  date
done

#===================================
# Compare outputs
#===================================

for CASE in $CLIST; do
  echo "============================================="
  echo "  COMPARE CASE = $CASE"
  echo "============================================="

  diff  $CASE.xml.gold $CASE.xml
  $VERADIFF $CASE.h5.mpact.gold $CASE.h5

done


DATE2=$(date)

echo "Start  Date $DATE1"
echo "Finish Date $DATE2"
