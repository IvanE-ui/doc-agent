"""
End-to-end document processing pipeline.
Orchestrates: parse → analyse → match zone → prioritise → route.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from agent import analyse_document
from document_parser import extract_text
from models import Document, DocumentStatus, ProcessedDocument
from prioritizer import calculate_priority
from zone_matcher import find_best_zone, ZoneProfile


def process_file(
    filepath: str,
    profiles: list[ZoneProfile],
    current_employee_id: str,
    doc_id: Optional[str] = None,
) -> ProcessedDocument:
    """Process a single document file through the full pipeline."""
    doc_id = doc_id or str(uuid.uuid4())[:8]
    text = extract_text(filepath)

    doc = Document(
        id=doc_id,
        filename=Path(filepath).name,
        raw_text=text,
    )

    print(f"  [→] Анализ '{doc.filename}'...")
    analysis = analyse_document(doc)

    print(f"  [→] Определение зоны ответственности...")
    best_match, all_matches = find_best_zone(analysis, profiles)

    if not best_match.in_zone:
        doc.status = DocumentStatus.ROUTED if best_match.suggested_redirect else DocumentStatus.UNASSIGNED
        doc.assigned_to = best_match.suggested_redirect
    else:
        doc.status = DocumentStatus.PENDING
        doc.assigned_to = current_employee_id

    print(f"  [→] Расчёт приоритета...")
    priority = calculate_priority(analysis)

    return ProcessedDocument(
        document=doc,
        analysis=analysis,
        zone_match=best_match,
        priority=priority,
    )


def process_texts(
    texts: dict[str, str],
    profiles: list[ZoneProfile],
    current_employee_id: str,
) -> list[ProcessedDocument]:
    """
    Process a dict of {doc_id: raw_text} without file I/O.
    Useful for demo and testing.
    """
    results = []
    for doc_id, raw_text in texts.items():
        doc = Document(id=doc_id, filename=doc_id, raw_text=raw_text)
        print(f"  [→] Анализ '{doc_id}'...")
        analysis = analyse_document(doc)

        print(f"  [→] Зона ответственности...")
        best_match, _ = find_best_zone(analysis, profiles)

        if not best_match.in_zone:
            doc.status = DocumentStatus.ROUTED if best_match.suggested_redirect else DocumentStatus.UNASSIGNED
            doc.assigned_to = best_match.suggested_redirect
        else:
            doc.status = DocumentStatus.PENDING
            doc.assigned_to = current_employee_id

        print(f"  [→] Приоритет...")
        priority = calculate_priority(analysis)

        results.append(ProcessedDocument(
            document=doc,
            analysis=analysis,
            zone_match=best_match,
            priority=priority,
        ))

    return results
