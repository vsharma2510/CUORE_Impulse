#!/usr/bin/env python3
"""Replay an asciinema v2 .cast through a minimal VT100 screen and report what is actually VISIBLE.

Needed because `tmux pipe-pane` records the pane's output *stream*, and Claude Code's TUI redraws by
repositioning the cursor and overwriting. Stripping escape sequences from that stream therefore
produces garbled text and makes contiguous substring searches fail, even when the text renders
correctly on screen. Only a real screen model answers "what did end up being recorded".

Handles the subset the TUI uses: CUP/HVP, CUU/CUD/CUF/CUB, ED, EL, CR, LF, BS, SGR (ignored),
scroll-on-overflow, and DECAWM-ish line wrap.

    python3 -I tools/cast_render.py <cast> [--grep STR ...] [--frame SECONDS ...]
"""
import json
import re
import sys

CSI = re.compile(r"\x1b\[([0-9;?]*)([@-~])")
OSC = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
OTHER_ESC = re.compile(r"\x1b[()#][0-9A-Za-z]|\x1b[=>DEHMZ78]")


class Screen:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.buf = [[" "] * w for _ in range(h)]
        self.x = self.y = 0
        self.frames = []           # (time, list-of-lines) snapshots

    def _scroll(self):
        self.buf.pop(0)
        self.buf.append([" "] * self.w)

    def put(self, ch):
        if self.x >= self.w:
            self.x = 0
            self.y += 1
        if self.y >= self.h:
            self._scroll()
            self.y = self.h - 1
        self.buf[self.y][self.x] = ch
        self.x += 1

    def feed(self, data):
        i, n = 0, len(data)
        while i < n:
            c = data[i]
            if c == "\x1b":
                for pat in (CSI, OSC, OTHER_ESC):
                    m = pat.match(data, i)
                    if m:
                        if pat is CSI:
                            self.csi(m.group(1), m.group(2))
                        i = m.end()
                        break
                else:
                    i += 1
                continue
            if c == "\n":
                self.y += 1
                if self.y >= self.h:
                    self._scroll()
                    self.y = self.h - 1
            elif c == "\r":
                self.x = 0
            elif c == "\b":
                self.x = max(0, self.x - 1)
            elif c == "\t":
                self.x = min(self.w - 1, (self.x // 8 + 1) * 8)
            elif c >= " ":
                self.put(c)
            i += 1

    def csi(self, params, final):
        p = [int(x) if x.isdigit() else 0 for x in params.split(";")] if params and params[0] != "?" else []
        a = p[0] if p else 0
        if final in "Hf":
            self.y = min(self.h - 1, max(0, (p[0] - 1) if len(p) > 0 and p[0] else 0))
            self.x = min(self.w - 1, max(0, (p[1] - 1) if len(p) > 1 and p[1] else 0))
        elif final == "A":
            self.y = max(0, self.y - max(1, a))
        elif final == "B":
            self.y = min(self.h - 1, self.y + max(1, a))
        elif final == "C":
            self.x = min(self.w - 1, self.x + max(1, a))
        elif final == "D":
            self.x = max(0, self.x - max(1, a))
        elif final == "G":
            self.x = min(self.w - 1, max(0, a - 1 if a else 0))
        elif final == "J":
            if a == 2:
                self.buf = [[" "] * self.w for _ in range(self.h)]
            elif a == 0:
                for xx in range(self.x, self.w):
                    self.buf[self.y][xx] = " "
                for yy in range(self.y + 1, self.h):
                    self.buf[yy] = [" "] * self.w
            elif a == 1:
                for yy in range(self.y):
                    self.buf[yy] = [" "] * self.w
                for xx in range(self.x + 1):
                    self.buf[self.y][xx] = " "
        elif final == "K":
            if a == 0:
                for xx in range(self.x, self.w):
                    self.buf[self.y][xx] = " "
            elif a == 1:
                for xx in range(self.x + 1):
                    self.buf[self.y][xx] = " "
            else:
                self.buf[self.y] = [" "] * self.w
        elif final == "L":
            for _ in range(max(1, a)):
                self.buf.insert(self.y, [" "] * self.w)
                self.buf.pop()
        elif final == "M":
            for _ in range(max(1, a)):
                self.buf.pop(self.y)
                self.buf.append([" "] * self.w)

    def lines(self):
        return ["".join(r).rstrip() for r in self.buf]


def main():
    args = sys.argv[1:]
    path = args[0]
    greps = [args[i + 1] for i, a in enumerate(args) if a == "--grep"]
    frames = [float(args[i + 1]) for i, a in enumerate(args) if a == "--frame"]

    with open(path) as fh:
        hdr = json.loads(fh.readline())
        evs = [json.loads(l) for l in fh if l.strip()]

    sc = Screen(hdr["width"], hdr["height"])
    seen_lines = set()          # every line that was ever fully rendered
    hits = {g: [] for g in greps}
    nf = 0
    for t, _, d in evs:
        sc.feed(d)
        cur = sc.lines()
        for ln in cur:
            s = ln.strip()
            if len(s) > 2:
                seen_lines.add(s)
                for g in greps:
                    if g in s and (not hits[g] or hits[g][-1][1] != s):
                        hits[g].append((t, s))
        while nf < len(frames) and t >= frames[nf]:
            print(f"\n===== FRAME at {frames[nf]:.0f} s =====")
            for ln in cur:
                print("  |" + ln)
            nf += 1

    print(f"\ncast {hdr['width']}x{hdr['height']}  {evs[-1][0]:.0f} s  {len(evs)} events")
    print(f"distinct fully-rendered lines: {len(seen_lines)}")
    for g in greps:
        print(f"\n--- VISIBLE occurrences of {g!r}: {len(hits[g])} ---")
        for t, s in hits[g][:6]:
            print(f"  {int(t // 60):3d}:{int(t % 60):02d}  {s[:110]}")


if __name__ == "__main__":
    main()
