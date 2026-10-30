"""Dynamic SVG generation (schematic + breadboard) from a circuit dict. No static images."""
from xml.sax.saxutils import escape as esc
from engine.catalog import COMPONENTS as C

PAL = ["#22d3ee", "#60a5fa", "#a78bfa", "#34d399", "#fbbf24", "#f472b6", "#fb923c", "#2dd4bf"]
RED, BLUE, INK = "#f87171", "#94a3b8", "#67e8f9"
ROW, PW = 20, 170


def render(circuit, view="schematic", title=""):
    return (_breadboard if view == "breadboard" else _schematic)(circuit, title)


def _wrap(w, h, body, title, sub):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="Helvetica,Arial,sans-serif">'
            '<defs><pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" stroke="#16202b" stroke-width="1"/></pattern></defs>'
            '<rect width="100%" height="100%" fill="#0b1016"/><rect width="100%" height="100%" fill="url(#g)"/>'
            f'<text x="20" y="24" fill="#e2e8f0" font-size="15" font-weight="700">{esc(title or "Circuit")}</text>'
            f'<text x="20" y="40" fill="#64748b" font-size="10">{esc(sub)}</text>{body}</svg>')


def _used_mcu_pins(c, mcu):
    ends = {(cn[s]["c"], cn[s]["p"]) for cn in c["connections"] for s in ("from", "to")}
    return [p for p in C[mcu["type"]]["pins"] if (mcu["id"], p) in ends]


def _depths(c):
    adj = {}
    for cn in c["connections"]:
        if cn["kind"] in ("power", "gnd"):
            continue
        a, b = cn["from"]["c"], cn["to"]["c"]
        adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    d, q = {c["mcu"]: 0}, [c["mcu"]]
    while q:
        x = q.pop(0)
        for y in adj.get(x, ()):
            if y not in d:
                d[y] = d[x] + 1; q.append(y)
    return d


def _sym(t, x, y):
    s = f'stroke="{INK}" stroke-width="1.6" fill="none" stroke-linejoin="round"'
    if t in ("resistor", "potentiometer", "ldr"):
        pts = [(-24, 0), (-16, 0), (-12, -7), (-4, 7), (4, -7), (12, 7), (16, 0), (24, 0)]
        o = f'<polyline {s} points="{" ".join(f"{x+a},{y+b}" for a, b in pts)}"/>'
        if t == "potentiometer":
            o += f'<path {s} d="M{x},{y-18} L{x},{y-8} M{x-3},{y-11} L{x},{y-8} L{x+3},{y-11}"/>'
        if t == "ldr":
            o += f'<path {s} d="M{x-16},{y-16} l8,6 M{x-8},{y-18} l8,6"/>'
        return o
    if t in ("led", "rgb_led"):
        return (f'<path {s} d="M{x-20},{y} h12 M{x-8},{y-9} v18 l16,-9 z M{x+8},{y-9} v18 M{x+8},{y} h12"/>'
                f'<path {s} d="M{x-2},{y-12} l6,-6 M{x+4},{y-12} l6,-6"/>')
    if t == "capacitor":
        return f'<path {s} d="M{x-20},{y} h16 M{x-4},{y-10} v20 M{x+4},{y-10} v20 M{x+4},{y} h16"/>'
    if t == "battery":
        return f'<path {s} d="M{x-20},{y} h14 M{x-6},{y-10} v20 M{x+1},{y-5} v10 M{x+8},{y-10} v20 M{x+15},{y-5} v10 M{x+15},{y} h5"/>'
    if t == "push_button":
        return f'<path {s} d="M{x-20},{y} h10 M{x+10},{y} h10 M{x-10},{y-6} L{x+9},{y-12} M{x},{y-16} v6"/>'
    if t == "dc_motor":
        return f'<circle {s} cx="{x}" cy="{y}" r="13"/><text x="{x}" y="{y+5}" fill="{INK}" font-size="14" text-anchor="middle">M</text>'
    return (f'<rect {s} x="{x-22}" y="{y-11}" width="44" height="22" rx="4"/>'
            f'<text x="{x}" y="{y+4}" fill="{INK}" font-size="11" text-anchor="middle">{esc(C[t]["ref"])}</text>')


def _stub(x, y, dr, label, kind):
    x2, col = x + dr * 18, (RED if kind == "power" else BLUE)
    s = f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y}" stroke="{col}" stroke-width="2"/>'
    if kind == "gnd":
        for k, h in enumerate((8, 5, 2)):
            xx = x2 + dr * 4 * k
            s += f'<line x1="{xx}" y1="{y-h}" x2="{xx}" y2="{y+h}" stroke="{col}" stroke-width="2"/>'
    else:
        s += (f'<circle cx="{x2}" cy="{y}" r="3" fill="{col}"/><text x="{x2+dr*6}" y="{y+3}" fill="{col}" font-size="9" '
              f'font-weight="700" text-anchor="{"start" if dr > 0 else "end"}">{esc(label)}</text>')
    return s


def _schematic(c, title):
    insts = [i for i in c["instances"] if i["type"] != "breadboard"]
    mcu = next(i for i in insts if i["id"] == c["mcu"])
    conns, d, pos = c["connections"], _depths(c), {}
    used = _used_mcu_pins(c, mcu)
    mh = 50 + ROW * max(len(used), 1)
    body = (f'<rect x="40" y="60" width="{PW}" height="{mh}" rx="10" fill="#0f1b26" stroke="#3b82f6" stroke-width="2"/>'
            f'<text x="{40+PW/2}" y="80" fill="#e2e8f0" font-size="12" font-weight="700" text-anchor="middle">{esc(mcu["id"])} · {esc(mcu["name"])}</text>')
    for k, p in enumerate(used):
        y = 104 + k * ROW
        pos[(mcu["id"], p)] = (40 + PW, y, 1)
        body += f'<text x="{40+PW-8}" y="{y+3}" fill="#93c5fd" font-size="10" text-anchor="end">{esc(p)}</text>'
    cols = {}
    for i in insts:
        if i is not mcu:
            cols.setdefault(max(1, d.get(i["id"], 1)), []).append(i)
    boxes, bottom = "", 60 + mh
    for dep, items in sorted(cols.items()):
        x, y = 300 + (dep - 1) * 270, 60
        for i in items:
            side = {p: -1 for p in C[i["type"]]["pins"]}
            for cn in conns:
                if cn["kind"] in ("power", "gnd"):
                    continue
                for a, b in ((cn["from"], cn["to"]), (cn["to"], cn["from"])):
                    if a["c"] == i["id"] and d.get(b["c"], 1) > dep:
                        side[a["p"]] = 1
            L = [p for p, s in side.items() if s < 0]; R = [p for p, s in side.items() if s > 0]
            h = 52 + ROW * max(len(L), len(R), 1)
            val = f' {esc(i["value"])}' if i.get("value") else ""
            boxes += (f'<rect x="{x}" y="{y}" width="{PW}" height="{h}" rx="10" fill="#111a24" stroke="#22d3ee" stroke-opacity=".7" stroke-width="1.5"/>'
                      f'<text x="{x+PW/2}" y="{y+17}" fill="#e2e8f0" font-size="11" font-weight="700" text-anchor="middle">{esc(i["id"])} · {esc(i["name"])}{val}</text>'
                      + _sym(i["type"], x + PW / 2, y + h / 2 + 8))
            for lst, sx in ((L, x), (R, x + PW)):
                for k, p in enumerate(lst):
                    py = y + 38 + k * ROW
                    pos[(i["id"], p)] = (sx, py, -1 if sx == x else 1)
                    boxes += (f'<circle cx="{sx}" cy="{py}" r="3.5" fill="#0b1016" stroke="#22d3ee" stroke-width="1.5"/>'
                              f'<text x="{sx + (7 if sx == x else -7)}" y="{py+3}" fill="#94a3b8" font-size="9" text-anchor="{"start" if sx == x else "end"}">{esc(p)}</text>')
            y += h + 24
        bottom = max(bottom, y)
    wires, stubbed, k = "", set(), 0
    for cn in conns:
        a, b = cn["from"], cn["to"]
        if cn["kind"] in ("power", "gnd"):
            for e, o in ((a, b), (b, a)):
                if (e["c"], e["p"]) in pos and (e["c"], e["p"]) not in stubbed:
                    stubbed.add((e["c"], e["p"]))
                    lab = o["p"] if inst_is(c, o["c"]) else e["p"]
                    x, y, dr = pos[(e["c"], e["p"])]
                    wires += _stub(x, y, dr, lab, cn["kind"])
            continue
        p1, p2 = pos[(a["c"], a["p"])], pos[(b["c"], b["p"])]
        x1, y1, d1 = p1; x2, y2, d2 = p2
        m, n = x1 + d1 * 16, x2 + d2 * 16
        xc = (m + n) / 2 + ((k % 7) - 3) * 5
        wires += (f'<path d="M{x1},{y1} L{m},{y1} L{xc},{y1} L{xc},{y2} L{n},{y2} L{x2},{y2}" fill="none" stroke="{PAL[k % len(PAL)]}" stroke-width="1.8" stroke-linejoin="round"/>'
                  f'<circle cx="{x1}" cy="{y1}" r="2.5" fill="{PAL[k % len(PAL)]}"/><circle cx="{x2}" cy="{y2}" r="2.5" fill="{PAL[k % len(PAL)]}"/>')
        k += 1
    w = 300 + (max(cols) if cols else 1) * 270
    return _wrap(w, bottom + 30, wires + boxes + body, title, "Schematic view · generated from components.json + wiring_rules.json")


def inst_is(c, cid):
    return cid == c["mcu"]


def _breadboard(c, title):
    insts = [i for i in c["instances"] if i["type"] != "breadboard"]
    mcu = next(i for i in insts if i["id"] == c["mcu"])
    others = [i for i in insts if i is not mcu]
    used = _used_mcu_pins(c, mcu)
    W = max(900, 90 + len(others) * 130)
    step = min(34, (W - 140) / max(len(used), 1))
    pos, body = {}, ""
    mw = 60 + len(used) * step
    body += (f'<rect x="40" y="50" width="{mw}" height="100" rx="10" fill="#0f1b26" stroke="#3b82f6" stroke-width="2"/>'
             f'<text x="52" y="72" fill="#e2e8f0" font-size="12" font-weight="700">{esc(mcu["id"])} · {esc(mcu["name"])}</text>')
    for k, p in enumerate(used):
        x = 70 + k * step; pos[(mcu["id"], p)] = (x, 150)
        body += (f'<circle cx="{x}" cy="150" r="4" fill="#3b82f6"/><text transform="rotate(-90 {x+3} 142)" x="{x+3}" y="142" fill="#93c5fd" font-size="9">{esc(p)}</text>')
    rails = {}
    for cn in c["connections"]:
        if cn["kind"] in ("power", "gnd"):
            m = cn["from"] if cn["from"]["c"] == mcu["id"] else cn["to"]
            rails.setdefault(m["p"], 200 + 14 * len(rails))
    body = (f'<rect x="30" y="190" width="{W-60}" height="240" rx="12" fill="#1a2330" stroke="#334155"/>') + body
    for p, y in rails.items():
        col = BLUE if p == C[mcu["type"]]["pin_types"]["gnd"] else RED
        body += (f'<line x1="44" y1="{y}" x2="{W-44}" y2="{y}" stroke="{col}" stroke-width="3" stroke-opacity=".8"/>'
                 f'<text x="{W-46}" y="{y-3}" fill="{col}" font-size="9" text-anchor="end">{esc(p)} rail</text>')
        x = pos[(mcu["id"], p)][0]
        body += f'<line x1="{x}" y1="150" x2="{x}" y2="{y}" stroke="{col}" stroke-width="2.5"/><circle cx="{x}" cy="{y}" r="3.5" fill="{col}"/>'
    for j, i in enumerate(others):
        x0, pins = 50 + j * 130, C[i["type"]]["pins"]
        val = f' {esc(i["value"])}' if i.get("value") else ""
        body += (f'<rect x="{x0}" y="320" width="112" height="70" rx="8" fill="#111a24" stroke="#22d3ee" stroke-opacity=".7"/>'
                 f'<text x="{x0+56}" y="360" fill="#e2e8f0" font-size="10" font-weight="700" text-anchor="middle">{esc(i["id"])}{val}</text>'
                 f'<text x="{x0+56}" y="374" fill="#64748b" font-size="8" text-anchor="middle">{esc(i["name"])}</text>')
        for k, p in enumerate(pins):
            px = x0 + (k + 1) * 112 / (len(pins) + 1); pos[(i["id"], p)] = (px, 320)
            body += (f'<circle cx="{px}" cy="320" r="3.5" fill="#0b1016" stroke="#22d3ee" stroke-width="1.5"/>'
                     f'<text x="{px}" y="336" fill="#94a3b8" font-size="8" text-anchor="middle">{esc(p)}</text>')
    k = 0
    for cn in c["connections"]:
        a, b = cn["from"], cn["to"]
        if cn["kind"] in ("power", "gnd"):
            comp, m = (a, b) if b["c"] == mcu["id"] else (b, a)
            if comp["c"] == mcu["id"]:
                continue
            x, y = pos[(comp["c"], comp["p"])]
            col = BLUE if cn["kind"] == "gnd" else RED
            body += f'<line x1="{x}" y1="320" x2="{x}" y2="{rails[m["p"]]}" stroke="{col}" stroke-width="2.2"/><circle cx="{x}" cy="{rails[m["p"]]}" r="3" fill="{col}"/>'
            continue
        (x1, y1), (x2, y2) = pos[(a["c"], a["p"])], pos[(b["c"], b["p"])]
        ym = (y1 + y2) / 2 if y1 != y2 else y1 - 45 - (k % 4) * 8
        col = PAL[k % len(PAL)]
        body += f'<path d="M{x1},{y1} C{x1},{ym} {x2},{ym} {x2},{y2}" fill="none" stroke="{col}" stroke-width="2.2"/>'
        k += 1
    return _wrap(W, 450, body, title, "Breadboard view · red = power, blue = GND, colours = signal jumpers")
