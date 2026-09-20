from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent.guardrails import safety_guardrail
from agent.planner import infer_intent
from observability.telemetry import Trace

@dataclass
class AgentResult:
    title: str
    worker_ready: bool
    narrative: str
    actions: List[str] = field(default_factory=list)
    trace: Optional[Trace] = None
    requires_approval: bool = False
    approval_reason: str = ""
    pending_action: Optional[Dict[str, Any]] = None
    details: Dict[str, Any] = field(default_factory=dict)

class ReadySafeAgent:
    def __init__(self, enterprise):
        self.enterprise = enterprise

    def run(self, employee_id, message, role, simulate_inventory_failure=False):
        trace = Trace()
        trace.add("request.received","SUCCESS",0,message[:140])

        blocked = safety_guardrail(message)
        if blocked:
            trace.final_status = "BLOCKED"
            trace.add("guardrail.safety","DENIED",0,blocked)
            return AgentResult("Safety policy override blocked",False,blocked,trace=trace)

        intent = infer_intent(message)
        trace.add("planner.intent","SUCCESS",0,intent)

        try:
            employee = self.enterprise.get_employee(employee_id, role, trace)
            program = self.enterprise.get_program(employee["program_id"], role, trace)

            if intent == "emergency_replacement":
                return self._replacement(employee, program, role, trace, simulate_inventory_failure)
            if intent == "fit_issue":
                return self._fit(employee, program, role, trace, simulate_inventory_failure)
            if intent == "return_request":
                return self._return(employee, program, role, trace)
            if intent == "new_hire":
                trace.final_status = "COMPLETED"
                return AgentResult(
                    "Program setup reviewed", True,
                    f"{employee['name']} is active in {program['program_name']} with "
                    f"${float(employee['allowance_remaining']):.2f} remaining.",
                    actions=[
                        f"Confirmed active worker profile for {employee['name']}.",
                        f"Loaded program: {program['program_name']}.",
                        f"Approved categories: {', '.join(program['approved_categories'])}.",
                        f"Allowance remaining: ${float(employee['allowance_remaining']):.2f}.",
                    ],
                    trace=trace,
                    details={"employee":employee,"program":program},
                )
            if intent == "update_allowance":
                return self._allowance(employee, role, trace)

            trace.final_status = "COMPLETED"
            return AgentResult(
                "Program information retrieved", True,
                f"{employee['name']} is enrolled in {program['program_name']}. "
                "No transactional action was inferred.",
                actions=["Retrieved worker profile.","Retrieved employer program rules.","No change executed."],
                trace=trace,
            )
        except PermissionError as exc:
            trace.final_status = "DENIED"
            return AgentResult("Access denied",False,str(exc),trace=trace)
        except Exception as exc:
            trace.final_status = "FAILED"
            trace.add("workflow","FAILED",0,str(exc))
            return AgentResult(
                "Workflow escalated",False,
                "The automated workflow could not complete safely. "
                f"It was escalated with context preserved. Error: {exc}",
                trace=trace,
            )

    def _replacement(self, employee, program, role, trace, simulate_failure):
        order = self.enterprise.get_recent_order(employee["employee_id"], role, trace)
        if simulate_failure:
            self.enterprise.inject_inventory_failure_once()
        candidates = self.enterprise.search_inventory(employee,"FR outerwear",role,trace)
        approved = self.enterprise.approved_candidates(employee,program,candidates)
        if not approved:
            trace.final_status = "ESCALATED"
            return AgentResult(
                "No immediate approved replacement found",False,
                "No in-stock, program-approved replacement was available.",
                actions=["Retrieved original order.","Searched local inventory.","Escalated for human resolution."],
                trace=trace,
            )
        choice = approved[0]
        allowance = self.enterprise.check_allowance(employee,choice["price"],role,trace)
        if allowance["requires_approval"]:
            trace.final_status = "WAITING_APPROVAL"
            return AgentResult(
                "Replacement found — approval required",False,
                f"{choice['name']} ({choice['sku']}) is approved and available now, "
                f"but costs ${choice['price']:.2f}, exceeding the remaining allowance by "
                f"${allowance['difference']:.2f}.",
                actions=[
                    "Retrieved worker and employer program.",
                    f"Found {len(approved)} approved in-stock replacement option(s).",
                    f"Selected lowest-cost immediately available option: {choice['name']}.",
                    "Paused because the allowance exception requires human approval.",
                ],
                trace=trace,
                requires_approval=True,
                approval_reason=f"Allowance exception: ${allowance['difference']:.2f} over remaining balance.",
                pending_action={
                    "type":"replace_order",
                    "employee_id":employee["employee_id"],
                    "old_order_id":order["order_id"] if order else "",
                    "replacement_sku":choice["sku"],
                    "price":float(choice["price"]),
                    "notification":f"Replacement {choice['name']} approved and created."
                },
                details={"choice":choice,"allowance":allowance},
            )

        created = self.enterprise.replace_order(
            employee["employee_id"], order["order_id"] if order else "",
            choice["sku"], float(choice["price"]), role, trace
        )
        self.enterprise.send_notification(
            employee["employee_id"], f"Replacement {choice['name']} created.", role, trace
        )
        trace.final_status = "COMPLETED"
        return AgentResult(
            "Worker ready",True,
            f"An approved in-stock replacement was created: {choice['name']}.",
            actions=[
                "Confirmed program rules.","Found approved local inventory.",
                "Verified allowance.","Created replacement order.","Sent synthetic notification."
            ],
            trace=trace, details={"order":created,"choice":choice},
        )

    def _fit(self, employee, program, role, trace, simulate_failure):
        if simulate_failure:
            self.enterprise.inject_inventory_failure_once()
        candidates = self.enterprise.search_inventory(employee,"FR shirt",role,trace)
        approved = self.enterprise.approved_candidates(employee,program,candidates)
        if not approved:
            trace.final_status = "ESCALATED"
            return AgentResult(
                "No approved fit alternative found",False,
                "No approved in-stock alternative matched the worker's fit and size.",
                actions=["Checked worker fit preference.","Searched approved inventory.","Escalated."],
                trace=trace,
            )
        choice = approved[0]
        allowance = self.enterprise.check_allowance(employee,choice["price"],role,trace)
        trace.final_status = "COMPLETED"
        return AgentResult(
            "Approved fit alternative identified",True,
            f"{choice['name']} is available in {employee['fit_preference']} {employee['size_top']} "
            f"for ${choice['price']:.2f} and is within the current allowance.",
            actions=[
                "Matched worker size and fit preference.","Filtered to employer-approved catalog.",
                "Checked local inventory.","Verified allowance."
            ],
            trace=trace, details={"choice":choice,"allowance":allowance},
        )

    def _return(self, employee, program, role, trace):
        order = self.enterprise.get_recent_order(employee["employee_id"],role,trace)
        if not order:
            trace.final_status = "ESCALATED"
            return AgentResult("No order found",True,"No recent order was found.",trace=trace)
        decision = self.enterprise.evaluate_return(order,program,role,trace)
        if not decision["eligible"]:
            trace.final_status = "COMPLETED"
            return AgentResult(
                "Automated return not eligible",True,
                "The agent did not create a return because controlled program rules were not met. "
                + " ".join(decision["reasons"]),
                actions=[
                    f"Located order {order['order_id']}.",
                    f"Order age: {decision['age_days']} day(s).",
                    "Applied deterministic return policy.",
                    "No transaction executed; case can be escalated for human review."
                ],
                trace=trace, details={"order":order,"decision":decision},
            )
        created = self.enterprise.create_return(order["order_id"],role,trace)
        trace.final_status = "COMPLETED"
        return AgentResult(
            "Return initiated",True,f"Return initiated for order {created['order_id']}.",
            actions=["Validated return policy.","Created synthetic return transaction."],
            trace=trace,
        )

    def _allowance(self, employee, role, trace):
        try:
            new_value = self.enterprise.update_allowance(employee["employee_id"],500.0,role,trace)
        except PermissionError:
            trace.final_status = "DENIED"
            return AgentResult(
                "Permission denied",True,
                "The requested allowance change was not executed. "
                "This action requires Program Administrator permission.",
                actions=[
                    "Identified transactional request.",
                    f"Checked permissions for role: {role}.",
                    "Blocked unauthorized allowance modification."
                ],
                trace=trace,
            )
        trace.final_status = "COMPLETED"
        return AgentResult(
            "Allowance updated",True,
            f"Program Administrator updated the synthetic allowance to ${new_value:.2f}.",
            actions=["Verified Program Administrator permission.","Updated synthetic allowance."],
            trace=trace,
        )

    def execute_approved_action(self, pending_action, role, trace):
        trace.approve(pending_action.get("type","transaction"))
        if pending_action["type"] == "replace_order":
            created = self.enterprise.replace_order(
                pending_action["employee_id"],pending_action["old_order_id"],
                pending_action["replacement_sku"],pending_action["price"],role,trace
            )
            self.enterprise.send_notification(
                pending_action["employee_id"],
                pending_action.get("notification","Approved action completed."),
                role,trace
            )
            trace.final_status = "COMPLETED"
            return created
        raise ValueError(f"Unknown approved action: {pending_action['type']}")
