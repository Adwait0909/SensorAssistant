"""
circuit_engine/bridge.py
Maps project component names (from DB/JSON) to circuit-engine type keys,
builds a circuit, validates it, and renders schematic + breadboard SVGs.
"""
from .catalog import COMPONENTS
from .wiring import build
from .validator import validate
from .diagram import render

# ── Fuzzy mapping: project component name substrings → catalog keys ──────────
_NAME_MAP = [
    # MCUs
    ("esp32",           "esp32"),
    ("esp-32",          "esp32"),
    ("arduino uno",     "arduino_uno"),
    ("arduino",         "arduino_uno"),
    # Sensors
    ("hc-sr04",         "hc_sr04"),
    ("hc_sr04",         "hc_sr04"),
    ("ultrasonic",      "hc_sr04"),
    ("dht11",           "dht11"),
    ("dht22",           "dht11"),   # treat dht22 like dht11 (same wiring)
    ("dht",             "dht11"),
    ("temperature",     "dht11"),
    ("humidity",        "dht11"),
    ("pir",             "pir"),
    ("motion",          "pir"),
    ("ldr",             "ldr"),
    ("light sensor",    "ldr"),
    ("photoresistor",   "ldr"),
    ("mq-2",            "ldr"),     # gas sensors map to ADC like LDR
    ("mq-7",            "ldr"),
    ("mq-135",          "ldr"),
    ("mq",              "ldr"),
    ("gas sensor",      "ldr"),
    ("soil",            "ldr"),     # soil moisture → ADC
    ("moisture",        "ldr"),
    # Outputs
    ("led",             "led"),
    ("rgb led",         "rgb_led"),
    ("rgb",             "rgb_led"),
    ("buzzer",          "buzzer"),
    ("servo",           "servo"),
    ("dc motor",        "dc_motor"),
    ("motor",           "dc_motor"),
    ("relay",           "relay"),
    ("oled",            "oled"),
    ("lcd",             "lcd"),
    # Passives / Power
    ("potentiometer",   "potentiometer"),
    ("pot ",            "potentiometer"),
    ("push button",     "push_button"),
    ("button",          "push_button"),
    ("switch",          "push_button"),
    ("capacitor",       "capacitor"),
    ("battery",         "battery"),
    # Ignore these — they are structural, not circuit components
    ("breadboard",      None),
    ("jumper",          None),
    ("resistor",        None),
    ("wire",            None),
]


def _map_component(name: str) -> str | None:
    """Return a catalog key for a component name string, or None to skip."""
    low = name.lower().strip()
    for substr, key in _NAME_MAP:
        if substr in low:
            return key
    return None


def build_circuit_for_project(project) -> dict:
    """
    Given a Project ORM object (or any object with .name and .required_components),
    returns a dict with keys:
        name, valid, checks, svg_schematic, svg_breadboard, components_used, unknown_components
    """
    raw_components = project.required_components or []
    seen = set()
    comp_keys = []
    unknown = []

    for raw in raw_components:
        key = _map_component(raw)
        if key is None:
            continue                        # explicitly ignored (breadboard, jumper, etc.)
        if key == "":
            unknown.append(raw)
            continue
        if key not in seen:
            seen.add(key)
            comp_keys.append(key)

    if not comp_keys:
        # Fall back to a minimal sensible circuit
        comp_keys = ["arduino_uno", "led"]

    circuit = build(comp_keys)
    validation = validate(circuit)

    svg_schematic  = render(circuit, "schematic",  project.name)
    svg_breadboard = render(circuit, "breadboard", project.name)

    components_used = [COMPONENTS[k]["name"] for k in comp_keys if k in COMPONENTS]

    return {
        "name":              project.name,
        "valid":             validation["valid"],
        "checks":            validation["checks"],
        "svg_schematic":     svg_schematic,
        "svg_breadboard":    svg_breadboard,
        "components_used":   components_used,
        "unknown_components": unknown,
    }
