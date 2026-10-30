import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENTS = json.loads((ROOT / "components.json").read_text(encoding="utf-8"))
RULES = json.loads((ROOT / "wiring_rules.json").read_text(encoding="utf-8"))["rules"]
MCUS = [k for k, v in COMPONENTS.items() if v["category"] == "mcu"]


def compatible(mcu, t):
    c = COMPONENTS[t]["compatible"]
    return t == mcu or "*" in c or mcu in c
