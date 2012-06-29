#!/bin/tcsh

set b=(CASEID CORE STATE ASSEMBLIES CONTROLS DETECTORS INSERTS DENOVO EDITS)

mkdir -p Parser_tests/pr3/XML
mkdir -p Parser_tests/pr3/YAML

cp Sample_p3.inp Parser_tests/pr3/Sample_p3.inp.txt
foreach ib ($b)
  set iby="${ib}_ddbg.yml"
  set ibx="${ib}.xml"

  cp $iby Parser_tests/pr3/YAML/
  cp $ibx Parser_tests/pr3/XML/
end

cp Sample_p3.xml Parser_tests/pr3/XML/Sample_p3.xml
