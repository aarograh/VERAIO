#!/usr/local/bin/perl

use lib qw(./);

use String::Approx 'amatch';

@inputs=('power','flow','rods','xenon','sym','boron','search','cycle');

my @matches = amatch($ARGV[0], @inputs);

print "$ARGV[0] matches @matches\n";

# my @catches = amatch("plugh", ['2'], @inputs);

