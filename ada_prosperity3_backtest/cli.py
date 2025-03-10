import argparse, os, sys, importlib
import pandas as pd
from .backtest import run_backtest_with_round_and_day, run_backtest_with_round, run_backtest_with_log
from .datamodel import *

def load_strategy(script_path):
    """Dynamically load a trading strategy from a Python script."""
    with open(script_path,'r') as f:
        script = f.read()
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),"env"))
    spec = importlib.util.spec_from_file_location("strategy", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return script, module


def get_trader(script_path):
    if not os.path.exists(script_path):
        print(f"Error: {script_path} does not exist.")
        return
    script, strategy = load_strategy(script_path)
    if not hasattr(strategy, "Trader"):
        print("Error: The strategy file must define a `Trader` class.")
        return

    trader = strategy.Trader()
    return script, trader


def main():
    parser = argparse.ArgumentParser(description="Backtest tool for Prosperity-3 trading competition, by team ADA Refactor.")
    parser.add_argument("script", type=str, help="Python script containing the trading strategy")
    parser.add_argument("--log_dir", type=str, required=False, help="Directory containing the test file")
    parser.add_argument("--round", type=int, required=False, help="Competition round number")
    parser.add_argument("--day", type=int, required=False, help="Day of the round")

    args = parser.parse_args()
    script, trader = get_trader(args.script)
    if args.log_dir is not None:
        run_backtest_with_log(trader, args.log_dir, script)
    elif args.round is not None:
        if args.day is None:
            run_backtest_with_round(trader, args.round, script)
        else:
            run_backtest_with_round_and_day(trader, args.round, args.day, script)
    else:
        raise AttributeError("Must either specify the directory containing the test file by `--dir path`, or specify the round you would like to test by `--round x`.")

if __name__ == "__main__":
    main()