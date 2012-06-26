#!/bin/tcsh

set b=(CASEID CORE STATE ASSEMBLIES CONTROLS DETECTORS INSERTS DENOVO EDITS)

cp pr4.inp Parser_tests/pr4/pr4.inp.txt
foreach ib ($b)
  set iby="${ib}_ddbg.yml"
  set ibx="${ib}.xml"

  cp $iby Parser_tests/pr4/YAML/
  cp $ibx Parser_tests/pr4/XML/
end

cp RINPUT.xml Parser_tests/pr4/XML/PROBLEM4.xml
