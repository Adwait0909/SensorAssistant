import json

def load_components():
    with open("data/components.json") as f:
        return json.load(f)

def classify_components(components_list):
    data = load_components()
    known_names = {comp["name"] for comp in data}
    known = []
    unknown = []

    for component in components_list:
        if component in known_names:
            known.append(component)
        else:
            unknown.append(component)

    return known, unknown

def get_roles(components_list):
    data = load_components()
    roles = []
    known, _ = classify_components(components_list)

    for comp in data:
        if comp["name"] in known:
            roles.append(comp["role"])

    return roles