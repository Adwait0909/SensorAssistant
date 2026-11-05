import random
from .catalog import COMPONENTS as C, MCUS, compatible
from .wiring import build
from .validator import validate

SKIP = {"resistor", "breadboard"}   # added automatically by the wiring engine


def random_selection(rng, n=None):
    n = n or rng.randint(3, 7)
    mcu = rng.choice(MCUS)
    pool = [t for t, d in C.items() if d["category"] != "mcu" and t not in SKIP and compatible(mcu, t)]
    return [mcu] + rng.sample(pool, min(n - 1, len(pool)))


def generate_random(rng=None):
    rng = rng or random.Random()
    for _ in range(200):
        sel = random_selection(rng)
        circ = build(sel)
        if validate(circ)["valid"]:
            return circ, sel
    raise RuntimeError("could not generate a valid circuit")


def build_steps(circuit):
    """Turn generated connections into a short, beginner-friendly build guide."""
    instances = {item["id"]: item for item in circuit["instances"]}

    def component_name(component_id):
        item = instances[component_id]
        value = f" ({item['value']})" if item.get("value") else ""
        return f"{component_id} {item['name']}{value}"

    def connection_text(connection):
        source = f"{component_name(connection['from']['c'])} — {connection['from']['p']}"
        target = f"{component_name(connection['to']['c'])} — {connection['to']['p']}"
        return {
            "from": source,
            "to": target,
            "kind": connection["kind"],
            "instruction": f"Connect {source} to {target}.",
        }

    power = [c for c in circuit["connections"] if c["kind"] in ("power", "gnd")]
    signals = [c for c in circuit["connections"] if c["kind"] in ("signal", "wire")]
    steps = [
        {
            "step_number": 1,
            "title": "Place and identify the components",
            "components": [component_name(item["id"]) for item in circuit["instances"]],
            "connections": [],
            "how_to_connect": "Place the microcontroller and breadboard first. Then place each sensor, output, and required resistor so the pin labels remain visible.",
            "expected_output": "All components are positioned and their power, ground, and signal pins are identified.",
            "warnings": ["Keep the power disconnected while placing or moving wires."],
        },
        {
            "step_number": 2,
            "title": "Connect power and common ground",
            "components": sorted({x for c in power for x in (component_name(c["from"]["c"]), component_name(c["to"]["c"]))}),
            "connections": [connection_text(c) for c in power],
            "how_to_connect": "Make the power connections first, then connect every ground pin to the controller ground. Use the connection list below as the exact reference.",
            "expected_output": "Every powered component has the correct supply and all ground pins share a common reference.",
            "warnings": ["Check the voltage shown for each component before switching on the supply."],
        },
        {
            "step_number": 3,
            "title": "Connect sensor and output signals",
            "components": sorted({x for c in signals for x in (component_name(c["from"]["c"]), component_name(c["to"]["c"]))}),
            "connections": [connection_text(c) for c in signals],
            "how_to_connect": "Connect each signal exactly as listed. Resistors and other protective parts must stay in series where shown.",
            "expected_output": "The controller can read the sensors and control the selected outputs.",
            "warnings": ["Never bypass a resistor or connect a motor directly to a controller pin."],
        },
        {
            "step_number": 4,
            "title": "Inspect and test",
            "components": [component_name(circuit["instances"][0]["id"])] if circuit["instances"] else [],
            "connections": [],
            "how_to_connect": "Inspect every wire against the connection table. Power the circuit, upload a small test program, and test one sensor or output at a time.",
            "expected_output": "The circuit powers without excess heat and each connected function responds to its test.",
            "warnings": ["Disconnect power immediately if a component becomes hot, smells unusual, or behaves unexpectedly."],
        },
    ]
    return steps
