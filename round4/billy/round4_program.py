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
        self.bananaPrevP = self.berriesPrevP= 0
        self.PrevP = {}
        self.productLim = {}
        self.berriesLim = 0
        self.dolphin = self.dolphinsignal= self.tradetime = 0

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
            print(state.timestamp)
            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':
                self.pearlsStrat(state)
                #self.pearlBase(state) #base line strategy to test to see if pnl is printed correctly
                #print(self.curOrders)
            if product == 'BANANAS':
                #self.printBananaSpread(state)
                self.bananaStrat(state)
            if product == 'BERRIES':
                self.berriesStrat(state)
            if product == 'DIVING_GEAR':
                self.DGstrat(state)
        self.pairCocoPinaStrat(state)
        self.picnicBasket(state)

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

    def berriesStrat(self, state, limit=250, product='BERRIES'):
    #market-making before 100k, then buying more aggressively, market taking if position not full by 115k. at 495k, selling to best 2 bid, until -650 pos.
        orders: list[Order] = []
        order_depth: OrderDepth = state.order_depths.get(product, 0)
        if order_depth == 0:
            print("Order book does not contain {}. PearlStrat strategy exiting".format(product))
            return
        BerriesPosition = state.position.get(product, 0)
        print('initial BerriesPos =',BerriesPosition)
        if BerriesPosition is None:
            BerriesPosition = 0
        sells       = order_depth.sell_orders # asks
        buys        = order_depth.buy_orders # bids
        sellPrices  = sorted(list(sells.keys()))
        buyPrices   = sorted(list(buys.keys()))
        best_ask    = sellPrices[0] if sellPrices else -1
        best_bid    = buyPrices[-1] if buyPrices else -1
        currenttime = state.timestamp 

        if currenttime <= 115000:
            print('phase1')
            self.berriesMM(state, limit = 250, product = 'BERRIES')
        if ((currenttime >115000 and currenttime<450000)and BerriesPosition <limit):
            print('phase2')
            buyquant = min(-sells[best_ask], limit - BerriesPosition)
            print('sellsbestask (should be volume of bid1=', -sells[best_ask])
            print(BerriesPosition)
            orders.append(Order(product, best_ask, buyquant))
            print('bought', buyquant, 'berries @', best_ask)
            BerriesPosition += buyquant
            

            if len(sellPrices)>=2:
                ask2 = sellPrices[1]
                if ask2 == best_ask + 1 and BerriesPosition < limit:
                    buyquant2 = min(-sells[ask2], limit - BerriesPosition)
                    orders.append(Order(product, ask2, buyquant2))
                    print('bought',buyquant2, 'berries @', ask2)
                    BerriesPosition += buyquant2
                    if len(sellPrices)>=3:
                        ask3 = sellPrices[2]
                        if ask3 == best_ask + 2 and BerriesPosition < limit:
                            buyquant3 = min(-sells[ask3], limit - BerriesPosition)
                            orders.append(Order(product, ask3, buyquant3))
                            print('bought',buyquant3, 'berries @', ask3)
                            BerriesPosition += buyquant3
        if BerriesPosition == limit:
            print('berries stock is full 250/250!')
        if currenttime >497000 and BerriesPosition > -250:
            print('phase3')
            sellquant = min(buys[best_bid], limit + BerriesPosition)
            orders.append(Order(product, best_bid, -sellquant))
            print('sold',sellquant, 'berries @', best_bid)
            BerriesPosition -= sellquant
            if len(buyPrices)>=2:
                bid2 = buyPrices[1]
                if bid2 == best_bid - 1 and BerriesPosition > -limit:
                    sellquant2 = min(buys[bid2], limit + BerriesPosition)
                    orders.append(Order(product, bid2, -sellquant2))
                    print('sold',sellquant2, 'berries @', bid2)
                    BerriesPosition -= sellquant2
                    if len(buyPrices)>=3:
                        bid3 = buyPrices[2]
                        if bid3 == best_bid - 2 and BerriesPosition > -limit:
                            sellquant3 = min(buys[bid3], limit + BerriesPosition)
                            orders.append(Order(product, bid3, -sellquant3))
                            print('sold',sellquant3, 'berries @', bid3)
                            BerriesPosition -= sellquant3
        if BerriesPosition  == -limit:
            print('short berries stock is full -250/-250!')
        print('BERRIES = ', state.position.get(product, 0))
        if orders:
            self.curOrders[product] = orders
            

    def berriesMM (self, state, limit=250, product='BERRIES'):
        ordersberries: list[Order] = []
        order_depth: OrderDepth = state.order_depths.get(product, 0)

        if order_depth == 0:
            print("Order book does not contain {}. PearlStrat strategy exiting".format(product))
            return
        myPosition = state.position.get(product)
        if myPosition is None:
            myPosition = 0
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

        berriesPrevP = theo

        print("Theo for mayberries before adjusting is {}".format(theo))
        if self.berriesPrevP and (theo - self.berriesPrevP is not None):
            bChange = theo-self.berriesPrevP
        else:
            bChange = 0
        self.berriesPrevP = theo

        bb_q = buys[best_bid]
        ba_q = -sells[best_ask]
        if bChange is not None and myPosition is not None:
            theo -= 0.05*myPosition-0.15*bChange
        


        print("Theo for berries after adjusting is {}".format(theo))

        if best_bid >= theo:
            for p in buyPrices[::-1]:
                # sell as much as possible above theo price
                if p < theo:
                    break
                sell_q = min(buys[p], limit + myPosition)
                if sell_q:
                    print("*******Selling {} for price: {} and quantity: {}".format(product, p, sell_q))
                    ordersberries.append(Order(product, p, -sell_q))
                    myPosition -= sell_q
                if myPosition <= -limit:
                    self.berriesLim += 1
                    break

            p = best_bid+1
            if p != best_ask and myPosition > -limit:
                ordersberries.append(Order(product, p, -limit-myPosition)) #keep probing

        elif best_ask <= theo:
            for p in sellPrices:
                # buy as much as possible below theo price
                if p > theo:
                    break
                buy_q = min(-sells[p], limit - myPosition)
                if buy_q:
                    print("*******Buying {} for price: {} and quantity: {}".format(product, p, buy_q))
                    ordersberries.append(Order(product, p, buy_q))
                    myPosition += buy_q
                if myPosition >= limit:
                    self.berriesLim += 1
                    break

            p = best_ask-1
            if p != best_bid and myPosition < limit:
                ordersberries.append(Order(product, p, limit-myPosition))



        elif best_bid < theo and best_ask > theo and best_bid != -1 and best_ask != -1:
            # money making portion
            print("Potential buy or sell submitted.")

            qbuy = limit-myPosition
            qsell = limit+myPosition
            d_bid = theo-best_bid
            d_ask = best_ask-theo

            if best_bid + 1 != best_ask - 1:
                ordersberries.append(Order(product, best_bid+1, qbuy))
                if qbuy == 0:
                    self.berriesLim+=1
                ordersberries.append(Order(product, best_ask-1, -qsell))
                if qsell==0:
                    self.berriesLim+=1
            else:
                if myPosition>0:
                    ordersberries.append(Order(product, best_ask-1, -myPosition))
                elif myPosition<0:
                    ordersberries.append(Order(product, best_bid+1, -myPosition))

        if ordersberries:
            self.curOrders[product] = ordersberries
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

    def DGstrat(self, state, limit = 50):
        orders: list[Order] = []
        order_depth: OrderDepth = state.order_depths.get('DIVING_GEAR', 0)
        if order_depth == 0:
            return
        myPosition = state.position.get('DIVING_GEAR', 0)
        if myPosition is None:
            myPosition = 0
        sells       = order_depth.sell_orders # asks
        buys        = order_depth.buy_orders # bids
        sellPrices  = sorted(list(sells.keys()))
        buyPrices   = sorted(list(buys.keys()))
        best_ask    = sellPrices[0] if sellPrices else -1
        best_bid    = buyPrices[-1] if buyPrices else -1
        self.tradetime = state.timestamp
        DS = state.observations['DOLPHIN_SIGHTINGS'] 
        if self.dolphin == 0:
            self.dolphin = state.observations['DOLPHIN_SIGHTINGS']
        if DS - self.dolphin <10:
            self.dolphin = DS
        if (DS - self.dolphin >10 or self.dolphinsignal == "buy"):
            if myPosition < limit:
                orders.append(Order('DIVING_GEAR', best_ask + 2, limit - myPosition))
                self.dolphinsignal = "buy"
            if myPosition == limit:
                self.dolphinsignal = "fully long"
                self.tradetime = state.timestamp
        if (DS - self.dolphin <10 or self.dolphinsignal == "sell"):
            if myPosition > - limit:
                orders.append(Order('DIVING_GEAR', best_bid -2, limit + myPosition))
                self.dolphinsignal = "sell"
            if myPosition == - limit:
                self.dolphinsignal = "fully short"
                self.tradetime = state.timestamp
        if self.dolphinsignal == "fully short" or self.dolphinsignal =="fully long":
            if state.timestamp - self.tradetime >= 95000 and myPosition !=0:
                orders.append(Order('DIVING_GEAR', (best_bid + best_ask)/2, -myPosition))
            if myPosition == 0:
                self.dolphinsignal = 0
        if orders:
            self.curOrders['DIVING_GEAR'] = orders
        return

    def PNstrat(self,state):
        orders: list[Order] = []
        order_depth: OrderDepth = state.order_depths.get('PICNIC_BASKET', 0)
        order_depth1: OrderDepth = state.order_depths.get('BAGUETTE', 0)
        order_depth2: OrderDepth = state.order_depths.get('DIP', 0)
        order_depth3: OrderDepth = state.order_depths.get('UKULELE', 0)
        if order_depth == 0 or order_depth1 ==0 or order_depth2 ==0 or order_depth3 ==0 :
            return
        myPosition = state.position.get('PICNIC_BASKET', 0)
        myPosition1 = state.position.get('BAGUETTE', 0)
        myPosition2 = state.position.get('DIP', 0)
        myPosition3 = state.position.get('UKULELE', 0)
        if myPosition is None:
            myPosition = 0
        sells       = order_depth.sell_orders # asks
        buys        = order_depth.buy_orders # bids
        sellPrices  = sorted(list(sells.keys()))
        buyPrices   = sorted(list(buys.keys()))
        best_ask    = sellPrices[0] if sellPrices else -1
        best_bid    = buyPrices[-1] if buyPrices else -1
        self.tradetime = state.timestamp
        DS = state.observations['DOLPHIN_SIGHTINGS'] 


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


    def picnicBasket(self, state):
        edge_max = 400 # refer to analysis.ipynb

        b_limit = 150
        d_limit = 300
        u_limit = 70
        pb_limit = 70

        product_d = "DIP"
        product_b = "BAGUETTE"
        product_u = "UKULELE"
        product_pb = "PICNIC_BASKET"

        orders_d: list[Order] = []
        orders_b: list[Order] = []
        orders_u: list[Order] = []
        orders_pb: list[Order] = []
        order_depth_d = state.order_depths.get(product_d, 0)
        order_depth_b = state.order_depths.get(product_b, 0)
        order_depth_u = state.order_depths.get(product_u, 0)
        order_depth_pb = state.order_depths.get(product_pb, 0)

        if order_depth_d == 0 or order_depth_b == 0 or order_depth_u == 0 or order_depth_pb == 0:
            print("Failed to extract PICNIC etc. data in the pair strategy")
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

        myPosition_d = state.position.get(product_d, 0)
        sells_d = order_depth_d.sell_orders # asks
        buys_d = order_depth_d.buy_orders # bids
        sellPrices_d = sorted(list(sells_d.keys()))
        buyPrices_d = sorted(list(buys_d.keys()))
        best_ask_d = sellPrices_d[0] if sellPrices_d else -1
        best_bid_d = buyPrices_d[-1] if buyPrices_d else -1

        myPosition_b = state.position.get(product_b, 0)
        sells_b = order_depth_b.sell_orders # asks
        buys_b = order_depth_b.buy_orders # bids
        sellPrices_b = sorted(list(sells_b.keys()))
        buyPrices_b = sorted(list(buys_b.keys()))
        best_ask_b = sellPrices_b[0] if sellPrices_b else -1
        best_bid_b = buyPrices_b[-1] if buyPrices_b else -1

        myPosition_u = state.position.get(product_u, 0)
        sells_u = order_depth_u.sell_orders # asks
        buys_u = order_depth_u.buy_orders # bids
        sellPrices_u = sorted(list(sells_u.keys()))
        buyPrices_u = sorted(list(buys_u.keys()))
        best_ask_u = sellPrices_u[0] if sellPrices_u else -1
        best_bid_u = buyPrices_u[-1] if buyPrices_u else -1

        myPosition_pb = state.position.get(product_pb, 0)
        sells_pb = order_depth_pb.sell_orders # asks
        buys_pb = order_depth_pb.buy_orders # bids
        sellPrices_pb = sorted(list(sells_pb.keys()))
        buyPrices_pb = sorted(list(buys_pb.keys()))
        best_ask_pb = sellPrices_pb[0] if sellPrices_pb else -1
        best_bid_pb = buyPrices_pb[-1] if buyPrices_pb else -1

        midPrice_b = getMidPrice(buys_b, sells_b)
        midPrice_d = getMidPrice(buys_d, sells_d)
        midPrice_u = getMidPrice(buys_u, sells_u)
        midPrice_pb = getMidPrice(buys_pb, sells_pb)

        edge = midPrice_pb - midPrice_d*4 - midPrice_b*2 - midPrice_u - 400
        print("edge is ", edge)
        if abs(edge) > edge_max:
            edge = np.sign(edge)*edge_max
        
        all_product_percent = edge/edge_max # product_pb_percent

        cur_d_precent = myPosition_d/d_limit
        cur_b_precent = myPosition_b/b_limit
        cur_u_precent = myPosition_u/u_limit
        cur_pb_precent = myPosition_pb/pb_limit

        product_d_percent = all_product_percent * 4/7
        product_b_percent = all_product_percent * 2/7
        product_u_percent = all_product_percent * 1/7

        trade_d_percent = product_d_percent - cur_d_precent
        trade_b_percent = product_b_percent - cur_b_precent
        trade_u_percent = product_u_percent - cur_u_precent
        trade_pb_percent = all_product_percent - cur_pb_precent

        trade_d = int(trade_d_percent*d_limit)
        trade_b = int(trade_b_percent*b_limit)
        trade_u = int(trade_u_percent*u_limit)
        trade_pb = int(trade_pb_percent*pb_limit)

        if trade_d > 0:
            p = best_ask_d
            q = trade_d
            while p in sells_d.keys() and q > 0:
                qq = min(q, -sells_d[p])
                orders_d.append(Order(product_d, p, qq))
                q -= qq
                p += 1
        elif trade_d < 0:
            p = best_bid_d
            q = trade_d
            while p in buys_d.keys() and q < 0:
                qq = max(q, -buys_d[p])
                orders_d.append(Order(product_d, p, qq))
                q += qq
                p -= 1

        if trade_b > 0:
            p = best_ask_b
            q = trade_b
            while p in sells_b.keys() and q > 0:
                qq = min(q, -sells_b[p])
                orders_b.append(Order(product_b, p, qq))
                q -= qq
                p += 1
        elif trade_b < 0:
            p = best_bid_b
            q = trade_b
            while p in buys_b.keys() and q < 0:
                qq = max(q, -buys_b[p])
                orders_b.append(Order(product_b, p, qq))
                q += qq
                p -= 1
        
        if trade_u > 0:
            p = best_ask_u
            q = trade_u
            while p in sells_u.keys() and q > 0:
                qq = min(q, -sells_u[p])
                orders_u.append(Order(product_u, p, qq))
                q -= qq
                p += 1
        elif trade_u < 0:
            p = best_bid_u
            q = trade_u
            while p in buys_u.keys() and q < 0:
                qq = max(q, -buys_u[p])
                orders_u.append(Order(product_u, p, qq))
                q += qq
                p -= 1
        
        if trade_pb > 0:
            p = best_ask_pb
            q = trade_pb
            while p in sells_pb.keys() and q > 0:
                qq = min(q, -sells_pb[p])
                orders_pb.append(Order(product_pb, p, qq))
                q -= qq
                p += 1
        elif trade_pb < 0:
            p = best_bid_pb
            q = trade_pb
            while p in buys_pb.keys() and q < 0:
                qq = max(q, -buys_pb[p])
                orders_pb.append(Order(product_pb, p, qq))
                q += qq
                p -= 1

        if orders_d:
            self.curOrders[product_d] = orders_d
        if orders_b:
            self.curOrders[product_b] = orders_b
        if orders_u:
            self.curOrders[product_u] = orders_u
        if orders_b:
            self.curOrders[product_pb] = orders_pb
        return