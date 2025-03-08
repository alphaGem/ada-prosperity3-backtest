import json, re
from .datamodel import *

def read_log(log_str: str) -> list[TradingState]:
    products = [
        'KELP',
        'RAINFOREST_RESIN'
    ]
    limits = {
        'KELP': 50,
        'RAINFOREST_RESIN': 50
    }

    sandbox_logs, activities, trade_history = [s.strip() for s in re.split(r'(\r?\n){2,}', log_str) if len(s.strip())>0]
    sandbox_logs = re.split('\{\r?\n', sandbox_logs)[1:]
    sandbox_logs = ['{\n'+log for log in sandbox_logs]
    states = []
    for log in sandbox_logs:
        log_json = json.loads(log)
        sandbox_log = log_json["sandboxLog"]
        lambda_log = json.loads(log_json["lambdaLog"])
        state, orders, converstions, trader_data, logs = lambda_log
        t, trader_data, listings, order_depths, own_trades, market_trades, position, observations = state
        def get_order_depth(v0,v1):
            od = OrderDepth()
            od.buy_orders = {int(k):v for k,v in v0.items()}
            od.sell_orders = {int(k):v for k,v in v1.items()}
            return od
        ot = {}
        mt = {}
        for v in own_trades:
            if v[2]==0:
                continue
            if v[0] not in mt:
                mt[v[0]] = []
            mt[v[0]].append(Trade(v[0],v[1],v[2],v[3],v[4],v[5]))
        for v in market_trades:
            if v[2]==0:
                continue
            if v[0] not in mt:
                mt[v[0]] = []
            mt[v[0]].append(Trade(v[0],v[1],v[2],v[3],v[4],v[5]))
        state = TradingState(
            traderData=trader_data,
            timestamp=t,
            listings={v[0]: {
                "symbol": v[0],
                "product": v[1],
                "denomination": v[2]
            } for v in listings},
            order_depths={k:get_order_depth(v[0],v[1]) for k,v in order_depths.items()},
            own_trades=ot,
            market_trades=mt,
            position=position,
            observations=Observation({},{}) # TODO: fix observations
        )
        states.append(state)
    return states
