#!/usr/bin/env python3
"""Print the LoopPrint banner with a pink -> blue 24-bit truecolor gradient (terminal).

Usage: python3 scripts/banner.py
Honors NO_COLOR / TERM=dumb (prints plain). The art lives in assets/logo.txt.
"""
import os

PINK = (255, 102, 196)
BLUE = (91, 141, 239)


def _lerp(a, b, t):
    return round(a + (b - a) * t)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    art_path = os.path.join(here, "..", "assets", "logo.txt")
    try:
        lines = open(art_path, encoding="utf-8").read().rstrip("\n").split("\n")
    except OSError:
        return
    plain = bool(os.environ.get("NO_COLOR")) or os.environ.get("TERM") == "dumb"
    width = max((len(line) for line in lines), default=1)
    out = []
    for line in lines:
        if plain:
            out.append(line)
            continue
        rendered = ""
        for x, ch in enumerate(line):
            if ch == " ":
                rendered += " "
                continue
            t = x / max(width - 1, 1)
            r = _lerp(PINK[0], BLUE[0], t)
            g = _lerp(PINK[1], BLUE[1], t)
            b = _lerp(PINK[2], BLUE[2], t)
            rendered += f"\033[38;2;{r};{g};{b}m{ch}"
        out.append(rendered + "\033[0m")
    print("\n".join(out))


if __name__ == "__main__":
    main()
