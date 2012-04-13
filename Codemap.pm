# vim:set ts=8 sts=4 sw=4 tw=0:
#
# Last Change: 25-May-2004.
# Maintainer:  MURAOKA Taro <koron@tka.att.ne.jp>

package Codemap;

use strict;
use Carp;
use Data::Dumper;
use UCSTable;

my $FILENAME_CODEMAP = 'codemap';

sub new
{
    my $class = shift;
    my $dir = shift;
    if (not -d $dir) {
	croak "Can't find codemap dir $dir\n";
    }
    my $codemap = shift;
    $codemap ||= $FILENAME_CODEMAP;
    my $this = bless {
	dir => $dir,
	name2codes => {},
	mapfile_path => '',
	mapfile_line => 0,
    }, $class;
    my $path = join('/', $dir, $codemap);
    # Read codemap file
    open CODEMAP, $path or croak "Can't find codemap file $path\n";
    $this->{mapfile_path} = $path;
    while (<CODEMAP>) {
	++$this->{mapfile_line};
	chomp;
	if (m/^\s*#/) {
	    if (m/^\s*#\s*encoding\s+(\S+)/) {
		$this->{ucstable} = new UCSTable($1);
	    } else {
		next;
	    }
	} elsif (m/^\s*$/) {
	    next;
	} else {
	    my @array = split " ";
	    my $eps_filename = shift @array;
	    my $eps_path = join('/', $this->{dir}, $eps_filename);
	    if (-f $eps_path) {
		my $ucs_array = $this->_map2ucs(\@array);
		#print "$eps_path : ".join(' ', @$ucs_array)."\n";
		$this->{name2codes}->{$eps_path} = $ucs_array;
	    }
	}
    }
    close CODEMAP;
    # Check files are not included in codemap
    opendir LS, $dir;
    for my $file (readdir LS) {
	next if (not $file =~ m/^(?:.*\.svg)$/);
	my $path = join('/', $dir, $file);
	if (not exists $this->{name2codes}->{$path}) {
	    printf STDERR "$path isn't included in codemap file\n";
	}
    }
    closedir LS;
    return $this;
}

sub _map2ucs
{
    my $this = shift;
    my $codes = shift;
    my @ucs_array;
    if (not exists $this->{ucstable}) {
	for my $code (@$codes) {
	    my @mapped;
	    for my $code2 (split m/,/, $code)
	    {
		if ($code2 =~ m/^0x([[:xdigit:]]+)(u)?$/ and defined $2) {
		    push @mapped, sprintf('u%04X', hex($1));
		} elsif ($code2 =~ m/^0x([[:xdigit:]]+)(un)?$/ and defined $2) {
		    push @mapped, sprintf('jp04_uni%04X', hex($1));
		} else {
		    $this->_maperror($code2);
		}
	    }
	    my $map = scalar(@mapped);
	    if ($map == 1) {
		push @ucs_array, $mapped[0];
	    } elsif ($map > 1) {
		push @ucs_array, \@mapped;
	    }
	}
    } else {
	for my $code (@$codes) {
	    my @mapped;
	    for my $code2 (split m/,/, $code)
	    {
		if ($code2 =~ m/^0x([[:xdigit:]]+)(u)?$/) {
		    if (defined $2) {
			push @mapped, sprintf('u%04X', hex($1));
		    } else {
			my $ucs = $this->{ucstable}->get($1);
			if (defined $ucs) {
			    push @mapped, sprintf('u%04X', $ucs);
			} else {
			    $this->_maperror($code2);
			}
		    }
		} else {
		    $this->_maperror($code2);
		}
	    }
	    my $map = scalar(@mapped);
	    if ($map == 1) {
		push @ucs_array, $mapped[0];
	    } elsif ($map > 1) {
		push @ucs_array, \@mapped;
	    }
	}
    }
    return \@ucs_array;
}

sub _maperror
{
    my $this = shift;
    my $code = shift;
    printf STDERR ("Found code %s can't be map at line %d in %s\n",
	$code, $this->{mapfile_line}, $this->{mapfile_path});
}

sub keys
{
    my $this = shift;
    my @keys = keys(%{$this->{name2codes}});
    return \@keys;
}

sub get_codes
{
    my $this = shift;
    my $key = shift;
    if (exists $this->{name2codes}->{$key}) {
	return $this->{name2codes}->{$key};
    } else {
	return [];
    }
}

1;
