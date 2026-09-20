from pathlib import Path
import json
import pandas as pd
import streamlit as st

from agent.orchestrator import ReadySafeAgent
from agent.tools import SyntheticEnterprise

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

st.set_page_config(
    page_title="ReadySafe AI | Worker Readiness Agent",
    page_icon="🦺",
    layout="wide",
)

st.title("ReadySafe AI")
st.markdown("**Agentic automation that helps workers start every shift protected.**")
st.caption("Developed by Kshipra S. Kapoor, PhD")

st.markdown(
    """
Protective-clothing programs involve more than placing an order. A worker may need a
replacement before the next shift, a better-fitting approved garment, help understanding
an employer program, or a return that must follow controlled rules.

**ReadySafe AI** is a synthetic enterprise-agent prototype that coordinates worker profiles,
employer program rules, approved apparel, inventory, allowances, approvals, order actions,
and audit logging in one workflow.
"""
)

st.info(
    "Portfolio prototype only. All workers, programs, orders, inventory, and policies are "
    "synthetic. No Tyndale or customer data are used. PPE rules are treated as deterministic, "
    "source-controlled policy and may not be overridden by the agent."
)

@st.cache_data
def load_scenarios():
    return json.loads((DATA_DIR / "scenarios.json").read_text())

def fresh_enterprise():
    return SyntheticEnterprise(DATA_DIR)

if "enterprise" not in st.session_state:
    st.session_state.enterprise = fresh_enterprise()
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None
if "pending_trace" not in st.session_state:
    st.session_state.pending_trace = None

scenarios = load_scenarios()
agent = ReadySafeAgent(st.session_state.enterprise)

tab_ops, tab_engineering, tab_data, tab_arch = st.tabs(
    ["Worker Operations", "Engineering View", "Synthetic Data", "Architecture"]
)

with tab_ops:
    st.subheader("Who needs help today?")
    scenario_name = st.selectbox("Choose a synthetic scenario", list(scenarios.keys()))
    scenario = scenarios[scenario_name]

    role = st.selectbox(
        "Signed-in user role",
        ["Customer Service", "Program Administrator"],
        help="Demonstrates role-based permissions and least-privilege access."
    )

    employee_id = scenario["employee_id"]
    emp_df = st.session_state.enterprise.employees
    employee = emp_df[emp_df["employee_id"] == employee_id].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Worker", employee["name"])
    c2.metric("Role", employee["role"])
    c3.metric("Location", employee["location"])
    c4.metric("Allowance remaining", f"${float(employee['allowance_remaining']):.0f}")

    st.markdown("#### Worker request")
    message = st.text_area(
        "Request",
        value=scenario["request"],
        height=115,
        label_visibility="collapsed",
    )

    simulate_failure = st.checkbox(
        "Simulate one inventory API failure (HTTP 503) to demonstrate retry logic",
        value=False,
    )

    if st.button("Run ReadySafe Agent", type="primary", use_container_width=True):
        result = agent.run(
            employee_id=employee_id,
            message=message,
            role=role,
            simulate_inventory_failure=simulate_failure,
        )
        st.session_state.last_result = result
        st.session_state.pending_action = result.pending_action
        st.session_state.pending_trace = result.trace

    result = st.session_state.last_result
    if result is not None:
        st.divider()

        if result.worker_ready:
            st.success(f"✅ {result.title}")
        elif result.requires_approval:
            st.warning(f"⚠️ {result.title}")
        else:
            st.error(result.title)

        st.write(result.narrative)

        if result.actions:
            st.markdown("#### Agent actions")
            for action in result.actions:
                st.write(f"✓ {action}")

        if result.requires_approval:
            st.markdown("#### Human approval required")
            st.warning(result.approval_reason)
            a1, a2 = st.columns(2)

            if a1.button("Approve transaction", type="primary", use_container_width=True):
                created = agent.execute_approved_action(
                    st.session_state.pending_action,
                    role,
                    st.session_state.pending_trace,
                )
                result.requires_approval = False
                result.worker_ready = True
                result.title = "Worker ready — approved action completed"
                result.narrative = (
                    f"Human approval was recorded and replacement order "
                    f"{created['order_id']} was created in the synthetic order system."
                )
                st.session_state.pending_action = None
                st.rerun()

            if a2.button("Reject transaction", use_container_width=True):
                result.requires_approval = False
                result.trace.add(
                    "human_approval", "REJECTED", 0, result.approval_reason
                )
                result.trace.final_status = "REJECTED"
                result.title = "Transaction rejected"
                result.narrative = "No order change was executed."
                st.session_state.pending_action = None
                st.rerun()

with tab_engineering:
    st.subheader("Agent observability")
    result = st.session_state.last_result

    if result is None or result.trace is None:
        st.write("Run a worker scenario to populate the execution trace.")
    else:
        summary = result.trace.summary()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Execution", summary["execution_id"])
        m2.metric("Status", summary["status"])
        m3.metric("Retries", summary["retries"])
        m4.metric("Human approvals", summary["human_approvals"])

        m5, m6, m7, m8 = st.columns(4)
        m5.metric("Tool / audit events", summary["tools_called"])
        m6.metric("Permission denials", summary["permission_denials"])
        m7.metric("Failed events", summary["failed_events"])
        m8.metric("Measured latency", f"{summary['total_latency_ms']} ms")

        st.markdown("#### Execution trace")
        trace_df = pd.DataFrame(result.trace.rows())
        st.dataframe(trace_df, use_container_width=True, hide_index=True)

        st.markdown("#### What this demonstrates")
        st.markdown(
            """
- **Tool calling** — worker, program, order, inventory, allowance, and transaction functions are explicit tools.
- **RBAC / least privilege** — unauthorized transactional actions are denied by role.
- **Human-in-the-loop** — exceptions pause before execution.
- **Retries** — a transient inventory failure can be retried and audited.
- **Guardrails** — workflow reasoning cannot override controlled PPE policy.
- **Auditability** — decisions and actions are visible in the execution trace.
"""
        )

with tab_data:
    st.subheader("Synthetic enterprise data")
    st.caption("Small fictional datasets keep the workflow transparent and reproducible.")

    data_choice = st.selectbox(
        "Dataset",
        ["Employees", "Products", "Inventory", "Orders", "Programs"]
    )
    ent = st.session_state.enterprise

    if data_choice == "Employees":
        st.dataframe(ent.employees, use_container_width=True, hide_index=True)
    elif data_choice == "Products":
        st.dataframe(ent.products, use_container_width=True, hide_index=True)
    elif data_choice == "Inventory":
        st.dataframe(ent.inventory, use_container_width=True, hide_index=True)
    elif data_choice == "Orders":
        st.dataframe(ent.orders, use_container_width=True, hide_index=True)
    else:
        rows = []
        for pid, p in ent.programs.items():
            rows.append({
                "program_id": pid,
                "program_name": p["program_name"],
                "annual_allowance": p["annual_allowance"],
                "approved_categories": ", ".join(p["approved_categories"]),
                "return_window_days": p["return_window_days"],
                "embellished_returns_allowed": p["embellished_returns_allowed"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if st.button("Reset synthetic enterprise state"):
        st.session_state.enterprise = fresh_enterprise()
        st.session_state.last_result = None
        st.session_state.pending_action = None
        st.session_state.pending_trace = None
        st.rerun()

with tab_arch:
    st.subheader("Production-oriented architecture")
    st.code(
        """
Worker / CSR / Manager
        |
        v
API Gateway / Event
        |
        v
Agent Planner / Workflow Orchestrator
        |
        +----------------------+----------------------+
        |                      |                      |
        v                      v                      v
 Worker API              Program / Policy API    Order / Inventory API
        |                      |                      |
        +----------------------+----------------------+
                               |
                               v
                   Deterministic Guardrails
                     + Human Approval Gate
                               |
                               v
                        Transaction Tools
                               |
                               v
                       Audit / Observability

AWS production mapping:
Bedrock / AgentCore + Lambda + API Gateway + IAM + Secrets Manager
+ CloudWatch / OpenTelemetry + CI/CD + Dev/UAT/Production
        """,
        language="text",
    )

    st.markdown(
        """
### Design principle

The model/agent layer may **interpret requests and construct plans**, but it should not
invent safety rules or bypass authorization. PPE policy, permissions, transaction validation,
and approval requirements remain deterministic and independently testable.

### Public demo vs production

This Streamlit version uses an in-memory synthetic enterprise and deterministic planner so it
runs without cloud credentials. In production, the same tool contracts can sit behind
REST/OpenAPI services, with an approved Bedrock model handling natural-language planning and
AWS infrastructure providing governed runtime execution.
"""
    )
