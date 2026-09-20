import json
from pathlib import Path
import time
import pandas as pd

from agent.guardrails import require_permission
from agent.policy_engine import program_approves_product, allowance_decision, return_eligibility
from observability.telemetry import timed_tool

class SyntheticEnterprise:
    def __init__(self, data_dir):
        data_dir = Path(data_dir)
        self.employees = pd.read_csv(data_dir/"employees.csv")
        self.products = pd.read_csv(data_dir/"products.csv")
        self.inventory = pd.read_csv(data_dir/"inventory.csv")
        self.orders = pd.read_csv(data_dir/"orders.csv")
        self.programs = json.loads((data_dir/"programs.json").read_text())
        self._inventory_failures_remaining = 0

    def inject_inventory_failure_once(self):
        self._inventory_failures_remaining = 1

    def get_employee(self, employee_id, role, trace):
        require_permission(role, "read_employee")
        with timed_tool() as t:
            row = self.employees[self.employees["employee_id"] == employee_id]
            if row.empty:
                raise KeyError(f"Unknown employee {employee_id}")
            result = row.iloc[0].to_dict()
        trace.add("worker.get_profile", "SUCCESS", t.latency_ms, employee_id)
        return result

    def get_program(self, program_id, role, trace):
        require_permission(role, "read_program")
        with timed_tool() as t:
            result = dict(self.programs[program_id])
        trace.add("program.get_rules", "SUCCESS", t.latency_ms, program_id)
        return result

    def get_recent_order(self, employee_id, role, trace):
        require_permission(role, "read_order")
        with timed_tool() as t:
            rows = self.orders[self.orders["employee_id"] == employee_id]
            if rows.empty:
                result = None
            else:
                result = rows.sort_values("order_date", ascending=False).iloc[0].to_dict()
        trace.add("orders.find_recent", "SUCCESS", t.latency_ms, employee_id)
        return result

    def search_inventory(self, employee, category, role, trace, max_attempts=2):
        require_permission(role, "read_inventory")
        for attempt in range(1, max_attempts+1):
            with timed_tool() as t:
                if self._inventory_failures_remaining > 0:
                    self._inventory_failures_remaining -= 1
                    time.sleep(0.02)
                    trace.add(
                        "inventory.search",
                        "RETRY" if attempt < max_attempts else "FAILED",
                        t.latency_ms,
                        "Synthetic HTTP 503 from inventory service",
                        attempt,
                    )
                    if attempt < max_attempts:
                        continue
                    raise RuntimeError("Inventory service unavailable after retry.")

                candidates = self.products[
                    (self.products["category"] == category)
                    & (self.products["fit"] == employee["fit_preference"])
                    & (self.products["size"].astype(str) == str(employee["size_top"]))
                ].copy()
                merged = candidates.merge(self.inventory, on="sku", how="left")
                merged = merged[
                    (merged["location"] == employee["location"])
                    & (merged["qty"] > 0)
                ]
                result = merged.sort_values(["eta_days","price"]).to_dict("records")
            trace.add(
                "inventory.search","SUCCESS",t.latency_ms,
                f"{len(result)} available candidate(s)",attempt
            )
            return result
        return []

    def approved_candidates(self, employee, program, candidates):
        return [
            c for c in candidates
            if program_approves_product(program, c, employee["program_id"])
        ]

    def check_allowance(self, employee, price, role, trace):
        require_permission(role, "check_allowance")
        with timed_tool() as t:
            decision = allowance_decision(employee["allowance_remaining"], price)
        trace.add(
            "allowance.check","SUCCESS",t.latency_ms,
            f"remaining=${float(employee['allowance_remaining']):.2f}; item=${float(price):.2f}"
        )
        return decision

    def replace_order(self, employee_id, old_order_id, replacement_sku, price, role, trace):
        require_permission(role, "replace_order")
        with timed_tool() as t:
            if old_order_id:
                mask = self.orders["order_id"] == old_order_id
                self.orders.loc[mask, "status"] = "Replaced"
            new_id = f"R{len(self.orders)+9000}"
            new_row = {
                "order_id": new_id,
                "employee_id": employee_id,
                "sku": replacement_sku,
                "status": "Replacement Created",
                "order_date": "2026-09-19",
                "embellished": False,
                "washed": False,
                "worn": False,
            }
            self.orders = pd.concat([self.orders, pd.DataFrame([new_row])], ignore_index=True)
            mask = self.employees["employee_id"] == employee_id
            current = float(self.employees.loc[mask, "allowance_remaining"].iloc[0])
            self.employees.loc[mask, "allowance_remaining"] = max(0.0, current-float(price))
        trace.add("orders.create_replacement","SUCCESS",t.latency_ms,new_id)
        return new_row

    def evaluate_return(self, order, program, role, trace):
        require_permission(role, "create_return")
        with timed_tool() as t:
            decision = return_eligibility(order, program)
        trace.add(
            "returns.evaluate","SUCCESS",t.latency_ms,
            "; ".join(decision["reasons"]) or "Eligible"
        )
        return decision

    def create_return(self, order_id, role, trace):
        require_permission(role, "create_return")
        with timed_tool() as t:
            mask = self.orders["order_id"] == order_id
            self.orders.loc[mask, "status"] = "Return Initiated"
        trace.add("returns.create","SUCCESS",t.latency_ms,order_id)
        return {"order_id": order_id, "status": "Return Initiated"}

    def update_allowance(self, employee_id, delta, role, trace):
        try:
            require_permission(role, "update_allowance")
        except PermissionError as exc:
            trace.add("allowance.update","DENIED",0,str(exc))
            raise
        with timed_tool() as t:
            mask = self.employees["employee_id"] == employee_id
            self.employees.loc[mask,"allowance_remaining"] = (
                self.employees.loc[mask,"allowance_remaining"].astype(float)+float(delta)
            )
            value = float(self.employees.loc[mask,"allowance_remaining"].iloc[0])
        trace.add("allowance.update","SUCCESS",t.latency_ms,f"new balance=${value:.2f}")
        return value

    def send_notification(self, employee_id, message, role, trace):
        require_permission(role, "send_notification")
        with timed_tool() as t:
            result = {"employee_id": employee_id, "message": message, "sent": True}
        trace.add("notifications.send","SUCCESS",t.latency_ms,"Synthetic notification")
        return result
