#### How to use in commandline

1. `pip install ada-prosperity3-backtest`. Or, if you have already installed it, remember to upgrade frequently because the package is still in development, and there will be data update during the contest.

2. The following commands can be used:

- `ada-prosperity3-backtest script.py --round x [--day y]`

   This will run `script.py` for you on round `x` day `y`. If `--day` is not specified, it will run on all days. The backtest tool should show you some information in the terminal.

   Currently, we only support round 0 day 0, which is the tutorial round.

3. After running, you should see a `ada_backtest` folder at the place you run the commandline, and inside there is a `log` folder contaning backtest logs, which is compatible with the log output from the website, and a `script` folder containing the script you run backtest on, with some additional comments at the beginning as a summary of the backtest result. The files are named `mmdd_HHMMSS_RxDy_hhhhhh.log/py`, where mmdd is the month & date, HHMMSS is the hour, minute and second, RxDy means day y of round x, and hhhhhh is the hash of the script.

4. Iterate your algorithm accordingly!

#### How to use in .ipynb

```python
from ada_prosperity3_backtest.backtest import run_backtest_with_round_and_day
result = run_backtest_with_round_and_day(trader, round, day, script, infix)
'''
Arguments:
    trader: Trader, your strategy
    round: int
    day: int
    script: [str|None], the script you want to save. If none, we will try to automatically detect the Trader class.
    infix: [str|None], the infix of saving.
Returns:
    result: BacktestResult, consisting of:
        result.pnls, a list of dictionary, the breakdown of accumulated pnls for each product in each turn.
        result.sandbox_logs: list[dict], the sandbox logs, containing your model's output.
        result.prices_df: pandas.DataFrame, the price history from the simulation.
        result.trades_df: pandas.DataFrame, the trade history from the simulation.
'''
```

Example on tutorial round:

```
from ada_prosperity3_backtest.backtest import run_backtest_with_round_and_day
result = run_backtest_with_round_and_day(trader, 0, 0)
```

WARNING: the back-up code under this calling method is automatically generated from `trader`, and is not guaranteed to be identical as your original code. Take your own risk when using!

#### How it simulates

The backtest is based on the history prices and trades. For each timestamp, assume the timestamp is $t$, the following will happen:

1. A `TradingState` will be passed onto your trading algorithm. The state consists of:

- Order depths based on the history prices at $t$.

- Trades, both own trades and market trades, based on the trades simulated iat $t-1$.

- Positions based on the position of the state at $t-1$, and the trades simulated at $t-1$.

- And some other variables, also produced in the simulation.

2. Your `Trader.run` will be called.

3. According to the response of your `Trader.run`, for each product, the following will happen:

- Your position and order quantity will be checked. If not satisfying the position limit, all orders will be canceled.

- Your trades will try to match with the current order depth. Successful matches will result in immediate changes.

- The history trades at $t$ will both try to match the current order depth and your orders, based on the price-time order. That is, we match the orders by price, and if at the same price both orders from `order_depth` and your own order exist,  `order_depth` will be matched first because those orders are placed before you.

4. During the simulation above, your own trades (happened in the current timestamp and ready to be passed to your algorithm for the next timestamp) are generated. The leftover trades from the next timestamp will be the market trades in the state passed to your algorithm in the next timestamp.

#### Pros and cons

The following are some pros and cons of this backtester.

**Pros:**

1. Strict price-order match of incoming trades, so that at the same price the market order depth will be first filled, then yours, simulating the situation that their orders have a higher priority than you.

2. Backup of your code, so that you know what to submit if you would like to rely on the metric of this backtester.

**Cons:**

1. Still in development, and not tested in real contests. This may lead to some instability.

2. The backtester may underestimate your performance, because you actively trading in the contest will likely trigger more trades with you, giving you more profit, or because of other reasons.

3. The backtester may also overestimate your performance, because of overfitting or other reasons.

According to our available data (n<10), the website result in the tutorial round seems to be around 110%-140% of the result of this backtester. You can take 125% as an estimation.

#### TODO List

- [x] Generate log files that are compatible with the log files from the website backtest.
    - [x] First part: lambda logs

    - [x] Second part: Prices history

    - [x] Third part: Trades history

- [x] Support running on all days at the same time.

- [x] Support running on `.ipynb` or regular python files.

- [ ] Support data from Prosperity2 to test the usage at a larger scale.

- [ ] Support conversions.

- [ ] Support secret spices and secret bots, which allows users to customize.