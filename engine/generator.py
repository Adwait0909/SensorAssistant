import json

def load_rules():
    with open("data/rules.json") as f:
        return json.load(f)

def load_components():
    with open("data/components.json") as f:
        return json.load(f)

def _component_lookup():
    return {item["name"]: item for item in load_components()}

def _sensor_prefix(component_name):
    base = component_name.split("(")[0].strip()
    replacements = [
        " Sensor",
        " Module",
        " Detector",
        " Reader",
        " Clock",
    ]
    for token in replacements:
        base = base.replace(token, "")
    return base.strip() or "Smart"

def _primary_sensor_name(user_components, comp_map):
    for name in user_components:
        comp = comp_map.get(name)
        if comp and comp.get("role") == "input":
            return _sensor_prefix(name)
    return "Smart"

def _has_role(user_components, comp_map, role):
    return any(comp_map.get(name, {}).get("role") == role for name in user_components)

def _has_component(user_components, target_name):
    return target_name in user_components

def _has_actuator(user_components, comp_map):
    for name in user_components:
        if comp_map.get(name, {}).get("category") == "actuator":
            return True
    return False

def _role_aware_project_name(user_components, comp_map, project_type):
    prefix = _primary_sensor_name(user_components, comp_map)
    normalized_type = project_type.lower()
    has_gsm = _has_component(user_components, "GSM SIM800L")
    has_buzzer = _has_component(user_components, "Buzzer")
    has_output = _has_role(user_components, comp_map, "output")
    has_actuator = _has_actuator(user_components, comp_map)
    has_sensor = _has_role(user_components, comp_map, "input")

    # High-priority fallback naming to avoid misleading smart/control labels.
    if has_output and not has_sensor:
        return "Basic Output System", "basic"
    if not has_sensor:
        return "Basic Control System", "basic"

    if "alert" in normalized_type:
        if has_gsm:
            return f"{prefix} SMS Alert System", "alert"
        if has_buzzer:
            return f"{prefix} Alarm System", "alert"

    if "control" in normalized_type and has_actuator:
        return f"{prefix} Control System", "control"

    if "iot" in normalized_type and _has_role(user_components, comp_map, "communication"):
        return f"{prefix} IoT Monitoring System", "monitoring"
    if "safety" in normalized_type:
        return f"{prefix} Safety Monitoring System", "monitoring"
    if "data logging" in normalized_type:
        return f"{prefix} Data Logging System", "monitoring"
    if "environmental" in normalized_type:
        return f"{prefix} Environmental Monitoring System", "monitoring"

    # Fallback naming rules
    if has_output:
        return f"{prefix} Monitoring System", "monitoring"
    if has_actuator:
        return f"{prefix} Control System", "control"

    return "Basic Control System", "basic"

def get_missing_component_suggestions(roles):
    role_set = set(roles)
    suggestions = []

    if "output" not in role_set:
        suggestions.append("Add LED/Buzzer/LCD output for feedback")
    if "communication" not in role_set:
        suggestions.append("Add GSM/Bluetooth for remote alerts")

    if not suggestions:
        suggestions.append("System is complete. Proceed to wiring and testing.")

    return suggestions

def generate_system_flow(user_components):
    comp_map = _component_lookup()
    flow = []
    controller_name = None
    sensor_name = None

    for name in user_components:
        meta = comp_map.get(name, {})
        if meta.get("role") == "controller" and controller_name is None:
            controller_name = name
        if meta.get("role") == "input" and sensor_name is None:
            sensor_name = _sensor_prefix(name)

    if sensor_name:
        flow.append(f"{sensor_name} sensor detects real-world data.")
    if controller_name and sensor_name:
        flow.append(f"{controller_name} processes sensor data and controls outputs.")
    elif controller_name:
        flow.append(f"{controller_name} controls connected modules.")

    if _has_component(user_components, "Buzzer"):
        flow.append("Buzzer provides audible alert.")
    else:
        for name in user_components:
            meta = comp_map.get(name, {})
            if meta.get("role") == "output":
                flow.append(f"{name} provides output feedback.")
                break

    if _has_component(user_components, "GSM SIM800L"):
        flow.append("GSM sends SMS alerts.")
    else:
        for name in user_components:
            meta = comp_map.get(name, {})
            if meta.get("role") == "communication":
                flow.append(f"{name} sends updates remotely.")
                break

    if not flow:
        flow.append("Add core components to build a complete system flow.")

    return flow

def get_feasibility_issues(roles, user_components=None):
    issues = []
    role_set = set(roles)
    user_components = user_components or []

    if "controller" not in role_set:
        issues.append("Missing controller (Arduino)")
    if "input" not in role_set:
        issues.append("No input sensor detected")
    if "GSM SIM800L" in user_components and "Power Supply (4V regulated)" not in user_components and "Battery" not in user_components:
        issues.append("Power constraint: GSM SIM800L needs stable 4V high-current supply")

    return issues

def _infer_project_type(project_name):
    lower_name = project_name.lower()
    if "alert" in lower_name or "alarm" in lower_name:
        return "Alert"
    if "safety" in lower_name:
        return "Safety"
    if "iot" in lower_name:
        return "IoT"
    if "data logging" in lower_name or "logger" in lower_name:
        return "Data Logging"
    if "monitoring" in lower_name or "monitor" in lower_name:
        return "Monitoring"
    if "control" in lower_name:
        return "Control"
    if "basic output" in lower_name:
        return "Basic Output"
    return "General"

def _unique_preserve_order(items):
    return list(dict.fromkeys(items))

def _build_component_groups(user_components, comp_map):
    groups = {"controller": [], "input": [], "output": [], "communication": []}
    for name in user_components:
        role = comp_map.get(name, {}).get("role")
        if role in groups:
            groups[role].append(name)
    return groups

def _build_sensor_sets(sensors, project_type, min_inputs):
    if not sensors:
        return [[]]

    sets = [[sensor] for sensor in sensors]
    if len(sensors) > 1 and project_type in ("Monitoring", "Data Logging", "IoT", "Safety"):
        sets.append(sensors[:])
    if min_inputs > 1 and len(sensors) >= min_inputs:
        sets.append(sensors[:min_inputs])
    return sets

def _system_logic_summary(project_type, used_sensor_count, has_decision_logic, has_comm_used):
    segments = []
    if used_sensor_count > 1:
        segments.append("Combines multiple sensors for richer decisions")
    elif used_sensor_count == 1:
        segments.append("Uses one sensor for focused measurement")

    if has_decision_logic:
        segments.append("Applies threshold/condition-based logic")
    if project_type in ("Monitoring", "Data Logging", "IoT", "Safety"):
        segments.append("Runs in a continuous monitoring loop")
    if has_comm_used:
        segments.append("Sends updates/alerts through communication module")

    return "; ".join(segments) if segments else "Basic component interaction only"

def _normalize_category(category_text):
    text = (category_text or "").strip().lower()
    mapping = {
        "alert": "Alert",
        "safety": "Safety",
        "iot": "IoT",
        "monitoring": "Monitoring",
        "data logging": "Data Logging",
        "datalogging": "Data Logging",
        "control": "Control",
        "basic output": "Basic Output",
    }
    return mapping.get(text, category_text.strip().title() if category_text else "Unknown")

def _get_ml_boost(project_type, ml_category):
    normalized_ml = _normalize_category(ml_category)
    related_map = {
        "Alert": {"Safety", "IoT", "Monitoring"},
        "Safety": {"Alert", "Monitoring", "IoT"},
        "IoT": {"Monitoring", "Data Logging", "Alert"},
        "Monitoring": {"Data Logging", "IoT", "Safety"},
        "Data Logging": {"Monitoring", "IoT"},
        "Control": {"Monitoring"},
        "Basic Output": {"Control"},
    }

    if project_type == normalized_ml:
        return 3, f"ML predicted '{normalized_ml}' (exact match, +3)"
    if normalized_ml in related_map.get(project_type, set()) or project_type in related_map.get(normalized_ml, set()):
        return 1, f"ML predicted '{normalized_ml}' (closely related, +1)"
    return 0, f"ML predicted '{normalized_ml}' (unrelated, +0)"

def _calculate_project_score(project_type, used_components, all_components, rule_conditions, comp_map, ml_category):
    used_roles = {comp_map.get(name, {}).get("role") for name in used_components}
    all_roles = {comp_map.get(name, {}).get("role") for name in all_components}
    used_roles.discard(None)
    all_roles.discard(None)

    used_sensor_count = sum(1 for name in used_components if comp_map.get(name, {}).get("role") == "input")
    core_score = 0
    depth_score = 0
    comm_score = 0
    real_world_score = 0
    penalties = 0

    # 1) Core Completeness (MAX +10)
    if "controller" in used_roles:
        core_score += 4
    if "input" in used_roles:
        core_score += 3
    if "output" in used_roles:
        core_score += 3

    # 2) Component Utilization (MAX +5)
    utilization_score = min(5, len(used_components))

    # 3) System Depth (MAX +5)
    if used_sensor_count > 1:
        depth_score += 2
    has_decision_logic = bool(
        rule_conditions.get("requires_threshold")
        or rule_conditions.get("requires_logic")
        or project_type in ("Alert", "Safety", "Control")
    )
    if has_decision_logic:
        depth_score += 2
    if project_type in ("Monitoring", "Data Logging", "IoT", "Safety"):
        depth_score += 1

    # 4) Communication Capability (MAX +4)
    if "communication" in all_roles:
        comm_score += 2
    if "communication" in used_roles:
        comm_score += 2

    # 5) Real-World Relevance (MAX +4)
    if project_type in ("Alert", "Safety", "Monitoring", "Data Logging", "IoT", "Control"):
        real_world_score += 2
    if core_score >= 7:
        real_world_score += 2

    # 6) Penalties
    if "input" not in used_roles:
        penalties -= 5
    if "controller" not in used_roles:
        penalties -= 4
    if len(set(all_components) - set(used_components)) > 0:
        penalties -= 2
    if project_type == "Safety" and not has_decision_logic:
        penalties -= 3

    rule_score = core_score + utilization_score + depth_score + comm_score + real_world_score
    ml_boost, ml_reason = _get_ml_boost(project_type, ml_category)
    final_score = rule_score + ml_boost + penalties
    has_comm_used = "communication" in used_roles

    why = {
        "core_completeness": f"{core_score}/10 from controller/input/output availability in used components",
        "component_usage": f"{len(used_components)} used component(s): {', '.join(used_components) if used_components else 'None'}",
        "system_logic": _system_logic_summary(project_type, used_sensor_count, has_decision_logic, has_comm_used),
        "ml_influence": ml_reason,
        "real_world": f"{real_world_score}/4 based on practical problem-solving and deployability",
    }

    return {
        "score": final_score,
        "why": why,
        "core_score": core_score,
        "used_count": len(used_components),
        "relevance_score": real_world_score,
        "has_communication": "communication" in used_roles,
        "project_type": project_type,
        "rule_score": rule_score,
        "ml_boost": ml_boost,
        "penalties": penalties,
    }

def get_score_label(score):
    if score >= 16:
        return "Highly Recommended"
    if score >= 10:
        return "Good Option"
    return "Basic Idea"

def generate_projects(user_components, roles, ml_category=None):
    rules = load_rules()
    comp_map = _component_lookup()
    component_groups = _build_component_groups(user_components, comp_map)
    ranked = []
    role_set = set(roles)
    sensors = component_groups["input"]
    outputs = component_groups["output"]
    communications = component_groups["communication"]
    controllers = component_groups["controller"]

    for rule in rules:
        required = rule["conditions"]["roles_required"]
        matched_roles = sum(1 for req in required if req in role_set)
        min_inputs = rule["conditions"].get("min_inputs", 0)
        if matched_roles <= 0 or len(sensors) < min_inputs:
            continue

        inferred_rule_type = _infer_project_type(rule.get("project_type", ""))
        sensor_sets = _build_sensor_sets(sensors, inferred_rule_type, min_inputs)

        for sensor_set in sensor_sets:
            used = []
            if controllers:
                used.append(controllers[0])
            used.extend(sensor_set)

            if inferred_rule_type in ("Alert", "Safety"):
                if "Buzzer" in outputs:
                    used.append("Buzzer")
                elif outputs:
                    used.append(outputs[0])
            elif outputs:
                used.append(outputs[0])

            if inferred_rule_type == "IoT" and communications:
                used.append(communications[0])
            elif inferred_rule_type == "Alert" and "GSM SIM800L" in communications:
                used.append("GSM SIM800L")
            elif "communication" in required and communications:
                used.append(communications[0])

            used = _unique_preserve_order(used)
            project_name, _ = _role_aware_project_name(used, comp_map, rule.get("project_type", ""))
            if len(sensor_set) > 1 and inferred_rule_type in ("Monitoring", "Data Logging", "IoT", "Safety"):
                project_name = f"Multi-Sensor {project_name}"

            scored = _calculate_project_score(
                project_type=inferred_rule_type,
                used_components=used,
                all_components=user_components,
                rule_conditions=rule.get("conditions", {}),
                comp_map=comp_map,
                ml_category=ml_category,
            )

            ranked.append({
                "name": project_name,
                "description": rule["description"],
                "score": scored["score"],
                "type": scored["project_type"],
                "why": scored["why"],
                "components_used": used,
                "used_count": scored["used_count"],
                "relevance_score": scored["relevance_score"],
                "core_score": scored["core_score"],
                "has_communication": scored["has_communication"],
                "label": get_score_label(scored["score"]),
            })

    # Tie-breaker priority:
    # 1) more used components, 2) more real-world relevance, 3) better core completeness
    ranked.sort(
        key=lambda item: (
            item["score"],
            item["used_count"],
            item["relevance_score"],
            item["core_score"],
            1 if item["has_communication"] else 0,
        ),
        reverse=True,
    )
    deduped = []
    seen = set()

    for item in ranked:
        signature = (item["name"], tuple(item["components_used"]))
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(item)
    for project in deduped:
        project.pop("used_count", None)
        project.pop("relevance_score", None)
        project.pop("core_score", None)
        project.pop("has_communication", None)

    return deduped