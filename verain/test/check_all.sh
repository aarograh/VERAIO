#!/bin/tcsh

set t=`egrep 'ADD_REACTOR_AWARE_INPUT_PARSER_TEST\(' CMakeLists.txt | sed 's/ADD_REACTOR_AWARE_INPUT_PARSER_TEST//g' | sed 's/[()]//g'`

foreach i ($t)
   echo $i
 #   ../scripts/react2xml.pl $i.inp $i.xml.gold; rm $i.xml
    ../scripts/react2xml.pl $i.inp $i.xml
    diff $i.xml  $i.xml.gold
end

