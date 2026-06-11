import os

# Claude model to use for document analysis
MODEL = "claude-opus-4-8"

# Anthropic API key — set via environment variable
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Priority scoring weights (must sum to 1.0)
WEIGHTS = {
    "deadline":      0.35,
    "doc_type":      0.30,
    "amount":        0.15,
    "counterparty":  0.12,
    "repeat":        0.08,
}

# Days-until-deadline thresholds for scoring
DEADLINE_THRESHOLDS = {
    "overdue":   1.0,
    "today":     0.9,
    "1_day":     0.8,
    "3_days":    0.6,
    "7_days":    0.4,
    "14_days":   0.2,
    "far":       0.0,
}

# High-priority document types
HIGH_PRIORITY_TYPES = {"судебный", "регуляторный", "исполнительный лист", "предписание", "претензия"}
MEDIUM_PRIORITY_TYPES = {"договор", "счёт", "акт", "приказ", "соглашение"}

# Counterparty tier scores
COUNTERPARTY_SCORES = {"key": 1.0, "regular": 0.5, "unknown": 0.1}

# Priority thresholds (score 0–1)
PRIORITY_HIGH_THRESHOLD = 0.65
PRIORITY_MEDIUM_THRESHOLD = 0.35
