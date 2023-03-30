from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import numpy as np

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
        self.pnl = {} #{product:{time:set, pnl:int}}
        self.timestamp = set()
        self.bananaSpread = {}
        self.bananaLim = 0
        self.pearlLim = 0
        self.bananaPrevP = 0
        self.PrevP = {}
        self.productLim = {}


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

        #self.showPnL2(state) # prints out pnl during each iteration

        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths.keys():

            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':

                self.pearlsStrat(state)
                #self.pearlBase(state) #base line strategy to test to see if pnl is printed correctly
                #print(self.curOrders)

            if product == 'BANANAS':
                #self.printBananaSpread(state)
                self.bananaStrat(state)

            #if product == 'COCONUTS':
            #    self.coconutStrat(state)

            #if product == 'PINA_COLADAS':
            #    self.pinaStrat(state)
        self.pairCocoPinaStrat(state)

        print(self.curOrders)
        print("&&&&&&&&&&&&&&&&&&&")
        print("The number of times bananas weren't able to be traded due to trade limit: {}".format(self.bananaLim))
        print("The number of times pearls weren't able to be traded due to trade limit: {}".format(self.pearlLim))
        for k in self.productLim.keys():
            print("The number of times {} weren't able to be traded due to trade limit: {}".format(k, self.productLim[k]))

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

    def showPnL(self, state):
        trades = state.own_trades
        for t in trades.keys():
            if t not in self.pnl.keys():
                self.pnl[t] = {'time':set(), 'pnl':0}
            tradeLst = trades[t]
            timestamps = set()
            for tt in tradeLst:
                if tt.timestamp not in self.pnl[t]['time']:
                    print("timestamp: {} not in {} list".format(tt.timestamp, t))
                    self.pnl[t]['pnl'] += tt.price*tt.quantity if tt.seller == ME else -1*tt.price*tt.quantity
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

    def showPnL2(self, state):
        trades = state.own_trades
        for t in trades.keys():
            if t not in self.pnl.keys():
                self.pnl[t] = {'time':set(), 'pnl':0}
            tradeLst = trades[t]

            ts = None
            for tt in tradeLst:

                if tt.timestamp not in self.pnl[t]['time']:
                    print("timestamp: {} not in {} list".format(tt.timestamp, t))
                    self.pnl[t]['pnl'] += tt.price*tt.quantity if tt.seller == ME else -1*tt.price*tt.quantity
                    ts = tt.timestamp
            if ts:
                self.pnl[t]['time'].add(ts)

        for p in self.pnl.keys():
            print("Product {} earns a PnL of {} at timestamp {}".format(p, self.pnl[p]['pnl'], state.timestamp))
            bestBid, bestAsk = self.getBestBidAsk(state, p)
            if bestBid == -1:
                bestBid = bestAsk
            if bestAsk == -1:
                bestAsk = bestBid

            if p in state.position.keys() and state.position[p] != 0:
                print("my position on {} is {}".format(p, state.position[p]))
                print("Adjusted PnL for product {} is {}".format(p, self.pnl[p]['pnl'] + state.position[p]*(bestBid+bestAsk)/2 ))

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

    def coconutStrat(self, state, limit=600, product='COCONUTS'):
        self.dynamicTheoStrat(state, limit, product)

    def pinaStrat(self, state, limit=300, product='PINA_COLADAS'):
        self.dynamicTheoStrat(state, limit, product)

    def bananaStrat(self, state, limit=20, product='BANANAS'):

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
        ba_q = -sells[best_ask]

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

    def pairCocoPinaStrat(self, state, edgeMax=20):
        #edgeMax is the max edge for product1: coconuts
        edgeMax2 = edgeMax*15/8

        lim1 = 600 #lim for coco
        lim2 = 300 #lim for pina

        product1 = 'COCONUTS'
        product2 = 'PINA_COLADAS'

        orders1: list[Order] = []
        orders2: list[Order] = []
        order_depth1 = state.order_depths.get(product1, 0)
        order_depth2 = state.order_depths.get(product2, 0)

        if order_depth1 == 0 or order_depth2 == 0:
            print("Failed to extract either pina or coco price data in the pair strategy")
            return

        def tosum(D):
            # return the sum of the dot product of key value pairs in dictionary, and the sum of the values
            res, val = 0,0
            for x in D.keys():
                res += D[x]*x
                val += D[x]
            return res, val

        def getMidPrice(buys, sells):
            rb, vb = tosum(buys)
            rs, vs = tosum(sells)
            rs, vs = -rs, -vs
            return (rb+rs)/(vb+vs) #mid price

        myPosition1 = state.position.get(product1, 0)
        sells1 = order_depth1.sell_orders # asks
        buys1 = order_depth1.buy_orders # bids
        sellPrices1 = sorted(list(sells1.keys()))
        buyPrices1 = sorted(list(buys1.keys()))
        best_ask1 = sellPrices1[0] if sellPrices1 else -1
        best_bid1 = buyPrices1[-1] if buyPrices1 else -1

        myPosition2 = state.position.get(product2, 0)
        sells2 = order_depth2.sell_orders # asks
        buys2 = order_depth2.buy_orders # bids
        sellPrices2 = sorted(list(sells2.keys()))
        buyPrices2 = sorted(list(buys2.keys()))
        best_ask2 = sellPrices2[0] if sellPrices2 else -1
        best_bid2 = buyPrices2[-1] if buyPrices2 else -1

        midPrice1 = getMidPrice(buys1, sells1)
        midPrice2 = getMidPrice(buys2, sells2)

        theo1 = (midPrice1+midPrice2*8/15)/2
        theo2 = (midPrice1*15/8+midPrice2)/2

        edge1 = theo1-midPrice1
        edge2 = theo2-midPrice2

        print('edge1 is {}'.format(edge1))
        print('edge2 is {}'.format(edge2))

        #assert edge2 = -15/8*edge1


        if abs(edge1) >= edgeMax:
            edge1 = np.sign(edge1)*edgeMax
        if abs(edge2) >= edgeMax2:
            edge2 = np.sign(edge2)*edgeMax2

        product1_percent = edge1/edgeMax #position percent we want to maintain at this time t
        product2_percent = edge2/edgeMax2
        print("Want to maintain Product1 percent 1: {}".format(product1_percent))
        print("Want to maintain product2_percent: {}".format(product2_percent))

        cur1_percent = myPosition1/lim1 #my current position percent
        cur2_percent = myPosition2/lim2


        trade_percent1 = product1_percent-cur1_percent #max trade percent I'm willing to take
        trade_percent2 = product2_percent-cur2_percent

        print("Willing to Trade percent 1: {}".format(trade_percent1))
        print("Willing to Trade percent 2: {}".format(trade_percent2))

        #max trades I'm willing to do
        trade_q1 = int(trade_percent1*lim1)
        trade_q2 = int(trade_percent2*lim2)
        print("Willing to Trade num 1: {}".format(trade_q1))
        print("Willing to Trade num 2: {}".format(trade_q2))


        if trade_q1 > 0:
            p = best_ask1
            q = trade_q1
            while p in sells1.keys() and p <= theo1 and q > 0:
                qq = min(q, -sells1[p])
                orders1.append(Order(product1, p, qq))
                q -= qq
                p += 1
        elif trade_q1 < 0:
            p = best_bid1
            q = trade_q1
            while p in buys1.keys() and p >= theo1 and q < 0:
                qq = max(q, -buys1[p])
                orders1.append(Order(product1, p, qq))
                q += qq
                p -= 1

        if trade_q2 > 0:
            p = best_ask2
            q = trade_q2
            while p in sells2.keys() and p <= theo2 and q > 0:
                qq = min(q, -sells2[p])
                orders2.append(Order(product2, p, qq))
                q -= qq
                p += 1
        elif trade_q2 < 0:
            p = best_bid2
            q = trade_q2
            while p in buys2.keys() and p >= theo2 and q < 0:
                qq = max(q, -buys2[p])
                orders2.append(Order(product2, p, qq))
                q += qq
                p -= 1








        if orders1:
            self.curOrders[product1] = orders1
        if orders2:
            self.curOrders[product2] = orders2
        return




    def dynamicTheoStrat(self, state, limit=20, product='BANANAS'):

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



        print("Theo for {}before adjusting is {}".format(product, theo))
        if product not in self.PrevP.keys():
            self.PrevP[product] = 0
        if product not in self.productLim.keys():
            self.productLim[product] = 0

        if self.PrevP[product]:
            bChange = theo-self.PrevP[product]
        else:
            bChange = 0
        self.PrevP[product] = theo

        bb_q = buys[best_bid]
        ba_q = sells[best_ask]

        #theo -= 0.05*myPosition-0.15*bChange-0*(ba_q-bb_q)
        #theo -= 0.05*myPosition-0.15*bChange
        #print("Theo for banana after adjusting is {}".format(theo))

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
                    self.productLim[product] += 1
                    break

            #p = best_bid+1
            #if p != best_ask and myPosition > -limit:
            #    orders.append(Order(product, p, -limit-myPosition)) #keep probing




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
                    self.productLim[product] += 1
                    break

            #p = best_ask-1
            #if p != best_bid and myPosition < limit:
            #    orders.append(Order(product, p, limit-myPosition))


        """
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
                    self.productLim[product] += 1
                orders.append(Order(product, best_ask-1, -qsell))
                if qsell==0:
                    self.productLim[product] += 1
            else:
                if myPosition>0:
                    orders.append(Order(product, best_ask-1, -myPosition))
                elif myPosition<0:
                    orders.append(Order(product, best_bid+1, -myPosition))"""





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
