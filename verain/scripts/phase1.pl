#!/usr/local/bin/perl

# use lib qw(./Packages);

my ($filename, $directory) = GetPaths();
eval "use lib qw(${directory}Packages);
use YAMLUtil;
use KeyTree;
use REACTOR;";

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
use Clone qw(clone);
use YAML;
use XML::Simple;

# use YAMLUtil;
# use KeyTree;
# use REACTOR;

# data structure with reactor file input commands
my $INPUT_DB;
# db of parsed reactor file
my $MAIN_DB;

my $pgnam=$0;     # program name

# options
# my ($filename, $directory) = GetPaths();
my $YMLSAVE;
my $XMLSAVE;
my $PLSAVE;
my $SCHEMA="${directory}Templates/Directory.yml";
my ($LOGFILE, $VERBOSE,$HELP);
{ # process options
    GetOptions("logfile=s" => \$LOGFILE,
	       "schema=s"  => \$SCHEMA,
	       "yml=s"     => \$YMLSAVE,
	       "xml=s"     => \$XMLSAVE,
	       "pl=s"      => \$PLSAVE,
	       "verbose"   => \$VERBOSE,
               "help"      => \$HELP);
}

if($HELP || @ARGV < 1){
    die "Usage: $pgnam [options ...] reactor_file

options:
  --logfile file
  --schema file
  --yml file
  --xml file
  --pl file
  --help
  --verbose
\n";
}

my ($ifile)=@ARGV;

# read configuration template for data structures
$YAML::UseAliases=0;    # minimize references
$YAML::UseAliases=0;    # minimize references
($INPUT_DB) = YAML::LoadFile( $SCHEMA );
mergekeys_loop( $INPUT_DB );

# set main directory tree for storage
my $dref=key_exists($INPUT_DB,'_DIRECTORY');
$MAIN_DB=clone($dref);

read_ascii($ifile,$INPUT_DB,$MAIN_DB,$VERBOSE);

# debug step
# save YAML of input tree
YAML::DumpFile($YMLSAVE,$MAIN_DB) if $YMLSAVE;
# save perl code of input tree
if($PLSAVE){
    open(OFILE,">$PLSAVE") || die "$pgnam: cannot open $PLSAVE.\n";
    print OFILE Data::Dumper->Dump([$MAIN_DB], [qw(MAIN_DB)]);
}
# save XML of input tree
XMLout($MAIN_DB, OutputFile => $XMLSAVE) if $XMLSAVE;

