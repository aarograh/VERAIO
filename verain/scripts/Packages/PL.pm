package PL;

# use Clone qw(clone);
use ClonePP qw(clone);

use KeyTree;
use MiscUtils;
use REACTOR;
use TypeUtils;

use Exporter;
@ISA = ('Exporter');
@EXPORT=('PLlist',
	 'PLparameter',
	 'PLarray',
	 'PLdoarg',
	 'PLtype',
	 'PLdo',
	 'PLname',
	 'PLnotempty',
	 'PLkeys',
	 'PLdelete',
	 'PLkeyon',
	 'rethread'
    );

{
    my $_VERBOSE = 0;
    sub get_verbose  {$_VERBOSE;}
    sub set_verbose { $_VERBOSE = 1; }

    my $_DEBUG = 0;
    sub get_debug  {$_DEBUG;}
    sub set_debug { $_DEBUG = 1; }

    $SOURCE_DB=undef;

    sub set_sourcedb {
	my ($self,$db)=@_;
	$SOURCE_DB=$db;
    }

    $DISPATCH={
	copy      => \&dbcopy1,
	copyarray => \&copyarray,
	copyhash  => \&copyhash,
	setdb     => \&setdb,
	matmap    => \&matmap2,
	rodmap    => \&rodmap,
	makemap   => \&makemap,
	echos     => \&echos,
	rename    => \&dbcopy,
	gridmap   => \&gridmap
    };

}

sub PLdoarg{
    my( $str, %userparam ) = @_ ;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    $str =~ s/=>/,/g;
    $str =~ s/,/ /g;

#    $str =~ s/ //g;

    $str =~ s/^\s+//;
    $str =~ s/\s+$//;
    my @a=split / +/, $str;

#    my @a = ($str =~ /(?:$RE{balanced}{-parens=>'[]'}|[^,])+/g);

    return @a;
}

sub PLname {
    my ($ref,%userparam)=@_;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    return key_exists($ref,'_name') ? read_off_label($ref,'_name') : undef;
}

sub PLtype{
    my ($ref,%userparam)=@_;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    if(defined($OPTIONS{ref}) &&
       $OPTIONS{ref} eq 'path' &&
       defined($OPTIONS{root}))
    {
	my @path=parse_path($ref);
	$ref=keys_defined($OPTIONS{root},@path);
    }

    if(defined($ref->{_pltype})){
	return $ref->{_pltype};
    }
    else{
	return undef;
    }
}

sub PLkeys{
    my ($ref,%userparam)=@_;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my @a=keys_at($ref->{'_content'});
    my @b = grep { ! /^_/ } @a;

    @a=();
    foreach my $iname (@b){
	my $iref=key_exists($ref,'_content',$iname);
	push @a, $iname, $iref;
    }

    return @a;
}

sub PLdelete{
    my ($ref,$name,%userparam)=@_;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my $iref=key_exists($ref,'_content',$name);
    if($iref){
	delete($ref->{'_content'}->{$name});
	return 1;
    }
    return undef;
}

sub PLkeyon{
    my ($ref,$ref2,$name,%userparam)=@_;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my $iref=key_exists($ref,'_content');
    if($iref){
	key_on($iref,$name,$ref2);
	return 1;
    }
    return undef;
}

sub PLdo{
    my ($ref,%userparam)=@_;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    if(defined($ref->{_do})){
	my @todo=@{ $ref->{_do} };
	return \@todo;
    }
    else{
	return undef;
    }
}
    
sub PLnotempty {
    my ($ref,%userparam)=@_;
    my %OPTIONS;

    $OPTIONS{_content}='_content';
    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    if(defined($ref->{$OPTIONS{_content}})){
	return 1;
    }
    else{
	return undef;
    }
}

sub PLparameter{
    my ($ref,$actions,%userparam)=@_;
    my %OPTIONS;
    my $home=$ref;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    if(my $todo=PLdo($ref)){
	my $val;
	foreach my $ido (@{ $todo }){
	    my @do_parse=PLdoarg($ido);
	    my $command=shift @do_parse;
	    if(PLnotempty($ref,_content=>'_content')){
		unshift @do_parse, $ref->{_content};
	    }
	    $val=$actions->{$command}->($home,@do_parse);
	    if(defined($val)){
		key_on($ref,'_content',$val);
	    }
	}
	if(defined($val)){
	    key_on($ref,'_content',$val);
	}
    }
}

sub PLarray{
    my ($ref,$actions,%userparam)=@_;
    my %OPTIONS;
    my $home=$ref;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    if(my $todo=PLdo($ref)){
	my $val;
	foreach my $ido (@{ $todo }){
	    my @do_parse=PLdoarg($ido);
	    my $command=shift @do_parse;
	    if(PLnotempty($ref,_content=>'_content')){
		unshift @do_parse, @{ $ref->{_content} };
	    }
	    $val=$actions->{$command}->($home,@do_parse);
	    if($val){
		key_on($ref,'_content',[@{$val}]);
	    }
	}
	if($val){
	    key_on($ref,'_content',[@{$val}]);
	}
    }
}

sub PLlist{
    my ($ref)=@_;
    my $home=$ref;

    $actions=$DISPATCH;

    my @PLcontent = keys %{ $ref->{_content} };

    print STDERR "PLlist: @PLcontent\n" if get_verbose();


    my $val;
    if(my $todo=PLdo($ref)){
	foreach my $ido (@{ $todo }){
	    my @do_parse=PLdoarg($ido);
	    my $command=shift @do_parse;
	    $val=$actions->{$command}->($home,@do_parse);
	    if(lc($command) eq 'rename'){
		key_on($ref,'_name',$val);
	    }
	}
    }

    foreach $iaddr (@PLcontent){
	my $rref = key_defined($ref,'_content',$iaddr);
	my $typ=PLtype($rref);

	if($typ eq 'parameter'){
	    &PLparameter($rref,$actions);
	}
	if($typ eq 'array'){
	    &PLarray($rref,$actions);
	}
	if($typ eq 'list'){
	    &PLlist($rref);
	}
	if($typ eq 'map'){
	    print STDERR "type map\n" if get_verbose();
	    &PLlist($rref);
	}
    }
}

sub rethread {
    my ($pref,$keyname,$reth_key)=@_;
    my (@parents,@children);

    my $ref=$pref->{$keyname};

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

    print STDERR "parents: @parents\n" if get_verbose();
    print STDERR "children: @children\n" if get_verbose();

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

    return $t unless defined($t);

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
    return undef unless $cm_ref;

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
    print STDERR "echos: @args\n";
    return;
}

sub setdb{
    my ($home,$db)=@_;
    
    if($db eq 'MAIN_DB'){
#	$SOURCE_DB=$MAIN_DB;
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
	if($mattype eq 'uo2'){
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

sub matmap2{
    my ($home,$basename,@paths)=@_;

    my @mats;
    my @mats_names;

    my $keyname;
    my $mattype;

#    my @MATS_RESERVED=('mod','vacuum','zirc','aic','he','b4c','inc','ss','pyrex','uo2');
    my @MATS_RESERVED=('mod','vacuum');
    my @MAT_RESERVED =('mod','vacuum','zirc','aic','he','b4c','inc','ss','pyrex');
    my @FUEL_RESERVED=('uo2');

    foreach my $ipath (@paths){
	my @apaths=find_keys($SOURCE_DB,$ipath);
	my @names =find_keys($SOURCE_DB,$ipath,undef,strings=>'true');
	push @mats, @apaths if @apaths;
	push @mats_names, @names if @names;
    }

    foreach my $imat_path (@mats){
	my @keypath=@{ $imat_path };
	my @content=@{ key_defined($SOURCE_DB,@keypath,'_content') };

	my $enrichable=0;
	my $depletable='false';
	my $enrichment;
	my $thdensity=0;
	my @mat_names=();
	my @mat_fracs=();

	my $density=$content[0];
	my $fissionable='false';

	if($keypath[$#keypath-2] eq 'mat'){
	    $keyname=$keypath[$#keypath];
	    $mattype=$content[1] || $keyname;
	    push @mat_names, $mattype;
	    push @mat_fracs, 1.0;
	}
	elsif($keypath[$#keypath-2] eq 'fuel'){
	    $keyname=$keypath[$#keypath];
	    $mattype="uo2";
	    $enrichable=1;
	    $thdensity=$content[1];
	    $enrichment=$content[2];
	    $depletable='true';
	    $fissionable='true';
	    push @mat_names, $mattype;
	    push @mat_fracs, 1.0;
	}
	else{    # old format
	    $keyname=$keypath[$#keypath];
	    $mattype=$keypath[$#keypath-2];
	    if($mattype eq 'uo2'){
		$enrichable=1;
		$enrichment=$content[1];
		$depletable='true';
		$fissionable='true';
	    }
	    push @mat_names, $mattype;
	    push @mat_fracs, 1.0;
	}

	my $mat_ref=&key_on_list($home,$basename.$keyname);
	&key_on_parameter($mat_ref,'density','double',$density);
	&key_on_parameter($mat_ref,'thden','double',$thdensity) if $thdensity;
	&key_on_parameter($mat_ref,'fissionable','bool',$fissionable);
	&key_on_parameter($mat_ref,'depletable','bool',$depletable)   if $enrichable;
	&key_on_parameter($mat_ref,'enrichment','double',$enrichment) if $enrichable;
	&key_on_parameter($mat_ref,'key_name','string',$keyname);

#	&key_on_parameter($mat_ref,'mat_name','string',$mattype);

	&key_on_array($mat_ref,'mat_names','string', @mat_names);
	&key_on_array($mat_ref,'mat_fracs','double', @mat_fracs);

    }
}

sub rodmap{
    my ($home,$axial_path,%userparam)=@_;
    my ($i,$j,$k,$m,$n);
    my (@a,@b,@c,@d);

#    my @MATS_RESERVED=('mod','vacuum','zirc','aic','he','b4c','inc','ss','pyrex','uo2');
    my @MATS_RESERVED=('mod','vacuum');
    my @MAT_RESERVED =('mod','vacuum','zirc','aic','he','b4c','inc','ss','pyrex');
    my @FUEL_RESERVED=('uo2');

    my %OPTIONS=('basename'=>'List','mapname'=>'rodmap');
    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    # create hash of all axial ids and their values
    my @axial_rpath = parse_path($axial_path);
    my $axial_ref=key_defined($SOURCE_DB,@axial_rpath);
    return unless $axial_ref;
    my @axial_available = keys_at($axial_ref);
    return unless @axial_available;
    print STDERR "available axials: @axial_available\n" if get_verbose();
    my @axial_common=@axial_available;

    if(exists($OPTIONS{coremap})){
	# get unique ids for assemblies, 0 means missing
	$coremap_path=$OPTIONS{coremap};
	my @coremap_path=parse_path($coremap_path);
	my $coremap_ref=key_defined($SOURCE_DB,@coremap_path);
	my @axials=unique(@{ $coremap_ref });    # labels of all unique axials
	print STDERR "axials w/path: [@axials] [@coremap_path]\n" if get_verbose();  # debug
	@axials=nonstring('0',@axials);
	@axials=nonstring('-',@axials);
	print STDERR "axials: @axials\n" if get_verbose();  # debug

	my @axial_common=intersection(\@axials,\@axial_available);

	unless($#axial_common == $#axials){
	    print STDERR "axial labels needed   : @axials\n";
	    print STDERR "axial labels available: @axial_available\n";
	    die   "rodmap: missing axial definitions in $axial_path\n";
	}
    }

    print STDERR "axial_rpath: @axial_rpath\n" if get_verbose();
    foreach (@axial_available){
	$AXIAL_DEFS{$_} = key_exists($axial_ref,$_);
	$AXIAL_CONTENT{$_}=[@{ $AXIAL_DEFS{$_}->{_content} }];
	@a=@{ $AXIAL_CONTENT{$_} };
	unless(@a%2){
	    die "rodmap: axial $_ has even number of elements @a\n";
	}
	@b=even(\@a);
	@c=odd(\@a);
	$AXIAL_ELEVATIONS{$_}=[@b];
	$AXIAL_LABELS{$_}=[@c];
	print STDERR "  AXIAL_DEFS{$_}: $AXIAL_DEFS{$_}\n" if get_verbose();
	print STDERR "         content: @{ $AXIAL_CONTENT{$_} }\n" if get_verbose();
	print STDERR "         heights: @b\n" if get_verbose();
	print STDERR "         labels : @c\n" if get_verbose();
    }

    # get material paths
    my @block_rpath=@axial_rpath;
    pop @block_rpath;
    pop @block_rpath;
    print STDERR "block_path: @block_rpath\n" if get_verbose();
    my %MATS_DB;
    if(defined $OPTIONS{ matsearch }){
	my $mat_search=$OPTIONS{ matsearch } ;
	print STDERR "mat_search: $mat_search\n" if get_verbose();
	my @mat_array=split(':',$mat_search);
	print "mat_array @mat_array\n" if get_verbose();
	foreach my $imat (@mat_array){
	    my @apaths=find_keys($SOURCE_DB,$imat);
	    my @names =find_keys($SOURCE_DB,$imat,undef,strings=>'true');
	    if(@apaths){
		print "\timat  : $imat\n" if get_verbose();
		print "\t\tapaths: @apaths\n" if get_verbose();
		print "\t\tnames : @names\n" if get_verbose();
		foreach my $iapath (@apaths){
		    print "\t\t\t @{ $iapath }\n" if get_verbose();
		    my @mat_path=@{ $iapath };
		    my @mat_flags = ($mat_path[$#mat_path],'other');
		    if( @mat_path[1] =~ m/(fuel|uo2)/ ){
			$mat_flags[1]='fuel';
		    }
		    unless(exists $MATS_DB{ $mat_flags[0] }){
			$MATS_DB{ $mat_flags[0] } = $mat_flags[1];
			print "\t\t\t\tMATS_DB{$mat_flags[0]}=$mat_flags[1]\n" if get_verbose();
		    }
		}
	    }

	}
    }

    # get npin for setting the maps
    my @npin_rpath=@axial_rpath;
    $npin_rpath[$#cell_rpath-1]='npin';
    $npin_rpath[$#cell_rpath]='_content';
    print STDERR "npin_rpath: @npin_rpath\n" if get_verbose();
    my $npin=key_defined($SOURCE_DB,@npin_rpath);
    print STDERR "npin: $npin\n" if get_verbose();

    # create hash of all rodmap ids and their values
    my @cellmap_rpath=@axial_rpath;
    $cellmap_rpath[$#cellmap_rpath-1]=$OPTIONS{mapname};
    my $cellmap_ref=key_defined($SOURCE_DB,@cellmap_rpath);
    my @cellmap_available = keys_at($cellmap_ref);
    print STDERR "cellmap_rpath: @cellmap_rpath\n" if get_verbose();
    foreach (@cellmap_available){
	$CELLMAP_DEFS{$_} = key_exists($cellmap_ref,$_);
	$CELLMAP_CONTENT{$_}=[@{ $CELLMAP_DEFS{$_}->{_content} }];
	print STDERR "  CELLMAP_DEFS{$_}: $CELLMAP_DEFS{$_}\n" if get_verbose();

	@a=@{ $CELLMAP_CONTENT{$_} };
	@b=();
	@c=unique(@a);   # why?
#	@c=nonzero(@c);  # why?
	@c=nonstring('-',@c);
	$CELLMAP_CELLS{$_}=[@c];
	print STDERR "  CELLMAP_CELLS{$_}: @c\n" if get_verbose();

	@b=fullcellmap($npin,@a);
	$CELLMAP_CONTENT{$_}=[@b];
    }
 
    # create hash of all cell ids and their values
    my @cell_rpath=@axial_rpath;
    $cell_rpath[$#cell_rpath-1]='cell';
    my $cell_ref=key_defined($SOURCE_DB,@cell_rpath);
    my @cell_available = keys_at($cell_ref);
    print STDERR "cell_rpath: @cell_rpath\n" if get_verbose();
    foreach (@cell_available){
	$CELL_DEFS{$_} = key_exists($cell_ref,$_);
	$CELL_CONTENT{$_}=[@{ $CELL_DEFS{$_}->{_content} }];
	print STDERR "  CELL_DEFS{$_}: $CELL_DEFS{$_}\n" if get_verbose();
	print STDERR "        content: @{ $CELL_CONTENT{$_} }\n" if get_verbose();

	@a=@{$CELL_CONTENT{$_}};
	if(@a==1){
	    if($a[0] ne 'mod'){
		die "rodmap: cell $_ @a has one entry and is not a moderator\n";
	    }
	    $CELL_TYPE{$_}='mod';
	    $CELL_radii{$_}=[];
	    $CELL_mats{$_} =['mod'];
	}
	else{
	    if(@a%2 != 0){
		die "rodmap: cell $_ @a has odd number of entries\n";
	    }
	    else{
		$CELL_radii{$_}=[fronthalf(\@a,0)];
		my @cmats=endhalf(\@a,0);

		# start mod
		# have to search for available materials and fuels
		# bomb if mat and fuel are at the same level
		# if exists mat cell_type=other, if exists fuel =fuel

		$CELL_TYPE{$_}='other';

		if(defined $OPTIONS{ matsearch }){
		    foreach my $imat (@cmats){
			print STDERR "    CELL mat $imat\n" if get_verbose();

			next if in_dictionary($imat, @MATS_RESERVED);

			if(exists($MATS_DB{ $imat })){
			    if($MATS_DB{ $imat } eq 'fuel'){
				$CELL_TYPE{$_}='fuel';
				print STDERR "    \tCELL mat $imat is fuel\n" if get_verbose();
			    }
			}
			else{
			    die "rodmap: cell $_ has material $imat which is not defined\n";
			}
		    }
		}
		else{    # remove after update of input files with new definitions
		    if(fany(sub{m/(u)/i}, @cmats)){
			$CELL_TYPE{$_}='fuel';
		    }
		}
#		else{
#		    $CELL_TYPE{$_}='other';
#		}
		# end mod

		$CELL_mats{$_} =[@cmats];
		print STDERR "    CELL radii @{ $CELL_radii{$_} }\n" if get_verbose();
		print STDERR "    CELL mats  @{ $CELL_mats{$_} }\n" if get_verbose();
		print STDERR "    CELL type  $CELL_TYPE{$_}\n" if get_verbose();
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
	    print STDERR "$OPTIONS{mapname} labels needed   : [@b]\n";
	    print STDERR "$OPTIONS{mapname} labels available: [@cellmap_available]\n";
	    die   "missing $OPTIONS{mapname} definitions in $axial_path\n";
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
	    print STDERR "cell labels needed   : [@b]\n";
	    print STDERR "cell labels available: [@cell_available]\n";
	    die   "rodmap: missing cell definitions in $axial_path\n";
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

1;
