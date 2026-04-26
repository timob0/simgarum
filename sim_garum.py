from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


FISH_PRICE = 1.0
SALT_PRICE = 0.5
STANDARD_GARUM_PRICE = 10.0
PREMIUM_GARUM_PRICE = 20.0
MERCHANT_MARKUP = 0.15

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
        premium_bias = 0.95 if self.preferred_quality == "premium" else 1.05
        demand_pressure = 1.0 + 0.08 * (self.standard_demand - self.standard_supply_sold_last_tick)
        return max(4.0, round(self.base_standard_price * premium_bias * demand_pressure, 2))

    def premium_price(self) -> float:
        premium_bias = 1.15 if self.preferred_quality == "premium" else 0.95
        demand_pressure = 1.0 + 0.08 * (self.premium_demand - self.premium_supply_sold_last_tick)
        return max(8.0, round(self.base_premium_price * premium_bias * demand_pressure, 2))

    def reset_tick_sales(self) -> None:
        self.standard_supply_sold_last_tick = 0
        self.premium_supply_sold_last_tick = 0


class WorldMarket:
    def buy_fish(self, buyer: Player, quantity: int) -> float:
        cost = quantity * FISH_PRICE
        if buyer.inventory.gold < cost:
            quantity = int(buyer.inventory.gold // FISH_PRICE)
            cost = quantity * FISH_PRICE
        buyer.inventory.gold -= cost
        buyer.inventory.fish += quantity
        return cost

    def buy_salt(self, buyer: Player, quantity: int) -> float:
        cost = quantity * SALT_PRICE
        if buyer.inventory.gold < cost:
            quantity = int(buyer.inventory.gold // SALT_PRICE)
            cost = quantity * SALT_PRICE
        buyer.inventory.gold -= cost
        buyer.inventory.salt += quantity
        return cost

    def provide_amphorae(self, buyer: Player, quantity: int) -> None:
        buyer.inventory.empty_amphorae += quantity

    def sell_fish(self, seller: Player, quantity: int) -> float:
        quantity = min(quantity, seller.inventory.fish)
        revenue = quantity * FISH_PRICE
        seller.inventory.fish -= quantity
        seller.inventory.gold += revenue
        return revenue

    def sell_salt(self, seller: Player, quantity: int) -> float:
        quantity = min(quantity, seller.inventory.salt)
        revenue = quantity * SALT_PRICE
        seller.inventory.salt -= quantity
        seller.inventory.gold += revenue
        return revenue


class Simulation:
    def __init__(self) -> None:
        self.world_market = WorldMarket()
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

    def run(self, ticks: int = 12) -> None:
        for tick in range(1, ticks + 1):
            print(f"\n=== Tick {tick} ===")
            for market in self.markets.values():
                market.reset_tick_sales()

            self.produce_resources()
            self.producers_restock_inputs()
            self.advance_garum_production()
            self.merchants_buy_garum()
            self.sell_surplus_raw_materials()
            self.merchants_sell_garum()
            self.print_market_snapshot()
            self.print_player_snapshot()

        print("\n=== Final State ===")
        self.print_player_snapshot()

    def produce_resources(self) -> None:
        for player in self.players:
            if player.role == "fisherman":
                produced = 5 * player.inventory.boats
                player.inventory.fish += produced
                print(f"{player.name} catches {produced} fish")
            elif player.role == "salt-maker":
                produced = 10 * player.inventory.pans
                player.inventory.salt += produced
                print(f"{player.name} harvests {produced} salt")

    def producers_restock_inputs(self) -> None:
        for player in self.players:
            if player.role != "producer":
                continue
            if player.inventory.empty_amphorae < 1:
                self.world_market.provide_amphorae(player, 1)
            if player.inventory.fish < 5:
                needed = 5 - player.inventory.fish
                spent = self.world_market.buy_fish(player, needed)
                if needed > 0 and spent > 0:
                    print(f"{player.name} buys {needed} fish for {spent:.2f} gold")
            if player.inventory.salt < 2:
                needed = 2 - player.inventory.salt
                spent = self.world_market.buy_salt(player, needed)
                if needed > 0 and spent > 0:
                    print(f"{player.name} buys {needed} salt for {spent:.2f} gold")

    def advance_garum_production(self) -> None:
        for player in self.players:
            if player.role != "producer":
                continue
            mode = player.production_mode
            if mode == "standard":
                needed_fish = STANDARD_RECIPE_FISH
                needed_salt = STANDARD_RECIPE_SALT
                duration = STANDARD_PRODUCTION_TICKS
            else:
                needed_fish = PREMIUM_RECIPE_FISH
                needed_salt = PREMIUM_RECIPE_SALT
                duration = PREMIUM_PRODUCTION_TICKS

            if player.production_progress == 0:
                if player.inventory.fish >= needed_fish and player.inventory.salt >= needed_salt and player.inventory.empty_amphorae >= 1:
                    player.inventory.fish -= needed_fish
                    player.inventory.salt -= needed_salt
                    player.inventory.empty_amphorae -= 1
                    player.production_progress = 1
                    print(f"{player.name} starts {mode} garum production")
                continue

            player.production_progress += 1
            if player.production_progress >= duration:
                if mode == "standard":
                    player.inventory.standard_garum += 1
                else:
                    player.inventory.premium_garum += 1
                player.production_progress = 0
                print(f"{player.name} completes 1 amphora of {mode} garum")

    def merchants_buy_garum(self) -> None:
        merchant = self.get_role_player("merchant")
        producer = self.get_role_player("producer")
        baelo_market = self.markets[producer.location]

        if producer.inventory.standard_garum > 0:
            price = baelo_market.standard_price()
            quantity = producer.inventory.standard_garum
            total = quantity * price
            if merchant.inventory.gold >= total:
                producer.inventory.standard_garum -= quantity
                producer.inventory.gold += total
                merchant.inventory.gold -= total
                merchant.merchant_stock_standard += quantity
                print(f"{merchant.name} buys {quantity} standard garum from {producer.name} for {total:.2f} gold")

        if producer.inventory.premium_garum > 0:
            price = baelo_market.premium_price()
            quantity = producer.inventory.premium_garum
            total = quantity * price
            if merchant.inventory.gold >= total:
                producer.inventory.premium_garum -= quantity
                producer.inventory.gold += total
                merchant.inventory.gold -= total
                merchant.merchant_stock_premium += quantity
                print(f"{merchant.name} buys {quantity} premium garum from {producer.name} for {total:.2f} gold")

    def merchants_sell_garum(self) -> None:
        merchant = self.get_role_player("merchant")
        market = self.markets[merchant.location]

        if merchant.merchant_stock_standard > 0:
            quantity = min(merchant.merchant_stock_standard, int(round(market.standard_demand)))
            sale_price = round(market.standard_price() * (1.0 + MERCHANT_MARKUP), 2)
            revenue = quantity * sale_price
            merchant.merchant_stock_standard -= quantity
            merchant.inventory.gold += revenue
            market.standard_supply_sold_last_tick += quantity
            print(f"{merchant.name} sells {quantity} standard garum in {merchant.location} for {revenue:.2f} gold")

        if merchant.merchant_stock_premium > 0:
            quantity = min(merchant.merchant_stock_premium, int(round(market.premium_demand)))
            sale_price = round(market.premium_price() * (1.0 + MERCHANT_MARKUP), 2)
            revenue = quantity * sale_price
            merchant.merchant_stock_premium -= quantity
            merchant.inventory.gold += revenue
            market.premium_supply_sold_last_tick += quantity
            print(f"{merchant.name} sells {quantity} premium garum in {merchant.location} for {revenue:.2f} gold")

    def sell_surplus_raw_materials(self) -> None:
        fisherman = self.get_role_player("fisherman")
        salt_maker = self.get_role_player("salt-maker")

        if fisherman.inventory.fish > 0:
            sold = fisherman.inventory.fish
            revenue = self.world_market.sell_fish(fisherman, sold)
            print(f"{fisherman.name} sells {sold} fish for {revenue:.2f} gold")

        if salt_maker.inventory.salt > 0:
            sold = salt_maker.inventory.salt
            revenue = self.world_market.sell_salt(salt_maker, sold)
            print(f"{salt_maker.name} sells {sold} salt for {revenue:.2f} gold")

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
                f"{player.name:7s} {player.role:10s} gold={inv.gold:6.2f} fish={inv.fish:2d} salt={inv.salt:2d} "
                f"empty_amp={inv.empty_amphorae:2d} std={inv.standard_garum:2d} prem={inv.premium_garum:2d} "
                f"boats={inv.boats:2d} pans={inv.pans:2d} prog={player.production_progress}"
            )

    def get_role_player(self, role: str) -> Player:
        for player in self.players:
            if player.role == role:
                return player
        raise ValueError(f"No player with role {role}")


if __name__ == "__main__":
    Simulation().run()
