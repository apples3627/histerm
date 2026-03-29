from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("~/.config/histerm/config.json").expanduser()


@dataclass(slots=True)
class HistermConfig:
    limit: int = 10
    initial_tab: str = "recent"
    history_file: str | None = None
    scan_limit: int = 5000
    dedupe_recent: bool = False
    favorites: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistermConfig":
        config = cls()
        if isinstance(data.get("limit"), int) and data["limit"] > 0:
            config.limit = data["limit"]
        if data.get("initial_tab") in {"recent", "frequent", "favorites"}:
            config.initial_tab = data["initial_tab"]
        if isinstance(data.get("history_file"), str) and data["history_file"].strip():
            config.history_file = data["history_file"]
        if isinstance(data.get("scan_limit"), int) and data["scan_limit"] > 0:
            config.scan_limit = data["scan_limit"]
        if isinstance(data.get("dedupe_recent"), bool):
            config.dedupe_recent = data["dedupe_recent"]
        favorites = data.get("favorites")
        if isinstance(favorites, list):
            config.favorites = normalize_favorites(favorites)
        return config


def load_config(path: Path | None = None) -> HistermConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return HistermConfig()
    except json.JSONDecodeError:
        return HistermConfig()
    if not isinstance(raw, dict):
        return HistermConfig()
    return HistermConfig.from_dict(raw)


def normalize_favorites(items: list[Any]) -> list[str]:
    favorites: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, str):
            continue
        command = item.strip()
        if not command or command in seen:
            continue
        favorites.append(command)
        seen.add(command)
    return favorites


def save_favorites(favorites: list[str], path: Path | None = None) -> None:
    config_path = path or DEFAULT_CONFIG_PATH
    raw: dict[str, Any] = {}
    try:
        existing = json.loads(config_path.read_text(encoding="utf-8"))
        if isinstance(existing, dict):
            raw = existing
    except (FileNotFoundError, json.JSONDecodeError):
        raw = {}

    raw["favorites"] = normalize_favorites(favorites)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(raw, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
