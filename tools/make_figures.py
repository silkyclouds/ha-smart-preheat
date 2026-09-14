#!/usr/bin/env python3
"""Generate the documentation figures for ha-smart-preheat.

Dependency free: emits plain SVG. Run: python3 tools/make_figures.py
"""
import os, math

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(os.path.dirname(HERE), "docs")
os.makedirs(DOCS, exist_ok=True)

# --- palette: readable on both GitHub light and dark themes -----------------
BG      = "#fbf9f6"
PANEL   = "#f2ede6"
INK     = "#14181e"
MUTED   = "#6b7280"
LINE    = "#d8d0c5"
WARM    = "#c9531f"
ROOM    = "#eb6834"
OUT     = "#2a78d6"
BLUE_L  = "#86b6ef"
VIOLET  = "#4a3aa7"
GREEN   = "#2e7d5b"

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# --- room model (measured on the real room, see README) ---------------------
C_WH   = 380.0   # Wh per degree
UA     = 12.0    # W per degree of indoor/outdoor difference
P_RATED= 1120.0  # W actually delivered by the panel

def minutes_needed(delta, t_out, t_target, p=P_RATED, c=C_WH, ua=UA):
    net = max(p - ua * (t_target - t_out), 150.0)
    return 60.0 * delta * c / net

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def head(w, h, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">\n'
            f'<title>{esc(title)}</title>\n'
            f'<rect width="{w}" height="{h}" rx="14" fill="{BG}"/>\n')

def txt(x, y, s, size=13, fill=INK, anchor="start", weight="400", font=None, op=1.0):
    return (f'<text x="{x}" y="{y}" font-family="{font or FONT}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'opacity="{op}">{esc(s)}</text>\n')

def box(x, y, w, h, label, sub=None, fill="#ffffff", stroke=LINE, accent=None):
    o = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>\n'
    if accent:
        o += f'<rect x="{x}" y="{y}" width="4" height="{h}" rx="2" fill="{accent}"/>\n'
    cy = y + (h / 2 + 5 if not sub else h / 2 - 3)
    o += txt(x + w / 2, cy, label, 13.5, INK, "middle", "600")
    if sub:
        o += txt(x + w / 2, cy + 18, sub, 11.5, MUTED, "middle")
    return o

def arrow(x1, y1, x2, y2, color=MUTED, dash=None, width=1.6):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{width}" marker-end="url(#a)"{d}/>\n')

def defs():
    return ('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{MUTED}"/></marker></defs>\n')

# ===========================================================================
# 1. control loop
# ===========================================================================
def control_loop():
    W, H = 900, 420
    s = head(W, H, "Control loop") + defs()
    s += txt(32, 40, "How the loop works", 18, INK, "start", "700")
    s += txt(32, 62, "Three inputs, one decision, twice a day.", 12.5, MUTED)

    ys = 90
    s += box(32, ys, 254, 62, "Room sensor", "T_room  — Zigbee, in the room", accent=ROOM)
    s += box(322, ys, 254, 62, "Outdoor sensor + forecast", "T_out  — real probe, weather as backup", accent=OUT)
    s += box(612, ys, 256, 62, "Panel probe", "T_probe — the heater's own sensor", accent=VIOLET)

    for x in (159, 449, 740):
        s += arrow(x, ys + 62, 450 if x != 450 else 450, 186, MUTED)

    s += f'<rect x="32" y="190" width="836" height="96" rx="12" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>\n'
    s += txt(52, 216, "Home Assistant — runs every 5 minutes", 13.5, INK, "start", "700")
    s += txt(52, 244, "minutes = 60 × Δ°C × C / ( P − UA × (T_target − T_out) )", 14, WARM, "start", "600", MONO)
    s += txt(52, 268, "Open the preheat window exactly that many minutes before the target time.", 11.5, MUTED)

    s += arrow(240, 286, 240, 322)
    s += arrow(660, 286, 660, 322)
    s += box(70, 324, 340, 60, "Window open?", "then push a setpoint, else drop to eco", accent=GREEN)
    s += box(490, 324, 378, 60, "Setpoint = T_probe + gain × (T_want − T_room)",
             "the room sensor drives the panel, not its own probe", accent=WARM)

    s += txt(32, 408, "C = thermal mass (Wh/°C)   ·   UA = heat loss (W/°C)   ·   P = real delivered power (W)",
             11, MUTED)
    return s + "</svg>\n"

# ===========================================================================
# 2. energy balance
# ===========================================================================
def energy_balance():
    W, H = 900, 452
    s = head(W, H, "Energy balance") + defs()
    s += txt(32, 40, "Why the outdoor temperature changes everything", 18, INK, "start", "700")
    s += txt(32, 62, "Only the leftover power heats the room.", 12.5, MUTED)

    rx, ry, rw, rh = 210, 100, 300, 150
    s += f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" rx="12" fill="#ffffff" stroke="{LINE}" stroke-width="2"/>\n'
    s += txt(rx + rw / 2, ry + 62, "The room", 15, INK, "middle", "700")
    s += txt(rx + rw / 2, ry + 88, "C = 380 Wh/°C", 13, VIOLET, "middle", "600", MONO)
    s += txt(rx + rw / 2, ry + 110, "stores this much per degree", 11, MUTED, "middle")

    s += arrow(70, 150, rx - 6, 150, WARM, width=3)
    s += txt(74, 140, "P = 1120 W in", 12.5, WARM, "start", "600")
    s += arrow(rx + rw + 6, 205, 830, 205, OUT, width=3)
    s += txt(rx + rw + 12, 195, "UA × ΔT out", 12.5, OUT, "start", "600")
    s += txt(rx + rw + 12, 228, "UA = 12 W/°C", 11.5, MUTED, "start", "400", MONO)

    bx, by, bw, bh = 32, 286, 836, 140
    s += f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="12" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>\n'
    s += txt(bx + 20, by + 26, "Power just to hold 23 °C", 12.5, INK, "start", "700")
    cases = [(15, "15 °C"), (10, "10 °C"), (5, "5 °C"), (0, "0 °C"), (-5, "−5 °C"), (-10, "−10 °C")]
    for i, (t, lab) in enumerate(cases):
        p = UA * (23 - t)
        cx = bx + 172 + i * 104
        hh = 76 * (p / (UA * 33))
        s += f'<rect x="{cx}" y="{by + 108 - hh}" width="40" height="{hh}" rx="4" fill="{OUT}" opacity="0.85"/>\n'
        s += txt(cx + 20, by + 126, lab, 11, MUTED, "middle")
        s += txt(cx + 20, by + 100 - hh, f"{int(p)} W", 11.5, INK, "middle", "700")
    s += txt(bx + 20, by + 48, "for each outdoor", 11, MUTED)
    s += txt(bx + 20, by + 64, "temperature", 11, MUTED)
    s += txt(bx + 20, by + 92, "always far under", 11, GREEN, "start", "600")
    s += txt(bx + 20, by + 108, "the panel's 1120 W", 11, GREEN, "start", "600")
    return s + "</svg>\n"

# ===========================================================================
# 3. preheat simulation
# ===========================================================================
def preheat_simulation():
    W, H = 900, 440
    L, R, T, B = 78, 40, 96, 64
    pw, ph = W - L - R, H - T - B
    s = head(W, H, "Preheat simulation") + defs()
    s += txt(32, 40, "How early does it have to start?", 18, INK, "start", "700")
    s += txt(32, 62, "Minutes of preheating needed to reach 23 °C, for this room.", 12.5, MUTED)

    xmin, xmax = -10.0, 18.0
    ymin, ymax = 0.0, 150.0
    def X(v): return L + (v - xmin) / (xmax - xmin) * pw
    def Y(v): return T + ph - (v - ymin) / (ymax - ymin) * ph

    for g in range(0, 151, 30):
        s += f'<line x1="{L}" y1="{Y(g)}" x2="{L+pw}" y2="{Y(g)}" stroke="{LINE}" stroke-width="1"/>\n'
        s += txt(L - 12, Y(g) + 4, f"{g}", 11, MUTED, "end")
    for g in range(-10, 19, 4):
        s += txt(X(g), T + ph + 22, f"{g}°", 11, MUTED, "middle")
    s += txt(L - 12, T - 22, "minutes", 11.5, MUTED, "end")
    s += txt(L + pw, T + ph + 46, "outdoor temperature", 11.5, MUTED, "end")

    series = [(1.0, "Δ 1 °C", BLUE_L), (2.0, "Δ 2 °C", OUT), (3.0, "Δ 3 °C", VIOLET), (4.0, "Δ 4 °C", ROOM)]
    for delta, lab, col in series:
        pts = []
        t = xmin
        while t <= xmax + 0.001:
            pts.append(f"{X(t):.1f},{Y(min(minutes_needed(delta, t, 23.0), ymax)):.1f}")
            t += 0.5
        s += f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="2.6" stroke-linecap="round"/>\n'
        ylab = Y(min(minutes_needed(delta, xmin, 23.0), ymax))
        s += txt(X(xmin) + 8, ylab - 8, lab, 11.5, col, "start", "700")

    # annotate the measured morning
    s += f'<line x1="{X(17.5)}" y1="{T}" x2="{X(17.5)}" y2="{T+ph}" stroke="{GREEN}" stroke-width="1.4" stroke-dasharray="4 4"/>\n'
    s += txt(X(17.5) - 8, T + 16, "the measured night, 17.5 °C out", 11, GREEN, "end", "600")
    s += txt(32, H - 18, "Δ = degrees to gain. A cold night costs more minutes because the room leaks while it heats.", 11, MUTED)
    return s + "</svg>\n"

# ===========================================================================
# 4. measured night
# ===========================================================================
def measured_night():
    W, H = 900, 440
    L, R, T, B = 78, 78, 96, 70
    pw, ph = W - L - R, H - T - B
    s = head(W, H, "Measured night") + defs()
    s += txt(32, 40, "One real morning", 18, INK, "start", "700")
    s += txt(32, 62, "14 September 2026 — target 23 °C at 06:15, outside 17.5 °C.", 12.5, MUTED)

    xmin, xmax = 4.0, 8.0          # hours
    ymin, ymax = 19.5, 24.0
    def X(v): return L + (v - xmin) / (xmax - xmin) * pw
    def Y(v): return T + ph - (v - ymin) / (ymax - ymin) * ph

    # preheat window and shower zone
    s += f'<rect x="{X(5.32)}" y="{T}" width="{X(6.25)-X(5.32)}" height="{ph}" fill="{WARM}" opacity="0.08"/>\n'
    s += txt((X(5.32)+X(6.25))/2, T + 18, "preheat window", 11, WARM, "middle", "700")
    s += f'<rect x="{X(7.08)}" y="{T}" width="{X(7.20)-X(7.08)}" height="{ph}" fill="{OUT}" opacity="0.10"/>\n'
    s += txt(X(7.14), T + 18, "shower", 10.5, OUT, "middle", "700")

    g = 20.0
    while g <= ymax + 0.01:
        s += f'<line x1="{L}" y1="{Y(g)}" x2="{L+pw}" y2="{Y(g)}" stroke="{LINE}" stroke-width="1"/>\n'
        s += txt(L - 12, Y(g) + 4, f"{g:.0f}°", 11, MUTED, "end")
        g += 1.0
    for hh in range(4, 9):
        s += txt(X(hh), T + ph + 22, f"{hh:02d}:00", 11, MUTED, "middle")

    s += f'<line x1="{L}" y1="{Y(23)}" x2="{L+pw}" y2="{Y(23)}" stroke="{GREEN}" stroke-width="1.6" stroke-dasharray="5 5"/>\n'
    s += txt(L + 8, Y(23) - 9, "target 23 °C", 11, GREEN, "start", "700")

    # measured anchors (room sensor, 0.2 C quantisation)
    pts = [(4.0,21.9),(4.5,21.8),(5.0,21.7),(5.32,21.6),(5.6,22.0),(5.9,22.4),
           (6.1,22.7),(6.25,23.0),(6.6,23.0),(7.0,23.0),(7.08,23.0),(7.2,23.5),
           (7.5,23.3),(8.0,22.9)]
    poly = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in pts)
    s += f'<polyline points="{poly}" fill="none" stroke="{ROOM}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>\n'
    for a, b in pts:
        s += f'<circle cx="{X(a):.1f}" cy="{Y(b):.1f}" r="2.6" fill="{ROOM}"/>\n'

    s += f'<line x1="{L}" y1="{Y(17.5) if 17.5>ymin else T+ph}" x2="{L}" y2="{T+ph}" stroke="none"/>\n'
    s += txt(X(4.1), Y(21.9) - 14, "drifting down −0.15 °C/h all night", 11, MUTED, "start")
    s += txt(X(5.95), Y(22.4) + 22, "+2.3 °C/h measured", 11.5, WARM, "start", "700")
    s += txt(X(7.24), Y(21.9), "shower, not the panel", 11, OUT, "start", "600")
    s += txt(32, H - 20, "405 Wh were spent for the last +1.0 °C — that measurement is what gave C = 380 Wh/°C.", 11, MUTED)
    return s + "</svg>\n"

FIGS = {"control-loop.svg": control_loop, "energy-balance.svg": energy_balance,
        "preheat-simulation.svg": preheat_simulation, "measured-night.svg": measured_night}

if __name__ == "__main__":
    for name, fn in FIGS.items():
        p = os.path.join(DOCS, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", p)
