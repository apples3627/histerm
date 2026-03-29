from __future__ import annotations

from dataclasses import dataclass
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistermConfig":
        config = cls()
        if isinstance(data.get("limit"), int) and data["limit"] > 0:
            config.limit = data["limit"]
        if data.get("initial_tab") in {"recent", "frequent"}:
            config.initial_tab = data["initial_tab"]
        if isinstance(data.get("history_file"), str) and data["history_file"].strip():
            config.history_file = data["history_file"]
        if isinstance(data.get("scan_limit"), int) and data["scan_limit"] > 0:
            config.scan_limit = data["scan_limit"]
        if isinstance(data.get("dedupe_recent"), bool):
            config.dedupe_recent = data["dedupe_recent"]
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

