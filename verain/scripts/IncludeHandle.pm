package IncludeHandle;
use strict;

use IO::File;
use Carp qw(carp);

sub TIEHANDLE {
  my $class = shift;

  my $file = shift;
  my $code = shift;             # might be string pattern, or qr//

  my $handle = IO::File->new($file, "r")
    or return undef;            # also sets $!

  unless ((ref $code || "") eq "CODE") {
    my $pattern = eval { qr/$code/ };
    $! = 29, return undef if $@; # bad RE
    $code = sub { $_ =~ $pattern ? $1 : undef };
  }

  bless {
         Handles => [$handle],
         Code    => $code,
        }, $class;
}

sub READLINE {
  my $self = shift;

  if (wantarray) {
    my @return;
    while (defined(my $line = $self->read_a_line)) {
      push @return, $line;
    }
    @return;
  } else {
    $self->read_a_line;
  }
}

sub read_a_line {
  my $self = shift;

  my $handles = $self->{Handles};
  {
    return undef unless @$handles;
    my $handle = $handles->[0];
    my $result = <$handle>;
    unless (defined $result) {
      shift @$handles;
      redo;
    }
    my $filename = do {
      local $_ = $result;
      $self->{Code}->();
    };
    if (defined $filename) {    # saw an include
      if (my $include_handle = IO::File->new($filename, "r")) {
        unshift @$handles, $include_handle;
      } else {
        carp "Cannot open $filename (skipping): $!";
      }
      redo;
    }
    $result;
  }
}

"0 but true";
