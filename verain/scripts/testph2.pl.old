#!/usr/local/bin/perl
# use strict;
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


my $pgnam=$0;     # program name

$DISPATCH={
    copy      => \&dbcopy1,
    copyarray => \&copyarray,
    copyhash  => \&copyhash,
    setdb     => \&setdb,
    matmap    => \&matmap,
    rodmap    => \&rodmap,
    makemap   => \&makemap,
    echos     => \&echos,
    rename    => \&dbcopy,
    gridmap   => \&gridmap
};

my $DB='o.yml';
my $CASEID_SCHEMA     ="${directory}Templates/CASEID.yml";
my $CORE_SCHEMA       ="${directory}Templates/CORE.yml";
my $STATE_SCHEMA      ="${directory}Templates/STATE.yml";
my $DENOVO_SCHEMA     ="${directory}Templates/DENOVO.yml";
my $EDITS_SCHEMA      ="${directory}Templates/EDITS.yml";
my $CONTROLS_SCHEMA   ="${directory}Templates/CONTROLS.yml";
my $INSERTS_SCHEMA    ="${directory}Templates/INSERTS.yml";
my $DETECTORS_SCHEMA  ="${directory}Templates/DETECTORS.yml";
my $ASSEMBLIES_SCHEMA ="${directory}Templates/ASSEMBLIES.yml";
my $DEBUG=0;
my ($LOGFILE, $VERBOSE,$HELP);
{ # process options
    GetOptions("logfile=s" => \$LOGFILE,
	       "db=s"      => \$DB,

	       "case=s"        => \$CASEID_SCHEMA,
	       "core=s"        => \$CORE_SCHEMA,
	       "state=s"       => \$STATE_SCHEMA,
	       "denovo=s"      => \$DENOVO_SCHEMA,
	       "edits=s"       => \$EDITS_SCHEMA,
	       "controls=s"    => \$CONTROLS_SCHEMA,
	       "inserts=s"     => \$INSERTS_SCHEMA,
	       "detectors=s"   => \$DETECTORS_SCHEMA,
	       "assemblies=s"  => \$ASSEMBLIES_SCHEMA,

	       "verbose"   => \$VERBOSE,
	       "debug=i"   => \$DEBUG,
               "help"      => \$HELP);
}

if($HELP || @ARGV < 1){
    die "Usage: $pgnam [options ...] yml_file

options:
  --logfile file
  --db file

  --core file
  --state file
  --denovo file
  --edits file
  --controls file
  --inserts file
  --detectors file
  --assemblies file

  --debug level
  --verbose
  --help
\n";
}

$YAML::UseAliases=0;    # minimize references
($MAIN_DB) = YAML::LoadFile( $DB );
mergekeys_loop( $MAIN_DB );
# print Data::Dumper->Dump([$MAIN_DB], [qw(MAIN_DB)]);

$YAML::UseAliases=0;    # minimize references
($CASEID_SCH) = YAML::LoadFile( $CASEID_SCHEMA );
mergekeys_loop( $CASEID_SCH );

$YAML::UseAliases=0;    # minimize references
($CORE_SCH) = YAML::LoadFile( $CORE_SCHEMA );
mergekeys_loop( $CORE_SCH );

($STATE_SCH) = YAML::LoadFile( $STATE_SCHEMA );
mergekeys_loop( $STATE_SCH );

($DENOVO_SCH) = YAML::LoadFile( $DENOVO_SCHEMA );
mergekeys_loop( $DENOVO_SCH );

($EDITS_SCH) = YAML::LoadFile( $EDITS_SCHEMA );
mergekeys_loop( $EDITS_SCH );

($CONTROLS_SCH) = YAML::LoadFile( $CONTROLS_SCHEMA );
mergekeys_loop( $CONTROLS_SCH );

($INSERTS_SCH) = YAML::LoadFile( $INSERTS_SCHEMA );
mergekeys_loop( $INSERTS_SCH );

($DETECTORS_SCH) = YAML::LoadFile( $DETECTORS_SCHEMA );
mergekeys_loop( $DETECTORS_SCH );

($ASSEMBLIES_SCH) = YAML::LoadFile( $ASSEMBLIES_SCHEMA );
mergekeys_loop( $ASSEMBLIES_SCH );

PLlist($CASEID_SCH->{CASEID},$DISPATCH);
YAML::DumpFile("CASEID_dbg.yml",$CASEID_SCH) if $DEBUG;

PLlist($CORE_SCH->{CORE},$DISPATCH);
YAML::DumpFile("CORE_dbg.yml",$CORE_SCH) if $DEBUG;

PLlist($STATE_SCH->{STATE},$DISPATCH);
YAML::DumpFile("STATE_dbg.yml",$STATE_SCH) if $DEBUG;

PLlist($DENOVO_SCH->{DENOVO},$DISPATCH);
YAML::DumpFile("DENOVO_dbg.yml",$DENOVO_SCH) if $DEBUG;

PLlist($EDITS_SCH->{EDITS},$DISPATCH);
YAML::DumpFile("EDITS_dbg.yml",$EDITS_SCH) if $DEBUG;

PLlist($CONTROLS_SCH->{CONTROLS},$DISPATCH);
YAML::DumpFile("CONTROLS_dbg.yml",$CONTROLS_SCH) if $DEBUG;

PLlist($INSERTS_SCH->{INSERTS},$DISPATCH);
YAML::DumpFile("INSERTS_dbg.yml",$INSERTS_SCH) if $DEBUG;

PLlist($DETECTORS_SCH->{DETECTORS},$DISPATCH);
YAML::DumpFile("DETECTORS_dbg.yml",$DETECTORS_SCH) if $DEBUG;

PLlist($ASSEMBLIES_SCH->{ASSEMBLIES},$DISPATCH);
YAML::DumpFile("ASSEMBLIES_dbg.yml",$ASSEMBLIES_SCH) if $DEBUG;

# dispatch functions

sub dbcopy{
    my( $home, $path, %userparam ) = @_ ;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my @path=parse_path($path);
    my $t=key_defined($SOURCE_DB,@path);

    return $t;
}

sub dbcopy1{
    my( $home, $path, %userparam ) = @_ ;
    my %OPTIONS;
    my @result;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }
    my $def=undef;
    if(exists($OPTIONS{apply})){
	$def = eval "sub { return $OPTIONS{apply};}";
	die "dbcopy: invalid apply string $OPTIONS{apply}\n" unless ref $def eq 'CODE';
    }

    my @path=parse_path($path);
    my $t=key_defined($SOURCE_DB,@path);

    if(ref $t eq 'ARRAY'){
	foreach (@{ $t }){
	    push @result, $def ? $def->($_) : $_;
	}
	return \@result;
    }
    elsif(ref $t eq 'HASH'){
	die "dbcopy: HASH copy not supported\n";
    }
    else{
	return $def ? $def->($t) : $t;
    }
}

sub makemap {
    my( $home, $npin_path, $cmap_path, %userparam ) = @_ ;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my @npin_path=parse_path($npin_path);
    my $npin=key_defined($SOURCE_DB,@npin_path);
    die "makemap: npin not valid [$npin_path] [@npin_path] [$npin]\n" 
	if ref $npin;

    my @cmap_path=parse_path($cmap_path);
    my $cm_ref=key_defined($SOURCE_DB,@cmap_path);
    die "makemap: cm_ref not valid [$cmap_path] [@cmap_path] [$cm_ref]\n" 
	unless ref $cm_ref eq 'ARRAY';

    my @a=fullcellmap($npin,@{ $cm_ref });

    return \@a;
}

sub copyarray{
    my( $home, $path, %userparam ) = @_ ;
    my %OPTIONS;
    my @a=();
    my @result=();

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    # get what
    my @path=parse_path($path);
    my $t=key_defined($SOURCE_DB,@path);
    return undef if ref $t ne 'ARRAY';
    @result=@{ $t };

    if(exists($OPTIONS{select})){
	if(lc($OPTIONS{select}) eq 'odd'){
	    @a=@{ $t };
	    @result=odd(\@a);
	}
	elsif(lc($OPTIONS{select}) eq 'even'){
	    @a=@{ $t };
	    @result=even(\@a);	    
	}
	else{
	    warn "copyarray: select option $OPTIONS{select} not valid\n";
	    return undef;
	}
    }
    return \@result;
}

sub copyhash{
    my( $home, $path, %userparam ) = @_ ;
    my %OPTIONS;
    my @a=();
    my @result=();
    my $key;
    my $value;

    while ( ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    # get what
    my @path=parse_path($path);
    my $t=key_defined($SOURCE_DB,@path);
    return undef if ref $t ne 'HASH';
    @a=keys %{ $t };
    foreach $key (@a){
	$value= $t->{$key}->{_content};
	push @result, ($key,$value);
    }

    if(exists($OPTIONS{select})){
	if(lc($OPTIONS{select}) eq 'keys'){
	    @result=even(\@result);
	}
	elsif(lc($OPTIONS{select}) eq 'values'){
	    @result=odd(\@result);
	}
	else{
	    warn "copyhash: select option $OPTIONS{select} not valid\n";
	    return undef;
	}
    }
    return \@result;
}

sub echos{
    my ($home,@args)=@_;
    print "echos: @args\n";
    return;
}

sub setdb{
    my ($home,$db)=@_;
    
    if($db eq 'MAIN_DB'){
	$SOURCE_DB=$MAIN_DB;
    }
    return undef;
}

sub gridmap{
    my ($home,$basename,@paths)=@_;

#    my $flagref=key_defined($home,'_content');
#    key_on($flagref,'FLAG','I was here');
    my @mats;
    my @mats_names;
    foreach my $ipath (@paths){
	my @apaths=find_keys($SOURCE_DB,$ipath);
	my @names =find_keys($SOURCE_DB,$ipath,undef,strings=>'true');
	push @mats, @apaths if @apaths;
	push @mats_names, @names if @names;
    }

    foreach my $imat_path (@mats){
	my @keypath=@{ $imat_path };
	my $keyname=$keypath[$#keypath];
	my @content=@{ key_defined($SOURCE_DB,@keypath,'_content') };

	my $mat_ref=&key_on_list($home,$basename.$keyname);

	&key_on_parameter($mat_ref,'label','string',$keyname);
	&key_on_parameter($mat_ref,'material','string',$content[0]);
	&key_on_parameter($mat_ref,'mass','double',$content[1]);
	&key_on_parameter($mat_ref,'height','double',$content[2]);
    }
}

sub matmap{
    my ($home,$basename,@paths)=@_;

    my @mats;
    my @mats_names;
    foreach my $ipath (@paths){
	my @apaths=find_keys($SOURCE_DB,$ipath);
	my @names =find_keys($SOURCE_DB,$ipath,undef,strings=>'true');
	push @mats, @apaths if @apaths;
	push @mats_names, @names if @names;
    }

    foreach my $imat_path (@mats){
	my @keypath=@{ $imat_path };
	my $keyname=$keypath[$#keypath];
	my $mattype=$keypath[$#keypath-2];
	my @content=@{ key_defined($SOURCE_DB,@keypath,'_content') };
	my $density=$content[0];

	my $enrichable=0;
	my $depletable='false';
	if($mattype eq 'uo2' || $mattype eq 'pyrex'){
	    $enrichable=1;
	    $enrichment=$content[1];
	    $depletable='true';
	}

	my $mat_ref=&key_on_list($home,$basename.$keyname);

	&key_on_parameter($mat_ref,'density','double',$density);
	&key_on_parameter($mat_ref,'depletable','bool',$depletable);
	if($enrichable){
	    &key_on_parameter($mat_ref,'enrichment','double',$enrichment);
	}
	&key_on_parameter($mat_ref,'key_name','string',$keyname);
	&key_on_parameter($mat_ref,'mat_name','string',$mattype);
    }
}

sub rodmap{
    my ($home,$coremap_path,$axial_path,%userparam)=@_;
    my ($i,$j,$k,$m,$n);
    my (@a,@b,@c,@d);

    my %OPTIONS=('basename'=>'List','mapname'=>'rodmap');
    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    # get unique ids for assemblies, 0 means missing
    my @coremap_path=parse_path($coremap_path);
    my $coremap_ref=key_defined($SOURCE_DB,@coremap_path);
    my @axials=unique(@{ $coremap_ref });    # labels of all unique axials
    print "axials w/path: [@axials] [@coremap_path]\n";  # debug
    @axials=nonstring('0',@axials);
    @axials=nonstring('-',@axials);
    print "axials: @axials\n";  # debug

    # create hash of all axial ids and their values
    my @axial_rpath = parse_path($axial_path);
    my $axial_ref=key_defined($SOURCE_DB,@axial_rpath);
    my @axial_available = keys_at($axial_ref);
    print "available axials: @axial_available\n";

    my @axial_common=intersection(\@axials,\@axial_available);

    unless($#axial_common == $#axials){
	print "axial labels needed   : @axials\n";
	print "axial labels available: @axial_available\n";
	die   "missing axial definitions in $axial_path\n";
    }

    print "axial_rpath: @axial_rpath\n";
    foreach (@axial_available){
	$AXIAL_DEFS{$_} = key_exists($axial_ref,$_);
	$AXIAL_CONTENT{$_}=[@{ $AXIAL_DEFS{$_}->{_content} }];
	@a=@{ $AXIAL_CONTENT{$_} };
	unless(@a%2){
	    die "axial $_ has even number of elements @a\n";
	}
	@b=even(\@a);
	@c=odd(\@a);
	$AXIAL_ELEVATIONS{$_}=[@b];
	$AXIAL_LABELS{$_}=[@c];
	print "  AXIAL_DEFS{$_}: $AXIAL_DEFS{$_}\n";
	print "         content: @{ $AXIAL_CONTENT{$_} }\n";
	print "         heights: @b\n";
	print "         labels : @c\n";
    }

    # get npin for setting the maps
    my @npin_rpath=@axial_rpath;
    $npin_rpath[$#cell_rpath-1]='npin';
    $npin_rpath[$#cell_rpath]='_content';
    print "npin_rpath: @npin_rpath\n";
    my $npin=key_defined($SOURCE_DB,@npin_rpath);
    print "npin: $npin\n";

    # create hash of all rodmap ids and their values
    my @cellmap_rpath=@axial_rpath;
    $cellmap_rpath[$#cellmap_rpath-1]=$OPTIONS{mapname};
    my $cellmap_ref=key_defined($SOURCE_DB,@cellmap_rpath);
    my @cellmap_available = keys_at($cellmap_ref);
    print "cellmap_rpath: @cellmap_rpath\n";
    foreach (@cellmap_available){
	$CELLMAP_DEFS{$_} = key_exists($cellmap_ref,$_);
	$CELLMAP_CONTENT{$_}=[@{ $CELLMAP_DEFS{$_}->{_content} }];
	print "  CELLMAP_DEFS{$_}: $CELLMAP_DEFS{$_}\n";

	@a=@{ $CELLMAP_CONTENT{$_} };
	@b=();
	@c=unique(@a);
	@c=nonzero(@c);
	@c=nonstring('-',@c);
	$CELLMAP_CELLS{$_}=[@c];
	print "  CELLMAP_CELLS{$_}: @c\n";

	@b=fullcellmap($npin,@a);
	$CELLMAP_CONTENT{$_}=[@b];
    }
 
    # create hash of all cell ids and their values
    my @cell_rpath=@axial_rpath;
    $cell_rpath[$#cell_rpath-1]='cell';
    my $cell_ref=key_defined($SOURCE_DB,@cell_rpath);
    my @cell_available = keys_at($cell_ref);
    print "cell_rpath: @cell_rpath\n";
    foreach (@cell_available){
	$CELL_DEFS{$_} = key_exists($cell_ref,$_);
	$CELL_CONTENT{$_}=[@{ $CELL_DEFS{$_}->{_content} }];
	print "  CELL_DEFS{$_}: $CELL_DEFS{$_}\n";
	print "        content: @{ $CELL_CONTENT{$_} }\n";

	@a=@{$CELL_CONTENT{$_}};
	if(@a==1){
	    if($a[0] ne 'mod'){
		die "cell $_ @a has one entry and is not a moderator\n";
	    }
	    $CELL_TYPE{$_}='mod';
	    $CELL_radii{$_}=[];
	    $CELL_mats{$_} =['mod'];
	}
	else{
	    if(@a%2 != 0){
		die "cell $_ @a has odd number of entries\n";
	    }
	    else{
		$CELL_radii{$_}=[fronthalf(\@a,0)];
		my @cmats=endhalf(\@a,0);
		if(fany(sub{m/(u)/i}, @cmats)){
		    $CELL_TYPE{$_}='fuel';
		}
		else{
		    $CELL_TYPE{$_}='other';
		}
		$CELL_mats{$_} =[@cmats];
		print "    CELL radii @{ $CELL_radii{$_} }\n";
		print "    CELL mats  @{ $CELL_mats{$_} }\n";
		print "    CELL type  $CELL_TYPE{$_}\n";
	    }
	}
    }

    my ($iref, $jref, $a_ref, $cm_ref, $c_ref);
    foreach $i (@axial_common){
	# create entry for Basename_X
	$a_ref=&key_on_list($home,$OPTIONS{basename}.$i);

	# create entries for bank level 
	&key_on_parameter($a_ref,'label','string',$i);
	&key_on_array($a_ref,'axial_labels','string',@{ $AXIAL_LABELS{$i} });
	&key_on_array($a_ref,'axial_elevations','double',@{ $AXIAL_ELEVATIONS{$i} });

	# see if we have all cellmaps needed
	@b=unique( @{ $AXIAL_LABELS{$i} } );
	my @cellmap_common=intersection(\@b,\@cellmap_available);
	unless($#cellmap_common == $#b){
	    print "cellmap labels needed   : [@b]\n";
	    print "cellmap labels available: [@cellmap_available]\n";
	    die   "missing cellmap definitions in $axial_path\n";
	}

	# Create CellMaps list in Assembly_X
	$cm_ref=&key_on_list($a_ref,'CellMaps');
	@c=();
	foreach $j (@b){
	    # Create CellMap in CellMaps list
	    $iref=&key_on_list($cm_ref,'CellMap'.'_'.$j);

	    &key_on_parameter($iref,'label','string',$j);
	    &key_on_array($iref,'cell_map','string',@{ $CELLMAP_CONTENT{$j} });
	    push @c, @{ $CELLMAP_CELLS{$j} }
	}

	@b=unique(@c);

	# see if we have all cells needed
	my @cell_common=intersection(\@b,\@cell_available);
	unless($#cell_common == $#b){
	    print "cell labels needed   : [@b]\n";
	    print "cell labels available: [@cell_available]\n";
	    die   "missing cell definitions in $axial_path\n";
	}

	# Create Cells list in Assembly_X
	$c_ref=&key_on_list($a_ref,'Cells');
	foreach $j (@b){
	    # Create Cells in Cells list
	    $iref=&key_on_list($c_ref,'Cell'.'_'.$j);

	    &key_on_parameter($iref,'label','string',$j);
	    &key_on_parameter($iref,'type','string',$CELL_TYPE{$j});
	    $k=@{ $CELL_radii{$j} };
	    &key_on_parameter($iref,'num_rings','int',$k);
	    &key_on_array($iref,'mats','string',@{ $CELL_mats{$j} });
	    &key_on_array($iref,'radii','double',@{ $CELL_radii{$j} });
	}
    }
}

sub key_on_parameter {
    ($iref,$name,$type,$value)=@_;
    my $jref;

    $jref=new_key($iref,'_content',$name);
    key_on($jref,'_pltype','parameter');
    key_on($jref,'_type',$type);
    key_on($jref,'_content',$value);
}
sub key_on_array {
    ($iref,$name,$type,@value)=@_;
    my $jref;

    $jref=new_key($iref,'_content',$name);
    key_on($jref,'_pltype','array');
    key_on($jref,'_type',$type);
    key_on($jref,'_content',[@value]);
}
sub key_on_list {
    ($iref,$name)=@_;
    my $jref;

    $jref=new_key($iref,'_content',$name);
    key_on($jref,'_pltype','list');

    return $jref;
}
