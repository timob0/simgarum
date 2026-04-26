# 🏛️ SIMGARUM — A Roman Garum Trade Empire Simulation

> *From fish to fortune — build your garum empire across the Roman world.*

---

## 1. Setting

### The World

The year is **50 BCE**. The Roman Republic is in turmoil. Civil wars, political upheaval, and the rise of powerful individuals reshape the Mediterranean world. Yet amid the chaos, one industry thrives: the production and trade of **garum**.

Garum is a fermented fish sauce — the ketchup, soy sauce, and Worcestershire sauce of the ancient world. Made from fish, salt, and time, it is the cornerstone of Roman cuisine. From the imperial kitchens of Rome to the mess tents of legions stationed along the Rhine and in Britain, garum is everywhere.

The trade network stretches across three continents:

- **Production** in the south: Hispania (modern Spain), Mauretania (modern Morocco), and the North African coast produce the raw materials — fish and salt — and ferment them into garum.
- **Distribution** through the Mediterranean: Amphorae of garum are loaded onto ships at production ports and carried across the sea to consumption centers.
- **Consumption** across the empire: Rome, Ostia, Lugdunum (Lyon), Londinium (London), Alexandria, and every Roman settlement in between demand garum.

### The Era

The game spans **50 years** of Roman history — from the twilight of the Republic through the early years of the Empire. During this period:

- Garum production reaches its peak
- Trade networks expand as the empire grows
- Infrastructure improves, reducing transport times
- New markets open as Roman legions push into new territories
- Eventually, changing tastes and substitute products begin to erode demand

The era is **configurable per game round** — a new game can be set for 10, 50, 100, or up to 400 years.

---

## 2. Economic Assumptions

### The Current Prototype Supply Chain

```
Fishers ──→ fish ──┐
                    ├──→ Producers ──→ standard / premium garum ──→ local market or merchant export
Salt-makers ─→ salt ┘
```

The current prototype model is intentionally simpler than the long-term design. It focuses on the core economic loop first:

1. **Fishers** produce fish each tick.
2. **Salt-makers** produce salt each tick.
3. **Producers** combine fish and salt in amphorae and ferment garum over several ticks.
4. **Standard garum** can be sold into a nearby local market.
5. **Premium garum** is mainly sold through merchants into distant, higher-value markets.
6. **Merchants** must balance quality, reputation, shipping time, storage risk, and perishability.

### Fixed Anchor Prices for Raw Materials

The current model uses fixed gold anchor prices for the main inputs:

| Resource | Price |
|---|---:|
| **Fish** | 1.0 gold |
| **Salt** | 0.5 gold |
| **Empty amphorae** | free and unlimited |

These prices are intentionally stable so that the first balancing work can focus on garum production, quality, reputation, and trade rather than on raw-material price volatility.

However, raw materials are **not** perfectly stable in storage:

- fish quality decays quickly and fish eventually spoils
- salt quality decays more slowly, but old salt eventually becomes unusable too

So even with fixed anchor prices, stockpiling raw inputs is risky.

### Garum Value Channels

Garum is where most market dynamics happen.

| Channel | Description |
|---|---|
| **Local standard market** | Nearby sales lane for standard garum near the production zone |
| **Merchant standard export** | Standard garum can also be exported, but it is not the main value path |
| **Merchant premium export** | Higher-value path for consistent, high-quality garum |

Base values in the current prototype:

| Good | Base Value |
|---|---:|
| **Standard garum** | 12.0 gold |
| **Premium garum** | 22.0 gold |

Merchant trade is not a flat guaranteed arbitrage. In the current model, merchants face:

- shipping costs based on route distance
- travel time while ships are in transit
- reputation requirements for premium markets
- downgrade risk if quality or reputation is insufficient
- perishability if garum is held too long in stock or transit

### Quality, Reputation, and Perishability

Premium garum is no longer unlocked simply by waiting longer once. It depends on repeated consistency.

- Each batch receives a **quality score**.
- Longer fermentation tends to raise quality, but ties up production capacity.
- **Input freshness matters**: old fish and old salt reduce the quality ceiling of the final garum batch, with fish quality weighing more heavily than salt quality.
- Producers gain **reputation** through repeated, consistent batches.
- Merchants also gain **reputation** through consistently handling and selling quality stock.
- Premium markets require both a minimum **quality level** and a minimum **merchant reputation**.
- Softer markets may accept **trial premium sales** before full reputation unlock.
- Garum can **perish** while held by producers or merchants.

Current perishability and decay limits:

| Good | Rule |
|---|---|
| **Fish** | starts at quality 10, loses 1 quality per tick, spoils at 0 |
| **Salt** | starts at quality 12, loses 0.35 quality per tick, becomes unusable at 0 |
| **Standard garum** | perishes after 15 ticks |
| **Premium garum** | perishes after 18 ticks |

This means overproduction is dangerous for everyone in the chain. If fishers, salt-makers, producers, or merchants expand faster than sell-through allows, value is destroyed rather than safely stockpiled.

In the current simulator, both producers and merchants are also increasingly **demand-aware**:

- producers should not lean too hard into premium if the merchant channel is not mature enough to absorb it
- merchants should avoid buying premium stock they cannot realistically move before it degrades or perishes

---

## 3. Game Mechanics

### Time

In the current prototype, the simulation advances in **ticks**. The code is currently tuned as a balancing simulator rather than a finished live service, so the exact real-time mapping is still open. A useful mental model is:

- **1 tick = 1 production / market step**
- fermentation, shipping, storage, spoilage, and expansion all evolve tick by tick

### The Current Core Loop

Each role participates in one part of the same chain:

```
fish / salt production → garum fermentation → local or export sale → reinvestment into capacity
```

### Resources

| Resource | Description |
|---|---|
| **Fish** | Raw input produced by fishermen |
| **Salt** | Raw input produced by salt-makers |
| **Garum batches** | Fermented output with quality and age |
| **Amphorae** | Free and effectively unlimited containers in the current model |
| **Merchant ships** | Export capacity for distant trade |
| **Gold** | Working capital and expansion currency |

### Locations in the Current Prototype

The current simulation uses three principal locations:

| Location | Role in the Economy |
|---|---|
| **Baelo** | Production zone, local standard market, close interaction between fishers, salt-makers, and producers |
| **Rome** | Premium-oriented consumption market with higher-value export demand |
| **Alexandria** | More standard-oriented distant market with additional export demand |

### Production, Processing, and Consumption Geography

The model currently assumes:

- **fishers, salt-makers, and producers are clustered near one another** in the production zone
- **standard garum has a local outlet** near production
- **premium garum is mainly worth shipping outward** to more demanding consumer markets
- distant premium markets are harder to access because they require both quality and merchant credibility

### Travel and Stock Risk

Merchants do not teleport product. In the current prototype:

- each ship can only handle limited throughput
- ships are occupied while cargo is in transit
- distance affects both **time** and **cost**
- garum ages while traveling
- aged stock can perish before sale

This means shipping is not just a profit multiplier, it is a risk management problem.

---

## 4. Player Starting Conditions

### Playable Roles in the Current Prototype

The current model has four playable economic roles:

| Role | Starting Position | Starting Resources |
|---|---|---|
| **Fisherman** | Raw fish producer in the production zone | 1 boat |
| **Salt-maker** | Raw salt producer in the production zone | 1 pan |
| **Garum Producer** | Fermentation and quality-management role | 30 gold, 2 empty amphorae, 10 fish, 4 salt, 2 production slots |
| **Merchant** | Export and market-access role | 80 gold, 1 ship |

### Role-by-Role Summary

#### Fisherman

- Produces **5 fish per boat per tick**
- Sells into the broader raw-material market at the fixed fish anchor price
- Feeds value into the system by supplying the fish input needed by producers
- Main growth path: more boats

#### Salt-maker

- Produces **10 salt per pan per tick**
- Sells into the broader raw-material market at the fixed salt anchor price
- Feeds value into the system by supplying the salt input needed by producers
- Main growth path: more salt pans

#### Garum Producer

- Converts fish and salt into fermenting garum batches
- Starts with **2 production slots**, so can run multiple batches in parallel
- Decides between throughput, quality consistency, and market timing
- Can sell **standard garum locally** or route high-quality output into the merchant channel
- Feeds value into the system by transforming cheap anchored inputs into higher-value finished goods

#### Merchant

- Buys sellable garum from producers
- Ships it to distant markets
- Earns value through market access, logistics, quality screening, and reputation
- Feeds value into the system by connecting production zones to richer demand centers
- Must avoid buying more than can realistically be sold before perishability destroys the margin

### Expansion Rules in the Current Model

The current prototype uses explicit expansion thresholds:

| Role | Expansion | Cost | Trigger Threshold |
|---|---|---:|---:|
| **Fisherman** | +1 boat | 60 gold | expands at 120 gold |
| **Salt-maker** | +1 pan | 60 gold | expands at 120 gold |
| **Producer** | +1 production slot | 80 gold | expands at 130 gold |
| **Merchant** | +1 ship | 140 gold | expands at 260 gold |

The thresholds are higher than the purchase prices because each role is expected to keep a safety buffer rather than expanding the instant it can barely afford to do so.

### Ongoing Operating Costs

Expansion is no longer free once purchased. In the current prototype, each productive asset has a per-tick upkeep cost:

| Asset | Upkeep per Tick |
|---|---:|
| **Boat** | 0.5 gold |
| **Salt pan** | 0.5 gold |
| **Production slot** | 0.5 gold |
| **Merchant ship** | 0.5 gold |

This upkeep is an important balancing mechanism. It prevents all four roles from expanding blindly without regard to whether their extra capacity can actually be used profitably.

### What Each Role Is Really Managing

| Role | Main Constraint | Main Value Channel |
|---|---|---|
| **Fisherman** | production volume vs. demand absorption | fish sales into the production economy |
| **Salt-maker** | production volume vs. demand absorption | salt sales into the production economy |
| **Producer** | slot time, quality consistency, spoilage risk | local standard sales plus selective premium supply |
| **Merchant** | sell-through capacity, reputation, transit risk | export margin on quality-controlled garum |

---

## 5. Development and Trading Options

### Current Prototype Notes

> **Implementation status note:** Everything in Sections 2 to 4 is intended to describe the current prototype model as closely as possible. From this point onward, some handbook material describes the broader intended game rather than mechanics already implemented in the simulator. Those future-facing sections are marked explicitly below.

The current Python prototype is not yet a full empire-scale grand simulation. It is a focused economic model designed to answer a smaller question first:

> Can fishers, salt-makers, producers, and merchants all occupy useful and distinct roles in a shared garum economy?

At this stage, the model already includes:

- role-specific expansion
- local standard sales
- distant premium exports
- batch quality
- producer and merchant reputation
- market-specific premium expectations
- stock perishability
- demand-aware merchant purchasing
- input freshness effects from fish and salt into garum quality
- a first multi-panel ncurses playtest frontend

Features that may still evolve later include:

- direct player-to-player deals outside market venues
- richer contract systems
- more locations and route specializations
- military or institutional buyers
- fuller era progression across decades of Roman history

The handbook sections below describe the broader intended direction of the game, but the sections above reflect the **current working prototype** most closely.


> **Status: partially implemented / partially planned**
>
> The simulator already implements fermentation time, quality emergence, local standard sales, premium export logic, merchant shipping, expansion, reputation, and spoilage.
>
> The simulator does **not** yet implement all of the detailed production ratios, public venue interactions, contract trading, packaging steps, or location-by-location facility specializations described below.

### Production

- **Combine fish and salt** in your production facility to create garum.
- Production time varies by **location**, **quality tier**, and **recipe**:

  | Quality | Cartagena | Cádiz | Other Locations |
  |---|---|---|---|
  | Poor | 2 ticks (2 months) | 2 ticks | 3 ticks (3 months) |
  | Standard | 3 ticks (3 months) | 3 ticks | 4 ticks (4 months) |
  | Premium | 3 ticks (3 months) | 3 ticks | 6 ticks (6 months) |
  | Premium+ | 4 ticks (4 months) | 4 ticks | 6 ticks (6 months) |

  Top-grade garum (Premium+) takes up to **6 months** at less ideal locations.

- Input: 10 fish + 2 salt → 5 garum (standard ratio).
- **Multiple facilities**: Each production facility processes one batch at a time. Own more facilities for more parallel batches.
- Quality depends on **location conditions** and **facility level** (see Upgrades below).

> **Not yet implemented as a separate step in the simulator.** In the current prototype, amphorae are free and effectively unlimited, and packaging is not modeled as its own time-consuming action.

### Packaging

- **Convert garum into amphorae** for transport and sale.
- Input: 1 garum + 2 amphorae → 2 packaged garum (each amphora holds 1 unit).
- Amphorae are consumed in the process.
- Packaging takes **1 tick** and can be done at any production facility or at a public trading venue.

> **Partially implemented.** Shipping time, ship occupancy, route distance, perishability in transit, and merchant ship expansion exist in the simulator. Fixed named route tables and a broader multi-location network as described below are still planned rather than fully implemented.

### Shipping

- **Dispatch ships** between locations with cargo.
- Ships carry amphorae of garum, raw materials, or other goods.
- Ships are busy during transit — they cannot accept new orders.
- You can dispatch multiple ships simultaneously on different routes.

> **Partially implemented.** The simulator models market sales and merchant purchasing behavior, but it does not yet expose full player-to-player trading flows or live venue negotiation in the richer sense described below.

### Trading

- **Buy and sell** with NPCs at any location.
- **Buy and sell** with other players at any location.
- **Negotiate contracts** for future delivery at a premium price.
  - Contracts specify quantity, location, delivery date, and price.
  - **Non-fulfillment penalty**: Lose 20% of contract value in gold + lose reputation points.
  - **Fulfillment bonus**: Earn extra gold and gain reputation.

> **Described differently than the current prototype.** The simulator currently models expansion by buying more boats, pans, production slots, and merchant ships. It does **not** yet implement facility upgrade levels such as production tier upgrades or shipyard upgrades.

### Upgrading Facilities

Every facility — fishing grounds, salt pans, production facilities, shipyards — can be upgraded by investing gold.

| Facility Type | Upgrade Cost | Effect |
|---|---|---|
| **Fishing Grounds** | 500 gold | +20% fish catch per tick |
| **Salt Pans** | 500 gold | +20% salt yield per tick |
| **Production Facility** | 1,000 gold | +1 quality tier (Poor → Standard → Premium → Premium+) |
| **Shipyard** | 1,500 gold | -1 tick ship construction time |

**How it works:**

1. Select a facility at your location.
2. Invest the required gold amount.
3. The upgrade takes **1 tick** to complete.
4. Quality increases by **1 tier** for production facilities:
   - Poor (×0.8 price) → Standard (×1.0) → Premium (×1.5) → Premium+ (×2.0)
5. Other upgrades take effect immediately upon completion.

**Multiple upgrades**: You can upgrade the same facility multiple times. A production facility can reach Premium+ (the highest tier). A shipyard can be upgraded multiple times (each upgrade reduces ship construction by 1 tick, minimum 1 tick).

**All occupations benefit equally** from upgrades. A Fisherman who buys a production facility upgrades it the same way as a Garum Producer.

> **Planned, not yet implemented in this full form.** The current simulator uses market logic and demand channels, but not fully interactive public trading venues with explicit player-visible order interaction.

### Public Trading Venues

Warehouses are **public infrastructure** — they are not owned by any player. Each location has a trading venue where:

- **Market prices** are determined by the aggregate supply and demand of all players and NPCs.
- **Players trade** with NPCs and with each other.
- **Future contracts** are struck — agreements to buy or sell garum at a specified future date and price.
- **Price discovery** happens organically: when many players sell garum at Ostia, the price drops. When supply is low, prices rise.

No player can control or monopolize a trading venue. The market is open to all.

> **Not yet implemented.** Future contracts, deposits, penalties, secondary contract trading, and delivery obligations are still design material rather than active simulator mechanics.

### Contracts

Future contracts allow you to lock in prices:

1. You commit to deliver X amphorae of garum to Location Y by tick Z at price P per amphora.
2. The buyer pays a deposit (10% of contract value).
3. If you fulfill on time: you receive the full price + a bonus.
4. If you fail to fulfill: you lose the deposit, pay a penalty (20% of contract value), and lose reputation.

Contracts can be **traded between players** — if you can't fulfill, you can sell the contract to someone who can. This creates a secondary market for delivery obligations.

---

## 6. Reputation

> **Partially implemented, but differently from the older text below.**
>
> The current simulator uses a continuous numerical reputation model for both producers and merchants rather than the handbook's older 1-to-10 prestige ladder. Reputation is currently driven mainly by quality consistency and sale execution, especially for premium access. The rank names and unlock bands below should therefore be read as future-facing flavor design, not as an exact description of the current code.

Reputation is a simple scale from **1 to 10** that affects your business:

| Reputation | Title | Unlocks |
|---|---|---|
| 1–2 | Unknown | Basic trading only |
| 3–4 | Noted | Access to mid-tier markets |
| 5–6 | Renowned | Military contracts (requires Premium garum) |
| 7–8 | Esteemed | Royal contracts (requires Premium garum) |
| 9–10 | Legendary | Exclusive deals, best prices |

Reputation increases by:
- Filling contracts on time
- Selling to high-profile customers
- Consistent quality (Premium garum sells for more and builds reputation faster)

Reputation decreases by:
- Failing to fulfill contracts
- Selling poor-quality product to premium buyers

---

## 7. Bankruptcy and End Game

> **Mostly planned, not yet implemented in full.** The current simulator is still a balancing model. It tracks gold, expansion, production, shipping, spoilage, and sales, but it does not yet implement the full bankruptcy, liquidation, round-ending, or winner-determination rules described below.

### Bankruptcy

You go bankrupt when:
- Your **gold reaches zero** AND
- You have **no liquidatable assets** (no facilities, ships, or inventory to sell)

If you have assets, you can sell them to stay afloat. Facilities and ships can be sold to other players or to NPCs at a discount.

### Winning

The game ends when:
- **All players have gone bankrupt**, or
- **The era has elapsed** (50 years, or the configured length)

The winner is the player with the **most total assets** at game end:
- Gold on hand
- Value of facilities (evaluated at current market price)
- Value of ships
- Value of inventory

If players exit early, they are considered bankrupt for scoring purposes. The last player standing — or the one with the most assets when the era ends — is declared the winner.

---

## 8. The User Interface

> **Not implemented in the current simulator.** The Python prototype is currently a command-line simulation and balancing model, not a completed interactive map UI or terminal game surface. The interface material below describes a likely future presentation layer rather than current functionality.

> **Current prototype note:** the actual Linux playtest client is currently an ncurses dashboard rather than the full map-driven interface described below. It already shows role-specific panels for assets, stock, markets, and recent events, but it is not yet the complete long-term interface.

### The Map

The main screen is an **ASCII map of the Roman garum trade network**, displayed on your 3270 terminal. Locations are marked with symbols and connected by trade routes. Your current location is highlighted.

```
        ┌──────────────────────────────────────────────┐
        │       ROMAN EMPIRE — GARUM TRADE NETWORK      │
        │                                               │
        │              ALEXANDRIA ●                     │
        │                    │                          │
        │        CARTHAGE ●──┤   ● OSTIA ● (YOU)       │
        │              │    │  ╱   │                   │
        │              │    │ ╱    │                   │
        │         CADIZ ●   ● LUGDUNUM ● LONDINIUM     │
        │              ╲   │ ╱  ╱      │               │
        │               ╲  │╱  ╱       │               │
        │        CARTAGENA ●           │               │
        │              │                │               │
        └──────────────────────────────────────────────┘
```

### Location Details

Select any location by typing its code (CART, CADIZ, OSTIA, etc.). You will see:

- **Market prices** for garum, fish, salt, amphorae
- **Supply and demand** levels
- **Labour costs** at this location
- **Available resources** (what NPCs are selling)
- **Your assets** at this location (inventory, facilities, ships)
- **Active contracts** involving this location

> **Current ncurses controls:** the current playtest UI already exposes early action scaffolding such as `s` (sell), `b` (buy), `i` (invest), `p` (pause/resume), `n` (next tick), `q` (quit), and `ESC` (close dialog). These are still first-pass controls and not yet the full command system described below.

### Commands

From any screen, you can enter commands:

| Command | Description |
|---|---|
| `BUY resource amount location` | Buy resource from NPC or player |
| `SELL resource amount location` | Sell resource to NPC or player |
| `PRODUCE resource amount` | Start production at your facility |
| `SHIP shipid from to cargo` | Dispatch a ship with cargo |
| `CONTRACT sell/buy resource qty location date price` | Strike a future contract |
| `STATUS` | View your overall status |
| `INVENTORY` | View your inventory at all locations |
| `MAP` | Return to the main map |
| `HELP` | Show available commands |

---

## 9. Random Events

> **Not yet implemented.** Storms, war, piracy, decrees, and similar systemic random events are still part of the broader design vision rather than active simulator logic.

The world is not static. Each tick, there is a chance of random events:

| Event | Effect |
|---|---|
| **Storm** | Ships at sea are delayed or lost. Prices spike at destination. |
| **War** | Trade routes disrupted. Military contracts appear. |
| **Harvest failure** | Grain prices rise. Labor costs increase. |
| **Piracy** | Ships on dangerous routes may be robbed. |
| **Plague** | Labor shortages. Reduced production at affected locations. |
| **Golden harvest** | Abundant fish/salt. Raw material prices drop. |
| **Imperial decree** | Government intervention — price controls or subsidies. |

Events affect the entire world, not just individual players.

---

## 10. The Economic Cycle

> **Partially conceptual.** The simulator does model growth, expansion, risk, spoilage, and differentiated value channels, but it does not yet implement the full long-era macroeconomic arc described below.

### The Rise and Fall of Garum

Over the 50-year span, the garum economy follows a natural arc:

1. **50–30 BCE (Republic's end)**: Garum demand is high. Production expands. Prices are strong. New markets open as Rome conquers new territories.
2. **30 BCE–1 CE (Empire begins)**: Peak prosperity. Trade routes are secure. Demand is at its height. Premium garum commands top prices.
3. **1–25 CE (Early Empire)**: Market saturates. Competition increases. Margins shrink. Some producers struggle.
4. **25–50 CE (Transition)**: Substitute products begin to appear. Demand slowly declines. Garum production becomes less profitable.

The economic model reflects this arc. Prices, demand, and event frequency shift as the era progresses. By the end of the game, only the most efficient and diversified players survive.

---

## 11. Quick Start

1. **Join a game round** — the system operator or first player sets the parameters (era length, tick interval).
2. **Choose your occupation** — Fisherman, Saltpan Owner, Garum Producer, or Merchant.
3. **Receive your starting location** — assigned based on your occupation.
4. **Begin trading** — acquire resources, produce garum, ship to market, sell for gold.
5. **Expand and compete** — invest in facilities, ships, and contracts. Strike deals at public trading venues. Build your reputation.
6. **Survive the era** — be the last player standing with the most assets when the 50 years are up.

---

## 12. Technical Appendix

*This section is intended for developers and system operators. It documents the software architecture, design decisions, and implementation details of the SimGarum game engine. It will be expanded as development progresses.*

### 12.1 Platform

SimGarum runs on **OS/390 V2R10** (ADCD distribution) via the **Hercules** mainframe emulator. The game leverages native OS/390 subsystems:

- **TSO/E** — interactive user sessions via 3270 terminals
- **JES2** — batch job scheduling for game ticks and periodic operations
- **VSAM KSDS** — keyed sequential data sets for persistent game state
- **REXX** — game engine logic, user interaction, and orchestration
- **COBOL** — economic calculation modules (price formulas, production yields, shipping times)
- **ISPF Dialog Manager** — 3270-based user interface panels

### 12.2 Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    OS/390 (Hercules)                      │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │   TSO/E  │  │   JES2   │  │     VSAM Datasets    │  │
│  │ (3270    │◄─┤ (Tick    │  │                      │  │
│  │ sessions)│  │  Engine) │  │  ┌────────────────┐  │  │
│  │          │  │          │  │  │ Player Records │  │  │
│  │          │  │          │  │  │ Market Records │  │  │
│  │          │  │          │  │  │ Inventory      │  │  │
│  │          │  │          │  │  │ Ship Records   │  │  │
│  │          │  │          │  │  │ Contracts      │  │  │
│  │          │  │          │  │  │ Game State     │  │  │
│  │          │  │          │  │  └────────────────┘  │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Game Engine (REXX + COBOL)               │  │
│  │                                                  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────┐ │  │
│  │  │ Tick       │  │ Market     │  │ NPC       │ │  │
│  │  │ Manager    │→ │ Simulator  │→ │ Engine    │ │  │
│  │  └────────────┘  └────────────┘  └───────────┘ │  │
│  │       │              │              │           │  │
│  │  ┌────┴──────────────┴──────────────┴──────┐   │  │
│  │  │         COBOL Calculation Modules       │   │  │
│  │  │  (Price formulas, Production yields,    │   │  │
│  │  │   Shipping times, Quality calculations) │   │  │
│  │  └─────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 12.3 Design Decisions

#### Why REXX for the Game Engine?

REXX is the natural choice for OS/390 game logic:
- Runs interactively in TSO — players and the engine share the same environment
- Excellent string handling for 3270 panel interaction
- Can call COBOL load modules for calculations
- No compilation step — rapid iteration and testing
- Native access to VSAM datasets via EXECIO and BLDLIB

#### Why COBOL for Calculations?

COBOL handles economic arithmetic precisely:
- Fixed-point arithmetic avoids floating-point rounding errors
- Native support for large numbers (essential for gold totals)
- Can be compiled as callable load modules from REXX
- Familiar to mainframe developers

#### Why VSAM KSDS?

VSAM Keyed Sequential Data Sets provide:
- Fast record lookup by key (player ID, location+resource, ship ID)
- Native OS/390 support — no external dependencies
- Concurrent access with proper locking
- Standard on all MVS/OS/390 systems

#### Why Public Trading Venues (Not Player-Owned Warehouses)?

Player-owned warehouses would create monopolies — a single player controlling all storage at a key location could manipulate prices for everyone. Public trading venues ensure:
- Fair price discovery through aggregate supply and demand
- No single player can control market access
- The Merchant occupation fills the intermediary role without monopolizing infrastructure

#### Time Model: Hybrid Ticks

The hybrid model (background ticks + interactive player sessions) fits the mainframe paradigm:
- Batch jobs (JES2) handle periodic world updates
- Interactive TSO sessions handle player input
- Players log in once daily, see changes, make decisions, log out
- The game world evolves continuously in the background

### 12.4 Data Model

#### Player Record (VSAM KSDS)

| Field | Type | Description |
|---|---|---|
| PLAYER_ID | CHAR(8) | Unique player identifier |
| PLAYER_NAME | CHAR(16) | Player display name |
| OCCUPATION | CHAR(20) | Fisherman, Saltpan Owner, etc. |
| GOLD | PACKED(11) | Current gold balance |
| REPUTATION | NUM(1) | Reputation level (1-10) |
| STATUS | CHAR(10) | ACTIVE, BANKRUPT, EXITED |
| LOCATION | CHAR(8) | Current location code |
| START_TICK | NUM(6) | Game tick when player joined |

#### Market Record (VSAM KSDS)

| Field | Type | Description |
|---|---|---|
| LOCATION | CHAR(8) | Location code |
| RESOURCE | CHAR(10) | Resource type (GARUM, FISH, SALT, etc.) |
| SUPPLY | NUM(8) | Current supply at this location |
| DEMAND | NUM(8) | Current demand level |
| PRICE | PACKED(9) | Current market price |
| LAST_ADJUSTED | NUM(6) | Tick when price was last updated |

#### Inventory Record (VSAM KSDS)

| Field | Type | Description |
|---|---|---|
| PLAYER_ID | CHAR(8) | Owner player ID |
| LOCATION | CHAR(8) | Location code |
| RESOURCE | CHAR(10) | Resource type |
| QUANTITY | NUM(8) | Amount held |

#### Ship Record (VSAM KSDS)

| Field | Type | Description |
|---|---|---|
| SHIP_ID | CHAR(8) | Unique ship identifier |
| OWNER | CHAR(8) | Owner player ID |
| STATUS | CHAR(10) | IDLE, TRANSIT, DOCKED, UNDER_CONSTRUCTION |
| CAPACITY | NUM(4) | Amphorae capacity |
| FROM_LOC | CHAR(8) | Departure location |
| TO_LOC | CHAR(8) | Destination location |
| DEPARTURE_TICK | NUM(6) | Tick when ship departed |
| ARRIVAL_TICK | NUM(6) | Tick when ship will arrive |
| CARGO | CHAR(20) | Cargo type |
| CARGO_QTY | NUM(6) | Cargo quantity |

#### Contract Record (VSAM KSDS)

| Field | Type | Description |
|---|---|---|
| CONTRACT_ID | CHAR(8) | Unique contract identifier |
| SELLER | CHAR(8) | Seller player ID |
| BUYER | CHAR(8) | Buyer player ID |
| RESOURCE | CHAR(10) | Resource type |
| QUANTITY | NUM(6) | Amount to deliver |
| LOCATION | CHAR(8) | Delivery location |
| DELIVERY_TICK | NUM(6) | Tick by which delivery is due |
| PRICE_PER_UNIT | PACKED(7) | Price per unit |
| STATUS | CHAR(10) | ACTIVE, FULFILLED, FAILED, TRADED |
| DEPOSIT | PACKED(9) | Deposit paid |

#### Game State (Sequential File)

| Field | Type | Description |
|---|---|---|
| CURRENT_TICK | NUM(6) | Current game tick |
| GAME_YEAR | NUM(4) | Current game year (BCE negative) |
| ERA_LENGTH | NUM(4) | Total era length in years |
| TICK_INTERVAL | NUM(4) | Real-time interval per tick (minutes) |
| GAME_STATUS | CHAR(10) | RUNNING, PAUSED, ENDED |
| NEXT_EVENT_TICK | NUM(6) | Tick of next scheduled event |

### 12.5 Tick Processing Flow

1. **JES2 triggers** the tick job at the configured interval.
2. **REXX Tick Manager** reads the Game State file.
3. **Market Simulator** updates supply/demand and recalculates prices for all locations (calls COBOL modules).
4. **NPC Engine** processes NPC buy/sell behavior and adjusts NPC inventory.
5. **Ship Tracker** updates ship positions — arrivals, departures, delays from events.
6. **Event Processor** checks for random events and applies their effects.
7. **Contract Fulfillment** checks due contracts — processes fulfillments and penalties.
8. **Game State** is written back to the sequential file.
9. **JES2 job ends** until the next interval.

### 12.6 Pricing Formulas

#### 12.6.1 Base Price

Each resource at each location has a **base price** set at game start:

| Resource | Base Price (per unit) |
|---|---|  
| Fish | 5 |
| Salt | 3 |
| Garum (Standard) | 20 |
| Garum (Premium) | 30 |
| Garum (Premium+) | 40 |
| Garum (Poor) | 16 |
| Amphora (empty) | 8 |
| Amphora (full) | 28 |

Premium and Poor prices are multipliers of the Standard base price (×1.5 and ×0.8 respectively). Amphora (full) = base garum price + amphora cost.

#### 12.6.2 Supply-Demand Adjustment

After each tick, the market simulator recalculates prices using the following formula:

```
price = base_price × (1 + (demand - supply) / total_supply) × era_modifier × location_modifier
```

Where:
- **total_supply** = supply + max(demand × 0.1, 10) — prevents division by zero and ensures prices don't swing wildly on thin markets
- **era_modifier** reflects the economic arc (see §12.6.4)
- **location_modifier** accounts for local conditions (see §12.6.3)

The adjustment is **capped at ±40% per tick** to prevent runaway price swings. A price that would move more than 40% is clamped to the 40% limit.

#### 12.6.3 Location Modifiers

| Location | Modifier | Reason |
|---|---|---|  
| Cartagena | 0.9 | Production hub, oversupply of raw materials |
| Cádiz | 1.0 | Neutral — premium production center |
| Ostia | 1.15 | Consumption hub, high demand |
| Lugdunum | 1.05 | Central hub, moderate demand |
| Londinium | 1.20 | Military demand, remote from production |
| Alexandria | 1.10 | Eastern trade hub |
| Carthage | 1.05 | Regional hub |

These modifiers are applied to **all** resource prices at each location.

#### 12.6.4 Era Modifiers

The garum economy follows a natural arc over the game era:

| Era Phase | Years | Era Modifier | Notes |
|---|---|---|---|  
| Republic's End | 50–30 BCE | 1.10 | High demand, expanding markets |
| Empire Peak | 30 BCE–1 CE | 1.20 | Peak prosperity, premium prices |
| Saturation | 1–25 CE | 1.00 | Normal market conditions |
| Transition | 25–50 CE | 0.85 | Declining demand, substitute products |

The era modifier is a **smooth linear interpolation** between phase boundaries. At the midpoint of each phase, use that phase's modifier. At phase boundaries, interpolate linearly between adjacent modifiers.

#### 12.6.5 Quality Adjustment

When garum of a specific quality is sold, the price is adjusted by the quality multiplier:

```
final_price = adjusted_price × quality_multiplier
```

Quality multipliers:
- Poor: ×0.8
- Standard: ×1.0
- Premium: ×1.5
- Premium+: ×2.0

### 12.7 NPC Behavior Rules

#### 12.7.1 General Principles

NPCs simulate market participants that fill roles no player occupies. They operate on simple rule-based logic:

1. **NPCs always buy** when supply exceeds demand (they accumulate inventory).
2. **NPCs always sell** when demand exceeds supply (they deplete inventory).
3. **NPCs have inventory limits** — they won't buy if their warehouse is full, won't sell if they're empty.
4. **NPCs trade at market price ±10%** — they're willing to pay up to 10% above market or sell up to 10% below.
5. **NPCs prefer quality** — if multiple quality tiers are available, they buy/sell the tier matching their profile.

#### 12.7.2 NPC Profiles

| NPC Type | Location | Buys | Sells | Inventory Cap |
|---|---|---|---|---|  
| Fishery (NPC) | CART, ALEX | Fish (catch) | Fish, Salt | 500 units |
| Saltpan (NPC) | CART, CADIZ | Salt (harvest) | Salt | 300 units |
| Producer (NPC) | CART, CADIZ | Fish, Salt | Garum | 200 units |
| Merchant (NPC) | OSTIA, LUGD, LONDIN | Garum, Fish, Salt | Garum | 400 units |
| Merchant (NPC) | ALEX, CARTH | Garum, Grain | Garum, Spices | 300 units |
| Military Buyer | LONDIN, LUGD | Garum (Premium) | — | 100 units |

#### 12.7.3 NPC Transaction Logic

Each tick, for each NPC:

1. Check current market price for each resource they trade.
2. If **supply > demand** and NPC has room: offer to buy at `market_price × 0.90`. Quantity = min(capacity - inventory, demand × 0.05).
3. If **demand > supply** and NPC has inventory: offer to sell at `market_price × 1.10`. Quantity = min(inventory, demand × 0.05).
4. If **supply ≈ demand** (within ±10%): NPC holds, no action.
5. NPC inventory adjusts slowly — they don't flood or drain the market in a single tick.

#### 12.7.4 Military Buyer Behavior

Military buyers at Londinium and Lugdunum have special rules:
- They only buy **Premium or Premium+ garum**.
- They buy in **bulk** (minimum 20 units per transaction).
- They have a **reputation requirement** — only interact with players with reputation ≥ 5.
- They pay a **premium of 15%** over market price for reliable suppliers.
- If no qualifying supplier is available, they buy from NPC merchants at market price.

### 12.8 Random Event Tables

#### 12.8.1 Event Probability

Base probability per tick (for a 50-year game):

| Event | Base Probability | Era Scaling |
|---|---|---|  
| Storm | 3% per tick | Increases in late era (war disrupts naval trade) |
| War | 2% per tick | Peaks during Republic's end, drops in Empire Peak |
| Harvest failure | 1.5% per tick | Higher in late era (infrastructure decay) |
| Piracy | 2% per tick | Increases in late era (navy weakens) |
| Plague | 0.5% per tick | Rare, but can cascade |
| Golden harvest | 3% per tick | Higher in early era (prosperity) |
| Imperial decree | 1% per tick | Only during Empire era (30 BCE onward) |

**Era scaling:** Each event's probability is multiplied by an era factor:

| Era Phase | Storm | War | Harvest | Piracy | Plague | Golden | Decree |
|---|---|---|---|---|---|---|---|  
| Republic's End | ×0.8 | ×2.0 | ×0.8 | ×0.6 | ×0.5 | ×1.5 | ×0 |
| Empire Peak | ×0.6 | ×0.3 | ×0.5 | ×0.4 | ×0.3 | ×1.2 | ×1.5 |
| Saturation | ×1.0 | ×0.8 | ×1.0 | ×1.0 | ×1.0 | ×1.0 | ×1.0 |
| Transition | ×1.3 | ×1.5 | ×1.5 | ×1.8 | ×1.5 | ×0.5 | ×1.5 |

#### 12.8.2 Event Effects

**Storm:**
- 1–3 ships at sea are delayed by 2–4 ticks.
- If a ship was carrying garum to a high-demand location, supply drops there and prices spike (+20% for 2 ticks).
- Ships lost (sunk): 5% chance per delayed ship. Lost ships are removed permanently.

**War:**
- 1–2 trade routes are disrupted for 5–10 ticks (ships cannot use them).
- Military contracts appear at Londinium and/or Lugdunum (see §12.9).
- Labor costs increase by 10% at affected locations.

**Harvest failure:**
- Fish and salt prices increase by 15% at production locations for 3 ticks.
- Labor costs increase by 5% empire-wide for 3 ticks.
- Production yields decrease by 10% for 2 ticks.

**Piracy:**
- Ships on long routes (Cartagena→Alexandria, Carthage→Alexandria) are at risk.
- 10% chance per ship on a dangerous route per tick.
- If pirated: cargo is lost (50% chance) or ransomed (50% chance, costs 30% of cargo value to recover).

**Plague:**
- One location is affected (chosen randomly).
- Labor costs at that location increase by 25% for 5 ticks.
- Production at that location is reduced by 20% for 5 ticks.
- If the affected location is a major production center, raw material prices rise empire-wide.

**Golden harvest:**
- Fish and salt prices decrease by 15% at production locations for 3 ticks.
- Production yields increase by 10% for 2 ticks.
- NPC fishermen and saltpan owners produce double their normal output.

**Imperial decree:**
- Only possible during Empire era (30 BCE onward).
- Random effect from:
  - **Price controls:** Max price increase of 20% at any location for 5 ticks.
  - **Subsidies:** Production costs reduced by 10% empire-wide for 5 ticks.
  - **Trade monopoly:** One location's market is temporarily closed (no player trading) for 3 ticks.
  - **Tax reform:** Transaction taxes increase by 5% (applied to all sales) for 10 ticks.

#### 12.8.3 Event Processing

Events are processed in this order each tick:
1. Check for event triggers (roll against probability table).
2. Apply all triggered events sequentially.
3. Record events in the event log (VSAM sequential file).
4. Events that persist (delays, price spikes, etc.) are tracked in a separate VSAM dataset and expire after their duration.

### 12.9 Military Contracts

#### 12.9.1 Contract Generation

Military contracts are generated by the event system (see §12.8) or appear at game start at Londinium and Lugdunum.

A military contract specifies:
- **Resource:** Garum (Premium or Premium+ only)
- **Quantity:** 20–100 units (bulk orders)
- **Delivery date:** 3–8 ticks from contract date
- **Price:** Market price × 1.15 (15% premium)
- **Penalty for non-fulfillment:** 20% of contract value + 2 reputation points
- **Bonus for early fulfillment:** Additional 5% if delivered 2+ ticks early

#### 12.9.2 Contract Availability

Military contracts are only available to players with:
- **Reputation ≥ 5** (Renowned or above)
- **Premium or Premium+ garum** available for delivery
- **Ships or inventory** at the contract location

Contracts are **limited** — only 1–2 per location per tick, and they expire after 3 ticks if not filled.

### 12.10 Ship Construction

#### 12.10.1 Base Values

| Parameter | Value |
|---|---|  
| Base construction time | 5 ticks |
| Base cost | 200 gold |
| Capacity per ship | 50 amphorae |
| Shipyard upgrade effect | -1 tick per upgrade (minimum 1 tick) |

#### 12.10.2 Construction Process

1. Player invests gold at a location with a shipyard.
2. Ship is marked as `UNDER_CONSTRUCTION` in the ship records.
3. After the construction period, the ship becomes `IDLE` at the construction location.
4. The ship can then be dispatched or sold.

#### 12.10.3 Ship Sales

Ships can be sold to:
- **Other players** at negotiated price (agreed in the trading venue).
- **NPCs** at 60% of original construction cost (depreciation).

### 12.11 Contract Secondary Market

#### 12.11.1 Trading Mechanics

Contracts can be transferred between players before their delivery date:

1. The current holder lists the contract at the trading venue.
2. Another player can **buy** the contract at a negotiated price.
3. The buyer assumes all obligations (delivery, penalties, bonuses).
4. The original seller receives the sale price immediately.

#### 12.11.2 Price Discovery

Secondary market prices are determined by:
- **Remaining time:** Contracts closer to delivery are worth more (less risk).
- **Market price at delivery location:** If garum prices have risen, contracts to sell are more valuable.
- **Buyer's reputation:** Buyers with low reputation may need to offer a discount (sellers perceive higher risk).

#### 12.11.3 Transfer Limitations

- A contract can only be traded **once per tick**.
- The buyer must have sufficient inventory or ships at the delivery location.
- Military contracts **cannot** be traded (they are tied to the player's reputation).

### 12.12 Facility Valuation (Bankruptcy)

#### 12.12.1 Asset Valuation

When calculating total assets for bankruptcy or game-end scoring:

| Asset Type | Valuation Formula |
|---|---|  
| Gold | Face value |
| Facilities | Base cost × (1 + quality_bonus × 0.3) |
| Ships | Construction cost × (1 - depreciation × 0.02 per tick) |
| Inventory | Market price at location (current tick) |

Where:
- **quality_bonus** = 0 for Poor, 1 for Standard, 2 for Premium, 3 for Premium+
- **depreciation** = number of ticks since construction/purchase

#### 12.12.2 Forced Liquidation

During bankruptcy proceedings:
- Facilities sell at **50% of valuation** (fire sale).
- Ships sell at **40% of valuation** (urgent sale).
- Inventory sells at **70% of market price** (bulk discount).

#### 12.12.3 Bankruptcy Check

Bankruptcy is checked at the end of each tick:
1. If gold ≤ 0, check liquidatable assets.
2. If assets can cover the deficit, force sell assets at liquidation prices.
3. If assets are still insufficient after liquidation, player goes bankrupt.
4. Bankrupt players are removed from the game and their assets are distributed to creditors (proportional to debt owed).

### 12.13 Production Yield Calculations

#### 12.13.1 Base Yield

Standard ratio: 10 fish + 2 salt → 5 garum (50% yield by input weight).

#### 12.13.2 Quality Modifiers

| Quality | Yield Modifier | Fermentation Time |
|---|---|---|  
| Poor | ×0.8 | 2 ticks |
| Standard | ×1.0 | 3 ticks |
| Premium | ×1.2 | 3 ticks (Cádiz) / 6 ticks (other) |
| Premium+ | ×1.4 | 4 ticks (Cádiz) / 6 ticks (other) |

#### 12.13.3 Location Modifiers

| Location | Yield Modifier |
|---|---|  
| Cádiz | ×1.1 (best conditions for fermentation) |
| Cartagena | ×1.0 |
| Other locations | ×0.9 |

#### 12.13.4 Event Modifiers

- **Golden harvest:** +10% yield for 2 ticks.
- **Harvest failure:** -10% yield for 2 ticks.
- **Plague:** -20% yield at affected location for 5 ticks.

#### 12.13.5 Final Yield Formula

```
yield = base_yield × quality_modifier × location_modifier × event_modifier
```

Example: Premium garum at Cádiz during golden harvest:
```
yield = 5 × 1.2 × 1.1 × 1.1 = 7.26 → 7 garum (rounded down)
```

### 12.6 Installation and Deployment

*This section will be expanded as development progresses. It will cover:*

- Hercules configuration for the ADCD OS/390 image
- VSAM dataset creation and initialization JCL
- COBOL compilation and load library setup
- REXX script deployment and execution
- JES2 job stream configuration
- 3270 terminal access (x3270 / a3270 on Linux)
- Game round lifecycle (start, run, end, reset)

---

*Senatus Populusque Romanus. SimGarum — where every amphora tells a story.*
