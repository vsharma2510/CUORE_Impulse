#!/usr/bin/env bash
# Start or stop recording the tmux pane that Claude Code is running in.
#   ./rec.sh start rec_02_critic     -> writes recordings/rec_02_critic.cast
#   ./rec.sh stop
#   ./rec.sh status
#   REC_CLEAN=1 ./rec.sh start ...   -> start from a blank screen instead of a snapshot of the pane
# Requires Claude Code to be running inside tmux. Uses `tmux pipe-pane`, which copies everything the
# pane displays to a command; only one pipe per pane can be open at a time.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dir="${REC_DIR:-$PWD/recordings}"
pane="${TMUX_PANE:?not inside tmux: start tmux first, then claude inside it}"

case "${1:-}" in
  start)
    name="${2:?usage: rec.sh start <name>}"
    mkdir -p "$dir"
    out="$dir/$name.cast"
    [[ -e "$out" ]] && { echo "exists: $out (choose another name)"; exit 1; }
    tmux pipe-pane -t "$pane"            # close any pipe already open on this pane
    w=$(tmux display -p -t "$pane" '#{pane_width}'); h=$(tmux display -p -t "$pane" '#{pane_height}')
    init="$dir/.$name.screen"
    if [[ "${REC_CLEAN:-0}" == "1" ]]; then : > "$init"   # start from a blank screen
    else tmux capture-pane -p -e -t "$pane" > "$init"; fi
    cx=$(tmux display -p -t "$pane" '#{cursor_x}'); cy=$(tmux display -p -t "$pane" '#{cursor_y}')
    tmux pipe-pane -t "$pane" "python3 '$here/pane_rec.py' '$out' $w $h '$init' $cx $cy"
    echo "$name" > "$dir/.current"
    echo "recording $name"
    ;;
  stop)
    tmux pipe-pane -t "$pane"
    name=$(cat "$dir/.current" 2>/dev/null || echo "?"); rm -f "$dir/.current"
    echo "stopped $name"
    ;;
  status)
    if [[ "$(tmux display -p -t "$pane" '#{pane_pipe}')" == "1" ]]; then
      echo "recording: $(cat "$dir/.current" 2>/dev/null || echo unknown)"
    else
      echo "not recording"
    fi
    ;;
  *) echo "usage: rec.sh start <name> | stop | status"; exit 2 ;;
esac
