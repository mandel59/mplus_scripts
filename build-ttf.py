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

# create font
f = fontforge.open('mplus.sfd')
f.encoding = 'unicode4'
f.hasvmetrics = True
f.ascent = 860
f.descent = 140

kanji_scale = 0.98
kanji_matrix = psMat.compose(
    psMat.translate(-f.em / 2, -f.ascent + f.em / 2), psMat.compose(
    psMat.scale(kanji_scale),
    psMat.translate(f.em / 2, f.ascent - f.em / 2)))

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
        if not alt_glyphs.has_key(tag):
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
    c.width = f.em
    c.vwidth = f.em
    c.clear()
    c.importOutlines(os.path.join(svgpath, svgfile),
        ('removeoverlap', 'correctdir'))
    f.selection.select(('more',), c)

def import_svgs(svgdir):
    for svgfile in os.listdir(svgdir):
        try:
            import_svg(svgdir, svgfile)
        except Exception, message:
            print message

def import_kanji(moddir):
    for svgdir in os.listdir(moddir):
        import_svgs(os.path.join(moddir, svgdir))

glyph_name = re.compile(r'(u|uni)?([0-9A-F]{4,5})')
def get_glyph_by_name(name):
    if len(name) == 1:
        return f[ord(name)]
    elif name == 'space':
        try:
            c = f[ord(' ')]
        except Exception:
            c = f.createChar(ord(' '))
            c.width = f.em
            c.vwidth = f.em
        return c
    m = glyph_name.match(name)
    if m:
        try:
            c = f[int(m.group(2), 16)]
        except Exception:
            c = f.createChar(int(m.group(2), 16))
    else:
        try:
            c = f[name]
        except Exception:
            c = f.createChar(-1, name)
            c.width = f.em
            c.vwidth = f.em
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
    bearings = splitted[position + 1:position + 3]
    l, r = charspaces
    c = get_glyph_by_name(splitted[0])
    m = bearings_format.match(bearings[0])
    if not m:
        raise Exception('format error: %s' % bearings[0])
    bearing = int(m.group(2))
    if m.group(1) == '+':
        c.left_side_bearing = c.left_side_bearing + bearing
    else:
        c.left_side_bearing = bearing + l
    m = bearings_format.match(bearings[1])
    if not m:
        raise Exception('format error: %s' % bearings[1])
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
            except Exception, message:
                print bearings_path, "line:", line_count
                print message
        fp.close()

def set_vbearings_line(line):
    splitted = line.split()
    ch, method = splitted[0:2]
    h2v_shift = splitted[2:]
    c = get_glyph_by_name(ch)
    f.selection.select(c)
    f.copy()
    n = f.createChar(-1, c.glyphname + '.vert')
    n.width = f.em
    n.vwidth = f.em
    f.selection.select(n)
    f.paste()
    if method.find('R') >= 0:
        rot = psMat.compose(
            psMat.translate(-f.em / 2, -f.ascent + f.em / 2),
            psMat.compose(psMat.rotate(-math.pi / 2),
            psMat.translate(f.em / 2, f.ascent - f.em / 2)))
        n.transform(rot)
        if method.find('F') >= 0:
            flip = psMat.compose(
                psMat.translate(-f.em / 2, -f.ascent + f.em / 2),
                psMat.compose(psMat.scale(-1, 1),
                psMat.translate(f.em / 2, f.ascent - f.em / 2)))
            n.transform(flip)
    elif method == 'S':
        position = weights_position[weight] * 2
        x, y = h2v_shift[position:position + 2]
        sht = psMat.translate(int(x), int(y))
        n.transform(sht)
        n.width = f.em
    alt_path = "../../../splitted/%s/%s/vert/u%04X.svg" % (
        weight, mod, c.unicode)
    if os.path.exists(alt_path):
        n.clear()
        n.importOutlines(alt_path, ('removeoverlap', 'correctdir'))
    c.addPosSub('j-vert', n.glyphname)

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
            except Exception, message:
                print vbearings_path, "line:", line_count
                print message
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
            except Exception, message:
                print kernings_path, "line:", line_count
                print message
        fp.close()

# add lookups
f.addLookup('gsubvert', 'gsub_single', ('ignore_ligatures'), (
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

f.addLookup('jis2004', 'gsub_single', (), (
    ("jp04", (("latn", ("dflt",)), ("grek", ("dflt",)),
              ("cyrl", ("dflt",)), ("kana", ("dflt", "JAN ")),
              ("hani", ("dflt",))),),))
f.addLookupSubtable('jis2004', 'jp04table')

# import SVG files in each module
f.selection.none()
for mod in modules:
    moddir = '../../../splitted/%s/%s' % (weight, mod)
    if mod == 'kanji':
        kfontname = fontname[:7]
        if modules[0] == 'kanji':
            glyphs = import_kanji(moddir)
            if kfontname == 'mplus-2':
                f.transform(kanji_matrix)
            for code in f.selection:
                c = f[code]
                c.width = f.em
                c.vwidth = f.em
        else:
            f.mergeFonts('../../%sk/%s/%sk-%s.ttf'
                % (kfontname, weight, kfontname, weight))
    else:
        import_svgs(moddir)

for mod in modules:
    set_bearings(mod)
    set_kernings(mod)
    set_vert_chars(mod)

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
    f.os2_family_class = 2054
    f.os2_winascent_add = 1075
    f.os2_windescent_add = 320
    f.hhea_ascent_add = 1075
    f.hhea_descent_add = -320
    f.hhea_linegap = 90

def merge_features():
    f.mergeFeature('ligature01.fea')
    f.mergeFeature('ccmp01.fea')
    f.mergeFeature('ccmp02.fea')
    f.mergeFeature('mark01.fea')

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
        except Exception, message:
            print t
            print message

def set_jp04():
    if alt_glyphs.has_key('jp04'):
        for names in alt_glyphs['jp04']:
            name, tagged_name = names
            c = get_glyph_by_name(name)
            c.addPosSub('jp04table', tagged_name)

f.selection.all()
f.removeOverlap()
f.round()
if modules[0] != 'kanji':
    merge_features()
    set_ccmp()
    # set_instructions()
else:
    set_jp04()
set_fontnames()
set_os2_value()

f.generate(ttfname, '', ('short-post', 'opentype', 'PfEd-lookups'))
