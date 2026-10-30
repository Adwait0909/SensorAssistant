import copy, os, random, tempfile, unittest
os.environ["CIRCUIT_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
from app import app
from diagram import render
from engine.examples import EXAMPLES
from engine.generator import generate_random
from engine.validator import validate
from engine.wiring import build


def errs(v, cat):
    return [m for c in v["checks"] if c["name"] == cat for m in c["messages"] if m["level"] == "error"]


class Engine(unittest.TestCase):
    def test_random_valid_and_renders(self):
        rng = random.Random(1)
        for _ in range(150):
            c, sel = generate_random(rng)
            self.assertTrue(validate(c)["valid"], sel)
            for view in ("schematic", "breadboard"):
                s = render(c, view, "t")
                self.assertTrue(s.startswith("<svg") and s.endswith("</svg>"))

    def test_examples(self):
        for k, ex in EXAMPLES.items():
            self.assertTrue(validate(build(ex["components"]))["valid"], k)

    def test_led_gets_resistor(self):
        c = build(["arduino_uno", "led"])
        self.assertIn("resistor", [i["type"] for i in c["instances"]])

    def test_missing_resistor(self):
        c = build(["arduino_uno", "led"])
        rid = {i["id"] for i in c["instances"] if i["type"] == "resistor"}
        c["connections"] = [x for x in c["connections"] if x["from"]["c"] not in rid and x["to"]["c"] not in rid]
        self.assertTrue(errs(validate(c), "Resistors"))

    def test_reversed_polarity(self):
        c = build(["arduino_uno", "led"])
        for x in c["connections"]:
            if x["from"]["p"] == "cathode":
                x["from"]["p"] = "anode"
        self.assertTrue(errs(validate(c), "Polarity"))

    def test_missing_gnd(self):
        c = build(["arduino_uno", "pir"])
        c["connections"] = [x for x in c["connections"] if x["kind"] != "gnd"]
        self.assertTrue(errs(validate(c), "Power / GND"))

    def test_duplicate_pin(self):
        c = build(["arduino_uno", "pir", "buzzer"])
        for a in c["assignments"]:
            a["mcu_pin"] = "D2"
        self.assertTrue(errs(validate(c), "Pin assignment"))

    def test_voltage_and_compat(self):
        c = build(["esp32", "servo"])           # servo needs 4.8-6 V, ESP32 only has 3.3 V
        v = validate(c)
        self.assertFalse(v["valid"])
        self.assertTrue(errs(v, "Voltage") and errs(v, "Compatibility"))

    def test_dependencies(self):
        types = [i["type"] for i in build(["arduino_uno", "dc_motor"])["instances"]]
        self.assertTrue({"relay", "battery"} <= set(types))

    def test_api(self):
        cl = app.test_client()
        d = cl.post("/api/random").get_json()
        self.assertTrue(d["validation"]["valid"] and "<svg" in d["svg"]["breadboard"])
        self.assertEqual(cl.post("/api/build", json={"components": []}).status_code, 400)
        self.assertTrue(cl.post("/api/validate", json={"circuit": d["circuit"]}).get_json()["valid"])
        self.assertEqual(cl.get("/api/example/servo").status_code, 200)
        self.assertTrue(cl.get("/api/history").get_json())


if __name__ == "__main__":
    unittest.main()
