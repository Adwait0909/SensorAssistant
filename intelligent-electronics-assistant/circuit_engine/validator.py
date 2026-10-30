"""Circuit validation — checks compatibility, resistors, power/GND, polarity, voltage, pin conflicts."""
from .catalog import COMPONENTS as C, compatible

CATS = ["Compatibility", "Resistors", "Power / GND", "Polarity", "Voltage", "Pin assignment"]


def validate(c):
    inst = {i["id"]: i for i in c["instances"]}
    par = {}

    def f(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def key(e):
        return (e["c"], e["p"])

    for cn in c["connections"]:
        par[f(key(cn["from"]))] = f(key(cn["to"]))
    for i in c["instances"]:
        for a, b in C[i["type"]].get("internal", []):
            par[f((i["id"], a))] = f((i["id"], b))
    nets = {}
    for k in list(par):
        nets.setdefault(f(k), []).append(k)

    def net(i, p):
        return nets.get(f((i, p)), [])

    def sources(n):
        v, g = set(), False
        for i, p in n:
            t = inst[i]["type"]
            d = C[t]
            if d["category"] == "mcu":
                if p in d["pin_types"]["power"]:
                    v.add(d["pin_types"]["power"][p])
                g = g or p == d["pin_types"]["gnd"]
            elif t == "battery":
                if p == "+":
                    v.add(d["voltage"]["max"])
                g = g or p == "-"
        return v, g

    res = {k: [] for k in CATS}

    def add(cat, level, msg):
        res[cat].append({"level": level, "msg": msg})

    mcus = [i for i in c["instances"] if C[i["type"]]["category"] == "mcu"]
    if len(mcus) != 1:
        add("Compatibility", "error", f"Exactly one microcontroller is required (found {len(mcus)}).")
    mcu = inst[c["mcu"]]
    types = [i["type"] for i in c["instances"]]
    for i in c["instances"]:
        d = C[i["type"]]
        if not compatible(mcu["type"], i["type"]):
            add("Compatibility", "error", f"{i['id']} ({d['name']}) is not compatible with {mcu['name']}.")
        for r in d["requires"]:
            if r != "resistor" and r not in types:
                add("Compatibility", "error", f"{i['id']} requires a {C[r]['name']}.")
    conn_of = {}
    for cn in c["connections"]:
        for s, o in (("from", "to"), ("to", "from")):
            conn_of.setdefault(key(cn[s]), []).append(cn[o])

    for i in c["instances"]:
        d = C[i["type"]]
        if "resistor" in d["requires"] and not any(
            x["type"] == "resistor" and any(k[0] == x["id"] for k in conn_of)
            for x in c["instances"]
        ):
            add("Resistors", "error", f"{i['id']} requires a resistor but none is wired.")
        for p in d.get("series_resistor", []):
            if not any(inst[o["c"]]["type"] == "resistor" for o in conn_of.get((i["id"], p), [])):
                add("Resistors", "error", f"{i['id']}.{p} has no series current-limiting resistor.")
    for i in c["instances"]:
        d = C[i["type"]]
        if not any(k[0] == i["id"] for k in conn_of) and d["category"] != "board":
            add("Power / GND", "warning", f"{i['id']} ({d['name']}) is unused / not connected.")
            continue
        for p in d["power_pins"]:
            n = net(i["id"], p)
            if len(n) < 2 or not sources(n)[0]:
                add("Power / GND", "error", f"{i['id']}.{p} has no power supply connection.")
        for p in d["gnd_pins"]:
            n = net(i["id"], p)
            if len(n) < 2 or not sources(n)[1]:
                add("Power / GND", "error", f"{i['id']}.{p} is not connected to GND.")
    for i in c["instances"]:
        pol = C[i["type"]]["polarity"]
        if not pol:
            continue
        for p in pol["pos"]:
            if sources(net(i["id"], p))[1]:
                add("Polarity", "error", f"{i['id']}.{p} (+) is connected to GND - reversed polarity.")
        for p in pol["neg"]:
            if sources(net(i["id"], p))[0]:
                add("Polarity", "error", f"{i['id']}.{p} (-) is connected to a supply rail - reversed polarity.")
    for n in nets.values():
        v, _ = sources(n)
        if len(v) > 1:
            add("Voltage", "error", f"Short between supply rails {sorted(v)} V.")
        for i, p in n:
            d = C[inst[i]["type"]]
            chk = list(d["power_pins"]) + ([d["pin_types"]["vin"]] if d["category"] == "mcu" else [])
            if p in chk:
                for x in v:
                    if not d["voltage"]["min"] <= x <= d["voltage"]["max"]:
                        add("Voltage", "error",
                            f"{i}.{p} is rated {d['voltage']['min']}-{d['voltage']['max']} V but is supplied {x} V.")
    owners = {}
    for a in c["assignments"]:
        if not a["bus"]:
            owners.setdefault(a["mcu_pin"], []).append(f"{a['comp']}.{a['pin']}")
    for p, o in owners.items():
        if len(o) > 1:
            add("Pin assignment", "error", f"MCU pin {p} is assigned more than once: {', '.join(o)}.")
    for cn in c["connections"]:
        for e in (cn["from"], cn["to"]):
            if e["p"] not in C[inst[e["c"]]["type"]]["pins"]:
                add("Pin assignment", "error", f"{e['c']} has no pin '{e['p']}'.")
    checks = [
        {"name": k, "passed": not any(m["level"] == "error" for m in res[k]), "messages": res[k]}
        for k in CATS
    ]
    return {"valid": all(x["passed"] for x in checks), "checks": checks}
