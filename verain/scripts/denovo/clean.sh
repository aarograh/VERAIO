#!/bin/tcsh

egrep -v docString: assembly_test.yml | \
egrep -v id: | \
egrep -v isDefault: | \
egrep -v isUsed: | \
egrep -v type:
