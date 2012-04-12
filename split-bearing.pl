#!/usr/local/bin/perl

# usage: split-bearing.pl WEIGHT module_name > set_bearings

%names_subst = ( 
    "\"" => "quotedbl",
    "'" =>  "quotesingle",
    "`" =>  "grave",
    "\\" => "backslash",
);

$weight = shift;

@ARGV = grep { -e $_ } map { $_ = "../../../../svg.d/$_/bearings" } @ARGV;
exit 0 if (scalar @ARGV == 0);

%weight_columns = ( 'black' => 0, 'heavy' => 2, 'bold' => 4, 'medium' => 6, 
		    'regular' => 8, 'light' => 10, 'thin' => 12);
$L = $weight_columns{$weight};
$R = $L+1;


foreach $arg (@ARGV) {
    open(BEARINGS, "<$arg") or die "can't open $arg";
    $cspace = $arg; $cspace =~ s/bearings$/charspaces/;
    if (-e $cspace) {
	open(CSPACE, "<$cspace") or die "$cspace exists but I can't open it";
	while ($line = <CSPACE>) {
	    @charspaces = split(" ", $line);
	    next if ($line =~ /^#/ || $line =~ /^\s*$/);
	    $dLSB = $charspaces[$L]; $dRSB = $charspaces[$R];
	    last;
	}
	close(CSPACE);
    } else { 
    	print STDERR "$cspace not exist: USE DEFAULT WIDTH \n";
	$dLSB = $dRSB = 0;
    }

    while ($_ = <BEARINGS>) {
	next if /^###/ || /^\s*$/;

	my ($ch, @bearings) = split();

	$l_is_relative = $r_is_relative = $r_is_width = 0;
	$l_is_relative = 1 if ($bearings[$L] =~ s/^[+]//);
	$r_is_width = 1 if ($bearings[$R] =~ s/^w//);
	$r_is_relative = 1 if ($bearings[$R] =~ s/^[+]//);
	    
	$ch = $names_subst{$ch} if defined $names_subst{$ch};
	print "Select(\"$ch\")\n";
	$bearings[$L] += $dLSB if not $l_is_relative;
	$bearings[$R] += $dRSB if not ($r_is_relative or $r_is_width);
	print "SetLBearing($bearings[$L], $l_is_relative)\n";
	if ($r_is_width) {
	    print "SetWidth($bearings[$R], $r_is_relative)\n";
	} else {
	    print "SetRBearing($bearings[$R], $r_is_relative)\n";
	}
    }
    close BEARINGS;
}
