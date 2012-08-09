package REACTOR;

use KeyTree;
use MiscUtils;
use TypeUtils;

use REACTORBlock;
use REACTORCommand;

# use Clone qw(clone);
use ClonePP qw(clone);

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

{
    my $_VERBOSE = 0;
    sub get_verbose  {$_VERBOSE;}
    sub set_verbose { $_VERBOSE = 1; }

    my $_DEBUG = 0;
    sub get_debug  {$_DEBUG;}
    sub set_debug { $_DEBUG = 1; }

}

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
	print "@a\n" if get_verbose();
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
	print "@a\n" if get_verbose();
    }
    return @b;
}

sub clean_line{
    my $lineref=shift;

#    die "clean_line: invalid reference\n" unless (ref($lineref) eq 'SCALAR' && defined($$lineref));

    $$lineref =~ s/\// /g;                 # replace slashes with spaces
    $$lineref =~  s/(\!\s*(.*))$//;         # strip comments
    $$lineref =~ s/(\d+)\s*\*\s*(\w+)/"$2 " x $1/ge; # expand fortran expressions
#    $$lineref =~ s/(zero)/0/g;               # convert zero to 0
    $$lineref =~ s/['"]//g;                # remove quotes
    $$lineref =~ s/[,;]/ /g;               # remove commas and such
    $$lineref =~ s/^\s+//;                 # strip leading blanks
    $$lineref =~ s/\s+$//;                 # strip trailing blanks
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
	      $block->inp_db($INPUT_DB);
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
