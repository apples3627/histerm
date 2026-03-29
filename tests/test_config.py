from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from histerm.config import HistermConfig, load_config, save_favorites


class ConfigTests(unittest.TestCase):
    def test_load_config_defaults_on_missing_file(self) -> None:
        config = load_config(Path("/tmp/does-not-exist.json"))
        self.assertEqual(config, HistermConfig())

    def test_load_config_reads_valid_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            path.write_text(
                '{"limit": 20, "initial_tab": "frequent", "dedupe_recent": true}',
                encoding="utf-8",
            )
            config = load_config(path)
        self.assertEqual(config.limit, 20)
        self.assertEqual(config.initial_tab, "frequent")
        self.assertTrue(config.dedupe_recent)

    def test_load_config_normalizes_favorites(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            path.write_text(
                '{"favorites": [" cd A ", "", "mkdir B", "cd A", 1]}',
                encoding="utf-8",
            )
            config = load_config(path)
        self.assertEqual(config.favorites, ["cd A", "mkdir B"])

    def test_save_favorites_preserves_existing_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            path.write_text(
                '{"limit": 20, "dedupe_recent": true}',
                encoding="utf-8",
            )
            save_favorites(["cd A", "mkdir B", "cd A"], path)
            raw = path.read_text(encoding="utf-8")
        self.assertIn('"limit": 20', raw)
        self.assertIn('"dedupe_recent": true', raw)
        self.assertIn('"favorites": [', raw)
        self.assertIn('"cd A"', raw)
        self.assertIn('"mkdir B"', raw)
