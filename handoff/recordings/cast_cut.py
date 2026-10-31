#!/usr/bin/env python3
"""Cut an asciinema v2 .cast down to the keep ranges in results/DEMO_NOTES.md.

You cannot cut a terminal recording by dropping events. The cast is an output STREAM, not a sequence
of frames: what is on screen at 68:40 is the accumulated result of every byte written since 0:00, so
a file that starts at 68:40 opens on a garbled screen. Claude Code's TUI makes this worse, because it
redraws by repositioning the cursor and overwriting rather than reprinting.

So each kept range after the first is opened with a reconstructed screen. Every event from the
beginning of the file is replayed through the VT100 model in tools/cast_render.py, and at the start
of a kept range the resulting screen is emitted as a single synthetic paint event: erase, home, the
rendered lines, then the cursor put back where it was. From there the real events resume.

One honest limitation: the model in cast_render.py ignores SGR, so a reconstructed opening frame is
monochrome. Colour returns as soon as the live events resume, within a second or two. The alternative
would be to track colour per cell, which is not worth it for a demo cut.

    python3 -I tools/cast_cut.py <in.cast> <out.cast> <start-end> [<start-end> ...] [--max-gap S]

Ranges are mm:ss-mm:ss or seconds. --max-gap caps idle time WITHIN a kept range (default: no cap).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cast_render import Screen  # noqa: E402


def parse_t(s):
    if ":" in s:
        m, sec = s.split(":")
        return int(m) * 60 + float(sec)
    return float(s)


def parse_range(s):
    a, b = s.split("-")
    return parse_t(a), parse_t(b)


def repaint(screen):
    """A single escape burst that reproduces the current screen and cursor position."""
    lines = screen.lines()
    while lines and not lines[-1].strip():
        lines.pop()
    body = "\r\n".join(lines)
    return f"\x1b[2J\x1b[H{body}\x1b[{screen.y + 1};{screen.x + 1}H"


def main():
    args = [a for a in sys.argv[1:]]
    max_gap = None
    if "--max-gap" in args:
        i = args.index("--max-gap")
        max_gap = float(args[i + 1])
        del args[i:i + 2]
    src, dst, ranges = args[0], args[1], [parse_range(r) for r in args[2:]]
    ranges.sort()

    with open(src) as fh:
        hdr = json.loads(fh.readline())
        evs = [json.loads(l) for l in fh if l.strip()]

    sc = Screen(hdr["width"], hdr["height"])
    out = []
    emitted = 0.0           # output clock
    kept_s = 0.0            # real seconds of content kept
    ri = 0
    opened = False
    prev_in = None

    for t, kind, data in evs:
        # advance the screen model over EVERY event, kept or not
        while ri < len(ranges) and t > ranges[ri][1]:
            ri += 1
            opened = False
        inside = ri < len(ranges) and ranges[ri][0] <= t <= ranges[ri][1]
        if not inside:
            sc.feed(data)
            prev_in = None
            continue

        if not opened:
            # open this range with a reconstructed screen, unless it is the very start of the file
            if out or ranges[ri][0] > 0.05:
                out.append([round(emitted, 6), "o", repaint(sc)])
                emitted += 0.20
            opened = True
            prev_in = t

        gap = t - prev_in
        if max_gap is not None:
            gap = min(gap, max_gap)
        emitted += gap
        kept_s += t - prev_in
        prev_in = t
        sc.feed(data)
        out.append([round(emitted, 6), kind, data])

    hdr.pop("duration", None)
    hdr["title"] = (hdr.get("title") or os.path.basename(dst).replace(".cast", "")) + " (cut)"
    with open(dst, "w") as fh:
        fh.write(json.dumps(hdr) + "\n")
        for e in out:
            fh.write(json.dumps(e) + "\n")

    src_len = evs[-1][0]
    print(f"{os.path.basename(src):24s} {src_len/60:6.1f} min -> "
          f"{os.path.basename(dst):24s} {emitted/60:5.1f} min   "
          f"{len(evs):6d} -> {len(out):5d} events   "
          f"ranges {' '.join(f'{a:.0f}-{b:.0f}' for a, b in ranges)}")


if __name__ == "__main__":
    main()
