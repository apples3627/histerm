from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shlex


DEFAULT_HISTORY_FILES = {
    "zsh": Path("~/.zsh_history").expanduser(),
    "bash": Path("~/.bash_history").expanduser(),
}

ZSH_EXTENDED_RE = re.compile(r"^: (\d+):\d+;(.*)$")
BASH_TIMESTAMP_RE = re.compile(r"^#(\d{10,})$")
ENV_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")
WRAPPER_COMMANDS = {"sudo", "doas", "env", "command", "nohup", "time", "builtin"}


@dataclass(slots=True)
class HistoryEntry:
    command: str
    timestamp: int | None = None


@dataclass(slots=True)
class FrequentEntry:
    key: str
    count: int
    sample: str


def detect_shell(explicit_shell: str | None = None, history_file: str | None = None) -> str:
    if explicit_shell in DEFAULT_HISTORY_FILES:
        return explicit_shell
    if history_file:
        filename = Path(history_file).name
        if "zsh" in filename:
            return "zsh"
        if "bash" in filename:
            return "bash"
    shell_path = os.environ.get("SHELL", "")
    if shell_path.endswith("zsh"):
        return "zsh"
    if shell_path.endswith("bash"):
        return "bash"
    for shell_name, path in DEFAULT_HISTORY_FILES.items():
        if path.exists():
            return shell_name
    return "zsh"


def resolve_history_file(shell_name: str, explicit_path: str | None = None) -> Path:
    if explicit_path:
        return Path(explicit_path).expanduser()
    histfile = os.environ.get("HISTFILE")
    if histfile:
        return Path(histfile).expanduser()
    return DEFAULT_HISTORY_FILES.get(shell_name, DEFAULT_HISTORY_FILES["zsh"])


def parse_history_lines(lines: list[str], shell_name: str) -> list[HistoryEntry]:
    if shell_name == "bash":
        return parse_bash_history(lines)
    return parse_zsh_history(lines)


def parse_zsh_history(lines: list[str]) -> list[HistoryEntry]:
    entries: list[HistoryEntry] = []
    pending_lines: list[str] = []
    pending_timestamp: int | None = None

    def flush() -> None:
        nonlocal pending_lines, pending_timestamp
        command = "\n".join(pending_lines).strip()
        if command:
            entries.append(HistoryEntry(command=command, timestamp=pending_timestamp))
        pending_lines = []
        pending_timestamp = None

    for line in lines:
        match = ZSH_EXTENDED_RE.match(line)
        if match:
            if pending_lines:
                flush()
            pending_timestamp = int(match.group(1))
            pending_lines = [match.group(2)]
            continue
        if pending_lines:
            pending_lines.append(line)
            continue
        stripped = line.strip()
        if stripped:
            pending_lines = [stripped]
    if pending_lines:
        flush()
    return entries


def parse_bash_history(lines: list[str]) -> list[HistoryEntry]:
    entries: list[HistoryEntry] = []
    pending_timestamp: int | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        match = BASH_TIMESTAMP_RE.match(stripped)
        if match:
            pending_timestamp = int(match.group(1))
            continue
        entries.append(HistoryEntry(command=stripped, timestamp=pending_timestamp))
        pending_timestamp = None
    return entries


def load_history(history_file: Path, shell_name: str, scan_limit: int = 5000) -> list[HistoryEntry]:
    try:
        raw = history_file.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return []
    lines = raw.splitlines()
    if scan_limit > 0 and len(lines) > scan_limit * 4:
        lines = lines[-(scan_limit * 4) :]
    entries = parse_history_lines(lines, shell_name)
    if scan_limit > 0 and len(entries) > scan_limit:
        entries = entries[-scan_limit:]
    return entries


def recent_entries(
    entries: list[HistoryEntry],
    limit: int,
    *,
    dedupe: bool = False,
) -> list[HistoryEntry]:
    results: list[HistoryEntry] = []
    seen: set[str] = set()
    for entry in reversed(entries):
        command = entry.command.strip()
        if not command:
            continue
        if dedupe and command in seen:
            continue
        seen.add(command)
        results.append(entry)
        if len(results) >= limit:
            break
    return results


def frequent_entries(entries: list[HistoryEntry], limit: int) -> list[FrequentEntry]:
    counts: Counter[str] = Counter()
    latest_sample: dict[str, str] = {}
    latest_index: dict[str, int] = {}

    for index, entry in enumerate(entries):
        key = command_key(entry.command)
        if not key:
            continue
        counts[key] += 1
        latest_sample[key] = entry.command
        latest_index[key] = index

    ordered = sorted(
        counts.items(),
        key=lambda item: (-item[1], -latest_index[item[0]], item[0]),
    )
    return [
        FrequentEntry(key=key, count=count, sample=latest_sample[key])
        for key, count in ordered[:limit]
    ]


def command_key(command: str) -> str:
    stripped = command.strip()
    if not stripped:
        return ""
    try:
        tokens = shlex.split(stripped, posix=True)
    except ValueError:
        tokens = stripped.split()
    if not tokens:
        return ""
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if ENV_ASSIGNMENT_RE.match(token):
            index += 1
            continue
        if token in WRAPPER_COMMANDS:
            index += 1
            continue
        return Path(token).name
    return Path(tokens[0]).name

