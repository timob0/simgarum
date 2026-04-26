from simgarum.engine import Simulation, run_monte_carlo, parse_args


if __name__ == "__main__":
    args = parse_args()
    if args.runs > 1:
        run_monte_carlo(runs=args.runs, ticks=args.ticks, producer_mode=args.producer_mode, seed=args.seed)
    else:
        Simulation(seed=args.seed, producer_mode=args.producer_mode, tick_duration_seconds=args.tick_seconds).run(ticks=args.ticks, verbose=True)
