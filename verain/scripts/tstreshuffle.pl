#!/usr/local/bin/perl

# use lib qw(./Packages);

my ($filename, $directory) = &GetPaths();
eval "use lib qw(${directory}Packages);
use YAMLUtil;
use KeyTree;
use REACTOR;
use PL;
use MiscUtils;";

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
# use File::Slurp;
use YAML;
use Clone qw(clone);

# use YAMLUtil;
# use KeyTree;
# use REACTOR;
# use PL;
# use MiscUtils;

my $pgnam=$0;     # program name

my $DEBUG=0;
my ($LOGFILE, $VERBOSE,$HELP);
{ # process options
    GetOptions("logfile=s" => \$LOGFILE,
	       "verbose"   => \$VERBOSE,
	       "debug=i"   => \$DEBUG,
               "help"      => \$HELP);
}

if($HELP || @ARGV < 1){
    die "Usage: $pgnam [options ...] yml_file

options:
  --logfile file
  --debug level
  --verbose
  --help
\n";
}

my ($ymlfile,$keyname,$reth_key,$outyml)=@ARGV;

$YAML::UseAliases=0;    # minimize references
$YAML::UseAliases=0;    # minimize references
($YML) = YAML::LoadFile( $ymlfile );
mergekeys_loop( $YML );

# open my($OFILE), '>', $outyml."_debug" or die "$0: $! $outyml._debug\n";
# print $OFILE Data::Dumper->Dump([$YML], [qw(YML)]);

&rethread($YML->{$keyname},$keyname,$reth_key);

YAML::DumpFile($outyml,$YML);

sub rethread {
    my ($ref,$keyname,$reth_key)=@_;
    my (@parents,@children);

    my %DIR=PLkeys($ref);
    foreach (keys %DIR){
	next if /^_/;
	if( /^$reth_key/ ){
	    push @parents, $_;
	}
	else{
	    push @children, $_;
	}
    }

    print "parents: @parents\n";
    print "children: @children\n";

    my %clones;
    my $ichild;
    foreach $ichild (@children){
	my $child_ref=$DIR{$ichild};
	my $child_copy_ref=clone($child_ref);
	PLdelete($ref,$ichild);
	$clone{$ichild}=$child_copy_ref;
    }

    foreach my $iparent (@parents){
	foreach $ichild (@children){
	    PLkeyon($DIR{$iparent},$clone{$ichild},$ichild);
	}
    }
}
