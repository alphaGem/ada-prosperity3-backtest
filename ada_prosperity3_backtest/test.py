import unittest
from .datamodel import *
from .logic import step

class TestStep(unittest.TestCase):
    def test_match_existing(self):
        order_depth = OrderDepth()
        order_depth.sell_orders[2025] = -10
        order_depth.buy_orders[2020] = 10
        orders = [Order("KELP", 2026, 13), Order("KELP", 2023, -10), Order("KELP", 2020, -5)]
        state = TradingState(
            traderData="",
            timestamp=0,
            listings={"KELP": Listing("KELP","KELP","KELP")},
            order_depths={"KELP": order_depth},
            own_trades={"KELP": []},
            market_trades={"KELP": []},
            position = {"KELP": 0},
            observations = Observation({},{})
        )
        next_state = TradingState(
            traderData="",
            timestamp=0,
            listings={"KELP": Listing("KELP","KELP","KELP")},
            order_depths={"KELP": OrderDepth()},
            own_trades={"KELP": []},
            market_trades={"KELP": []},
            position = {"KELP": 0},
            observations = Observation({},{})
        )
        ns = step(state, orders, 0, "", next_state)
        self.assertEqual(len(ns.own_trades["KELP"]), 2)
        t0 = ns.own_trades["KELP"][0]
        self.assertEqual(t0.buyer, "SUBMISSION")
        self.assertEqual(t0.seller, "MARKET")
        self.assertEqual(t0.price, 2025)
        self.assertEqual(t0.quantity, 10)
        t1 = ns.own_trades["KELP"][1]
        self.assertEqual(t1.buyer, "MARKET")
        self.assertEqual(t1.seller, "SUBMISSION")
        self.assertEqual(t1.price, 2020)
        self.assertEqual(t1.quantity, 5)

    def test_match_incoming(self):
        order_depth = OrderDepth()
        order_depth.buy_orders[2019]=15
        orders = [Order("KELP", 2026, -13), Order("KELP", 2023, 10), Order("KELP", 2020, 5)]
        state = TradingState(
            traderData="",
            timestamp=0,
            listings={"KELP": Listing("KELP","KELP","KELP")},
            order_depths={"KELP": order_depth},
            own_trades={"KELP": []},
            market_trades={"KELP": []},
            position = {"KELP": 0},
            observations = Observation({},{})
        )
        next_state = TradingState(
            traderData="",
            timestamp=0,
            listings={"KELP": Listing("KELP","KELP","KELP")},
            order_depths={"KELP": OrderDepth()},
            own_trades={"KELP": []},
            market_trades={"KELP": [Trade("KELP", 2019, 12, "Alice", "Charlie")]},
            position = {"KELP": 0},
            observations = Observation({},{})
        )
        ns = step(state, orders, 0, "", next_state)
        self.assertEqual(len(ns.market_trades["KELP"]), 0)
        self.assertEqual(len(ns.own_trades["KELP"]), 2)
        t0 = ns.own_trades["KELP"][0]
        self.assertEqual(t0.buyer, "SUBMISSION")
        self.assertEqual(t0.seller, "Charlie")
        self.assertEqual(t0.price, 2023)
        self.assertEqual(t0.quantity, 10)
        t1 = ns.own_trades["KELP"][1]
        self.assertEqual(t1.buyer, "SUBMISSION")
        self.assertEqual(t1.seller, "Charlie")
        self.assertEqual(t1.price, 2020)
        self.assertEqual(t1.quantity, 2)

    def test_match_tie(self):
        order_depth = OrderDepth()
        order_depth.buy_orders[2020]=15
        orders = [Order("KELP", 2026, -13), Order("KELP", 2023, 10), Order("KELP", 2020, 5)]
        state = TradingState(
            traderData="",
            timestamp=0,
            listings={"KELP": Listing("KELP","KELP","KELP")},
            order_depths={"KELP": order_depth},
            own_trades={"KELP": []},
            market_trades={"KELP": []},
            position = {"KELP": 0},
            observations = Observation({},{})
        )
        next_state = TradingState(
            traderData="",
            timestamp=0,
            listings={"KELP": Listing("KELP","KELP","KELP")},
            order_depths={"KELP": OrderDepth()},
            own_trades={"KELP": []},
            market_trades={"KELP": [Trade("KELP", 2020, 12, "Alice", "Charlie")]},
            position = {"KELP": 0},
            observations = Observation({},{})
        )
        ns = step(state, orders, 0, "", next_state)
        self.assertEqual(len(ns.market_trades["KELP"]), 1)
        self.assertEqual(len(ns.own_trades["KELP"]), 1)
        t0 = ns.own_trades["KELP"][0]
        self.assertEqual(t0.buyer, "SUBMISSION")
        self.assertEqual(t0.seller, "Charlie")
        self.assertEqual(t0.price, 2023)
        self.assertEqual(t0.quantity, 10)
        t1 = ns.market_trades["KELP"][0]
        self.assertEqual(t1.buyer, "MARKET")
        self.assertEqual(t1.seller, "Charlie")
        self.assertEqual(t1.price, 2020)
        self.assertEqual(t1.quantity, 2)

    def test_exceeding_order_limit(self):
        pass

if __name__ == "__main__":
    unittest.main()
