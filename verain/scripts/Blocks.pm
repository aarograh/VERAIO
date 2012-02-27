package Blocks;          # todo: muy brittle, must add error checks

use strict;
use Class::Struct;
use XML::LibXML;
use Data::Dumper;

use MyUtils;

my $DIRECTIVE_TABLE={
    STATE=>
    {
	power => \&parse_scalar,
	flow  => \&parse_scalar,
	rods  => \&parse_scalar,
	xenon => \&parse_scalar,
	sym   => \&parse_scalar,
	boron => \&parse_scalar,
	search=> \&parse_scalar,
	tmod  => \&parse_scalar,
	tfuel => \&parse_scalar,
	cycle => \&parse_scalar
    },
    MATERIAL =>
    {
	uo2   => \&parse_scalar,
	pyrex => \&parse_scalar,
	aic   => \&parse_scalar,
	b4c   => \&parse_scalar,
	ref   => \&parse_scalar,
    },
    CORE =>
    {
	size            => \&parse_scalar,
	apitch          => \&parse_scalar,
	rated           => \&parse_scalar,
	sym             => \&parse_scalar,
	baffle          => \&parse_scalar,
	barrel          => \&parse_scalar,
	bot_reflector   => \&parse_scalar,
	top_reflector   => \&parse_scalar,
	boundary        => \&parse_scalar,
	fuel            => \&parse_map,
	poison          => \&parse_map,
    },
    ASSEMBLY =>
    {
	title   => \&parse_scalar,
	pitch   => \&parse_scalar,
	offset  => \&parse_scalar,
	cell    => \&parse_scalar,
	layout  => \&parse_map,
	lattice => \&parse_map,
	assy    => \&parse_scalar,
	grid    => \&parse_scalar,
	spacers => \&parse_scalar,
	uo2     => \&parse_scalar,     # ?
    },
    INSERT => 
    {
	cell  => \&parse_scalar,
	rod   => \&parse_scalar,
	assy  => \&parse_map,
    },
    CONTROL=>
    {
	cell    => \&parse_scalar,
	rod     => \&parse_scalar,
	stroke  => \&parse_scalar,
	banks   => \&parse_map,
	types   => \&parse_scalar,
    },
    INSTRUMENT => 
    {
	cell   => \&parse_scalar,
	rod    => \&parse_scalar,
	layout => \&parse_map,
    },
    EDIT =>
    {
	restart => \&parse_scalar,
	ascii   => \&parse_scalar,
	silo    => \&parse_scalar,
    },
    DECART =>
    {
	file     => \&parse_scalar,
	mesh   => \&parse_scalar,
	ray   => \&parse_scalar,
	fuel_mesh   => \&parse_scalar,
	cmfd   => \&parse_scalar,
	conv_crit   => \&parse_scalar,
	reso_opt   => \&parse_scalar,
	boron   => \&parse_scalar,
	threads   => \&parse_scalar,
    },
    DENOVO =>
    {
	mesh      => \&parse_scalar,
	conv_crit => \&parse_scalar,
    },
    CASEID =>
    {
	CASEID   => \&parse_scalar,
    },
};

my %_VALID_KEYS=(          # quick fix, needed for tokenize and
			   # nothing else
    'STATE'      => 'split:',
    'MATERIAL'   => 'split:',
    'CORE'       => 'split:',
    'ASSEMBLY'   => 'split:',
    'INSERT'     => 'split:',
    'CONTROL'    => 'split:',
    'INSTRUMENT' => 'split:',
    'EDIT'       => 'split:',
    'DECART'     => 'split:',
    'DENOVO'     => 'split:',
    'CASEID'     => 'copy:',
    );

sub key_valid {
    my ($self,$key)=@_;
    return exists($_VALID_KEYS{$key}) ? 1 : 0;
}
sub keys {
    return \%_VALID_KEYS;
}

my %_VALID=('BLOCK'=>1, 'TEXT'=>1);

struct ( 
    'Blocks' => { BLOCK      => '$',     # block label
		  TEXT       => '$',     # block text w/o labels
		  NKEY       => '$',     # number of keywords
		  NVALUE     => '$',     # number of values
		  KEY        => '@',     # keywords
		  VALUE      => '@'      # values
    });

sub tokenize   # must replace it with error checking and sequential
	       # reading, convoluted big time multiline string split
               # on keywords for given block, keeps newlines
{
    my ($self, %args) = @_;
    my $i;
    my @a;

    my $blk=$self->BLOCK();
    my $txt=$self->TEXT();

    if($_VALID_KEYS{$blk} =~ /split/){
	my $pattern=join('|',keys %{ $DIRECTIVE_TABLE->{$blk}});
	@a=split(/^($pattern)/m,$txt);
	shift @a;
	for($i=0;$i<(@a-1);$i+=2){
	    push @{ $self->KEY }, $a[$i];
	    push @{ $self->VALUE }, $a[$i+1];
	    $self->NKEY($self->NKEY()+1);
	    $self->NVALUE($self->NVALUE()+1);;
	}
	return 1;
    }
    elsif($_VALID_KEYS{$blk} =~ /copy/){
	push @{ $self->KEY }, $blk;
	push @{ $self->VALUE }, $txt;
	$self->NKEY(1);
	$self->NVALUE(1);
	return 1;
    }
    else{
	return 0;
    }
}

sub init
{
    my ($self, %args) = @_;

    my $key;
    foreach (keys %args) {
	$key=uc($_);
	if(exists($_VALID{$key}) && 
	   exists($_VALID_KEYS{$args{$_}})){
	    $self->$key($args{$_});
	}
	else{
	    die "Blocks.pm: Invalid key pair ($key=>$args{$_}).\n";
	}
    }
    return $self;
}

sub append
{
    my ($self, %args) = @_;

    my $key;
    foreach (keys %args) {
	$key=uc($_);
	if(exists($_VALID{$key})){
	    my $c=$self->$key();     # todo: need to add handle for
				     # direct append
	    $self->$key($c.$args{$_});
	}
    }
    return $self;
}

sub to_string         # why this?
{
    my ($self, $arg) = @_;
    return $self->$arg();
}

sub dump
{
    my ($self, $arg) = @_;
    print Data::Dumper->Dump([\$self], [qw(BLOCK)]);
}


sub parse_scalar {    # basic xml setup prototype for scalar, sets a
		      # plain scalar node, need to add attributes,
		      # here takes the entire line, whatever it is,
		      # and puts it into scalar
    my ($name,$value)=@_;
    my $node;

# quick fix for parameter list
    my $i;
    my @content;
    my $iname='name';
    $value=~s/\// /g;
    $value=~s/^\s+//mg;
    if($name=~ m/(CASEID)|(title)/){
	@content[0]=$value;
    }
    else{
	@content=split /\s+/, $value;
    }
    if(@content>1){
	$node = XML::LibXML::Element->new( 'ParameterList' );
	$node->setAttribute( 'name', $name );
	for($i=0;$i<@content;$i++){
	    my $nodei = XML::LibXML::Element->new( 'Parameter' );
	    $nodei->setAttribute( 'name', $name.".".$i );
	    if(is_numeric($content[$i])){
		$nodei->setAttribute( 'type',  'double' );
	    }
	    else{
		$nodei->setAttribute( 'type',  'string' );
	    }	       
	    $nodei->setAttribute( 'value', $content[$i] );
	    $node->appendChild( $nodei );
	}
    }
    else{
	$node = XML::LibXML::Element->new( 'Parameter' );
	$node->setAttribute( 'name', $name );
	if(is_numeric($content[0])){
	    $node->setAttribute( 'type',  'double' );
	}
	else{
	    $node->setAttribute( 'type',  'string' );
	}	       
	$node->setAttribute( 'value', $content[0] );
    }

#    my $node = XML::LibXML::Element->new( $name );
#    $node->appendTextNode( $value );
    return $node;
}

sub parse_map {       # basic setup for reactor maps, need some
		      # consistency in the definition, this way too
		      # messy
    my ($name,$value)=@_;
    my $i;
    my $j;
    my @a;
    my $b;
    my @b;
    my $irow=0;

#    my $node = XML::LibXML::Element->new( $name );
    my $node = XML::LibXML::Element->new( "ParameterList" );
    $node->setAttribute( 'name', $name );

    @a=split /\n+/, $value;
    for($i=0;$i<@a;$i++){
#	my $inode = XML::LibXML::Element->new( 'map' );

	my $inode = XML::LibXML::Element->new( "ParameterList" );
	$inode->setAttribute( 'name', 'row' );
	my $jnode = XML::LibXML::Element->new( "Parameter" );
	$jnode->setAttribute( 'name', 'rowNumber' );
	$jnode->setAttribute( 'type', 'int' );
	$jnode->setAttribute( 'value', $i );
	$inode->appendChild( $jnode );

	$a[$i]=~s/^\s+//;
	$a[$i]=~s/\s+$//;
	@b=split /\s+/, $a[$i];
	if(@b){
	    $b=join(',',@b);
	    $b='{'.$b.'}';
	    my $knode = XML::LibXML::Element->new( "Parameter" );
	    $knode->setAttribute( 'name', 'rowData' );
	    $knode->setAttribute( 'type', 'Array(string)' );
	    $knode->setAttribute( 'value', $b );
	    $inode->appendChild( $knode );
	}

#	$inode->setAttribute( 'row', $i );
#	$inode->appendTextNode( $a[$i] );

	$node->appendChild( $inode );
    }
    return $node;
}

sub to_XML {       # from tokenized arrays, make XML nodes and append
		   # at the current tree level
    my ($self, %args) = @_;
    my $i;

    my $blkname=$self->BLOCK();
    my $actions = $DIRECTIVE_TABLE->{$blkname};

#    my $node = XML::LibXML::Element->new( $blkname );

    my $node = XML::LibXML::Element->new( "ParameterList" );
    $node->setAttribute( 'name', $blkname );

    my $nkeys=$self->NKEY();    # todo: must check for equality at
				# construction
    for($i=0;$i<$nkeys;$i++){
	my $directive = $self->KEY($i);
	my $rest = $self->VALUE($i);

	# todo: keep for a reminder, need to fix sorting package
	if (exists $actions->{$directive} || 
	    &default_action($directive,keys %{ $DIRECTIVE_TABLE->{$blkname} }) ){
	    my $directivenode=$actions->{$directive}->($directive, $rest);
	    $node->appendChild( $directivenode );
	} else {
	    die "Unrecognized directive $directive; aborting";
	}
    }
    return $node;  # Success
}

sub default_action {     # for some other time, for String::Approx
    my ($key, @commands)=@_;
    die "Bad command $key, available @commands\n";
}


1;
