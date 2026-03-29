from __future__ import annotations

import argparse
import curses
from pathlib import Path
import sys

from histerm.config import DEFAULT_CONFIG_PATH, HistermConfig, load_config, save_favorites
from histerm.history import (
    detect_shell,
    frequent_entries,
    load_history,
    recent_entries,
    resolve_history_file,
)
from histerm.integration import SUPPORTED_SHELLS, load_shell_integration
from histerm.tui import HistermUI


def build_picker_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Popup shell history picker",
        epilog="Shell integration: histerm init {bash,zsh}",
    )
    parser.add_argument("--config", type=Path, help="Path to config JSON file")
    parser.add_argument("--no-config", action="store_true", help="Ignore config file")
    parser.add_argument("--limit", type=int, help="Number of items per tab")
    parser.add_argument(
        "--tab",
        choices=["recent", "frequent", "favorites"],
        help="Initial tab",
    )
    parser.add_argument("--shell", choices=["zsh", "bash"], help="History format to parse")
    parser.add_argument("--history-file", help="Explicit history file path")
    parser.add_argument("--scan-limit", type=int, help="Maximum parsed history entries")
    parser.add_argument(
        "--dedupe-recent",
        action="store_true",
        help="Hide duplicates in the recent tab",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="Write the selected command to a file instead of stdout",
    )
    return parser


def build_init_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="histerm init",
        description="Print shell integration for histerm",
    )
    parser.add_argument("shell", choices=sorted(SUPPORTED_SHELLS))
    return parser


def run_picker(argv: list[str]) -> int:
    parser = build_picker_parser()
    args = parser.parse_args(argv)

    config_path = None if args.no_config else args.config or DEFAULT_CONFIG_PATH
    config = HistermConfig() if args.no_config else load_config(config_path)

    limit = args.limit if args.limit and args.limit > 0 else config.limit
    initial_tab = args.tab or config.initial_tab
    history_file_arg = args.history_file or config.history_file
    shell_name = detect_shell(args.shell, history_file_arg)
    history_file = resolve_history_file(shell_name, history_file_arg)
    scan_limit = args.scan_limit if args.scan_limit and args.scan_limit > 0 else config.scan_limit
    dedupe_recent = args.dedupe_recent or config.dedupe_recent

    entries = load_history(history_file, shell_name, scan_limit=scan_limit)
    recent = recent_entries(entries, limit, dedupe=dedupe_recent)
    frequent = frequent_entries(entries, limit)

    ui = HistermUI(
        recent,
        frequent,
        favorites=config.favorites,
        initial_tab=initial_tab,
        history_file=history_file,
        config_file=config_path,
        save_favorites_callback=(
            None if config_path is None else lambda favorites: save_favorites(favorites, config_path)
        ),
    )
    try:
        selected = curses.wrapper(ui.run)
    except curses.error:
        print("histerm requires an interactive terminal.", file=sys.stderr)
        return 1

    if not selected:
        return 0

    if args.output_file:
        args.output_file.write_text(selected, encoding="utf-8")
    else:
        print(selected)
    return 0


def run_init(argv: list[str]) -> int:
    parser = build_init_parser()
    args = parser.parse_args(argv)
    sys.stdout.write(load_shell_integration(args.shell))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "init":
        return run_init(argv[1:])
    return run_picker(argv)
