package TypeUtils;

use Exporter;
@ISA = ('Exporter');
@EXPORT=('is_whole','to_whole','is_count','to_count','is_int','to_int','is_real',
	 'to_real','is_decimal','to_decimal','is_float','to_float','is_string',
	 'to_string','is_eq','is_neq','is_geq','is_leq','is_gt','is_lt',
	 'is_word','in_dictionary','not_in_dictionary','is_date','is_odd','is_even',
	 'is_regex','filesame');

use Time::Local;

use constant DEF_PRECISION => 5;

sub is_whole ($) {
    return unless defined $_[0];
    return unless $_[0] =~ /^\d+$/;
    return 1;
}

sub to_whole ($) {
    return unless defined $_[0];
    my ($num) = $_[0] =~ /([+-]?(?:\d+(?:\.\d*)?|\.\d+))/;
    return unless defined $num && $num >= 0;
    sprintf "%.0f", $num;
}

sub is_count ($) {
    return unless $_[0];
    return unless $_[0] =~ /^\d+$/;
    return 1;
}

sub to_count ($) {
    return unless $_[0];
    my ($num) = $_[0] =~ /([+-]?(?:\d+(?:\.\d*)?|\.\d+))/;
    return unless $num && $num > .5;
    sprintf "%.0f", $num;
}

sub is_eq ($$) {
    return unless defined $_[0] && $_[0] ne '' && is_float($_[0]);
    return unless defined $_[1] && $_[1] ne '' && is_float($_[1]);
    return unless $_[0] == $_[1];
    return 1;
	    }
sub is_neq ($$) {
    return unless defined $_[0] && $_[0] ne '' && is_float($_[0]);
    return unless defined $_[1] && $_[1] ne '' && is_float($_[1]);
    return unless $_[0] != $_[1];
    return 1;
	    }
sub is_geq ($$) {
    return unless defined $_[0] && $_[0] ne '' && is_float($_[0]);
    return unless defined $_[1] && $_[1] ne '' && is_float($_[1]);
    return unless $_[0] >= $_[1];
    return 1;
	    }
sub is_leq ($$) {
    return unless defined $_[0] && $_[0] ne '' && is_float($_[0]);
    return unless defined $_[1] && $_[1] ne '' && is_float($_[1]);
    return unless $_[0] <= $_[1];
    return 1;
	    }
sub is_gt ($$) {
    return unless defined $_[0] && $_[0] ne '' && is_float($_[0]);
    return unless defined $_[1] && $_[1] ne '' && is_float($_[1]);
    return unless $_[0] > $_[1];
    return 1;
	    }
sub is_lt ($$) {
    return unless defined $_[0] && $_[0] ne '' && is_float($_[0]);
    return unless defined $_[1] && $_[1] ne '' && is_float($_[1]);
    return unless $_[0] < $_[1];
    return 1;
	    }


sub is_int ($) {
    return unless defined $_[0] && $_[0] ne '';
    return unless $_[0] =~ /^[+-]?\d+$/;
    return 1;
}

sub to_int ($) {
    return unless defined $_[0] && $_[0] ne '';
    my ($num) = $_[0] =~ /([+-]?(?:\d+(?:\.\d*)?|\.\d+))/;
    return unless defined $num;
    sprintf "%.0f", $num;
}

sub is_decimal ($) {
    return unless defined $_[0] && $_[0] ne '';
    return unless $_[0] =~ /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/;
    return 1;
}

sub to_decimal ($;$) {
    return unless defined $_[0] && $_[0] ne '';
    my ($num) = $_[0] =~ /([+-]?(?:\d+(?:\.\d*)?|\.\d+))/;
    return unless defined $num;
    $_[1] ||= DEF_PRECISION;
    sprintf "%.$_[1]f", $num;
}

#sub is_real ($) {
#    return unless defined $_[0] && $_[0] ne '';
#    return unless $_[0] =~ /^[+-]?\d*\.?\d*$/;
#    return 1;
#}

#sub to_real ($) {
#    return unless defined $_[0] && $_[0] ne '';
#    sprintf "%f", $_[0] =~ /([+-]?\d*\.?\d*)/;
#}

# These may need to be separated in the future, in order to identify non-decimal
# real numbers.
*is_real = *is_decimal;
*to_real = *to_decimal;

sub is_float ($) {
    return unless defined $_[0] && $_[0] ne '';
    return unless $_[0] =~ /^([+-]?)(?=\d|\.\d)\d*(\.\d*)?([Ee]([+-]?\d+))?$/;
    return 1;
}

sub to_float ($;$) {
    return unless defined $_[0] && $_[0] ne '';
    my ($num) = $_[0] =~ /(([+-]?)(?=\d|\.\d)\d*(\.\d*)?([Ee]([+-]?\d+))?)/;
    return unless defined $num;
    my $type = $num =~ /e|E/ ? 'e' : 'f';
    $_[1] ||= DEF_PRECISION;
    sprintf "%.$_[1]$type", $num;
#    sprintf "%g", $_[0] =~ /(([+-]?)(?=\d|\.\d)\d*(\.\d*)?([Ee]([+-]?\d+))?)/;
}

sub is_string ($) { defined $_[0] && ! ref $_[0] }
sub is_word ($)   { defined $_[0] && ! ref $_[0] && !($_[0] =~ /\s/)}

sub to_string ($;$) {
    return unless defined $_[0];
    return $_[1] ? substr("$_[0]", 0, $_[1]) : "$_[0]";
}

sub in_dictionary ($@) {
    my ($word,@dict)=@_;
    my $iword;

    foreach $iword (@dict){
	return 1 if $iword eq $word;
    }
    return 0;
}

sub not_in_dictionary ($@) {
    my ($word,@dict)=@_;
    my $iword;

    foreach $iword (@dict){
	return 0 if $iword eq $word;
    }
    return 1;
}

sub is_date ($) {
    my $date=shift;

    $date =~ s/\s+$//;
    $date =~ s/^\s*//;
    my ($year, $month, $day) = unpack "A4 A2 A2", $date;
    eval{ 
	timelocal(0,0,0,$day, $month-1, $year); # croaks in case of bad date 
	1;
    } or return 0;
	     }

sub is_even ($) {
    return unless defined $_[0] && $_[0] ne '';
    return  $_[0] % 2 == 0;
}

sub is_odd ($) {
    return unless defined $_[0] && $_[0] ne '';
    return  $_[0] % 2 == 1;
}

sub is_regex ($$) {
    return $_[0] =~ m/$_[1]/;
}

sub filesame {
    use English;
    use File::stat;
    my $file1=shift;
    my $file2=shift;
    my $ret=0;

    die "filesame: $file1 not a file.\n" unless -f $file1;
    die "filesame: $file2 not a file.\n" unless -f $file2;

    my $st1 = stat($file1) or die "filesame: $file1: $!";
    my $st2 = stat($file2) or die "filesame: $file2: $!";

    if($OSNAME eq 'MSWin32'){
	if($file1 eq $file2){
	    $ret=1;
	}
    }
    else{
	if(($st1->dev == $st2->dev) &&
	   ($st1->ino == $st2->ino)){
	    $ret=1;
	}
    }
    return $ret;
}

1;
