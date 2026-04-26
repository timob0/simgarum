from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List, Optional


FISH_PRICE = 1.0
SALT_PRICE = 0.5
STANDARD_GARUM_PRICE = 10.0
PREMIUM_GARUM_PRICE = 22.0
MERCHANT_MARKUP = 0.25
WHOLESALE_DISCOUNT = 0.88
PREMIUM_WHOLESALE_DISCOUNT = 0.94

STANDARD_RECIPE_FISH = 5
STANDARD_RECIPE_SALT = 2
PREMIUM_RECIPE_FISH = 4
PREMIUM_RECIPE_SALT = 2

STANDARD_PRODUCTION_TICKS = 3
PREMIUM_PRODUCTION_TICKS = 6

BOAT_COST = 60.0
PAN_COST = 60.0
PRODUCTION_SLOT_COST = 80.0
MERCHANT_SHIP_COST = 100.0

STANDARD_SHIP_CAPACITY = 2
PREMIUM_SHIP_CAPACITY = 1


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
class ProducerSlot:
    mode: str = "standard"
    progress: int = 0


@dataclass
class Shipment:
    quality: str
    quantity: int
    ticks_remaining: int
    destination: str
    transport_cost_paid: float


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
    producer_slots: Optional[List[ProducerSlot]] = None
    merchant_ships: int = 0
    shipments: List[Shipment] = field(default_factory=list)


@dataclass
class GarumMarket:
    location: str
    preferred_quality: str
    distance_from_baelo: int
    base_standard_price: float = STANDARD_GARUM_PRICE
    base_premium_price: float = PREMIUM_GARUM_PRICE
    standard_demand: float = 4.0
    premium_demand: float = 2.0
    standard_supply_sold_last_tick: int = 0
    premium_supply_sold_last_tick: int = 0

    def standard_price(self) -> float:
        quality_bias = 0.95 if self.preferred_quality == "premium" else 1.05
        distance_bias = 1.0 + 0.03 * self.distance_from_baelo
        demand_pressure = 1.0 + 0.08 * (self.standard_demand - self.standard_supply_sold_last_tick)
        return max(4.0, round(self.base_standard_price * quality_bias * distance_bias * demand_pressure, 2))

    def premium_price(self) -> float:
        quality_bias = 1.15 if self.preferred_quality == "premium" else 0.95
        distance_bias = 1.0 + 0.04 * self.distance_from_baelo
        demand_pressure = 1.0 + 0.08 * (self.premium_demand - self.premium_supply_sold_last_tick)
        return max(8.0, round(self.base_premium_price * quality_bias * distance_bias * demand_pressure, 2))

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
        demand = max(0, int(round(self.rng.gauss(4.0 + seller.inventory.boats, 1.5))))
        quantity = min(quantity, seller.inventory.fish, demand)
        revenue = quantity * FISH_PRICE
        seller.inventory.fish -= quantity
        seller.inventory.gold += revenue
        return revenue

    def sell_salt(self, seller: Player, quantity: int) -> float:
        demand = max(0, int(round(self.rng.gauss(8.0 + seller.inventory.pans, 2.0))))
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
                inventory=Inventory(gold=30.0, fish=10, salt=4, empty_amphorae=2),
                producer_slots=[ProducerSlot(), ProducerSlot()],
            ),
            Player(
                name="Cassia",
                role="merchant",
                location="Baelo",
                inventory=Inventory(gold=80.0),
                merchant_ships=1,
            ),
        ]
        self.markets: Dict[str, GarumMarket] = {
            "Baelo": GarumMarket(location="Baelo", preferred_quality="standard", distance_from_baelo=0, standard_demand=2.0, premium_demand=1.0),
            "Rome": GarumMarket(location="Rome", preferred_quality="premium", distance_from_baelo=3, standard_demand=5.0, premium_demand=6.0),
            "Alexandria": GarumMarket(location="Alexandria", preferred_quality="standard", distance_from_baelo=4, standard_demand=6.0, premium_demand=3.0),
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
            self.advance_shipments(verbose)
            self.sell_surplus_raw_materials(verbose)
            self.merchants_invest(verbose)
            self.producers_invest(verbose)
            self.raw_producers_invest(verbose)

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
            needed_amphorae = len(player.producer_slots or [])
            if player.inventory.empty_amphorae < needed_amphorae:
                self.world_market.provide_amphorae(player, needed_amphorae - player.inventory.empty_amphorae)
            min_fish = 3 * max(1, len(player.producer_slots or []))
            min_salt = 2 * max(1, len(player.producer_slots or []))
            if player.inventory.fish < min_fish:
                bought = self.world_market.buy_fish(player, min_fish - player.inventory.fish)
                if verbose and bought > 0:
                    print(f"{player.name} buys {bought} fish for {bought * FISH_PRICE:.2f} gold")
            if player.inventory.salt < min_salt:
                bought = self.world_market.buy_salt(player, min_salt - player.inventory.salt)
                if verbose and bought > 0:
                    print(f"{player.name} buys {bought} salt for {bought * SALT_PRICE:.2f} gold")

    def advance_garum_production(self, verbose: bool) -> None:
        for player in self.players:
            if player.role != "producer":
                continue

            slots = player.producer_slots or [ProducerSlot(mode=player.production_mode, progress=player.production_progress)]
            for index, slot in enumerate(slots, start=1):
                if slot.progress == 0:
                    slot.mode = self.choose_production_mode(player)
                    needed_fish, needed_salt, duration = self.recipe_for_mode(slot.mode)
                    if player.inventory.fish >= needed_fish and player.inventory.salt >= needed_salt and player.inventory.empty_amphorae >= 1:
                        player.inventory.fish -= needed_fish
                        player.inventory.salt -= needed_salt
                        player.inventory.empty_amphorae -= 1
                        slot.progress = 1
                        if verbose:
                            print(f"{player.name} starts {slot.mode} garum production in slot {index}")
                    continue

                _, _, duration = self.recipe_for_mode(slot.mode)
                slot.progress += 1
                if slot.progress >= duration:
                    if slot.mode == "standard":
                        player.inventory.standard_garum += 1
                        self.total_standard_completed += 1
                    else:
                        player.inventory.premium_garum += 1
                        self.total_premium_completed += 1
                    slot.progress = 0
                    player.inventory.empty_amphorae += 1
                    if verbose:
                        print(f"{player.name} completes 1 amphora of {slot.mode} garum in slot {index}")

            player.producer_slots = slots

    def choose_production_mode(self, player: Player) -> str:
        if self.producer_mode == "standard":
            return "standard"
        if self.producer_mode == "premium":
            return "premium"

        producer_market = self.markets[player.location]
        distant_market = self.markets["Rome"]
        standard_revenue = producer_market.standard_price() * WHOLESALE_DISCOUNT
        premium_revenue = distant_market.premium_price() * PREMIUM_WHOLESALE_DISCOUNT
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
        available_capacity_standard = merchant.merchant_ships * STANDARD_SHIP_CAPACITY
        available_capacity_premium = merchant.merchant_ships * PREMIUM_SHIP_CAPACITY

        if producer.inventory.standard_garum > 0 and available_capacity_standard > 0:
            retail_price = producer_market.standard_price()
            wholesale_price = round(retail_price * WHOLESALE_DISCOUNT, 2)
            quantity = min(producer.inventory.standard_garum, available_capacity_standard)
            affordable = min(quantity, int(merchant.inventory.gold // wholesale_price)) if wholesale_price > 0 else quantity
            if affordable > 0:
                destination = self.choose_market_destination("standard")
                distance = self.markets[destination].distance_from_baelo
                transport_cost = affordable * distance * 0.5
                total = affordable * wholesale_price + transport_cost
                if merchant.inventory.gold >= total:
                    producer.inventory.standard_garum -= affordable
                    producer.inventory.gold += affordable * wholesale_price
                    merchant.inventory.gold -= total
                    merchant.shipments.append(
                        Shipment("standard", affordable, distance, destination, transport_cost)
                    )
                    if verbose:
                        print(f"{merchant.name} buys {affordable} standard garum from {producer.name} for {affordable * wholesale_price:.2f} gold")

        if producer.inventory.premium_garum > 0 and available_capacity_premium > 0:
            retail_price = producer_market.premium_price()
            wholesale_price = round(retail_price * PREMIUM_WHOLESALE_DISCOUNT, 2)
            quantity = min(producer.inventory.premium_garum, available_capacity_premium)
            affordable = min(quantity, int(merchant.inventory.gold // wholesale_price)) if wholesale_price > 0 else quantity
            if affordable > 0:
                destination = self.choose_market_destination("premium")
                distance = self.markets[destination].distance_from_baelo
                transport_cost = affordable * distance * 1.0
                total = affordable * wholesale_price + transport_cost
                if merchant.inventory.gold >= total:
                    producer.inventory.premium_garum -= affordable
                    producer.inventory.gold += affordable * wholesale_price
                    merchant.inventory.gold -= total
                    merchant.shipments.append(
                        Shipment("premium", affordable, distance, destination, transport_cost)
                    )
                    if verbose:
                        print(f"{merchant.name} buys {affordable} premium garum from {producer.name} for {affordable * wholesale_price:.2f} gold")

    def choose_market_destination(self, quality: str) -> str:
        candidates = [market for market in self.markets.values() if market.location != "Baelo"]
        if quality == "premium":
            weights = [market.premium_price() * market.premium_demand for market in candidates]
        else:
            weights = [market.standard_price() * market.standard_demand for market in candidates]
        return self.rng.choices(candidates, weights=weights, k=1)[0].location

    def advance_shipments(self, verbose: bool) -> None:
        merchant = self.get_role_player("merchant")
        remaining: List[Shipment] = []
        for shipment in merchant.shipments:
            shipment.ticks_remaining -= 1
            if shipment.ticks_remaining > 0:
                remaining.append(shipment)
                continue

            market = self.markets[shipment.destination]
            if shipment.quality == "standard":
                demand = max(0, int(round(self.rng.gauss(market.standard_demand, 1.0))))
                quantity_sold = min(shipment.quantity, demand)
                sale_price = round(market.standard_price() * (1.0 + MERCHANT_MARKUP), 2)
                spoilage = max(0, shipment.quantity - quantity_sold)
                spoilage_cost = spoilage * 0.5
                revenue = quantity_sold * sale_price
                merchant.inventory.gold += revenue - spoilage_cost
                market.standard_supply_sold_last_tick += quantity_sold
                self.total_standard_sold += quantity_sold
                if verbose:
                    print(f"{merchant.name} receives and sells {quantity_sold}/{shipment.quantity} standard garum in {shipment.destination} for {revenue:.2f} gold")
            else:
                demand = max(0, int(round(self.rng.gauss(market.premium_demand, 1.0))))
                quantity_sold = min(shipment.quantity, demand)
                sale_price = round(market.premium_price() * (1.0 + MERCHANT_MARKUP), 2)
                spoilage = max(0, shipment.quantity - quantity_sold)
                spoilage_cost = spoilage * 1.5
                revenue = quantity_sold * sale_price
                merchant.inventory.gold += revenue - spoilage_cost
                market.premium_supply_sold_last_tick += quantity_sold
                self.total_premium_sold += quantity_sold
                if verbose:
                    print(f"{merchant.name} receives and sells {quantity_sold}/{shipment.quantity} premium garum in {shipment.destination} for {revenue:.2f} gold")

        merchant.shipments = remaining

    def sell_surplus_raw_materials(self, verbose: bool) -> None:
        fisherman = self.get_role_player("fisherman")
        salt_maker = self.get_role_player("salt-maker")

        if fisherman.inventory.fish > 0:
            sold = fisherman.inventory.fish
            revenue = self.world_market.sell_fish(fisherman, sold)
            if verbose:
                print(f"{fisherman.name} sells raw fish for {revenue:.2f} gold")

        if salt_maker.inventory.salt > 0:
            sold = salt_maker.inventory.salt
            revenue = self.world_market.sell_salt(salt_maker, sold)
            if verbose:
                print(f"{salt_maker.name} sells raw salt for {revenue:.2f} gold")

    def raw_producers_invest(self, verbose: bool) -> None:
        fisherman = self.get_role_player("fisherman")
        salt_maker = self.get_role_player("salt-maker")

        if fisherman.inventory.gold >= BOAT_COST + 60:
            fisherman.inventory.gold -= BOAT_COST
            fisherman.inventory.boats += 1
            if verbose:
                print(f"{fisherman.name} buys a new boat")

        if salt_maker.inventory.gold >= PAN_COST + 60:
            salt_maker.inventory.gold -= PAN_COST
            salt_maker.inventory.pans += 1
            if verbose:
                print(f"{salt_maker.name} expands with a new salt pan")

    def producers_invest(self, verbose: bool) -> None:
        producer = self.get_role_player("producer")
        if producer.inventory.gold >= PRODUCTION_SLOT_COST + 50:
            producer.inventory.gold -= PRODUCTION_SLOT_COST
            producer.producer_slots = producer.producer_slots or []
            producer.producer_slots.append(ProducerSlot())
            producer.inventory.empty_amphorae += 1
            if verbose:
                print(f"{producer.name} adds a new production slot")

    def merchants_invest(self, verbose: bool) -> None:
        merchant = self.get_role_player("merchant")
        in_transit = len(merchant.shipments)
        if merchant.inventory.gold >= MERCHANT_SHIP_COST + 50 and in_transit >= merchant.merchant_ships:
            merchant.inventory.gold -= MERCHANT_SHIP_COST
            merchant.merchant_ships += 1
            if verbose:
                print(f"{merchant.name} buys a new merchant ship")

    def snapshot(self, ticks: int) -> Dict[str, object]:
        role_gold = {player.role: round(player.inventory.gold, 2) for player in self.players}
        merchant = self.get_role_player("merchant")
        producer = self.get_role_player("producer")
        fisherman = self.get_role_player("fisherman")
        salt_maker = self.get_role_player("salt-maker")
        return {
            "ticks": ticks,
            "role_gold": role_gold,
            "merchant_ships": merchant.merchant_ships,
            "producer_slots": len(producer.producer_slots or []),
            "boats": fisherman.inventory.boats,
            "pans": salt_maker.inventory.pans,
            "shipments_in_transit": len(merchant.shipments),
            "total_standard_completed": self.total_standard_completed,
            "total_premium_completed": self.total_premium_completed,
            "total_standard_sold": self.total_standard_sold,
            "total_premium_sold": self.total_premium_sold,
        }

    def print_market_snapshot(self) -> None:
        for market in self.markets.values():
            print(
                f"Market {market.location}: standard={market.standard_price():.2f}, premium={market.premium_price():.2f}, "
                f"prefers={market.preferred_quality}, distance={market.distance_from_baelo}"
            )

    def print_player_snapshot(self) -> None:
        for player in self.players:
            inv = player.inventory
            extra = ""
            if player.role == "producer":
                extra = f" slots={len(player.producer_slots or [])} prog={self.format_progress(player)}"
            elif player.role == "merchant":
                extra = f" ships={player.merchant_ships} transit={len(player.shipments)}"
            print(
                f"{player.name:7s} {player.role:10s} gold={inv.gold:7.2f} fish={inv.fish:3d} salt={inv.salt:3d} "
                f"empty_amp={inv.empty_amphorae:2d} std={inv.standard_garum:2d} prem={inv.premium_garum:2d} "
                f"boats={inv.boats:2d} pans={inv.pans:2d}{extra}"
            )

    def format_progress(self, player: Player) -> str:
        if player.producer_slots:
            return "/".join(str(slot.progress) for slot in player.producer_slots)
        return str(player.production_progress)

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
        print(f"- {role:10s} avg_gold={avg_gold:8.2f} min={min_gold:8.2f} max={max_gold:8.2f}")

    print(f"- avg boats:           {mean(snapshot['boats'] for snapshot in snapshots):.2f}")
    print(f"- avg pans:            {mean(snapshot['pans'] for snapshot in snapshots):.2f}")
    print(f"- avg producer slots:  {mean(snapshot['producer_slots'] for snapshot in snapshots):.2f}")
    print(f"- avg merchant ships:  {mean(snapshot['merchant_ships'] for snapshot in snapshots):.2f}")
    print(f"- avg standard done:   {mean(snapshot['total_standard_completed'] for snapshot in snapshots):.2f}")
    print(f"- avg premium done:    {mean(snapshot['total_premium_completed'] for snapshot in snapshots):.2f}")
    print(f"- avg standard sold:   {mean(snapshot['total_standard_sold'] for snapshot in snapshots):.2f}")
    print(f"- avg premium sold:    {mean(snapshot['total_premium_sold'] for snapshot in snapshots):.2f}")
    print(f"- avg shipments live:  {mean(snapshot['shipments_in_transit'] for snapshot in snapshots):.2f}")


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
