from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class Priority(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DocumentStatus(Enum):
    NEW = "new"
    ROUTED = "routed"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNASSIGNED = "unassigned"


@dataclass
class Document:
    id: str
    filename: str
    raw_text: str
    received_at: str = ""
    status: DocumentStatus = DocumentStatus.NEW
    assigned_to: Optional[str] = None


@dataclass
class AnalysisResult:
    doc_id: str
    doc_type: str
    sender: str
    subject: str
    summary: str
    key_amounts: list[str]
    deadline: Optional[date]
    requires_signature: bool
    is_regulatory: bool
    is_legal: bool
    is_repeat: bool
    counterparty_tier: str  # "key", "regular", "unknown"
    raw_thinking: str = ""


@dataclass
class ZoneMatch:
    doc_id: str
    employee_id: str
    in_zone: bool
    confidence: float  # 0.0 – 1.0
    reason: str
    suggested_redirect: Optional[str] = None


@dataclass
class PriorityResult:
    doc_id: str
    priority: Priority
    score: float
    breakdown: dict[str, float]


@dataclass
class ZoneProfile:
    employee_id: str
    name: str
    department: str
    keywords: list[str] = field(default_factory=list)
    doc_types: list[str] = field(default_factory=list)
    counterparties: list[str] = field(default_factory=list)


@dataclass
class ProcessedDocument:
    document: Document
    analysis: AnalysisResult
    zone_match: ZoneMatch
    priority: PriorityResult
