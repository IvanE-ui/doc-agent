"""
main.py — CLI entry point.

Usage examples:
  python main.py demo                        # Run demo with built-in sample documents
  python main.py file invoice.pdf            # Analyse a single file
  python main.py folder ./inbox              # Analyse all documents in a folder
  python main.py demo --employee petrov_dm   # Demo filtered to finance department
"""

import argparse
import json
import sys
from pathlib import Path

from config import ANTHROPIC_API_KEY
from dashboard import render_dashboard, render_routing_log
from models import ZoneProfile
from pipeline import process_file, process_texts


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".eml", ".msg", ".txt"}


def load_profiles(config_path: str = "zones_config.json") -> list[ZoneProfile]:
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)
    return [ZoneProfile(**item) for item in data]


def run_demo(employee_id: str, filter_priority=None) -> None:
    from demo_documents import SAMPLE_DOCUMENTS

    profiles = load_profiles()
    profile = next((p for p in profiles if p.employee_id == employee_id), profiles[0])

    print(f"\nЗапуск демо для: {profile.name} ({profile.department})")
    print(f"Документов в очереди: {len(SAMPLE_DOCUMENTS)}\n")

    results = process_texts(SAMPLE_DOCUMENTS, profiles, employee_id)

    # Split: mine vs. rerouted
    mine = [r for r in results if r.zone_match.in_zone]
    rerouted = [r for r in results if not r.zone_match.in_zone]

    render_dashboard(mine, employee_name=profile.name, filter_priority=filter_priority)
    render_routing_log(rerouted)


def run_file(filepath: str, employee_id: str) -> None:
    if not Path(filepath).exists():
        print(f"Ошибка: файл не найден — {filepath}", file=sys.stderr)
        sys.exit(1)

    profiles = load_profiles()
    result = process_file(filepath, profiles, employee_id)
    render_dashboard([result], employee_name=employee_id)
    render_routing_log([result])


def run_folder(folder: str, employee_id: str) -> None:
    p = Path(folder)
    if not p.is_dir():
        print(f"Ошибка: папка не найдена — {folder}", file=sys.stderr)
        sys.exit(1)

    files = [f for f in p.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not files:
        print(f"Нет поддерживаемых файлов в {folder}")
        return

    profiles = load_profiles()
    results = []
    for i, f in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Обработка: {f.name}")
        results.append(process_file(str(f), profiles, employee_id))

    mine = [r for r in results if r.zone_match.in_zone]
    rerouted = [r for r in results if not r.zone_match.in_zone]
    render_dashboard(mine, employee_name=employee_id)
    render_routing_log(rerouted)


def main() -> None:
    if not ANTHROPIC_API_KEY:
        print("Ошибка: установите переменную окружения ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="AI-агент приоритизации входящих документов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("command", choices=["demo", "file", "folder"])
    parser.add_argument("target", nargs="?", default="", help="Путь к файлу или папке")
    parser.add_argument(
        "--employee",
        default="ivanova_av",
        help="ID сотрудника из zones_config.json (по умолчанию: ivanova_av)",
    )
    parser.add_argument(
        "--priority",
        choices=["HIGH", "MEDIUM", "LOW"],
        default=None,
        help="Фильтр по приоритету",
    )

    args = parser.parse_args()

    from models import Priority
    filter_p = Priority[args.priority] if args.priority else None

    if args.command == "demo":
        run_demo(args.employee, filter_priority=filter_p)
    elif args.command == "file":
        if not args.target:
            parser.error("Укажите путь к файлу: python main.py file <path>")
        run_file(args.target, args.employee)
    elif args.command == "folder":
        if not args.target:
            parser.error("Укажите папку: python main.py folder <path>")
        run_folder(args.target, args.employee)


if __name__ == "__main__":
    main()
