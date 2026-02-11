"""Audit logger for MCP Geo evaluation runs."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ToolCallRecord:
    tool_name: str
    timestamp: str
    duration_ms: float
    inputs: Dict[str, Any]
    outputs: Any
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


@dataclass
class AuditRecord:
    audit_id: str
    timestamp: str
    query: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    recommended_tool: Optional[str] = None
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    final_response: Optional[str] = None
    total_duration_ms: float = 0.0
    rate_limit_429_count: int = 0
    rate_limit_429_by_tool: Dict[str, int] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    SECTION_START = "=" * 60
    SECTION_END = "-" * 60
    SUBSECTION = "·" * 40

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path("tests/evaluation/logs/audit")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._current_record: Optional[AuditRecord] = None
        self._start_time: Optional[float] = None

    def start_query(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        audit_id = str(uuid.uuid4())[:8]
        self._current_record = AuditRecord(
            audit_id=audit_id,
            timestamp=datetime.now().isoformat(),
            query=query,
            metadata=metadata or {},
        )
        self._start_time = time.time()
        return audit_id

    def record_routing(
        self,
        intent: str,
        confidence: float,
        recommended_tool: str,
        workflow_steps: List[str],
    ) -> None:
        if not self._current_record:
            return
        self._current_record.intent = intent
        self._current_record.confidence = confidence
        self._current_record.recommended_tool = recommended_tool
        self._current_record.metadata["workflow_steps"] = workflow_steps

    def record_tool_call(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        outputs: Any,
        duration_ms: float,
        status_code: Optional[int],
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        if not self._current_record:
            return
        self._current_record.tool_calls.append(
            ToolCallRecord(
                tool_name=tool_name,
                timestamp=datetime.now().isoformat(),
                duration_ms=duration_ms,
                inputs=inputs,
                outputs=outputs,
                status_code=status_code,
                success=success,
                error=error,
            )
        )
        if status_code == 429:
            self._current_record.rate_limit_429_count += 1
            self._current_record.rate_limit_429_by_tool[tool_name] = (
                self._current_record.rate_limit_429_by_tool.get(tool_name, 0) + 1
            )

    def record_response(self, response: str) -> None:
        if self._current_record:
            self._current_record.final_response = response

    def record_error(self, error: str) -> None:
        if self._current_record:
            self._current_record.success = False
            self._current_record.error = error

    def end_query(self) -> Optional[AuditRecord]:
        if not self._current_record:
            return None
        if self._start_time:
            self._current_record.total_duration_ms = (time.time() - self._start_time) * 1000
        record = self._current_record
        self._write_to_file(record)
        self._current_record = None
        self._start_time = None
        return record

    def format_for_llm(self, record: AuditRecord) -> str:
        lines: List[str] = []
        lines.append(self.SECTION_START)
        lines.append(f"AUDIT LOG: {record.audit_id}")
        lines.append(f"Timestamp: {record.timestamp}")
        lines.append(self.SECTION_START)
        lines.append("")

        lines.append("## 1. QUERY")
        lines.append(self.SECTION_END)
        lines.append(f'User Question: "{record.query}"')
        lines.append("")

        lines.append("## 2. ROUTING DECISION")
        lines.append(self.SECTION_END)
        if record.intent:
            lines.append(f"Intent Detected: {record.intent}")
            lines.append(f"Confidence: {record.confidence}")
            lines.append(f"Recommended Tool: {record.recommended_tool}")
            lines.append(f"Workflow Steps: {record.metadata.get('workflow_steps', [])}")
        else:
            lines.append("No routing decision recorded.")
        lines.append("")

        lines.append("## 3. TOOL CALLS")
        lines.append(self.SECTION_END)
        if not record.tool_calls:
            lines.append("No tool calls recorded.")
        for idx, call in enumerate(record.tool_calls, start=1):
            lines.append(f"### Tool Call {idx}: {call.tool_name}")
            lines.append(self.SUBSECTION)
            lines.append(f"Timestamp: {call.timestamp}")
            lines.append(f"Duration: {call.duration_ms:.1f}ms")
            if call.status_code is not None:
                lines.append(f"HTTP Status: {call.status_code}")
            lines.append(f"Status: {'SUCCESS' if call.success else 'ERROR'}")
            lines.append("")
            lines.append("Inputs:")
            lines.append(f"{call.inputs}")
            lines.append("")
            lines.append("Outputs:")
            lines.append(f"{call.outputs}")
            lines.append("")

        lines.append("## 4. RESPONSE")
        lines.append(self.SECTION_END)
        lines.append(record.final_response or "")
        lines.append("")

        lines.append("## 5. METRICS")
        lines.append(self.SECTION_END)
        lines.append(f"Duration: {record.total_duration_ms:.1f}ms")
        lines.append(f"429 Rate-limit hits: {record.rate_limit_429_count}")
        if record.rate_limit_429_by_tool:
            lines.append(f"429 by tool: {record.rate_limit_429_by_tool}")
        lines.append(f"Success: {record.success}")
        if record.error:
            lines.append(f"Error: {record.error}")

        return "\n".join(lines)

    def _write_to_file(self, record: AuditRecord) -> None:
        path = self.log_dir / f"{record.audit_id}.txt"
        path.write_text(self.format_for_llm(record))
