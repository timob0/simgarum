from __future__ import annotations

import argparse
import curses
import time
from typing import List


COLOR_DEFAULT = 1
COLOR_GOOD = 2
COLOR_WARN = 3
COLOR_NOTE = 4

from .engine import Simulation


ROLE_ORDER = ["fisherman", "salt-maker", "producer", "merchant"]


def choose_role(stdscr, random_enabled: bool = False) -> str:
    if random_enabled:
        import random
        return random.choice(ROLE_ORDER)

    idx = 0
    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "SimGarum, choose your role", curses.A_BOLD)
        stdscr.addstr(3, 2, "Use arrow keys, press Enter. Press r for random role.")
        for i, role in enumerate(ROLE_ORDER):
            attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
            stdscr.addstr(5 + i, 4, role, attr)
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('k')):
            idx = (idx - 1) % len(ROLE_ORDER)
        elif key in (curses.KEY_DOWN, ord('j')):
            idx = (idx + 1) % len(ROLE_ORDER)
        elif key in (10, 13, curses.KEY_ENTER):
            return ROLE_ORDER[idx]
        elif key in (ord('r'), ord('R')):
            import random
            return random.choice(ROLE_ORDER)


def fmt_delta(value: float) -> str:
    if value > 0:
        return f"+{value}"
    return str(value)


def event_color(event: str) -> int:
    low = event.lower()
    if any(word in low for word in ["sells", "buys a new", "adds a new", "completes"]):
        return COLOR_GOOD
    if any(word in low for word in ["spoilage", "loses", "downgrades"]):
        return COLOR_WARN
    return COLOR_NOTE


def render(stdscr, sim: Simulation, role: str, tick: int, paused: bool, tick_seconds: float) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    player = sim.get_role_player(role)
    merchant = sim.get_role_player("merchant")
    producer = sim.get_role_player("producer")

    deltas = sim.last_tick_deltas
    fdelta = deltas.get('fisherman', {})
    sdelta = deltas.get('salt-maker', {})
    pdelta = deltas.get('producer', {})
    mdelta = deltas.get('merchant', {})

    lines: List[str] = [
        f"SimGarum ncurses playtest", 
        f"Tick: {tick}    Role: {role}    Tick delay: {tick_seconds:.2f}s    {'PAUSED' if paused else 'RUNNING'}",
        "",
        f"You: gold={player.inventory.gold:.2f} fish={player.inventory.fish} salt={player.inventory.salt} boats={player.inventory.boats} pans={player.inventory.pans}",
        f"Fisherman: gold={sim.get_role_player('fisherman').inventory.gold:.2f} ({fmt_delta(fdelta.get('gold', 0))})  fish={sim.get_role_player('fisherman').inventory.fish} ({fmt_delta(fdelta.get('fish', 0))})  boats={sim.get_role_player('fisherman').inventory.boats}",
        f"Salt-maker: gold={sim.get_role_player('salt-maker').inventory.gold:.2f} ({fmt_delta(sdelta.get('gold', 0))})  salt={sim.get_role_player('salt-maker').inventory.salt} ({fmt_delta(sdelta.get('salt', 0))})  pans={sim.get_role_player('salt-maker').inventory.pans}",
        f"Producer: gold={producer.inventory.gold:.2f} ({fmt_delta(pdelta.get('gold', 0))}) rep={producer.producer_reputation:.1f} batches={len(producer.producer_batches)} ({fmt_delta(pdelta.get('producer_batches', 0))}) slots={len(producer.producer_slots or [])}",
        f"Merchant: gold={merchant.inventory.gold:.2f} ({fmt_delta(mdelta.get('gold', 0))}) rep={merchant.merchant_reputation:.1f} ships={merchant.merchant_ships} transit={len(merchant.shipments)} ({fmt_delta(mdelta.get('shipments', 0))})",
        "",
        "Markets:",
    ]
    for market in sim.markets.values():
        lines.append(
            f"- {market.location}: std={market.standard_price():.2f} prem={market.premium_price():.2f} std_dem={market.standard_demand:.1f} prem_dem={market.premium_demand:.1f}"
        )

    lines += [
        "",
        "Recent tick events:",
    ]
    lines.extend([f"  - {event}" for event in sim.recent_events[-10:]])
    lines += [
        "",
        "Controls:",
        "  SPACE step one tick when paused",
        "  p pause/resume",
        "  q quit",
        "",
        "This first client is observational. It lets a human pick a role and watch the economy evolve.",
        "Interactive actions per role are the next layer.",
    ]

    row = 0
    for line in lines[: h - 14]:
        stdscr.addstr(row, 0, line[: max(1, w - 1)], curses.color_pair(COLOR_DEFAULT))
        row += 1

    if row < h - 1:
        stdscr.addstr(row, 0, "", curses.color_pair(COLOR_DEFAULT))
        row += 1
    if row < h - 1:
        stdscr.addstr(row, 0, "Recent tick events:", curses.A_BOLD | curses.color_pair(COLOR_DEFAULT))
        row += 1

    for event in sim.recent_events[-min(10, max(1, h - row - 2)):]:
        if row >= h - 1:
            break
        stdscr.addstr(row, 0, f"  - {event}"[: max(1, w - 1)], curses.color_pair(event_color(event)))
        row += 1

    stdscr.refresh()


def run_ui(stdscr, ticks: int, tick_seconds: float, seed: int | None, producer_mode: str, random_role: bool) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_DEFAULT, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_GOOD, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_WARN, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_NOTE, curses.COLOR_CYAN, -1)

    role = choose_role(stdscr, random_enabled=random_role)
    sim = Simulation(seed=seed, producer_mode=producer_mode, tick_duration_seconds=0.0)
    paused = False
    tick = 0
    last_tick = time.time()

    while True:
        render(stdscr, sim, role, tick, paused, tick_seconds)
        now = time.time()
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break
        elif key in (ord('p'), ord('P')):
            paused = not paused
        elif key == ord(' ') and paused and tick < ticks:
            tick += 1
            sim.step(tick, verbose=False)
        elif not paused and tick < ticks and now - last_tick >= tick_seconds:
            tick += 1
            sim.step(tick, verbose=False)
            last_tick = now

        if tick >= ticks:
            paused = True
        time.sleep(0.03)


def main() -> None:
    parser = argparse.ArgumentParser(description="SimGarum ncurses UI")
    parser.add_argument("--ticks", type=int, default=120)
    parser.add_argument("--tick-seconds", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--producer-mode", choices=["standard", "premium", "weighted"], default="weighted")
    parser.add_argument("--random-role", action="store_true")
    args = parser.parse_args()
    curses.wrapper(run_ui, args.ticks, args.tick_seconds, args.seed, args.producer_mode, args.random_role)


if __name__ == "__main__":
    main()
