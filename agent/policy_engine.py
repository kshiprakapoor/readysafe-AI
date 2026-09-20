from datetime import datetime

def program_approves_product(program, product, program_id):
    product_programs = {x.strip() for x in str(product["programs"]).split(",")}
    return product["category"] in program["approved_categories"] and program_id in product_programs

def allowance_decision(allowance_remaining, item_price):
    difference = round(float(item_price) - float(allowance_remaining), 2)
    return {
        "within_allowance": difference <= 0,
        "difference": max(0.0, difference),
        "requires_approval": difference > 0,
    }

def return_eligibility(order, program, today="2026-09-19"):
    order_date = datetime.strptime(str(order["order_date"]), "%Y-%m-%d")
    current = datetime.strptime(today, "%Y-%m-%d")
    age_days = (current - order_date).days
    reasons = []
    if age_days > int(program["return_window_days"]):
        reasons.append(f"Outside {program['return_window_days']}-day return window.")
    if bool(order["washed"]):
        reasons.append("Item has been washed.")
    if bool(order["worn"]):
        reasons.append("Item has been worn.")
    if bool(order["embellished"]) and not bool(program["embellished_returns_allowed"]):
        reasons.append("Embellished items are not eligible for automated return.")
    return {"eligible": not reasons, "age_days": age_days, "reasons": reasons}
