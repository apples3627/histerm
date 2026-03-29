from __future__ import annotations

from pathlib import Path
import unittest

from histerm.tui import HistermUI


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
