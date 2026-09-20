from agent.policy_engine import allowance_decision, return_eligibility

def test_allowance_requires_approval_when_over_balance():
    result = allowance_decision(100.0, 125.0)
    assert result["requires_approval"] is True
    assert result["difference"] == 25.0

def test_embellished_item_not_auto_returnable():
    order = {
        "order_date": "2026-09-01",
        "washed": False,
        "worn": False,
        "embellished": True,
    }
    program = {
        "return_window_days": 60,
        "embellished_returns_allowed": False,
    }
    result = return_eligibility(order, program, today="2026-09-19")
    assert result["eligible"] is False
    assert any("Embellished" in r for r in result["reasons"])
