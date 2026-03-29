from __future__ import annotations

from importlib.resources import files


SUPPORTED_SHELLS = frozenset({"bash", "zsh"})


def load_shell_integration(shell_name: str) -> str:
    if shell_name not in SUPPORTED_SHELLS:
        raise ValueError(f"unsupported shell: {shell_name}")
    return files("histerm").joinpath("shell", f"histerm.{shell_name}").read_text(
        encoding="utf-8"
    )

