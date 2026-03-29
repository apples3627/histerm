__histerm_widget() {
  local tmp
  tmp="$(mktemp -t histerm.XXXXXX)" || return 1

  histerm --output-file "$tmp"
  local exit_code=$?

  if [[ $exit_code -eq 0 && -s "$tmp" ]]; then
    READLINE_LINE="$(<"$tmp")"
    READLINE_POINT=${#READLINE_LINE}
  fi

  rm -f "$tmp"
  return $exit_code
}

bind -x '"\C-r":__histerm_widget'

