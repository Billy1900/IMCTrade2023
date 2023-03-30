from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order

def printOrderBook(book, specific=[]):
    for product in book.keys():
        if specific and product not in specific:
            continue
        print(product)
        print("Buy orders:")
        print(book[product].buy_orders)
        print("Sell orders:")
        print(book[product].sell_orders)


class Trader:

    def __init__(self):
        self.curOrders = {}


    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}
        self.curOrders = {} # Initialize the method output dict as an empty dict

        print("My prev confirmed trades:======================================")
        print(state.own_trades)
        print("Prev market trades:~~~~~~~~~~~~~~~")
        print(state.market_trades)
        print("============================================================")
        printOrderBook(state.order_depths, specific=['PEARLS'])

        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths.keys():

            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':
                """
                # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
                order_depth: OrderDepth = state.order_depths[product]

                # Initialize the list of Orders to be sent as an empty list
                orders: list[Order] = []

                # Define a fair value for the PEARLS.
                # Note that this value of 1 is just a dummy value, you should likely change it!
                acceptable_price = 10000

                # If statement checks if there are any SELL orders in the PEARLS market
                if len(order_depth.sell_orders) > 0:
                    # Sort all the available sell orders by their price,
                    # and select only the sell order with the lowest price
                    best_ask = min(order_depth.sell_orders.keys())
                    best_ask_volume = -1*min(-1*order_depth.sell_orders[best_ask], 20-state.position.get(product,0))
                    # Check if the lowest ask (sell order) is lower than the above defined fair value
                    if best_ask < acceptable_price and best_ask_volume:
                        # In case the lowest ask is lower than our fair value,
                        # This presents an opportunity for us to buy cheaply
                        # The code below therefore sends a BUY order at the price level of the ask,
                        # with the same quantity
                        # We expect this order to trade with the sell order
                        print("BUY", str(-best_ask_volume) + "x", best_ask)
                        orders.append(Order(product, best_ask, -best_ask_volume))

                # The below code block is similar to the one above,
                # the difference is that it find the highest bid (buy order)
                # If the price of the order is higher than the fair value
                # This is an opportunity to sell at a premium
                if len(order_depth.buy_orders) != 0:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = min(order_depth.buy_orders[best_bid], 20+state.position.get(product,0))
                    if best_bid > acceptable_price:
                        print("SELL", str(best_bid_volume) + "x", best_bid)
                        orders.append(Order(product, best_bid, -best_bid_volume))

                # Add all the above the orders to the result dict
                result[product] = orders
                """
                self.pearlsStrat(state)

                print(self.curOrders)
        return self.curOrders

    def pearlsStrat(self, state, theo=10000, limit=20):
        # theo is the theoretical price of pearls
        product = 'PEARLS'
        orders: list[Order] = []
        order_depth: OrderDepth = state.order_depths.get(product, 0)

        if order_depth == 0:
            print("Order book does not contain {}. PearlStrat strategy exiting".format(product))
            return
        myPosition = state.position.get(product, 0)
        sells = order_depth.sell_orders # asks
        buys = order_depth.buy_orders # bids
        sellPrices = sorted(list(sells.keys()))
        buyPrices = sorted(list(buys.keys()))
        best_ask = sellPrices[0] if sellPrices else -1
        best_bid = buyPrices[-1] if buyPrices else -1

        if best_bid >= theo:
            for p in buyPrices[::-1]:
                # sell as much as possible above theo price
                if p < theo:
                    break
                sell_q = min(buys[p], limit + myPosition)
                if sell_q:
                    print("*******Selling for price: {} and quantity: {}".format(p, sell_q))
                    orders.append(Order(product, p, -sell_q))
                    myPosition -= sell_q
                if myPosition <= -limit:
                    break
        elif best_ask <= theo:
            for p in sellPrices:
                # buy as much as possible below theo price
                if p > theo:
                    break
                buy_q = min(-sells[p], limit - myPosition)
                if buy_q:
                    print("*******Buying for price: {} and quantity: {}".format(p, buy_q))
                    orders.append(Order(product, p, buy_q))
                    myPosition += buy_q
                if myPosition >= limit:
                    break

        elif best_bid < theo and best_ask > theo and best_bid != -1 and best_ask != -1:
            # money making portion
            print("Potential buy or sell submitted.")
            if myPosition > 0 :
                orders.append(Order(product, best_ask-1, -myPosition-limit)) # try to sell my position by creating a new best_ask price
                orders.append(Order(product, best_bid+1, limit-myPosition))
            elif myPosition < 0:
                orders.append(Order(product, best_bid+1, -myPosition+limit)) # try to buy my position back by creating a new best_bid price
                orders.append(Order(product, best_ask-1, -(limit+myPosition)))
            else: #myPosition == 0
                orders.append(Order(product, best_ask-1, -limit))
                orders.append(Order(product, best_bid+1, limit))
                """
                if best_ask-1 != theo and best_bid+1 != theo:
                    orders.append(Order(product, best_ask-1, -limit//2))
                    orders.append(Order(product, best_bid+1, limit//2))
                elif best_ask-1 == theo and best_bid+1 != theo:
                    orders.append(Order(product, best_bid+1, limit//2))
                elif best_ask-1 != theo and best_bid+1 == theo:
                    orders.append(Order(product, best_ask-1, -limit//2))
                else: #bestbid+1 == bestask+1==theo, then simply buy limit/2 amount of products
                    orders.append(Order(product, best_bid+1, limit//2))"""

        if orders:
            self.curOrders[product] = orders
        return
