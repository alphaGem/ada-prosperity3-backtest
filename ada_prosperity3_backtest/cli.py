import argparse, os, sys, importlib
import pandas as pd
from .backtest import SaveConfig, run_backtest_with_round_and_day, run_backtest_with_round, run_backtest_with_log
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
    parser.add_argument("--save_dir", type=str, default="ada_backtest", help="The directory to save logs and backups")
    parser.add_argument("--infix", type=str, default="", help="The infix of saved file, which will appear in the name of the saved file")

    args = parser.parse_args()
    script, trader = get_trader(args.script)
    save_config = SaveConfig(
        script = script,
        infix = args.infix,
        save_dir = args.save_dir
    )
    if args.log_dir is not None:
        run_backtest_with_log(trader, args.log_dir, save_config)
    elif args.round is not None:
        if args.day is None:
            run_backtest_with_round(trader, args.round, save_config)
        else:
            run_backtest_with_round_and_day(trader, args.round, args.day, save_config)
    else:
        raise AttributeError("Must either specify the directory containing the test file by `--dir path`, or specify the round you would like to test by `--round x`.")

if __name__ == "__main__":
    main()