import pytest
from agent.guardrails import require_permission

def test_customer_service_cannot_update_allowance():
    with pytest.raises(PermissionError):
        require_permission("Customer Service", "update_allowance")

def test_program_admin_can_update_allowance():
    require_permission("Program Administrator", "update_allowance")
