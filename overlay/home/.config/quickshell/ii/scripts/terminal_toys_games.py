import math


FONT = {
    'Y': ['#.#', '#.#', '.#.', '.#.', '.#.'],
    'O': ['.#.', '#.#', '#.#', '#.#', '.#.'],
    'U': ['#.#', '#.#', '#.#', '#.#', '###'],
    'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'I': ['###', '.#.', '.#.', '.#.', '###'],
    'E': ['###', '#..', '##.', '#..', '###'],
    'H': ['#.#', '#.#', '###', '#.#', '#.#'],
    'L': ['#..', '#..', '#..', '#..', '###'],
    'S': ['.##', '#..', '.#.', '..#', '##.'],
    'T': ['###', '.#.', '.#.', '.#.', '.#.'],
    'N': ['##.', '#.#', '#.#', '#.#', '#.#'],
    '!': ['#', '#', '#', '.', '#'],
}


def text_pixels(msg, x, y):
    out = []
    for ch in msg:
        if ch == ' ':
            x += 2
            continue
        rows = FONT[ch]
        for dy, row in enumerate(rows):
            for dx, c in enumerate(row):
                if c == '#':
                    out.append((x+dx, y+dy, dy))
        x += len(rows[0])+1
    return out


def text_width(msg):
    return sum(2 if ch == ' ' else len(FONT[ch][0])+1 for ch in msg)-1


def scenes(t):
    F = t.FRAMES
    W, H = t.W, t.H
    WHITE, INK = t.WHITE, t.INK
    HOP = [0, -1, -2, -1, 0, 0, 0, 0]
    SHAKE = [0, -1, 1, -1, 1, 0, 0, 0]
    WAVE = [round(math.sin(k/F*2*math.pi)) for k in range(F)]

    def post(s, fn):
        if not hasattr(s, 'posts'):
            s.posts = []
            base = s.image
            def image():
                out = base()
                for f in s.posts:
                    f(out)
                return out
            s.image = image
        s.posts.append(fn)

    def glow(s, cx, cy, r, color, strength):
        def fn(out):
            px = out.load()
            for y in range(max(0, int(cy-r)), min(H, int(cy+r)+1)):
                for x in range(max(0, int(cx-r)), min(W, int(cx+r)+1)):
                    d = math.hypot(x+.5-cx, y+.5-cy)
                    if d >= r:
                        continue
                    p = px[x, y]
                    if p[3] == 255:
                        continue
                    a = strength*(1-d/r)**1.6
                    px[x, y] = t.blend(p, color, round(255*a))
        post(s, fn)

    def overlay_text(s, msg, y, color, top, alpha):
        x0 = (W-text_width(msg))//2
        pts = text_pixels(msg, x0, y)
        def fn(out):
            px = out.load()
            for x, yy, row in pts:
                if 0 <= x < W and 0 <= yy < H:
                    px[x, yy] = t.blend(px[x, yy], top if row == 0 else color, round(255*alpha))
        post(s, fn)

    def stamp_text(s, msg, x, y, color, layer='fx'):
        for px, py, _ in text_pixels(msg, x, y):
            s.dot(px, py, color, layer)

    def rell(cx, cy, a, b, ang):
        c, n = math.cos(ang), math.sin(ang)
        return lambda x, y: (((x-cx)*c+(y-cy)*n)/a)**2+((-(x-cx)*n+(y-cy)*c)/b)**2 <= 1

    def disc(s, cx, cy, r, color, layer='light'):
        s.fill(t.ellipse(cx, cy, r, r), (color, color, color), light=None, rim=False, layer=layer)

    def ring(s, cx, cy, r, color, step=1, layer='light'):
        n = max(8, int(2*math.pi*r))
        for k in range(0, n, step):
            a = k/n*2*math.pi
            s.dot(cx+math.cos(a)*r, cy+math.sin(a)*r, color, layer)

    def motes(s, i, cx, base, n, speed, spread, rise, colors):
        for k in range(n):
            ph = ((i*speed)/F+k/n) % 1
            mx = cx+math.sin(k*2.4+ph*5)*(spread*(.4+(k % 3)*.3))
            my = base-ph*rise
            if 0 <= my < H:
                s.dot(mx, my, colors[0] if ph < .55 else colors[1], 'light')

    def draw_chest(s, state, i, accent):
        BL = ((104, 150, 232), (48, 82, 168), (26, 40, 100))
        GD = ((255, 238, 160), (228, 178, 62), (150, 96, 30))
        GR = {'h': (170, 255, 170), 'b': (52, 200, 84), 'l': (18, 116, 52), 'w': WHITE}
        sh = SHAKE[i] if state == 'error' else 0
        lift = HOP[i] if state == 'waiting' else 0
        cx = 16+sh
        by0 = 19+lift
        s.shadow = (16, 30.6, 12)
        opened = state == 'success'
        gap = [0, 0, 1, 1, 1, 1, 0, 0][i] if state == 'running' else 0
        if opened:
            glow(s, cx, by0-6, 16, (255, 228, 140), .65)
            for y in range(0, by0-6):
                half = 3+(by0-6-y)*.35
                for x in range(int(cx-half), int(cx+half)+1):
                    if (x-cx) % 2 == 0 and (y+i+abs(x-cx)) % 3 != 0:
                        s.dot(x, y, (255, 246, 200) if abs(x-cx) < 3 else (250, 214, 120), 'light')
            s.fill(t.rrect(cx-11, by0-6, cx+11, by0-2, 1), ((70, 104, 190), (30, 52, 120), (18, 28, 72)))
            s.paint(lambda x, y: abs(x-cx) >= 9 or y <= by0-5, GD[1])
            s.fill(t.rrect(cx-10, by0-2, cx+10, by0+.5, .3), ((255, 255, 240), (255, 240, 170), (246, 206, 110)), light=None, rim=False)
        if gap:
            glow(s, cx, by0-1, 13, (255, 228, 140), .6)
        s.fill(t.rrect(cx-11, by0, cx+11, 29.5, 1), BL)
        s.paint(lambda x, y: abs(x-cx) >= 9 or y >= 28 or y <= by0+1.5, GD[1])
        s.paint(lambda x, y: y <= by0+.9 and abs(x-cx) < 10.5, GD[0])
        s.paint(lambda x, y: y >= 29 or (abs(x-cx) >= 10.5 and y > by0+1), GD[2])
        for rx in (cx-10, cx+9):
            for ry in (by0+3, 26):
                s.dot(rx, ry, GD[2])
        if not opened:
            lid_b = by0-gap
            s.fill(lambda x, y: t.ellipse(cx, lid_b, 11, 7.5)(x, y) and y <= lid_b, BL)
            s.paint(lambda x, y: abs(x-cx) >= 9 and y <= lid_b, GD[1])
            s.paint(lambda x, y: lid_b-1.2 <= y <= lid_b, GD[2])
            s.stamp(['...y...', '..yyy..', '.y...y.', 'yyy.yyy'], cx-3, lid_b-6, {'y': GD[0]})
            if state != 'error':
                s.fill(t.rrect(cx-2.5, by0-1.5, cx+2.5, by0+4.5, .8), GD)
                s.stamp(['k', 'k'], cx, by0+1, {'k': INK})
        if state == 'error':
            pal = {'s': (206, 212, 226), 'g': (150, 156, 178), 'd': (100, 104, 126), 'k': INK}
            s.stamp(['.sss.', 's...s', 's...s', 'ggggg', 'ggkgg', 'gdkdg', 'ddddd'], cx-2, by0-2, pal, 'fx')
            for k in range(-9, 10, 3):
                s.dot(cx+k, by0+3+(k % 2), (180, 186, 204), 'fx')
            if i < 4:
                s.dot(cx+12, 27-i, (200, 190, 170), 'fx')
                s.dot(cx-12, 28-i, (200, 190, 170), 'fx')
        if opened:
            ry = by0-5-min(i, 4)*3
            s.stamp(['..h..', '.hhb.', 'hhbbl', 'hwbbl', 'hhbbl', '.bbl.', '..l..'], cx-2, ry, GR, 'fx')
            if i >= 3:
                t.sparkles(s, i, [(5, 5), (27, 6), (26, 14), (6, 14)])
        if state == 'idle':
            gx = [cx-10, cx-7, cx-4, cx-1, cx+2, cx+5, cx+8, None][i]
            if gx is not None:
                s.stamp(t.STAR_S, gx, by0-1, t.FX, 'fx')
        if state == 'waiting':
            t.attention(s, i, 24, 0)

    def draw_grace(s, state, i, accent):
        cx, base = 16, 27
        bright = {'idle': 1, 'running': 1.3, 'success': 1.45, 'error': .6, 'waiting': 1.1}[state]
        if state == 'waiting':
            bright *= [1, 1.08, 1.16, 1.08, 1, .94, .9, .94][i]
        s.shadow = None
        dirt = ((112, 100, 80), (78, 70, 58), (52, 46, 42))
        s.fill(lambda x, y: t.ellipse(cx, 31, 6, 2)(x, y) and y <= 31.5, dirt)
        for gx, gh, lean in ((cx-5, 2, -1), (cx+5, 2, 1), (cx+3, 1, 0)):
            s.line(gx, 29, gx+lean, 29-gh, (96, 132, 62))
        if state != 'error':
            glow(s, cx, base-5, 12*bright, (255, 214, 120), min(.7, .42*bright))
        else:
            glow(s, cx, base-3, 6, (220, 150, 80), .3)
        dim = state == 'error'
        outer = (214, 138, 56) if dim else (242, 176, 64)
        mid = (236, 172, 80) if dim else (255, 216, 112)
        core = (255, 220, 160) if dim else (255, 250, 226)

        def tongue(dx, h, w, lean, color, phase):
            for y in range(int(base-h), base+1):
                v = (base-y)/h
                if v < 0 or v > 1:
                    continue
                xc = cx+dx+lean*v*v+math.sin(i*.8+v*3+phase)*.7*v
                half = w*(1-v)**.75
                for x in range(int(xc-half-1), int(xc+half+2)):
                    if abs(x+.5-xc) <= max(half, .5):
                        s.dot(x, y, color, 'light')

        h = 11*bright
        for k, (dx, hh, ph) in enumerate(((-4.5, .6, 1.1), (4.8, .65, 2.3), (-2.4, .85, 3.1), (2.6, .9, .4), (-.6, 1.1, 1.9), (.8, 1.0, 4.4))):
            top = base-h*hh
            for y in range(int(top), base):
                v = (base-y)/(h*hh)
                x = cx+dx*v**.8+math.sin(i*.9+v*4+ph)*.9*v
                if v < .8 or (y+i+k) % 2 == 0:
                    s.dot(x, y, outer if v > .55 else mid, 'light')
        tongue(0, h*.45, 1.6, 0, mid, 0)
        tongue(0, h*.3, 1, 0, core, 0)
        disc(s, cx, base-1, 2, mid)
        disc(s, cx, base-1.3, 1.2, core)
        n = {'idle': 4, 'running': 6, 'success': 9, 'error': 2, 'waiting': 5}[state]
        sp = {'idle': 1, 'running': 2, 'success': 2, 'error': 1, 'waiting': 1}[state]
        motes(s, i, cx, base-3, n, sp, 7, 22, ((255, 232, 140), (226, 176, 70)))
        if state == 'running':
            for ang, strong in ((-1.05, True), (-2.2, False)):
                for d in range(6, 26):
                    if (d-i*2) % 4 == 0 or (strong and (d-i*2) % 4 == 1):
                        s.dot(cx+math.cos(ang)*d, base-10+math.sin(ang)*d, (255, 230, 150) if strong else (230, 190, 100), 'light')
        if state == 'success':
            for k, r in enumerate((3+i*1.7, 1+i*1.7)):
                if r > 1.5 and r < 17:
                    ring(s, cx, base-6, r, (255, 236, 160) if k == 0 else (240, 196, 90), 1 if k == 0 else 2)
        if state == 'error':
            a = [0, .45, .85, 1, 1, 1, 1, .9][i]
            s.band(10.5, 21.5, (6, 2, 4), .82*a)
            overlay_text(s, 'YOU DIED', 13, (176, 26, 30), (226, 76, 64), a)
        if state == 'waiting':
            t.attention(s, i, 24, 1)

    def draw_navi(s, state, i, accent):
        palettes = {
            'blue': ((70, 140, 245), (170, 220, 255), (110, 180, 255)),
            'green': ((50, 180, 90), (190, 255, 200), (110, 235, 140)),
            'yellow': ((220, 170, 30), (255, 245, 170), (255, 216, 70)),
        }
        tone = {'success': 'green', 'error': 'yellow'}.get(state, 'blue')
        ring_c, inner_c, glow_c = palettes[tone]
        if state == 'running':
            a = i/F*2*math.pi
            cx, cy = 16+7*math.sin(a), 16+3.5*math.sin(2*a)
            trail = [(16+7*math.sin(a-k*.5), 16+3.5*math.sin(2*(a-k*.5))) for k in (1, 2, 3)]
        elif state == 'error':
            cx, cy = 16+[0, -3, 2, -2, 3, -1, 1, 0][i], 16+[0, 1, -2, 2, -1, 1, -2, 0][i]
            trail = []
        elif state == 'waiting':
            cx, cy = 16, 20+[0, -1, -2, -1, 0, -1, -2, -1][i]
            trail = []
        elif state == 'success':
            cx, cy = 16, 16+HOP[i]
            trail = []
        else:
            cx, cy = 16, 16+WAVE[i]
            trail = []
        flap = i % 2 == 0 if state in ('running', 'error', 'success') else i % 4 < 2
        glow(s, cx, cy, 14, glow_c, .85)
        for k, (tx, ty) in enumerate(trail):
            if (i+k) % 2 == 0:
                s.dot(tx, ty, inner_c, 'light')
            s.dot(tx+(k % 2), ty+1, glow_c, 'light')
        wing = ((250, 252, 255), (206, 226, 255), (128, 164, 232))
        up = .8 if flap else .35
        for side in (-1, 1):
            for spread, length, width in ((up, 5.6, 1.7), (-.45 if flap else -.25, 3.8, 1.3)):
                dx, dy = side*math.cos(spread), -math.sin(spread)
                wx, wy = cx+dx*(3+length*.75), cy+dy*(3+length*.75)
                s.fill(rell(wx, wy, length, width, math.atan2(dy, dx)), wing, light=(0, 1), layer='light')
        disc(s, cx, cy, 4.4, ring_c)
        disc(s, cx, cy, 3.3, inner_c)
        disc(s, cx, cy, 1.9, (255, 255, 255))
        if state == 'success':
            t.sparkles(s, i, [(6, 7), (26, 8), (25, 25), (7, 24)])
        if state == 'waiting':
            msg = 'HEY!' if i < 4 else 'LISTEN!'
            stamp_text(s, msg, (W-text_width(msg))//2, 1, WHITE)

    def draw_eye(s, state, i, accent):
        bob = WAVE[i]
        sh = SHAKE[i] if state == 'error' else 0
        dash = [0, -1, -2, -3, -2, -1, 0, 0][i] if state == 'running' else 0
        cx, cy, R = 14+sh+dash, 15+bob, 8.5
        s.shadow = (15, 30.6, 7)
        red = ((220, 80, 90), (168, 30, 44), (106, 18, 32))
        amp = 1.6 if state == 'running' else 1.1
        for k, oy in enumerate((-4.5, 0, 4.5)):
            pts = []
            for x10 in range(int((cx+5)*2), 62):
                x = x10/2
                f = (x-cx-5)/12
                y = cy+oy*(1+f*.5)+math.sin(x*.7+i*(1.6 if state == 'running' else .8)+k*2)*amp*f
                pts.append((x, y))
            s.blob(pts, .9 if k != 1 else 1.1, red)
        sclera = ((255, 250, 246), (238, 226, 222), (200, 170, 172)) if state != 'error' else ((255, 236, 236), (240, 206, 206), (200, 150, 156))
        s.fill(t.ellipse(cx, cy, R, R), sclera)
        for ang in (-2.1, -1.0, .1, 1.1, 2.2):
            x0, y0 = cx+math.cos(ang)*(R-.4), cy+math.sin(ang)*(R-.4)
            x1, y1 = cx+math.cos(ang)*(R-3.4), cy+math.sin(ang)*(R-3.4)
            s.line(x0, y0, x1, y1, (204, 46, 58))
            s.dot(x1+math.cos(ang+1.4), y1+math.sin(ang+1.4), (204, 46, 58))
        if state == 'error':
            mx, my = cx-3.5, cy+.5
            s.fill(t.ellipse(mx, my, 3.6, 5.6), ((150, 34, 44), (96, 16, 28), (56, 8, 18)), light=None)
            for k, yy in enumerate(range(int(my-4), int(my+5), 2)):
                s.dot(mx-2.5, yy, WHITE)
                s.dot(mx+2, yy+1, WHITE)
            if i % 4 < 2:
                for k in range(3):
                    s.dot(mx-1+k, my+6.5+(i % 2), (200, 30, 40), 'fx')
            return
        if state == 'waiting':
            ix, iy, rx, ry = cx-1, cy, 3.8, 3.8
        elif state == 'success':
            ix, iy, rx, ry = cx-3.5, cy-2.5, 3.2, 3.8
        else:
            look = [0, 0, 0, -1, -1, 0, 1, 0][i] if state == 'idle' else 0
            ix, iy, rx, ry = cx-4.2, cy+.5+look, 3, 4.3
        s.fill(t.ellipse(ix, iy, rx, ry), ((130, 190, 245), (64, 116, 206), (30, 60, 134)), light=None)
        s.fill(t.ellipse(ix, iy, rx*.45, ry*.55), ((40, 30, 50), (20, 16, 30), (10, 8, 16)), light=None, rim=False)
        s.dot(ix-1, iy-2, WHITE)
        if state == 'running':
            for k, y in enumerate((cy-6, cy-1, cy+4)):
                n = 4+((i+k) % 3)
                s.line(cx+R+9, y, cx+R+9+n, y, (230, 230, 240), 'light')
        if state == 'success':
            coin = {'y': (255, 214, 72), 'h': (255, 248, 200), 'd': (190, 140, 30)}
            for k in range(3):
                ph = ((i/F)+k/3) % 1
                x = 4+k*9+ph*4
                y = 9-math.sin(ph*math.pi)*8
                s.stamp(['hy', 'yd'], x, y, coin, 'fx')
        if state == 'waiting':
            t.attention(s, i, 24, 0)

    def draw_tear(s, state, i, accent):
        wilt = state == 'error'
        sway = WAVE[i] if state in ('idle', 'waiting') else 0
        hx, hy = 16+sway, 12
        if wilt:
            hx, hy = 19+[0, 0, 1, 1, 1, 1, 1, 1][i], 16+[0, 1, 2, 2, 2, 2, 2, 2][i]
        green = ((140, 210, 140), (76, 160, 96), (40, 100, 62)) if not wilt else ((150, 170, 120), (104, 124, 84), (70, 84, 60))
        pts = []
        for k in range(15):
            u = k/14
            x = 16+(hx-16)*u**2
            y = 30-(30-(hy+3))*u
            if wilt:
                x = 16+(hx-16)*u**1.5
            pts.append((x, y))
        s.blob(pts, .6, green)
        s.fill(rell(13, 25, 3.2, 1.3, -.5), green)
        s.fill(rell(19.2, 22.6, 3.2, 1.3, .55), green)
        scale = 1.0
        if state == 'success':
            scale = [1, 1.08, 1.16, 1.2, 1.2, 1.2, 1.2, 1.2][i]
        if state != 'error':
            g = {'idle': .45, 'running': .45+.25*(i % 4 in (1, 2)), 'success': .75, 'waiting': .55}[state]
            glow(s, hx, hy, 11*scale, (176, 214, 255), g)
        petal = ((246, 252, 255), (196, 224, 255), (128, 170, 234)) if not wilt else ((214, 218, 224), (170, 176, 188), (118, 122, 138))
        rot = .15*WAVE[(i+2) % F] if not wilt else .4
        n = 7
        for k in range(n):
            a = rot+k*2*math.pi/n-math.pi/2
            if wilt and k == 3 and i >= 3:
                continue
            px, py = hx+math.cos(a)*3.3*scale, hy+math.sin(a)*2.8*scale
            s.fill(rell(px, py, 2.6*scale, 1.3*scale, a), petal, light=None)
        s.fill(t.ellipse(hx, hy, 1.5, 1.3), ((255, 255, 240), (240, 246, 210), (190, 210, 170)), light=None)
        if wilt and i >= 3:
            fx, fy = hx+3+(i-3)*.6, hy+3+(i-3)*2.2
            s.fill(rell(fx, fy, 1.8, .9, .6+i*.3), petal, light=None, layer='fx')
        if state in ('running', 'success'):
            motes(s, i, hx, hy+2, 6 if state == 'running' else 9, 2, 6, 14, ((230, 244, 255), (150, 196, 255)))
        if state == 'success' and i >= 2:
            t.sparkles(s, i, [(6, 6), (26, 5), (27, 17)])
        if state == 'waiting':
            t.attention(s, i, 24, 0)

    def draw_weiss(s, state, i, accent):
        bob = WAVE[i]
        sh = SHAKE[i] if state == 'error' else 0
        cover = ((252, 252, 248), (226, 224, 218), (168, 164, 162))
        gold = ((255, 232, 150), (214, 168, 66), (140, 96, 34))
        silver = ((248, 248, 252), (204, 204, 216), (140, 140, 158))
        s.shadow = (16, 30.6, 8)
        if state == 'success':
            y0 = 11+bob
            glow(s, 16, y0, 14, (255, 236, 170), .55)
            for k in range(7):
                a = -math.pi/2+(k-3)*.32
                for d in range(5, 13):
                    if (d+i) % 3 != 0 and k % 2 == i % 2:
                        s.dot(16+math.cos(a)*d, y0+1+math.sin(a)*d, (255, 230, 140), 'light')
            s.fill(t.rrect(2, y0, 30, y0+14, 1), cover)
            s.paint(lambda x, y: y >= y0+13, gold[1])
            page = ((255, 252, 240), (244, 236, 214), (210, 196, 168))
            s.fill(lambda x, y: 3 <= x <= 15.5 and y0-1+abs(x-9)*.12 <= y <= y0+12.5, page, light=None)
            s.fill(lambda x, y: 16.5 <= x <= 29 and y0-1+abs(x-23)*.12 <= y <= y0+12.5, page, light=None)
            for row in range(3):
                for x in range(5, 14):
                    if (x+row) % 4:
                        s.dot(x, y0+2+row*3, (150, 136, 120))
                for x in range(18, 27):
                    if (x+row+1) % 4:
                        s.dot(x, y0+2+row*3, (150, 136, 120))
            s.line(16, y0-1, 16, y0+13, (120, 104, 96))
            r = 3+(i % 4)*.6
            ring(s, 16, y0-6, r, (255, 226, 120), 2, 'fx')
            t.sparkles(s, i, [(4, 4), (28, 6), (27, 26)])
            return
        x0, x1 = 8+sh, 24+sh
        y0, y1 = 6+bob, 26+bob
        s.fill(t.rrect(x0+1, y0+1, x1+1.6, y1+1, .5), ((255, 250, 232), (238, 228, 200), (196, 182, 156)))
        s.fill(t.rrect(x0, y0, x1, y1, 1), cover)
        s.paint(lambda x, y: x <= x0+1.6, (130, 118, 126))
        s.paint(lambda x, y: (x0+2.5 <= x <= x1-1.5 and y0+1.5 <= y <= y1-1.5) and not (x0+3.5 <= x <= x1-2.5 and y0+2.5 <= y <= y1-2.5), gold[1])
        for gx, gy in ((x0+2.5, y0+1.5), (x1-2.5, y0+1.5), (x0+2.5, y1-2.5), (x1-2.5, y1-2.5)):
            s.fill(t.rrect(gx-.5, gy-.5, gx+1.5, gy+1.5, .3), gold, light=None)
        mx, my = (x0+x1)/2+.5, (y0+y1)/2+.5
        s.fill(t.ellipse(mx, my, 4.6, 5.6), gold, light=None)
        s.fill(t.ellipse(mx, my, 3.4, 4.4), silver)
        s.stamp(['.g.', 'ggg'], mx-1.5, y0+3, {'g': gold[1]})
        s.stamp(['ggg', '.g.'], mx-1.5, y1-4, {'g': gold[1]})
        ex0, ex1, ey = mx-3, mx+1, my-1
        if state == 'idle':
            s.stamp(['kk'], ex0, ey+.5, {'k': INK})
            s.stamp(['kk'], ex1, ey+.5, {'k': INK})
            t.zzz(s, i, 25, 1)
        elif state == 'error':
            s.stamp(['r.', '.r'], ex0, ey, {'r': (230, 40, 50)})
            s.stamp(['.r', 'r.'], ex1, ey, {'r': (230, 40, 50)})
            t.puff(s, i, x1+3, y0+2, (120, 96, 150))
            t.puff(s, (i+4) % F, x0-2, y0+4, (120, 96, 150))
        else:
            c = (170, 90, 255) if state == 'running' else INK
            s.stamp(['kk', 'kk'], ex0, ey, {'k': c})
            s.stamp(['kk', 'kk'], ex1, ey, {'k': c})
        s.stamp(['kkk'], mx-1.5, my+2.5, {'k': (110, 108, 126)})
        if state == 'running':
            orb = ((214, 170, 255), (140, 72, 220), (76, 30, 140))
            for k in range(2):
                a = i/F*2*math.pi+k*math.pi
                ox, oy = mx+12*math.cos(a), my+8*math.sin(a)
                s.fill(t.ellipse(ox, oy, 1.8, 1.8), orb, light=None, layer='fx')
                s.dot(ox-math.cos(a+.5)*3, oy-math.sin(a+.5)*3, (150, 90, 220), 'light')
        if state == 'waiting':
            t.attention(s, i, 24, 0)

    return [
        ('fairy', 'Navi', 'flare', draw_navi),
        ('chest', 'Chest', 'inventory_2', draw_chest),
        ('ember', 'Grace', 'local_fire_department', draw_grace),
        ('eye', 'Cthulhu', 'visibility', draw_eye),
        ('moonflower', 'Lunar Tear', 'filter_vintage', draw_tear),
        ('tome', 'Weiss', 'menu_book', draw_weiss),
    ]
