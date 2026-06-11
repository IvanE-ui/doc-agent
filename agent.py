"""
Claude-powered document analysis agent.
Uses adaptive thinking for deep structured extraction.
"""

import json
import re
from datetime import date, datetime
from typing import Optional

import anthropic

from config import ANTHROPIC_API_KEY, MODEL
from models import AnalysisResult, Document


_ANALYSIS_SCHEMA = """{
  "doc_type": "тип документа (договор/счёт/приказ/письмо/претензия/акт/исполнительный лист/предписание/судебный/регуляторный/иное)",
  "sender": "наименование отправителя / контрагента",
  "subject": "тема или заголовок документа",
  "summary": "краткое содержание в 2-3 предложениях",
  "key_amounts": ["список сумм с валютами, например '1 500 000 руб.'"],
  "deadline": "дата в формате YYYY-MM-DD или null",
  "requires_signature": true or false,
  "is_regulatory": true or false,
  "is_legal": true or false,
  "is_repeat": true or false,
  "counterparty_tier": "key или regular или unknown"
}"""

_SYSTEM_PROMPT = f"""Ты — аналитик входящих документов организации.
Твоя задача: внимательно прочитать текст документа и извлечь структурированные данные.

Верни ТОЛЬКО валидный JSON строго по схеме ниже. Без пояснений, без markdown-обёртки.

Схема:
{_ANALYSIS_SCHEMA}

Правила:
- doc_type: выбери наиболее точный тип из предложенных
- deadline: дата ответа / оплаты / согласования; null если не указана
- is_regulatory: true если документ от регулятора (ФНС, ЦБ, Роспотребнадзор и т.д.)
- is_legal: true если это судебный акт, исполнительный лист, претензия, иск
- is_repeat: true если в тексте упоминается «повторно», «напоминание», «reminder»
- counterparty_tier: «key» — если контрагент явно стратегический/ключевой, «regular» — обычный, «unknown» — не определить
"""


def analyse_document(doc: Document) -> AnalysisResult:
    """Call Claude with adaptive thinking to extract document metadata."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    from document_parser import truncate_for_llm
    text = truncate_for_llm(doc.raw_text)

    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Проанализируй следующий документ:\n\n{text}",
            }
        ],
    ) as stream:
        response = stream.get_final_message()

    thinking_text = ""
    json_text = ""

    for block in response.content:
        if block.type == "thinking":
            thinking_text = getattr(block, "thinking", "") or getattr(block, "summary", "")
        elif block.type == "text":
            json_text = block.text

    data = _parse_json(json_text)
    deadline = _parse_date(data.get("deadline"))

    return AnalysisResult(
        doc_id=doc.id,
        doc_type=data.get("doc_type", "неизвестно"),
        sender=data.get("sender", "неизвестно"),
        subject=data.get("subject", ""),
        summary=data.get("summary", ""),
        key_amounts=data.get("key_amounts", []),
        deadline=deadline,
        requires_signature=bool(data.get("requires_signature", False)),
        is_regulatory=bool(data.get("is_regulatory", False)),
        is_legal=bool(data.get("is_legal", False)),
        is_repeat=bool(data.get("is_repeat", False)),
        counterparty_tier=data.get("counterparty_tier", "unknown"),
        raw_thinking=thinking_text,
    )


def _parse_json(text: str) -> dict:
    """Extract JSON even if the model wrapped it in backticks."""
    text = text.strip()
    # Strip markdown code fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        text = match.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON object in the text
        match = re.search(r"\{[\s\S]+\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return {}


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value or value == "null":
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None
