from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from statistics import mean
from typing import Dict, List, Optional


FISH_PRICE = 1.0
SALT_PRICE = 0.5
STANDARD_GARUM_PRICE = 10.0
PREMIUM_GARUM_PRICE = 22.0
MERCHANT_MARKUP = 0.20
WHOLESALE_DISCOUNT = 0.82

STANDARD_RECIPE_FISH = 5
STANDARD_RECIPE_SALT = 2
PREMIUM_RECIPE_FISH = 5
PREMIUM_RECIPE_SALT = 2

STANDARD_PRODUCTION_TICKS = 3
PREMIUM_PRODUCTION_TICKS = 6


@dataclass
class Inventory:
    gold: float = 0.0
    fish: int = 0
    salt: int = 0
    empty_amphorae: int = 0
    standard_garum: int = 0
    premium_garum: int = 0
    boats: int = 0
    pans: int = 0


@dataclass
class Player:
    name: str
    role: str
    location: str
    inventory: Inventory
    production_mode: str = "standard"
    production_progress: int = 0
    merchant_stock_standard: int = 0
    merchant_stock_premium: int = 0


@dataclass
class GarumMarket:
    location: str
    preferred_quality: str
    base_standard_price: float = STANDARD_GARUM_PRICE
    base_premium_price: float = PREMIUM_GARUM_PRICE
    standard_demand: float = 4.0
    premium_demand: float = 2.0
    standard_supply_sold_last_tick: int = 0
    premium_supply_sold_last_tick: int = 0

    def standard_price(self) -> float:
        quality_bias = 0.95 if self.preferred_quality == "premium" else 1.05
        demand_pressure = 1.0 + 0.08 * (self.standard_demand - self.standard_supply_sold_last_tick)
        return max(4.0, round(self.base_standard_price * quality_bias * demand_pressure, 2))

    def premium_price(self) -> float:
        quality_bias = 1.15 if self.preferred_quality == "premium" else 0.95
        demand_pressure = 1.0 + 0.08 * (self.premium_demand - self.premium_supply_sold_last_tick)
        return max(8.0, round(self.base_premium_price * quality_bias * demand_pressure, 2))

    def reset_tick_sales(self) -> None:
        self.standard_supply_sold_last_tick = 0
        self.premium_supply_sold_last_tick = 0


class WorldMarket:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def buy_fish(self, buyer: Player, quantity: int) -> int:
        affordable = min(quantity, int(buyer.inventory.gold // FISH_PRICE))
        cost = affordable * FISH_PRICE
        buyer.inventory.gold -= cost
        buyer.inventory.fish += affordable
        return affordable

    def buy_salt(self, buyer: Player, quantity: int) -> int:
        affordable = min(quantity, int(buyer.inventory.gold // SALT_PRICE))
        cost = affordable * SALT_PRICE
        buyer.inventory.gold -= cost
        buyer.inventory.salt += affordable
        return affordable

    def provide_amphorae(self, buyer: Player, quantity: int) -> None:
        buyer.inventory.empty_amphorae += quantity

    def sell_fish(self, seller: Player, quantity: int) -> float:
        demand = max(0, int(round(self.rng.gauss(4.0, 1.5))))
        quantity = min(quantity, seller.inventory.fish, demand)
        revenue = quantity * FISH_PRICE
        seller.inventory.fish -= quantity
        seller.inventory.gold += revenue
        return revenue

    def sell_salt(self, seller: Player, quantity: int) -> float:
        demand = max(0, int(round(self.rng.gauss(8.0, 2.0))))
        quantity = min(quantity, seller.inventory.salt, demand)
        revenue = quantity * SALT_PRICE
        seller.inventory.salt -= quantity
        seller.inventory.gold += revenue
        return revenue


class Simulation:
    def __init__(self, seed: Optional[int] = None, producer_mode: str = "weighted") -> None:
        self.rng = random.Random(seed)
        self.producer_mode = producer_mode
        self.world_market = WorldMarket(self.rng)
        self.players: List[Player] = [
            Player(
                name="Gaius",
                role="fisherman",
                location="Baelo",
                inventory=Inventory(boats=1),
            ),
            Player(
                name="Livia",
                role="salt-maker",
                location="Baelo",
                inventory=Inventory(pans=1),
            ),
            Player(
                name="Nereus",
                role="producer",
                location="Baelo",
                inventory=Inventory(fish=5, salt=2, empty_amphorae=1),
                production_mode="standard",
            ),
            Player(
                name="Cassia",
                role="merchant",
                location="Rome",
                inventory=Inventory(gold=20.0),
            ),
        ]
        self.markets: Dict[str, GarumMarket] = {
            "Baelo": GarumMarket(location="Baelo", preferred_quality="standard", standard_demand=5.0, premium_demand=1.0),
            "Rome": GarumMarket(location="Rome", preferred_quality="premium", standard_demand=4.0, premium_demand=6.0),
            "Alexandria": GarumMarket(location="Alexandria", preferred_quality="standard", standard_demand=6.0, premium_demand=3.0),
        }
        self.total_standard_completed = 0
        self.total_premium_completed = 0
        self.total_standard_sold = 0
        self.total_premium_sold = 0

    def run(self, ticks: int = 12, verbose: bool = True) -> Dict[str, object]:
        for tick in range(1, ticks + 1):
            if verbose:
                print(f"\n=== Tick {tick} ===")
            for market in self.markets.values():
                market.reset_tick_sales()

            self.produce_resources(verbose)
            self.producers_restock_inputs(verbose)
            self.advance_garum_production(verbose)
            self.merchants_buy_garum(verbose)
            self.sell_surplus_raw_materials(verbose)
            self.merchants_sell_garum(verbose)

            if verbose:
                self.print_market_snapshot()
                self.print_player_snapshot()

        if verbose:
            print("\n=== Final State ===")
            self.print_player_snapshot()

        return self.snapshot(ticks)

    def produce_resources(self, verbose: bool) -> None:
        for player in self.players:
            if player.role == "fisherman":
                produced = 5 * player.inventory.boats
                player.inventory.fish += produced
                if verbose:
                    print(f"{player.name} catches {produced} fish")
            elif player.role == "salt-maker":
                produced = 10 * player.inventory.pans
                player.inventory.salt += produced
                if verbose:
                    print(f"{player.name} harvests {produced} salt")

    def producers_restock_inputs(self, verbose: bool) -> None:
        for player in self.players:
            if player.role != "producer":
                continue
            if player.inventory.empty_amphorae < 1:
                self.world_market.provide_amphorae(player, 1)
            if player.inventory.fish < 5:
                needed = 5 - player.inventory.fish
                bought = self.world_market.buy_fish(player, needed)
                if verbose and bought > 0:
                    print(f"{player.name} buys {bought} fish for {bought * FISH_PRICE:.2f} gold")
            if player.inventory.salt < 2:
                needed = 2 - player.inventory.salt
                bought = self.world_market.buy_salt(player, needed)
                if verbose and bought > 0:
                    print(f"{player.name} buys {bought} salt for {bought * SALT_PRICE:.2f} gold")

    def advance_garum_production(self, verbose: bool) -> None:
        for player in self.players:
            if player.role != "producer":
                continue

            if player.production_progress == 0:
                player.production_mode = self.choose_production_mode(player)
                needed_fish, needed_salt, duration = self.recipe_for_mode(player.production_mode)
                if player.inventory.fish >= needed_fish and player.inventory.salt >= needed_salt and player.inventory.empty_amphorae >= 1:
                    player.inventory.fish -= needed_fish
                    player.inventory.salt -= needed_salt
                    player.inventory.empty_amphorae -= 1
                    player.production_progress = 1
                    if verbose:
                        print(f"{player.name} starts {player.production_mode} garum production")
                continue

            _, _, duration = self.recipe_for_mode(player.production_mode)
            player.production_progress += 1
            if player.production_progress >= duration:
                if player.production_mode == "standard":
                    player.inventory.standard_garum += 1
                    self.total_standard_completed += 1
                else:
                    player.inventory.premium_garum += 1
                    self.total_premium_completed += 1
                player.production_progress = 0
                if verbose:
                    print(f"{player.name} completes 1 amphora of {player.production_mode} garum")

    def choose_production_mode(self, player: Player) -> str:
        if self.producer_mode == "standard":
            return "standard"
        if self.producer_mode == "premium":
            return "premium"

        producer_market = self.markets[player.location]
        standard_revenue = producer_market.standard_price() * WHOLESALE_DISCOUNT
        premium_revenue = producer_market.premium_price() * WHOLESALE_DISCOUNT
        standard_input_cost = STANDARD_RECIPE_FISH * FISH_PRICE + STANDARD_RECIPE_SALT * SALT_PRICE
        premium_input_cost = PREMIUM_RECIPE_FISH * FISH_PRICE + PREMIUM_RECIPE_SALT * SALT_PRICE
        standard_profit_per_tick = (standard_revenue - standard_input_cost) / STANDARD_PRODUCTION_TICKS
        premium_profit_per_tick = (premium_revenue - premium_input_cost) / PREMIUM_PRODUCTION_TICKS

        if player.inventory.gold < premium_input_cost and player.inventory.gold >= standard_input_cost:
            return "standard"
        if premium_profit_per_tick > standard_profit_per_tick * 1.20:
            return "premium"
        if standard_profit_per_tick > premium_profit_per_tick * 1.20:
            return "standard"
        return self.rng.choices(["standard", "premium"], weights=[3, 2], k=1)[0]

    def recipe_for_mode(self, mode: str) -> tuple[int, int, int]:
        if mode == "premium":
            return PREMIUM_RECIPE_FISH, PREMIUM_RECIPE_SALT, PREMIUM_PRODUCTION_TICKS
        return STANDARD_RECIPE_FISH, STANDARD_RECIPE_SALT, STANDARD_PRODUCTION_TICKS

    def merchants_buy_garum(self, verbose: bool) -> None:
        merchant = self.get_role_player("merchant")
        producer = self.get_role_player("producer")
        producer_market = self.markets[producer.location]

        if producer.inventory.standard_garum > 0:
            retail_price = producer_market.standard_price()
            wholesale_price = round(retail_price * WHOLESALE_DISCOUNT, 2)
            quantity = producer.inventory.standard_garum
            affordable = min(quantity, int(merchant.inventory.gold // wholesale_price)) if wholesale_price > 0 else quantity
            if affordable > 0:
                total = affordable * wholesale_price
                producer.inventory.standard_garum -= affordable
                producer.inventory.gold += total
                merchant.inventory.gold -= total
                merchant.merchant_stock_standard += affordable
                if verbose:
                    print(f"{merchant.name} buys {affordable} standard garum from {producer.name} for {total:.2f} gold")

        if producer.inventory.premium_garum > 0:
            retail_price = producer_market.premium_price()
            wholesale_price = round(retail_price * WHOLESALE_DISCOUNT, 2)
            quantity = producer.inventory.premium_garum
            affordable = min(quantity, int(merchant.inventory.gold // wholesale_price)) if wholesale_price > 0 else quantity
            if affordable > 0:
                total = affordable * wholesale_price
                producer.inventory.premium_garum -= affordable
                producer.inventory.gold += total
                merchant.inventory.gold -= total
                merchant.merchant_stock_premium += affordable
                if verbose:
                    print(f"{merchant.name} buys {affordable} premium garum from {producer.name} for {total:.2f} gold")

    def merchants_sell_garum(self, verbose: bool) -> None:
        merchant = self.get_role_player("merchant")
        market = self.markets[merchant.location]

        if merchant.merchant_stock_standard > 0:
            random_demand = max(0, int(round(self.rng.gauss(market.standard_demand, 1.0))))
            quantity = min(merchant.merchant_stock_standard, random_demand)
            sale_price = round(market.standard_price() * (1.0 + MERCHANT_MARKUP), 2)
            revenue = quantity * sale_price
            merchant.merchant_stock_standard -= quantity
            merchant.inventory.gold += revenue
            market.standard_supply_sold_last_tick += quantity
            self.total_standard_sold += quantity
            if verbose:
                print(f"{merchant.name} sells {quantity} standard garum in {merchant.location} for {revenue:.2f} gold")

        if merchant.merchant_stock_premium > 0:
            random_demand = max(0, int(round(self.rng.gauss(market.premium_demand, 1.0))))
            quantity = min(merchant.merchant_stock_premium, random_demand)
            sale_price = round(market.premium_price() * (1.0 + MERCHANT_MARKUP), 2)
            revenue = quantity * sale_price
            merchant.merchant_stock_premium -= quantity
            merchant.inventory.gold += revenue
            market.premium_supply_sold_last_tick += quantity
            self.total_premium_sold += quantity
            if verbose:
                print(f"{merchant.name} sells {quantity} premium garum in {merchant.location} for {revenue:.2f} gold")

    def sell_surplus_raw_materials(self, verbose: bool) -> None:
        fisherman = self.get_role_player("fisherman")
        salt_maker = self.get_role_player("salt-maker")

        if fisherman.inventory.fish > 0:
            sold = fisherman.inventory.fish
            revenue = self.world_market.sell_fish(fisherman, sold)
            if verbose:
                print(f"{fisherman.name} sells {sold} fish for {revenue:.2f} gold")

        if salt_maker.inventory.salt > 0:
            sold = salt_maker.inventory.salt
            revenue = self.world_market.sell_salt(salt_maker, sold)
            if verbose:
                print(f"{salt_maker.name} sells {sold} salt for {revenue:.2f} gold")

    def snapshot(self, ticks: int) -> Dict[str, object]:
        role_gold = {player.role: round(player.inventory.gold, 2) for player in self.players}
        merchant = self.get_role_player("merchant")
        producer = self.get_role_player("producer")
        return {
            "ticks": ticks,
            "role_gold": role_gold,
            "merchant_stock_standard": merchant.merchant_stock_standard,
            "merchant_stock_premium": merchant.merchant_stock_premium,
            "producer_standard": producer.inventory.standard_garum,
            "producer_premium": producer.inventory.premium_garum,
            "total_standard_completed": self.total_standard_completed,
            "total_premium_completed": self.total_premium_completed,
            "total_standard_sold": self.total_standard_sold,
            "total_premium_sold": self.total_premium_sold,
        }

    def print_market_snapshot(self) -> None:
        for market in self.markets.values():
            print(
                f"Market {market.location}: standard={market.standard_price():.2f}, premium={market.premium_price():.2f}, "
                f"prefers={market.preferred_quality}"
            )

    def print_player_snapshot(self) -> None:
        for player in self.players:
            inv = player.inventory
            print(
                f"{player.name:7s} {player.role:10s} gold={inv.gold:7.2f} fish={inv.fish:2d} salt={inv.salt:2d} "
                f"empty_amp={inv.empty_amphorae:2d} std={inv.standard_garum:2d} prem={inv.premium_garum:2d} "
                f"boats={inv.boats:2d} pans={inv.pans:2d} prog={player.production_progress}"
            )

    def get_role_player(self, role: str) -> Player:
        for player in self.players:
            if player.role == role:
                return player
        raise ValueError(f"No player with role {role}")


def run_monte_carlo(runs: int, ticks: int, producer_mode: str, seed: Optional[int]) -> None:
    base_seed = 0 if seed is None else seed
    snapshots = []
    for run_index in range(runs):
        sim = Simulation(seed=base_seed + run_index, producer_mode=producer_mode)
        snapshots.append(sim.run(ticks=ticks, verbose=False))

    roles = ["fisherman", "salt-maker", "producer", "merchant"]
    print(f"Monte Carlo summary: runs={runs}, ticks={ticks}, producer_mode={producer_mode}")
    for role in roles:
        avg_gold = mean(snapshot["role_gold"][role] for snapshot in snapshots)
        min_gold = min(snapshot["role_gold"][role] for snapshot in snapshots)
        max_gold = max(snapshot["role_gold"][role] for snapshot in snapshots)
        print(f"- {role:10s} avg_gold={avg_gold:7.2f} min={min_gold:7.2f} max={max_gold:7.2f}")

    avg_std_completed = mean(snapshot["total_standard_completed"] for snapshot in snapshots)
    avg_prem_completed = mean(snapshot["total_premium_completed"] for snapshot in snapshots)
    avg_std_sold = mean(snapshot["total_standard_sold"] for snapshot in snapshots)
    avg_prem_sold = mean(snapshot["total_premium_sold"] for snapshot in snapshots)
    avg_merchant_stock_std = mean(snapshot["merchant_stock_standard"] for snapshot in snapshots)
    avg_merchant_stock_prem = mean(snapshot["merchant_stock_premium"] for snapshot in snapshots)

    print(f"- avg standard completed: {avg_std_completed:.2f}")
    print(f"- avg premium completed:  {avg_prem_completed:.2f}")
    print(f"- avg standard sold:      {avg_std_sold:.2f}")
    print(f"- avg premium sold:       {avg_prem_sold:.2f}")
    print(f"- avg merchant std stock: {avg_merchant_stock_std:.2f}")
    print(f"- avg merchant prem stock:{avg_merchant_stock_prem:.2f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SimGarum economic simulation")
    parser.add_argument("--ticks", type=int, default=12, help="Number of ticks per simulation")
    parser.add_argument("--runs", type=int, default=1, help="Number of Monte Carlo runs")
    parser.add_argument(
        "--producer-mode",
        choices=["standard", "premium", "weighted"],
        default="weighted",
        help="How producers choose garum quality to produce",
    )
    parser.add_argument("--seed", type=int, default=None, help="Base random seed")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.runs > 1:
        run_monte_carlo(runs=args.runs, ticks=args.ticks, producer_mode=args.producer_mode, seed=args.seed)
    else:
        Simulation(seed=args.seed, producer_mode=args.producer_mode).run(ticks=args.ticks, verbose=True)
