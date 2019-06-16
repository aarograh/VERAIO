package ErrHandler;

use Exporter;
@ISA = ('Exporter');
@EXPORT=('err_set',
         'err_get',
         'err_size',
         'err_list',
         'err_keys',
         'err_flushkey',
         'err_flushdb'
    );

our %ERR_DB;

{
    my $_VERBOSE = 0;
    sub get_verbose  {$_VERBOSE;}
    sub set_verbose { $_VERBOSE = 1; }

    my $_DEBUG = 0;
    sub get_debug  {$_DEBUG;}
    sub set_debug { $_DEBUG = 1; }
}

sub err_set{
    my ($key, $val)=@_;
    print "set $key, $val\n" if get_debug();
    push @{$ERR_DB{$key}}, $val;
    return;
}
sub err_get{
    my $key=shift @_;
    my $val;
    $val=shift @{$ERR_DB{$key}};
    print "get $key, $val\n" if get_debug();
    return $val;
}
sub err_size{
    my $key = shift @_;
    my $n=@{$ERR_DB{$key}};
    return $n;
}
sub err_list{
    my $key = shift @_;
    my @a=@{$ERR_DB{$key}};
    return @a;
}
sub err_keys{
    my @keys = keys %ERR_DB;
    return @keys;
}
sub err_flushkey{
    my $key = shift @_;
    $ERR_DB{$key}=();
    return;
}
sub err_flushdb{
    %ERR_DB=();
    return;
}

return 1;
