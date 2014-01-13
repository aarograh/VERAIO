#!/bin/bash

#PBS -A nfi007pri
#PBS -l nodes=45 
#PBS -l walltime=00:30:00
#PBS -o p5.out
#PBS -N VERACS_Pr5-1
#PBS -l gres=widow1%widow2%widow3
#PBS -j oe
#PBS -m ea
#PBS -M agm@ornl.gov
#PBS -q batch

cd $PBS_O_WORKDIR
export HDF5_DISABLE_VERSION_CHECK=1
export MPICH_PTL_MATCH_OFF=1

build=/tmp/proj/nfi007/mbaird/VERA_062413_final
vera=$build/VERA

echo build=$build
echo  vera=$vera  

exe=$build/build/Exnihilo/packages/Insilico/neutronics/neutronics
inp=p5

date
echo job ID = $PBS_JOBID
echo mpi nodes = $PBS_NNODES
echo working directory = $PBS_O_WORKDIR
echo executable = $exe
echo

cp -f ../../casl_comp* .

pwd
rm -r $inp.xml

ls -l $inp.inp
echo parsing input....       
perl $vera/VERAInExt/verain/scripts/react2xml.pl $inp.inp $inp.xml

ls -l $inp.xml
ls -l $exe 

export DATA=$vera/SCALE/test_data
export SCALE=$vera/SCALE

aprun -n 720 $exe -i $inp.xml
date
