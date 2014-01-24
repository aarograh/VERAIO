package REACTORBlock;

# use Clone qw(clone);
use ClonePP qw(clone);
use Carp;
use Data::Dumper ;

use KeyTree;
use MiscUtils;
use TypeUtils;
use REACTORCommand;

my %BLOCK_COUNTERS;

{
    my $_count = 0;
    sub get_count {$_count;}
    sub _incr_count { ++$_count }
    sub _decr_count { --$_count }

    my $_VERBOSE = 0;
    sub get_verbose  {$_VERBOSE;}
    sub set_verbose { $_VERBOSE = 1; }

    my $_DEBUG = 0;
    sub get_debug  {$_DEBUG;}
    sub set_debug { $_DEBUG = 1; }
}

sub new
{
    my ($class, %arg) = @_;
    bless{
	name    => $arg{name}    || croak("missing block name"),
	inp_db  => $arg{inp_db}  || undef,
	out_db  => $arg{out_db}  || undef,
	named   => $arg{named}   || 0,
	keytree => undef,
    }, $class;
}

sub name
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 2;
    $self->{name}= $newval if @_ > 1;
    croak "$myfun undefined" unless defined($self->{name});
    return $self->{name};
}

sub named
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 2;
    $self->{named}= $newval if @_ > 1;
    croak "$myfun undefined" unless defined($self->{named});
    return $self->{named};
}

sub command
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 2;
    $self->{command}= $newval if @_ > 1;
    croak "$myfun undefined" unless defined($self->{command});
    return $self->{command};
}

sub inp_db
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 2;
    if(@_ >1){
	$self->{inp_db} = $newval;
	my $dir_ref=key_exists($newval,$self->name());  # find block data tree in input template, Directory.yml(ROOT)->BLOCK_NAME
	croak "directory entry does not exist" unless defined($dir_ref);
	$self->{keytree}=clone($dir_ref);               # create new instance of block db
	my %args=%{ $self->{keytree} };
	my $name_idx=$args{_named};

	if(defined($name_idx) && $name_idx ne '0'){
	    $BLOCK_COUNTERS{$self->name()}++;
	    $self->named($BLOCK_COUNTERS{$self->name()});
#           In case we want to use id
#	    $self->named($name_idx);
#	    print "block named $name_idx\n";
	}
    }
    croak "$myfun undefined" unless defined($self->{inp_db});
    return $self->{inp_db};
}

sub out_db
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 2;
    $self->{out_db}= $newval if @_ > 1;
    croak "$myfun undefined" unless defined($self->{out_db});
    return $self->{out_db};
}

sub keytree
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 1;
    croak "$myfun undefined" unless defined($self->{keytree});
    return $self->{keytree};
}

sub keyon
{
    my $self=shift;
    my $MAIN_DB=$self->out_db();
    my $block=$self->name();
    my $store=$self->keytree();
    my $named=$self->named();

#    my @blocklabels=($block);
    if(defined($named) && $named ne '0'){

#       In case we want to use id
#	print "keyon named $named\n";
#	my $path='$' . $named;
#	my @path=parse_path($path);
#	print "path @path\n";
#	my $kr=key_defined($store,@path);
#	unless(defined($kr)){
#	    die "error in block $block: parameter $named is not specified\n";
#	}
#	print "kr: $kr\n";
#	print Dumper($store);
#	push @blocklabels, $kr;

	$MAIN_DB=new_key($MAIN_DB,$block);
#	$block=$kr;
	$block=$named;
    }

    key_on($MAIN_DB,$block,$store);
}

sub is_command
{
    my ($self,$command)=@_;
    my $myfun=(caller(0))[3];

    croak "Invalid number of arguments to $myfun" if @_ != 2;
    my $block_ref=$self->keytree();
    return key_exists($block_ref,$command);
}

1;
