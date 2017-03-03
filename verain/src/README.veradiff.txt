
9/6/2013

This directory contains a Fortran program used to compare two VERA HDF output files.

Right now, it only compares eigenvalues, but more tests will be added later.


=======================
  Compiling code
=======================

The program has a dependency on HDF.

An example commandline to compile the code is:

> h5fc -Wall -c veradiff.f90

where "h5fc" is the HDF wrapper for the Fortran compiler.



=======================
  To see if it works:
=======================

Compare two same HDF file to itself:

   [pmy@pu239 vera_all]$ ~/bin/veradiff.exe 2a.h5 2a.h5
   reading h5 file: 2a.h5
   reading h5 file: 2a.h5
    reading dataset: keff
    reading dataset: keff
    keff1  =   1.1819651
    keff2  =   1.1819651
    diff   =        0.00 pcm
    tol    =       10.00 pcm
    PASS - eigenvalue difference is less than tolerance
   [pmy@pu239 vera_all]$ echo $?
   0


Compare two different HDF files:

   [pmy@pu239 vera_all]$ ~/bin/veradiff.exe 2a.h5 2b.h5
   reading h5 file: 2a.h5
   reading h5 file: 2b.h5
    reading dataset: keff
    reading dataset: keff
    keff1  =   1.1819651
    keff2  =   1.1827832
    diff   =       81.81 pcm
    tol    =       10.00 pcm
    FAIL - eigenvalue difference exceeds tolerance
   [pmy@pu239 vera_all]$ echo $?
   1


The "reference" vera HDF files are in the directory $VERA/VERAInExt/verain/Progression_Problems/GOLD





