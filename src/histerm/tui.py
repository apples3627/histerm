from __future__ import annotations

import curses
from dataclasses import dataclass
from pathlib import Path

from histerm.history import FrequentEntry, HistoryEntry


@dataclass(slots=True)
class MenuItem:
    title: str
    subtitle: str
    value: str


def preview_text(text: str, width: int) -> str:
    single_line = " ".join(part for part in text.splitlines() if part.strip())
    if len(single_line) <= width:
        return single_line
    if width <= 3:
        return single_line[:width]
    return f"{single_line[: width - 3]}..."


class HistermUI:
    def __init__(
        self,
        recent: list[HistoryEntry],
        frequent: list[FrequentEntry],
        *,
        initial_tab: str,
        history_file: Path,
    ) -> None:
        self.history_file = history_file
        self.tabs = ["recent", "frequent"]
        self.active_tab = initial_tab if initial_tab in self.tabs else "recent"
        self.items = {
            "recent": [
                MenuItem(
                    title=preview_text(entry.command, 120),
                    subtitle="",
                    value=entry.command,
                )
                for entry in recent
            ],
            "frequent": [
                MenuItem(
                    title=entry.key,
                    subtitle=f"{entry.count}x | latest: {preview_text(entry.sample, 100)}",
                    value=entry.sample,
                )
                for entry in frequent
            ],
        }
        self.selection = {"recent": 0, "frequent": 0}
        self.scroll = {"recent": 0, "frequent": 0}

    def run(self, stdscr: curses.window) -> str | None:
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        stdscr.keypad(True)
        if curses.has_colors():
            curses.start_color()
            try:
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_CYAN, -1)
            except curses.error:
                pass

        while True:
            self.draw(stdscr)
            key = stdscr.getch()
            if key in (27, ord("q")):
                return None
            if key in (curses.KEY_ENTER, 10, 13):
                current = self.current_items()
                if current:
                    return current[self.selection[self.active_tab]].value
                return None
            if key in (curses.KEY_RIGHT, ord("\t"), ord("l")):
                self.switch_tab(1)
                continue
            if key in (curses.KEY_LEFT, ord("h")):
                self.switch_tab(-1)
                continue
            if key in (curses.KEY_UP, ord("k")):
                self.move_selection(-1, stdscr)
                continue
            if key in (curses.KEY_DOWN, ord("j")):
                self.move_selection(1, stdscr)
                continue
            if key == curses.KEY_NPAGE:
                self.move_selection(self.visible_rows(stdscr), stdscr)
                continue
            if key == curses.KEY_PPAGE:
                self.move_selection(-self.visible_rows(stdscr), stdscr)

    def current_items(self) -> list[MenuItem]:
        return self.items[self.active_tab]

    def switch_tab(self, step: int) -> None:
        current_index = self.tabs.index(self.active_tab)
        self.active_tab = self.tabs[(current_index + step) % len(self.tabs)]

    def move_selection(self, step: int, stdscr: curses.window) -> None:
        current = self.current_items()
        if not current:
            return
        key = self.active_tab
        next_index = max(0, min(self.selection[key] + step, len(current) - 1))
        self.selection[key] = next_index
        visible = max(1, self.visible_rows(stdscr))
        if next_index < self.scroll[key]:
            self.scroll[key] = next_index
        if next_index >= self.scroll[key] + visible:
            self.scroll[key] = next_index - visible + 1

    def visible_rows(self, stdscr: curses.window) -> int:
        max_y, _ = stdscr.getmaxyx()
        height = min(max_y - 2, max(14, len(self.current_items()) + 8))
        return max(1, height - 8)

    def draw(self, stdscr: curses.window) -> None:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        if max_y < 12 or max_x < 50:
            stdscr.addstr(0, 0, "Terminal too small for histerm.")
            stdscr.addstr(1, 0, "Resize and try again.")
            stdscr.refresh()
            return

        items = self.current_items()
        height = min(max_y - 2, max(14, len(items) + 8))
        width = min(max_x - 4, 100)
        start_y = max(1, (max_y - height) // 2)
        start_x = max(2, (max_x - width) // 2)
        win = stdscr.derwin(height, width, start_y, start_x)
        win.box()

        title_attr = curses.A_BOLD
        if curses.has_colors():
            title_attr |= curses.color_pair(1)

        win.addstr(1, 3, "histerm", title_attr)
        win.addstr(1, width - 17, "q/Esc to close")

        tabs = []
        for tab_name in self.tabs:
            label = f" {tab_name.title()} "
            if tab_name == self.active_tab:
                tabs.append((label, curses.A_REVERSE | curses.A_BOLD))
            else:
                tabs.append((label, curses.A_DIM))
        x = 3
        for label, attr in tabs:
            win.addstr(3, x, label, attr)
            x += len(label) + 1

        subtitle = f"history: {preview_text(str(self.history_file), width - 14)}"
        win.addstr(4, 3, subtitle, curses.A_DIM)

        visible_rows = max(1, height - 8)
        offset = self.scroll[self.active_tab]
        end = offset + visible_rows
        visible_items = items[offset:end]

        if not visible_items:
            win.addstr(7, 3, "No history entries found.", curses.A_DIM)
        else:
            title_width = max(12, width - 10)
            for row, item in enumerate(visible_items, start=0):
                item_y = 6 + row
                index = offset + row
                attr = curses.A_NORMAL
                if index == self.selection[self.active_tab]:
                    attr = curses.A_REVERSE
                marker = ">" if index == self.selection[self.active_tab] else " "
                line = item.title
                if item.subtitle:
                    line = f"{item.title} | {item.subtitle}"
                title = preview_text(line, title_width)
                win.addstr(item_y, 2, marker, attr)
                win.addstr(item_y, 4, title, attr | curses.A_BOLD)

        footer = "Enter choose | Left/Right switch tab | Up/Down move"
        win.addstr(height - 2, 3, preview_text(footer, width - 6), curses.A_DIM)
        stdscr.refresh()
