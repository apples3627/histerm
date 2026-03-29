from __future__ import annotations

import curses
from pathlib import Path
import unittest
from unittest.mock import patch

from histerm.tui import HistermUI


class FakeWindow:
    def __init__(self, height: int = 24, width: int = 80) -> None:
        self.height = height
        self.width = width
        self.calls: list[tuple[int, int, str]] = []

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def erase(self) -> None:
        return None

    def refresh(self) -> None:
        return None

    def derwin(self, height: int, width: int, start_y: int, start_x: int) -> "FakeWindow":
        return self

    def box(self) -> None:
        return None

    def addstr(self, y: int, x: int, text: str, attr: int | None = None) -> None:
        self.calls.append((y, x, text))


class FavoriteUITests(unittest.TestCase):
    def build_ui(self, favorites: list[str] | None = None) -> HistermUI:
        return HistermUI(
            [],
            [],
            favorites=[] if favorites is None else favorites,
            initial_tab="favorites",
            history_file=Path("/tmp/history"),
            config_file=Path("/tmp/config.json"),
        )

    def test_add_favorite_appends_new_command(self) -> None:
        ui = self.build_ui()
        added = ui.add_favorite("cd A")
        self.assertTrue(added)
        self.assertEqual(ui.favorite_commands, ["cd A"])
        self.assertEqual(ui.items["favorites"][0].value, "cd A")

    def test_add_favorite_rejects_duplicates(self) -> None:
        ui = self.build_ui(["cd A", "mkdir B"])
        added = ui.add_favorite("cd A")
        self.assertFalse(added)
        self.assertEqual(ui.favorite_commands, ["cd A", "mkdir B"])
        self.assertEqual(ui.selection["favorites"], 0)
        self.assertEqual(ui.status_message, "Favorite already exists.")

    def test_delete_selected_favorite_removes_command(self) -> None:
        ui = self.build_ui(["cd A", "mkdir B"])
        ui.selection["favorites"] = 1
        removed = ui.delete_selected_favorite()
        self.assertEqual(removed, "mkdir B")
        self.assertEqual(ui.favorite_commands, ["cd A"])

    def test_draw_shows_favorites_tab_label(self) -> None:
        ui = self.build_ui()
        screen = FakeWindow()
        with patch.object(curses, "has_colors", return_value=False):
            ui.draw(screen)

        labels = [text for _, _, text in screen.calls]
        self.assertIn(" Favorites ", labels)
