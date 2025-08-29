def diff_schemas(schema_old: dict, schema_new: dict) -> dict:
    """Compare two schema dicts and return added/removed fields."""
    old_fields = set(schema_old.get("fields", []))
    new_fields = set(schema_new.get("fields", []))

    return {
        "added": list(new_fields - old_fields),
        "removed": list(old_fields - new_fields)
    }
