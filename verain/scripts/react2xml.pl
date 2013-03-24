#!/usr/local/bin/perl

# use lib qw(./Packages);

#
# Dynamic path setting to accomodate vri repositories
#
my ($filename, $directory) = GetPaths();
eval "use lib qw(${directory}Packages);
use YAML;
use YAMLUtil;
use KeyTree;
use REACTOR;
use PL;
use XMLPack;
use ClonePP qw(clone);
use TypeUtils;";

sub GetPaths()
{
    use Cwd 'abs_path';
    use File::Basename;
    my $pscript=abs_path($0);
    my($filename, $directory) = fileparse($pscript);
    return ($filename, $directory);
}

#
# Standard Perl modules
#
use warnings ;
use Data::Dumper ;
use Getopt::Long;

#
# Data structure with reactor file input commands
# to initiate hash tree for the parsed input and
# to initiate subtrees
#
my $INPUT_DB;

#
# The resulting hash tree that contains parsed reactor
# input data
#
my $MAIN_DB;

my $pgnam=$0;                # program name
my @VERSION=('major'=>3,
	     'minor'=>1,
	     'date'=>10242012);

#
# Input schema to initiate INPUT_DB
#
my $SCHEMA="${directory}Templates/Directory.yml";
#
# Schemas for the format of the output blocks in PL
#
my @BLOCKS=('CASEID','STATE','CORE','ASSEMBLIES',
	    'CONTROLS','DETECTORS','INSERTS',
	    'INSILICO','EDITS','COBRATF','MPACT');
foreach $iblock (@BLOCKS){
    $SCHEMA_PL{$iblock} = "${directory}Templates/$iblock.yml";
}

#
# Rethreads
# PL for INSILICO requires repeating maps, axial, cells, etc
#
%RETHREAD=( 
    'ASSEMBLIES' => 'Assembly_',
    'CONTROLS'   => 'Control_',
    'INSERTS'    => 'Insert_',
    'DETECTORS'  => 'Detector_'
    );

# To have a bona fide XMl file
my $XML_HEADER='<?xml version="1.0" encoding="UTF-8"?>';

#
# Process the command line
#
my $DEBUG=0;
my ($VERBOSE,$HELP,$VERSION);
my $XML='on';
my $XSLT='on';
{ # process options
    GetOptions(
	"xml=s"     => \$XML,
	"xslt=s"    => \$XSLT,
	"verbose"   => \$VERBOSE,
	"debug"     => \$DEBUG,
	"version"   => \$VERSION,
	"help"      => \$HELP
	);
}
(&help_print() && exit) if $HELP;;
if($VERSION){
    print STDERR "@VERSION\n";
    exit;
}

# For formatted display in a browser.
my $XSLT_FILE='PL9.xsl';
if($XSLT ne 'on' && $XSLT ne 'off'){
   $XSLT_FILE=$XSLT; 
}
my $XSLT_HEADER="<?xml-stylesheet version=\"1.0\" type=\"text/xsl\" href=\"$XSLT_FILE\"?>";


if(@ARGV < 2){
    die "Usage: $pgnam [options ...] reactor_input_file output_xml_file
options:
  --xml=(on|off)
  --xslt=(on|off)
  --verbose
  --debug
  --version
  --help\n";
}

my ($ifile,$ofile)=@ARGV;

#
# Initiate configuration template for data structures
#
$YAML::UseAliases=0;    # minimize references
($INPUT_DB) = YAML::LoadFile( $SCHEMA );
# Clean up the inner references in the tree
# Need to fix
mergekeys_loop( $INPUT_DB );

#
# Initiate main directory tree for storage of input data
#
my $dref=key_exists($INPUT_DB,'_DIRECTORY');
$MAIN_DB=clone($dref);

#
# Turn on printing to STDERR in each of the packages
#
REACTOR->set_verbose()        if $VERBOSE;
REACTORBlock->set_verbose()   if $VERBOSE;
REACTORCommand->set_verbose() if $VERBOSE;
PL->set_verbose()             if $VERBOSE;
XMLPack->set_verbose()        if $VERBOSE;

#
# Read input file into main_db
#
read_ascii($ifile,$INPUT_DB,$MAIN_DB);

print STDERR "\nFile $ifile read.\n\n"    if $VERBOSE;
YAML::DumpFile("$ifile.dbg.yml",$MAIN_DB) if $DEBUG;

#
# Process data from MAIN_DB and store it to
# separate trees for each of the PL blocks
#

# Associate the MAIN_DB data with the PL package
# To be used for multiple blocks of the same name in the future
# Currently, setting the main database in the PL yml files is
# just a placeholder for multiple blocks
PL->set_sourcedb($MAIN_DB);
PL->dispatch();
$YAML::UseAliases=0;    # minimize references
foreach $iblock (@BLOCKS){

    # Initiate each block
    ($SCH_PL{$iblock}) = YAML::LoadFile( $SCHEMA_PL{$iblock} );
    mergekeys_loop( $SCH_PL{$iblock} );   # needs fix to eliminate

    # Process the block using commands in the block templates
    PLlist($SCH_PL{$iblock}->{$iblock});
    YAML::DumpFile("$iblock.dbg.yml",$SCH_PL{$iblock}) if $DEBUG;

    # Used for repeating information in the PL, lattices, cells and such
    if(exists($RETHREAD{$iblock})){
	# Gum up the tree
	rethread($SCH_PL{$iblock},$iblock,$RETHREAD{$iblock});
	YAML::DumpFile("$iblock.ddbg.yml",$SCH_PL{$iblock}) if $DEBUG;
    };
}

#
# XML output
#
open my($OFILE), '>', $ofile or die "$0: $! $ofile\n";

# Headers
unless($XML eq "off" && $XSLT eq "off"){
    print "Adding XML header ... $XML_HEADER\n" if $VERBOSE;
    print $OFILE "$XML_HEADER\n";
}
if($XSLT ne "off"){
    print "Adding XSLT header ... $XSLT_HEADER\n" if $VERBOSE;
    print $OFILE "$XSLT_HEADER\n";
}


# Select CASEID to be the root XML node
foreach $iblock (@BLOCKS){
    if($iblock eq 'CASEID'){
	packXMLlist($SCH_PL{$iblock}->{$iblock},$iblock,$OFILE,0,notclose=>1);
    }
    else{
	packXMLlist($SCH_PL{$iblock}->{$iblock},$iblock,$OFILE,1);
    }
}
# close the CASEID node
print $OFILE "</ParameterList>\n";

close $OFILE;

#
# User manual
#
sub help_print{
    print STDERR <<EOF

Converts reactor input file (reactor_input_file) into ParameterList
XML file (output_xml_file). ParameterList format is defined in
Trilinos Teuchos package http://trilinos.sandia.gov/packages/teuchos/

Program errors messages indicate errors in the input file. More
verbose diagnostic messages are currently being added.

Program switches:

--help    This help.

--xml=(on|off)
          Write XML declaration as the first line of the ParameterList
          XML file. Default=on.

--xslt=(on|off)
          Write XSLT processing instruction as the second line of the
          ParameterList XML file. Turns on --xml switch, as well. XSLT
          style file PL9.xsl should be in the same directory as the
          resulting ParameterListXML file in order for transofrmation
          to work in a browser. See additional information in
          "User-Friendly Formatting of VERA Input" on CASL
          Wiki. Default=on.

--verbose Add processing printouts as the code executes.

--debug   Create debug files for finding the errors in the converter
          program. Does not help much in tracing invalid input.

EOF
}
