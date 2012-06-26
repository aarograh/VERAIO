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

my ($ymlfile,$keyname,$outXML)=@ARGV;

$YAML::UseAliases=0;    # minimize references
$YAML::UseAliases=0;    # minimize references
($YML) = YAML::LoadFile( $ymlfile );
mergekeys_loop( $YML );

open my($OFILE), '>', $outXML or die "$0: $! $outXML\n";
# print $OFILE Data::Dumper->Dump([$YML], [qw(YML)]);

&packXMLlist($YML->{$keyname},$keyname,$OFILE,0);

sub packXMLparameter {
    my ($ref,$name,$phandle,$Nindent,%userparam)=@_;

    my %OPTIONS=('indent'=>'  ');
    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my $data=read_off_label($ref,'_content');
    my $type=read_off_label($ref,'_type');

    if(defined($data)){
	my $indent=$OPTIONS{indent} x $Nindent;
	print $phandle "$indent<Parameter name=\"$name\" type=\"$type\" value=\"$data\"/>\n";
    }
}

sub packXMLarray {
    my ($ref,$name,$phandle,$Nindent,%userparam)=@_;
    local $" = ',';

    my %OPTIONS=('indent'=>'  ');
    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my $data=read_off_label($ref,'_content');
    my $type=read_off_label($ref,'_type');
    if($data){
	my @data=@{ $data };
	my $indent=$OPTIONS{indent} x $Nindent;
	print $phandle "$indent<Parameter name=\"$name\" type=\"Array($type)\" value=\"{@data}\"/>\n";
    }
}

sub packXMLlist {
    my ($ref,$name,$phandle,$Nindent,%userparam)=@_;

    my %OPTIONS=('indent'=>'  ');
    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my $nameupd=PLname($ref);
    if(defined($nameupd)){
	$name=$nameupd;
    }

    my %a=PLkeys($ref);

    my $indent=$OPTIONS{indent} x $Nindent;
    print $phandle "$indent<ParameterList name=\"$name\">\n";
 
    $Nindent++;

    my @b=keys %a;
    print "Level $Nindent: found @b\n";
    foreach my $PLentry (keys %a){
	if( PLtype($a{$PLentry} ) eq 'parameter'){
	    &packXMLparameter($a{$PLentry},$PLentry,$phandle,$Nindent);
	}
	if( PLtype($a{$PLentry} ) eq 'array'){
	    &packXMLarray($a{$PLentry},$PLentry,$phandle,$Nindent);
	}
	if( PLtype($a{$PLentry}) eq 'list'){
	    &packXMLlist($a{$PLentry},$PLentry,$phandle,$Nindent)     
	}
    }

    print $phandle "$indent</ParameterList>\n";
}
