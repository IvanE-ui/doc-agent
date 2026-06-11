"""
Responsibility zone matching: decide if a document belongs to an employee's zone.
"""

from models import AnalysisResult, ZoneMatch, ZoneProfile


def match_zone(analysis: AnalysisResult, profile: ZoneProfile) -> ZoneMatch:
    """
    Rule-based zone matching scored 0–1.
    Returns in_zone=True when confidence >= 0.5.
    """
    score = 0.0
    reasons = []

    # --- Document type match ---
    doc_type_lower = analysis.doc_type.lower()
    for dt in profile.doc_types:
        if dt.lower() in doc_type_lower or doc_type_lower in dt.lower():
            score += 0.4
            reasons.append(f"тип документа '{analysis.doc_type}' входит в профиль")
            break

    # --- Keyword match (subject + summary + sender) ---
    haystack = " ".join([
        analysis.subject,
        analysis.summary,
        analysis.sender,
        analysis.doc_type,
    ]).lower()

    matched_keywords = [kw for kw in profile.keywords if kw.lower() in haystack]
    if matched_keywords:
        kw_score = min(0.4, 0.15 * len(matched_keywords))
        score += kw_score
        reasons.append(f"ключевые слова: {', '.join(matched_keywords)}")

    # --- Counterparty match ---
    sender_lower = analysis.sender.lower()
    for cp in profile.counterparties:
        if cp.lower() in sender_lower or sender_lower in cp.lower():
            score += 0.2
            reasons.append(f"контрагент '{analysis.sender}' в профиле")
            break

    score = min(score, 1.0)
    in_zone = score >= 0.5

    return ZoneMatch(
        doc_id=analysis.doc_id,
        employee_id=profile.employee_id,
        in_zone=in_zone,
        confidence=round(score, 2),
        reason="; ".join(reasons) if reasons else "нет совпадений с профилем",
    )


def find_best_zone(
    analysis: AnalysisResult,
    profiles: list[ZoneProfile],
) -> tuple[ZoneMatch, list[ZoneMatch]]:
    """
    Match against all profiles. Return (best_match, all_matches).
    If best confidence < 0.5, in_zone=False → document goes to unassigned queue.
    """
    results = [match_zone(analysis, p) for p in profiles]
    results.sort(key=lambda r: r.confidence, reverse=True)

    best = results[0] if results else ZoneMatch(
        doc_id=analysis.doc_id,
        employee_id="unassigned",
        in_zone=False,
        confidence=0.0,
        reason="нет профилей",
    )

    # Attach redirect suggestion: second-best if best is out-of-zone
    if not best.in_zone and len(results) >= 2:
        second = results[1]
        if second.confidence > 0.2:
            best.suggested_redirect = second.employee_id

    return best, results
