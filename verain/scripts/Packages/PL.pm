package PL;

# use Clone qw(clone);
# use ClonePP qw(clone);
use Clone::PP qw(clone);

use Text::Balanced qw (
                        extract_delimited
                        extract_bracketed
                        extract_quotelike
                        extract_multiple
                       );
use Text::ParseWords;

use Data::Types qw(:all);
use List::MoreUtils::PP;

use KeyTree;
use MiscUtils;
use REACTOR;
use Cellmaps;
use TypeUtils;
use Data::Dumper ;
use ErrHandler;

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
	 'rethread',
	 'PLtrim'
    );

our $DISPATCH;
our $FILE_LABEL='_file';
our $LINE_LABEL='_line';

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

    my %_VARS;
    sub setvar{
	my ($home,$name, $value, %userparam)=@_;
	my %OPTIONS;

	while ( my ($key, $value) = each %userparam ) # to avoid perl bug of $$
	{$OPTIONS{$key}=$value;}
	my $def=undef;
	if(exists($OPTIONS{apply})){
	    $def = eval "sub { return $OPTIONS{apply};}";
	    die "setvar: invalid apply string $OPTIONS{apply}\n" unless ref $def eq 'CODE';
	}

	my @args=($value);
	if(exists($OPTIONS{arg})){
	    push @args, $OPTIONS{arg};
	}
	$_VARS{$name}= $def ? &$def(@args) : $value;
	undef;
    }

    sub clearvar{
	my ($home,$name)=@_;
        print "clearvar $name : $_VARS{$name}\n"  if exists $OPTIONS{debug};
	delete($_VARS{$name});
	undef;
    }

    sub getvar{
	my ($home, $name, %userparam)=@_;
	my %OPTIONS;

	while ( my ($key, $value) = each %userparam ) # to avoid perl bug of $$
	{$OPTIONS{$key}=$value;}
	my $def=undef;
	if(exists($OPTIONS{apply})){
	    print "code: $OPTIONS{apply}\n" if exists $OPTIONS{debug};
	    $def = eval "sub { $OPTIONS{apply};}";
	    die "getvar: invalid apply string $OPTIONS{apply}\n" unless ref $def eq 'CODE';
	}
	die "getvar: variable $name does not exist.\n" unless exists($_VARS{$name});
	my $value=$_VARS{$name};
	my @args=($value);
	if(exists($OPTIONS{arg})){
	    push @args, $OPTIONS{arg};
	}
	$value = $def ? &$def(@args) : $value;
	$_VARS{$name} = $value;
	print "value: $value\n" if exists $OPTIONS{debug};

	undef;
#	return $value;
    }

    sub subvar{
	my( $str, %userparam ) = @_ ;
	my %OPTIONS;

	while ( my ($key, $value) = each %userparam ) # to avoid perl bug of $$
	{ $OPTIONS{$key}=$value;}

	$str =~ s/^\s+//;
	$str =~ s/\s+$//;
	my @a=keys %_VARS;
	foreach my $i (@a){
	    my $v='\('.$i.'\)';
	    my $s=$_VARS{$i};
	    $str =~ s/$v/$s/g;
	}
	return $str;
    }

    sub valuevar{
	my( $home, $name, %userparam ) = @_ ;
	my %OPTIONS;

	while ( my ($key, $value) = each %userparam ) # to avoid perl bug of $$
	{ $OPTIONS{$key}=$value;}

        print "valuevar: $name : $_VARS{$name}\n" if exists $OPTIONS{debug};
	die "valuevar: variable $name does not exist.\n" unless exists($_VARS{$name});
	return $_VARS{$name};
    }

    sub existsvar{
	my( $home, $name, %userparam ) = @_ ;
	my %OPTIONS;

	while ( my ($key, $value) = each %userparam ) # to avoid perl bug of $$
	{ $OPTIONS{$key}=$value;}

	return exists($_VARS{$name});
    }

}

sub dispatch {
    my ($self,$version)=@_;

    $DISPATCH={
	copy       => \&dbcopy2,
	copyarray  => \&copyarray,
	copytable  => \&copytable,
	copyhash   => \&copyhash,
	setdb      => \&setdb,
	matmap     => \&matmap,
	fuelmap    => \&fuelmap,
        sourcemap  => \&sourcemap,
	makemap    => \&makemap,
	echos      => \&echos,
	rename     => \&dbcopy,
	coremapmap => \&coremapmap,
	mpact_mesh => \&mpact_mesh,
	mpact_db   => \&mpact_db,
	tocelsius  => \&toCelsius,
	setvar     => \&setvar,
	clearvar   => \&clearvar,
	getvar     => \&getvar,
	valuevar   => \&valuevar,
	namesunique=> \&namesunique,
	value      => \&value,
	cellsmaps  => \&cellsmaps,
	isinmaps   => \&listscompare,
        axialtype  => \&setaxialtype,
	blademaps  => \&blademaps
    };

#    if($version eq '007'){
#	$DISPATCH->{matmap}  = \&matmap007;
#	$DISPATCH->{fuelmap} = \&fuelmap007;
#    }
}

sub PLdoarg{
    my( $str, %userparam ) = @_ ;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    $str =~ s/^\s+//;
    $str =~ s/\s+$//;
    my $delim='\s+|,|\s|=>';
    my $keep=0;
    my @a = parse_line($delim, $keep, $str);

    foreach (@a){
	$_=subvar($_);
	print "subvar $_\n" if exists $OPTIONS{debug};
    }

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
    my %OPTIONS=(
	'trsub' => [],
	'trvar' => [],
	);
    my $home=$ref;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }
    if( @{$OPTIONS{trsub}} ){
	print "parameter trvar: @{$OPTIONS{trvar}}\n" if get_verbose();;
	print "parameter trsub: @{$OPTIONS{trsub}}\n" if get_verbose();;
    }

    my @trsubin=@{ $OPTIONS{'trsub'} };
    my @trvarin=@{ $OPTIONS{'trvar'} };

    if(my $todo=PLdo($ref)){
	my $val;
	foreach my $ido (@{ $todo }){

	    for(my $i; $i<@trsubin; $i++){
		my $trsub=$trsubin[$i];
		my $trvar=$trvarin[$i];
		$trsub=quotemeta($trsub);
		$trvar=quotemeta($trvar);
		print "parameter ido1 $ido: $trvar,$trsub\n" if get_verbose();;
		$ido =~ s/\($trvar\)/$trsub/g;
		print "parameter ido2 $ido\n" if get_verbose();;
	    }

	    my @do_parse=PLdoarg($ido);
	    my $command=shift @do_parse;
	    if(PLnotempty($ref,_content=>'_content')){
		print "----> content $ref->{_content}\n" if get_verbose();
		unshift @do_parse, $ref->{_content};
		print "----> doparse @do_parse\n" if get_verbose();
	    }
	    $val=$actions->{$command}->($home,@do_parse);
	    if(defined($val)){
		key_on($ref,'_content',$val);
	    }
	}
# ssmod 150411 : why was this inserted since it would just reinsert the last one?
#	if(defined($val)){
#	    key_on($ref,'_content',$val);
#	}
    }
}

sub PLarray{
    my ($ref,$actions,%userparam)=@_;
    my %OPTIONS=(
	'trsub' => [],
	'trvar' => [],
	);
    my $home=$ref;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }
    if( @{$OPTIONS{trsub}} ){
	print "array trvar: @{$OPTIONS{trvar}}\n" if get_verbose();;
	print "trsub: @{$OPTIONS{trsub}}\n" if get_verbose();;
    }

    my @trsubin=@{ $OPTIONS{'trsub'} };
    my @trvarin=@{ $OPTIONS{'trvar'} };

    if(my $todo=PLdo($ref)){
	my $val;
	foreach my $ido (@{ $todo }){

	    for(my $i; $i<@trsubin; $i++){
		my $trsub=$trsubin[$i];
		my $trvar=$trvarin[$i];
		$trsub=quotemeta($trsub);
		$trvar=quotemeta($trvar);
		print "array ido1 $ido: $trvar,$trsub\n" if get_verbose();;
		$ido =~ s/\($trvar\)/$trsub/g;
		print "array ido2 $ido\n" if get_verbose();;
	    }

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
    my ($ref,%userparam)=@_;
    my $home=$ref;
    my %OPTIONS=(
	'trsub' => [],
	'trvar' => [],
	);

    $actions=$DISPATCH;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }
    if( @{$OPTIONS{trsub}} ){
	print "PLlist trvar: @{$OPTIONS{trvar}}\n" if get_verbose();;
	print "PLlist trsub: @{$OPTIONS{trsub}}\n" if get_verbose();;
    }

# TODO: Need a major rewrite.
# must be fully recursive with inheriting _tr varaibles.
# problem is using array pairs instead of trees

# applying actions:
# needs to be done with modified commands, but only modified by the arguments
# that are passed through the function call

    my @trsubin=@{ $OPTIONS{'trsub'} };
    my @trvarin=@{ $OPTIONS{'trvar'} };

    # first resolve _do and then _tr
    # TODO: should I do it other way around

    my $val;
    if(my $todo=PLdo($ref)){
	foreach my $ido (@{ $todo }){

	    for(my $i; $i<@trsubin; $i++){
		my $trsub=$trsubin[$i];
		my $trvar=$trvarin[$i];
		$trsub=quotemeta($trsub);
		$trvar=quotemeta($trvar);
		print "PLlist ido1 $ido: $trvar,$trsub\n" if get_verbose();;
		$ido =~ s/\($trvar\)/$trsub/g;
		print "PLlist ido2 $ido\n" if get_verbose();;
	    }

	    my @do_parse=PLdoarg($ido);
	    my $command=shift @do_parse;
	    $val=$actions->{$command}->($home,@do_parse);

# must fix this one out
#	    if(lc($command) eq 'rename'){
#		key_on($ref,'_name',$val);
#	    }
	}
    }

    # now do _tr
    # _tr increases tree space.

    my $trref = key_exists($ref,'_tr');
    my $trname;
    my @trsubs=();
    if(defined($trref)){
	$trname=read_off_label($trref,'_name');
	my $trcont=read_off_label($trref,'_content');

	print "PLlist found _tr: $trname,$trcont\n" if get_verbose();;
	print "PLlist current subs: @trsubin\n" if get_verbose();;
	print "PLlist current vars: @trvarin\n" if get_verbose();;

	# previous _tr get substituted, but variables are missed
	# apply varaibles
	$trcont=subvar($trcont);
	print "PLlist subvar: $trcont\n" if get_verbose();;

# Uncomment block below for syntax that includes previous _tr
#	for(my $i; $i<@trsubin; $i++){
#	    my $trsub=$trsubin[$i];
#	    my $trvar=$trvarin[$i];
#	    $trsub=quotemeta($trsub);
#	    $trvar=quotemeta($trvar);
#	    print "PLlist trcont: $trvar,$trsub\n" if get_verbose();;
#	    $trcont =~ s/\($trvar\)/$trsub/g;
#	    print "PLlist trcont new $trcont\n" if get_verbose();;
#	}

	my @trpath=find_keys($SOURCE_DB,$trcont);
	return unless(@trpath);  # to avoid empty loops
	foreach my $ipath ( @trpath ){
	    my @aipath = @{ $ipath };
	    print "trPATH: @aipath\n"  if get_verbose();
	    my $kr=key_defined($SOURCE_DB,@aipath);
	    die "PLlist: error in translation expression, invalid $trcont expression.\n" unless $kr;
	    push @trsubs, pop @aipath;
	}
    }

    my $trvar_arg;
    my $trsub_arg;

# if trref defined, do the loop and pass regex arguments

    my @PLcontent = keys %{ $ref->{_content} };
    my %DIR=PLkeys($ref);


    print  "PLlist: @PLcontent\n" if get_verbose();

    do {

	$trsub_arg=[ @trsubin ];
	$trvar_arg=[ @trvarin ];
	my $trsubi;
	if(@trsubs && defined($trname)){
	    print "trname: $trname trsubs: @trsubs\n" if get_verbose();
	    $trsubi=shift @trsubs;
	    $trsub_arg=[ @trsubin, $trsubi ];
	    $trvar_arg=[ @trvarin, $trname ];
	}

	foreach $iaddr (@PLcontent){
	    print "PLlist content loop: $iaddr\n" if get_verbose();;
	    my $rref = key_defined($ref,'_content',$iaddr);
	    my $typ=PLtype($rref);
	    print "PLlist typ: $typ\n" if get_verbose();;

	    my $crref=$rref;
	    if(defined($trref)){
		if($iaddr =~ m/\($trname\)/){
		    $imaddr=$iaddr;
		    $imaddr=~s/\($trname\)/$trsubi/g;
		    print "translated -----> $imaddr\n" if get_verbose();
		    $crref=clone($rref);
		    print Dumper($crref) if get_verbose();
		    PLkeyon($ref,$crref,$imaddr);
		}
	    }


	    if($typ eq 'parameter'){
		&PLparameter($crref,$actions, trsub=>$trsub_arg, trvar=>$trvar_arg);
	    }
	    if($typ eq 'array'){
		&PLarray($crref,$actions, trsub=>$trsub_arg, trvar=>$trvar_arg);
	    }
	    if($typ eq 'list'){
		&PLlist($crref, trsub=>$trsub_arg, trvar=>$trvar_arg);
	    }
	    if($typ eq 'map'){
		print  "type map\n" if get_verbose();
		&PLlist($crref, trsub=>$trsub_arg, trvar=>$trvar_arg);
	    }
	}

    } while (@trsubs);

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

    print  "parents: @parents\n" if get_verbose();
    print  "children: @children\n" if get_verbose();

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

sub PLtrim{
    my ($ref,$indent)=@_;

    my @PLcontent = keys %{ $ref->{_content} };

    print  "PLtrim: @PLcontent\n" if get_verbose();
    my $empty=0;

    $indent++;

    foreach $iaddr (@PLcontent){
	my $rref = key_defined($ref,'_content',$iaddr);
	my $typ=PLtype($rref);

	if($typ eq 'parameter' || $typ eq 'array'){
	    $empty++ if PLnotempty($rref,_content=>'_content');
	    next;
	}
	if($typ eq 'list'){
	    $empty+=&PLtrim($rref,$indent);
	    next;
	}
	die "PLtrim: undefined type @PLCONTENT\n";
    }
    print "\t" x $indent, "PLtrim: counter $empty at @PLcontent\n" if get_verbose();

    $ref->{_content}={} unless $empty;

    return $empty;
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

sub dbcopy2{
    my( $home, $path, %userparam ) = @_ ;
    my %OPTIONS;
    my @result;
    my @ary;
    my @aryw;
    my $istart=0;
    my $section=-1;
    my $isection=0;

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

    my %AVAILABLE;
    my @AVAILABLE;
    my $_search;
    if(defined $OPTIONS{ existspath }){
	$_search=$OPTIONS{ existspath } ;
	print  "dbcopy2 search: $_search\n" if get_verbose();
	my @_array=split(':',$_search);
	print "dbcopy2 array @_array\n" if get_verbose();
	foreach my $imat (@_array){
	    my @apaths=find_keys($SOURCE_DB,$imat);
	    if(@apaths){
		print "\timat  : $imat\n" if get_verbose();
		print "\t\tapaths: @apaths\n" if get_verbose();
		foreach my $iapath (@apaths){
		    print "\t\t\t @{ $iapath }\n" if get_verbose();
		    my @_path=@{ $iapath };
		    my $_name=pop @_path;
		    $AVAILABLE{$_name}=$iapath;
		}
	    }
	}
	@AVAILABLE = keys %AVAILABLE;
	die "dbcopy2: no entities found for path $_search\n" unless @AVAILABLE;
    }


    if(ref $t eq 'ARRAY'){
	@ary = @{ $t };

	if(exists($OPTIONS{section})){      # for selection of data between /-s
	    $section=$OPTIONS{section};
	}

	if(exists($OPTIONS{isection})){     # for selection of data between /-s
	    $isection=$OPTIONS{isection};
	}

	if($section >= 0){                  # for selection of data between /-s
	    @aryw=partarray($section,$isection,'/',@ary);
	    @ary=@aryw;
	}

	if(exists($OPTIONS{start})){
	    $istart=$OPTIONS{start};
	}

	if(exists($OPTIONS{stride})){
	    @aryw=stride($istart,$OPTIONS{stride},@ary);
	    @ary=@aryw;
	}

	if(exists($OPTIONS{select})){
	    if(lc($OPTIONS{select}) eq 'odd'){
		@aryw=odd(\@ary);
		@ary=@aryw;
	    }
	    elsif(lc($OPTIONS{select}) eq 'even'){
		@aryw=even(\@ary);
		@ary=@aryw;
	    }
	    else{
		warn "dbcopy2: select option $OPTIONS{select} not valid\n";
		return undef;
	    }
	}

	foreach ( @ary ){
	    die "dbcopy2: entity $_ not available in $_search\n"
		if(@AVAILABLE && !exists($AVAILABLE{$_}));
	    push @result, $def ? $def->($_) : $_;
	}
	return \@result;
    }
    elsif(ref $t eq 'HASH'){
	die "dbcopy: HASH copy not supported\n";
    }
    else{
	die "dbcopy2: entity $t not available in $_search\n"
	    if(@AVAILABLE && !exists($AVAILABLE{$t}));
	return $def ? $def->($t) : $t;
    }


}

sub value{
    my( $home, $value, %userparam ) = @_ ;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {$OPTIONS{$key}=$value;}
    my $def=undef;
    if(exists($OPTIONS{apply})){
	$def = eval "sub { return $OPTIONS{apply};}";
	die "value: invalid apply string $OPTIONS{apply}\n" unless ref $def eq 'CODE';
    }
    my $result = $def ? $def->($value) : $value;
    return $result;
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

#    my @a=fullcellmap($npin,@{ $cm_ref });
    my @a=fullcellmap($npin,$cm_ref);

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

    if(exists($OPTIONS{start})){
	@a=splice(@result,$OPTIONS{start});
	@result=@a;
    }

    if(exists($OPTIONS{stride})){
	@a=stride(0,$OPTIONS{stride},@result);
	@result=@a;
    }

    if(exists($OPTIONS{select})){
	if(lc($OPTIONS{select}) eq 'odd'){
	    @a=@result;
	    @result=odd(\@a);
	}
	elsif(lc($OPTIONS{select}) eq 'even'){
	    @a=@result;
	    @result=even(\@a);
	}
	else{
	    warn "copyarray: select option $OPTIONS{select} not valid\n";
	    return undef;
	}
    }
    if(@result == 0){
	return undef;
    }
    else{
	return \@result;
    }
}

sub copytable{
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

    my $nc=shift @result;
    my $nr=shift @result;

    if(exists($OPTIONS{columns})){
	@a=splice(@result,0,$nc);
	@result=@a;
    }

    if(exists($OPTIONS{rows})){
	@a=splice(@result,$nc,$nr);
	@result=@a;
    }

    if(exists($OPTIONS{data})){
	@a=splice(@result,$nc+$nr);
	@result=@a;
    }

    if(@result == 0){
	return undef;
    }
    else{
	return \@result;
    }
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

    if(exists($OPTIONS{sort})){
	if(lc($OPTIONS{sort}) eq 'name'){
	    @a=sort { $a cmp $b } @a;
	}
	elsif(lc($OPTIONS{sort}) eq 'name_reverse'){
	    @a=sort { $b cmp $a } @a;
	}
	elsif(lc($OPTIONS{sort}) eq 'number'){
	    @a=sort { $a <=> $b } @a;
	}
	elsif(lc($OPTIONS{sort}) eq 'number_reverse'){
	    @a=sort { $b <=> $a } @a;
	}
	else{
	    warn "copyhash: sort option $OPTIONS{sort} not valid\n";
	    return undef;
	}
    }

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
    print  "echos: @args\n";
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

    my $keyname;
    my $mattype;

    foreach my $ipath (@paths){
	my @apaths=find_keys($SOURCE_DB,$ipath);
	my @names =find_keys($SOURCE_DB,$ipath,undef,strings=>'true');
	push @mats, @apaths if @apaths;
	push @mats_names, @names if @names;
    }

    foreach my $imat_path (@mats){
	my @keypath=@{ $imat_path };
	$keyname=$keypath[$#keypath];
	unless($keypath[$#keypath-2] eq 'mat'){
	    die "matmap: invalid material type: @keypath\n";
	}

	my $enrichable=0;
	my $depletable= 'false';
	my $enrichment;
	my $thdensity=0;
	my @mat_names=();
	my @mat_fracs=();

	my @content=@{ key_defined($SOURCE_DB,@keypath,'_content') };
	my @rpath=@keypath[0..$#keypath-2];  # path to find options
	my %opk=%{ key_defined($SOURCE_DB,@rpath,'_options') };
	my @ak=keys %opk;

	my @opmat=extract_options(\@content); # options in input
	my %opths=@opmat if @opmat;

	my $density=shift @content;
	if(@content > 1){
	    @mat_names=even(\@content);
	    @mat_fracs=odd(\@content);
	}
	else{
	    $mattype=shift(@content) || $keyname;
	    push @mat_names, $mattype;
	    push @mat_fracs, 1.0;
	}

	my $mat_ref=&key_on_list($home,$basename.$keyname);
	&key_on_parameter($mat_ref,'density','double',$density);
	&key_on_parameter($mat_ref,'depletable','bool',$depletable) if ($depletable eq 'true');
	&key_on_parameter($mat_ref,'key_name','string',$keyname);

	foreach my $iop (keys(%opths)){
	    if(exists($opk{$iop})){
		&key_on_parameter($mat_ref,$iop,$opk{$iop}, $opths{$iop});
	    }
	    else{
		die "matmap: Invalid material option $iop in @content / @opmat\n";
	    }
	}

	&key_on_array($mat_ref,'mat_names','string', @mat_names);
	&key_on_array($mat_ref,'mat_fracs','double', @mat_fracs);

    }
}

sub fuelmap{
    my ($home,$basename,@paths)=@_;

    my @mats;
    my @mats_names;

    my $keyname;
    my $mattype;

    foreach my $ipath (@paths){
	my @apaths=find_keys($SOURCE_DB,$ipath);
	my @names =find_keys($SOURCE_DB,$ipath,undef,strings=>'true');
	push @mats, @apaths if @apaths;
	push @mats_names, @names if @names;
    }

    foreach my $imat_path (@mats){
	my @keypath=@{ $imat_path };
	$keyname=$keypath[$#keypath];
	unless($keypath[$#keypath-2] eq 'fuel'){
	    die "fuelmap: invalid material type: @keypath\n";
	}

	my $thdensity=0;
	my @mat_names=();
	my @mat_fracs=();
	my $gad_mat;
	my $gad_frac;
	my $use_gad=0;

	my @content=@{ key_defined($SOURCE_DB,@keypath,'_content') };
        my @rpath=@keypath[0..$#keypath-2];  # path to find options
        my %opk=%{ key_defined($SOURCE_DB,@rpath,'_options') };
	my @slshs=indexes { $_ eq '/' } @content;
        my $nslshs=scalar @slshs;

	if($nslshs < 1 || $nslshs > 3){
	    die "fuelmap: invalid number of slashes in command fuel @content\n";
	}

	my @part1=before {$_ eq '/'} @content;
	my @part2=after  {$_ eq '/'} @content;
	my @part3=();
        my @opmat=();
        if($nslshs > 1){
            @part3=after  {$_ eq '/'} @part2;
            @part2=before {$_ eq '/'} @part2;
            if($nslshs > 2){
                @opmat=after  {$_ eq '/'} @part3; #options
                @part3=before {$_ eq '/'} @part3;
            }
        }
        my %opths=@opmat if @opmat; #get option data types

# until the 1st slash
	my $density=shift @part1;
	$thdensity=shift @part1 || 0;

# after the 1st slash until 2nd slash or end
# Enrichment or number density composition
	if(is_float($part2[0])){
	    unshift @part2, 'u-235';
	}
	@mat_names  =even(\@part2);
	@mat_fracs  =odd(\@part2);

# 2nd slash to the 3rd slash or end
# For gadolinium or other dopants
	if(@part3){
	    $use_gad=1;
	    $gad_mat=shift  @part3;
	    $gad_frac=shift @part3;
	}

	my $mat_ref=&key_on_list($home,$basename.$keyname);
	&key_on_parameter($mat_ref,'density','double',$density);
	&key_on_parameter($mat_ref,'thden','double',$thdensity) if $thdensity;
	&key_on_parameter($mat_ref,'key_name','string',$keyname);

	if($use_gad){
	    &key_on_parameter($mat_ref,'gad_mat','string',$gad_mat);
	    &key_on_parameter($mat_ref,'gad_frac','double',$gad_frac);
	}

	&key_on_array($mat_ref,'fuel_names','string', @mat_names);
	&key_on_array($mat_ref,'enrichments','double',@mat_fracs);

        #Write options
        foreach my $iop (keys(%opths)){
            if(exists($opk{$iop})){
                &key_on_parameter($mat_ref,$iop,$opk{$iop}, $opths{$iop});
            }
            else{
                die "fuelmap: Invalid fuel option $iop in @content / @opmat\n";
            }
        }
    }
}

sub sourcemap{
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
        my @content=@{ key_defined($SOURCE_DB,@keypath,'_content') };

        my $mat_ref=&key_on_list($home,$basename.$keyname);

        my @slshs=indexes { $_ eq '/' } @content;
        if((@slshs<1) || !(@slshs<3)){
            die "sourcemap: invalid number of slashes in command source @content\n";
        }

        &key_on_parameter($mat_ref,'key_name','string',$keyname);

        my @part1= @content;
        my @part2=();
        my @part3=();
        if(@slshs >= 1){
           @part2=after  {$_ eq '/'} @part1;
           @part1=before {$_ eq '/'} @part1;
           @part3=();
        }
        if(@slshs == 2){
            @part3=after  {$_ eq '/'} @part2;
            @part2=before {$_ eq '/'} @part2;
        }

        if(@part1){
          if(($#part1+1)==2){
            $iso_id=$part1[0];
            &key_on_parameter($mat_ref,'iso_id','string',$iso_id);
            $iso_scal=$part1[1];
            &key_on_parameter($mat_ref,'iso_scaling_factor','double',$iso_scal);
            &key_on_array($mat_ref,'fractional_spectrum','double',@part2);
          }
          else{
            die "sourcemap: number of entries in first part exceeds 2 in command source @content\n";
          }
        }

        if(!(@part1)){
          &key_on_array($mat_ref,'absolute_spectrum','double',@part2);
        }

        if(($#part3+1)==2){
            $stt_str=$part3[0];
            $src_mult=$part3[1];
            &key_on_parameter($mat_ref,'init_strength','double',$stt_str);
            &key_on_parameter($mat_ref,'strength_mult','double',$src_mult);
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

sub coremapmap {
    my( $home, $csize_path, $cmap_path, $mmap_path, $bc_sym_path, %userparam ) = @_ ;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my @csize_path=parse_path($csize_path);
    my $csize=key_defined($SOURCE_DB,@csize_path);
    die "coremapmap: csize not valid [$csize_path] [@csize_path] [$csize]\n"
	if ref $csize;

    my @cmap_path=parse_path($cmap_path);
    my $cm_ref=key_defined($SOURCE_DB,@cmap_path);
    return undef unless $cm_ref;
    die "coremapmap: cm_ref not valid [$cmap_path] [@cmap_path] [$cm_ref]\n"
	unless ref $cm_ref eq 'ARRAY';

    my @mmap_path=parse_path($mmap_path);
    my $mm_ref=key_defined($SOURCE_DB,@mmap_path);
    return undef unless $mm_ref;
    die "coremapmap: mm_ref not valid [$mmap_path] [@mmap_path] [$mm_ref]\n"
	unless ref $mm_ref eq 'ARRAY';

    my @bc_sym_path=parse_path($bc_sym_path);
    my $bc_sym=key_defined($SOURCE_DB,@bc_sym_path);
    die "coremapmap: bc_sym not valid [$bc_sym_path] [@bc_sym_path] [$bc_sym]\n"
	if ref $bc_sym;

    unless(defined($bc_sym)){
	## ssmod
#	$bc_sym='mir';
	$bc_sym='rot';
    }

    $PATH_CM = source_from_path(@cmap_path);
    $PATH_MM = source_from_path(@mmap_path);
    $NAME_CM = name_from_path(@cmap_path);
    $NAME_MM = name_from_path(@mmap_path);
#    print "\nP1: $NAME_CM $PATH_CM\nP2: $NAME_MM $PATH_MM\n";

    err_set('PATH', $PATH_CM);
    err_set('PATH', $PATH_MM);
    err_set('NAME', $NAME_CM);
    err_set('NAME', $NAME_MM);
    my @a=core_map($cm_ref,$mm_ref,$csize,$bc_sym,%userparam);
    err_flushkey('PATH');
    err_flushkey('NAME');

    return \@a;
}

sub file_from_path{
    my $idx=2;
    if(@_[-2] eq '_key'){
        $idx = 1;
    }
    my @p=@_[-@_ .. -$idx];
    print "file_from_path: @_ : @p\n"  if get_verbose();
    return key_defined($SOURCE_DB,@_[-@_ .. -$idx], $FILE_LABEL);
}

sub line_from_path{
    my $idx=2;
    if(@_[-2] eq '_key'){
        $idx = 1;
    }
    my @p=@_[-@_ .. -$idx];
    print "line_from_path: @_ : @p\n"  if get_verbose();
    return key_defined($SOURCE_DB,@_[-@_ .. -$idx], $LINE_LABEL);
}

sub name_from_path{
    my $idx=2;
    if(@_[-2] eq '_key'){
        $idx = 1;
    }
    print "name_from_path: @_ : @_[-$idx]\n"  if get_verbose();
    return @_[-$idx];
}
sub keyword_from_path{
    my $idx=2;
    if(@_[-2] eq '_key'){
        $idx = 3;
    }
    print "keyword_from_path: @_ : @_[-$idx]\n"  if get_verbose();
    return @_[-$idx];
}
sub fileline_from_path{
    my ($file, $line);
    my $idx=2;
    if(@_[-2] eq '_key'){
        $idx = 1;
    }
    my @p=@_[-@_ .. -$idx];
    $file = key_defined($SOURCE_DB,@_[-@_ .. -$idx], $FILE_LABEL);
    $line = key_defined($SOURCE_DB,@_[-@_ .. -$idx], $LINE_LABEL);
    print "fileline_from_path: @_ : @p : $file | : $line\n"  if get_verbose();
    return ($file, $line);
}
sub source_from_path{
    my ($file, $line);
    my $idx=2;
    if(@_[-2] eq '_key'){
        $idx = 1;
    }
    my @p=@_[-@_ .. -$idx];

    $file = key_defined($SOURCE_DB,@_[-@_ .. -$idx], $FILE_LABEL);
    $line = key_defined($SOURCE_DB,@_[-@_ .. -$idx], $LINE_LABEL);
    print "source_from_path: @_ : @p : $file | : $line\n"  if get_verbose();
    return join(":line ", $file, $line);
}

sub mpact_mesh{
    my ($home,$basename,@paths)=@_;

    my @mats;
    my @mats_names;

    my $keyname;
    my $mattype;

    foreach my $ipath (@paths){
	my @apaths=find_keys($SOURCE_DB,$ipath);
	my @names =find_keys($SOURCE_DB,$ipath,undef,strings=>'true');
	push @mats, @apaths if @apaths;
	push @mats_names, @names if @names;
    }

    foreach my $imat_path (@mats){
	my @keypath=@{ $imat_path };
	$keyname=$keypath[$#keypath];
	unless($keypath[$#keypath-2] eq 'mesh'){
	    die "mpact_mesh: invalid mesh type: @keypath\n";
	}

	my @content=@{ key_defined($SOURCE_DB,@keypath,'_content') };

# count slashes
	my @slshs=indexes { $_ eq '/' } @content;
  if(@slshs == 1){
      my @part1=before {$_ eq '/'} @content;
      my @part2=after {$_ eq '/'} @content;

      # template
      my @num_rad = @part1;
      my @num_theta = @part2;

      my $mat_ref=&key_on_list($home,$basename.$keyname);
      &key_on_parameter($mat_ref,'label','string',$keyname);
      &key_on_array($mat_ref,'num_rad','int', @num_rad);
      &key_on_array($mat_ref,'num_theta','int', @num_theta);
  }elsif(@slshs == 0){
      my @part1=@content;
      my $np1=@part1;
      if($np1 != 2){
        die "mpact_mesh: must specify nx and ny for rectangular mesh! @content\n";
      }

      # template
      my $nx=@content[0];
      my $ny=@content[1];

      my $mat_ref=&key_on_list($home,$basename.$keyname);
      &key_on_parameter($mat_ref,'label','string',$keyname);
      &key_on_parameter($mat_ref,'nx','int', $nx);
      &key_on_parameter($mat_ref,'ny','int', $ny);
  }else{
    die "mpact_mesh: invalid number of slashes in MPACT command mesh @content\n";
  }
    }
}

# Tc=(Tf-32)/1.8
# Tc=Tk-273.15
# Tc=Tc
sub toCelsius{
    my( $home, $path, %userparam ) = @_ ;
    my %OPTIONS;
    my $result;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }
    my $def=undef;
    if(exists($OPTIONS{apply})){
	$def = eval "sub { return $OPTIONS{apply};}";
	die "toCelsius: invalid apply string $OPTIONS{apply}\n" unless ref $def eq 'CODE';
    }

    my @path=parse_path($path);
    my $t=key_defined($SOURCE_DB,@path);

    return $t unless defined($t);

    if(ref $t eq 'ARRAY'){
	my ($T,$unit)=@{ $t };
	if($unit eq 'F'){
	    $result=($T-32)/1.8;
	}
	elsif($unit eq 'K'){
	    $result=$T-273.15;
	}
	elsif($unit eq 'C'){
	    $result=$T;
	}
	else{
	    die "toCelsius: invalid temperature unit $unit\n";
	}
	if($result < -273.15){
	    die "toCelsius: invalid temperature value $result\n";
	}
    }
    else{
	die "toCelsius: incorrect data stored. Email the developer, simunovics@ornl.gov.\n";
    }

    $result = $def ? $def->($result) : $result;

    return $result;
}

sub pathfind{
    my ($path, %userparam)=@_;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my @trpath=find_keys($SOURCE_DB,$path,undef,strings=>'true');
    die "pathfind: path $path not found.\n" unless (@trpath);
    die "pathfind: multiple values found for $path.\n" if (@trpath>1 && exists($OPTIONS{dieonmultiple}) );

    print "pathfind: $path = @trpath\n" if exists $OPTIONS{debug};

    my $val=shift @trpath;

    return $val;
}

sub findfirst{
    my ($path, %userparam)=@_;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )
    {$OPTIONS{$key}=$value;}

    my @trpath=find_defined($SOURCE_DB,$path,undef,strings=>'true');
    die "findfirst: path $path not found.\n" unless (@trpath);
    die "findfirst: multiple values found for $path.\n" if (@trpath>1 && exists($OPTIONS{dieonmultiple}) );

    print "findfirst: $path = @trpath\n" if exists $OPTIONS{debug};

    my $val=shift @trpath;

    return $val;
}

sub pathlevel{
    my ($path, $level, %userparam)=@_;
    my %OPTIONS;

    $level=int $level;
    die "pathlevel: level $level too low.\n" if $level <= 0;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my @trpath=split /\//, $path;
    die "pathlevel: path $path cannot be split.\n" unless (@trpath);
    die "pathlevel: path $path too short for level $level.\n" if $level > @trpath;

    $level--;

    $level = $trpath[$level];
    return $level;
}

sub namesunique{
    my ($home,$path, %userparam)=@_;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    print "namesunique: $path\n" if get_verbose();
    my @trpath=find_keys($SOURCE_DB,$path);
    my @trsubs=();
    my $keyw;
    foreach my $ipath ( @trpath ){
	my @aipath = @{ $ipath };
	print "namesunique: aipath @aipath\n"  if get_verbose();
	my $kr=key_defined($SOURCE_DB,@aipath);
	die "namesunique: invalid reference for @aipath\n" unless $kr;
        my $file=file_from_path(@aipath);
        my $line=line_from_path(@aipath);
        $keyw=keyword_from_path(@aipath);
	print "namesunique: file $file\n"  if get_verbose();
	print "namesunique: line $line\n"  if get_verbose();
        my $aaipath = pop @aipath;
	push @trsubs, $aaipath;
        err_set('NUNQ_VAR', $aaipath);
        err_set('NUNQ_FILE', $file);
        err_set('NUNQ_LINE', $line);
    }

    print "namesunique: trsubs @trsubs\n" if get_verbose();
    my @trtmp=@trsubs;
    if(@trsubs){
        if(@trtmp != unique(@trsubs)){
            my @dups=duplicate(@trsubs);
            my @dupsidx=duplicateidx(@trsubs);
            my @dup_var =err_list('NUNQ_VAR');
            my @dup_file=err_list('NUNQ_FILE');
            my @dup_line=err_list('NUNQ_LINE');
            print "namesunique: duplicate input for keyword $keyw.\n";
            print "   duplicate entries @dups in list @trtmp.\n";
            for(my $i=0; $i<@trsubs; $i++){
                if($dupsidx[$i]){
                    print "   parameter $dup_var[$i] defined in $dup_file[$i], line $dup_line[$i]\n";
                }
            }
            die "parser failed\n";
        }
        else{
            err_flushkey('NUNQ_VAR');
            err_flushkey('NUNQ_FILE');
            err_flushkey('NUNQ_LINE');
        }
    }

    undef;
}

sub cellsmaps{
    my ($home,
	$cellmap_path,
	$cell_path,
	$npin_path,
	$axial_path,
	%userparam)=@_;

    my ($i,$j,$k,$m,$n);
    my (@a,@b,@c,@d);

    my @MATS_RESERVED =('vacuum','mod','cool');

    my %OPTIONS=('cellmapname'=>'CellMap_',
		 'cellname'=>'Cell_',
		 'mapname'=>'rodmap');
    while ( my ($key, $value) = each %userparam )
    {$OPTIONS{$key}=$value;}

    # check if internal variable is set to use blademap instead
    if(existsvar($home, '_axtyp')){
        my $vvar=valuevar($home,'_axtyp');
        print "cellsmaps: exists _axtyp : $vvar : $axial_path\n" if get_verbose();
        return unless $vvar eq $OPTIONS{'mapname'};
    }

    # get axial id and content
    my @axial_rpath = parse_path($axial_path);
    print  "axial_rpath: @axial_rpath\n" if get_verbose();
    my $axial_ref=key_defined($SOURCE_DB,@axial_rpath);
    return unless $axial_ref;
    my $axial_name=$axial_rpath[-2];
    my @AXIAL_CONTENT = @{ $axial_ref };
    @a=@AXIAL_CONTENT;
    unless(@a%2){
        die "cellsmaps: axial $axial_name has even number of elements @a\n";
    }
    @b=even(\@a);
    @c=odd(\@a);
    my @AXIAL_LABELS = @c;
    print  "         content: @AXIAL_CONTENT\n" if get_verbose();
    print  "         heights: @b\n" if get_verbose();
    print  "         labels : @c\n" if get_verbose();

    # get materials from material paths
    my $MATS_DB;
    my $mat_search;
    if(defined $OPTIONS{ matsearch }){
	$mat_search=$OPTIONS{ matsearch } ;
	print  "mat_search: $mat_search\n" if get_verbose();
        $MATS_DB=matsearch($mat_search);
    }

    # create hash of all cellmap ids and their values
    my @cellmap_rpath = parse_path($cellmap_path);
    print  "cellmap_rpath: @cellmap_rpath\n" if get_verbose();
    my $cellmap_ref=key_defined($SOURCE_DB,@cellmap_rpath);
    return unless $cellmap_ref;      # SSTODO: this would work for
                                     # blade types. But it would not
                                     # return error for messed up
                                     # lattices. Let's have it this
                                     # way and fix the error trigger
                                     # later.
    my @cellmap_available = keys_at($cellmap_ref);

    # get npin for setting the maps
    my @npin_rpath=parse_path($npin_path);
    print  "npin_rpath: @npin_rpath\n" if get_verbose();
    my $npin=key_defined($SOURCE_DB,@npin_rpath);
    print  "npin: $npin\n" if get_verbose();
    return unless $npin; # should it bomb here?

    # see if we have all cellmaps needed
    @AXIAL_LABELS_UNIQUE=unique( @AXIAL_LABELS );
    my @cellmap_common=intersection(\@AXIAL_LABELS_UNIQUE,\@cellmap_available);
    unless($#cellmap_common == $#AXIAL_LABELS_UNIQUE){
	print  "axial labels needed   : [@AXIAL_LABELS_UNIQUE]\n";
	print  "$OPTIONS{mapname} labels available: [@cellmap_available]\n";
	die   "missing $OPTIONS{mapname} definitions in $axial_path\n";
    }

    my %CELLMAP_DEFS;
    my %CELLMAP_CONTENT;
    my %CELLMAP_CELLS;
    foreach (@cellmap_available){
	$CELLMAP_DEFS{$_} = key_exists($cellmap_ref,$_);
	$CELLMAP_CONTENT{$_}=[@{ $CELLMAP_DEFS{$_}->{_content} }];
	print  "  CELLMAP_DEFS{$_}: $CELLMAP_DEFS{$_}\n" if get_verbose();

	@a=@{ $CELLMAP_CONTENT{$_} };
	@b=();
	@c=unique(@a);   # why?
#	@c=nonzero(@c);  # why?
	@c=nonstring('-',@c);
	$CELLMAP_CELLS{$_}=[@c];
	print  "  CELLMAP_CELLS{$_}: @c\n" if get_verbose();

	@b=fullcellmap($npin,\@a);
	$CELLMAP_CONTENT{$_}=[@b];
    }

    my ($cell_available, $CELL_TYPE, $CELL_TABLE, $CELL_mats, $CELL_radii)=
        cellsearch($cell_path, \@MATS_RESERVED, $mat_search, $MATS_DB);

    my ($iref, $jref, $a_ref, $cm_ref, $c_ref);

    # Create CellMaps list in Assembly_X
    $cm_ref=&key_on_list($home,'CellMaps');
    @c=();
    foreach $j (@AXIAL_LABELS_UNIQUE){
	# Create CellMap in CellMaps list
	$iref=&key_on_list($cm_ref,$OPTIONS{cellmapname}.$j);

	&key_on_parameter($iref,'label','string',$j);
	&key_on_array($iref,'cell_map','string',@{ $CELLMAP_CONTENT{$j} });
	push @c, @{ $CELLMAP_CELLS{$j} }
    }

    @b=unique(@c);
    # see if we have all cells needed
    my @cell_common=intersection(\@b,$cell_available);
    unless($#cell_common == $#b){
	print  "cell labels needed   : [@b]\n";
	print  "cell labels available: [@{$cell_available}]\n";
	die   "cellsmaps: missing cell definitions in $axial_path\n";
    }

    # Create Cells list in Assembly_X
    $c_ref=&key_on_list($home,'Cells');
    foreach $j (@b){
	# Create Cells in Cells list
	$iref=&key_on_list($c_ref,$OPTIONS{cellname}.$j);

	&key_on_parameter($iref,'label','string',$j);
	&key_on_parameter($iref,'type','string',$CELL_TYPE->{$j});
	unless( $CELL_TABLE->{$j} eq '' ) {
	  &key_on_parameter($iref,'table_label','string',$CELL_TABLE->{$j});
	}
	$k=@{ $CELL_radii->{$j} };
	&key_on_parameter($iref,'num_rings','int',$k);
	&key_on_array($iref,'mats','string',@{ $CELL_mats->{$j} });
	&key_on_array($iref,'radii','double',@{ $CELL_radii->{$j} });
    }
}

sub listscompare{
    my ($home,
	$axial_path,
	$coremap_path,
	%userparam)=@_;

    my ($i,$j,$k,$m,$n);
    my (@a,@b,@c,@d);

    my %OPTIONS=('compare'=>'eq','purge2'=>1);
    while ( my ($key, $value) = each %userparam )
    {$OPTIONS{$key}=$value;}

#    my @apaths=find_keys($SOURCE_DB,$axial_path,undef,strings=>'true');
#    my @cpaths=find_keys($SOURCE_DB,$coremap_path,undef,strings=>'true');

    my @apaths=find_keys($SOURCE_DB,$axial_path);
    my @cpaths=find_keys($SOURCE_DB,$coremap_path);

    my @a1;
    foreach my $ipath (@apaths){
	my @p = @{ $ipath };
	if($p[-2] eq '_key'){
	    push @a1, $p[-1];
	}
	elsif($p[-2] eq '_content'){
	    my $t=key_defined($SOURCE_DB,@p);
	    die "listscompare: undefined value at @p\n" unless defined($t);
	    push @a1, $t;
	}
	else{
	    die "listscompare: invalid path @p\n";
	}
    }

    my @a2;
    foreach my $ipath (@cpaths){
	my @p = @{ $ipath };
	if($p[-2] eq '_key'){
	    push @a2, $p[-1];
	}
	elsif($p[-2] eq '_content'){
	    my $t=key_defined($SOURCE_DB,@p);
	    die "listscompare: undefined value at @p\n" unless defined($t);
	    push @a2, $t;
	}
	else{
	    die "listscompare: invalid path @p\n";
	}
    }

    @a1=unique(@a1);
    @a2=unique(@a2);
    if( exists($OPTIONS{purge2}) && $OPTIONS{purge2} ){
	@a2=nonstring('0',@a2);
	@a2=nonstring('-',@a2);
    }
    if( exists($OPTIONS{purge1}) && $OPTIONS{purge1} ){
	@a1=nonstring('0',@a1);
	@a1=nonstring('-',@a1);
    }

    my @acommon=intersection(\@a1,\@a2);

    print "listscompare: have[$axial_path]: @a1\n"   if exists $OPTIONS{debug};
    print "listscompare: need[$coremap_path]: @a2\n" if exists $OPTIONS{debug};
    print "listscompare: common[".scalar(@acommon)."]: @acommon\n" if exists $OPTIONS{debug};

    if($OPTIONS{compare} eq 'eq'){
	unless($#a2 == $#acommon){
	    print  "needed   : @a2\n";
	    print  "available: @a1\n";
	    die   "listscompare: mismatch in arrays\n";
	}
    }
    elsif($OPTIONS{compare} eq 'geq'){
	unless($#a2 >= $#acommon){
	    print  "need: @a2\n";
	    print  "have: @a1\n";
	    die   "listscompare: mismatch in arrays\n";
	}
    }
    else{
	die   "listscompare: invalid comparison operator\n";
    }

    undef;
}

sub matsearch{
    my $mat_search=shift @_;
    
    my %MATS_DB;
    my @mat_array=split(':',$mat_search);
    print "matsearch: mat_array @mat_array\n" if get_verbose();
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
                if( @mat_path[-3] =~ m/(fuel)/ ){  # cheeky
                    $mat_flags[1]='fuel';
                }
                
                if(exists $MATS_DB{ $mat_flags[0] }){
                    my $mat_type=$MATS_DB{ $mat_flags[0] };
                    if($mat_type ne $mat_flags[1]){
                        die "matsearch: material and fuel keyword use same identifiers.\n"
                    }
                }
                
                unless(exists $MATS_DB{ $mat_flags[0] }){
                    $MATS_DB{ $mat_flags[0] } = $mat_flags[1];
                    print "\t\t\t\tMATS_DB{$mat_flags[0]}=$mat_flags[1]\n" if get_verbose();
                }
            }
        }
    }
    return \%MATS_DB;
}

sub cellsearch{
    my ($cell_path, $MATS_RESERVED, $matsearch, $MATS_DB)=@_;
    my %CELL_TYPES_POSSIBLE=( 'large4' => 1 );

    # create hash of all cell ids and their values
    my @cell_rpath = parse_path($cell_path);
    print  "cell_rpath: @cell_rpath\n" if get_verbose();
    my $cell_ref=key_defined($SOURCE_DB,@cell_rpath);
    my @cell_available = keys_at($cell_ref);
    print  "cell_rpath: @cell_rpath\n" if get_verbose();

    my %CELL_DEFS;
    my %CELL_CONTENT;
    foreach (@cell_available){
	$CELL_DEFS{$_} = key_exists($cell_ref,$_);
	$CELL_CONTENT{$_}=[@{ $CELL_DEFS{$_}->{_content} }];
	print  "  CELL_DEFS{$_}: $CELL_DEFS{$_}\n" if get_verbose();
	print  "        content: @{ $CELL_CONTENT{$_} }\n" if get_verbose();

	@a=@{$CELL_CONTENT{$_}};
	if(@a==1){
	    if($a[0] ne 'mod'){
		die "cellmaps: cell $_ @a has one entry and is not a moderator\n";
	    }
	    $CELL_TYPE{$_}='mod';
	    $CELL_radii{$_}=[];
	    $CELL_mats{$_} =['mod'];
	}
	else{

# Per Scott's three commands in one
	    my @slshs=indexes { $_ eq '/' } @a;
	    if(@slshs < 1 && @slshs > 2){
		die "cellmaps: invalid number of slashes in command cell $_ @a\n";
	    }

	    my @part1=before {$_ eq '/'} @a;
	    my @part2=after  {$_ eq '/'} @a;
	    my @part3=();
	    if(@slshs == 2){
		@part3=after  {$_ eq '/'} @part2;
		@part2=before {$_ eq '/'} @part2;
	    }
	    die "cellmaps: unequal number of entries for radii and materials in cell $_ @a\n" if (@part1 != @part2);
	    $CELL_radii{$_}=\@part1;
	    my @cmats=@part2;

        # start mod
        # have to search for available materials and fuels
        # bomb if mat and fuel are at the same level
        # if exists mat cell_type=other, if exists fuel=fuel
        $CELL_TYPE{$_}='other';
        $CELL_TABLE{$_}='';
        if(@part3){
          if(exists $CELL_TYPES_POSSIBLE{$part3[0]} ){
            $CELL_TYPE{$_}=$part3[0];
          }
          else {
            $CELL_TABLE{$_}=$part3[0];
          }
        }

        if($matsearch){
          foreach my $imat (@cmats){
            print  "    CELL mat $imat\n" if get_verbose();
            next if in_dictionary($imat, @{$MATS_RESERVED});
            if(exists($MATS_DB->{ $imat })){
            if($MATS_DB->{ $imat } eq 'fuel'){
              die "rodmap: cell $_ @a type is $CELL_TYPE{$_} but it has fuel $imat\n"
              if exists( $CELL_TYPES_POSSIBLE{ $CELL_TYPE{$_} } );
                $CELL_TYPE{$_}='fuel';
                print  "    \tCELL mat $imat is fuel\n" if get_verbose();
              }
            }
            else{
              die "rodmap: cell $_ @a has material $imat which is not defined\n";
            }
          }
        }

	    $CELL_mats{$_} =[@cmats];
	    print  "    CELL radii @{ $CELL_radii{$_} }\n" if get_verbose();
	    print  "    CELL mats  @{ $CELL_mats{$_} }\n" if get_verbose();
	    print  "    CELL type  $CELL_TYPE{$_}\n" if get_verbose();
	    print  "    CELL table  $CELL_TABLE{$_}\n" if get_verbose();
	}
    }
    return \@cell_available, \%CELL_TYPE, \%CELL_TABLE, \%CELL_mats, \%CELL_radii;
}

sub setaxialtype{
    my ($home,
        $varname,
	$cellmap_path,
	$blade_path,
	$axial_path)=@_;

    my ($i,$j,$k,$m,$n);
    my (@a,@b,@c,@d);

    # get axial id and content
    my @axial_rpath = parse_path($axial_path);
    print  "axial_rpath: @axial_rpath\n" if get_verbose();
    my $axial_ref=key_defined($SOURCE_DB,@axial_rpath);
    return unless $axial_ref;
    my $axial_name=$axial_rpath[-2];
    my @AXIAL_CONTENT = @{ $axial_ref };
    @a=@AXIAL_CONTENT;
    unless(@a%2){
	    die "setaxialtype: axial $axial_name has even number of elements @a\n";
    }
    @b=even(\@a);
    @c=odd(\@a);
    my @AXIAL_LABELS = @c;
    print  "         content: @AXIAL_CONTENT\n" if get_verbose();
    print  "         heights: @b\n" if get_verbose();
    print  "         labels : @c\n" if get_verbose();


    # create hash of all cellmap ids and their values
    my @cellmap_rpath = parse_path($cellmap_path);
    print  "cellmap_rpath: @cellmap_rpath\n" if get_verbose();
    my $cellmap_ref=key_defined($SOURCE_DB,@cellmap_rpath);

    # create hash of all blade ids and their values
    my @blademap_rpath = parse_path($blade_path);
    print  "blademap_rpath: @blademap_rpath\n" if get_verbose();
    my $blademap_ref=key_defined($SOURCE_DB,@blademap_rpath);

    my @cellmap_available  = $cellmap_ref  ? keys_at($cellmap_ref)  : ();
    my @blademap_available = $blademap_ref ? keys_at($blademap_ref) : ();

    # see if we have all cell/blade maps needed
    @AXIAL_LABELS_UNIQUE=unique( @AXIAL_LABELS );
    my @cellmap_common =intersection(\@AXIAL_LABELS_UNIQUE,\@cellmap_available);
    my @blademap_common=intersection(\@AXIAL_LABELS_UNIQUE,\@blademap_available);

    if($#cellmap_common == $#AXIAL_LABELS_UNIQUE){
        setvar($home,$varname,'rodmap');
        return undef;
    }
    elsif($#blademap_common == $#AXIAL_LABELS_UNIQUE){
        setvar($home,$varname,'bladetype');
        return undef;
    }
    else{
	print  "axial labels needed    : [@AXIAL_LABELS_UNIQUE]\n";
	print  "rodmap labels available: [@cellmap_available]\n";
	print  "blade labels available : [@blademap_available]\n";
        die   "missing definitions in $axial_path\n";
    }
}

sub blademaps{
    my ($home,
	$blade_path,
	$blade_geom_path,
	$cell_path,
	$axial_path,
	%userparam)=@_;

    my ($i,$j,$k,$m,$n);
    my (@a,@b,@c,@d);

    my @MATS_RESERVED =('vacuum','mod','cool');

    my %OPTIONS=('cellmapname'=>'BladeType_',
                 'cellgeomname' => 'BladeGeom_',
		 'cellname'=>'BladeCell_',
		 'mapname'=>'bladetype');
    while ( my ($key, $value) = each %userparam )
    {$OPTIONS{$key}=$value;}

    # check if internal variable is set to use cellmap instead
    if(existsvar($home, '_axtyp')){
        my $vvar=valuevar($home,'_axtyp');
        print "blademaps: exists _axtyp : $vvar : $axial_path\n" if get_verbose();
        return unless $vvar eq $OPTIONS{'mapname'};
    }

    # get axial id and content
    my @axial_rpath = parse_path($axial_path);
    print  "axial_rpath: @axial_rpath\n" if get_verbose();
    my $axial_ref=key_defined($SOURCE_DB,@axial_rpath);
    return unless $axial_ref;
    my $axial_name=$axial_rpath[-2];
    my @AXIAL_CONTENT = @{ $axial_ref };
    @a=@AXIAL_CONTENT;
    unless(@a%2){
        die "blademaps: axial $axial_name has even number of elements @a\n";
    }
    @b=even(\@a);
    @c=odd(\@a);
    my @AXIAL_LABELS = @c;
    print  "         content: @AXIAL_CONTENT\n" if get_verbose();
    print  "         heights: @b\n" if get_verbose();
    print  "         labels : @c\n" if get_verbose();

    # get materials from material paths
    my $MATS_DB;
    my $mat_search;
    if(defined $OPTIONS{ matsearch }){
	$mat_search=$OPTIONS{ matsearch } ;
	print  "mat_search: $mat_search\n" if get_verbose();
        $MATS_DB=matsearch($mat_search);
    }

    # create hash of all blade ids and their values
    my @blademap_rpath = parse_path($blade_path);
    print  "blademap_rpath: @blademap_rpath\n" if get_verbose();
    my $blademap_ref=key_defined($SOURCE_DB,@blademap_rpath);
    return unless $blademap_ref;
    my @blademap_available = keys_at($blademap_ref);

    # create hash of all blade_geom ids and their values
    my @blade_geommap_rpath = parse_path($blade_geom_path);
    print  "blade_geommap_rpath: @blade_geommap_rpath\n" if get_verbose();
    my $blade_geommap_ref=key_defined($SOURCE_DB,@blade_geommap_rpath);
    return unless $blade_geommap_ref;
    my @blade_geommap_available = keys_at($blade_geommap_ref);

    # see if we have all blademaps needed
    @AXIAL_LABELS_UNIQUE=unique( @AXIAL_LABELS  );
    my @blademap_common=intersection(\@AXIAL_LABELS_UNIQUE,\@blademap_available);
    unless($#blademap_common == $#AXIAL_LABELS_UNIQUE){
	print "axial labels needed   : [@AXIAL_LABELS_UNIQUE]\n";
	print "$OPTIONS{mapname} labels available: [@blademap_available]\n";
	die   "missing $OPTIONS{mapname} definitions in $blade_path\n";
    }

    my %BLADEMAP_DEFS;
    my %BLADEMAP_CONTENT;
    my @BLADEMAP_CELLS;
    my @BLADEMAP_GEOMS;
    @a=();
    @b=();
    foreach (@blademap_common){
	$BLADEMAP_DEFS{$_} = key_exists($blademap_ref,$_);
	$BLADEMAP_CONTENT{$_}=[@{ $BLADEMAP_DEFS{$_}->{_content} }];
        $BLADEMAP_GEOM{$_}  = $BLADEMAP_CONTENT{$_}->[0];

        push @a, $BLADEMAP_CONTENT{$_}->[0];
        unless( $BLADEMAP_CONTENT{$_}->[3] eq '-' ){
            push @b, $BLADEMAP_CONTENT{$_}->[3];
        }
	print  "  BLADEMAP_DEFS{$_}: $BLADEMAP_DEFS{$_}\n" if get_verbose();
    }
    @BLADEMAP_GEOMS=unique(@a);
    @BLADEMAP_CELLS=unique(@b);

    # see if we have all blade_geommaps needed
    my @blade_geommap_common=intersection(\@BLADEMAP_GEOMS,\@blade_geommap_available);
    unless($#blade_geommap_common == $#BLADEMAP_GEOMS){
	print  "blade_geom labels needed   : [@BLADEMAP_GEOMS]\n";
	print  "blade_geom labels available: [@blade_geommap_available]\n";
	die    "missing blade_geom definitions in $blade_geom_path\n";
    }

    my %BLADE_GEOMMAP_DEFS;
    my %BLADE_GEOMMAP_CONTENT;
    foreach (@blade_geommap_common){
        $BLADE_GEOMMAP_DEFS{$_} = key_exists($blade_geommap_ref,$_);
        $BLADE_GEOMMAP_CONTENT{$_}=[@{ $BLADE_GEOMMAP_DEFS{$_}->{_content} }];
	print  "  BLADE_GEOMMAP_DEFS{$_}: $BLADE_GEOMMAP_DEFS{$_}\n" if get_verbose();
    }

    my ($cell_available, $CELL_TYPE, $CELL_TABLE, $CELL_mats, $CELL_radii)=
        cellsearch($cell_path, \@MATS_RESERVED, $mat_search, $MATS_DB);

    # see if we have all cells needed
    my @cell_common=intersection(\@BLADEMAP_CELLS,$cell_available);
    unless($#cell_common == $#BLADEMAP_CELLS){
	print "cell labels needed   : [@BLADEMAP_CELLS]\n";
	print "cell labels available: [@{$cell_available}]\n";
	die   "blademaps: missing cell definitions in $cell_path\n";
    }

    my ($iref, $cm_ref);

    # Create Bladetypes list in Control_X
    $cm_ref=&key_on_list($home,'BladeTypes');
    foreach $j (@blademap_common){
	# Create Blade_Type entries
	$iref=&key_on_list($cm_ref,$OPTIONS{cellmapname}.$j);

	&key_on_parameter($iref,'label','string',$j);

	&key_on_parameter($iref,'bladegeomlabel','string',$BLADEMAP_CONTENT{$j}->[0]);
	&key_on_parameter($iref,'blademat','string',$BLADEMAP_CONTENT{$j}->[1]);
	&key_on_parameter($iref,'ntube','int',$BLADEMAP_CONTENT{$j}->[2]);
	&key_on_parameter($iref,'tubecell','string',$BLADEMAP_CONTENT{$j}->[3]);
	&key_on_parameter($iref,'tubefillermat','string',$BLADEMAP_CONTENT{$j}->[4]);
	&key_on_parameter($iref,'tubeorient','string',$BLADEMAP_CONTENT{$j}->[5]);
    }

    # Create Bladegeoms list in Control_X
    $cm_ref=&key_on_list($home,'BladeGeoms');
    foreach $j (@blade_geommap_common){
	# Create CellMap in CellMaps list
	$iref=&key_on_list($cm_ref,$OPTIONS{cellgeomname}.$j);

	&key_on_parameter($iref,'label','string',$j);

	&key_on_parameter($iref,'span',           'double',$BLADE_GEOMMAP_CONTENT{$j}->[0]);
	&key_on_parameter($iref,'thickness',      'double',$BLADE_GEOMMAP_CONTENT{$j}->[1]);
	&key_on_parameter($iref,'tipradius',      'double',$BLADE_GEOMMAP_CONTENT{$j}->[2]);
	&key_on_parameter($iref,'sheaththickness','double',$BLADE_GEOMMAP_CONTENT{$j}->[3]);
	&key_on_parameter($iref,'winglength',     'double',$BLADE_GEOMMAP_CONTENT{$j}->[4]);
    }

    # Create Blade_cells list in Control_X
    $cm_ref=&key_on_list($home,'BladeCells');
    foreach $j (@cell_common){
	# Create Cells in Cells list
	$iref=&key_on_list($cm_ref,$OPTIONS{cellname}.$j);

	&key_on_parameter($iref,'label','string',$j);
	&key_on_parameter($iref,'type','string',$CELL_TYPE->{$j});
	unless( $CELL_TABLE->{$j} eq '' ) {
	  &key_on_parameter($iref,'table_label','string',$CELL_TABLE->{$j});
	}
	$k=@{ $CELL_radii->{$j} };
	&key_on_parameter($iref,'num_rings','int',$k);
	&key_on_array($iref,'mats','string',@{ $CELL_mats->{$j} });
	&key_on_array($iref,'radii','double',@{ $CELL_radii->{$j} });
    }
}

1;
