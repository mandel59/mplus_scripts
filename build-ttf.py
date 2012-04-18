import math
import sys
import os
import re
import psMat
import fontforge

ttfname = sys.argv[1]
fontname, weight = os.path.splitext(ttfname)[0].rsplit('-', 1)
year = "2012"
version = "1.048"
modules = sys.argv[2:]

ascent = 860
descent = 140
em = ascent + descent

kanji_scale = 0.98
kanji_matrix = psMat.compose(
    psMat.translate(-em / 2, -ascent + em / 2), psMat.compose(
    psMat.scale(kanji_scale),
    psMat.translate(em / 2, ascent - em / 2)))

svg_uni_name = re.compile('u[0-9A-F]{4,5}', re.IGNORECASE)
feature_name = re.compile('([- 0-9a-zA-Z]{4})_(uni[0-9A-F]{4,5})')

alt_glyphs = {}
def svgname_to_glyphname(name):
    if svg_uni_name.match(name):
        return (int(name[1:], 16),)
    m = feature_name.match(name)
    if m:
        tag = m.group(1)
        name = m.group(2)
        tagged_name = "%s.%s" % (name, tag)
        if not (tag in alt_glyphs):
            alt_glyphs[tag] = []
        alt_glyphs[tag].append((name, tagged_name))
        return (-1, tagged_name)
    return (-1, name)

def import_svg(svgpath, svgfile):
    name, ext = os.path.splitext(os.path.basename(svgfile))
    if ext != '.svg':
        raise Exception('%s is not SVG file' % os.path.join(svgpath, svgfile))
    glyphname = svgname_to_glyphname(name)
    c = f.createChar(*glyphname)
    c.width = em
    c.vwidth = em
    c.clear()
    c.importOutlines(os.path.join(svgpath, svgfile),
        ('removeoverlap', 'correctdir'))
    f.selection.select(('more',), c)

def import_svgs(svgdir):
    for svgfile in os.listdir(svgdir):
        try:
            import_svg(svgdir, svgfile)
        except Exception as message:
            print(message)

def import_kanji(moddir):
    for svgdir in os.listdir(moddir):
        import_svgs(os.path.join(moddir, svgdir))

glyph_name = re.compile(r'^(u|uni)?([0-9A-F]{4,5})$')
def get_glyph_by_name(name):
    if len(name) == 1 and ord(name) in f:
        return f[ord(name)]
    elif name == 'space':
        if ord(' ') in f:
            c = f[ord(' ')]
        else:
            c = f.createChar(ord(' '))
            c.width = em
            c.vwidth = em
        return c
    m = glyph_name.match(name)
    if m:
        ucode = int(m.group(2), 16)
        if ucode in f:
            c = f[ucode]
        else:
            c = f.createChar(ucode)
    else:
        if name in f:
            c = f[name]
        else:
            c = f.createChar(-1, name)
            c.width = em
            c.vwidth = em
    return c

charspaces_comment = re.compile(r'^#')
bearings_comment = re.compile(r'^###')
bearings_space = re.compile(r'^\s*$')
bearings_format = re.compile(r'(\+|w)?([-0-9]+)')
weights_position = {'black': 0, 'heavy': 1, 'bold': 2,
                    'medium': 3, 'regular': 4, 'light': 5, 'thin': 6}

def set_bearings_line(line, charspaces):
    splitted = line.split()
    position = weights_position[weight] * 2
    for s in splitted[1:]:
        if not bearings_format.match(s):
            raise Exception('format error: %s' % s)
    bearings = splitted[position + 1:position + 3]
    l, r = charspaces
    c = get_glyph_by_name(splitted[0])
    m = bearings_format.match(bearings[0])
    bearing = int(m.group(2))
    if m.group(1) == '+':
        c.left_side_bearing = c.left_side_bearing + bearing
    else:
        c.left_side_bearing = bearing + l
    m = bearings_format.match(bearings[1])
    bearing = int(m.group(2))
    if m.group(1) == '+':
        c.right_side_bearing = c.right_side_bearing + bearing
    elif m.group(1) == 'w':
        c.width = bearing
    else:
        c.right_side_bearing = bearing + r

def set_bearings(mod):
    charspaces_path = "../../../../svg.d/%s/charspaces" % mod
    bearings_path = "../../../../svg.d/%s/bearings" % mod
    if os.path.exists(charspaces_path):
        fp = open(charspaces_path, 'r')
        for line in fp:
            if charspaces_comment.match(line):
                continue
            if bearings_space.match(line):
                continue
            position = weights_position[weight] * 2
            splitted = line.split()
            charspaces = map(int, splitted[position:position + 2])
            break
        fp.close()
    else:
        charspaces = [0, 0]
    if os.path.exists(bearings_path):
        fp = open(bearings_path, 'r')
        line_count = 0
        for line in fp:
            line_count = line_count + 1
            if bearings_comment.match(line):
                continue
            if bearings_space.match(line):
                continue
            try:
                set_bearings_line(line, charspaces)
            except Exception as message:
                print(bearings_path, "line:", line_count)
                print(message)
        fp.close()

def set_vbearings_line(line):
    splitted = line.split()
    ch, method = splitted[0:2]
    h2v_shift = splitted[2:]
    c = get_glyph_by_name(ch)
    f.selection.select(c)
    f.copy()
    tag = 'vert'
    name = c.glyphname
    tagged_name = "%s.%s" % (name, tag)
    n = get_glyph_by_name(tagged_name)
    f.selection.select(n)
    alt_path = "../../../splitted/%s/%s/vert/u%04X.svg" % (
        weight, mod, c.unicode)
    if os.path.exists(alt_path):
        n.clear()
        n.importOutlines(alt_path, ('removeoverlap', 'correctdir'))
    else:
        f.paste()
        if method.find('R') >= 0:
            rot = psMat.compose(
                psMat.translate(-em / 2, -ascent + em / 2),
                psMat.compose(psMat.rotate(-math.pi / 2),
                psMat.translate(em / 2, ascent - em / 2)))
            n.transform(rot)
            if method.find('F') >= 0:
                flip = psMat.compose(
                    psMat.translate(-em / 2, -ascent + em / 2),
                    psMat.compose(psMat.scale(-1, 1),
                    psMat.translate(em / 2, ascent - em / 2)))
                n.transform(flip)
        elif method == 'S':
            position = weights_position[weight] * 2
            x, y = h2v_shift[position:position + 2]
            sht = psMat.translate(int(x), int(y))
            n.transform(sht)
            n.width = em
    if not (tag in alt_glyphs):
        alt_glyphs[tag] = []
    alt_glyphs[tag].append((name, tagged_name))

def set_vert_chars(mod):
    vbearings_path = "../../../../svg.d/%s/vbearings" % mod
    if os.path.exists(vbearings_path):
        fp = open(vbearings_path, 'r')
        line_count = 0
        for line in fp:
            line_count = line_count + 1
            if bearings_comment.match(line):
                continue
            if bearings_space.match(line):
                continue
            try:
                set_vbearings_line(line)
            except Exception as message:
                print(vbearings_path, "line:", line_count)
                print(message)
        fp.close()

def set_kernings_line(line):
    splitted = line.split()
    first, second = splitted[0][1:-1].split('][', 1)
    first = first.replace(
        '\\[', '[').replace('\\]', ']').replace('\\\\', '\\')
    second = second.replace(
        '\\[', '[').replace('\\]', ']').replace('\\\\', '\\')
    kerns = int(splitted[1:][weights_position[weight]])
    for l in first:
        cl = get_glyph_by_name(l)
        for r in second:
            cr = get_glyph_by_name(r)
            cl.addPosSub('kp', cr.glyphname, kerns)

def set_kernings(mod):
    kernings_path = "../../../../svg.d/%s/kernings" % mod
    if os.path.exists(kernings_path):
        fp = open(kernings_path, 'r')
        line_count = 0
        for line in fp:
            line_count = line_count + 1
            if bearings_comment.match(line):
                continue
            if bearings_space.match(line):
                continue
            try:
                set_kernings_line(line)
            except Exception as message:
                print(kernings_path, "line:", line_count)
                print(message)
        fp.close()

def set_fontnames():
    family = 'M+ ' + fontname[6:]
    if weight in ('black', 'heavy', 'bold'):
        subfamily = 'Bold'
    else:
        subfamily = 'Regular'
    fullname = ("%s %s" % (family, weight))
    copyright = "Copyright(c) %s M+ FONTS PROJECT" % year
    f.fontname = '%s-%s' % (fontname, weight)
    f.familyname = family
    f.fullname = fullname
    f.weight = weight
    f.copyright = copyright
    f.version = version
    f.sfnt_names = (
        ('English (US)', 'Copyright', copyright),
        ('English (US)', 'Family', fullname),
        ('English (US)', 'SubFamily', subfamily),
        ('English (US)', 'Fullname', fullname),
        ('English (US)', 'Version', 'Version %s' % version),
        ('English (US)', 'PostScriptName', '%s-%s' % (fontname, weight)),
        ('English (US)', 'Vendor URL', 'http://mplus-fonts.sourceforge.jp'),
        ('English (US)', 'Preferred Family', family),
        ('English (US)', 'Preferred Styles', weight),)

def set_os2_value():
    panose = [2, 11, 0, 2, 2, 2, 3, 2, 2, 7]
    panose[2] = 9 - weights_position[weight]
    if weight in ('light', 'thin'):
        panose[3] = 3
    else:
        panose[3] = 2
    f.os2_panose = tuple(panose)
    f.os2_vendor = 'M+  '
    f.os2_family_class = 2054
    f.os2_winascent_add = 0
    f.os2_windescent_add = 0
    f.hhea_ascent_add = 0
    f.hhea_descent_add = 0
    f.os2_winascent = 1075
    f.os2_windescent = 320
    f.hhea_ascent = 1075
    f.hhea_descent = -320
    f.hhea_linegap = 90

def merge_features():
    if fontname[7] != 'm':
        f.mergeFeature('ligature01.fea')
        f.mergeFeature('mark01.fea')
    f.mergeFeature('ccmp01.fea')
    f.mergeFeature('ccmp02.fea')

def set_ccmp():
    table = [
        (0xE055, "uni304B_uni309A"),
        (0xE056, "uni304D_uni309A"),
        (0xE057, "uni304F_uni309A"),
        (0xE058, "uni3051_uni309A"),
        (0xE059, "uni3053_uni309A"),
        (0xE205, "uni30AB_uni309A"),
        (0xE206, "uni30AD_uni309A"),
        (0xE207, "uni30AF_uni309A"),
        (0xE208, "uni30B1_uni309A"),
        (0xE209, "uni30B3_uni309A"),
        (0xE20D, "uni30BB_uni309A"),
        (0xE211, "uni30C4_uni309A"),
        (0xE213, "uni30C8_uni309A"),
        (0xE29B, "uni31F7_uni309A")]
    for t in table:
        try:
            c = f[t[0]]
            c.unicode = -1
            c.glyphname = t[1]
            c.addPosSub('kana semi-voiced table', tuple(t[1].split('_')))
        except Exception as message:
            print(t)
            print(message)

def set_alt_tables():
    tag_table = {
        'jp04': 'jp04table',
        'vert': 'j-vert'
    }
    for tag in alt_glyphs:
        for names in alt_glyphs[tag]:
            name, tagged_name = names
            c = get_glyph_by_name(name)
            c.addPosSub(tag_table[tag], tagged_name)

def set_kanji_aliases():
    kangxi_ucs = [
        0x4E00, 0x4E28, 0x4E36, 0x4E3F, 0x4E59, 0x4E85, 0x4E8C, 0x4EA0,
        0x4EBA, 0x513F, 0x5165, 0x516B, 0x5182, 0x5196, 0x51AB, 0x51E0,
        0x51F5, 0x5200, 0x529B, 0x52F9, 0x5315, 0x531A, 0x5338, 0x5341,
        0x535C, 0x5369, 0x5382, 0x53B6, 0x53C8, 0x53E3, 0x56D7, 0x571F,
        0x58EB, 0x5902, 0x590A, 0x5915, 0x5927, 0x5973, 0x5B50, 0x5B80,
        0x5BF8, 0x5C0F, 0x5C22, 0x5C38, 0x5C6E, 0x5C71, 0x5DDB, 0x5DE5,
        0x5DF1, 0x5DFE, 0x5E72, 0x5E7A, 0x5E7F, 0x5EF4, 0x5EFE, 0x5F0B,
        0x5F13, 0x5F50, 0x5F61, 0x5F73, 0x5FC3, 0x6208, 0x6236, 0x624B,
        0x652F, 0x6534, 0x6587, 0x6597, 0x65A4, 0x65B9, 0x65E0, 0x65E5,
        0x66F0, 0x6708, 0x6728, 0x6B20, 0x6B62, 0x6B79, 0x6BB3, 0x6BCB,
        0x6BD4, 0x6BDB, 0x6C0F, 0x6C14, 0x6C34, 0x706B, 0x722A, 0x7236,
        0x723B, 0x723F, 0x7247, 0x7259, 0x725B, 0x72AC, 0x7384, 0x7389,
        0x74DC, 0x74E6, 0x7518, 0x751F, 0x7528, 0x7530, 0x758B, 0x7592,
        0x7676, 0x767D, 0x76AE, 0x76BF, 0x76EE, 0x77DB, 0x77E2, 0x77F3,
        0x793A, 0x79B8, 0x79BE, 0x7A74, 0x7ACB, 0x7AF9, 0x7C73, 0x7CF8,
        0x7F36, 0x7F51, 0x7F8A, 0x7FBD, 0x8001, 0x800C, 0x8012, 0x8033,
        0x807F, 0x8089, 0x81E3, 0x81EA, 0x81F3, 0x81FC, 0x820C, 0x821B,
        0x821F, 0x826E, 0x8272, 0x8278, 0x864D, 0x866B, 0x8840, 0x884C,
        0x8863, 0x897E, 0x898B, 0x89D2, 0x8A00, 0x8C37, 0x8C46, 0x8C55,
        0x8C78, 0x8C9D, 0x8D64, 0x8D70, 0x8DB3, 0x8EAB, 0x8ECA, 0x8F9B,
        0x8FB0, 0x8FB5, 0x9091, 0x9149, 0x91C6, 0x91CC, 0x91D1, 0x9577,
        0x9580, 0x961C, 0x96B6, 0x96B9, 0x96E8, 0x9751, 0x975E, 0x9762,
        0x9769, 0x97CB, 0x97ED, 0x97F3, 0x9801, 0x98A8, 0x98DB, 0x98DF,
        0x9996, 0x9999, 0x99AC, 0x9AA8, 0x9AD8, 0x9ADF, 0x9B25, 0x9B2F,
        0x9B32, 0x9B3C, 0x9B5A, 0x9CE5, 0x9E75, 0x9E7F, 0x9EA5, 0x9EBB,
        0x9EC3, 0x9ECD, 0x9ED1, 0x9EF9, 0x9EFD, 0x9F0E, 0x9F13, 0x9F20,
        0x9F3B, 0x9F4A, 0x9F52, 0x9F8D, 0x9F9C, 0x9FA0,
    ]
    for i in range(0, len(kangxi_ucs)):
        kangxi_code = i + 0x2F00
        if kangxi_code in f:
            if kangxi_code == 0x2F5B:
                # KANGXI RADICAL FANG
                alt_glyphs['jp04'].append(('uni7259', 'uni2F5B'))
            continue
        if kangxi_ucs[i] in f:
            f.selection.select(kangxi_ucs[i])
            f.copyReference()
            n = get_glyph_by_name('uni%04X' % kangxi_code)
            f.selection.select(n)
            f.paste()

def set_kanji_altuni():
    kanjidir = '../../../../svg.d/kanji'
    for subdir in os.listdir(kanjidir):
        if subdir.upper().find('CVS') >= 0:
            continue
        altuni_path = os.path.join(kanjidir, subdir, 'altuni')
        if os.path.exists(altuni_path):
            fp = open(altuni_path, 'r')
            line_count = 0
            for line in fp:
                line_count += 1
                l = line.strip()
                if len(l) == 0 or l[0] == '#':
                    continue
                splitted = line.split(None, 1)
                name = splitted[0]
                def hex2int(s):
                    return int(s, 16)
                alts = [tuple(map(hex2int, x.split()))
                        for x in splitted[1].split(',')]
                if name in f:
                    try:
                        f[name].altuni = tuple(alts)
                    except Exception as message:
                        print(altuni_path, line_count)
                        print(message)
                        print(alts)
            fp.close()

# create font
f = fontforge.open('mplus.sfd')
f.encoding = 'unicode4'
f.hasvmetrics = True
ascent = ascent
f.descent = descent

kanji_flag = False
if 'kanji' in modules:
    kfontname = fontname[:7]
    if modules[0] == 'kanji':
        kanji_flag = True
        moddir = '../../../splitted/%s/%s' % (weight, 'kanji')
        glyphs = import_kanji(moddir)
        if kfontname == 'mplus-2':
            f.transform(kanji_matrix)
        for code in f.selection:
            c = f[code]
            c.width = em
            c.vwidth = em
    else:
        f.close()
        f = fontforge.open('../../%sk/%s/%sk-%s.ttf'
            % (kfontname, weight, kfontname, weight))
    modules.remove('kanji')


# import SVG files in each module
f.selection.none()
for mod in modules:
    moddir = '../../../splitted/%s/%s' % (weight, mod)
    import_svgs(moddir)

f.selection.all()
f.removeOverlap()
f.round()

# add lookups
if kanji_flag:
    f.addLookup('jis2004', 'gsub_single', (), (
        ("jp04", (("latn", ("dflt",)), ("grek", ("dflt",)),
                  ("cyrl", ("dflt",)), ("kana", ("dflt", "JAN ")),
                  ("hani", ("dflt",))),),))
    f.addLookupSubtable('jis2004', 'jp04table')
    set_kanji_aliases()
    set_kanji_altuni()
else:
    f.addLookup('gsubvert', 'gsub_single', (), (
        ("vert", (("latn", ("dflt",)), ("grek", ("dflt",)),
                  ("cyrl", ("dflt",)), ("kana", ("dflt", "JAN ")),
                  ("hani", ("dflt",))),),))
    f.addLookupSubtable('gsubvert', 'j-vert')
    f.addLookup('kerning pairs', 'gpos_pair', (), (
        ("kern", (("latn", ("dflt",)),)),))
    f.addLookupSubtable('kerning pairs', 'kp')
    f.addLookup('kana semi-voiced lookup', 'gsub_ligature', (), (
        ("ccmp", (("kana", ("JAN ", "dflt")),)),
        ("liga", (("kana", ("JAN ", "dflt")),))))
    f.addLookupSubtable('kana semi-voiced lookup', 'kana semi-voiced table')
    for mod in modules:
        set_bearings(mod)
        set_kernings(mod)
        set_vert_chars(mod)
    merge_features()
    set_ccmp()
    # set_instructions()

set_alt_tables()
set_fontnames()
set_os2_value()

f.generate(ttfname, '', ('short-post', 'opentype', 'PfEd-lookups'))
