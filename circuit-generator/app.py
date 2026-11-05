import random
from flask import Flask, jsonify, render_template, request
from engine import db
from engine.catalog import COMPONENTS
from engine.examples import EXAMPLES
from engine.generator import generate_random, build_steps
from engine.validator import validate
from engine.wiring import build
from diagram import render

app = Flask(__name__)


def payload(circuit, name):
    return {"name": name, "circuit": circuit, "validation": validate(circuit),
            "svg": {v: render(circuit, v, name) for v in ("schematic", "breadboard")},
            "build_steps": build_steps(circuit)}


def finish(circuit, sel, name):
    data = payload(circuit, name)
    db.save(name, sel, data["validation"]["valid"])
    return jsonify(data)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/components")
def components():
    return jsonify({k: {"name": v["name"], "category": v["category"], "voltage": v["voltage"], "compatible": v["compatible"]} for k, v in COMPONENTS.items()})


@app.get("/api/examples")
def examples():
    return jsonify([{"key": k, **{x: v[x] for x in ("name", "desc")}} for k, v in EXAMPLES.items()])


@app.post("/api/random")
def api_random():
    circuit, sel = generate_random(random.Random())
    return finish(circuit, sel, "Random Circuit")


@app.post("/api/build")
def api_build():
    sel = [t for t in (request.get_json(silent=True) or {}).get("components", []) if t in COMPONENTS]
    if not sel:
        return jsonify({"error": "Select at least one component."}), 400
    return finish(build(sel), sel, "Custom Circuit")


@app.get("/api/example/<key>")
def api_example(key):
    if key not in EXAMPLES:
        return jsonify({"error": "unknown example"}), 404
    ex = EXAMPLES[key]
    return finish(build(ex["components"]), ex["components"], ex["name"])


@app.post("/api/validate")
def api_validate():
    circuit = (request.get_json(silent=True) or {}).get("circuit")
    if not circuit:
        return jsonify({"error": "No circuit supplied."}), 400
    return jsonify(validate(circuit))


@app.get("/api/history")
def history():
    return jsonify(db.recent())


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)   # 5000 is taken by AirPlay on macOS 12+
