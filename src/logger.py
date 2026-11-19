"""Structured JSON logger for tracking orchestration traces, tool execution, and errors."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredLogger:
    """Writes JSON Lines events to log files and standard output."""

    def __init__(self, log_file: Optional[str] = "logs/orchestrator.jsonl", console: bool = True):
        self.console = console
        self.log_path = Path(log_file) if log_file else None
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: str, message: str, payload: Optional[Dict[str, Any]] = None, level: str = "INFO"):
        """Emits a structured JSON log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "event": event_type,
            "message": message,
            "payload": payload or {},
        }
        json_line = json.dumps(entry, default=str)

        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json_line + "\n")

        if self.console:
            print(f"[{entry['level']}] [{entry['event']}] {entry['message']}")
