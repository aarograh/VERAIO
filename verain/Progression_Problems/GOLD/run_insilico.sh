#!/bin/bash

# Script to run all problem 1 and 2 cases on Fissile-4 machines with INSILICO

# **** This script currently does not work
# **** Andrew needs to add casl_comp to ini file
# **** and we need to specify different number of processors for problems 1 and 2

BUILD=/localhome/pmy/BUILDS/CHECKIN/MPI_DEBUG
 VERA=/localhome/pmy/VERA

# set executables
EXEC=$BUILD/SCALE/Exnihilo/packages/Insilico/neutronics/neutronics
VERADIFF=$BUILD/VERAInExt/verain/src/veradiff
PARSER=$VERA/VERAInExt/verain/scripts/react2xml.pl

export DATA=$VERA/SCALE/test_data

CLIST="1a 1b 1c 1d 1e 2a 2b 2c 2d 2e 2f 2g 2h 2i 2j 2k 2l 2m 2n 2o 2p 2q"
NCORE=1  

DATE1=$(date)

CASLCOMP=casl_comp_r2.sh5

#===================================
# Test everything
#===================================

if [ ! -f "$PARSER" ]; then
  echo $PARSER
  echo "ERROR: ASCII Input parser does not exist"
  exit 1
fi
if [ ! -f "$EXEC" ]; then
  echo "$EXEC"
  echo "ERROR: EXEC executable does not exist"
  exit 1
fi
if [ ! -f "$VERADIFF" ]; then
  echo "$VERADIFF"
  echo "ERROR: VERADIFF executable does not exist"
  exit 1
fi
if [ ! -d "$DATA" ]; then
  echo "$DATA"
  echo "ERROR: DATA directory does not exist"
  exit 1
fi

echo executable = $EXEC
echo data = $DATA

cp -f $DATA/$CASLCOMP .
if [ ! -f "$CASLCOMP" ]
then
   echo "ERROR: CASL Composition file $CASLCOMP does not exist."
   exit 2
fi


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

  # run EXEC 
  echo "============================================="
  echo "   Running EXEC Job on $NCORE cores"
  echo "============================================="
  mpirun -n $NCORE $EXEC -i $CASE.xml
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
  $VERADIFF $CASE.h5.EXEC.gold $CASE.h5

done


DATE2=$(date)

echo "Start  Date $DATE1"
echo "Finish Date $DATE2"
