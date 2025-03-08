from .datamodel import *
from .logic import step
from .df_to_states import states_to_df
import importlib.util
import os, io, hashlib, contextlib, sys
from datetime import datetime
from copy import deepcopy
from abc import abstractmethod


class Trader:
    @abstractmethod
    def run(self, state: TradingState) -> tuple[dict[list[Order]], int, str]:
        pass


def load_strategy(script_path):
    """Dynamically load a trading strategy from a Python script."""
    with open(script_path,'r') as f:
        script = f.read()
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),"env"))
    spec = importlib.util.spec_from_file_location("strategy", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return script, module

def get_pnl(cash: dict[Symbol, int], state: TradingState):
    pnl = {k:v for k,v in cash.items()}
    for p in state.listings:
        od = state.order_depths[p]
        fair_buy = sum([k*v for k,v in od.buy_orders.items()])/sum(od.buy_orders.values())
        fair_sell = sum([k*v for k,v in od.sell_orders.items()])/sum(od.sell_orders.values())
        fair = (fair_buy+fair_sell)/2
        pnl[p] += fair*state.position[p]
    return pnl

def save_result(script, output, tag):
    folder_name = "ada_backtest"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    log_folder = os.path.join(folder_name, "log")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    script_folder = os.path.join(folder_name, "script")
    if not os.path.exists(script_folder):
        os.makedirs(script_folder)

    with open(f"{folder_name}/log/{tag}.log","w") as f:
        f.write(output)
    with open(f"{folder_name}/script/{tag}.py","w") as f:
        f.write(script)

def run_backtest(script_path, states: list[TradingState]) -> list[int]:
    """Executes the backtest using the Trader class."""
    if not os.path.exists(script_path):
        print(f"Error: {script_path} does not exist.")
        return

    script, strategy = load_strategy(script_path)

    if not hasattr(strategy, "Trader"):
        print("Error: The strategy file must define a `Trader` class.")
        return

    trader:Trader = strategy.Trader()
    
    if not hasattr(trader, "run"):
        print("Error: The `Trader` class must have a `run` method.")
        return

    trader:Trader

    n = len(states)
    state = states[0]
    cashes = [{"KELP": 0, "RAINFOREST_RESIN": 0}]
    pnls = [{"KELP": 0, "RAINFOREST_RESIN": 0}]
    to_print = "Sandbox logs:\n"
    for i in range(n):
        cash = deepcopy(cashes[-1])
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            orders, conversions, traderData = trader.run(state)
        algo_log = output_buffer.getvalue().strip()
        to_print += json.dumps({
            "sandboxLog": "",
            "lambdaLog": algo_log,
            "timestamp": i*100
        }, indent=2)+'\n'

        if i<n-1:
            state = step(state, orders, conversions, traderData, states[i+1])
            trades = state.own_trades
            for p in trades:
                for trade in trades[p]:
                    if trade.buyer == "SUBMISSION":
                        cash[p] -= trade.price*trade.quantity
                    if trade.seller == "SUBMISSION":
                        cash[p] += trade.price*trade.quantity
            cashes.append(cash)
            pnls.append(get_pnl(cash, state))

    prices_df, trades_df = states_to_df(states, pnls)
    prices_csv = prices_df.to_csv(sep=';', index=False)
    prices_str = io.StringIO(prices_csv).getvalue()
    trades_csv = trades_df.to_csv(sep=';', index=False)
    trades_str = io.StringIO(trades_csv).getvalue()
    
    to_print += f"\n\n\nActivities log:\n{prices_str}\n\n\nTrade History:\n{trades_str}"
    now = datetime.now()
    hash = hashlib.sha256(script.encode()).hexdigest()[:6]
    tag = now.strftime("%m-%d_%H.%M.%S_") +hash
    script = f'# Date-Hash Tag: {tag}\n# Final pnls: {pnls[-1]}\n\n'+script
    save_result(script, to_print, tag)
    return pnls