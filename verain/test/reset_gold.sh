#!/bin/tcsh

set t=`egrep 'ADD_REACTOR_AWARE_INPUT_PARSER_TEST\(' CMakeLists.txt | sed 's/ADD_REACTOR_AWARE_INPUT_PARSER_TEST//g' | sed 's/[()]//g'`
# Sample_full_core_fuelmix 


foreach i ($t)
    echo ../scripts/react2xml.pl $i.inp $i.xml.gold
    ../scripts/react2xml.pl $i.inp $i.xml.gold
    if (-e $i.xml) rm $i.xml
end

