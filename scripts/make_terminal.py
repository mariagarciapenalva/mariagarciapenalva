#!/usr/bin/env python3
"""Generate an animated terminal SVG (typing effect) for a GitHub profile README.

Usage:  python make_terminal.py            -> writes assets/terminal.svg
Edit PALETTE and BLOCKS below. Everything else is plumbing.
"""
import html
import os
import textwrap
import base64
import re

# ---------- look ----------
PALETTE = dict(
    bg="#1b1426",       # window background
    bar="#2a1f3d",      # title bar
    prompt="#b57bff",   # maria@github:~$
    cmd="#f2eaff",      # typed commands
    key="#9d6bff",      # neofetch keys
    val="#d9c8ff",      # neofetch values / output text
    dots=("#ff5f57", "#febc2e", "#28c840"),
)
FONT = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
FS, CW, LH = 14, 8.4, 21     # font size, assumed char width (px), line height
PAD, TOP, COLS = 22, 48, 88  # side padding, space for title bar, wrap width
TYPE_SPEED = 0.05            # seconds per typed character
LINE_DELAY = 0.07            # seconds between output lines
PAUSE = 0.45                 # pause between blocks
BLOCK_GAP = 18
PROMPT = "maria@github:~$ "

# -----------pixel art--------
PIXEL_ART = "assets/pixel.svg"
PA_W = 250   #px
PA_GAP = 24  #px
PA_DY  = 20  #px, vertical shift

def load_pixel(path, width):
    """ returns (data_uri, width, height) for an svg file. and None if there is no art to fetch"""
    if not path or not os.path.exists(path):
        return None
    raw = open(path, "rb").read()
    txt = raw.decode("utf-8", "ignore")
    m = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', txt)
    if m:
        w0, h0 = float(m.group(1)), float(m.group(2))
    else:
        mw = re.search(r'<svg[^>]*?\swidth="([\d.]+)', txt)
        mh = re.search(r'<svg[^>]*?\sheight="([\d.]+)', txt)
        if not (mw and mh):
            raise SystemExit(f"{path}: needs a viewBox or width/height on the <svg> tag")
        w0, h0 = float(mw.group(1)), float(mh.group(1))
    uri = "data:image/svg+xml;base64," + base64.b64encode(raw).decode()
    return uri, width, width*h0/w0
            
       

# ---------- content ----------
# ("cmd", text)           typed command
# ("kv", [(key, value)])  neofetch-style table, key column aligned
# ("out", text)           wrapped paragraph
BLOCKS = [
    ("cmd", "neofetch"),
    ("kv", [
        ("maria@github", ""),
        ("────────────", ""),
        ("Focus", "Physics · HPC · Quantum Computing"),
        ("Stack", "C/C++ · CUDA · Python · Linux"),
        ("Events", "BSC MNHack26, MNHack25 · PUMPS+AI 26"),
        (" ", "ALBA Hackathon 2025 · CQA Quantum Summer School"),
        ("Pronouns", "She/Her · Any"),
        ("Status", "Available. Feel free to cd /reach-out!"),
        (" ", "I read every email :)"),
        ("────────────", "")
    ]),
    ("cmd", "pwd"),
    ("out", "You are /home! This is my personal repo, a safe space where I share what I'm up to: "
            "project proposals, personal projects and academic stuff. "
            "Welcome, there is no place like 127.0.0.1!"),
    ("cmd", "whoami"),
    ("out", "I am María, a Physics Undergraduate at UNED working at the intersection of "
            "physics, scientific computing, HPC and everything in between. "
            "Always open to suggestions and happy to learn new things."),
    ("cmd", "cat pronouns.txt"),
    ("out", "She/Her/Hers · Any pronouns. Share yours too if you'd like :)"),
]

# ---------- generator ----------
esc = html.escape
css, body = [], []
t = 0.4          # running timeline (s)
y = TOP
n_id = 0
pixel = load_pixel(PIXEL_ART, PA_W)
p_uri, p_w, p_h = pixel if pixel else (None, 0, 0)


def appear(el_id, at):
    css.append(f"#{el_id}{{opacity:0;animation:show .01s linear {at:.2f}s forwards}}")


def add_text(x, y, txt, color, el_id=None, extra=""):
    attrs = f'x="{x}" y="{y}" fill="{color}" {extra}'
    if el_id:
        attrs += f' id="{el_id}"'
    body.append(f"<text {attrs}>{esc(txt)}</text>")


for kind, data in BLOCKS:
    if kind == "cmd":
        n_id += 1
        p, c, r, k = f"p{n_id}", f"c{n_id}", f"r{n_id}", f"k{n_id}"
        x0 = PAD + len(PROMPT) * CW
        n = len(data)
        dur = n * TYPE_SPEED
        # prompt appears instantly
        add_text(PAD, y, PROMPT, PALETTE["prompt"], p, f'textLength="{len(PROMPT)*CW:.1f}" lengthAdjust="spacing"')
        appear(p, t)
        # command: clip rect grows in n discrete steps = typing
        body.append(f'<clipPath id="{c}"><rect id="{r}" x="{x0:.1f}" y="{y-FS}" width="0" height="{LH}"/></clipPath>')
        add_text(x0, y, data, PALETTE["cmd"], None,
                 f'clip-path="url(#{c})" textLength="{n*CW:.1f}" lengthAdjust="spacing"')
        css.append(f"@keyframes w{n_id}{{to{{width:{n*CW:.1f}px}}}}")
        css.append(f"@keyframes f{n_id}{{to{{width:{n*CW+6:.1f}px}}}}")
        css.append(f"#{r}{{animation:w{n_id} {dur:.2f}s steps({n},end) {t+0.15:.2f}s forwards,"
        f"f{n_id} .01s linear {t+0.15+dur:.2f}s forwards}}")
        # block cursor follows the text while typing, then disappears
        body.append(f'<rect id="{k}" x="{x0:.1f}" y="{y-FS+2}" width="{CW:.1f}" height="{FS}" fill="{PALETTE["cmd"]}"/>')
        css.append(f"@keyframes m{n_id}{{to{{transform:translateX({n*CW:.1f}px)}}}}")
        css.append(f"@keyframes v{n_id}{{from,to{{opacity:1}}}}")
        css.append(f"#{k}{{opacity:0;animation:m{n_id} {dur:.2f}s steps({n},end) {t+0.15:.2f}s forwards,"
                   f"v{n_id} {dur+0.35:.2f}s linear {t+0.15:.2f}s}}")
        t += 0.15 + dur + 0.35
        y += LH

    elif kind == "kv":
        keyw = max(len(k) for k, v in data if v) + 2
        #shift in the text to make room for pixel art
        x_key = PAD + (p_w + PA_GAP if pixel else 0)
        y_top, t_top = y, t
        for key, val in data:
            n_id += 1
            e = f"o{n_id}"
            body.append(f'<text id="{e}" x="{x_key}" y="{y}" xml:space="preserve">'
                        f'<tspan fill="{PALETTE["key"]}" font-weight="bold">{esc(key)}</tspan>'
                        f'<tspan x="{x_key + keyw*CW:.1f}" fill="{PALETTE["val"]}">{esc(val)}</tspan></text>')
            appear(e, t)
            t += LINE_DELAY
            y += LH
        if pixel:
            n_id += 1
            body.append(f'<image id="a{n_id}" href="{p_uri}" x="{PAD}" y = "{y_top - FS + PA_DY:.1f}" '
            f'width="{p_w}" height="{p_h:.1f}" style="image-rendering:pixelated"/>')
            appear(f"a{n_id}", t_top)
            y = max(y, y_top - FS + PA_DY + p_h + LH/2)
        t += PAUSE
        y += BLOCK_GAP

    elif kind == "out":
        for line in textwrap.wrap(data, COLS):
            n_id += 1
            e = f"o{n_id}"
            add_text(PAD, y, line, PALETTE["val"], e, 'xml:space="preserve"')
            appear(e, t)
            t += LINE_DELAY
            y += LH
        t += PAUSE
        y += BLOCK_GAP

# final idle prompt with blinking cursor
n_id += 1
add_text(PAD, y, PROMPT, PALETTE["prompt"], f"p{n_id}")
appear(f"p{n_id}", t)
body.append(f'<rect id="blink" x="{PAD + len(PROMPT)*CW:.1f}" y="{y-FS+2}" width="{CW:.1f}" height="{FS}" fill="{PALETTE["cmd"]}"/>')
css.append("@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}")
css.append(f"#blink{{opacity:0;animation:blink 1.1s steps(1) {t:.2f}s infinite}}")
y += LH + 10

W = int(PAD * 2 + COLS * CW)
H = int(y)
dots = "".join(f'<circle cx="{22+i*20}" cy="17" r="6" fill="{c}"/>' for i, c in enumerate(PALETTE["dots"]))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="ttl">
<title id="ttl">Terminal: neofetch, pwd, whoami and cat pronouns.txt for María García Penalva</title>
<style>
text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}
@keyframes show{{to{{opacity:1}}}}
{chr(10).join(css)}
</style>
<rect width="{W}" height="{H}" rx="10" fill="{PALETTE["bg"]}"/>
<path d="M0 10a10 10 0 0 1 10-10h{W-20}a10 10 0 0 1 10 10v24H0z" fill="{PALETTE["bar"]}"/>
{dots}
{chr(10).join(body)}
</svg>
'''

os.makedirs("assets", exist_ok=True)
with open("assets/terminal.svg", "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote assets/terminal.svg  ({W}x{H}px, animation ends at ~{t:.1f}s)")
