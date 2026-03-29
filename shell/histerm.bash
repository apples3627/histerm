# Load this file from ~/.bashrc
# Example:
#   source /path/to/histerm/shell/histerm.bash

__histerm_widget() {
  local tmp
  tmp="$(mktemp -t histerm.XXXXXX)" || return 1

  histerm --output-file "$tmp"
  local status=$?

  if [[ $status -eq 0 && -s "$tmp" ]]; then
    READLINE_LINE="$(<"$tmp")"
    READLINE_POINT=${#READLINE_LINE}
  fi

  rm -f "$tmp"
  return $status
}

bind -x '"\C-r":__histerm_widget'

