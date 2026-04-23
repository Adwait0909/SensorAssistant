import json

def load_warnings():
    with open("data/warnings.json") as f:
        return json.load(f)

def generate_warnings(user_components):
    warnings_data = load_warnings()
    output = []

    for w in warnings_data:
        condition = w["condition"]

        if "component" in condition:
            if condition["component"] in user_components:
                
                if "missing" in condition:
                    if condition["missing"] not in user_components:
                        output.append(w["warning"])

    return output