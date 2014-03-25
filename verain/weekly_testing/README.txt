
This directory contains input files to use with either Insilico or Insilico-CTF continuous/weekly testing

All sample input files should have the following:
  * input file     (*.inp)
  * gold XML file  (*.xml.gold)
  * gold HDF file  (*.h5.gold)

Once the files are placed in this directory, either add a line to the following 
CMAKE file to run an Insilico test:

  ...VERA/PSSDriversExt/VRIPSS/drivers/neutronics/CMakeLists.txt

or add a line to the following CMAKE file to run a coupled Insilico-CTF test:

  ...VERA/PSSDriversExt/VRIPSS/drivers/cobra_denovo/examples/CMakeLists.txt




