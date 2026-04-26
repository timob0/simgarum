"""SimGarum ncurses UI – Phase 1: structured panels, stock breakdown,
assets, market panel, and action-key scaffolding with placeholder dialogs.

Design principles:
  - Engine and UI are fully separated. The UI only reads from the
    Simulation object; it never mutates state.
  - All display helpers live here. Core economy logic is untouched.
"""
from __future__ import annotations

import argparse
import curses
import time
from typing import Dict, List, Optional, Tuple

from .engine import Simulation

# ── colour pairs ──────────────────────────────────────────────────
C_DEFAULT = 1
C_GOOD    = 2
C_WARN    = 3
C_NOTE    = 4
C_TITLE   = 5
C_HIGHLIGHT = 6
C_DIM     = 7
C_BORDER  = 8

# ── role-specific colour themes ──────────────────────────────────
ROLE_THEMES: Dict[str, Tuple[int, int, int]] = {
    "fisherman": (curses.COLOR_BLUE,    curses.COLOR_BLACK, curses.COLOR_CYAN),
    "salt-maker": (curses.COLOR_YELLOW, curses.COLOR_BLACK, curses.COLOR_WHITE),
    "producer":  (curses.COLOR_MAGENTA, curses.COLOR_BLACK, curses.COLOR_WHITE),
    "merchant":  (curses.COLOR_GREEN,   curses.COLOR_BLACK, curses.COLOR_WHITE),
}

# ── panel layout constants ───────────────────────────────────────
# We split the screen into 5 panels:
#   ┌───────────────────────────────────────────────────┐
#   │  HEADER  (role, tick, controls)                   │
#   ├──────────┬──────────────────┬────────────────────┤
#   │  ASSETS  │     STOCK        │     MARKET         │
#   │          │                  │                    │
#   ├──────────┴──────────────────┴────────────────────┤
#   │  EVENTS (scrolling log)                           │
#   └───────────────────────────────────────────────────┘
#
# Panel widths are fractions of terminal width.
# Heights are fractions of terminal height minus header/footer.

HEADER_H = 1
FOOTER_H = 3  # bottom 3 rows: events + controls hint

LEFT_PANEL_W_RATIO = 0.20
MIDDLE_PANEL_W_RATIO = 0.40
RIGHT_PANEL_W_RATIO = 0.40


# ── helpers ──────────────────────────────────────────────────────

def _safe_addstr(win: curses.window, y: int, x: int, text: str,
                 attr: int = curses.A_NORMAL) -> None:
    """Write text to a window, clipping to visible area."""
    try:
        win.addstr(y, x, text[:_visible_width(win, y)], attr)
    except curses.error:
        pass


def _visible_width(win: curses.window, y: int) -> int:
    _, w = win.getmaxyx()
    return max(w - 1, 1)


def _pad_right(s: str, width: int) -> str:
    return s.ljust(width)


def _fmt_gold(v: float) -> str:
    return f"{v:.2f}"


def _fmt_delta(v: float) -> str:
    if v > 0:
        return f"+{v:.2f}"
    return f"{v:.2f}"


def _quality_bar(score: float, width: int = 12) -> str:
    """Render a simple ASCII quality bar."""
    filled = int(min(max(score, 0), 100) / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _fmt_age_quality(age: int, quality: float, width: int = 24) -> str:
    bar = _quality_bar(quality, 10)
    return f"age={age:2d}  {bar}  {quality:5.1f}"


# ── event colouring ──────────────────────────────────────────────

def event_color(event: str) -> int:
    low = event.lower()
    if any(w in low for w in ["sells", "buys a new", "adds a new", "completes"]):
        return C_GOOD
    if any(w in low for w in ["spoilage", "loses", "downgrades"]):
        return C_WARN
    return C_NOTE


# ── panel renderers ──────────────────────────────────────────────

def render_header(win: curses.window, role: str, tick: int,
                  paused: bool, tick_seconds: float) -> None:
    """Top bar: role label, tick, pause state, tick delay."""
    theme_fg, _, _ = ROLE_THEMES.get(role, (curses.COLOR_WHITE, curses.COLOR_BLACK, curses.COLOR_WHITE))
    attr = curses.A_BOLD | curses.color_pair(C_TITLE) | curses.color_pair(theme_fg)
    status = "PAUSED" if paused else "RUNNING"
    line = f"  ⚙ SimGarum  |  Tick: {tick}  |  Role: {role.upper()}  |  {status}  |  Tick: {tick_seconds:.2f}s"
    _safe_addstr(win, 0, 0, line, attr)


def render_assets_panel(win: curses.window, player, sim: Simulation) -> None:
    """Left panel: productive assets and their upkeep costs."""
    inv = player.inventory
    theme_fg, _, _ = ROLE_THEMES.get(player.role, (curses.COLOR_WHITE, curses.COLOR_BLACK, curses.COLOR_WHITE))

    # Title
    _safe_addstr(win, 0, 1, "── ASSETS ──", curses.A_BOLD | curses.color_pair(C_TITLE))

    row = 2
    lines: List[str] = []

    # Boat / Pan / Slot / Ship depending on role
    if player.role == "fisherman":
        lines.append(f"Boats:          {inv.boats}")
        lines.append(f"Upkeep:         {inv.boats * 1.0:.2f}g/tick")
    elif player.role == "salt-maker":
        lines.append(f"Pans:           {inv.pans}")
        lines.append(f"Upkeep:         {inv.pans * 1.0:.2f}g/tick")
    elif player.role == "producer":
        slots = len(player.producer_slots or [])
        lines.append(f"Slots:          {slots}")
        lines.append(f"Upkeep:         {slots * 0.5:.2f}g/tick")
        lines.append(f"Reputation:     {player.producer_reputation:.1f}")
        # Show current production progress per slot
        if player.producer_slots:
            lines.append("── Production ──")
            for idx, slot in enumerate(player.producer_slots, 1):
                if slot.progress > 0:
                    mode = slot.mode or "?"
                    dur = slot.target_duration or 1
                    pct = min(100, int(slot.progress / dur * 100))
                    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                    lines.append(f"  Slot {idx}: {mode:8s} [{bar}] {slot.progress}/{dur}")
                else:
                    lines.append(f"  Slot {idx}: idle")
    elif player.role == "merchant":
        lines.append(f"Ships:          {player.merchant_ships}")
        lines.append(f"Upkeep:         {player.merchant_ships * 0.5:.2f}g/tick")
        lines.append(f"Reputation:     {player.merchant_reputation:.1f}")
        lines.append(f"In transit:     {len(player.shipments)}")
        # Show active shipments
        if player.shipments:
            lines.append("── Shipments ──")
            for sh in player.shipments[:5]:
                lines.append(f"  → {sh.destination:12s} {sh.batch.quality_label:8s}  {sh.ticks_remaining} ticks left")
            if len(player.shipments) > 5:
                lines.append(f"  ... and {len(player.shipments) - 5} more")

    # Gold always shown
    lines.append("")
    lines.append(f"Gold:           {_fmt_gold(inv.gold)}")

    for i, line in enumerate(lines):
        if row + i >= win.getmaxyx()[0] - 1:
            break
        attr = curses.color_pair(theme_fg) | curses.color_pair(C_NOTE) if "Upkeep" in line or "Reputation" in line else curses.color_pair(theme_fg)
        _safe_addstr(win, row + i, 1, line, attr)


def render_stock_panel(win: curses.window, player, sim: Simulation) -> None:
    """Middle panel: current stock broken down by age/quality."""
    inv = player.inventory
    theme_fg, _, _ = ROLE_THEMES.get(player.role, (curses.COLOR_WHITE, curses.COLOR_BLACK, curses.COLOR_WHITE))

    _safe_addstr(win, 0, 1, "── STOCK ──", curses.A_BOLD | curses.color_pair(C_TITLE))

    row = 2
    lines: List[str] = []

    # Raw materials
    if player.role in ("fisherman", "producer"):
        lines.append("── Fish ──")
        if player.fish_stock:
            # Group by quality bands
            low = [f for f in player.fish_stock if f.quality < 30]
            mid = [f for f in player.fish_stock if 30 <= f.quality < 70]
            high = [f for f in player.fish_stock if f.quality >= 70]
            if high:
                lines.append(f"  High (≥70):   {len(high)} units  avg-q={sum(f.quality for f in high)/len(high):.1f}")
            if mid:
                lines.append(f"  Mid  (30-70): {len(mid)} units  avg-q={sum(f.quality for f in mid)/len(mid):.1f}")
            if low:
                lines.append(f"  Low  (<30):   {len(low)} units  avg-q={sum(f.quality for f in low)/len(low):.1f}")
            # Oldest 3
            oldest = sorted(player.fish_stock, key=lambda f: f.age, reverse=True)[:3]
            if oldest:
                lines.append(f"  Oldest:       {_fmt_age_quality(oldest[0].age, oldest[0].quality)}")
        else:
            lines.append("  (empty)")

    if player.role in ("salt-maker", "producer"):
        lines.append("")
        lines.append("── Salt ──")
        if player.salt_stock:
            low = [s for s in player.salt_stock if s.quality < 30]
            mid = [s for s in player.salt_stock if 30 <= s.quality < 70]
            high = [s for s in player.salt_stock if s.quality >= 70]
            if high:
                lines.append(f"  High (≥70):   {len(high)} units  avg-q={sum(s.quality for s in high)/len(high):.1f}")
            if mid:
                lines.append(f"  Mid  (30-70): {len(mid)} units  avg-q={sum(s.quality for s in mid)/len(mid):.1f}")
            if low:
                lines.append(f"  Low  (<30):   {len(low)} units  avg-q={sum(s.quality for s in low)/len(low):.1f}")
            oldest = sorted(player.salt_stock, key=lambda s: s.age, reverse=True)[:3]
            if oldest:
                lines.append(f"  Oldest:       {_fmt_age_quality(oldest[0].age, oldest[0].quality)}")
        else:
            lines.append("  (empty)")

    # Garum stock
    if player.role in ("producer", "merchant"):
        lines.append("")
        lines.append("── Garum ──")
        if player.role == "producer":
            batches = player.producer_batches
        else:
            batches = player.merchant_batches

        if batches:
            std = [b for b in batches if b.quality_label == "standard"]
            prem = [b for b in batches if b.quality_label == "premium"]
            lines.append(f"  Standard:     {len(std)} batch(es)")
            for b in std[:5]:
                lines.append(f"    age={b.age:2d}  {_quality_bar(b.quality_score, 12)}  q={b.quality_score:.1f}")
            if len(std) > 5:
                lines.append(f"    ... and {len(std) - 5} more")
            lines.append(f"  Premium:      {len(prem)} batch(es)")
            for b in prem[:5]:
                lines.append(f"    age={b.age:2d}  {_quality_bar(b.quality_score, 12)}  q={b.quality_score:.1f}")
            if len(prem) > 5:
                lines.append(f"    ... and {len(prem) - 5} more")
        else:
            lines.append("  (no garum batches)")

    # Amphorae
    if inv.empty_amphorae > 0:
        lines.append("")
        lines.append(f"Empty amphorae: {inv.empty_amphorae}")

    # Raw counts
    if inv.fish > 0:
        lines.append(f"Fish (total):   {inv.fish}")
    if inv.salt > 0:
        lines.append(f"Salt (total):   {inv.salt}")

    for i, line in enumerate(lines):
        if row + i >= win.getmaxyx()[0] - 1:
            break
        _safe_addstr(win, row + i, 1, line, curses.color_pair(theme_fg))


def render_market_panel(win: curses.window, player, sim: Simulation) -> None:
    """Right panel: local and merchant-facing prices, demand,
    consumer locations with shipping info."""
    theme_fg, _, _ = ROLE_THEMES.get(player.role, (curses.COLOR_WHITE, curses.COLOR_BLACK, curses.COLOR_WHITE))

    _safe_addstr(win, 0, 1, "── MARKET ──", curses.A_BOLD | curses.color_pair(C_TITLE))

    row = 2
    lines: List[str] = []

    # Local market prices (always shown)
    local = sim.markets.get(player.location)
    if local:
        lines.append(f"── {player.location} (local) ──")
        lines.append(f"  Std price:    {_fmt_gold(local.standard_price())}  (demand {local.standard_demand:.1f})")
        lines.append(f"  Prem price:   {_fmt_gold(local.premium_price())}  (demand {local.premium_demand:.1f})")

    # Distant markets (merchant-facing)
    lines.append("")
    lines.append("── Distant markets ──")
    for mkt in sim.markets.values():
        if mkt.location == player.location:
            continue
        dist = mkt.distance_from_baelo
        # Shipping time (approximate: distance + 1 ticks for standard, +2 for premium)
        ship_time_std = dist + 1
        ship_time_prem = dist + 2
        # Shipping cost per unit: 1.5 per distance (std), 1.8 per distance (prem)
        ship_cost_std = dist * 1.5
        ship_cost_prem = dist * 1.8

        lines.append(f"── {mkt.location} (dist={dist}) ──")
        lines.append(f"  Std price:    {_fmt_gold(mkt.standard_price())}")
        lines.append(f"  Prem price:   {_fmt_gold(mkt.premium_price())}")
        lines.append(f"  Std demand:   {mkt.standard_demand:.1f}")
        lines.append(f"  Prem demand:  {mkt.premium_demand:.1f}")

        # Premium requirements
        lines.append(f"  Prem quality: ≥{mkt.premium_quality_requirement:.0f}")
        lines.append(f"  Prem rep:     ≥{mkt.premium_reputation_requirement:.0f}")

        # Shipping info
        lines.append(f"  Ship time:    {ship_time_std}t (std) / {ship_time_prem}t (prem)")
        lines.append(f"  Ship cost:    {ship_cost_std:.1f}g (std) / {ship_cost_prem:.1f}g (prem)")

    for i, line in enumerate(lines):
        if row + i >= win.getmaxyx()[0] - 1:
            break
        attr = curses.color_pair(theme_fg)
        if line.startswith("──"):
            attr = curses.A_BOLD | curses.color_pair(C_TITLE)
        _safe_addstr(win, row + i, 1, line, attr)


def render_events_panel(win: curses.window, events: List[str],
                        role: str) -> None:
    """Bottom panel: scrolling event log + control hints."""
    h, _ = win.getmaxyx()
    max_events = max(h - 1, 1)

    # Control hints
    hint = "  [s]ell  [b]uy  [i]nvest  [n]ext-tick  [p]ause  [q]uit"
    _safe_addstr(win, h - 2, 0, hint, curses.A_DIM | curses.color_pair(C_NOTE))
    _safe_addstr(win, h - 1, 0, f"  Events (last {min(len(events), max_events)}):",
                 curses.A_BOLD | curses.color_pair(C_NOTE))

    row = h - 1
    for ev in reversed(events[-max_events:]):
        if row <= 0:
            break
        _safe_addstr(win, row - 1, 2, f"  {ev}"[:_visible_width(win, row - 1)],
                     event_color(ev))
        row -= 1


# ── placeholder action dialogs ───────────────────────────────────

def render_placeholder_dialog(win: curses.window, title: str,
                              body: str) -> None:
    """Render a simple centered placeholder dialog box."""
    h, w = win.getmaxyx()
    box_w = min(len(body) + 8, w - 2)
    box_h = 5
    start_y = max(0, (h - box_h) // 2)
    start_x = max(0, (w - box_w) // 2)

    # Draw border
    try:
        win.attron(curses.color_pair(C_BORDER))
        for dy in range(box_h):
            y = start_y + dy
            if y >= h:
                break
            if dy == 0:
                top = "┌" + "─" * (box_w - 2) + "┐"
            elif dy == box_h - 1:
                top = "└" + "─" * (box_w - 2) + "┘"
            else:
                top = "│" + " " * (box_w - 2) + "│"
            _safe_addstr(win, y, start_x, top, curses.color_pair(C_BORDER))
        win.attroff(curses.color_pair(C_BORDER))

        # Title
        title_line = f"  {title}  "
        _safe_addstr(win, start_y, start_x + 2, title_line[:box_w - 4],
                     curses.A_BOLD | curses.color_pair(C_HIGHLIGHT))

        # Body
        body_lines = body.splitlines()
        for i, bl in enumerate(body_lines):
            y = start_y + 2 + i
            if y >= h:
                break
            _safe_addstr(win, y, start_x + 2, bl[:box_w - 4],
                         curses.color_pair(C_NOTE))
    except curses.error:
        pass


# ── main render ──────────────────────────────────────────────────

def render(stdscr, sim: Simulation, role: str, tick: int,
           paused: bool, tick_seconds: float,
           active_dialog: Optional[str] = None) -> None:
    """Full-screen render with structured panels."""
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    if h < 10 or w < 40:
        _safe_addstr(stdscr, 0, 0, "Terminal too small", curses.A_BOLD)
        stdscr.refresh()
        return

    player = sim.get_role_player(role)

    # ── header ──────────────────────────────────────────────────
    header_win = curses.newwin(HEADER_H, w, 0, 0)
    render_header(header_win, role, tick, paused, tick_seconds)

    # ── compute panel geometry ──────────────────────────────────
    content_h = h - HEADER_H - FOOTER_H
    if content_h < 2:
        content_h = 2

    # Left panel (assets)
    left_w = max(12, int(w * LEFT_PANEL_W_RATIO))
    left_x = 0
    left_y = HEADER_H

    # Middle panel (stock)
    mid_w = max(20, int(w * MIDDLE_PANEL_W_RATIO))
    mid_x = left_x + left_w
    mid_y = HEADER_H

    # Right panel (market)
    right_w = max(20, w - left_x - left_w - mid_w)
    right_x = mid_x + mid_w
    right_y = HEADER_H

    # ── draw borders between panels ─────────────────────────────
    for y in range(left_y, left_y + content_h):
        if y < h - FOOTER_H:
            try:
                stdscr.addch(y, left_x + left_w, curses.ACS_VLINE,
                             curses.color_pair(C_BORDER))
                stdscr.addch(y, mid_x + mid_w, curses.ACS_VLINE,
                             curses.color_pair(C_BORDER))
            except curses.error:
                pass

    # ── left panel ──────────────────────────────────────────────
    left_win = curses.newwin(content_h, left_w, left_y, left_x)
    render_assets_panel(left_win, player, sim)
    left_win.refresh()

    # ── middle panel ────────────────────────────────────────────
    mid_win = curses.newwin(content_h, mid_w, mid_y, mid_x)
    render_stock_panel(mid_win, player, sim)
    mid_win.refresh()

    # ── right panel ─────────────────────────────────────────────
    right_win = curses.newwin(content_h, right_w, right_y, right_x)
    render_market_panel(right_win, player, sim)
    right_win.refresh()

    # ── events + footer ─────────────────────────────────────────
    footer_win = curses.newwin(FOOTER_H, w, h - FOOTER_H, 0)
    render_events_panel(footer_win, sim.recent_events, role)
    footer_win.refresh()

    # ── dialog overlay ──────────────────────────────────────────
    if active_dialog:
        # Dim background
        for y in range(h):
            for x in range(w):
                try:
                    stdscr.addch(y, x, ' ', curses.color_pair(C_DIM) | curses.A_DIM)
                except curses.error:
                    break
        # Dialog box
        dialog_win = curses.newwin(h, w, 0, 0)
        if active_dialog == "sell":
            render_placeholder_dialog(dialog_win, "SELL",
                "Sell action not yet implemented.\nPress ESC to return.")
        elif active_dialog == "buy":
            render_placeholder_dialog(dialog_win, "BUY",
                "Buy action not yet implemented.\nPress ESC to return.")
        elif active_dialog == "invest":
            render_placeholder_dialog(dialog_win, "INVEST",
                "Invest action not yet implemented.\nPress ESC to return.")
        dialog_win.refresh()

    stdscr.refresh()


# ── role chooser ─────────────────────────────────────────────────

def choose_role(stdscr, random_enabled: bool = False) -> str:
    if random_enabled:
        import random
        return random.choice(["fisherman", "salt-maker", "producer", "merchant"])

    idx = 0
    roles = ["fisherman", "salt-maker", "producer", "merchant"]
    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "SimGarum – choose your role", curses.A_BOLD)
        stdscr.addstr(3, 2, "Arrow keys / j,k  |  r = random  |  Enter = confirm")
        for i, role in enumerate(roles):
            attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
            theme_fg = ROLE_THEMES.get(role, (curses.COLOR_WHITE,))[0]
            stdscr.addstr(5 + i, 4, role, attr | curses.color_pair(theme_fg))
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('k')):
            idx = (idx - 1) % len(roles)
        elif key in (curses.KEY_DOWN, ord('j')):
            idx = (idx + 1) % len(roles)
        elif key in (10, 13, curses.KEY_ENTER):
            return roles[idx]
        elif key in (ord('r'), ord('R')):
            import random
            return random.choice(roles)


# ── main UI loop ─────────────────────────────────────────────────

def run_ui(stdscr, ticks: int, tick_seconds: float, seed: int | None,
           producer_mode: str, random_role: bool) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    # Initialise colour pairs
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(C_DEFAULT,    curses.COLOR_WHITE, -1)
    curses.init_pair(C_GOOD,       curses.COLOR_GREEN, -1)
    curses.init_pair(C_WARN,       curses.COLOR_YELLOW, -1)
    curses.init_pair(C_NOTE,       curses.COLOR_CYAN, -1)
    curses.init_pair(C_TITLE,      curses.COLOR_WHITE, -1)
    curses.init_pair(C_HIGHLIGHT,  curses.COLOR_RED, -1)
    curses.init_pair(C_DIM,        curses.COLOR_BLACK, curses.COLOR_BLACK)
    curses.init_pair(C_BORDER,     curses.COLOR_WHITE, -1)

    role = choose_role(stdscr, random_enabled=random_role)
    sim = Simulation(seed=seed, producer_mode=producer_mode, tick_duration_seconds=0.0)
    paused = False
    tick = 0
    last_tick = time.time()
    active_dialog: Optional[str] = None

    while True:
        render(stdscr, sim, role, tick, paused, tick_seconds, active_dialog)
        now = time.time()
        key = stdscr.getch()

        # Dialog escape
        if active_dialog and key == 27:  # ESC
            active_dialog = None
            continue

        # Dialog actions
        if active_dialog:
            if key in (ord('q'), ord('Q')):
                break
            continue

        # Normal controls
        if key in (ord('q'), ord('Q')):
            break
        elif key in (ord('p'), ord('P')):
            paused = not paused
        elif key == ord(' ') and paused and tick < ticks:
            tick += 1
            sim.step(tick, verbose=False)
        elif key == ord('n') and not paused and tick < ticks:
            tick += 1
            sim.step(tick, verbose=False)
        elif not paused and tick < ticks and now - last_tick >= tick_seconds:
            tick += 1
            sim.step(tick, verbose=False)
            last_tick = now
        elif key == ord('s') and tick < ticks:
            active_dialog = "sell"
        elif key == ord('b') and tick < ticks:
            active_dialog = "buy"
        elif key == ord('i') and tick < ticks:
            active_dialog = "invest"

        if tick >= ticks:
            paused = True

        time.sleep(0.03)


def main() -> None:
    parser = argparse.ArgumentParser(description="SimGarum ncurses UI")
    parser.add_argument("--ticks", type=int, default=120)
    parser.add_argument("--tick-seconds", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--producer-mode",
                        choices=["standard", "premium", "weighted"],
                        default="weighted")
    parser.add_argument("--random-role", action="store_true")
    args = parser.parse_args()
    curses.wrapper(run_ui, args.ticks, args.tick_seconds, args.seed,
                   args.producer_mode, args.random_role)


if __name__ == "__main__":
    main()
