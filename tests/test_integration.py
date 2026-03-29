from __future__ import annotations

from contextlib import redirect_stdout
import io
import unittest

from histerm.cli import main
from histerm.integration import load_shell_integration


class IntegrationTests(unittest.TestCase):
    def test_load_shell_integration_reads_zsh_script(self) -> None:
        script = load_shell_integration("zsh")
        self.assertIn("histerm-widget", script)
        self.assertIn("command histerm --output-file", script)

    def test_cli_init_prints_bash_script(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["init", "bash"])
        self.assertEqual(exit_code, 0)
        self.assertIn('__histerm_widget()', buffer.getvalue())

