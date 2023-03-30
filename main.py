import matplotlib.pyplot as plt
import pandas as pd
from round2.billy.pina import Trader

from datamodel import *


class Simulation:
    def __init__(self):
        # Simulation data
        self.position = {}
        self.my_trades = {}
        self.market_trades = {}
        self.observations = {}
        self.resting_orders = {}

        # Trader's cash values
        self.cash = 0
        self.historical_cash = list()

        # Initial values for the time and the state
        self.prev_time = -1
        self.state = TradingState(-1, {}, {}, {}, {}, {}, {})

        # Simulation's position limit
        self.position_limit = 20

    def process_order(self, order: Order, is_resting_order: bool = False):
        # Get the product name
        product = order.symbol

        # Get order levels, { Price: Quantity }
        levels = self.state.order_depths[order.symbol]

        if order.quantity < 0:
            # Sell/Ask order - Need corresponding buy
            volume = abs(order.quantity)


            while len(levels.buy_orders):
                # Get the best bid (Highest buy price)
                best_bid = max(levels.buy_orders.keys())

                # Break if the best bid does not match the order price
                if best_bid < order.price: break

                # The amount that is exchanged (Buy orders are positive)
                taken_volume = min(volume, abs(levels.buy_orders[best_bid]))

                # If it is resting order and the position is invalid
                # after making order, then drop the order for now
                if is_resting_order and abs(self.position[product] - taken_volume) > self.position_limit: continue
                
                # Update volumes and position by taken_volume
                volume -= taken_volume
                levels.buy_orders[best_bid] -= taken_volume
                self.position[product] -= taken_volume

                # Update cash (Selling so cash increases by volume sold)
                self.cash += best_bid * taken_volume

                # Add the trade to completed trades
                self.my_trades[product].append(Trade(product, best_bid, taken_volume, None, "self", self.prev_time))

                # Break if volume left is 0
                if volume <= 0: break

                # Delist the buy order if it is fulfilled
                if levels.buy_orders[best_bid] <= 0: del levels.buy_orders[best_bid]


            # Add a resting order if the trader's order is not fulfilled
            if volume > 0:
                resting_order = Order(product, order.price, -volume)
                self.resting_orders[product].append(resting_order)
                print(f"Resting order added: {resting_order}")

        else:
            # Buy/Bid order - Need corresponding sell
            volume = abs(order.quantity)


            while len(levels.sell_orders):
                # Get the best ask (Lowest sell price)
                best_ask = min(levels.sell_orders.keys())

                # Break if the best ask does not match the order price
                if best_ask > order.price: break

                # The amount that is exchanged (Sell orders are negative)
                taken_volume = min(volume, abs(levels.sell_orders[best_ask]))

                # If it is resting order and the position is invalid
                # after making order, then drop the order for now
                if is_resting_order and abs(self.position[product] + taken_volume) > self.position_limit: continue

                # Update volumes and position by taken_volume
                volume -= taken_volume
                levels.sell_orders[best_ask] += taken_volume
                self.position[product] += taken_volume

                # Update cash (Buying so cash decreases by volume bought)
                self.cash -= best_ask * taken_volume

                # Add the trade to completed trades
                self.my_trades[product].append(Trade(product, best_ask, taken_volume, "self", None, self.prev_time))

                # Break if volume left is 0
                if volume <= 0: break

                # Delist the sell order if it is fulfilled
                if abs(levels.sell_orders[best_ask]) <= 0: del levels.sell_orders[best_ask]


            # Add a resting order if the trader's order is not fulfilled
            if volume > 0:
                resting_order = Order(product, order.price, volume)
                self.resting_orders[product].append(resting_order)
                print(f"Resting order added: {resting_order}")

    def simulate(self, round: int, day: int, trader: Trader):
        # The file path for the prices and trades of the selected round
        prices_path = f"round{round}/data/prices_round_{round}_day_{day}.csv"
        trades_path = f"round{round}/data/trades_round_{round}_day_{day}_nn.csv"

        # Data frames for each csv
        df_prices = pd.read_csv(prices_path, sep=';')
        df_trades = pd.read_csv(trades_path, sep=';')


        # Iterate through each row of the data frame
        for _, row in df_prices.iterrows():
            # The current time and product being traded
            time = row["timestamp"]
            product = row["product"]

            # Initialize product's data
            if product not in self.position:
                self.position[product] = 0
                self.my_trades[product] = []
                self.market_trades[product] = []

            # Default listing
            listing = {product: {"symbol": product, "product": product, "denomination": product}}

            # Setup order depth
            depth = {product: OrderDepth({}, {})}
            for i in range(1, 4):
                if row[f"bid_price_{i}"] > 0: depth[product].buy_orders[row[f"bid_price_{i}"]] = row[f"bid_volume_{i}"]
                if row[f"ask_price_{i}"] > 0: depth[product].sell_orders[row[f"ask_price_{i}"]] = -row[f"ask_volume_{i}"]

            # Get all trades that happened at this time
            trades = df_trades[df_trades['timestamp'] == time]

            # Process each of those trades
            for _, trade in trades.iterrows():
                # Get the product that is being traded
                symbol = trade['symbol']

                # Skip any trades that aren't for our product
                if symbol != product: continue

                # Create a new trade object and add it to market_trades
                t = Trade(symbol, trade['price'], trade['quantity'], trade['buyer'], trade['seller'], time)
                self.market_trades[product].append(t)

            # If time has elapsed
            if time != self.prev_time and self.prev_time != -1:

                # Update the current state's timestamp
                self.state.timestamp = time

                # Act on our trader's actions at this time
                output = trader.run(self.state)

                # Loop through each product
                for product in output:

                    # Process our trader's orders
                    for order in output[product]:
                        self.process_order(order)
                    output[product] = []

                    # Process resting orders
                    output[product].extend(self.resting_orders[product]);
                    self.resting_orders[product] = [];

                    for order in output[product]:
                        self.process_order(order, True);
                    output[product] = []

                # Update the trading state
                self.state = TradingState(time, listing, depth, self.my_trades, self.market_trades, self.position, self.observations)

            else:
                # Before trading starts, initialize trading state's listings and order_depths
                self.state.listings[product] = listing[product]
                self.state.order_depths[product] = depth[product]

                # Also initialize resting orders
                self.resting_orders[product] = []


            # Complain if the position limit is violated
            for product in self.position:
                if abs(self.position[product]) > self.position_limit:
                    print(f"Position limit for {product} violated - {self.position[product]}")
                    raise RuntimeError()

            # Update historical_cash
            self.historical_cash.append(self.cash)

            # Update prev_time
            self.prev_time = time

        # Output trader's end cash
        print(f"You ended with: {self.cash} seashells")

        # Plot trader's cash over time
        plt.plot(df_prices["timestamp"], self.historical_cash)
        plt.show()



if __name__ == '__main__':
    simulation = Simulation()
    simulation.simulate(1, 1, Trader())