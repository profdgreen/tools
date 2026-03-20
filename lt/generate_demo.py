#!/usr/bin/env python3
'''
Generate an animated SVG terminal demo for lt.
Vertical layout: tree (scrolling, clipped) on top, lt (fits cleanly) on bottom.
Run from the lt/ directory: python generate_demo.py
'''

import html
import subprocess
import re

# ── capture real terminal output ──
DEMO_DIR = '/tmp/lt_demo/my-project'

subprocess.run(['bash', '-c', f'''
mkdir -p {DEMO_DIR}/{{src,tests,docs,data}}
touch {DEMO_DIR}/{{README.md,setup.py,.gitignore,Makefile}}
touch {DEMO_DIR}/src/{{__init__.py,main.py,config.py,utils.py}}
touch {DEMO_DIR}/tests/{{__init__.py,test_main.py,test_utils.py}}
touch {DEMO_DIR}/docs/{{index.md,api.md,guide.md}}
for i in $(seq 1 40); do touch "{DEMO_DIR}/data/sample_$(printf '%03d' $i).csv"; done
'''], check=True)

raw_tree = subprocess.run(
    ['tree', '-L', '2', '--du', '-h', '-C', DEMO_DIR],
    capture_output=True, text=True
).stdout

raw_lt = subprocess.run(
    ['./lt', DEMO_DIR],
    capture_output=True, text=True
).stdout

# ── ANSI to SVG ──
ANSI_COLORS = {
    '0': None, '00': None,
    '2': '#666666',
    '01;34': '#5c9aff', '34': '#5c9aff',
}

def ansi_to_svg_spans(text):
    parts = re.split(r'\033\[([0-9;]*)m', text)
    result = []
    current_color = None
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part:
                escaped = html.escape(part)
                if current_color:
                    result.append(f'<tspan fill="{current_color}">{escaped}</tspan>')
                else:
                    result.append(escaped)
        else:
            current_color = ANSI_COLORS.get(part)
    return ''.join(result)

def visible_len(line):
    return len(re.sub(r'\033\[[0-9;]*m', '', line))


# ── process lines ──
display_tree = raw_tree.replace(DEMO_DIR, './my-project')
display_lt = raw_lt.replace(DEMO_DIR, './my-project')

tree_lines = display_tree.rstrip('\n').split('\n')
lt_lines = display_lt.rstrip('\n').split('\n')

# ── layout ──
font_size = 13
char_w = 7.8
line_h = 17
pad = 16
corner_r = 8
title_bar_h = 32

max_vis = max(
    max(visible_len(l) for l in tree_lines),
    max(visible_len(l) for l in lt_lines),
    45
)
panel_w = max_vis * char_w + pad * 2

# both panels same viewport height, sized to fit the lt output
lt_n = len(lt_lines) + 1  # +1 for prompt
lt_content_h = lt_n * line_h + pad * 2
# cap at a reasonable height so the SVG isn't huge
max_viewport_h = 24 * line_h + pad * 2
panel_viewport_h = min(lt_content_h, max_viewport_h)
panel_h = title_bar_h + panel_viewport_h

# tree content is taller than viewport — it will scroll
tree_n = len(tree_lines) + 1
tree_content_h = tree_n * line_h + pad
scroll_distance = max(tree_content_h - panel_viewport_h + pad, 0)

gap = 20
svg_pad = 20
total_w = panel_w + svg_pad * 2
total_h = svg_pad + panel_h + gap + panel_h + svg_pad

tree_px = svg_pad
tree_py = svg_pad
lt_px = svg_pad
lt_py = tree_py + panel_h + gap

# ── timing ──
tree_panel_fade = 0.0
tree_lines_start = 0.4
tree_lines_dur = 1.0
scroll_start = tree_lines_start + tree_lines_dur + 0.3
scroll_dur = 2.0
lt_panel_fade = scroll_start + scroll_dur + 0.5
lt_lines_start = lt_panel_fade + 0.3
lt_lines_dur = 1.2


def render_chrome(px, py, pw, ph, title, title_color, fade_delay):
    p = []
    p.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
             f'dur="0.3s" begin="{fade_delay}s" fill="freeze"/>')
    # background
    p.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" '
             f'rx="{corner_r}" fill="#0d1117" stroke="#30363d" stroke-width="1"/>')
    # title bar
    p.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{title_bar_h}" '
             f'rx="{corner_r}" fill="#1c2128"/>')
    p.append(f'<rect x="{px}" y="{py + title_bar_h - corner_r}" width="{pw}" '
             f'height="{corner_r}" fill="#1c2128"/>')
    p.append(f'<line x1="{px}" y1="{py + title_bar_h}" x2="{px + pw}" '
             f'y2="{py + title_bar_h}" stroke="#30363d" stroke-width="1"/>')
    # dots
    dx = px + 14
    dy = py + title_bar_h / 2
    for c in ['#ff5f57', '#febc2e', '#28c840']:
        p.append(f'<circle cx="{dx}" cy="{dy}" r="5" fill="{c}"/>')
        dx += 20
    # title
    p.append(f'<text x="{px + pw/2}" y="{py + title_bar_h/2 + 4}" '
             f'class="t" fill="{title_color}" text-anchor="middle" '
             f'font-weight="bold" font-size="12">{html.escape(title)}</text>')
    p.append('</g>')
    return '\n'.join(p)


def render_lines_svg(lines, cmd, cx, cy, start, dur):
    p = []
    items = []
    # prompt
    items.append(
        f'<text x="{cx}" y="{cy}" class="t" fill="#7ee787">$ </text>'
        f'<text x="{cx + char_w * 2}" y="{cy}" class="t" fill="#e6edf3">'
        f'{html.escape(cmd)}</text>'
    )
    for i, line in enumerate(lines):
        ly = cy + (i + 1) * line_h
        content = ansi_to_svg_spans(line)
        items.append(
            f'<text x="{cx}" y="{ly}" class="t" fill="#c9d1d9" '
            f'xml:space="preserve">{content}</text>'
        )
    for i, item in enumerate(items):
        delay = start + (i / max(len(items), 1)) * dur
        p.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
                 f'dur="0.05s" begin="{delay:.3f}s" fill="freeze"/>{item}</g>')
    return '\n'.join(p)


svg = []
svg.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w:.0f} {total_h:.0f}"
     width="{total_w:.0f}" height="{total_h:.0f}">
<defs>
  <clipPath id="tc"><rect x="{tree_px}" y="{tree_py + title_bar_h}"
    width="{panel_w}" height="{panel_viewport_h}"/></clipPath>
  <linearGradient id="fb" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#0d1117" stop-opacity="0"/>
    <stop offset="100%" stop-color="#0d1117" stop-opacity="1"/>
  </linearGradient>
</defs>
<style>.t {{ font-family: 'JetBrains Mono','Fira Code','SF Mono','Cascadia Code',Menlo,Consolas,monospace; font-size: {font_size}px; }}</style>
<rect width="100%" height="100%" rx="10" fill="#161b22"/>
''')

# ── tree panel chrome ──
svg.append(render_chrome(tree_px, tree_py, panel_w, panel_h, 'tree', '#ff6b6b', tree_panel_fade))

# ── tree content (clipped + scrolling) ──
tree_cx = tree_px + pad
tree_cy = tree_py + title_bar_h + pad + font_size

svg.append(f'<g clip-path="url(#tc)">')
svg.append(f'<g>')
if scroll_distance > 0:
    svg.append(f'  <animateTransform attributeName="transform" type="translate" '
               f'from="0 0" to="0 -{scroll_distance:.0f}" '
               f'begin="{scroll_start}s" dur="{scroll_dur}s" fill="freeze"/>')
svg.append(render_lines_svg(tree_lines, 'tree -L 2 --du -h ./my-project',
                             tree_cx, tree_cy, tree_lines_start, tree_lines_dur))
svg.append('</g></g>')

# fade gradient at bottom of tree panel
fade_y = tree_py + panel_h - 50
svg.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
           f'dur="0.3s" begin="{tree_panel_fade}s" fill="freeze"/>'
           f'<rect x="{tree_px + 1}" y="{fade_y}" width="{panel_w - 2}" height="50" '
           f'fill="url(#fb)"/></g>')

# ── lt panel chrome ──
svg.append(render_chrome(lt_px, lt_py, panel_w, panel_h, 'lt', '#51cf66', lt_panel_fade))

# ── lt content ──
lt_cx = lt_px + pad
lt_cy = lt_py + title_bar_h + pad + font_size

svg.append(render_lines_svg(lt_lines, 'lt ./my-project',
                             lt_cx, lt_cy, lt_lines_start, lt_lines_dur))

svg.append('</svg>\n')

svg_content = '\n'.join(svg)
with open('demo.svg', 'w') as f:
    f.write(svg_content)

print(f'Generated demo.svg ({total_w:.0f} x {total_h:.0f})')
print(f'  tree: {len(tree_lines)} lines, scroll: {scroll_distance:.0f}px')
print(f'  lt:   {len(lt_lines)} lines (fits in viewport)')

subprocess.run(['rm', '-rf', '/tmp/lt_demo'])
