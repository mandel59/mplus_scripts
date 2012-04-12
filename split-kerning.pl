#!/usr/local/bin/perl

# usage: split-kerning.pl WEIGHT /some/where/kernings > set_kernings

%names_subst = ( 
    "\"" => "quotedbl",
    "'" =>  "quotesingle",
    "`" =>  "grave",
    "\\" => "backslash",
);

$weight = shift;

@ARGV = grep { -e $_ } map { $_ = "../../../../svg.d/$_/kernings" } @ARGV;
exit 0 if (scalar @ARGV == 0);

%weight_columns = ( 'black' => 0, 'heavy' => 1, 'bold' => 2, 'medium' => 3,
		    'regular' => 4, 'light' => 5, 'thin' => 6);

print "AddLookup(\"kerning pairs\", \"gpos_pair\", 0, [[\"kern\", [[\"latn\", [\"dflt\"]]]]])\n";
print "AddLookupSubtable(\"kerning pairs\", \"kp\")\n";

while (<ARGV>) {
    next if /^###/ || /^\s*$/;
    while ($_ =~ s/\\\s*$//) {
	$_ .= <ARGV>;
    }

    my ($chars, @kerns) = split();
    my @first = get_first_char($chars);
    my @second = get_second_char($chars);

    $col = $weight_columns{$weight};
    foreach $L (@first) {
	$L = $names_subst{$L} if defined $names_subst{$L};
	foreach $R (@second) {
	    $R = $names_subst{$R} if defined $names_subst{$R};
	    print "Select(\"$L\"); SetKern(\"$R\", $kerns[$col],\"kp\")\n";
	}
    }
}


sub get_first_char {
    my $chars = shift;

    if ($chars =~ /^\[(\]?[^\]]*)\]/) {
	return(map chr, unpack("C*", $1));
    } else {
	return (substr($chars,0,1));
    }
}

sub get_second_char {
    my $chars = shift;

    if (substr($chars,0,1) eq '[') {
	$chars =~ s/^\[\]?[^\]]*\]//;
    } else {
	$chars =~ s/^.//;
    }
    return get_first_char($chars);
}

