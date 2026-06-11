"""
Flask web prototype for the document prioritization agent.
Uses mock data so it works without an API key.
"""

from flask import Flask, render_template, jsonify, request
from datetime import date, timedelta
import json, uuid, os

app = Flask(__name__)

today = date.today()

# ── Mock document data ──────────────────────────────────────────────────────
MOCK_DOCS = [
    {
        "id": "doc_001",
        "filename": "pretenziya_2026_47.pdf",
        "doc_type": "Претензия",
        "sender": "ООО «Арбитражный партнёр»",
        "subject": "Претензия по договору поставки №2025-153",
        "summary": "Требование погасить задолженность 1 750 000 руб. по договору поставки. В случае отказа — подача иска в Арбитражный суд г. Москвы.",
        "amounts": ["1 750 000 руб.", "3 500 000 руб."],
        "deadline": str(today + timedelta(days=1)),
        "requires_signature": False,
        "is_legal": True,
        "is_regulatory": False,
        "is_repeat": False,
        "counterparty_tier": "key",
        "priority": "HIGH",
        "score": 0.91,
        "in_zone": True,
        "zone_employee": "ivanova_av",
        "zone_name": "Иванова А.В.",
        "department": "Юридический отдел",
        "status": "new",
    },
    {
        "id": "doc_002",
        "filename": "predpisanie_FNS_0112.pdf",
        "doc_type": "Предписание",
        "sender": "ИФНС России №7 по г. Москве",
        "subject": "Предписание о предоставлении пояснений по НДС",
        "summary": "ФНС выявила расхождения в декларации по НДС за II квартал 2026. Требует предоставить пояснения и документы. Штраф за непредставление — 200 руб. за документ.",
        "amounts": [],
        "deadline": str(today),
        "requires_signature": False,
        "is_legal": False,
        "is_regulatory": True,
        "is_repeat": False,
        "counterparty_tier": "key",
        "priority": "HIGH",
        "score": 0.88,
        "in_zone": True,
        "zone_employee": "ivanova_av",
        "zone_name": "Иванова А.В.",
        "department": "Юридический отдел",
        "status": "new",
    },
    {
        "id": "doc_003",
        "filename": "dogovor_postavki_201.docx",
        "doc_type": "Договор поставки",
        "sender": "ООО «МеталлСтрой»",
        "subject": "Договор поставки металлопроката №2026-201",
        "summary": "Договор на поставку арматуры и швеллера на сумму 2 800 000 руб. Требует подписи. Аванс 50% в течение 3 дней, итоговая оплата через 10 дней.",
        "amounts": ["2 800 000 руб."],
        "deadline": str(today + timedelta(days=3)),
        "requires_signature": True,
        "is_legal": False,
        "is_regulatory": False,
        "is_repeat": False,
        "counterparty_tier": "regular",
        "priority": "HIGH",
        "score": 0.72,
        "in_zone": True,
        "zone_employee": "ivanova_av",
        "zone_name": "Иванова А.В.",
        "department": "Юридический отдел",
        "status": "new",
    },
    {
        "id": "doc_004",
        "filename": "schet_techsnab_0589.pdf",
        "doc_type": "Счёт на оплату",
        "sender": "ООО «ТехСнаб»",
        "subject": "Счёт №2026-0589 на офисное оборудование",
        "summary": "Счёт на поставку 15 единиц офисного оборудования на сумму 485 000 руб. включая НДС. Срок оплаты через 10 дней.",
        "amounts": ["485 000 руб.", "НДС 80 833 руб."],
        "deadline": str(today + timedelta(days=10)),
        "requires_signature": False,
        "is_legal": False,
        "is_regulatory": False,
        "is_repeat": False,
        "counterparty_tier": "regular",
        "priority": "MEDIUM",
        "score": 0.44,
        "in_zone": False,
        "zone_employee": "petrov_dm",
        "zone_name": "Петров Д.М.",
        "department": "Финансовый отдел",
        "status": "routed",
    },
    {
        "id": "doc_005",
        "filename": "zayavka_romashka_povtorno.eml",
        "doc_type": "Заявка на поставку",
        "sender": "ГК «Ромашка»",
        "subject": "Заявка на поставку комплектующих — повторно",
        "summary": "Повторная заявка на поставку подшипников, уплотнительных колец и смазочных материалов на общую сумму 190 000 руб. Ожидают подтверждения срока поставки.",
        "amounts": ["190 000 руб."],
        "deadline": None,
        "requires_signature": False,
        "is_legal": False,
        "is_regulatory": False,
        "is_repeat": True,
        "counterparty_tier": "regular",
        "priority": "MEDIUM",
        "score": 0.38,
        "in_zone": False,
        "zone_employee": "sidorova_ev",
        "zone_name": "Сидорова Е.В.",
        "department": "Отдел снабжения",
        "status": "routed",
    },
    {
        "id": "doc_006",
        "filename": "pismo_consulting_plus.eml",
        "doc_type": "Информационное письмо",
        "sender": "ООО «Консалтинг Плюс»",
        "subject": "Изменение юридического адреса",
        "summary": "Уведомление об изменении юридического адреса компании с 01.07.2026. Банковские реквизиты остаются прежними. Действий не требует.",
        "amounts": [],
        "deadline": None,
        "requires_signature": False,
        "is_legal": False,
        "is_regulatory": False,
        "is_repeat": False,
        "counterparty_tier": "unknown",
        "priority": "LOW",
        "score": 0.08,
        "in_zone": True,
        "zone_employee": "ivanova_av",
        "zone_name": "Иванова А.В.",
        "department": "Юридический отдел",
        "status": "new",
    },
]

EMPLOYEES = {
    "ivanova_av": {"name": "Иванова Анна Владимировна", "dept": "Юридический отдел", "avatar": "ИА"},
    "petrov_dm":  {"name": "Петров Дмитрий Михайлович", "dept": "Финансовый отдел",  "avatar": "ПД"},
    "sidorova_ev":{"name": "Сидорова Елена Викторовна", "dept": "Отдел снабжения",   "avatar": "СЕ"},
}

doc_statuses = {d["id"]: d["status"] for d in MOCK_DOCS}


@app.route("/")
def index():
    employee_id = request.args.get("employee", "ivanova_av")
    emp = EMPLOYEES.get(employee_id, EMPLOYEES["ivanova_av"])
    return render_template("dashboard.html", employee=emp, employee_id=employee_id, employees=EMPLOYEES)


@app.route("/api/docs")
def api_docs():
    employee_id = request.args.get("employee", "ivanova_av")
    priority_filter = request.args.get("priority", "ALL")

    mine = [d for d in MOCK_DOCS if d["in_zone"] and d["zone_employee"] == employee_id]
    rerouted = [d for d in MOCK_DOCS if not d["in_zone"]]

    if priority_filter != "ALL":
        mine = [d for d in mine if d["priority"] == priority_filter]

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    mine.sort(key=lambda d: (order[d["priority"]], -d["score"]))

    # Attach live status
    for d in mine + rerouted:
        d = d.copy()
        d["status"] = doc_statuses.get(d["id"], d["status"])

    return jsonify({
        "mine": mine,
        "rerouted": rerouted,
        "stats": {
            "HIGH":   sum(1 for d in mine if d["priority"] == "HIGH"),
            "MEDIUM": sum(1 for d in mine if d["priority"] == "MEDIUM"),
            "LOW":    sum(1 for d in mine if d["priority"] == "LOW"),
            "total":  len(mine),
            "rerouted": len(rerouted),
        }
    })


@app.route("/api/action", methods=["POST"])
def api_action():
    data = request.json
    doc_id = data.get("doc_id")
    action = data.get("action")  # approve | reject | reroute

    if doc_id in doc_statuses:
        if action == "approve":
            doc_statuses[doc_id] = "approved"
        elif action == "reject":
            doc_statuses[doc_id] = "rejected"
        elif action == "reroute":
            doc_statuses[doc_id] = "routed"

    return jsonify({"ok": True, "doc_id": doc_id, "new_status": doc_statuses.get(doc_id)})


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Simulate document upload and analysis."""
    import time, random
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "no file"}), 400

    # Simulate processing delay
    fake_types = ["Договор", "Счёт на оплату", "Письмо", "Акт", "Претензия"]
    fake_senders = ["ООО «Новый Партнёр»", "ИП Сидоров", "АО «Технологии»"]
    doc_type = random.choice(fake_types)
    priority = random.choice(["HIGH", "MEDIUM", "LOW"])

    new_doc = {
        "id": f"doc_{uuid.uuid4().hex[:6]}",
        "filename": file.filename,
        "doc_type": doc_type,
        "sender": random.choice(fake_senders),
        "subject": f"{doc_type} от {random.choice(fake_senders)}",
        "summary": f"Документ типа «{doc_type}» загружен и проанализирован AI-агентом. Требует рассмотрения.",
        "amounts": [f"{random.randint(10, 5000) * 1000:,} руб.".replace(",", " ")],
        "deadline": str(today + timedelta(days=random.randint(1, 14))),
        "requires_signature": random.choice([True, False]),
        "is_legal": doc_type == "Претензия",
        "is_regulatory": False,
        "is_repeat": False,
        "counterparty_tier": random.choice(["key", "regular", "unknown"]),
        "priority": priority,
        "score": round(random.uniform(0.3, 0.95), 2),
        "in_zone": True,
        "zone_employee": "ivanova_av",
        "zone_name": "Иванова А.В.",
        "department": "Юридический отдел",
        "status": "new",
        "analyzed": True,
    }
    MOCK_DOCS.insert(0, new_doc)
    doc_statuses[new_doc["id"]] = "new"
    return jsonify(new_doc)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
