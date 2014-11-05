#!/bin/tcsh

# set printexitvalue

foreach i ( *.xml.gold )
    set l=`echo $i | sed 's/\.xml\.gold//'`
    if ( -e ${l}.inp ) then
	echo -n Checking ${l}.inp '... '
	if ( -e _${l}.xml ) then
	   echo _${l}.xml exists
	   exit 1
	endif
        ../scripts/react2xml.pl ${l}.inp _${l}.xml
        diff _${l}.xml  ${l}.xml.gold
	if ( $status ) then
           echo false
#           exit 2
	else
           echo ok
	endif
	rm _${l}.xml
    endif
end
    

