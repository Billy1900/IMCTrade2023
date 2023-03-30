from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order


ME = "SUBMISSION"


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

        self.timestamp = set()
        self.bananaSpread = {}
        self.bananaLim = 0
        self.pearlLim = 0
        self.bananaPrevP = 0
        self.start = self.start1 = self.cocoprice = self.cocobid = self.cocoask = self.pinaprice = 0
        self.cocoposition = self.pinaposition = 0
        self.cocoBP = self.cocoSP = self.pinaBP = self.pinaSP = []

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
        printOrderBook(state.order_depths, specific=['PEARLS', 'BANANAS'])


        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths.keys():

            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':
                print("PEARLL")
                self.pearlsStrat(state)
                #self.pearlBase(state) #base line strategy to test to see if pnl is printed correctly
                #print(self.curOrders)

            if product == 'BANANAS':

                print("BANANAA")
                #self.printBananaSpread(state)
                self.bananaStrat(state)

            if product == 'COCONUTS':
                print("COCONUTT")
                self.cocoStrat(state)

            if product == 'PINA_COLADAS':
                print("PINAA")
                self.pinaStrat(state)

        print(self.curOrders)
        print("&&&&&&&&&&&&&&&&&&&")
        print("The number of times bananas weren't able to be traded due to trade limit: {}".format(self.bananaLim))
        print("The number of times pearls weren't able to be traded due to trade limit: {}".format(self.pearlLim))
        return self.curOrders

    def printBananaSpread(self, state):
        b, a = self.getBestBidAsk(state, 'BANANAS')
        if b!=-1 and a!=-1:
            self.bananaSpread[a-b] = self.bananaSpread.get(a-b, 0) + 1
        else:
            self.bananaSpread['None'] = self.bananaSpread.get('None', 0) + 1
        print("Bananas spread data: +++++++++++++++++++++++++++++++++++++++++++++")
        print(self.bananaSpread)
        return

    def getBestBidAsk(self, state, product):
        order_depth: OrderDepth = state.order_depths.get(product, 0)
        sells = order_depth.sell_orders # asks
        buys = order_depth.buy_orders # bids
        sellPrices = sorted(list(sells.keys()))
        buyPrices = sorted(list(buys.keys()))
        best_ask = sellPrices[0] if sellPrices else -1
        best_bid = buyPrices[-1] if buyPrices else -1
        return best_bid, best_ask

    def pearlBase(self, state):
        product = 'PEARLS'
        order_depth: OrderDepth = state.order_depths[product]

        orders: list[Order] = []
        acceptable_price = 10000

        if len(order_depth.sell_orders) > 0:
            best_ask = min(order_depth.sell_orders.keys())
            best_ask_volume = order_depth.sell_orders[best_ask]
            if best_ask < acceptable_price:

                print("BUY", str(-best_ask_volume) + "x", best_ask)
                orders.append(Order(product, best_ask, -best_ask_volume))

        if len(order_depth.buy_orders) != 0:
            best_bid = max(order_depth.buy_orders.keys())
            best_bid_volume = order_depth.buy_orders[best_bid]
            if best_bid > acceptable_price:
                print("SELL", str(best_bid_volume) + "x", best_bid)
                orders.append(Order(product, best_bid, -best_bid_volume))

        if orders:
            self.curOrders[product] = orders
        return

    def bananaStrat(self, state, limit=20):
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
        best_ask = sellPrices[0] if sellPrices else -1
        best_bid = buyPrices[-1] if buyPrices else -1
        def tosum(D):
            # return the sum of the dot product of key value pairs in dictionary, and the sum of the values
            res, val = 0,0
            for x in D.keys():
                res += D[x]*x
                val += D[x]
            return res, val
        rb, vb = tosum(buys)
        rs, vs = tosum(sells)
        rs, vs = -rs, -vs
        theo = (rb+rs)/(vb+vs) #dynamic theo value
        bananaPrevP = theo
        print("Theo for banana before adjusting is {}".format(theo))
        if self.bananaPrevP:
            bChange = theo-self.bananaPrevP
        else:
            bChange = 0
        self.bananaPrevP = theo

        bb_q = buys[best_bid]
        ba_q = sells[best_ask]
        #theo -= 0.05*myPosition-0.15*bChange-0*(ba_q-bb_q)
        theo -= 0.05*myPosition-0.15*bChange
        print("Theo for banana after adjusting is {}".format(theo))

        if best_bid >= theo:
            for p in buyPrices[::-1]:
                # sell as much as possible above theo price
                if p < theo:
                    break
                sell_q = min(buys[p], limit + myPosition)
                if sell_q:
                    print("*******Selling {} for price: {} and quantity: {}".format(product, p, sell_q))
                    orders.append(Order(product, p, -sell_q))
                    myPosition -= sell_q
                if myPosition <= -limit:
                    self.bananaLim += 1
                    break
            p = best_bid+1
            if p != best_ask and myPosition > -limit:
                orders.append(Order(product, p, -limit-myPosition)) #keep probing
        elif best_ask <= theo:
            for p in sellPrices:
                # buy as much as possible below theo price
                if p > theo:
                    break
                buy_q = min(-sells[p], limit - myPosition)
                if buy_q:
                    print("*******Buying {} for price: {} and quantity: {}".format(product, p, buy_q))
                    orders.append(Order(product, p, buy_q))
                    myPosition += buy_q
                if myPosition >= limit:
                    self.bananaLim += 1
                    break
            p = best_ask-1
            if p != best_bid and myPosition < limit:
                orders.append(Order(product, p, limit-myPosition))
        elif best_bid < theo and best_ask > theo and best_bid != -1 and best_ask != -1:
            # money making portion
            print("Potential buy or sell submitted.")

            qbuy = limit-myPosition
            qsell = limit+myPosition
            d_bid = theo-best_bid
            d_ask = best_ask-theo
            if best_bid + 1 != best_ask - 1:
                orders.append(Order(product, best_bid+1, qbuy))
                if qbuy == 0:
                    self.bananaLim+=1
                orders.append(Order(product, best_ask-1, -qsell))
                if qsell==0:
                    self.bananaLim+=1
            else:
                if myPosition>0:
                    orders.append(Order(product, best_ask-1, -myPosition))
                elif myPosition<0:
                    orders.append(Order(product, best_bid+1, -myPosition))
        if orders:
            self.curOrders[product] = orders
        return

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
        theo -= 0.05*myPosition
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
                    self.pearlLim +=1
                    break

            p = best_bid+1
            if p != best_ask and myPosition > -limit:
                orders.append(Order(product, p, -limit-myPosition)) #keep probing
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
                    self.pearlLim +=1
                    break

            p = best_ask-1
            if p != best_bid and myPosition < limit:
                orders.append(Order(product, p, limit-myPosition))
        elif best_bid < theo and best_ask > theo and best_bid != -1 and best_ask != -1:
            # money making portion
            print("Potential buy or sell submitted.")

            qbuy = limit-myPosition
            qsell = limit+myPosition
            d_bid = theo-best_bid
            d_ask = best_ask-theo

            if best_bid + 1 != best_ask - 1:
                orders.append(Order(product, best_bid+1, qbuy))
                if qbuy==0:
                    self.pearlLim +=1
                orders.append(Order(product, best_ask-1, -qsell))
                if qsell==0:
                    self.pearlLim +=1
            else:
                if myPosition>0:
                    orders.append(Order(product, best_ask-1, -myPosition))
                elif myPosition<0:
                    orders.append(Order(product, best_bid+1, -myPosition))
                else:
                    orders.append(Order(product, best_bid+1, 5))
        if orders:
            self.curOrders[product] = orders
        return
    def cocoStrat(self, state, limit = 600): #only updates self variables for pinastrat to run with updated prices/positions
        product = 'COCONUTS'
        order_depth: OrderDepth = state.order_depths.get(product, 0)
        if order_depth == 0:
            print("Order book does not contain {}. cocoStrat strategy exiting".format(product))
            return
        self.cocoposition = state.position.get(product, 0)
        sells = order_depth.sell_orders # asks
        buys = order_depth.buy_orders # bids
        self.cocoSP = sorted(list(sells.keys()))
        self.cocoBP = sorted(list(buys.keys()))
        self.cocobid = self.cocoSP[0] if self.cocoSP else -1
        self.cocoask = self.cocoBP[-1] if self.cocoBP else -1
        self.cocoprice = (self.cocobid + self.cocoask)/2
    def pinaStrat(self, state, limit = 300):
        product = 'PINA_COLADAS'
        orders: list[Order] = []
        order_depth: OrderDepth = state.order_depths.get(product, 0)
        if order_depth == 0 or (self.cocoprice ==0 or self.cocoprice == -1):
            print("Order book does not contain {}. or no coco data. pinaStrat strategy exiting".format(product))
            return
        self.pinaposition = state.position.get(product, 0)
        sells = order_depth.sell_orders # asks
        buys = order_depth.buy_orders # bids
        self.pinaSP = sorted(list(sells.keys()))
        self.pinaBP = sorted(list(buys.keys()))
        best_ask = self.pinaSP[0] if self.pinaSP else -1
        print("pina best ask",best_ask)
        best_bid = self.pinaBP[-1] if self.pinaBP else -1
        print("pina best bid",best_bid)
        self.pinaprice = (best_ask + best_bid)/2
        cocoFV = (self.cocoprice+self.pinaprice*(8/15))/2
        print("cocoFV =", cocoFV)
        pinaFV = (self.pinaprice + self.cocoprice*(15/8))/2
        print("pinaFV =", pinaFV)
        cocoedge = self.cocoprice - cocoFV
        pinaedge = self.pinaprice - pinaFV
        print("pinaedge = ", pinaedge)
        if pinaedge > 8: # <=> cocoedge>8:
            print("pinaedge>15")
            sell_q = min(self.pinaBP[0], limit + self.pinaposition)
            if sell_q:
                print("*******Selling for price: {} and quantity: {}".format(p, sell_q))
                orders.append(Order(product, best_bid, -sell_q))
                orders.append(Order("COCONUTS", 999999, 2*sell_q))
                self.pinaposition -= sell_q
                self.cocoposition += sell_q * 2
            #if myPosition <= -limit:
            #    self.pearlLim +=1
            #   break
        if pinaedge < -8:
            buy_q = min(-self.pinaSP[0], limit - self.pinaposition)
            if buy_q:
                print("*******Selling for price: {} and quantity: {}".format(p, sell_q))
                orders.append(Order(product, best_ask, buy_q))
                orders.append(Order("COCONUTS", 1, -buy_q*2))
                self.pinaposition += buy_q
                self.cocoposition -= buy_q *2
        if orders:
            self.curOrders[product] = orders
            #if myPosition <= -limit:
            #    self.pearlLim +=1
            #   break
        
