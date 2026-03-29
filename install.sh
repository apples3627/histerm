#!/usr/bin/env sh
set -eu

REPO_URL="${HISTERM_REPO_URL:-git+https://github.com/apples3627/histerm.git}"
SHELL_NAME="${HISTERM_SHELL:-$(basename "${SHELL:-}")}"

say() {
  printf '%s\n' "$*"
}

fail() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

ensure_python() {
  if ! need_cmd python3; then
    fail "python3 is required to install histerm."
  fi
}

ensure_pip() {
  if python3 -m pip --version >/dev/null 2>&1; then
    return
  fi
  if python3 -m ensurepip --upgrade >/dev/null 2>&1; then
    return
  fi
  fail "python3 -m pip is required before installing pipx."
}

ensure_pipx() {
  if need_cmd pipx; then
    PIPX_BIN="$(command -v pipx)"
    return
  fi

  ensure_pip
  say "Installing pipx..."
  python3 -m pip install --user pipx

  if need_cmd pipx; then
    PIPX_BIN="$(command -v pipx)"
    return
  fi

  USER_BASE="$(python3 -c 'import site; print(site.USER_BASE)')"
  if [ -x "$USER_BASE/bin/pipx" ]; then
    PIPX_BIN="$USER_BASE/bin/pipx"
    return
  fi

  fail "pipx was installed but is not on PATH. Add it to PATH and rerun."
}

append_line_once() {
  line="$1"
  file="$2"

  mkdir -p "$(dirname "$file")"
  if [ -f "$file" ] && grep -Fqs "$line" "$file"; then
    return
  fi
  printf '\n%s\n' "$line" >> "$file"
}

configure_shell() {
  case "$SHELL_NAME" in
    zsh)
      rc_file="${ZDOTDIR:-$HOME}/.zshrc"
      init_line='source <(histerm init zsh)'
      ;;
    bash)
      rc_file="$HOME/.bashrc"
      init_line='source <(histerm init bash)'
      ;;
    *)
      say "Installed histerm, but skipped shell setup for unsupported shell: ${SHELL_NAME:-unknown}"
      return
      ;;
  esac

  append_line_once "$init_line" "$rc_file"
  say "Added shell integration to $rc_file"
}

main() {
  ensure_python
  ensure_pipx

  say "Installing histerm with pipx..."
  "$PIPX_BIN" install --force "$REPO_URL"
  "$PIPX_BIN" ensurepath >/dev/null 2>&1 || true

  configure_shell

  say
  say "histerm is installed."
  say "Open a new shell, or reload your shell config file to start using it."
}

main "$@"

