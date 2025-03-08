from .datamodel import *
from copy import deepcopy

def match(bid:Order, ask:Order, price: int, buyer: UserId, seller: UserId, timestamp: Time) -> Trade:
    '''
    Match two orders.
    NB: the orders will be changed if there is a successful match. (Usually there is)
    '''
    assert bid.quantity>0
    assert ask.quantity<0
    assert bid.symbol==ask.symbol
    assert bid.price>=ask.price
    quantity = min(bid.quantity, -ask.quantity)
    bid.quantity -= quantity
    ask.quantity += quantity
    return Trade(
        symbol = bid.symbol,
        price = price,
        quantity=quantity,
        buyer = buyer,
        seller = seller,
        timestamp = timestamp
    )

def match_bid_order(
        old_asks: dict[int, int],
        new_asks: dict[int, int],
        bid: Order,
        old_ask_trader: UserId,
        new_ask_trader: UserId,
        bid_trader: UserId,
        timestamp: Time) -> list[Trade]:
    '''
    Match a bid order with previous ask orders.
    NB: the `old_asks` and the `new_asks` will both be CHANGED, reflecting the successful matches.
    '''
    assert bid.quantity>0 # must be a bid order to proceed
    result: list[Trade] = []
    prices = set(old_asks.keys())
    prices.update(set(new_asks.keys()))
    prices = sorted(prices)
    for price in prices:
        if price > bid.price:
            break
        for (asks, buyer, seller) in [(old_asks, bid_trader, old_ask_trader), (new_asks, bid_trader, new_ask_trader)]:
            if price in asks:
                ask=Order(
                    bid.symbol,
                    price,
                    asks[price],
                )
                trade = match(bid, ask, price,buyer,seller,timestamp)
                result.append(trade)
                asks[price] = ask.quantity
                if asks[price] == 0:
                    asks.pop(price)
                if bid.quantity == 0:
                    break
        if bid.quantity == 0:
            break
    return result

def match_ask_order(
        old_bids: dict[int, int],
        new_bids: dict[int, int],
        ask: Order,
        old_bid_trader: UserId,
        new_bid_trader: UserId,
        ask_trader: UserId,
        timestamp: Time) -> list[Trade]:
    '''
    Match a bid order with previous ask orders.
    NB: the `old_asks` and the `new_asks` will both be CHANGED, reflecting the successful matches.
    '''
    assert ask.quantity<0 # must be a bid order to proceed
    result: list[Trade] = []
    prices = set(old_bids.keys())
    prices.update(set(new_bids.keys()))
    prices = sorted(prices, reverse=True)
    for price in prices:
        if price < ask.price:
            break
        for (bids, seller, buyer) in [(old_bids, ask_trader, old_bid_trader), (new_bids, ask_trader, new_bid_trader)]:
            if price in bids:
                bid=Order(
                    ask.symbol,
                    price,
                    bids[price],
                )
                trade = match(bid, ask, price,buyer,seller,timestamp)
                result.append(trade)
                bids[price] = bid.quantity
                if bids[price] == 0:
                    bids.pop(price)
                if ask.quantity == 0:
                    break
        if ask.quantity == 0:
            break
    return result

'''
ns update checklist
O traderData: str,
= timestamp: Time,
= listings: Dict[Symbol, Listing],
= order_depths: Dict[Symbol, OrderDepth],
O own_trades: Dict[Symbol, List[Trade]],
O market_trades: Dict[Symbol, List[Trade]],
O position: Dict[Product, Position],
= observations: Observation):
'''
def step(state: TradingState, orders: dict[Product, list[Order]], conversions: int, traderData: str, new_state: TradingState) -> TradingState:
    position_limit = {
        "KELP": 50,
        "RAINFOREST_RESIN": 50
    }
    inf = 10**9
    ns = deepcopy(new_state)
    ns.traderData = traderData
    ns.own_trades = {s:[] for s in state.listings}
    ns.market_trades = {s:[] for s in state.listings}
    # check order position
    new_position_max = deepcopy(state.position)
    new_position_min = deepcopy(state.position)
    for p in orders:
        for order in orders[p]:
            if order.quantity > 0:
                new_position_max[p] = new_position_max.get(p, 0) + order.quantity
            if order.quantity < 0:
                new_position_min[p] = new_position_min.get(p, 0) + order.quantity
    blacklist = set()
    for p in new_position_max:
        if new_position_max[p]>position_limit[p]:
            blacklist.add(p)
    for p in new_position_min:
        if new_position_min[p]<-position_limit[p]:
            blacklist.add(p)
    orders = {k:v for k,v in orders.items() if k not in blacklist}
    # TODO: conversion
    pass
    # match existing orders in state
    for p in orders:
        for order in orders[p]:
            if order.quantity > 0:
                ns.own_trades[p] += match_bid_order(
                    old_asks=state.order_depths[p].sell_orders,
                    new_asks={},
                    bid = order,
                    old_ask_trader = "MARKET",
                    new_ask_trader = "UNKNOWN",
                    bid_trader = "SUBMISSION",
                    timestamp = state.timestamp
                )
            elif order.quantity < 0:
                ns.own_trades[p] += match_ask_order(
                    old_bids=state.order_depths[p].buy_orders,
                    new_bids={},
                    ask = order,
                    old_bid_trader = "MARKET",
                    new_bid_trader = "UNKNOWN",
                    ask_trader = "SUBMISSION",
                    timestamp = state.timestamp
                )
            else:
                pass # ignore zero order
    # match orders observed from the new trading state to the current one
    
    for p in orders:
        own_bid_orders = {}
        for order in orders[p]:
            if order.quantity>0:
                own_bid_orders[order.price] = own_bid_orders.get(order.price, 0) + order.quantity
        own_ask_orders = {}
        for order in orders[p]:
            if order.quantity<0:
                own_ask_orders[order.price] = own_ask_orders.get(order.price, 0) + order.quantity
        if p not in new_state.market_trades:
            continue
        for trade in new_state.market_trades[p]:
            if trade.timestamp != state.timestamp:
                continue
            bid_price = max(
                max(own_bid_orders.keys(), default=-inf),
                max(state.order_depths[p].buy_orders.keys(),default=-inf)
            )
            ask_price = min(
                min(own_ask_orders.keys(), default=inf),
                min(state.order_depths[p].sell_orders.keys(), default=inf)
            )
            assert bid_price <= ask_price
            if trade.price <= bid_price: # try to match it with bid orders, as an ask order because it is selling low
                trades = match_ask_order(
                    state.order_depths[p].buy_orders,
                    own_bid_orders,
                    Order(p, trade.price, -trade.quantity),
                    "MARKET",
                    "SUBMISSION",
                    trade.seller,
                    trade.timestamp
                )
                for t in trades:
                    if t.buyer == "SUBMISSION" or t.seller == "SUBMISSION":
                        ns.own_trades[p].append(t)
                    else:
                        ns.market_trades[p].append(t)
            if trade.price >= ask_price: # try to match it with ask orders, as an bid order because it is buying high
                trades = match_bid_order(
                    state.order_depths[p].sell_orders,
                    own_ask_orders,
                    Order(p, trade.price, trade.quantity),
                    "MARKET",
                    "SUBMISSION",
                    trade.buyer,
                    trade.timestamp
                )
                for t in trades:
                    if t.buyer == "SUBMISSION" or t.seller == "SUBMISSION":
                        ns.own_trades[p].append(t)
                    else:
                        ns.market_trades[p].append(t)
    for p in ns.own_trades:
        pos = state.position.get(p, 0)
        for t in ns.own_trades[p]:
            if t.buyer == "SUBMISSION":
                pos += t.quantity
            if t.seller == "SUBMISSION":
                pos -= t.quantity
        ns.position[p] = pos
    return ns