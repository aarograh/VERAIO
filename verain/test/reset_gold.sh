#!/bin/tcsh

# set printexitvalue

foreach i ( *.xml.gold )
    set l=`echo $i | sed 's/\.xml\.gold//'`
    if ( -e ${l}.inp ) then
	echo -n Resetting XML file for ${l}.inp '... '
	if ( -e _${l}.xml ) then
	   echo _${l}.xml exists
	   exit 1
	endif
        ../scripts/react2xml.pl ${l}.inp _${l}.xml
	mv _${l}.xml $i
	echo done.
    endif
end
