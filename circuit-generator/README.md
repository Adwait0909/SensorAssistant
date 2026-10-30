# CircuitForge – Circuit Diagram Generator

Flask + SQLite + SVG. Circuits are generated from `components.json` (pins, voltage, category, polarity, requirements, compatibility)
and `wiring_rules.json` (pin → target rules). No pre-made images.

## Run on macOS 12.7.6 (Intel)
```bash
# 1. Python 3.11 (skip if `python3.11 --version` works)
brew install python@3.11            # or use the installer from python.org
# 2. Setup
cd circuit-generator
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# 3. Test + run
python -m unittest discover -s tests -t .
python app.py
```
Open **http://127.0.0.1:5001** (port 5000 is used by AirPlay Receiver on macOS 12+).

## Structure
- `engine/wiring.py` dependency resolution, pin assignment, connection generation
- `engine/validator.py` resistor / power-GND / polarity / voltage / duplicate-pin / compatibility checks (net-based)
- `engine/generator.py` random 3–7 component selection (retries until valid)
- `diagram/svg.py` schematic and breadboard SVG renderer
- `app.py` REST API + SQLite history (`instance/circuits.db`)

## Adding a component
Add an entry to `components.json` and pin rules to `wiring_rules.json`. That's all.
