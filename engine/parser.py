import json

def load_aliases():
    with open("data/aliases.json") as f:
        return json.load(f)

def normalize_input(user_input):
    aliases = load_aliases()
    parts = [part.strip().lower() for part in user_input.split(",") if part.strip()]
    normalized = []

    for part in parts:
        # 1) Exact alias match first
        if part in aliases:
            normalized.append(aliases[part])
            continue

        # 2) Partial match using substring in both directions
        best_match = None
        for alias_key, canonical_name in aliases.items():
            if alias_key in part or part in alias_key:
                if best_match is None or len(alias_key) > best_match[0]:
                    best_match = (len(alias_key), canonical_name)

        if best_match:
            normalized.append(best_match[1])
        else:
            # Keep unknown token as-is so user can still see what was parsed.
            if part.isalnum() and len(part) <= 4:
                normalized.append(part.upper())
            else:
                normalized.append(part.title())

    # Preserve order while removing duplicates
    return list(dict.fromkeys(normalized))