ROLE_PERMISSIONS = {
    "Customer Service": {
        "read_employee","read_program","read_order","read_inventory",
        "check_allowance","create_return","replace_order","send_notification",
    },
    "Program Administrator": {
        "read_employee","read_program","read_order","read_inventory",
        "check_allowance","create_return","replace_order","send_notification",
        "update_allowance","update_program",
    },
}

def is_allowed(role, permission):
    return permission in ROLE_PERMISSIONS.get(role, set())

def require_permission(role, permission):
    if not is_allowed(role, permission):
        raise PermissionError(f"Role '{role}' does not have permission '{permission}'.")

def safety_guardrail(message):
    lower = message.lower()
    risky = ["ignore safety","override ppe","bypass ppe","invent arc rating","change safety rating"]
    for phrase in risky:
        if phrase in lower:
            return (
                "Safety policy override blocked. This demo agent may automate workflow "
                "but may not invent or override approved PPE requirements."
            )
    return None
