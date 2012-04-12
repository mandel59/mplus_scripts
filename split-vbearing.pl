#!/usr/local/bin/perl

# usage: split-vbearing.pl WEIGHT module_name > set_vert_chars

%names_subst = ( 
    "\"" => "quotedbl",
    "'" =>  "quotesingle",
    "`" =>  "grave",
    "\\" => "backslash",
);
%names_already_used = ();

$weight = shift;

@ARGV = grep { -e $_ } map { $_ = "../../../../svg.d/$_/vbearings" } @ARGV;
exit 0 if (scalar @ARGV == 0);

%weight_columns = ( 'black' => 0, 'heavy' => 2, 'bold' => 4, 'medium' => 6, 
		    'regular' => 8, 'light' => 10, 'thin' => 12);
$DX = $weight_columns{$weight};
$DY = $DX + 1;

print "xcenter = \$em / 2\n";
print "ycenter = (\$ascent - \$descent) / 2\n";
print "AddLookup(\"gsubvert\", \"gsub_single\", 0, [[\"vert\", [[\"latn\", [\"dflt\"]], [\"grek\", [\"dflt\"]], [\"cyrl\", [\"dflt\"]], [\"kana\", [\"dflt\", \"JAN \"]], [\"hani\", [\"dflt\"]]]]])\n";
print "AddLookupSubtable(\"gsubvert\", \"j-vert\")\n";
#print "SetFontHasVerticalMetrics(1)\n";
print "\n";

foreach $arg (@ARGV) {
    open(H2V_SHIFT, "<$arg") or die "can't open $arg";

    while ($_ = <H2V_SHIFT>) {
	next if /^###/ || /^\s*$/;

	my ($ch, $method, @h2v_shift) = split();
	$ch = $names_subst{$ch} if defined $names_subst{$ch};

	next if (defined $names_already_used{$ch});
	$names_already_used{$ch} = 1;

	print "SetCharCnt(CharCnt() + 1)\n";
	print "Select(\"$ch\"); Copy(); Select(CharCnt() - 1); Paste()\n";
	print "SetGlyphName(\"${ch}.vert\")\n";

	if ($method =~ /R/) {
	    print "Rotate(-90, xcenter, ycenter)\n";
	    if ($method =~ /F/) {
		print "HFlip(); CorrectDirection()\n";
	    }
	}

	if (defined $h2v_shift[$DX]) {
	    print ("Move($h2v_shift[$DX], $h2v_shift[$DY])\n");
	    print "SetWidth(\$em)\n";
	}

	my $module = $arg;
	$module =~ s/.*\/(.*)\/vbearings$/\1/;
	$vert = "../../../splitted/$weight/$module/vert/$ch.svg";
	$vert =~ s/vert\/uni/vert\/u/;
	print "if (FileAccess(\"$vert\") == 0) Select(\"$ch.vert\"); Import(\"$vert\"); endif\n";

	print "Reencode(\"unicode4\")\n";
	print "Select(\"$ch\"); AddPosSub(\"j-vert\", \"${ch}.vert\")\n";
	print "\n";
    }
    close H2V_SHIFT;
}
