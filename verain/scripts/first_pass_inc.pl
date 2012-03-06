#!/usr/local/bin/perl

use lib qw(./);

# Perl modules
use warnings ;
use File::Basename;
use IO::File;
use Data::Dumper ;
use IO::Handle;
use Getopt::Long;
use XML::LibXML;

# local packages
use IncludeHandle;
use Blocks;
# use ParseState;

my $pgnam=basename($0);     # program name

# options
my $LOGFILE;
my $SCHEMA;
my $VERBOSE;
my $ROOT='MODEL';
my $HELP;
{ # process options
    GetOptions("logfile=s" => \$LOGFILE,
	       "schema=s"  => \$SCHEMA,
	       "model=s"   => \$ROOT,
	       "verbose"   => \$VERBOSE,
               "help"      => \$HELP);

}

if($HELP || @ARGV < 2){
    die "Usage: $pgnam [options ...] reactor_file xml_file

options:
  --logfile=file
  --schema=file
  --model=name
  --help
  --verbose
\n";
}

($ifile,$ofile)=@ARGV;
my $fho = new IO::File($ofile, "w") or die "$ofile $!\n";

# enable C-like include, can do others with different pattern below,
# will move to to package and replace with iterator
local *IFILE;
tie *IFILE, 'IncludeHandle', $ifile, 
sub {
    /^#include \"(.*)\"/ ? $1 : /^#include <(.*)>/ ? $1 : undef
} or die "Cannot tie $ifile: $!";

# read blocks and save them in variables
undef $block;
 READ: while (<IFILE>) {
     s/^\s+//; s/\s+$/\n/;     # strip leading and trailing blanks
     s/(\!\s*(.*))$// &&       # strip comments
	 do{
	     $comment=$2;
	     print "[$.] Comment: $comment\n" if $VERBOSE;
     };
     /^$/ &&                   # skip empty lines
	 do{
	     print "[$.] Blank line\n" if $VERBOSE;
	     next READ;
     };
     /^\[\s*(\w+)\s*\]/ &&     # find keyword, .ini style
	 do{
	     $block=$1;
	     $blk=Blocks->new->init(BLOCK => $block);
	     print "[$.] Found block: $block\n"  if $VERBOSE;
	     push @BLOCKS, $blk;
	     next READ;
     };
     $block &&                 # read block data
	 do{
	     s/(\d+)\s*\*\s*(\w+)/"$2 " x $1/ge;      # expand fortran
						      # expressions
	     $blk->append(TEXT => $_);
	     next READ;
     };
}

# create new XML document
my $dom  = XML::LibXML::Document->new("1.0", "utf-8");

# set root node and its attributes
# my $root = $dom->createElement( $ROOT );
my $root = $dom->createElement( "ParameterList" );
$dom->setDocumentElement( $root );

foreach $blk (@BLOCKS){
    $blk->tokenize();
    my $node=$blk->to_XML();
    $root->appendChild( $node );
}

# send output to filehandle
my $format = 2;     # possible options: 0, 1, or 2
my $state = $dom->toFH($fho, $format);

close ($fho);
