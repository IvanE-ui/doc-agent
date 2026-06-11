"""
Document priority scoring based on weighted criteria from the PRD.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from config import (
    COUNTERPARTY_SCORES,
    DEADLINE_THRESHOLDS,
    HIGH_PRIORITY_TYPES,
    MEDIUM_PRIORITY_TYPES,
    PRIORITY_HIGH_THRESHOLD,
    PRIORITY_MEDIUM_THRESHOLD,
    WEIGHTS,
)
from models import AnalysisResult, Priority, PriorityResult


def score_deadline(deadline: Optional[date], today: Optional[date] = None) -> float:
    if deadline is None:
        return 0.0
    today = today or date.today()
    days = (deadline - today).days
    if days <= 0:
        return DEADLINE_THRESHOLDS["overdue"]
    elif days == 0:
        return DEADLINE_THRESHOLDS["today"]
    elif days <= 1:
        return DEADLINE_THRESHOLDS["1_day"]
    elif days <= 3:
        return DEADLINE_THRESHOLDS["3_days"]
    elif days <= 7:
        return DEADLINE_THRESHOLDS["7_days"]
    elif days <= 14:
        return DEADLINE_THRESHOLDS["14_days"]
    return DEADLINE_THRESHOLDS["far"]


def score_doc_type(analysis: AnalysisResult) -> float:
    dt = analysis.doc_type.lower()
    if analysis.is_regulatory or analysis.is_legal:
        return 1.0
    for t in HIGH_PRIORITY_TYPES:
        if t in dt:
            return 1.0
    for t in MEDIUM_PRIORITY_TYPES:
        if t in dt:
            return 0.5
    return 0.1


def score_amount(amounts: list[str]) -> float:
    """Higher score for larger declared amounts."""
    if not amounts:
        return 0.0
    max_val = 0.0
    for a in amounts:
        digits = "".join(c for c in a if c.isdigit() or c == ".")
        try:
            val = float(digits)
            if val > max_val:
                max_val = val
        except ValueError:
            pass
    if max_val >= 10_000_000:
        return 1.0
    elif max_val >= 1_000_000:
        return 0.7
    elif max_val >= 100_000:
        return 0.4
    elif max_val > 0:
        return 0.2
    return 0.0


def score_counterparty(tier: str) -> float:
    return COUNTERPARTY_SCORES.get(tier, 0.1)


def score_repeat(is_repeat: bool) -> float:
    return 0.5 if is_repeat else 0.0


def calculate_priority(analysis: AnalysisResult) -> PriorityResult:
    breakdown = {
        "deadline":     score_deadline(analysis.deadline),
        "doc_type":     score_doc_type(analysis),
        "amount":       score_amount(analysis.key_amounts),
        "counterparty": score_counterparty(analysis.counterparty_tier),
        "repeat":       score_repeat(analysis.is_repeat),
    }

    total = sum(WEIGHTS[k] * v for k, v in breakdown.items())

    # Require-signature bump
    if analysis.requires_signature:
        total = min(1.0, total + 0.05)

    if total >= PRIORITY_HIGH_THRESHOLD:
        priority = Priority.HIGH
    elif total >= PRIORITY_MEDIUM_THRESHOLD:
        priority = Priority.MEDIUM
    else:
        priority = Priority.LOW

    return PriorityResult(
        doc_id=analysis.doc_id,
        priority=priority,
        score=round(total, 3),
        breakdown={k: round(v, 3) for k, v in breakdown.items()},
    )
