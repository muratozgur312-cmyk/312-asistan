import math
def arc_center(s):
    x0, y0, x1, y1, r = s['x0'], s['y0'], s['x'], s['y'], s['r']
    dx, dy = x1 - x0, y1 - y0; q = math.hypot(dx, dy)
    h = math.sqrt(max(r * r - (q / 2) ** 2, 0)); mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    cw = s['g'] == 2
    sgn = (-1 if cw else 1) * (1 if r > 0 else -1)
    return mx - sgn * h * dy / q, my + sgn * h * dx / q
def pts(s, step=2.0):
    if s['g'] in (2, 3) and s['r']:
        cx, cy = arc_center(s); r = abs(s['r'])
        a0 = math.atan2(s['y0'] - cy, s['x0'] - cx); a1 = math.atan2(s['y'] - cy, s['x'] - cx)
        if s['g'] == 2:
            while a1 >= a0 - 1e-9: a1 -= 2 * math.pi
        else:
            while a1 <= a0 + 1e-9: a1 += 2 * math.pi
        n = max(2, int(abs(a1 - a0) * r / step))
        return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    return [(s['x0'], s['y0']), (s['x'], s['y'])]
