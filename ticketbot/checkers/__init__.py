from dataclasses import dataclass


@dataclass
class CheckResult:
    available: bool
    summary: str | None = None
    error: str | None = None
