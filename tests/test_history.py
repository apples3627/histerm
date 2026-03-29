from __future__ import annotations

import unittest

from histerm.history import (
    HistoryEntry,
    command_key,
    frequent_entries,
    parse_bash_history,
    parse_zsh_history,
    recent_entries,
)


class HistoryParsingTests(unittest.TestCase):
    def test_parse_zsh_extended_history(self) -> None:
        lines = [
            ": 1711111111:0;ls -la",
            ": 1711111112:0;git status",
        ]
        entries = parse_zsh_history(lines)
        self.assertEqual([entry.command for entry in entries], ["ls -la", "git status"])
        self.assertEqual(entries[0].timestamp, 1711111111)

    def test_parse_bash_history_with_timestamps(self) -> None:
        lines = [
            "#1711111111",
            "docker ps",
            "#1711111112",
            "kubectl get pods",
        ]
        entries = parse_bash_history(lines)
        self.assertEqual([entry.command for entry in entries], ["docker ps", "kubectl get pods"])
        self.assertEqual(entries[1].timestamp, 1711111112)

    def test_recent_entries_can_dedupe(self) -> None:
        entries = [
            HistoryEntry("ls"),
            HistoryEntry("git status"),
            HistoryEntry("ls"),
        ]
        result = recent_entries(entries, 5, dedupe=True)
        self.assertEqual([entry.command for entry in result], ["ls", "git status"])


class FrequencyTests(unittest.TestCase):
    def test_command_key_skips_wrapper_commands(self) -> None:
        self.assertEqual(command_key("sudo env DEBUG=1 /usr/bin/git status"), "git")

    def test_frequent_entries_group_by_main_command(self) -> None:
        entries = [
            HistoryEntry("git status"),
            HistoryEntry("ls -la"),
            HistoryEntry("git pull"),
            HistoryEntry("git diff"),
        ]
        result = frequent_entries(entries, 5)
        self.assertEqual(result[0].key, "git")
        self.assertEqual(result[0].count, 3)
        self.assertEqual(result[0].sample, "git diff")

