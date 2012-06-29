package PL;

use KeyTree;

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
	 'PLkeyon'
    );

sub PLdoarg{
    my( $str, %userparam ) = @_ ;
    my %OPTIONS;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    $str =~ s/=>/,/g;
    $str =~ s/,/ /g;
    $str =~ s/^\s+//;
    $str =~ s/\s+$//;
    my @a=split / +/, $str;

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
    my ($ref,$actions,%userparam)=@_;
    my %OPTIONS;
    my $home=$ref;

    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$OPTIONS{$key}=$value;
    }

    my @PLcontent = keys %{ $ref->{_content} };

    print STDERR "PLlist: @PLcontent\n";


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
	    &PLlist($rref,$actions);
	}
	if($typ eq 'map'){
	    print STDERR "type map\n";
	    &PLlist($rref,$actions);
	}
    }
}

1;
