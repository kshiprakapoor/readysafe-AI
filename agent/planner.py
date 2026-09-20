def infer_intent(message):
    text = message.lower()
    if "allowance" in text and any(k in text for k in ["increase","add","change"]):
        return "update_allowance"
    if "return" in text or "embroider" in text or "logo" in text:
        return "return_request"
    if any(k in text for k in ["backorder","damaged","replacement","tomorrow"]):
        return "emergency_replacement"
    if any(k in text for k in ["uncomfortable","fit","women","alternative"]):
        return "fit_issue"
    if any(k in text for k in ["new","starting","first day","what can i order"]):
        return "new_hire"
    return "general_program_help"
