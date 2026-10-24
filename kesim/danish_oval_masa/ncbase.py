import math
from shapely.geometry import Polygon, LineString
F = lambda v: ('%.3f' % v).rstrip('0').rstrip('.') if abs(v) > 1e-9 else '0'

def ccw(p, want=True):
    c = list(p.exterior.coords)
    if Polygon(c).exterior.is_ccw != want: c = c[::-1]
    return c
def off(p, d): return p.buffer(d, resolution=64, join_style=1)

class NC:
    def __init__(s, name): s.name = name; s.o = []; s.t = 0.0; s.cur = (0.0, 0.0); s.tool = None
    def tc(s, t, name, rpm):
        if s.tool is not None: s.o.append('M5')
        s.o += ['M6T%d ;Tool Name:%s' % (t, name), 'S%d M03' % rpm, 'h%d' % t]; s.tool = t
    def path(s, pts, z, fc, fz=2000, closed=True):
        pts = list(LineString(pts).simplify(0.03).coords)
        s.o += ['G0 X%s Y%s' % (F(pts[0][0]), F(pts[0][1])), 'G0 Z40', 'G1 Z%s F%d' % (F(z), fz)]
        s.o += ['G1 X%s Y%s Z%s F%d' % (F(x), F(y), F(z), fc) for x, y in pts[1:]]
        s.o.append('G0 Z40')
        s.t += LineString(pts).length / fc + math.dist(s.cur, pts[0]) / 25000 + 0.04; s.cur = pts[-1]
    def drill(s, x, y, z, fz=1500):
        s.o += ['G0 X%s Y%s' % (F(x), F(y)), 'G0 Z40', 'G1 Z%s F%d' % (F(z), fz), 'G0 Z40']; s.t += 0.05 + math.dist(s.cur, (x, y)) / 25000; s.cur = (x, y)
    def save(s, tools, desc):
        dk = s.t + 2; mm = int(dk); ss = int((dk - mm) * 60)
        head = [';NC', ';' + s.name, ';' + desc, ';SURE = %dDK %dSN' % (mm, ss)] + [';Tool=%d, Name=%s, Diameter=%s' % t for t in tools] + \
               ['#@PIECE_X=2100', '#@PIECE_Y=2800', 'E90=2']
        body = ['G79 Z0.', 'M10', '(DLY,2)', 'M12'] + s.o + ['M5', 'M11', 'M13', 'G0 G79 Z0.', 'M14']
        n = 0; out = []
        for l in body:
            if l.startswith('('): out.append(l); continue
            n += 1; out.append('N%d %s' % (n, l))
        open(s.name + '.anc', 'w', encoding='iso-8859-9', newline='').write('\r\n'.join(head + out + ['', ';Cut Time=%dMins %dSecs' % (mm, ss)]) + '\r\n')
        return mm

