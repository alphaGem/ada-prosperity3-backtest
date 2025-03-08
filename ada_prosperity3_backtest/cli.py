import argparse, os
import pandas as pd
from .backtest import run_backtest
from .datamodel import *
from .log_to_states import read_log
from .df_to_states import df_to_states

def main():
    parser = argparse.ArgumentParser(description="Backtest tool for Prosperity-3 trading competition, by team ADA Refactor.")
    parser.add_argument("script", type=str, help="Python script containing the trading strategy")
    parser.add_argument("--log_dir", type=str, required=False, help="Directory containing the test file")
    parser.add_argument("--round", type=int, required=False, help="Competition round number")
    parser.add_argument("--day", type=int, required=False, help="Day of the round")

    args = parser.parse_args()
    states = []
    if args.log_dir is not None:
        print(f"Reading files from directory {args.dir}")
        with open(args.dir,'r') as f:
            states = read_log(f.read())
    elif args.round is not None:
        
        if args.day is None:
            print(f"Running backtest on all days of round {args.round}")
            raise NotImplementedError("Please specify the --day variable; running without --day will be supported soon")
        else:
            print(f"Running backtest on day {args.day} of round {args.round}")

            script_dir = os.path.dirname(os.path.abspath(__file__))

            # Construct the absolute path to the CSV file
            folder_path = os.path.join(script_dir, "data", f"round{args.round}", f"day{args.day}")

            prices_path = os.path.join(folder_path, f"prices{args.round}{args.day}.csv")
            trades_path = os.path.join(folder_path, f"trades{args.round}{args.day}.csv")

            price_df = pd.read_csv(prices_path, sep=';')
            trade_df = pd.read_csv(trades_path, sep=';')
            states = df_to_states(price_df, trade_df)
    else:
        raise AttributeError("Must either specify the directory containing the test file by `--dir path`, or specify the round you would like to test by `--round x`.")

    pnls = run_backtest(args.script, states)
    print(pnls[-1], sum(pnls[-1].values()))

if __name__ == "__main__":
    main()