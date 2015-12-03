package MiscUtils;

use Exporter;
@ISA = ('Exporter');
@EXPORT=('nonzero',
	 'unique',
	 'any',
	 'fany',
	 'all',
	 'fall',
	 'none',
	 'fnone',
	 'notall',
	 'fnotall',
	 'true',
	 'ftrue',
	 'false',
	 'ffalse',
	 'odd',
	 'even',
	 'fronthalf',
	 'endhalf',
	 'min',
	 'max',
	 'minmax',
	 'compare_arrays',
	 'union',
	 'intersection',
	 'difference',
	 'nonstring',
	 'part',
	 'apply',
	 'natatime',
	 'arraysize',
	 'first',
	 'last',
	 'nth',
	 'mmult',
	 'transpose',
	 'everynth',
	 'skipeverynth',
	 'stride',
	 'after',
	 'after_incl',
	 'before',
	 'before_incl',
	 'indexes',
	 'lastval',
	 'firstval',
	 'factorial',
	 'diagsum',
	 'txt2xml'
    );

{
    my $_VERBOSE = 0;
    sub get_verbose  {$_VERBOSE;}
    sub set_verbose { $_VERBOSE = 1; }
}

sub nonzero { # remove zeros from array entry
    @_ = grep { $_ != 0 } @_;
    return @_;
}

sub nonstring { # remove strings from array entry
    my $str=shift;
    @_ = grep { $_ ne $str } @_;
    return @_;
}

sub unique (@) {
    my %saw = ();
    grep { not $saw{$_}++ } @_;
}

sub part (&@) {
    my ($code, @list) = @_;
    my @parts=();
    push @{ $parts[ $code->($_) ] }, $_  foreach @list;
    return @parts;
}

#
#    my $it = natatime 3, @x;
#    while (my @vals = $it->())
#
sub natatime ($@) {
    my $n    = shift;
    my @list = @_;
    return sub {
        return splice @list, 0, $n;
    }
}

# One argument is true, f* uses function for evaluation
sub any  {                   $_  && return 1 for @_; 0 }
sub fany (&@) { my $f=shift; $f->($_) && return 1 for @_; 0 }

# All arguments are true
sub all  {                   $_  || return 0 for @_; 1 }
sub fall (&@) { my $f=shift; $f->($_) || return 0 for @_; 1 }

# All arguments are false
sub none  {                   $_  && return 0 for @_; 1 }
sub fnone (&@) { my $f=shift; $f->($_) && return 0 for @_; 1 }

# One argument is false
sub notall  {                   $_  || return 1 for @_; 0 }
sub fnotall (&@) { my $f=shift; $f->($_) || return 1 for @_; 0 }

# How many elements are true
sub true  {              scalar grep { $_       } @_ }
sub ftrue (&@) { my $f=shift; scalar grep { $f->($_) } @_ }

# How many elements are false
sub false  {              scalar grep { !$_       } @_ }
sub ffalse (&@) { my $f=shift; scalar grep { !$f->($_) } @_ }

# get elements with odd indices, 1,3,5,7,
sub odd {my $aref=shift; return map {$aref->[$_]} grep {$_ & 1} 1..$#{$aref};}

# get elements with even indices, 0,2,4,6
sub even {my $aref=shift; return map {$aref->[$_]} grep {($_+1) & 1} 0..$#{$aref};}

# get front half of an array 
sub fronthalf {my ($aref,$offset)=@_; return @{$aref}[$offset..int(($#{$aref}+$offset)/2)];}

# get end half of an array 
sub endhalf {my ($aref,$offset)=@_; return @{$aref}[int(($#{$aref}+$offset)/2)+1..$#{$aref}];}

# apply block to array
sub apply {
    my $action = shift;
    my @values=@_;
    foreach (@values) {
	$_=$action->($_);
    }
    return wantarray ? @values : $values[-1];
}

sub min{
    (sort { $a <=> $b } @_)[0];
}

sub max{
    (sort { $b <=> $a } @_)[0];
}

sub minmax {
    my @a=sort { $a <=> $b } @_;
    return ($a[0], $a[$#a]);
}

sub compare_arrays {
    my ($first, $second) = @_;
    no warnings;  # silence spurious -w undef complaints
    return 0 unless @$first == @$second;
    for (my $i = 0; $i < @$first; $i++) {
	return 0 if $first->[$i] ne $second->[$i];
    }
    return 1;
} 

# must add prototypes
sub aryop {
    my ($first,$second,$OPERATOR)=@_;

    my @array1=@{ $first };
    my @array2=@{ $second };
    my @union=();
    my @intersection=();
    my @difference=();
    my %count = ();
    my $element;

    foreach $element (@array1, @array2) { $count{$element}++ }
    foreach $element (keys %count) {
	push @union, $element;
	push @{ $count{$element} > 1 ? \@intersection : \@difference }, $element;
    }
    if(lc($OPERATOR) eq 'union'){
	return @union;
    }
    elsif(lc($OPERATOR) eq 'intersection'){
	return @intersection;
    }
    elsif(lc($OPERATOR) eq 'difference'){
	return @difference;
    }
    else{
	return undef;
    }
}

sub union {
    my ($first, $second) = @_;
    return aryop($first,$second,'union');
}
sub intersection {
    my ($first, $second) = @_;
    return aryop($first,$second,'intersection');
}
sub difference {
    my ($first, $second) = @_;
    return aryop($first,$second,'difference');
}

sub arraysize {
    my $size=@_;
    return $size;
}

sub first {
    return $_[0];
}
sub last {
    return $_[-1];
}
sub nth ($@) {
    my ($idx,@a)=@_;
    return $a[$idx] || undef;
}

sub everynth ($@) {
    my ($n,@a)=@_;
    my $i;

    my @b=grep {not ++$i % $n} @a;
    return @b;
}

sub stride ($$@) {
    my ($offset,$n,@a)=@_;
    my $i;

    my @c=splice @a, $offset;
    my $b=shift @c;
    @b=grep {not ++$i % $n} @c;

    return ($b,@b);
}

sub skipeverynth ($@) {
    my ($n,@a)=@_;
    my $i;

    my @b=grep {++$i % $n} @a;
    return @b;
}

# multiply two matrices which are arrays of arrays
sub mmult {
    my ($rows, $cols, $m1, $m2) = @_;
    my $m3 = [];
    --$rows; --$cols;
    for my $i (0 .. $rows) {
        for my $j (0 .. $cols) {
            $m3->[$i][$j] += $m1->[$i][$_] * $m2->[$_][$j] for 0..$cols;
        }
    }
    return $m3;
}

# transpose a matrix
sub transpose {
    my $matrix = shift;
    my @result;
    my $m;

    for my $col (@{$matrix->[0]}) {
        push @result, [];
    }
    for my $row (@{$matrix}) {
        $m=0;
        for my $col (@{$row}) {
            push(@{$result[$m++]}, $col);
        }
    }

    return \@result;
}


sub after (&@) {
    my $test = shift;
    my $started;
    my $lag;
    grep $started ||= do {
        my $x = $lag;
        $lag = $test->();
        $x
    }, @_;
}

sub after_incl (&@) {
    my $test = shift;
    my $started;
    grep $started ||= $test->(), @_;
}

sub before (&@) {
    my $test = shift;
    my $more = 1;
    grep $more &&= ! $test->(), @_;
}

sub before_incl (&@) {
    my $test = shift;
    my $more = 1;
    my $lag  = 1;
    grep $more &&= do {
        my $x = $lag;
        $lag = ! $test->();
        $x
    }, @_;
}

sub indexes (&@) {
    my $test = shift;
    grep {
        local *_ = \$_[$_];
        $test->()
    } 0 .. $#_;
}

sub lastval (&@) {
    my $test = shift;
    my $ix;
    for ( $ix = $#_; $ix >= 0; $ix-- ) {
        local *_ = \$_[$ix];
        my $testval = $test->();

        # Simulate $_ as alias
        $_[$ix] = $_;
        return $_ if $testval;
    }
    return undef;
}

sub firstval (&@) {
    my $test = shift;
    foreach ( @_ ) {
        return $_ if $test->();
    }
    return undef;
}

sub factorial ($) {
    my $num = shift;
    my $fac = 1;

    unless($num >= 0){
	die "factorial: number not valid: $num\n";
    }

    $fac *= $num-- while $num > 0;
    return $fac;
}

sub diagsum ($) {
    my $num = shift;
    my $fac = 0;

    unless($num > 0){
	die "diag: number not valid: $num\n";
    }

    $fac += $num-- while $num > 0;
    return $fac;
}

sub txt2xml {
    my $r = shift;

    if (ref($r) eq "SCALAR") {
	$$r =~ s/&/&amp;/g;
	$$r =~ s/</&lt;/g;
#	$$r =~ s/>/&gt;/g;
#       should this trigger error, like unbalanced quotes?
	$$r =~ s/'/&apos;/g;
	$$r =~ s/"/&quot;/g;
	return 1;
    }
    elsif (ref($r) eq "ARRAY") {
	for (my $i = 0; $i <= $#$r; $i++) {
	    $r->[$i];
	    $r->[$i] =~ s/&/&amp;/g;
	    $r->[$i] =~ s/</&lt;/g;
#	    $r->[$i] =~ s/>/&gt;/g;
	    $r->[$i] =~ s/'/&apos;/g;
	    $r->[$i] =~ s/"/&quot;/g;
	}
	return 1;
    }
    else{
	die "txt2xml: incorrect data reference type\n";
    }
}

1;
