"""
Rich CLI dashboard for the employee document view.
Falls back to plain-text if `rich` is not installed.
"""

from __future__ import annotations

from models import Priority, ProcessedDocument

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.text import Text
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False


_PRIORITY_ICON = {
    Priority.HIGH:   "🔴",
    Priority.MEDIUM: "🟡",
    Priority.LOW:    "🟢",
}

_PRIORITY_COLOR = {
    Priority.HIGH:   "bold red",
    Priority.MEDIUM: "bold yellow",
    Priority.LOW:    "bold green",
}


def _priority_label(p: Priority) -> str:
    labels = {Priority.HIGH: "ВЫСОКИЙ", Priority.MEDIUM: "СРЕДНИЙ", Priority.LOW: "НИЗКИЙ"}
    return f"{_PRIORITY_ICON[p]} {labels[p]}"


def render_dashboard(
    docs: list[ProcessedDocument],
    employee_name: str = "Сотрудник",
    filter_priority: Priority | None = None,
) -> None:
    # Sort: HIGH first, then MEDIUM, then LOW, then by score desc
    order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    sorted_docs = sorted(docs, key=lambda d: (order[d.priority.priority], -d.priority.score))

    if filter_priority:
        sorted_docs = [d for d in sorted_docs if d.priority.priority == filter_priority]

    counts = {
        Priority.HIGH:   sum(1 for d in docs if d.priority.priority == Priority.HIGH),
        Priority.MEDIUM: sum(1 for d in docs if d.priority.priority == Priority.MEDIUM),
        Priority.LOW:    sum(1 for d in docs if d.priority.priority == Priority.LOW),
    }

    if _HAS_RICH:
        _render_rich(sorted_docs, employee_name, counts)
    else:
        _render_plain(sorted_docs, employee_name, counts)


def _render_rich(docs: list[ProcessedDocument], employee_name: str, counts: dict) -> None:
    console = Console()
    console.print()
    console.rule(f"[bold cyan]Дашборд: {employee_name}[/bold cyan]")
    console.print(
        f"  🔴 Высокий: [bold red]{counts[Priority.HIGH]}[/bold red]   "
        f"🟡 Средний: [bold yellow]{counts[Priority.MEDIUM]}[/bold yellow]   "
        f"🟢 Низкий: [bold green]{counts[Priority.LOW]}[/bold green]   "
        f"Всего: [bold]{len(docs)}[/bold]"
    )
    console.print()

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    table.add_column("#", width=3, justify="right")
    table.add_column("Приоритет", width=16)
    table.add_column("Тип документа", width=20)
    table.add_column("Отправитель", width=22)
    table.add_column("Срок", width=12)
    table.add_column("Сумма", width=18)
    table.add_column("Подпись", width=8, justify="center")
    table.add_column("Краткое содержание")

    for i, d in enumerate(docs, 1):
        a = d.analysis
        p = d.priority.priority
        color = _PRIORITY_COLOR[p]
        deadline_str = str(a.deadline) if a.deadline else "—"
        amounts_str = ", ".join(a.key_amounts[:2]) or "—"
        sig = "✓" if a.requires_signature else "—"

        table.add_row(
            str(i),
            Text(_priority_label(p), style=color),
            a.doc_type,
            a.sender[:20],
            deadline_str,
            amounts_str[:18],
            sig,
            a.summary[:80] + ("…" if len(a.summary) > 80 else ""),
        )

    console.print(table)
    console.print()


def _render_plain(docs: list[ProcessedDocument], employee_name: str, counts: dict) -> None:
    sep = "=" * 80
    print(f"\n{sep}")
    print(f"  ДАШБОРД: {employee_name}")
    print(f"  🔴 Высокий: {counts[Priority.HIGH]}  🟡 Средний: {counts[Priority.MEDIUM]}  🟢 Низкий: {counts[Priority.LOW]}  Всего: {len(docs)}")
    print(sep)

    for i, d in enumerate(docs, 1):
        a = d.analysis
        p = d.priority
        label = _priority_label(p.priority)
        print(f"\n[{i}] {label} | Счёт: {p.score:.2f}")
        print(f"    Тип:        {a.doc_type}")
        print(f"    Отправитель:{a.sender}")
        print(f"    Срок:       {a.deadline or '—'}")
        print(f"    Суммы:      {', '.join(a.key_amounts) or '—'}")
        print(f"    Подпись:    {'Требуется' if a.requires_signature else 'Нет'}")
        print(f"    Резюме:     {a.summary}")

    print(f"\n{sep}\n")


def render_routing_log(docs: list[ProcessedDocument]) -> None:
    """Show documents that were rerouted or left unassigned."""
    rerouted = [d for d in docs if not d.zone_match.in_zone]
    if not rerouted:
        return

    if _HAS_RICH:
        console = Console()
        console.print()
        console.rule("[bold magenta]Маршрутизация: перенаправленные документы[/bold magenta]")
        table = Table(box=box.SIMPLE, header_style="bold magenta", expand=True)
        table.add_column("ID")
        table.add_column("Тип")
        table.add_column("Отправитель")
        table.add_column("Уверенность")
        table.add_column("Причина")
        table.add_column("Предлагаемый получатель")

        for d in rerouted:
            zm = d.zone_match
            table.add_row(
                d.document.id,
                d.analysis.doc_type,
                d.analysis.sender,
                f"{zm.confidence:.0%}",
                zm.reason,
                zm.suggested_redirect or "Не определён → очередь «Нераспределено»",
            )
        console.print(table)
    else:
        print("\n--- Перенаправленные документы ---")
        for d in rerouted:
            zm = d.zone_match
            redirect = zm.suggested_redirect or "Нераспределено"
            print(f"  {d.document.id} → {redirect} (уверенность {zm.confidence:.0%}): {zm.reason}")
        print()
