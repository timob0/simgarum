# SimGarum

A Garum economy game and Python simulation for the economics of garum production and trade.

## Current model

This version implements:

- fixed anchor prices for raw materials
- effectively unlimited market supply for fish, salt, and amphoras
- external raw-material demand that is softer than player-to-player supply
- dynamic market demand and pricing for garum
- location-specific garum demand by quality
- merchant shipping delays and distance-based shipping costs
- a local outlet for standard garum near production centers
- batch quality, reputation, and perishability mechanics for garum
- location-specific premium quality and reputation requirements
- capital expansion for every role

## Roles

- Fisherman
- Salt-maker
- Garum producer
- Merchant

## Fixed raw material prices

- Fish: 1.0 gold
- Salt: 0.5 gold
- Amphora: free, unlimited

## Garum base values

- Standard garum: 12.0 gold
- Premium garum: 22.0 gold
- Merchant resale markup: 18%
- Merchant wholesale discount from venue price: 8% for standard, 4% for premium

## Production rules per tick

- Fisherman: 5 fish per boat
- Salt-maker: 10 salt per pan
- Producer:
  - starts with 2 production slots
  - standard garum can be sold locally near production centers
  - standard garum takes 3 ticks and consumes 5 fish + 2 salt per amphora
  - premium garum takes 6 ticks and consumes 4 fish + 2 salt per amphora
  - longer, more consistent fermentation increases quality and producer reputation
- Merchant:
  - reputation can be earned through consistent standard and premium trade
  - premium trade depends on market-specific quality and reputation requirements
  - softer premium markets can accept trial premium sales before full reputation unlock
  - premium batches can be downgraded if quality or reputation is insufficient
  - garum can spoil if held or shipped too long, currently after 15 ticks for standard and 18 ticks for premium
- Merchant:
  - starts with 1 ship
  - shipping takes time based on distance to market
  - shipping costs gold based on distance and garum quality
  - ship count limits throughput

## Starting inventories

- Fisherman: 1 boat
- Salt-maker: 1 pan
- Producer: 30 gold, 2 empty amphorae, 10 fish, 4 salt
- Merchant: 80 gold, 1 ship

## Expansion

- New fishing boat: 60 gold
- New salt pan: 60 gold
- New production slot: 80 gold
- New merchant ship: 140 gold

## Running

CLI simulation:

```bash
python3 sim_garum.py
```

Optional real-time tick delay:

```bash
python3 sim_garum.py --tick-seconds 0.5
```

The script prints a per-tick summary and a final state dump.

## Linux ncurses playtest UI

A structured ncurses client is available on Linux:

```bash
python3 -m simgarum.ncurses_ui --tick-seconds 0.5
```

### Layout

The screen is split into five panels:

1. **Header** – role, tick number, running/paused state, tick delay.
2. **Assets** (left) – productive assets (boats, pans, slots, ships)
   with their per-tick upkeep costs and, where relevant, production
   progress bars or active shipment list.
3. **Stock** (center) – current inventory broken down by quality band
   (high/mid/low) with quality bars and age information for raw
   materials, and per-batch quality+age for garum.
4. **Market** (right) – local venue prices plus all distant markets
   with per-market shipping time, shipping cost, demand, and premium
   quality/reputation requirements.
5. **Events** (bottom) – scrolling event log with colour-coded entries
   (green = gains, yellow = losses).

### Controls

| Key       | Action                                                    |
| `j`/`↓`   | Move down in role chooser                                 |
| `k`/`↑`   | Move up in role chooser                                   |
| `r`       | Random role in role chooser                               |
| `Enter`   | Confirm role selection                                    |
| `SPACE`   | Step one tick (when paused)                               |
| `n`       | Step one tick (when running)                              |
| `p`       | Pause / resume                                            |
| `s`       | Open sell dialog (placeholder)                            |
| `b`       | Open buy dialog (placeholder)                             |
| `i`       | Open invest dialog (placeholder)                          |
| `ESC`     | Close placeholder dialog                                  |
| `q`       | Quit                                                      |

### Current status

- Structured panel layout with role-specific colour themes
- Stock broken down by quality bands and age
- Separate asset panel with upkeep costs and production/shipment details
- Market panel with distant-market shipping info and premium requirements
- Action keys scaffolded (sell/buy/invest show placeholder dialogs)
- Runs the same engine as the CLI simulation
- Supports pause/resume, manual stepping, and random role selection

## Monte Carlo balance checks

Run many simulated games to inspect whether the economy stays plausible:

```bash
python3 sim_garum.py --runs 100 --ticks 60
```

Useful options:

- `--producer-mode standard`
- `--producer-mode premium`
- `--producer-mode weighted`
- `--seed 42`
