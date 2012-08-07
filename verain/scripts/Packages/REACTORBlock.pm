package REACTORBlock;

use Clone qw(clone);
use Carp;

use KeyTree;
use MiscUtils;
use TypeUtils;
use REACTORCommand;

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
	keytree => $undef,
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
	my $dir_ref=key_exists($newval,$self->name());  # find block data tree in input template
	croak "directory entry does not exist" unless defined($dir_ref);
	$self->{keytree}=clone($dir_ref);               # create new instance of block db
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
