from __future__ import annotations

import argparse
import curses
import time
from typing import List

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


def render(stdscr, sim: Simulation, role: str, tick: int, paused: bool, tick_seconds: float) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    player = sim.get_role_player(role)
    merchant = sim.get_role_player("merchant")
    producer = sim.get_role_player("producer")

    lines: List[str] = [
        f"SimGarum ncurses playtest", 
        f"Tick: {tick}    Role: {role}    Tick delay: {tick_seconds:.2f}s    {'PAUSED' if paused else 'RUNNING'}",
        "",
        f"You: gold={player.inventory.gold:.2f} fish={player.inventory.fish} salt={player.inventory.salt} boats={player.inventory.boats} pans={player.inventory.pans}",
        f"Producer rep={producer.producer_reputation:.1f} batches={len(producer.producer_batches)} slots={len(producer.producer_slots or [])}",
        f"Merchant rep={merchant.merchant_reputation:.1f} ships={merchant.merchant_ships} in_transit={len(merchant.shipments)}",
        "",
        "Markets:",
    ]
    for market in sim.markets.values():
        lines.append(
            f"- {market.location}: std={market.standard_price():.2f} prem={market.premium_price():.2f} std_dem={market.standard_demand:.1f} prem_dem={market.premium_demand:.1f}"
        )

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

    for i, line in enumerate(lines[: h - 1]):
        stdscr.addstr(i, 0, line[: max(1, w - 1)])
    stdscr.refresh()


def run_ui(stdscr, ticks: int, tick_seconds: float, seed: int | None, producer_mode: str, random_role: bool) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

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
