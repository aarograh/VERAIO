package REACTORCommand;
use Carp;

use REACTORBlock;

use KeyTree;
use MiscUtils;
use TypeUtils;


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

    my $self={
	keyword => $arg{keyword} || croak("missing keyword"),
	keytree => $arg{keytree} || croak("missing keytree"),
	ctext   => exists($arg{ctext}) ? $arg{ctext} : undef,
#	ctext   =>$arg{ctext} || undef,
	file    => exists($arg{file})  ? $arg{ctext} : undef,
	line    => exists($arg{line})  ? $arg{ctext} : undef,
    };

#    print STDERR "ctext $arg{ctext}\n";

    bless $self, $class;
}

sub argvalue
{
    my ($self,$argument)=@_;
    my $myfun=(caller(0))[3];

    croak "Too few arguments to $myfun" if @_ < 2;

    my $tree=$self->keytree();
    return key_defined($tree,$argument);
}

sub is_multiline
{
    my ($self)=@_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 1;

    my $keyw_style=$self->argvalue('_style') || 0;
    if($keyw_style eq 'multi-line'){
	return 1;
    }
    return 0;
}

sub argarray
{
    my ($self,$argument)=@_;
    my $myfun=(caller(0))[3];

    croak "Too few arguments to $myfun" if @_ < 2;

    my $tree=$self->keytree();
    return values_at($tree,$argument);
}

sub ctext
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 2;
    $self->{ctext} .= " ".$newval if @_ > 1;
    croak "$myfun undefined" unless defined($self->{ctext});
    return $self->{ctext};
}

sub file
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 2;
    $self->{file}= $newval if @_ > 1;
    croak "$myfun undefined" unless defined($self->{file});
    return $self->{file};
}

sub line
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 2;
    $self->{line}= $newval if @_ > 1;
    croak "$myfun undefined" unless defined($self->{line});
    return $self->{line};
}

sub keytree
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 2;
    $self->{keytree} = $newval if @_ > 1;
    croak "$myfun undefined" unless defined($self->{keytree});
    return $self->{keytree};
}

sub keyword
{
    my ($self, $newval) = @_;
    my $myfun=(caller(0))[3];

    croak "Too many arguments to $myfun" if @_ > 2;
    $self->{keyword} = $newval if @_ > 1;
    croak "$myfun undefined" unless defined($self->{keyword});
    return $self->{keyword};
}

sub keyin{
    my $self=shift;
    my $myfun=(caller(0))[3];

    my ($name_idx, $name);
    my @a;
    my $result;
    my $errmsg;

    my $dtx=$self->ctext();
    my $line=$self->line();
    my $file=$self->file();

    my $REF_LABEL='_key';
    my $CONTENT_LABEL='_content';
    my $FILE_LABEL='_file';
    my $LINE_LABEL='_line';

    my $templ=$self->keytree();
    my %args=%{ $templ };

    $dtx=~s/^\s+//;
    @a=split /\s+/, $dtx;
    $name_idx=$args{_named};
    if($name_idx){
	$name=splice(@a,$name_idx-1,1);

# In case we want to use _content instead of _default. Then must
# change all entries in Directory.yml, _default -> _content, and use
# content to define default value. Otherwise, use _default and make a
# map from _default to create _content.
#
#	key_delete($templ,$CONTENT_LABEL) if key_exists($templ,$CONTENT_LABEL);

	$templ=new_key($templ,$REF_LABEL,$name);
    }

    my @sr=values_at($templ,'_check');
    $result=0;
    if($args{_parse} eq 'scalar'){
	$dtx=$args{_type} eq 'string' ? $dtx : $a[0];
	$result=&apply_evals(\$dtx,\@sr,\$errmsg);
	key_on($templ,$CONTENT_LABEL,$dtx);
    }
    elsif($args{_parse} eq 'list'){
	$result=&apply_evals(\@a,\@sr,\$errmsg);
	key_on($templ,$CONTENT_LABEL,[@a]);
    }
    else{
	croak "$myfun invalid parse type";
    }
    unless($result){
	&error_report($self->keyword(),$dtx,$file,$line,$errmsg);
	die "$myfun check fail\n";
    }

    return $result;
}

sub error_report
{
    my ($command,$text,$file,$line,$error)=@_;

    print STDERR "Error in $file line $line:\n";
    print STDERR "    Keyword: [$command]\n";
    print STDERR "    String : [$command $text]\n";
    print STDERR "    Error  : [$error]\n";
}

sub apply_evals {
    my ($data_ref,$eval_ref,$errmsg_ref)=@_;
    my $ieval;
    my $dtype=ref $data_ref;

    foreach $ieval (@{$eval_ref}){
	$$errmsg_ref="$ieval";
	if($ieval=~ m/(error>)(.*)/){
	    $$errmsg_ref=$2;
	    substr( $ieval, $-[2], $+[2], '' );
	    substr( $ieval, $-[1], $+[1], '' );
	}
	$ieval =~ s/^\s+//;
	$ieval =~ s/\s+$//;
	return 1 unless $ieval;

	my @cargs=split(/\s+/,$ieval);
	my $cmdc=shift(@cargs);
	if($dtype eq 'SCALAR'){
	    unshift @cargs,$$data_ref;
	}
	elsif($dtype eq 'ARRAY'){
	    unshift @cargs,@{ $data_ref };
	}
	else{
	    die "apply_evals: error in data_ref $ieval\n";
	}
	@cargs=map { "\"$_\"" } @cargs;
	my $exa=join(',',@cargs);
	print STDERR "--------- check $dtype: [$ieval]\n" if get_verbose();;
	$cmdc =~ s/\(\)/\($exa\)/g;
	$cmdc =~ s/\[\]/\[$exa\]/g;
	my $expr="$cmdc";
	print STDERR "--------------- $expr\n" if get_verbose();;
	my $result=eval $expr || 0;
	print STDERR "--------------- result $result\n" if get_verbose();;

	if(!$result){
	    print STDERR "------------------- error: $$errmsg_ref\n" if get_verbose();;
	    return 0;
	}

    }
    return 1;
}

1;
