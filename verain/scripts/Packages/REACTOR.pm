package REACTOR;

use KeyTree;
use MiscUtils;
use TypeUtils;

use REACTORBlock;
use REACTORCommand;

# use Clone qw(clone);
use ClonePP qw(clone);

use Text::Balanced qw (
                        extract_delimited
                        extract_bracketed
                       );

use List::Maker 'range';

use Exporter;
@ISA = ('Exporter');
@EXPORT=('full_size',
	 'oct_size',
	 'qtr_size',
	 'reflectOCT',
	 'gen_oct_list',
	 'gen_quad_list',
	 'gen_oct_list_rot',
	 'gen_quad_list_rot',
	 'fullcellmap',
	 'fullcellmap_rot',
	 'read_ascii',
	 'times_in_array',
	 'fillin',
	 'purge_array',
	 'extract_map',
	 'core_map'
    );

# for initialization of every block
# it gets used on every invocation of new block
our %BLOCKINIT=();

{
    sub set_blockinit { $BLOCKINIT{$_[0]} = $_[1]; }

    my $_VERBOSE = 0;
    sub get_verbose  {$_VERBOSE;}
    sub set_verbose { $_VERBOSE = 1; }

    my $_DEBUG = 0;
    sub get_debug  {$_DEBUG;}
    sub set_debug { $_DEBUG = 1; }

}

sub full_size {
    my $size=shift;

    unless(is_int($size) && $size > 0){
	die "full_size: size not valid: $size\n";
    }

#    SSMOD: quick hack for Andrew, needs more checks
#    !($size % 2) && die "full_size: size not odd: $size\n";

    my $total=$size*$size;
    return $total;
}

sub oct_size {
    my $size=shift;

#    SSMOD: quick hack for Andrew, needs more checks
#    !($size % 2) && die "oct_size: size not odd: $size\n";

    unless(is_int($size) && $size > 0){
	die "oct_size: size not valid: $size\n";
    }

    if(is_odd($size)){
	$size--;
	$size=$size/2+1;
    }
    else{
	$size=$size/2;
    }

    my $total=0;
    $total += $_ foreach (1..$size);
    return $total;
}

sub qtr_size {
    my $size=shift;

#    SSMOD: quick hack for Andrew, needs more checks
#    !($size % 2) && die "qtr_size: size not odd: $size\n";

    unless(is_int($size) && $size > 0){
	die "qtr_size: size not valid: $size\n";
    }

    if(is_odd($size)){
	$size--;
	$size=$size/2+1;
    }
    else{
	$size=$size/2;
    }

    my $total=$size*$size;
    return $total;
}

# generates array with full map from a list of octal symmetry
sub gen_oct_list {
    my ($isize,@cellmap)=@_;
    my ($i,$j);
    my @a=();
    my @b=();

    my $ITLIMIT=$isize+3;

    my $ibound=int($isize/2);
    my @bounds;
    if(is_odd($isize)){
	@bounds=(-$ibound..$ibound);
    }
    else{
	$ibound--;
	@bounds=(-$ibound..0,0..$ibound);
    }

    my $it = incrmf3($ITLIMIT, 1, 1);  # create iterator for partitioning
    my @part = part { $it->($_) } @cellmap; # get list of references to array chunks
    my $map8=index_map(\@part,'OCTANT'); # make addressing function mapping into the original array chunks
#    my $map8=index_map_rotational(\@part,'OCTANT'); # make addressing function mapping into the original array chunks
#    for($i=-$ibound;$i<=$ibound;$i++){ # make an array of values from mapping into chunks
    foreach $i (@bounds){
	@a=();
#	for($j=-$ibound;$j<=$ibound;$j++){
	foreach $j (@bounds){
	    push @a, $map8->($i,$j);
	    push @b, $map8->($i,$j);
	}
	print "@a\n" if get_verbose();
    }
#    exit;
    return @b;
}

# generates array with full map from a list of quarter symmetry
sub gen_quad_list {
    my ($isize,@cellmap)=@_;
    my ($i,$j);
    my @b=();

    my $ITLIMIT=$isize+3;

    my $ibound=int($isize/2);
    my @bounds;
    if(is_odd($isize)){
	@bounds=(-$ibound..$ibound);
    }
    else{
	$ibound--;
	@bounds=(-$ibound..0,0..$ibound);
    }

    my $it = incrmf3($ITLIMIT, 1, 1, $ibound);
    my @part = part { $it->($_) } @cellmap;
    my $map4=index_map(\@part,'QUARTER');
#    my $map4=index_map_rotational(\@part,'QUARTER');

#    for($i=-$ibound;$i<=$ibound;$i++){
    foreach $i (@bounds){
	my @a=();
#	for($j=-$ibound;$j<=$ibound;$j++){
	foreach $j (@bounds){
	    push @a, $map4->($i,$j);
	    push @b, $map4->($i,$j);
	}
	print "@a\n" if get_verbose();
    }
    return @b;
}

# generates array with full map from a list of octal symmetry
sub gen_oct_list_rot {
    my ($isize,@cellmap)=@_;
    my ($i,$j);
    my @a=();
    my @b=();

    my $ITLIMIT=$isize+3;

    my $ibound=int($isize/2);
    my $it = incrmf3($ITLIMIT, 1, 1);  # create iterator for partitioning
    my @part = part { $it->($_) } @cellmap; # get list of references to array chunks
#    my $map8=index_map(\@part,'OCTANT'); # make addressing function mapping into the original array chunks
    my $map8=index_map_rotational(\@part,'OCTANT'); # make addressing function mapping into the original array chunks
    for($i=-$ibound;$i<=$ibound;$i++){ # make an array of values from mapping into chunks
	@a=();
	for($j=-$ibound;$j<=$ibound;$j++){
	    push @a, $map8->($i,$j);
	    push @b, $map8->($i,$j);
	}
	print "@a\n" if get_verbose();
    }
#    exit;
    return @b;
}

# generates array with full map from a list of quarter symmetry
sub gen_quad_list_rot {
    my ($isize,@cellmap)=@_;
    my ($i,$j);
    my @b=();

    my $ITLIMIT=$isize+3;

    my $ibound=int($isize/2);
    my $it = incrmf3($ITLIMIT, 1, 1, $ibound);
    my @part = part { $it->($_) } @cellmap;
#    my $map4=index_map(\@part,'QUARTER');
    my $map4=index_map_rotational(\@part,'QUARTER');
    for($i=-$ibound;$i<=$ibound;$i++){
	my @a=();
	for($j=-$ibound;$j<=$ibound;$j++){
	    push @a, $map4->($i,$j);
	    push @b, $map4->($i,$j);
	}
	print "@a\n" if get_verbose();
    }
    return @b;
}

sub clean_line2{
    my $lineref=shift;

#    die "clean_line: invalid reference\n" unless (ref($lineref) eq 'SCALAR' && defined($$lineref));

#    $$lineref =~ s/\// /g;                 # replace slashes with spaces
    $$lineref =~  s/(\!\s*(.*))$//;         # strip comments
    $$lineref =~ s/(\d+)\s*\*\s*(\w+)/"$2 " x $1/ge; # expand fortran expressions
#    $$lineref =~ s/(zero)/0/g;               # convert zero to 0
#    $$lineref =~ s/['"]//g;                # remove quotes
    $$lineref =~ s/[,;]/ /g;               # remove commas and such
    $$lineref =~ s/^\s+//;                 # strip leading blanks
    $$lineref =~ s/\s+$//;                 # strip trailing blanks
}

# sub clean_slash{
#     my $lineref=shift;
# 
#     $$lineref =~ s/\// /g;                 # replace slashes with spaces
# }

sub clean_line{
    my $lineref=shift;

    my ($text, $loc1, $loc2, $delim);
    my ($dist, $rest, $transl, $pfx, $next, $str);
    my @ary;

    $text=$$lineref;

    $loc1=0;
    $loc2=0;
    pos($text) = $loc1;

    while( $text =~ m/(['"<!])/g ){   # search for quote marks
	$delim=$1;
	$loc2=pos($text);             # quote mark location + 1
	pos($text)= $loc2-1;          # set position to the quote
	$dist=$loc2-$loc1;            # distance from the previous location to after quote
	undef $next;
	undef $rest;
	if($delim eq '<'){
	    ($next,$rest) = extract_bracketed($text,'<');
	}
	elsif($delim eq '!'){
	    $pfx=substr($text, $loc1, $dist-1);   # string before the quote mark, prefix
	    $pfx =~ s/(\d+)\s*\*\s*(\w+)/"$2 " x $1/ge; # expand fortran expressions
	    $transl.=$pfx;                        # append prefix to the result
	    last;
	}
	else{
	    ($next,$rest) = extract_delimited($text,"$delim");
	}

	if(defined($next)){                       # found balanced text
	    $pfx=substr($text, $loc1, $dist-1);   # string before the quote mark, prefix
	    if(length($pfx)){
		$pfx =~ s/(\d+)\s*\*\s*(\w+)/"$2 " x $1/ge; # expand fortran expressions
		$pfx =~ s/[,;]/ /g;               # remove commas and such
		$transl.=$pfx;                        # append prefix to the result
	    }
	    $loc2=pos($text);                     # location of closing quote mark + 1
	    if($delim eq '<'){                    # generate list
		$next =~ s/^.//; $next =~ s/.$//; # strip angle brackets
		@ary=();
		$str = "\@ary = range( \'$next \' );"; # string to generate
		eval $str;
		$next=" @ary ";
	    }
	    $transl.=$next;                        # append to result
	}
	else{
	    die "clean_line: unbalanced quotes in $text: at location $loc2\n";
	}
	$loc1=$loc2;       # location after quotes
    }
    if(defined($rest)){    # leftover from the match
	$rest =~ s/(\d+)\s*\*\s*(\w+)/"$2 " x $1/ge; # expand fortran expressions
	$rest =~ s/[,;]/ /g;               # remove commas and such
	$transl.=$rest;
    }
    unless(defined($transl)){
	$transl=$text;     # there were no quotes nor comments in the string
	$transl =~ s/(\d+)\s*\*\s*(\w+)/"$2 " x $1/ge; # expand fortran expressions
	$transl =~ s/[,;]/ /g;               # remove commas and such
    }

    $transl=~s/^\s+//;           # just in case
    $transl=~s/\s+$//;

    $$lineref=$transl;
    return;
}

sub read_ascii {
    my ($filename, $INPUT_DB, $MAIN_DB, %userparam) = @_;
    # temporary references to store data while building the db
    my ($block,$command,$cname,$ctext);
    my ($name,$res);

    $block=$command=undef;
    while ( my ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$key eq 'block'   && do {$block=$value;};     # current open block
	$key eq 'command' && do {$command=$value;};   # open command
    }

    open my($IFILE), $filename or die "Cannot open file $filename\n";

  READ: while (<$IFILE>) {       # main read loop
      &clean_line(\$_);
      next READ if /^$/;        # skip empty lines

      /^include\s+(\S+)/ && do{
	  my $ifile=$1;
	  print STDERR "[$filename:$.] Include file: $ifile\n" if get_verbose();
	  read_ascii($ifile,$INPUT_DB, $MAIN_DB, 
		     'block'=>$block, 'command'=>$command);
	  next READ;
      };
#      &clean_slash(\$_);

      /^\[\s*(\w+)\s*\]/ &&     # found new block
	  do{
	      $name=$1;
	      if($block){        # old block that needs to be put into the main tree
		  if($command){  # old command to complete
		      print STDERR "[$filename:$.] End command: ", $command->keyword(), ": ", $command->ctext(), "\n"  if get_verbose();
		      $command->keyin();
		  }
		  print STDERR "[$filename:$.] End block: ", $block->name(), "\n"  if get_verbose();
		  $block->keyon();
	      }
	      print STDERR "[$filename:$.] New block: $name\n"  if get_verbose();
	      die "[$filename:$.] Bad block name.\n" unless key_exists($INPUT_DB,$name);
	      $block=REACTORBlock->new( name=>$name, out_db=>$MAIN_DB );
	      $block->inp_db($INPUT_DB);  # INPUT_DB is root of Directory.yml

	      if(exists($REACTOR::BLOCKINIT{$name})){
		  print STDERR "Initialize block $name with file $BLOCKINIT{$name}\n" if get_verbose();
		  read_ascii($BLOCKINIT{$name}, $INPUT_DB, $MAIN_DB, 'block'=>$block);
	      }

	      $command=undef;
	      next READ;
      };
      $block && !$command && do{      # block previously initialized, but no commands yet.
	  /^(\w+)\s*(.*?)$/ && do{ # check if the first line is a command
	      $cname=$1;
	      $ctext=($+[2]-$-[2]) ? $2 : '';
	      $res=$block->is_command($cname) || 0;
	      die "[$filename:$.] invalid keyword $cname in block ", $block->name(), "\n" unless $res;
	      print STDERR "[$filename:$.] New command: $cname $ctext\n"  if get_verbose();
	      $cname=$block->command_name($cname);

	      $command=REACTORCommand->new(keyword=>$cname,keytree=>$res,ctext=>$ctext,file=>$filename,line=>$.);
	      unless($command->is_multiline()){
		  print STDERR "[$filename:$.] End command: ", $command->keyword(), ": ", $command->ctext(), "\n"  if get_verbose();
		  $command->keyin();
		  $command=undef;
	      }
	      next READ;
	  };
      };
      $block && $command && do{    # new block initialized, multi-line command already started
	  /^(\w+)\s*(.*)$/ && do{  # check if the new entry is a command
	      $cname=$1;
	      $ctext=($+[2]-$-[2]) ? $2 : '';
	      $res=$block->is_command($cname) || 0;

	      if($res){   # complete old command
		  print STDERR "[$filename:$.] End command: ", $command->keyword(), ": ", $command->ctext(), "\n"  if get_verbose();
		  $command->keyin();
		  $command=undef;

		  print STDERR "[$filename:$.] New command: $cname $ctext\n"  if get_verbose();
		  $cname=$block->command_name($cname);
		  $command=REACTORCommand->new(keyword=>$cname,keytree=>$res,ctext=>$ctext,file=>$filename,line=>$.);
		  unless($command->is_multiline()){
		      print STDERR "[$filename:$.] End command: ", $command->keyword(), ": ", $command->ctext(), "\n"  if get_verbose();
		      $command->keyin();
		      $command=undef;
		  }
		  next READ;
	      }
	  };
	  $command->ctext($_); # if not a new command, keep accumulating
      };
  }
    # file ended, check for uncompleted commands
    if($block || $command){
	if($command){
	    print STDERR "[$filename:$.] End command: ", $command->keyword(), ": ", $command->ctext(), "\n"  if get_verbose();
	    $command->keyin();
	}
	print STDERR "[$filename:$.] End block: ", $block->name(), "\n"  if get_verbose();
	$block->keyon();
    }

    return 1;
}

sub reflectOCT {
    my $mask=shift;
    my $ny=@{ $mask };
    my $i=0;
    my $j=0;

    for($i=0;$i<$ny;$i++){
	for($j=1;$j<$ny;$j++){
	    $v=$mask->[$j]->[$i];
	    $mask->[$i]->[$j]=$v;
	}
    }
}

# incrmf3(20,1,1) will partion array in pyramidal chunks
# incrmf3(20,1,8) will partion array in square chunks
# guess what mf stands for
sub incrmf3 {
    my ($nmax,$counter_inc,$bin_inc,$bin_size)=@_;
    my $m=0;
    my $n=0;
    return sub {
	if($m<= ($bin_size ? $bin_size : $n)){
	    $m=$m+$counter_inc;
	}
	else{
	    $m=1;
	    $n=$n+$bin_inc;
	}
	return $n > $nmax ? undef : $n;
    };
}

sub index_map {
    my ($map,$type)=@_;
    my $m=@{ $map };

    if(uc($type) eq 'OCTANT'){
	return sub {
	    my ($i,$j)=@_;
#	    my $flag="$i$j";

	    $i=abs($i);
	    $j=abs($j);
	    if($j>$i){
		my $t=$i;
		$i=$j;
		$j=$t;
	    }

	    my $value= $map->[$i]->[$j];

	    unless(defined($map->[$i]->[$j])){
		die "index_map: undefined OCTANT $i $j\n";
	    }

#	    my $flag="$i$j";
#	    $value = $value eq 0 ? 0 : $flag;

	    return $value;
	}
    }
    if(uc($type) eq 'QUARTER'){
	return sub {
	    my ($i,$j)=@_;
#	    my $flag="$i$j";

	    $i=abs($i);
	    $j=abs($j);

	    unless(defined($map->[$i]->[$j])){
		die "index_map: undefined QARTER $i $j\n";
	    }

	    my $value= $map->[$i]->[$j];

#	    my $flag="$i$j";
#	    $value = $value eq 0 ? 0 : $flag;

	    return $value;
	}
    }
    undef;
}

sub fullcellmap {
    my ($npin,@a)=@_;
    my @b=();

    my $qtrsize =qtr_size($npin);
    my $octsize =oct_size($npin);
    my $fullsize=full_size($npin);

 #   if(is_odd($npin)){
	if(@a == $qtrsize){
	    @b=gen_quad_list($npin,@a);
	}
	elsif(@a == $octsize){
	    @b=gen_oct_list($npin,@a);
	}
	elsif(@a == $fullsize){
	    @b=@a;
	}
	else{
	    die "fullcellmap: invalid map size ($fullsize) for map dimension (odd, $npin) [@a] $#a\n";
	}
#    }
#    else{
#	if(@a == $fullsize){
#	    @b=@a;
#	}
#	else{
#	    die "fullcellmap: invalid map size ($fullsize) for map dimension (even, $npin) [@a]\n";
#	}
#    }

    return @b;
}

sub fullcellmap_rot {
    my ($npin,@a)=@_;
    my @b=();

    my $qtrsize =qtr_size($npin);
    my $octsize =oct_size($npin);
    my $fullsize=full_size($npin);

    if(@a == $qtrsize){
	@b=gen_quad_list_rot($npin,@a);
    }
    elsif(@a == $octsize){
	@b=gen_oct_list_rot($npin,@a);
    }
    elsif(@a == $fullsize){
	@b=@a;
    }
    else{
	die "fullcellmap_rot: invalid map $npin [@a]\n";
    }
    return @b;
}

sub times_in_array{
    my ($ary,$symbol)=@_;

    my $n=0;
    foreach (@{ $ary }){
	$n++ if $_ eq $symbol;
    }
    return $n;
}

sub fillin{
    my ($ary1, $ary2, $valid)=@_;
    my @result;
    my $i;

#    @result= map { $_ == $valid ? $ary2->[$i++] : $_ } @{ $ary1 };
    @result= map { $_ == $valid ? $ary2->[$i++] : '_EMPTY_' } @{ $ary1 };

    return  wantarray ? @result : \@result;
}

sub purge_array{
    my ($ary, $invalid)=@_;
    my @result;
    my $i;

    @result= grep { $_ ne $invalid } @{ $ary };

    return  wantarray ? @result : \@result;
}

sub extract_map{
    my($ary,$n,$m,$maptype)=@_;
    my $na=@{ $ary };

    die "extract_map: indices not valid $n, $m, $na\n"
	if ($n <= 0 || 
	    $m <= 0 || 
	    ($n*$m > $na)
# ||
#	    !($n % 2) ||
#	    !($m % 2)
	);

    my $nhalf=int($n/2);
    my $mhalf=int($m/2);
    my $icenter= $nhalf * $m + $mhalf;  # central location

    $icenter += ($n%2) ? 0 : 1;

    my @result = ();
    if($maptype eq 'OCTANT'){
	for(my $i=0; $i<=$nhalf;$i++){
	    for(my $j=0; $j<=$i;$j++){
		push @result, $ary->[$icenter+$i*$m+$j];
	    }
	}
	return wantarray ? @result : \@result;
    }
    if($maptype eq 'QUARTER'){
	for(my $i=0; $i<=$nhalf;$i++){
	    for(my $j=0; $j<=$mhalf;$j++){
		push @result, $ary->[$icenter+$i*$m+$j];
	    }
	}
	return wantarray ? @result : \@result;
    }
    
    die "extract_map: invalid maptype: $maptype\n";

}

sub core_map{
    my ($cmap, $mmap, $n, $bc_sym)=@_;

    # how many 1 in core shape
    my $nfull=times_in_array($cmap,1);

    # get octant and quarter maps from core shape
    my @core_map_o=extract_map($cmap,$n,$n,'OCTANT');
    my $noct      =times_in_array(\@core_map_o,1);
    my @core_map_q=extract_map($cmap,$n,$n,'QUARTER');
    my $nquad     =times_in_array(\@core_map_q,1);

    # elements in the other map
    my $nmmap=@{ $mmap };

    my @ccmap;
    my @resmap;
    my @fullm;
    my @fullmp;

    print STDERR "core_map: $bc_sym\n"  if get_verbose();;

    if($nmmap == $noct){
	@ccmap=@core_map_o;
	@resmap=fillin(\@ccmap, $mmap, 1);
	## ssmod
	if($bc_sym eq 'mir'){
	    @fullm=fullcellmap($n,@resmap);
	}
	else{
#	    @fullm=fullcellmap_rot($n,@resmap);
	    @fullm=fullcellmap($n,@resmap);
	}

#	@fullmp=purge_array(\@fullm,0);
	@fullmp=purge_array(\@fullm,'_EMPTY_');
    }
    elsif ($nmmap == $nquad){
	@ccmap=@core_map_q;
	@resmap=fillin(\@ccmap, $mmap, 1);
	## ssmod
	if($bc_sym eq 'mir'){
	    @fullm=fullcellmap($n,@resmap);
	}
	else{
	    @fullm=fullcellmap_rot($n,@resmap);
#	    @fullm=fullcellmap($n,@resmap);
	}
#	@fullmp=purge_array(\@fullm,0);
	@fullmp=purge_array(\@fullm,'_EMPTY_');
    }
    elsif ($nmmap == $nfull){
	@fullm=@{ $mmap };
#	@fullmp=purge_array(\@fullm,0);
	@fullmp=@fullm;
    }
    else{
	die "core_map: invalid map, map=$nmmap, octant=$noct, quarter=$nquad, full=$nfull\n";
    }

    return  wantarray ? @fullmp : \@fullmp;
}

sub index_map_rotational {
    my ($map,$type)=@_;
    my $m=@{ $map };

    if(uc($type) eq 'OCTANT'){
	return sub {
	    my ($ibar,$jbar)=@_;
	    my ($i,$j)=($ibar,$jbar);
	    my $region=1.1;

	    # second octant in first quadrant, O^-1
	    ($ibar >  0 && $jbar >  0 && $ibar <=  $jbar) &&
		do{
		    $i=         $jbar;
		    $j=-$ibar + $jbar;
		    $region=1.2;
	    };

	    # second quadrant, Q^-1
	    ($ibar <= 0 && $jbar >  0 && $jbar >  (-$ibar)) &&
		do{
		    $i= $jbar;
		    $j=-$ibar;
		    die "redoing region 2.1\n" if $region != 1.1;
		    $region=2.1;
	    };
	    # second quadrant, O^-1 Q^-1
	    ($ibar <= 0 && $jbar >  0 && $jbar <=  (-$ibar)) &&
		do{
		    $i=-$ibar;
		    $j=-$ibar - $jbar;
		    die "redoing region 2.2\n" if $region != 1.1;
		    $region=2.2;
	    };

	    # third quadrant, Q^-2
	    ($ibar <  0 && $jbar <=  0 && (-$jbar) <  (-$ibar)) &&
		do{
		    $i=-$ibar;
		    $j=-$jbar;
		    die "redoing region 3.1\n" if $region != 1.1;
		    $region=3.1;
	    };
	    # third quadrant, O^-1 Q^-2
	    ($ibar <  0 && $jbar <=  0 && (-$jbar) >= (-$ibar)) &&
		do{
		    $i=       - $jbar;
		    $j= $ibar - $jbar;
		    die "redoing region 3.2\n" if $region != 1.1;
		    $region=3.2;
	    };

	    # fourth quadrant, Q^-3
	    ($ibar >=  0 && $jbar <  0 && (-$jbar) >  $ibar) &&
		do{
		    $i=-$jbar;
		    $j= $ibar;
		    die "redoing region 4.1\n" if $region != 1.1;
		    $region=4.1;
	    };
	    # fourth quadrant
	    ($ibar >=  0 && $jbar <  0 && (-$jbar) <=  $ibar) &&
		do{
		    $i= $ibar;
		    $j= $ibar + $jbar;
		    die "redoing region 4.2\n" if $region != 1.1;
		    $region=4.2;
	    };

	    unless(defined($map->[$i]->[$j])){
		die "oct: $region ($ibar, $jbar) = ($i,$j)\n";
	    }

	    my $value= $map->[$i]->[$j];

#	    my $flag="$i$j";
#	    print "oct: $region: $ibar,$jbar -> $i,$j\n";
#	    $value = $value eq 0 ? 0 : $flag;

	    return $value;
	}
    }
    if(uc($type) eq 'QUARTER'){
	return sub {
	    my ($ibar,$jbar)=@_;
	    my ($i,$j)=($ibar,$jbar);

	    my $region=1;

	    # second quadrant
	    ($ibar <= 0 && $jbar >  0) &&
		do{
		    $i=         $jbar;
		    $j=-$ibar;
		    $region=2;
	    };
	    # third quadrant
	    ($ibar <  0 && $jbar <=  0) &&
		do{
		    $i=-$ibar;
		    $j=-$jbar;
		    $region=3;
	    };
	    # fourth quadrant
	    ($ibar >=  0 && $jbar <   0) &&
		do{
		    $i=        -$jbar;
		    $j= $ibar;
		    $region=4;
	    };
	    
	    unless(defined($map->[$i]->[$j])){
		die "quad: $region ($ibar, $jbar) = ($i,$j)\n";
	    }

	    my $value= $map->[$i]->[$j];

#	    my $flag="$i$j";
#	    print "qad: $region: $ibar,$jbar -> $i,$j\n";
#	    $value = $value eq 0 ? 0 : $flag;

	    return $value;
	}
    }
    undef;
}


1;
