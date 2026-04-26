# SimGarum

A Garum economy game and Python simulation for the economics of garum production and trade.

## Initial model

This first version implements:

- fixed anchor prices for raw materials
- effectively unlimited market supply for fish, salt, and amphoras
- anchored raw-material prices with softer external demand caps for raw-material sellers
- player trading via market venues only
- deterministic per-round production by occupation
- dynamic market demand and pricing for garum only
- location-specific garum demand by quality

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

- Standard garum: 10.0 gold
- Premium garum: 22.0 gold
- Merchant resale markup: 25%
- Merchant wholesale discount from venue price: 12% for standard, 6% for premium

## Production rules per tick

- Fisherman: 5 fish per boat
- Salt-maker: 10 salt per pan
- Producer:
  - starts with 2 production slots
  - standard garum takes 3 ticks and consumes 5 fish + 2 salt per amphora
  - premium garum takes 6 ticks and consumes 4 fish + 2 salt per amphora

## Starting inventories

- Fisherman: 1 boat
- Salt-maker: 1 pan
- Producer: 2 empty amphorae, 10 fish, 4 salt
- Merchant: 20 gold

## Running

```bash
python3 sim_garum.py
```

The script prints a per-tick summary and a final state dump.

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
