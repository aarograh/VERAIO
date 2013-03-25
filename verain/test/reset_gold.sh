#!/bin/tcsh

set t=(Sample_full_core_maps \
Sample_full_core_matmix \
Sample_full_core_reflector \
Sample_full_core_wsym_assm_even \
Sample_full_core_wsym \
Sample_full_core \
Sample_p3_mpact \
Sample_p3_unit_test \
Sample_p3 \
Sample_p4a_unit_test \
Sample_p4a \
Sample_p4_mpact \
Sample_p4 \
Sample_p6a \
small_3x3rod_HFP \
small_3x3rod_HZP \
small_singlerod_HFP \
small_singlerod_HZP_no_spacers \
small_singlerod_HZP )
# Sample_full_core_fuelmix 


foreach i ($t)
   echo $i
    ../scripts/react2xml.pl $i.inp $i.xml.gold; rm $i.xml
end

