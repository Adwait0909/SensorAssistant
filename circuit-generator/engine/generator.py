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
