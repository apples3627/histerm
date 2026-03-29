from __future__ import annotations

from collections.abc import Callable
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
        favorites: list[str],
        initial_tab: str,
        history_file: Path,
        config_file: Path | None,
        save_favorites_callback: Callable[[list[str]], None] | None = None,
    ) -> None:
        self.history_file = history_file
        self.config_file = config_file
        self.save_favorites_callback = save_favorites_callback
        self.favorite_commands = list(favorites)
        self.tabs = ["recent", "frequent", "favorites"]
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
            "favorites": [],
        }
        self.selection = {tab: 0 for tab in self.tabs}
        self.scroll = {tab: 0 for tab in self.tabs}
        self.status_message = ""
        self.refresh_favorites_items()

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
            if self.active_tab == "favorites" and key in (ord("a"), ord("A")):
                command = self.prompt_command(stdscr, "Add favorite command")
                if command is not None:
                    if self.add_favorite(command):
                        self.ensure_selection_visible("favorites", stdscr)
                        self.persist_favorites("Favorite saved.")
                    else:
                        self.ensure_selection_visible("favorites", stdscr)
                continue
            if self.active_tab == "favorites" and key in (ord("d"), ord("D")):
                removed = self.delete_selected_favorite()
                if removed is not None:
                    self.ensure_selection_visible("favorites", stdscr)
                    self.persist_favorites(f"Removed favorite: {preview_text(removed, 40)}")
                continue
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
                continue
            if key == curses.KEY_RESIZE:
                continue

    def current_items(self) -> list[MenuItem]:
        return self.items[self.active_tab]

    def refresh_favorites_items(self) -> None:
        self.items["favorites"] = [
            MenuItem(
                title=preview_text(command, 120),
                subtitle="",
                value=command,
            )
            for command in self.favorite_commands
        ]
        if not self.items["favorites"]:
            self.selection["favorites"] = 0
            self.scroll["favorites"] = 0
            return
        self.selection["favorites"] = min(
            self.selection["favorites"],
            len(self.items["favorites"]) - 1,
        )
        self.scroll["favorites"] = min(
            self.scroll["favorites"],
            self.selection["favorites"],
        )

    def add_favorite(self, command: str) -> bool:
        normalized = command.strip()
        if not normalized:
            self.status_message = "Favorite commands cannot be empty."
            return False
        if normalized in self.favorite_commands:
            self.selection["favorites"] = self.favorite_commands.index(normalized)
            self.status_message = "Favorite already exists."
            return False
        self.favorite_commands.append(normalized)
        self.refresh_favorites_items()
        self.selection["favorites"] = len(self.favorite_commands) - 1
        return True

    def delete_selected_favorite(self) -> str | None:
        if not self.favorite_commands:
            self.status_message = "No favorites to delete."
            return None
        index = self.selection["favorites"]
        removed = self.favorite_commands.pop(index)
        self.refresh_favorites_items()
        return removed

    def persist_favorites(self, success_message: str) -> None:
        if self.save_favorites_callback is None:
            self.status_message = f"{success_message} Session only."
            return
        try:
            self.save_favorites_callback(list(self.favorite_commands))
        except OSError as exc:
            self.status_message = f"Failed to save favorites: {preview_text(str(exc), 40)}"
            return
        self.status_message = success_message

    def prompt_command(self, stdscr: curses.window, prompt: str) -> str | None:
        buffer: list[str] = []
        while True:
            self.draw(stdscr)
            max_y, max_x = stdscr.getmaxyx()
            width = min(max_x - 6, 90)
            height = 6
            start_y = max(1, (max_y - height) // 2)
            start_x = max(2, (max_x - width) // 2)
            win = stdscr.derwin(height, width, start_y, start_x)
            win.box()
            win.addstr(1, 3, preview_text(prompt, width - 6), curses.A_BOLD)
            win.addstr(
                height - 2,
                3,
                preview_text("Enter save | Esc cancel | Backspace delete", width - 6),
                curses.A_DIM,
            )
            value = "".join(buffer)
            input_width = max(1, width - 6)
            display_value = value[-input_width:]
            win.addstr(3, 3, " " * input_width)
            win.addstr(3, 3, display_value)
            try:
                curses.curs_set(1)
            except curses.error:
                pass
            win.move(3, 3 + len(display_value))
            stdscr.refresh()

            try:
                key = stdscr.get_wch()
            except curses.error:
                continue

            if isinstance(key, str):
                if key == "\x1b":
                    self.status_message = "Favorite input canceled."
                    break
                if key in ("\n", "\r"):
                    command = value.strip()
                    if command:
                        self.status_message = ""
                        try:
                            curses.curs_set(0)
                        except curses.error:
                            pass
                        return command
                    self.status_message = "Favorite commands cannot be empty."
                    continue
                if key in ("\x08", "\x7f"):
                    if buffer:
                        buffer.pop()
                    continue
                if key.isprintable():
                    buffer.append(key)
                    continue
            elif key in (curses.KEY_BACKSPACE, curses.KEY_DC):
                if buffer:
                    buffer.pop()
                continue

        try:
            curses.curs_set(0)
        except curses.error:
            pass
        return None

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
        self.ensure_selection_visible(key, stdscr)

    def ensure_selection_visible(self, tab_name: str, stdscr: curses.window) -> None:
        visible = max(1, self.visible_rows(stdscr))
        current_index = self.selection[tab_name]
        if current_index < self.scroll[tab_name]:
            self.scroll[tab_name] = current_index
        if current_index >= self.scroll[tab_name] + visible:
            self.scroll[tab_name] = current_index - visible + 1

    def visible_rows(self, stdscr: curses.window) -> int:
        max_y, _ = stdscr.getmaxyx()
        height = min(max_y - 2, max(14, len(self.current_items()) + 8))
        return max(1, height - 8)

    def subtitle_text(self, width: int) -> str:
        if self.active_tab == "favorites":
            if self.config_file is None:
                return "favorites: session only (--no-config)"
            return f"favorites: {preview_text(str(self.config_file), width - 16)}"
        return f"history: {preview_text(str(self.history_file), width - 14)}"

    def empty_state_text(self) -> str:
        if self.active_tab == "favorites":
            return "No favorites yet. Press a to add a command."
        return "No history entries found."

    def footer_text(self) -> str:
        if self.active_tab == "favorites":
            return "Enter insert | a add | d delete | Left/Right tab | Up/Down move"
        return "Enter choose | Left/Right tab | Tab switch | Up/Down move"

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

        win.addstr(4, 3, self.subtitle_text(width), curses.A_DIM)
        if self.status_message:
            win.addstr(5, 3, preview_text(self.status_message, width - 6), curses.A_DIM)

        visible_rows = max(1, height - 8)
        offset = self.scroll[self.active_tab]
        end = offset + visible_rows
        visible_items = items[offset:end]

        if not visible_items:
            win.addstr(7, 3, self.empty_state_text(), curses.A_DIM)
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

        win.addstr(height - 2, 3, preview_text(self.footer_text(), width - 6), curses.A_DIM)
        stdscr.refresh()
