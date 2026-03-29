typeset -g HISTERM_SELECTION=""

function _histerm_pick() {
  emulate -L zsh
  setopt localoptions pipefail no_aliases

  local tmp
  tmp="$(mktemp -t histerm.XXXXXX)" || return 1

  typeset -g HISTERM_SELECTION=""
  command histerm --output-file "$tmp"
  local exit_code=$?

  if [[ $exit_code -eq 0 && -s "$tmp" ]]; then
    typeset -g HISTERM_SELECTION="$(<"$tmp")"
  fi

  rm -f "$tmp"
  return $exit_code
}

function _histerm_widget() {
  emulate -L zsh
  setopt localoptions pipefail no_aliases

  zle -I
  _histerm_pick
  local exit_code=$?

  if [[ $exit_code -eq 0 && -n "$HISTERM_SELECTION" ]]; then
    BUFFER="$HISTERM_SELECTION"
    CURSOR=${#BUFFER}
  fi

  zle redisplay
  return $exit_code
}

function histerm() {
  emulate -L zsh
  setopt localoptions pipefail no_aliases

  if (( $# > 0 )) || [[ ! -o interactive ]]; then
    command histerm "$@"
    return $?
  fi

  _histerm_pick
  local exit_code=$?

  if [[ $exit_code -eq 0 && -n "$HISTERM_SELECTION" ]]; then
    print -z -- "$HISTERM_SELECTION"
  fi

  return $exit_code
}

zle -N histerm-widget _histerm_widget
bindkey '^R' histerm-widget

