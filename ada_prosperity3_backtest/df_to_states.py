import pandas as pd
from copy import deepcopy
from .datamodel import *

def df_to_states(prices: pd.DataFrame, trades: pd.DataFrame) -> list[TradingState]:
    states = []
    
    # Convert trades DataFrame into a dictionary grouped by timestamp and symbol
    trade_dict = {}
    trades["buyer"] = trades["buyer"].astype(str).fillna("", inplace=True)
    trades["seller"] = trades["seller"].astype(str).fillna("", inplace=True)
    for _, row in trades.iterrows():
        ts, sym, price, qty, buyer, seller = row["timestamp"], row["symbol"], row["price"], row["quantity"], row["buyer"], row["seller"]
        trade_obj = Trade(symbol=sym, price=int(price), quantity=int(qty), buyer=buyer, seller=seller, timestamp=ts)
        
        if ts not in trade_dict:
            trade_dict[ts] = {}
        if sym not in trade_dict[ts]:
            trade_dict[ts][sym] = []
        
        trade_dict[ts][sym].append(trade_obj)
    
    # Process price data to generate TradingState instances
    market_trades = {}
    for timestamp, grouped_df in prices.groupby("timestamp"):
        listings = {}
        order_depths = {}
        market_trades.update(trade_dict.get(timestamp-100, {}))  # Retrieve market trades for the timestamp
        own_trades = {}  # Assuming no own trades (initialize empty)
        position = {}  # Initialize empty positions
        observations = Observation({}, {})  # Empty for now
        
        for _, row in grouped_df.iterrows():
            product = row["product"]
            listings[product] = {
                "symbol": product,
                "product": product,
                "denomination": product
            }

            # Extract order book data
            order_depth = OrderDepth()
            for i in range(1, 4):
                bid_price = row.get(f"bid_price_{i}")
                bid_volume = row.get(f"bid_volume_{i}")
                ask_price = row.get(f"ask_price_{i}")
                ask_volume = row.get(f"ask_volume_{i}")
                
                if not pd.isna(bid_price) and not pd.isna(bid_volume):
                    order_depth.buy_orders[int(bid_price)] = int(bid_volume)
                if not pd.isna(ask_price) and not pd.isna(ask_volume):
                    order_depth.sell_orders[int(ask_price)] = -int(ask_volume)
            
            order_depths[product] = order_depth

        # Create TradingState object
        state = TradingState(
            traderData="",  # Empty for now
            timestamp=timestamp,
            listings=listings,
            order_depths=order_depths,
            own_trades=own_trades,
            market_trades=deepcopy(market_trades),
            position=position,
            observations=observations
        )
        
        states.append(state)
    
    return states

def states_to_df(states: list[TradingState], pnl: list[dict[Symbol, int]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    price_records = []
    trade_records = []

    for state in states:
        timestamp = state.timestamp
        
        # Process Order Depths (for prices.csv)
        for symbol, depth in state.order_depths.items():
            bid_prices = sorted(depth.buy_orders.keys(), reverse=True)
            ask_prices = sorted(depth.sell_orders.keys())

            record = {
                "day": 0,
                "timestamp": timestamp,
                "product": symbol,
                "bid_price_1": bid_prices[0] if len(bid_prices) > 0 else None,
                "bid_volume_1": depth.buy_orders[bid_prices[0]] if len(bid_prices) > 0 else None,
                "bid_price_2": bid_prices[1] if len(bid_prices) > 1 else None,
                "bid_volume_2": depth.buy_orders[bid_prices[1]] if len(bid_prices) > 1 else None,
                "bid_price_3": bid_prices[2] if len(bid_prices) > 2 else None,
                "bid_volume_3": depth.buy_orders[bid_prices[2]] if len(bid_prices) > 2 else None,
                "ask_price_1": ask_prices[0] if len(ask_prices) > 0 else None,
                "ask_volume_1": depth.sell_orders[ask_prices[0]] if len(ask_prices) > 0 else None,
                "ask_price_2": ask_prices[1] if len(ask_prices) > 1 else None,
                "ask_volume_2": depth.sell_orders[ask_prices[1]] if len(ask_prices) > 1 else None,
                "ask_price_3": ask_prices[2] if len(ask_prices) > 2 else None,
                "ask_volume_3": depth.sell_orders[ask_prices[2]] if len(ask_prices) > 2 else None,
            }

            # Calculate mid_price
            if len(bid_prices) > 0 and len(ask_prices) > 0:
                record["mid_price"] = (bid_prices[0] + ask_prices[0]) / 2
            else:
                record["mid_price"] = None

            record["profit_and_loss"] = pnl[timestamp//100].get(symbol, 0)

            price_records.append(record)

        for trades in state.own_trades.values():
            for trade in trades:
                trade_records.append({
                    "timestamp": trade.timestamp,
                    "buyer": trade.buyer if trade.buyer else "",
                    "seller": trade.seller if trade.seller else "",
                    "symbol": trade.symbol,
                    "price": trade.price,
                    "quantity": trade.quantity,
                })

        for trades in state.market_trades.values():
            for trade in trades:
                trade_records.append({
                    "timestamp": trade.timestamp,
                    "buyer": trade.buyer if trade.buyer else "",
                    "seller": trade.seller if trade.seller else "",
                    "symbol": trade.symbol,
                    "price": trade.price,
                    "quantity": trade.quantity,
                })

    # Convert to DataFrames
    prices_df = pd.DataFrame(price_records)
    trades_df = pd.DataFrame(trade_records)

    trades_df["buyer"] = trades_df["buyer"].fillna("")
    trades_df["seller"] = trades_df["seller"].fillna("")

    return prices_df, trades_df