"""Turns a list of component types into a full circuit: dependencies, pins, connections."""
from .catalog import COMPONENTS as C, RULES, MCUS


def resolve(types):
    out = [t for t in types if t in C]
    if not any(t in MCUS for t in out):
        out.insert(0, "arduino_uno")
    i = 0
    while i < len(out):
        for r in C[out[i]]["requires"]:
            if r != "resistor" and r not in out:
                out.append(r)
        i += 1
    if "breadboard" not in out:
        out.append("breadboard")
    return out


def build(selection):
    types = resolve(selection)
    insts, conns, assigns, used, counts = [], [], [], set(), {}

    def new(t, value=None):
        counts[t] = counts.get(t, 0) + 1
        insts.append({"id": f"{C[t]['ref']}{counts[t]}", "type": t, "name": C[t]["name"], "value": value})
        return insts[-1]

    for t in types:
        new(t)
    mcu = next(i for i in insts if C[i["type"]]["category"] == "mcu")
    pt = C[mcu["type"]]["pin_types"]

    def link(a, ap, b, bp, kind):
        conns.append({"from": {"c": a["id"], "p": ap}, "to": {"c": b["id"], "p": bp}, "kind": kind})

    def rail(t):
        v, opts = C[t]["voltage"], pt["power"]
        ok = [p for p, x in opts.items() if v["min"] <= x <= v["max"]] or list(opts)
        return max(ok, key=lambda p: opts[p])

    def take(value):
        for r in insts:
            if r["type"] == "resistor" and not r["value"]:
                r["value"] = value
                return r
        return new("resistor", value)

    def alloc(kind, inst, pin):
        if kind in ("SDA", "SCL"):
            p = pt[kind.lower()]
            bus = True
        else:
            cands = pt[{"DIG": "dig", "PWM": "pwm", "ADC": "adc"}[kind]]
            p = next((x for x in cands if x not in used), cands[0])
            bus = False
        used.add(p)
        assigns.append({"mcu_pin": p, "comp": inst["id"], "pin": pin, "bus": bus})
        return p

    for inst in list(insts):
        t = inst["type"]
        for r in RULES.get(t, []):
            p, to = r["pin"], r["to"]
            if to == "VCC":
                link(inst, p, mcu, rail(t), "power")
            elif to == "VIN":
                link(inst, p, mcu, pt["vin"], "power")
            elif to == "GND":
                link(inst, p, mcu, pt["gnd"], "gnd")
            elif to.startswith("COMP:"):
                ty, pp = to[5:].split(".")
                tgt = next((i for i in insts if i["type"] == ty), None)
                if tgt:
                    link(inst, p, tgt, pp, "wire")
            else:
                mp = alloc(to, inst, p)
                if "series" in r:
                    res = take(r["series"])
                    link(inst, p, res, "a", "wire")
                    link(res, "b", mcu, mp, "signal")
                else:
                    link(inst, p, mcu, mp, "signal")
                if "pull" in r:
                    side, val = r["pull"].split(":")
                    res = take(val)
                    link(res, "a", mcu, mp, "signal")
                    if side == "GND":
                        link(res, "b", mcu, pt["gnd"], "gnd")
                    else:
                        link(res, "b", mcu, rail(t), "power")
    return {"instances": insts, "connections": conns, "assignments": assigns, "mcu": mcu["id"]}
