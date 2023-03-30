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
        self.pnl = {} #{product:{time:set, pnl:int}}
        self.POSITION_LIMIT = 20
        self.ask_vol_dict = {}
        self.buy_vol_dict = {}
        self.quote_maps(1.0)

    def quote_maps(self, risk_factor: float):
        for position in range(-20, 21):
            bid_vol = int(((20 - position - risk_factor) / 2.0)) - int(risk_factor / 2.0)
            bid_vol = max(0, bid_vol)

            if position < 0:
                ask_vol = int(((20 - abs(position) - risk_factor) / 2.0)) - int(risk_factor / 2.0)
            else:
                ask_vol = int(((20 + abs(position) - risk_factor) / 2.0)) - int(risk_factor / 2.0)
            ask_vol = max(0, ask_vol)

            self.buy_vol_dict[position] = bid_vol
            self.ask_vol_dict[position] = ask_vol
    
    def getBestBidAsk(self, state, product):
        order_depth: OrderDepth = state.order_depths.get(product, 0)
        sells = order_depth.sell_orders # asks
        buys = order_depth.buy_orders # bids
        sellPrices = sorted(list(sells.keys()))
        buyPrices = sorted(list(buys.keys()))
        best_ask = sellPrices[0] if sellPrices else -1
        best_bid = buyPrices[-1] if buyPrices else -1
        return best_bid, best_ask
    
    def showPnL(self, state):
        trades = state.own_trades
        for t in trades.keys():
            if t not in self.pnl.keys():
                self.pnl[t] = {'time':set(), 'pnl':0}
            tradeLst = trades[t]
            timestamps = set()
            for tt in tradeLst:
                if tt.timestamp not in self.pnl[t]['time']:
                    self.pnl[t]['pnl'] += tt.price*tt.quantity if tt.seller == "SUBMISSION" else -1*tt.price*tt.quantity
                    timestamps.add(tt.timestamp)
            self.pnl[t]['time'] = self.pnl[t]['time'].union(timestamps)

        for p in self.pnl.keys():
            print("Product {} earns a PnL of {} at timestamp {}".format(p, self.pnl[p]['pnl'], state.timestamp))
            bestBid, bestAsk = self.getBestBidAsk(state, p)
            if bestBid == -1:
                bestBid = bestAsk
            if bestAsk == -1:
                bestAsk = bestBid

            if p in state.position.keys() and state.position[p] != 0:
                print("Adjusted PnL for product {} is {}".format(p, self.pnl[p]['pnl'] + state.position[p]*(bestBid+bestAsk)/2 ))

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        print("My prev confirmed trades:======================================")
        print(state.own_trades)
        print("Prev market trades:~~~~~~~~~~~~~~~")
        print(state.market_trades)
        print("============================================================")
        printOrderBook(state.order_depths, specific=['PEARLS'])

        self.showPnL(state) # prints out pnl during each iteration

        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths.keys():
            # Check if the current product is the 'PEARLS' product, only then run the order logic
            # if product == 'PEARLS':
            #     self.pearlsStrat(state)
            #     print(self.curOrders)
            # elif product == "BANANA":
            #     self.bananaStrat(state)
            #     print(self.curOrders)
            if product == "BANANAS":
                self.bananaStrat(state)
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


    def bananaStrat(self, state):
        # theo is the theoretical price of pearls
        product = 'BANANAS'
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

        theo_price = 0
        if buys[buyPrices[-1]] >= 10:
            theo_price = (buyPrices[-1]*buys[buyPrices[-1]] + sellPrices[0]*abs(sells[sellPrices[0]]))/(buys[buyPrices[-1]] + abs(sells[sellPrices[0]]))
        elif len(buyPrices) >= 2 and len(sellPrices) >= 2 and buys[buyPrices[-1]] + buys[buyPrices[-2]] >= 10:
            theo_price = (buyPrices[-1]*buys[buyPrices[-1]] + buyPrices[-2]*buys[buyPrices[-2]] + sellPrices[0]*abs(sells[sellPrices[0]]) + sellPrices[1]*abs(sells[sellPrices[1]]))/(buys[buyPrices[-1]] + buys[buyPrices[-2]] + abs(sells[sellPrices[0]]) + abs(sells[sellPrices[1]]))
        else:
            if len(buyPrices) > 2 and len(sellPrices) > 2:
                theo_price = (buyPrices[-1]*buys[buyPrices[-1]] + buyPrices[-2]*buys[buyPrices[-2]] + buyPrices[-3]*buys[buyPrices[-3]] + sellPrices[0]*abs(sells[sellPrices[0]]) + sellPrices[1]*abs(sells[sellPrices[1]]) + sellPrices[2]*abs(sells[sellPrices[2]]))/(buys[buyPrices[-1]] + buys[buyPrices[-2]] + buys[buyPrices[-3]] + abs(sells[sellPrices[0]]) + abs(sells[sellPrices[1]]) + abs(sells[sellPrices[2]]))
        
        new_bid_price = 0
        if theo_price == 0:
            new_bid_price = buyPrices[-1]
        else:
            new_bid_price = theo_price - 1
        
        new_ask_price = 0
        if theo_price == 0:
            new_ask_price = sellPrices[-1]
        else:
            new_ask_price = theo_price + 1

        myAsk_volume = self.ask_vol_dict[myPosition]
        if new_ask_price != 0 and myPosition >= -self.POSITION_LIMIT and myAsk_volume != 0:
            orders.append(Order(product, new_ask_price, myAsk_volume))
        
        myBid_volume = self.buy_vol_dict[myPosition]
        if new_bid_price != 0 and myPosition <= self.POSITION_LIMIT and myBid_volume != 0:
            orders.append(Order(product, new_bid_price, myBid_volume))
        
        if orders:
            self.curOrders[product] = orders
        