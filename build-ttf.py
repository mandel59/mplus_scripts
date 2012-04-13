import sys
import os
import re
import psMat
import fontforge

ttfname = sys.argv[1]
fontname, weight = os.path.splitext(ttfname)[0].rsplit('-', 1)
modules = sys.argv[2:]

kanji_scale = 0.98
kanji_matrix = psMat.compose(
    psMat.translate(-500, -500), psMat.compose(
    psMat.scale(kanji_scale), psMat.translate(500, 500)))

# create font
f = fontforge.open('mplus.sfd')
f.encoding = 'unicode4'
f.hasvmetrics = True
f.ascent = 860
f.descent = 140

svg_uni_name = re.compile('u[0-9A-F]{4,5}', re.IGNORECASE)

def svgname_to_glyphname(name):
    if svg_uni_name.match(name):
        return (int(name[1:], 16),)
    else:
        return (-1, name)

def import_svg(svgpath, svgfile):
    name, ext = os.path.splitext(os.path.basename(svgfile))
    if ext != '.svg':
        raise Exception('%s is not SVG file' % os.path.join(svgpath, svgfile))
    glyphname = svgname_to_glyphname(name)
    c = f.createChar(*glyphname)
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
            space = f[ord(' ')]
            return space
        except Exception:
            return f.createChar(ord(' '))
    m = glyph_name.match(name)
    if m:
        try:
            glyph = f[int(m.group(2), 16)]
        except Exception:
            return f.createChar(int(m.group(2), 16))
    else:
        try:
            glyph = f[name]
        except Exception:
            return f.createChar(-1, name)
    return glyph

charspaces_comment = re.compile(r'^#')
bearings_comment = re.compile(r'^###')
bearings_space = re.compile(r'^\s*$')
bearings_format = re.compile(r'(\+|w)?([-0-9]+)')
weights_position = {'black': 0, 'heavy': 2, 'bold': 4,
                    'medium': 6, 'regular': 8, 'light': 10, 'thin': 12}

def set_bearings_line(line, charspaces):
    splitted = line.split()
    position = weights_position[weight]
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
            position = weights_position[weight]
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
                    c.width = c.vwidth = f.em
        else:
            f.mergeFonts('../../%sk/%s/%sk-%s.ttf'
                % (kfontname, weight, kfontname, weight))
    else:
        import_svgs(moddir)
        set_bearings(mod)

if modules[0] != 'kanji':
    f.removeOverlap()
    f.round()

f.generate(ttfname, '', ('short-post', 'opentype', 'PfEd-lookups'))
