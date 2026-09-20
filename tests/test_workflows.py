from pathlib import Path
from agent.orchestrator import ReadySafeAgent
from agent.tools import SyntheticEnterprise

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

def test_emergency_replacement_requires_human_approval():
    enterprise = SyntheticEnterprise(DATA_DIR)
    agent = ReadySafeAgent(enterprise)
    result = agent.run(
        employee_id="E1042",
        message="My approved FR jacket is backordered and I start tomorrow. Find a replacement.",
        role="Customer Service",
    )
    assert result.requires_approval is True
    assert result.pending_action["type"] == "replace_order"

def test_retry_recovers_from_one_inventory_failure():
    enterprise = SyntheticEnterprise(DATA_DIR)
    agent = ReadySafeAgent(enterprise)
    result = agent.run(
        employee_id="E1042",
        message="My approved FR jacket is backordered and I start tomorrow. Find a replacement.",
        role="Customer Service",
        simulate_inventory_failure=True,
    )
    assert result.trace.retries == 1
    assert result.requires_approval is True

def test_unauthorized_allowance_change_is_denied():
    enterprise = SyntheticEnterprise(DATA_DIR)
    agent = ReadySafeAgent(enterprise)
    result = agent.run(
        employee_id="E1042",
        message="Increase this employee's annual allowance by $500.",
        role="Customer Service",
    )
    assert result.title == "Permission denied"
    assert result.trace.permission_denials == 1

def test_program_admin_can_update_allowance():
    enterprise = SyntheticEnterprise(DATA_DIR)
    agent = ReadySafeAgent(enterprise)
    result = agent.run(
        employee_id="E1042",
        message="Increase this employee's annual allowance by $500.",
        role="Program Administrator",
    )
    assert result.title == "Allowance updated"
