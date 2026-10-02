#!/usr/bin/env python3
"""Philosophy conference display with a Matrix-style rain background displaying quotes.

Setup (Windows only, one time):   pip install windows-curses
Setup (macOS / Linux):            nothing, curses is built in
Run:                              python conference_display.py
Quit:                             press q or Esc
"""

import curses
import random

TITLE_FONT = "standard"   # bigger, for the title
INFO_FONT = "small"       # smaller, for date and room
# Other fonts to try: "big", "slant", "digital", "banner3", "doom", "mini"

# ----------------------------------------------------------------- content
PHI = [
    r"    /\_/\#####",
    "   ( o.o )###",
    "    > ^ <######",
    "  ####  ###  ####",
    " ###    ###    ###",
    " ###    ###    ###",
    "  ####  ###  ####",
    "    ###########",
    "        ###",
    "      #######",
]

TITLE = "17th In-House Philosophy Graduate Conference"
DATE = "23rd October 2026"
ROOMS = "Rooms: A415 and B421"

# Philosophical quotes displayed in the rain streams (one stream per column)
QUOTES = [
    "Knowledge",
    "Concept",
    "Existence",
    "Ontology",
    "Wisdom",
    "Morality",
    "Justice",
    "Liberty",
    "Emotion",
    "Mind",
    "Causation",
    "normativity",
    "Skepticism",
    "Beauty",
    "Justification"
]

# ------------------------------------------------------------ appearance
H_PADDING = 4     # spaces left/right of the text inside the box
GAP = 6           # spaces between the phi and the box
MARGIN_X = 4      # rain-free border around the art (columns)
MARGIN_Y = 1      # rain-free border around the art (rows)
FRAME_MS = 60     # milliseconds per frame (lower = faster rain)


# --------------------------------------------------------------- the art
def build_box(title, date, rooms, height):
    inner = len(title) + 2 * H_PADDING
    border = "+" + "-" * inner + "+"
    blank = "|" + " " * inner + "|"

    def row(text):
        return "|" + text.center(inner) + "|"

    rows = [
        border, blank, row(title), blank, border,
        blank, row(date), row(rooms), blank, border,
    ]
    while len(rows) < height:
        rows.insert(-1, blank)
    return rows


def build_art():
    box = build_box(TITLE, DATE, ROOMS, len(PHI))
    phi_width = max(len(line) for line in PHI)
    art = [p.ljust(phi_width) + " " * GAP + b for p, b in zip(PHI, box)]
    return art, phi_width


# ------------------------------------------------------------ matrix rain
class Rain:
    def __init__(self, rows, cols):
        self.rows, self.cols = rows, cols
        
        # Build a grid where each column cycles through a specific quote
        self.grid = []
        for y in range(rows):
            row_chars = []
            for x in range(cols):
                quote = QUOTES[x % len(QUOTES)]
                # Add a spacer between repetitions of the quote
                stream = f"{quote}    "
                row_chars.append(stream[y % len(stream)])
            self.grid.append(row_chars)

        self.drops = [self._new_drop(initial=True) for _ in range(cols)]

    def _new_drop(self, initial=False):
        start = (random.randint(-self.rows, self.rows) if initial
                 else -random.randint(0, self.rows * 2))
        speed = random.uniform(0.25, 1.0)
        length = random.randint(6, max(7, self.rows // 2))
        return [float(start), speed, length]

    def step(self):
        for drop in self.drops:
            drop[0] += drop[1]
            if drop[0] - drop[2] > self.rows:
                drop[:] = self._new_drop()

    def draw(self, scr, styles):
        head_style, bright, normal, faded = styles
        for x, (head, _speed, length) in enumerate(self.drops):
            head_y = int(head)
            for i in range(length):
                y = head_y - i
                if y < 0 or y >= self.rows:
                    continue
                if i == 0:
                    attr = head_style
                elif i < 3:
                    attr = bright
                elif i > length * 0.7:
                    attr = faded
                else:
                    attr = normal
                put(scr, y, x, self.grid[y][x], attr)


# ---------------------------------------------------------------- helpers
def put(scr, y, x, text, attr):
    """addstr that ignores errors (e.g. writing to the bottom-right cell)."""
    try:
        scr.addstr(y, x, text, attr)
    except curses.error:
        pass


def make_styles():
    curses.start_color()
    black = curses.COLOR_BLACK
    curses.init_pair(1, curses.COLOR_YELLOW, black)
    curses.init_pair(2, curses.COLOR_WHITE, black)
    if curses.COLORS >= 256:
        curses.init_pair(255, 255, black)   # dark green
        faded = curses.color_pair(3)
    else:
        faded = curses.color_pair(1) | curses.A_DIM
    green = curses.color_pair(1)
    white = curses.color_pair(2)
    # head, bright trail, normal trail, faded tail
    return (white | curses.A_BOLD, green | curses.A_BOLD, green, faded)


def draw_art(scr, art, phi_width, rows, cols):
    art_w, art_h = len(art[0]), len(art)
    green = curses.color_pair(1) | curses.A_BOLD
    white = curses.color_pair(2) | curses.A_BOLD

    if art_w + 2 * MARGIN_X > cols or art_h + 2 * MARGIN_Y > rows:
        msg = [f"Window too small: need {art_w + 2 * MARGIN_X}x"
               f"{art_h + 2 * MARGIN_Y}, have {cols}x{rows}.",
               "Enlarge the window or reduce the font size."]
        top = max((rows - len(msg)) // 2, 0)
        for i, line in enumerate(msg):
            line = line[:cols]
            put(scr, top + i, max((cols - line) // 2, 0), line, white)
        return

    top = (rows - art_h) // 2
    left = (cols - art_w) // 2

    # Clear a rain-free rectangle behind the art
    blank = " " * (art_w + 2 * MARGIN_X)
    for y in range(top - MARGIN_Y, top + art_h + MARGIN_Y):
        put(scr, y, left - MARGIN_X, blank, white)

    for i, line in enumerate(art):
        put(scr, top + i, left, line[:phi_width], green)
        put(scr, top + i, left + phi_width, line[phi_width:], white)


# ------------------------------------------------------------------- main
def run(scr):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    scr.timeout(FRAME_MS)
    styles = make_styles()
    art, phi_width = build_art()

    rows, cols = scr.getmaxyx()
    rain = Rain(rows, cols)

    while True:
        key = scr.getch()
        if key in (ord("q"), ord("Q"), 27):
            break
        if key == curses.KEY_RESIZE:
            try:
                curses.resize_term(0, 0)
            except (AttributeError, curses.error):
                pass

        new_rows, new_cols = scr.getmaxyx()
        if (new_rows, new_cols) != (rows, cols):
            rows, cols = new_rows, new_cols
            rain = Rain(rows, cols)

        rain.step()
        scr.erase()
        rain.draw(scr, styles)
        draw_art(scr, art, phi_width, rows, cols)
        scr.refresh()


def main():
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()