#!/usr/local/bin/perl

# use lib qw(./Packages);

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

# Perl modules
use warnings ;
use Data::Dumper ;
use Getopt::Long;
# use Clone qw(clone);
# use YAML;

# data structure with reactor file input commands
my $INPUT_DB;
# db of parsed reactor file
my $MAIN_DB;

my $pgnam=$0;     # program name

# input schema
my $SCHEMA="${directory}Templates/Directory.yml";
# output schemas
my @BLOCKS=('CASEID','STATE','CORE','ASSEMBLIES','CONTROLS','DETECTORS','INSERTS','DENOVO','EDITS');
foreach $iblock (@BLOCKS){
    $SCHEMA_PL{$iblock} = "${directory}Templates/$iblock.yml";
}

# rethreads
%RETHREAD=( 
    'ASSEMBLIES' => 'Assembly_',
    'CONTROLS'   => 'Control_',
    'INSERTS'    => 'Insert_',
    'DETECTORS'  => 'Detector_'
    );

$XML_HEADER='<?xml version="1.0" encoding="UTF-8"?>';
$XSLT_HEADER='<?xml-stylesheet version="1.0" type="text/xsl" href="PL9.xsl"?>';

my $DEBUG=0;
my ($LOGFILE, $VERBOSE,$HELP,$XML,$XSLT);
{ # process options
    GetOptions("logfile=s" => \$LOGFILE,
	       "schema=s"  => \$SCHEMA,
	       "xml"       => \$XML,
	       "xslt"      => \$XSLT,
	       "verbose"   => \$VERBOSE,
	       "debug"   => \$DEBUG,
               "help"      => \$HELP);
}

if($HELP || @ARGV < 2){
    die "Usage: $pgnam [options ...] reactor_input_file output_xml_file

options:
  --logfile file
  --schema file
  --xml
  --xslt
  --verbose
  --debug
  --help
\n";
}

my ($ifile,$ofile)=@ARGV;

# read configuration template for data structures
$YAML::UseAliases=0;    # minimize references
($INPUT_DB) = YAML::LoadFile( $SCHEMA );
mergekeys_loop( $INPUT_DB );

# set main directory tree for storage
my $dref=key_exists($INPUT_DB,'_DIRECTORY');
$MAIN_DB=clone($dref);

REACTOR->set_verbose()        if $VERBOSE;
REACTORBlock->set_verbose()   if $VERBOSE;
REACTORCommand->set_verbose() if $VERBOSE;
PL->set_verbose()             if $VERBOSE;
XMLPack->set_verbose()        if $VERBOSE;

# ------ read input into db

read_ascii($ifile,$INPUT_DB,$MAIN_DB);

print STDERR "\nFile $ifile read.\n\n" if $VERBOSE;
YAML::DumpFile("$ifile.dbg.yml",$MAIN_DB) if $DEBUG;

# ------ phase 2

PL->set_sourcedb($MAIN_DB);
$YAML::UseAliases=0;    # minimize references
foreach $iblock (@BLOCKS){
    ($SCH_PL{$iblock}) = YAML::LoadFile( $SCHEMA_PL{$iblock} );
    mergekeys_loop( $SCH_PL{$iblock} );
    PLlist($SCH_PL{$iblock}->{$iblock});
    YAML::DumpFile("$iblock.dbg.yml",$SCH_PL{$iblock}) if $DEBUG;

    if(exists($RETHREAD{$iblock})){
	rethread($SCH_PL{$iblock},$iblock,$RETHREAD{$iblock});
	YAML::DumpFile("$iblock.ddbg.yml",$SCH_PL{$iblock}) if $DEBUG;
    };
}

# ------ xml

open my($OFILE), '>', $ofile or die "$0: $! $ofile\n";
if($XML){
    print "Adding XML header ... $XML_HEADER\n" if $VERBOSE;
    print $OFILE "$XML_HEADER\n";
}
if($XSLT){
    print "Adding XSLT header ... $XSLT_HEADER\n" if $VERBOSE;
    print $OFILE "$XSLT_HEADER\n";
}

foreach $iblock (@BLOCKS){
    if($iblock eq 'CASEID'){
	packXMLlist($SCH_PL{$iblock}->{$iblock},$iblock,$OFILE,0,notclose=>1);
    }
    else{
	packXMLlist($SCH_PL{$iblock}->{$iblock},$iblock,$OFILE,1);
    }
}
print $OFILE "</ParameterList>\n";

close $OFILE;
