#!/usr/bin/env python3
"""Write a tmux pane's output stream (from `tmux pipe-pane`) as an asciinema v2 recording.

Called by rec.sh, not directly:  pane_rec.py OUT.cast WIDTH HEIGHT INITIAL_SCREEN_FILE CURSOR_X CURSOR_Y
The initial screen (from `tmux capture-pane -e`) is written first, so the recording starts with
what was already on screen instead of a blank terminal.
"""
import json, os, sys, time

out, width, height, initial = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
cx, cy = int(sys.argv[5]), int(sys.argv[6])
t0 = time.time()
with open(out, "w", buffering=1) as fh:
    fh.write(json.dumps({"version": 2, "width": width, "height": height, "timestamp": int(t0),
                         "env": {"TERM": "xterm-256color"}}) + "\n")
    try:
        screen = open(initial, encoding="utf-8", errors="replace").read()
        screen = "\x1b[2J\x1b[H" + screen.rstrip("\n").replace("\n", "\r\n")
        screen += f"\x1b[{cy + 1};{cx + 1}H"  # put the cursor where tmux has it
        fh.write(json.dumps([0.0, "o", screen]) + "\n")
    except OSError:
        pass
    fd = sys.stdin.fileno()
    pending = b""
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        data = pending + chunk
        # do not split a UTF-8 character across two events
        cut = len(data)
        while cut > 0 and cut > len(data) - 4 and (data[cut - 1] & 0xC0) == 0x80:
            cut -= 1
        if cut > 0 and data[cut - 1] >= 0xC0:
            cut -= 1
        text, pending = data[:cut].decode("utf-8", "replace"), data[cut:]
        if text:
            fh.write(json.dumps([round(time.time() - t0, 6), "o", text]) + "\n")
