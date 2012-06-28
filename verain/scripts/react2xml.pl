#!/usr/local/bin/perl

$MOTD=<<MOTD;
No, this is not the final version of the code. All the separate
files will be pulled into one package, and checks will be added as
we determine what is the actual input format.
There is minimal error checking. At this point this is a converter
for valid reactor input files into xml parameter list.
MOTD

use Getopt::Long;

my ($filename, $directory) = GetPaths();
sub GetPaths()
{
    use Cwd 'abs_path';
    use File::Basename;
    my $pscript=abs_path($0);
    my($filename, $directory) = fileparse($pscript);
    return ($filename, $directory);
}


my $pgnam=$filename;     # program name

# options
my ($VERBOSE,$HELP,$DEBUG);
{ # process options
    GetOptions(
	"verbose"   => \$VERBOSE,
	"debug"     => \$DEBUG,
	"help"      => \$HELP);
}

if($HELP || @ARGV < 2){
    die "Usage: $pgnam [options ...] reactor_file xml_file

options:
  --help
  --verbose

$MOTD
\n";
}

my ($ifile,$ofile)=@ARGV;

die "File $ifile $!\n" unless (-e $ifile);

@runit=(
    "${directory}phase1.pl $ifile --yml $ifile.yml",
    "${directory}testph2.pl 1 --debug 1 --db $ifile.yml",
    "${directory}tstreshuffle.pl ASSEMBLIES_dbg.yml ASSEMBLIES Assembly_ ASSEMBLIES_ddbg.yml",
    "${directory}tstreshuffle.pl DETECTORS_dbg.yml  DETECTORS  Detector_ DETECTORS_ddbg.yml",
    "${directory}tstreshuffle.pl INSERTS_dbg.yml    INSERTS    Insert_   INSERTS_ddbg.yml",
    "${directory}tstreshuffle.pl CONTROLS_dbg.yml   CONTROLS   Control_  CONTROLS_ddbg.yml",

    "${directory}tst2xml.pl ASSEMBLIES_ddbg.yml ASSEMBLIES ASSEMBLIES.xml",
    "${directory}tst2xml.pl DETECTORS_ddbg.yml  DETECTORS  DETECTORS.xml",
    "${directory}tst2xml.pl INSERTS_ddbg.yml    INSERTS    INSERTS.xml",
    "${directory}tst2xml.pl CONTROLS_ddbg.yml   CONTROLS   CONTROLS.xml",

    "${directory}tst2xml.pl STATE_dbg.yml      STATE      STATE.xml",
    "${directory}tst2xml.pl CORE_dbg.yml       CORE       CORE.xml",
    "${directory}tst2xml.pl DENOVO_dbg.yml     DENOVO     DENOVO.xml",
    "${directory}tst2xml.pl EDITS_dbg.yml      EDITS      EDITS.xml",
    "${directory}tst2xml.pl CASEID_dbg.yml     CASEID     CASEID.xml",

    "cp STATE_dbg.yml  STATE_ddbg.yml",
    "cp CORE_dbg.yml   CORE_ddbg.yml",
    "cp DENOVO_dbg.yml DENOVO_ddbg.yml",
    "cp EDITS_dbg.yml  EDITS_ddbg.yml",
    "cp CASEID_dbg.yml CASEID_ddbg.yml",

    "head -1 CASEID.xml > $ofile",
    "cat CORE.xml STATE.xml ASSEMBLIES.xml CONTROLS.xml DETECTORS.xml INSERTS.xml DENOVO.xml EDITS.xml >> $ofile",
    "tail -1 CASEID.xml >> $ofile"
    );

if (-e $ofile ){
    unlink $ofile;
}
foreach (@runit){
    print "Running ... $_\n" if $VERBOSE;
    $out=`$_`;
    print "$out"  if $VERBOSE;
#    system($_);
}

unless($DEBUG){
    @DBGF=( 
	"ASSEMBLIES",
	"DETECTORS",
	"INSERTS",
	"CONTROLS",
	"STATE",
	"CORE",
	"DENOVO",
	"EDITS",
	"CASEID" );

    print "rm $ifile.yml\n" if $VERBOSE;
    unlink("$ifile.yml");
    foreach $i (@DBGF){
	print "rm ${i}_dbg.yml ", "${i}_ddbg.yml", "\n"   if $VERBOSE;
	unlink "${i}_dbg.yml", "${i}_ddbg.yml"
    }
    foreach $i (@DBGF){
	print "rm ${i}.xml ", "${i}.xml", "\n"   if $VERBOSE;
	unlink "${i}.xml", "${i}.xml"
    }
}
