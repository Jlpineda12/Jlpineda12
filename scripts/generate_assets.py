#!/usr/bin/env python3
"""
Genera los SVG animados del perfil (estilo retro web-dev / synthwave).

    python3 scripts/generate_assets.py

Todo es SVG puro con animaciones SMIL/CSS, así que se mueve dentro del README
de GitHub sin JavaScript. Las fuentes pixel (Press Start 2P y VT323, licencia
OFL) se incrustan como subconjuntos woff2 en base64 desde scripts/fonts/.
"""
import base64
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'retro')
FONTS = os.path.join(ROOT, 'scripts', 'fonts')
os.makedirs(OUT, exist_ok=True)
random.seed(1984)

CYAN, PINK, AMBER, LIME, VIOLET = '#00f5d4', '#ff2e88', '#fda415', '#39ff14', '#9b5de5'


def font_face():
    def b64(name):
        with open(os.path.join(FONTS, name), 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return (
        "@font-face{font-family:'PS2P';src:url(data:font/woff2;base64,%s) format('woff2');}"
        "@font-face{font-family:'VT';src:url(data:font/woff2;base64,%s) format('woff2');}"
        ".px{font-family:'PS2P',monospace}.vt{font-family:'VT',monospace}"
    ) % (b64('PressStart2P.woff2'), b64('VT323.woff2'))


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def svg(w, h, body, extra_css='', title=''):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<style>{font_face()}{extra_css}</style>
{body}
</svg>
'''


def write(name, content):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  assets/retro/{name}  ({len(content) // 1024} KB)')


def glow_filter(fid, std=3):
    return f'''<filter id="{fid}" x="-30%" y="-60%" width="160%" height="220%">
  <feGaussianBlur stdDeviation="{std}" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>'''


def typing_anim(full_w, n_chars, start, end, total):
    """Discrete SMIL width animation: types n_chars between start..end, holds, resets."""
    vals, keys = ['0'], ['0']
    for i in range(1, n_chars + 1):
        t = start + (end - start) * i / n_chars
        vals.append(f'{full_w * i / n_chars:.1f}')
        keys.append(f'{t / total:.4f}')
    vals.append('0')
    keys.append(f'{(total - 0.05) / total:.4f}')
    if float(keys[1]) == 0:
        keys[1] = '0.0001'
    return (f'<animate attributeName="width" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
            f'values="{";".join(vals)}" keyTimes="{";".join(keys)}"/>')


def show_at(t, total, hide=None):
    """Opacity 0 until t, 1 until hide (or loop end)."""
    hide = hide if hide is not None else total - 0.05
    return (f'<animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
            f'values="0;1;0" keyTimes="0;{t / total:.4f};{hide / total:.4f}"/>')


# ---------------------------------------------------------------------------
# Synthwave scenery helpers
# ---------------------------------------------------------------------------
def stars(w, h, n, twinkle=12):
    out = []
    for i in range(n):
        x, y = random.uniform(0, w), random.uniform(0, h)
        s = 2 if random.random() < 0.15 else 1.2
        op = random.uniform(0.35, 0.9)
        anim = ''
        if i < twinkle:
            d = random.uniform(1.5, 4)
            anim = f'<animate attributeName="opacity" values="{op:.2f};0.1;{op:.2f}" dur="{d:.1f}s" repeatCount="indefinite"/>'
        out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{s}" height="{s}" fill="#fff" opacity="{op:.2f}">{anim}</rect>')
    return '\n'.join(out)


def sun(cx, cy, r, gid):
    stripes = ''.join(
        f'<rect x="{cx - r}" y="{cy - r * 0.05 + i * r * 0.16:.1f}" width="{2 * r}" height="{2 + i * 2.2:.1f}" fill="#000"/>'
        for i in range(7))
    return f'''<defs>
  <linearGradient id="{gid}g" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffe66d"/><stop offset="0.45" stop-color="#ff9a5a"/>
    <stop offset="0.75" stop-color="#ff2e88"/><stop offset="1" stop-color="#9b1fe8"/>
  </linearGradient>
  <mask id="{gid}m"><rect x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{r}" fill="#fff"/>{stripes}</mask>
  <filter id="{gid}f" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>
</defs>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="#ff2e88" opacity="0.45" filter="url(#{gid}f)" mask="url(#{gid}m)">
  <animate attributeName="opacity" values="0.35;0.6;0.35" dur="5s" repeatCount="indefinite"/>
</circle>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid}g)" mask="url(#{gid}m)"/>'''


def grid_floor(w, top, bottom, vx, color_v=PINK, color_h=CYAN, n_h=9, dur=1.8):
    lines = []
    for i in range(-16, 17):
        lines.append(f'<line x1="{vx + i * 18}" y1="{top}" x2="{vx + i * 120}" y2="{bottom}" stroke="{color_v}" stroke-width="1.3" opacity="0.75"/>')
    for i in range(n_h):
        vals = []
        for k in range(11):
            p = ((i + k / 10) / n_h) ** 2.1
            vals.append(f'{top + p * (bottom - top):.1f}')
        ops = ';'.join(f'{0.15 + 0.85 * ((i + k / 10) / n_h):.2f}' for k in range(11))
        v = ';'.join(vals)
        lines.append(
            f'<line x1="0" x2="{w}" y1="{vals[0]}" y2="{vals[0]}" stroke="{color_h}" stroke-width="1.4">'
            f'<animate attributeName="y1" values="{v}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y2" values="{v}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="{ops}" dur="{dur}s" repeatCount="indefinite"/></line>')
    return '\n'.join(lines)


def scanlines(w, h, pid='scan'):
    return (f'<defs><pattern id="{pid}" width="4" height="3" patternUnits="userSpaceOnUse">'
            f'<rect width="4" height="1" fill="#000" opacity="0.28"/></pattern></defs>'
            f'<rect width="{w}" height="{h}" fill="url(#{pid})" pointer-events="none"/>')


# ---------------------------------------------------------------------------
# 1. HERO
# ---------------------------------------------------------------------------
def hero():
    W, H, HZ = 900, 420, 300
    T = 18  # loop seconds
    body = [f'''<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#07020f"/><stop offset="0.6" stop-color="#1d0836"/><stop offset="1" stop-color="#3b0b52"/>
  </linearGradient>
  <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#14031f"/><stop offset="1" stop-color="#030006"/>
  </linearGradient>
  <linearGradient id="win" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#000080"/><stop offset="1" stop-color="#1084d0"/>
  </linearGradient>
  {glow_filter('neon', 3)}
  {glow_filter('soft', 1.6)}
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>
</defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{HZ}" fill="url(#sky)"/>
{stars(W, HZ - 40, 90)}
{sun(450, HZ, 120, 'hs')}
<polygon points="0,{HZ} 70,{HZ - 38} 130,{HZ - 18} 210,{HZ - 62} 290,{HZ - 20} 330,{HZ} " fill="#2a0b45"/>
<polygon points="560,{HZ} 640,{HZ - 50} 700,{HZ - 22} 790,{HZ - 70} 900,{HZ - 26} 900,{HZ}" fill="#2a0b45"/>
<rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#floor)"/>
{grid_floor(W, HZ, H, 450)}
<rect y="{HZ - 1}" width="{W}" height="3" fill="{PINK}" filter="url(#neon)"/>''']

    # Left column: tag + neon name
    body.append(f'''<text x="40" y="54" class="vt" font-size="22" fill="#b39ebd">&lt;<tspan fill="{PINK}">developer</tspan> <tspan fill="{AMBER}">type</tspan>=<tspan fill="{CYAN}">"web"</tspan> <tspan fill="{AMBER}">style</tspan>=<tspan fill="{CYAN}">"retro"</tspan> /&gt;</text>
<g filter="url(#neon)">
  <text x="40" y="112" class="px" font-size="32" fill="#eafffb">JOSE LUIS
    <animate attributeName="opacity" values="1;1;0.45;1;1;0.6;1" keyTimes="0;0.55;0.56;0.58;0.8;0.81;1" dur="6s" repeatCount="indefinite"/></text>
  <text x="40" y="160" class="px" font-size="32" fill="#eafffb">PINEDA</text>
</g>
<text x="40" y="112" class="px" font-size="32" fill="none" stroke="{CYAN}" stroke-width="1" opacity="0.9">JOSE LUIS</text>
<text x="40" y="160" class="px" font-size="32" fill="none" stroke="{CYAN}" stroke-width="1" opacity="0.9">PINEDA</text>
<text x="40" y="196" class="px" font-size="11" fill="{AMBER}">WEB · GAMES · 3D · IA</text>
<text x="40" y="222" class="vt" font-size="22" fill="#d6c6e0">Ingeniería en Multimedia · Colombia</text>''')

    # Blinking INSERT COIN + hi score
    body.append(f'''<text x="40" y="262" class="px" font-size="10" fill="{LIME}" filter="url(#soft)">▶ INSERT COIN
  <animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" calcMode="discrete" dur="1.2s" repeatCount="indefinite"/></text>
<text x="230" y="262" class="px" font-size="10" fill="#b39ebd">HI <tspan fill="{AMBER}">012026</tspan></text>''')

    # Right column: Win95 terminal window
    X, Y, WW, WH = 480, 34, 380, 232
    body.append(f'''<g>
<rect x="{X + 6}" y="{Y + 8}" width="{WW}" height="{WH}" fill="#000" opacity="0.55"/>
<rect x="{X}" y="{Y}" width="{WW}" height="{WH}" fill="#c0c0c0"/>
<rect x="{X}" y="{Y}" width="{WW}" height="{WH}" fill="none" stroke="#fff" stroke-width="2"/>
<path d="M{X + WW} {Y} V{Y + WH} H{X}" fill="none" stroke="#404040" stroke-width="2"/>
<rect x="{X + 4}" y="{Y + 4}" width="{WW - 8}" height="22" fill="url(#win)"/>
<text x="{X + 12}" y="{Y + 20}" class="vt" font-size="19" fill="#fff">C:\\JLP\\PROFILE.EXE</text>
<g fill="#c0c0c0" stroke="#fff">
  <rect x="{X + WW - 62}" y="{Y + 8}" width="16" height="14"/><rect x="{X + WW - 44}" y="{Y + 8}" width="16" height="14"/><rect x="{X + WW - 24}" y="{Y + 8}" width="16" height="14"/>
</g>
<text x="{X + WW - 20}" y="{Y + 20}" class="vt" font-size="16" fill="#000">x</text>
<rect x="{X + 6}" y="{Y + 30}" width="{WW - 12}" height="{WH - 36}" fill="#05010a"/>
</g>''')

    lines = [  # (text, kind)  kind: cmd types, out appears
        ('C:\\JLP> whoami', 'cmd'),
        ('Jose Luis Pineda Barrera', 'out'),
        ('C:\\JLP> type skills.txt', 'cmd'),
        ('HTML CSS JS TS React Node', 'out'),
        ('Three.js Unity Unreal TensorFlow', 'out'),
        ('C:\\JLP> npm run arcade', 'cmd'),
        ('> 5 juegos cargados ...... OK', 'ok'),
        ('> READY_', 'ok'),
    ]
    t = 0.6
    ly = Y + 54
    tx = X + 16
    cw = 9.2  # VT323 @ 20px char width (approx)
    out = ['<g class="vt" font-size="20">']
    for i, (txt, kind) in enumerate(lines):
        color = {'cmd': '#c5ffd8', 'out': '#9aa3ff', 'ok': LIME}[kind]
        if kind == 'cmd':
            n = len(txt)
            dur = n * 0.07
            cid = f'tc{i}'
            out.append(f'<clipPath id="{cid}"><rect x="{tx}" y="{ly - 18}" height="24" width="0">{typing_anim(n * cw + 4, n, t, t + dur, T)}</rect></clipPath>')
            out.append(f'<text x="{tx}" y="{ly}" fill="{color}" clip-path="url(#{cid})">{esc(txt)}</text>')
            t += dur + 0.35
        else:
            out.append(f'<text x="{tx}" y="{ly}" fill="{color}" opacity="0">{esc(txt)}{show_at(t, T)}</text>')
            t += 0.3
        ly += 23
    # blinking block cursor at the end
    out.append(f'<rect x="{tx + 9 * cw}" y="{ly - 23 - 16}" width="10" height="18" fill="{LIME}" opacity="0">'
               f'<animate attributeName="opacity" values="0;1;0;1;0;1;0" keyTimes="0;{t / T:.3f};{(t + 0.5) / T:.3f};{(t + 1) / T:.3f};{(t + 1.5) / T:.3f};{(t + 2) / T:.3f};0.99" dur="{T}s" repeatCount="indefinite" calcMode="discrete"/></rect>')
    out.append('</g>')
    body.append('\n'.join(out))

    # little pixel car racing on the floor
    body.append(f'''<g opacity="0.95">
  <g>
    <rect x="0" y="0" width="34" height="8" fill="{PINK}"/><rect x="8" y="-6" width="16" height="6" fill="{PINK}"/>
    <rect x="11" y="-4" width="10" height="3" fill="#7df9ff"/><rect x="0" y="2" width="4" height="3" fill="#ffe66d"/>
    <rect x="4" y="8" width="6" height="4" fill="#111"/><rect x="24" y="8" width="6" height="4" fill="#111"/>
    <rect x="34" y="2" width="4" height="3" fill="#ff334b"><animate attributeName="opacity" values="1;0.2;1" dur="0.4s" repeatCount="indefinite"/></rect>
    <animateTransform attributeName="transform" type="translate" values="-60 386;960 386" dur="7s" repeatCount="indefinite"/>
  </g>
</g>''')

    body.append(scanlines(W, H, 'hscan'))
    body.append(f'''<rect width="{W}" height="{H}" fill="none" stroke="{CYAN}" stroke-opacity="0.5" stroke-width="2" rx="14"/>
<rect x="0" y="-60" width="{W}" height="60" fill="#fff" opacity="0.035">
  <animate attributeName="y" values="-60;{H}" dur="6s" repeatCount="indefinite"/></rect>
</g>''')
    write('hero.svg', svg(W, H, '\n'.join(body), title='Jose Luis Pineda — retro web developer'))


# ---------------------------------------------------------------------------
# 2. SECTION HEADERS  <tag /> style
# ---------------------------------------------------------------------------
def header(slug, label, color, icon):
    W, H = 900, 64
    tw = len(label) * 18 + 10
    body = f'''<defs>{glow_filter('g', 2.4)}
<linearGradient id="bar" x1="0" x2="1"><stop offset="0" stop-color="{color}" stop-opacity="0"/><stop offset="0.5" stop-color="{color}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>
<rect width="{W}" height="{H}" rx="10" fill="#0b0414"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{color}" stroke-opacity="0.35"/>
<text x="22" y="41" class="px" font-size="20" fill="{color}" filter="url(#g)">{icon}</text>
<text x="62" y="40" class="vt" font-size="30" fill="#8c7a99">&lt;</text>
<text x="80" y="41" class="px" font-size="18" fill="#fff" filter="url(#g)">{esc(label)}
  <animate attributeName="opacity" values="1;1;0.5;1;1" keyTimes="0;0.7;0.71;0.73;1" dur="{4 + len(label) % 3}s" repeatCount="indefinite"/></text>
<text x="{86 + tw}" y="40" class="vt" font-size="30" fill="#8c7a99">/&gt;</text>
<rect x="{116 + tw}" y="22" width="12" height="22" fill="{color}">
  <animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" calcMode="discrete" dur="1s" repeatCount="indefinite"/></rect>
<rect x="0" y="{H - 4}" width="240" height="3" fill="url(#bar)">
  <animate attributeName="x" values="-240;{W}" dur="3.2s" repeatCount="indefinite"/></rect>
<text x="{W - 20}" y="40" class="vt" font-size="20" fill="#5d4a6b" text-anchor="end">#{slug}</text>'''
    write(f'h-{slug}.svg', svg(W, H, body, title=label))


# ---------------------------------------------------------------------------
# 3. CARTRIDGE CARDS (clickable in the README -> live game)
# ---------------------------------------------------------------------------
def cartridge(slug, title, sub, color, scene):
    W, H = 280, 330
    bx, by, bw, bh = 22, 18, 236, 280
    # preview window
    px, py, pw, ph = bx + 26, by + 44, bw - 52, 128
    body = f'''<defs>{glow_filter('cg', 4)}
<linearGradient id="shell" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4f4860"/><stop offset="1" stop-color="#26212f"/></linearGradient>
<clipPath id="pv"><rect x="{px}" y="{py}" width="{pw}" height="{ph}"/></clipPath></defs>
<g>
<animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0" dur="3s" repeatCount="indefinite"/>
<ellipse cx="{W / 2}" cy="{by + bh + 22}" rx="96" ry="7" fill="{color}" opacity="0.35" filter="url(#cg)"/>
<path d="M{bx + 18} {by} H{bx + bw - 18} L{bx + bw} {by + 18} V{by + bh} H{bx} V{by + 18} Z" fill="url(#shell)" stroke="{color}" stroke-width="2.5"/>
{''.join(f'<rect x="{bx + 30 + i * 12}" y="{by + 8}" width="6" height="16" fill="#000" opacity="0.3"/>' for i in range(6))}
<rect x="{bx + bw - 64}" y="{by + 8}" width="44" height="18" fill="#12051a"/>
<text x="{bx + bw - 42}" y="{by + 21}" class="px" font-size="8" fill="{color}" text-anchor="middle">{scene['num']}</text>
<rect x="{bx + 14}" y="{by + 34}" width="{bw - 28}" height="{bh - 52}" fill="{color}"/>
<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#0d0418"/>
<g clip-path="url(#pv)">{scene['svg'](px, py, pw, ph)}</g>
{''.join(f'<rect x="{px}" y="{py + i}" width="{pw}" height="1" fill="#000" opacity="0.22"/>' for i in range(0, ph, 3))}
<text x="{W / 2}" y="{py + ph + 30}" class="px" font-size="13" fill="#12051a" text-anchor="middle">{esc(title)}</text>
<text x="{W / 2}" y="{py + ph + 48}" class="px" font-size="7" fill="#12051a" text-anchor="middle" opacity="0.8">{esc(sub)}</text>
<text x="{W / 2}" y="{py + ph + 74}" class="px" font-size="9" fill="#12051a" text-anchor="middle">▶ CLICK TO PLAY
  <animate attributeName="opacity" values="1;0.15;1" dur="1.4s" repeatCount="indefinite"/></text>
</g>'''
    write(f'cart-{slug}.svg', svg(W, H, body, title=f'{title} — click para jugar'))


def scene_snake(x, y, w, h):
    path = f'M{x + 20} {y + 30} H{x + w - 30} V{y + h - 26} H{x + 40} V{y + 60} H{x + w - 60} V{y + h - 50} H{x + 20} Z'
    segs = []
    for i in range(12):
        c = '#ffffff' if i == 0 else (CYAN if i % 2 else '#00b89f')
        segs.append(f'<rect x="-5" y="-5" width="10" height="10" fill="{c}"><animateMotion path="{path}" dur="7s" begin="-{i * 0.13:.2f}s" repeatCount="indefinite"/></rect>')
    grid = ''.join(f'<line x1="{x + i}" y1="{y}" x2="{x + i}" y2="{y + h}" stroke="{CYAN}" stroke-opacity="0.08"/>' for i in range(0, w, 12))
    apple = (f'<rect x="{x + w - 44}" y="{y + 70}" width="10" height="10" fill="#ff334b"><animate attributeName="opacity" values="1;0.4;1" dur="0.8s" repeatCount="indefinite"/></rect>'
             f'<rect x="{x + w - 40}" y="{y + 66}" width="4" height="4" fill="{LIME}"/>')
    return grid + apple + ''.join(reversed(segs))


def scene_combat(x, y, w, h):
    g = y + h - 18

    def fighter(fx, gi, band, flip, delay):
        s = -1 if flip else 1
        arm = f'<rect x="{fx + (14 if not flip else -10)}" y="{g - 40}" width="10" height="5" fill="{gi}"><animate attributeName="width" values="10;22;10;10" keyTimes="0;0.15;0.3;1" dur="1.6s" begin="{delay}s" repeatCount="indefinite"/>' + (f'<animate attributeName="x" values="{fx - 10};{fx - 22};{fx - 10};{fx - 10}" keyTimes="0;0.15;0.3;1" dur="1.6s" begin="{delay}s" repeatCount="indefinite"/>' if flip else '') + '</rect>'
        return f'''<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -2;0 0" dur="0.5s" repeatCount="indefinite"/>
<rect x="{fx}" y="{g - 56}" width="14" height="4" fill="#1e293b"/><rect x="{fx}" y="{g - 52}" width="14" height="10" fill="#fed7aa"/>
<rect x="{fx - 2}" y="{g - 52}" width="18" height="3" fill="{band}"/>
<rect x="{fx - 3}" y="{g - 42}" width="20" height="20" fill="{gi}"/><rect x="{fx - 3}" y="{g - 30}" width="20" height="3" fill="#111827"/>
{arm}
<rect x="{fx - 3}" y="{g - 22}" width="8" height="22" fill="{gi}"/><rect x="{fx + 9}" y="{g - 22}" width="8" height="22" fill="{gi}"/></g>'''
    sunc = f'<circle cx="{x + w / 2}" cy="{y + h - 20}" r="46" fill="#ff9a3c" opacity="0.85"/>'
    floor = f'<rect x="{x}" y="{g}" width="{w}" height="18" fill="#2a0b2f"/>'
    fb = (f'<g><rect x="0" y="{g - 38}" width="16" height="10" fill="#7df9ff" opacity="0.5"/><rect x="5" y="{g - 36}" width="8" height="6" fill="#fff"/>'
          f'<animateTransform attributeName="transform" type="translate" values="{x + 50} 0;{x + w - 70} 0" dur="1.8s" repeatCount="indefinite"/></g>')
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#3a0d3d"/>' + sunc + floor + fighter(x + 34, '#00bbf9', '#ff334b', False, 0) + fighter(x + w - 50, '#ff2a44', '#fee440', True, 0.8) + fb


def scene_space(x, y, w, h):
    st = ''.join(f'<rect x="{x + random.uniform(0, w):.0f}" y="{y + random.uniform(0, h):.0f}" width="1.5" height="1.5" fill="#fff" opacity="{random.uniform(0.3, 0.9):.2f}"/>' for _ in range(30))
    cols = ['#ff334b', AMBER, CYAN]
    aliens = []
    for r in range(3):
        for c in range(6):
            ax, ay = x + 18 + c * 26, y + 14 + r * 20
            col = cols[r]
            aliens.append(f'<rect x="{ax + 2}" y="{ay}" width="12" height="3" fill="{col}"/><rect x="{ax}" y="{ay + 3}" width="16" height="6" fill="{col}"/>'
                          f'<rect x="{ax + 4}" y="{ay + 4}" width="2" height="2" fill="#000"/><rect x="{ax + 10}" y="{ay + 4}" width="2" height="2" fill="#000"/>'
                          f'<rect x="{ax}" y="{ay + 9}" width="3" height="3" fill="{col}"><animate attributeName="x" values="{ax};{ax + 2}" dur="0.8s" calcMode="discrete" repeatCount="indefinite"/></rect>'
                          f'<rect x="{ax + 13}" y="{ay + 9}" width="3" height="3" fill="{col}"><animate attributeName="x" values="{ax + 13};{ax + 11}" dur="0.8s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    army = f'<g><animateTransform attributeName="transform" type="translate" values="-10 0;14 0;-10 0" dur="4s" calcMode="discrete" keyTimes="0;0.5;1" repeatCount="indefinite"/>' + ''.join(aliens) + '</g>'
    ship = (f'<g><animateTransform attributeName="transform" type="translate" values="{x + 30} {y + h - 18};{x + w - 50} {y + h - 18};{x + 30} {y + h - 18}" dur="5s" repeatCount="indefinite"/>'
            f'<rect x="0" y="6" width="22" height="6" fill="#e0fbfc"/><rect x="8" y="0" width="6" height="6" fill="#e0fbfc"/><rect x="10" y="-3" width="2" height="3" fill="{CYAN}"/>'
            f'<rect x="10" y="-10" width="2" height="7" fill="#fee440"><animate attributeName="y" values="-10;-110" dur="0.9s" repeatCount="indefinite"/></rect></g>')
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#050318"/>' + st + army + ship


def scene_breaker(x, y, w, h):
    cols = [AMBER, '#ff334b', '#ff758f', CYAN]
    bricks = []
    for r in range(4):
        for c in range(7):
            bx, byy = x + 6 + c * 25, y + 8 + r * 11
            hide = random.random() < 0.3
            anim = f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;{random.uniform(0.1, 0.8):.2f};0.85;0.99;1" dur="6s" repeatCount="indefinite"/>' if hide else ''
            bricks.append(f'<rect x="{bx}" y="{byy}" width="22" height="8" fill="{cols[r]}">{anim}</rect>')
    path = f'M{x + 30} {y + h - 16} L{x + w - 20} {y + 60} L{x + w - 60} {y + h - 16} L{x + 10} {y + 70} Z'
    ball = f'<rect x="-3" y="-3" width="6" height="6" fill="#fff"><animateMotion path="{path}" dur="3.2s" repeatCount="indefinite"/></rect>'
    pad = (f'<rect y="{y + h - 12}" width="44" height="6" fill="#ff758f"><animate attributeName="x" values="{x + 8};{x + w - 82};{x + 18}" keyTimes="0;0.5;1" dur="3.2s" repeatCount="indefinite"/></rect>')
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#1c0628"/>' + ''.join(bricks) + ball + pad


def scene_maze(x, y, w, h):
    walls = (f'<rect x="{x + 6}" y="{y + 6}" width="{w - 12}" height="{h - 12}" fill="none" stroke="#3c4bd6" stroke-width="3" rx="4"/>'
             f'<rect x="{x + 40}" y="{y + 48}" width="{w - 80}" height="{h - 96}" fill="none" stroke="#3c4bd6" stroke-width="3" rx="4"/>')
    lane = y + 27
    dots = ''.join(
        f'<rect x="{x + 20 + i * 15}" y="{lane - 2}" width="4" height="4" fill="#ffd7a8">'
        f'<animate attributeName="opacity" values="1;0;0;1" keyTimes="0;{(0.05 + i * 0.07):.2f};0.95;1" dur="4s" calcMode="discrete" repeatCount="indefinite"/></rect>'
        for i in range(11))
    pac = (f'<g><animateTransform attributeName="transform" type="translate" values="{x + 14} {lane};{x + w - 10} {lane}" dur="4s" repeatCount="indefinite"/>'
           f'<path d="M0 0 L10 -6 A11 11 0 1 0 10 6 Z" fill="#fee440"><animate attributeName="d" values="M0 0 L10 -6 A11 11 0 1 0 10 6 Z;M0 0 L11 -1 A11 11 0 1 0 11 1 Z;M0 0 L10 -6 A11 11 0 1 0 10 6 Z" dur="0.3s" repeatCount="indefinite"/></path></g>')
    ghost = (f'<g><animateTransform attributeName="transform" type="translate" values="{x - 40} {lane};{x + w - 60} {lane}" dur="4s" repeatCount="indefinite"/>'
             f'<path d="M-10 10 V-2 A10 10 0 0 1 10 -2 V10 L6 6 L2 10 L-2 6 L-6 10 Z" fill="#ff334b"/>'
             f'<rect x="-6" y="-4" width="5" height="6" fill="#fff"/><rect x="2" y="-4" width="5" height="6" fill="#fff"/>'
             f'<rect x="-3" y="-2" width="3" height="3" fill="#1a1aff"/><rect x="5" y="-2" width="3" height="3" fill="#1a1aff"/></g>')
    cherry = f'<circle cx="{x + w / 2 - 6}" cy="{y + h / 2 + 4}" r="6" fill="#ff334b"/><circle cx="{x + w / 2 + 6}" cy="{y + h / 2 + 6}" r="6" fill="#ff334b"/><path d="M{x + w / 2 - 6} {y + h / 2 - 2} Q{x + w / 2} {y + h / 2 - 20} {x + w / 2 + 6} {y + h / 2}" stroke="{LIME}" fill="none" stroke-width="2"/>'
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#02031a"/>' + walls + dots + cherry + ghost + pac


def scene_hub(x, y, w, h):
    colors = [CYAN, '#ff334b', AMBER, '#ff758f', '#fee440']
    names = ['SNAKE', 'COMBAT', 'SPACE', 'BREAKER', 'MAZE']
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#0c0418"/>']
    for i in range(14):
        out.append(f'<line x1="{x + w / 2}" y1="{y + h * 0.62}" x2="{x - 200 + i * 45}" y2="{y + h}" stroke="{PINK}" stroke-opacity="0.5"/>')
    out.append(f'<rect x="{x}" y="{y + h * 0.62}" width="{w}" height="2" fill="{CYAN}"/>')
    n = len(colors)
    for i, (c, nm) in enumerate(zip(colors, names)):
        vals = ';'.join('1' if k == i else '0' for k in range(n)) + (';1' if i == 0 else ';0')
        kt = ';'.join(f'{k / n:.2f}' for k in range(n)) + ';1'
        out.append(f'''<g opacity="0"><animate attributeName="opacity" values="{vals}" keyTimes="{kt}" dur="7.5s" calcMode="discrete" repeatCount="indefinite"/>
<rect x="{x + w / 2 - 40}" y="{y + 16}" width="80" height="74" fill="#4a4458" stroke="{c}" stroke-width="2"/>
<rect x="{x + w / 2 - 32}" y="{y + 26}" width="64" height="56" fill="{c}"/>
<text x="{x + w / 2}" y="{y + 60}" class="px" font-size="7" fill="#12051a" text-anchor="middle">{nm}</text>
<text x="{x + w / 2}" y="{y + h - 12}" class="px" font-size="8" fill="{c}" text-anchor="middle">CART {i + 1}/5</text></g>''')
    return ''.join(out)


# ---------------------------------------------------------------------------
# 4. FLOPPY DISK project cards
# ---------------------------------------------------------------------------
def floppy(slug, title, lines, tech, color, label_no):
    W, H = 420, 170
    body = f'''<defs>{glow_filter('fg', 3)}
<linearGradient id="fb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a2340"/><stop offset="1" stop-color="#15111f"/></linearGradient>
<linearGradient id="metal" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8d93a6"/><stop offset="0.5" stop-color="#e6e9f2"/><stop offset="1" stop-color="#7b8194"/></linearGradient></defs>
<rect x="4" y="4" width="{W - 8}" height="{H - 8}" rx="8" fill="url(#fb)" stroke="{color}" stroke-width="2"/>
<path d="M{W - 30} 4 L{W - 4} 30" stroke="#0a0710" stroke-width="10"/>
<!-- shutter -->
<rect x="24" y="4" width="92" height="46" fill="#0a0710"/>
<g><rect x="20" y="4" width="70" height="46" fill="url(#metal)"/><rect x="62" y="12" width="14" height="30" fill="#0a0710"/>
  <animateTransform attributeName="transform" type="translate" values="0 0;0 0;34 0;34 0;0 0" keyTimes="0;0.4;0.5;0.9;1" dur="5s" repeatCount="indefinite"/></g>
<!-- LED -->
<circle cx="{W - 26}" cy="{H - 22}" r="5" fill="{LIME}" filter="url(#fg)"><animate attributeName="opacity" values="1;0.15;1;0.15;1" keyTimes="0;0.1;0.2;0.3;1" dur="2.4s" repeatCount="indefinite"/></circle>
<!-- label -->
<rect x="130" y="14" width="{W - 150}" height="{H - 46}" rx="3" fill="#f4efe1"/>
<rect x="130" y="14" width="{W - 150}" height="10" fill="{color}"/>
<text x="140" y="44" class="px" font-size="11" fill="#12051a">{esc(title)}</text>
{''.join(f'<text x="140" y="{68 + i * 19}" class="vt" font-size="19" fill="#3a2f4a">{esc(l)}</text>' for i, l in enumerate(lines))}
<text x="22" y="{H - 40}" class="px" font-size="7" fill="#8c7a99">DISK {label_no}</text>
<text x="22" y="{H - 22}" class="vt" font-size="17" fill="{color}">{esc(tech)}</text>
<text x="{W - 40}" y="{H - 17}" class="vt" font-size="15" fill="#6b5b7a" text-anchor="end">READ &gt;</text>'''
    write(f'disk-{slug}.svg', svg(W, H, body, title=title))


# ---------------------------------------------------------------------------
# 5. FOOTER ticker
# ---------------------------------------------------------------------------
def footer():
    W, H = 900, 120
    msg = '* GRACIAS POR VISITAR  * INSERT COIN TO CONTINUE  * HECHO CON HTML · CSS · JS  * 0 FRAMEWORKS EN MIS JUEGOS  * BEST VIEWED AT 800×600  '
    tick = esc(msg * 2)
    body = f'''<defs><linearGradient id="fsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1d0836"/><stop offset="1" stop-color="#07020f"/></linearGradient>
{glow_filter('fg2', 2)}<clipPath id="fc"><rect width="{W}" height="{H}" rx="12"/></clipPath></defs>
<g clip-path="url(#fc)">
<rect width="{W}" height="{H}" fill="url(#fsky)"/>
{grid_floor(W, 70, H, 450, n_h=5, dur=1.4)}
<rect y="69" width="{W}" height="2" fill="{PINK}" filter="url(#fg2)"/>
<rect y="14" width="{W}" height="36" fill="#000" opacity="0.55"/>
<g><text y="40" class="vt" font-size="26" fill="{AMBER}">{tick}</text>
<animateTransform attributeName="transform" type="translate" values="0 0;-{len(msg) * 13} 0" dur="26s" repeatCount="indefinite"/></g>
<text x="{W / 2}" y="104" class="px" font-size="11" fill="#fff" text-anchor="middle" filter="url(#fg2)">GAME OVER? <tspan fill="{CYAN}">CONTINUE ▶ 9</tspan>
<animate attributeName="opacity" values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/></text>
</g>'''
    write('footer.svg', svg(W, H, body, title='Gracias por visitar'))


if __name__ == '__main__':
    print('Generando assets retro…')
    hero()
    for slug, label, color, icon in [
        ('about', 'SOBRE_MI', CYAN, '?'), ('arcade', 'ARCADE_STATION', AMBER, '▶'),
        ('projects', 'PROYECTOS', PINK, '#'), ('stack', 'STACK', VIOLET, '$'),
        ('stats', 'STATS', LIME, '▲'), ('contact', 'CONTACTO', CYAN, '@')]:
        header(slug, label, color, icon)
    cartridge('hub', 'ARCADE STATION', '5 JUEGOS · 1 PANTALLA', CYAN, dict(num='5in1', svg=scene_hub))
    cartridge('snake', 'PIXEL SNAKE', 'RETRO SLITHER · 1976', '#00f5d4', dict(num='#1', svg=scene_snake))
    cartridge('combat', 'PIXEL COMBAT', 'RYU VS KEN · 1984', '#ff334b', dict(num='#2', svg=scene_combat))
    cartridge('space', 'PIXEL SPACE', 'RETRO INVADERS · 1984', AMBER, dict(num='#3', svg=scene_space))
    cartridge('breaker', 'PIXEL BREAKER', 'RETRO ARKANOID · 1986', '#ff758f', dict(num='#4', svg=scene_breaker))
    cartridge('maze', 'PIXEL MAZE', 'PAC-CHASER · 1980', '#fee440', dict(num='#5', svg=scene_maze))
    floppy('lingopulse', 'LINGOPULSE', ['Inglés gamificado con mascota', '3D en tiempo real (A1–C2)'], 'Expo · React Native · Three.js', CYAN, 'A:')
    floppy('melodia', 'MELODIA AI', ['Clasifica instrumentos con', 'CNN + RNN sobre espectrogramas'], 'TensorFlow · Librosa · Web Audio', PINK, 'B:')
    floppy('neurotext', 'NEUROTEXT AI', ['Predicción de texto secuencial', 'API Flask + cliente web'], 'Keras · Flask · Tailwind', VIOLET, 'C:')
    floppy('gamevault', 'GAMEVAULT API', ['API REST + panel para tu', 'biblioteca de videojuegos'], 'Node · Express · Prisma · SQLite', AMBER, 'D:')
    floppy('timeseries', 'TIME SERIES', ['MLP vs LSTM vs Bi-LSTM en', 'series de tiempo climáticas'], 'Python · Keras · Jupyter', LIME, 'E:')
    floppy('threejs', 'THREE.JS LAB', ['12 talleres de gráficos 3D:', 'matrices, cámaras, poliedros'], 'Three.js · WebGL · Álgebra 3D', '#7df9ff', 'F:')
    footer()
    print('Listo.')
