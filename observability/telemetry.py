from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import time
import uuid

@dataclass
class TraceEvent:
    timestamp: str
    tool: str
    status: str
    latency_ms: int
    detail: str = ""
    attempt: int = 1

class Trace:
    def __init__(self):
        self.execution_id = f"RSAFE-{uuid.uuid4().hex[:8].upper()}"
        self.started_at = datetime.now(timezone.utc)
        self.events = []
        self.human_approvals = 0
        self.permission_denials = 0
        self.retries = 0
        self.final_status = "RUNNING"

    def add(self, tool, status, latency_ms=0, detail="", attempt=1):
        if status == "DENIED":
            self.permission_denials += 1
        if status == "RETRY":
            self.retries += 1
        self.events.append(
            TraceEvent(
                datetime.now(timezone.utc).strftime("%H:%M:%S"),
                tool, status, int(latency_ms), detail, attempt
            )
        )

    def approve(self, detail=""):
        self.human_approvals += 1
        self.add("human_approval", "APPROVED", 0, detail)

    def summary(self):
        total_latency = sum(e.latency_ms for e in self.events)
        successful = sum(e.status in {"SUCCESS","APPROVED"} for e in self.events)
        failed = sum(e.status in {"FAILED","DENIED"} for e in self.events)
        return {
            "execution_id": self.execution_id,
            "status": self.final_status,
            "tools_called": len(self.events),
            "successful_events": successful,
            "failed_events": failed,
            "retries": self.retries,
            "permission_denials": self.permission_denials,
            "human_approvals": self.human_approvals,
            "total_latency_ms": total_latency,
        }

    def rows(self):
        return [asdict(e) for e in self.events]

class timed_tool:
    def __enter__(self):
        self.start = time.perf_counter()
        self.latency_ms = 0
        return self

    def __exit__(self, *args):
        self.latency_ms = int((time.perf_counter() - self.start) * 1000)
