package REACTOR;

use KeyTree;
use MiscUtils;

use Clone qw(clone);

use Exporter;
@ISA = ('Exporter');
@EXPORT=('full_size',
	 'oct_size',
	 'qtr_size',
	 'reflectOCT',
	 'gen_oct_list',
	 'gen_quad_list',
	 'fullcellmap',
	 'read_ascii'
    );

sub full_size {
    my $size=shift;
    !($size % 2) && die "full_size: size not odd: $size\n";

    my $total=$size*$size;
    return $total;
}

sub oct_size {
    my $size=shift;
    !($size % 2) && die "oct_size: size not odd: $size\n";

    $size--;
    $size=$size/2+1;
    my $total=0;
    $total += $_ foreach (1..$size);
    return $total;
}

sub qtr_size {
    my $size=shift;
    !($size % 2) && die "qtr_size: size not odd: $size\n";

    $size--;
    $size=$size/2+1;
    my $total=$size*$size;
    return $total;
}

# generates array with full map from a list of quarter symmetry
sub gen_oct_list {
    my ($isize,@cellmap)=@_;
    my ($i,$j);
    my @a=();
    my @b=();

    my $ITLIMIT=$isize+3;

    my $ibound=int($isize/2);
    my $it = incrmf3($ITLIMIT, 1, 1);  # create iterator for partitioning
    my @part = part { $it->($_) } @cellmap; # get list of references to array chunks
    my $map8=index_map(\@part,'OCTANT'); # make addressing function mapping into the original array chunks
    for($i=-$ibound;$i<=$ibound;$i++){ # make an array of values from mapping into chunks
	@a=();
	for($j=-$ibound;$j<=$ibound;$j++){
	    push @a, $map8->($i,$j);
	    push @b, $map8->($i,$j);
	}
	print "@a\n";
    }
    return @b;
}

sub gen_quad_list {
    my ($isize,@cellmap)=@_;
    my ($i,$j);
    my @b=();

    my $ITLIMIT=$isize+3;

    my $ibound=int($isize/2);
    my $it = incrmf3($ITLIMIT, 1, 1, $ibound);
    my @part = part { $it->($_) } @cellmap;
    my $map4=index_map(\@part,'QUARTER');
    for($i=-$ibound;$i<=$ibound;$i++){
	my @a=();
	for($j=-$ibound;$j<=$ibound;$j++){
	    push @a, $map4->($i,$j);
	    push @b, $map4->($i,$j);
	}
	print "@a\n";
    }
    return @b;
}



sub read_ascii {
    my ($filename, $INPUT_DB, $MAIN_DB, $VERBOSE, %userparam) = @_;
    # temporary references to store data while building the db
    my ($block,$command,$ctext,$file,$line);
    my ($cmd,$ctxt);
    my ($block_ref,$dir_ref);
    my ($key, $value);
    my @options;
    my $BLOCK_COUNTER;

    $block=$command=$ctext=$block_ref=undef;
    while ( ($key, $value) = each %userparam )        # to avoid perl bug of $$
    {
	$key eq 'block'   && do {$block=$value;};     # current open block
	$key eq 'command' && do {$command=$value;};   # open command
	$key eq 'ctext'   && do {$ctext=$value;};     # accumulated text for the command
	$key eq 'db'      && do {$block_ref=$value;}; # block db built so far
	$key eq 'file'    && do {$file=$value;};      # command file 
	$key eq 'line'    && do {$line=$value;};      # command line
    }

    open my($IFILE), $filename or return;  # Failure

  READ: while (<$IFILE>) {       # main read loop
      s/\// /g;                 # replace slashes with spaces
      s/(\!\s*(.*))$//;         # strip comments
      s/(\d+)\s*\*\s*(\w+)/"$2 " x $1/ge; # expand fortran expressions
      s/['"]//g;                # remove quotes
      s/^\s+//;                 # strip leading blanks
      s/\s+$//;                 # strip trailing blanks
      next READ if /^$/;        # skip empty lines

      /^include\s+(\S+)/ && do{
	  my $ifile=$1;
	  print STDERR "[$.] Include file: $ifile\n" if $VERBOSE;
	  read_ascii($ifile,$INPUT_DB, $MAIN_DB, $VERBOSE,
		     'block'=>$block, 'command'=>$command,
		     'ctext'=>$ctext,'db'=>$block_ref,
		     'file'=>$file,'line'=>$line);
	  next READ;
      };

      /^\[\s*(\w+)\s*\]/ &&     # found new block
	  do{
	      if($block){        # there is an old block that needs to be put into the main tree
		  if($command){  # check for a command to complete
		      print STDERR "[$.] End command: $command ", defined($ctext) ? $ctext : '',"\n"  if $VERBOSE;
		      &keyin($block_ref,$command,$ctext,$file,$line);
		  }
		  # store block into the main tree
		  my $store=clone($block_ref);
#		  my $lref=key_exists($MAIN_DB,$block);
#		  my $lnum=++$BLOCK_COUNTER;
#		  key_on($lref,$lnum,$store);
#ssASM		  if($block eq 'ASSEMBLY'){
#ssASM		      push_on($MAIN_DB,$block,$store);
#ssASM		  }
#ssASM		  else{
		      key_on($MAIN_DB,$block,$store);
#ssASM		  }
	      }
	      $block=$1;          # block name
	      $BLOCK_COUNTER=0;
	      die "[$.] Bad block name.\n" unless key_exists($INPUT_DB,$block);
	      print STDERR "[$.] Found block: $block\n"  if $VERBOSE;
	      $dir_ref=key_exists($INPUT_DB,$block);     # find block data tree in the main template
	      $block_ref=clone($dir_ref);                # create new instance of block db
	      $command=undef;
	      $ctext=undef;
	      next READ;
      };
      $block && !$command && do{      # block previously initialized, but no commands yet.
	  /^(\w+)\s*(.*?)$/ && do{ # check if the first line is a command
	      $command=$1;
	      $ctext=($+[2]-$-[2]) ? $2 : '';
	      die "[$.] invalid keyword $command in block $block\n" unless key_exists($block_ref,$command);
	      print STDERR "[$.] Found new command: $command ", defined($ctext) ? $ctext : '',"\n"  if $VERBOSE;
	      $file=$filename;
	      $line=$.;
	      next READ;
	  };};
      $block && $command && do{       # new block initialized, command already started
	  /^(\w+)\s*(.*)$/ && do{  # check if the new entry is a command
	      $cmd=$1;
	      $ctxt=($+[2]-$-[2]) ? $2 : '';
	      if(key_exists($block_ref,$cmd)){   # new command is starting, complete old command
		  print STDERR "[$.] End command: $command ", defined($ctext) ? $ctext : '',"\n"  if $VERBOSE;
		  &keyin($block_ref,$command,$ctext,$file,$line);
		  $command=$cmd;
		  $ctext=$ctxt ? $ctxt : undef;
		  $file=$filename;
		  $line=$.;
		  print STDERR "[$.] Found command: $command ", defined($ctext) ? $ctext : '',"\n"  if $VERBOSE;
		  next READ;
	      }
	  };
      };
      $ctext.=" ".$_;  # if not a new command, keep accumulating
  }
    # file ended, check for uncompleted commands
    print STDERR "[$.] End command: ", $command ? $command : '', $ctext ? $ctext : '',"\n"  if $VERBOSE;
    &keyin($block_ref,$command,$ctext,$file,$line);
    my $store=clone($block_ref);
#    my $lref=key_exists($MAIN_DB,$block);
#    my $lnum=++$BLOCK_COUNTER;
#    key_on($lref,$lnum,$store);
#ssASM    if($block eq 'ASSEMBLY'){
#ssASM	push_on($MAIN_DB,$block,$store);
#ssASM    }
#ssASM    else{
	key_on($MAIN_DB,$block,$store);
#ssASM    }

    return 1;
}

sub keyin {
    my ($directory,$command,$dtx,$file,$line)=@_;
    my ($templ, $name_idx, $name);
    my %args;
    my @a;

    my $REF_LABEL='_key';
    my $CONTENT_LABEL='_content';
    my $FILE_LABEL='_file';
    my $LINE_LABEL='_line';

    $templ=key_exists($directory,$command);
    return undef unless $templ;
    %args=%{$templ};

    $args{_parse} eq 'scalar' && do{
	$dtx=~s/^\s+//;
	@a=split /\s+/, $dtx;
	$dtx=$args{_type} eq 'title' ? $dtx : $a[0];
	key_on($templ,$CONTENT_LABEL,$dtx);
	key_on($templ,$FILE_LABEL,$file);
	key_on($templ,$LINE_LABEL,$line);

	return 1;
    };

    $args{_parse} eq 'list' && do{
	$dtx=~s/^\s+//;
	@a=split /\s+/, $dtx;
	$name_idx=$args{_named};
	if($name_idx){
	    $name=splice(@a,$name_idx-1,1);
	    $templ=new_key($templ,$REF_LABEL,$name);
	}
	key_on($templ,$CONTENT_LABEL,[@a]);
	key_on($templ,$FILE_LABEL,$file);
	key_on($templ,$LINE_LABEL,$line);

	return 1;
    };	

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
	    $i=abs($i);
	    $j=abs($j);

	    return $j>$i ? $map->[$j]->[$i] : $map->[$i]->[$j];
	}
    }
    if(uc($type) eq 'QUARTER'){
	return sub {
	    my ($i,$j)=@_;
	    $i=abs($i);
	    $j=abs($j);

	    return $map->[$i]->[$j];
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
	die "setcellmap: invalid map $npin [@a]\n";
    }
    return @b;
}

1;
