# histerm

`histerm` is a lightweight terminal popup for shell history.

It reads your shell history file, shows a centered TUI with three tabs:

- `Recent`: your latest commands
- `Frequent`: the commands you use most often
- `Favorites`: your saved shortcut commands such as `cd ~/work` or `mkdir tmp`

You move with the arrow keys, press `Enter`, and the selected command is placed back into your current shell prompt.

## Features

- Popup-style terminal UI built with the Python standard library
- No third-party runtime dependencies
- `zsh` and `bash` shell integration
- Default list size of `10` for history tabs, configurable by CLI flag or config file
- Frequency tab groups by the main command name and inserts the latest matching full command
- Favorites tab lets you save your own commands and reinsert them with `Enter`

## Quick Start

### 1. Install

Recommended with `pipx`:

```bash
pipx install git+https://github.com/apples3627/histerm.git
```

If `histerm` is not found after install, run:

```bash
pipx ensurepath
```

Optional one-line installer:

```bash
curl -fsSL https://raw.githubusercontent.com/apples3627/histerm/main/install.sh | bash
```

The installer uses `pipx`, installs it first if needed, and adds shell integration for the detected shell.

### 2. Add shell integration

For `zsh`, add this to `~/.zshrc`:

```bash
echo 'source <(histerm init zsh)' >> ~/.zshrc
```

For `bash`, add this to `~/.bashrc`:

```bash
echo 'source <(histerm init bash)' >> ~/.bashrc
```

By default the widget is bound to `Ctrl-R`.

For `zsh`, after loading the integration, you can also run plain `histerm` and the selected command will be inserted into the next prompt instead of printed.

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
histerm --tab favorites
histerm --history-file ~/.zsh_history
histerm --dedupe-recent
histerm init zsh
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
  "dedupe_recent": true,
  "favorites": [
    "cd ~/work/project-a",
    "mkdir ~/tmp/demo"
  ]
}
```

Supported keys:

- `limit`: number of items shown in the `recent` and `frequent` tabs
- `initial_tab`: `recent`, `frequent`, or `favorites`
- `favorites`: saved commands shown in the favorites tab
- `history_file`: explicit history file path
- `scan_limit`: maximum parsed history entries
- `dedupe_recent`: hide duplicate commands in the recent tab

The favorites tab also writes back to the same config file when you add or delete entries inside the TUI.

CLI flags override config values.

## Keybindings

- `Up` / `Down`: move selection
- `Left` / `Right`: switch tabs
- `Tab`: switch tabs
- `Enter`: choose command
- `a`: add a favorite command when the favorites tab is open
- `d`: delete the selected favorite command when the favorites tab is open
- `q` or `Esc`: close

## Shell Integration Notes

An external program cannot reliably modify the current shell input buffer by itself. `histerm` solves this by:

1. running the TUI as a normal terminal app
2. writing the selected command to a temporary file
3. letting a shell widget place that command into the live prompt buffer

This keeps the UI stable and works well for interactive terminal use.

In `zsh`, the integration also defines a small shell wrapper so typing `histerm` with no arguments pushes the selected command into the next editable prompt. In `bash`, prompt insertion remains bound to `Ctrl-R` because readline buffer editing is most reliable from a key binding.

## Install Notes

- `pipx` is the recommended installation path for end users.
- `histerm init zsh` and `histerm init bash` print the integration script so your shell can source it without depending on the cloned repository path.
- The `curl` installer is optional convenience on top of the same `pipx` flow.

## Development

Local editable install:

```bash
python3 -m pip install -e .
```

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## License

MIT
