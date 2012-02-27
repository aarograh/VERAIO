package MyUtils;

# SSMOD: 2010-12-02
# bag of stuff
# Srdjan Simunovic, simunovics@ornl.gov

use Switch;
use Exporter;
use POSIX;

@ISA = ('Exporter');
@EXPORT=('atoi_ss','atof_ss',
	 'unpackfy',
	 'iunpackfy','funpackfy','mixunpackfy',
	 'deblankfy',
	 'unique',
	 'hash_subtract_ref',
	 'hash_subtract_ref_large',
	 'hash_intersection_ref',
	 'hash_union_ref',
	 'min','max', 'minmax',
	 'nsort_increasing_inplace',
	 'nsort_decreasing_inplace',
	 'push_to_minlist',
	 'nonzero',
	 'sort_ascending_into_tuples',
	 'sort_descending_into_tuples',
	 'sort_num_hash',
	 'sort_cmp_hash',
	 'is_numeric',
	 'round_dec',
	 'median',
	 'maverage'
    );

sub atoi_ss { # works on arrays and scalars
    @_ = map { s/\s//g; $_ = $_ ? int($_*1) : 0 } @_;
    return wantarray ? @_ : $_[0];
} 

sub atof_ss { # works on arrays and scalars
    @_ = map { s/\s//g; $_ = $_ ? $_*1.0 : 0 } @_;
    return wantarray ? @_ : $_[0];
} 

sub nonzero { # remove zeros from array entry
    @_ = grep { $_ != 0 } @_;
    return @_;
}

# usage @f=unpackfy($lin, "A8 A16 A16 A16");
sub unpackfy { # unpack string into character fields
    my ($string, $format) = @_;
    my @a = unpack($format, $string);
    return wantarray ? @a : $a[0];
}

# usage @f=iunpackfy($lin, "A8 A16 A16 A16");
sub iunpackfy { # unpack string into integers
    my ($string, $format) = @_;
    my @a = unpack($format, $string);
    @a = &atoi_ss(@a);
    return wantarray ? @a : $a[0];
}

# usage @f=funpackfy($lin, "A8 A16 A16 A16");
sub funpackfy { # unpack string into floats
    my ($string, $format) = @_;
    my @a = unpack($format, $string);
    @a = &atof_ss(@a);
    return wantarray ? @a : $a[0];
}

# usage @f=mixunpackfy($lin, "A8 A16 A16 A16", 'ifff');
sub mixunpackfy { # unpack string into floats
    my ($string, $format, $types) = @_;
    my $i;
    my @types = split(//, $types);
#    @types = unpack("C*", $types);
    my @a = unpack($format, $string);

    for($i=0;$i<@a;$i++){
	switch ($types[$i]){
	    case 'i' {$a[$i]=&atoi_ss($a[$i])}
	    case 'f' {$a[$i]=&atof_ss($a[$i])}
	}
    }
    return wantarray ? @a : $a[0];
}

sub deblankfy{ # remove blanks from input
    my @a;
    @a=map { s/\s//g } @_;
    return wantarray ? @a : $a[0];
}

sub unique{
    my %saw;
    my @un;
    undef %saw;
    @un = grep(!$saw{$_}++, @_);
    return @un;
}

# find the elements in one hash (%h1) that are not in another hash (%h2)
sub hash_subtract_ref{
    my ($hash1_ref, $hash2_ref)=@_;

    my %result = %{ $hash1_ref };
    delete @result{keys %{ $hash2_ref }};

    return \%result;
}

# find the elements in one hash (%hash1) that are not in another hash (%hash2), large hashes
sub hash_subtract_ref_large{
    my ($hash1_ref, $hash2_ref)=@_;

    my %result = map { $_, $hash1_ref->{$_} } grep { not exists $hash2_ref->{$_} } keys %{ $hash1_ref };

    return \%result;
}

# find the elements in one hash (%hash1) that exist in another hash (%hash2), large hashes
sub hash_intersection_ref{
    my ($hash1_ref, $hash2_ref)=@_;

    my %result = map { $_, $hash1_ref->{$_} } grep { exists $hash2_ref->{$_} } keys %{ $hash1_ref };

    return \%result;
}

# merge two hashes
sub hash_union_ref {
    my $k;
    my $v;
    my %merged = ();

    foreach (@_){
	while ( ($k,$v) = each(%{ $_ }) ) {
	    $merged{$k} = $v;
	}
    }

    return \%merged;
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

sub nsort_increasing_inplace{
    @{ $_[0] } = sort { $a <=> $b } @{ $_[0] };
}

sub nsort_decreasing_inplace{
    @{ $_[0] } = sort { $b <=> $a } @{ $_[0] };
}

# keep list of minimum values
# pass value and reference to presized array of undefs
sub push_to_minlist {
    my ($val, $ary)=@_;
    my $i;
    my $len=@{ $ary };
    $len--;

    return if defined($ary->[$len]) && $ary->[$len] < $val;

    $ary->[$len] = $val;

    for($i=$len-1;$i>=0;$i--){
	if(!defined($ary->[$i]) || $val<$ary->[$i] ){
	    $ary->[$i+1]=$ary->[$i];
	    $ary->[$i]=$val;
	}
	else{
	    return;
	}
    }
    return;
}

# Sort array of in descending order of value
# return array of tuples of [value, original_index]
# use as @b=&sort_descending_into_tuples(\@a);
sub sort_descending_into_tuples {
    my ($a_ref)=@_;
    my @b=();
    my $idx;

    @b =
	map { [$_->[1], $_->[0]] }   # 3. slice out the original list, now sorted
        sort { $b->[1] <=> $a->[1] } # 2. sort the list of tuples
        map { [$idx++, $_] }         # 1. create a list of tuples by nesting
        @{ $a_ref };                 # the data to be sorted

    return @b;
}

# Sort array of in descendingascending order of value
# return array of tuples of [value, original_index]
# use as @b=&sort_ascending_into_tuples(\@a);
sub sort_ascending_into_tuples {
    my ($a_ref)=@_;
    my @b=();
    my $idx;

    @b =
	map { [$_->[1], $_->[0]] }   # 3. slice out the original list, now sorted
        sort { $a->[1] <=> $b->[1] } # 2. sort the list of tuples
        map { [$idx++, $_] }         # 1. create a list of tuples by nesting
        @{ $a_ref };                 # the data to be sorted

    return @b;
}

# assign values to hash elements based on numerical order of their keys
# pass reference to hash and starting number of ordering
sub sort_num_hash {
    my ($hash_ref,$idx)=@_;
    %{ $hash_ref } = map { ($_ => $idx++) } sort {$a <=> $b} keys %{ $hash_ref };
}
# assign values to hash elements based on asci order of their keys
# pass reference to hash and starting number of ordering
sub sort_cmp_hash {
    my ($hash_ref,$idx)=@_;
    %{ $hash_ref } = map { ($_ => $idx++) } sort {$a cmp $b} keys %{ $hash_ref };
}


sub getnum {
    my $str = shift;
    $str =~ s/^\s+//;
    $str =~ s/\s+$//;
    $! = 0;
    my($num, $unparsed) = strtod($str);
    if (($str eq '') || ($unparsed != 0) || $!) {
        return;
    } else {
        return $num;
    } 
} 

#
# check if argument is a number
#
sub is_numeric { defined scalar &getnum($_[0]) }

# rounding of floats

sub round_dec {
# round the floating point numer to decomal place
# if fract is 1000 it will round to 0.001
    my($number,$fract) = @_;
    my $v;
    $number*=$fract;
    $v=int($number + .5 * ($number <=> 0));
    $v/=$fract;
    return $v;
}

# median of array
sub median {
    my ($aref, $median_samples)=@_;

    my $cnt=@{ $aref };
    my $hmedian=int($median_samples/2);

    my $i=0;
    my $j=0;
    my @filtered=();

    for ($i=0; $i<=$cnt-$median_samples; $i++)
    {
	my @arr;
	@arr=();
	for ($j=0; $j<$median_samples; $j++)
	{
	    $arr[$j]= $aref->[$i+$j]
	}
	my @sorted= sort {$a <=> $b} @arr;
	push @filtered, $sorted[$hmedian];
    }

    for ($i=0; $i< $hmedian; $i++)
    {
	unshift @filtered, $filtered[0];
	push @filtered, $filtered[$#filtered];
    }

    return \@filtered;
}

# moving average of an array
sub maverage {
    my ($aref, $mov_avg_pts)=@_;

    my @pts=@{ $aref };
    my @mavg=@pts;
    my $total;
    my $i;
    my $j;
    my $n=int($mov_avg_pts/2);

    for ($i=0; $i<$mov_avg_pts; $i++)
    {
	$total += $pts[$i];
    }

    for ($i=$mov_avg_pts; $i<=$#pts; $i++)
    {
	$j=$i-$n;
	$mavg[$j]=$total/$mov_avg_pts;
	$total += $pts[$i]-$pts[$i-$mov_avg_pts];
    }

    return \@mavg;
}

1;
