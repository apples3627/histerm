# histerm

`histerm` is a lightweight terminal popup for shell history.

It reads your shell history file, shows a centered TUI with two tabs:

- `Recent`: your latest commands
- `Frequent`: the commands you use most often

You move with the arrow keys, press `Enter`, and the selected command is placed back into your current shell prompt.

## Features

- Popup-style terminal UI built with the Python standard library
- No third-party runtime dependencies
- `zsh` and `bash` shell integration
- Default list size of `10`, configurable by CLI flag or config file
- Frequency tab groups by the main command name and inserts the latest matching full command

## Quick Start

### 1. Install

```bash
python3 -m pip install -e .
```

### 2. Add shell integration

For `zsh`, add this to `~/.zshrc`:

```bash
source /path/to/histerm/shell/histerm.zsh
```

For `bash`, add this to `~/.bashrc`:

```bash
source /path/to/histerm/shell/histerm.bash
```

By default the widget is bound to `Ctrl-R`.

For `zsh`, after sourcing the integration file, you can also run plain `histerm` and the selected command will be inserted into the next prompt instead of printed.

### 3. Reload your shell

```bash
source ~/.zshrc
```

or

```bash
source ~/.bashrc
```

## Usage

Run directly:

```bash
histerm
```

Behavior note:

- bare `histerm` inserts back into the prompt when the `zsh` integration file is sourced
- otherwise the standalone binary prints the selected command to standard output

Useful options:

```bash
histerm --limit 20
histerm --tab frequent
histerm --history-file ~/.zsh_history
histerm --dedupe-recent
```

## Configuration

Optional config file:

`~/.config/histerm/config.json`

Example:

```json
{
  "limit": 15,
  "initial_tab": "frequent",
  "scan_limit": 8000,
  "dedupe_recent": true
}
```

Supported keys:

- `limit`: number of items shown per tab
- `initial_tab`: `recent` or `frequent`
- `history_file`: explicit history file path
- `scan_limit`: maximum parsed history entries
- `dedupe_recent`: hide duplicate commands in the recent tab

CLI flags override config values.

## Keybindings

- `Up` / `Down`: move selection
- `Left` / `Right`: switch tabs
- `Tab`: switch tabs
- `Enter`: choose command
- `q` or `Esc`: close

## Shell Integration Notes

An external program cannot reliably modify the current shell input buffer by itself. `histerm` solves this by:

1. running the TUI as a normal terminal app
2. writing the selected command to a temporary file
3. letting a shell widget place that command into the live prompt buffer

This keeps the UI stable and works well for interactive terminal use.

In `zsh`, the integration file also defines a small shell wrapper so typing `histerm` with no arguments pushes the selected command into the next editable prompt. In `bash`, prompt insertion remains bound to `Ctrl-R` because readline buffer editing is most reliable from a key binding.

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## License

MIT
