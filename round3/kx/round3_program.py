from typing import Dict, List, Any
from datamodel import *
import numpy as np
import pandas as pd
import math
import json

ME = "SUBMISSION"

class Logger:
    def __init__(self) -> None:
        self.logs = ""

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders) -> None:
        print(json.dumps({
            "state": state,
            "orders": orders,
            "logs": self.logs,
        }, cls=ProsperityEncoder, separators=(",", ":"), sort_keys=True))

        self.logs = ""

logger = Logger()


class Trader:
    prevSighting = 0
    limits = {"COCONUTS": 600, "PINA_COLADAS": 300, "BERRIES": 250, "DIVING_GEAR": 50, 'BAGUETTE':150, 'DIP':300, 'UKULELE':70, 'PICNIC_BASKET':70}
    building = []
    dropping = []
    shorting = []
    bbacking = []
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
        result = {}
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}
        self.curOrders = {} # Initialize the method output dict as an empty dict

        #self.showPnL2(state) # prints out pnl during each iteration

        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths.keys():
            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':

                self.pearlsStrat(state)
                #self.pearlBase(state) #base line strategy to test to see if pnl is printed correctly
                #print(self.curOrders)

            if product == 'BANANAS':
                self.bananaStrat(state)
            if product == 'BERRIES':
                self.berriesStrat(state)
            if product == 'DIVING_GEAR':
                self.DGstrat(state)
            if product == 'PICNIC_BASKET':
                self.PBstrat(state)

        self.pairCocoPinaStrat(state)
        
        logger.flush(state, self.curOrders)
        return self.curOrders
    def PBstrat(self, state):
        orders = []
        orders2 = []
        orders3 = []
        orders4 = []
        orders.append(Order('PICNIC_BASKET', 999999,10))
        orders2.append(Order('BAGUETTE', 999999,10))
        orders3.append(Order('DIP', 999999,10))
        orders4.append(Order('UKULELE', 999999,10))
        self.curOrders['PICNIC_BASKET'] = orders
        self.curOrders['BAGUETTE'] = orders2
        self.curOrders['DIP'] = orders3
        self.curOrders['UKULELE'] = orders4


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

                orders.append(Order(product, best_ask, -best_ask_volume))

        if len(order_depth.buy_orders) != 0:
            best_bid = max(order_depth.buy_orders.keys())
            best_bid_volume = order_depth.buy_orders[best_bid]
            if best_bid > acceptable_price:
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

        if self.bananaPrevP:
            bChange = theo-self.bananaPrevP
        else:
            bChange = 0
        self.bananaPrevP = theo

        bb_q = buys[best_bid]
        ba_q = -sells[best_ask]

        theo -= 0.05*myPosition-0.15*bChange



        if best_bid >= theo:
            for p in buyPrices[::-1]:
                # sell as much as possible above theo price
                if p < theo:
                    break
                sell_q = min(buys[p], limit + myPosition)
                if sell_q:
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
            return
        BerriesPosition = state.position.get(product, 0)
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
            self.berriesMM(state, limit = 250, product = 'BERRIES')
        if ((currenttime >115000 and currenttime<450000)and BerriesPosition <limit):
            buyquant = min(-sells[best_ask], limit - BerriesPosition)
            orders.append(Order(product, best_ask, buyquant))
            BerriesPosition += buyquant
            

            if len(sellPrices)>=2:
                ask2 = sellPrices[1]
                if ask2 == best_ask + 1 and BerriesPosition < limit:
                    buyquant2 = min(-sells[ask2], limit - BerriesPosition)
                    orders.append(Order(product, ask2, buyquant2))
                    BerriesPosition += buyquant2
                    if len(sellPrices)>=3:
                        ask3 = sellPrices[2]
                        if ask3 == best_ask + 2 and BerriesPosition < limit:
                            buyquant3 = min(-sells[ask3], limit - BerriesPosition)
                            orders.append(Order(product, ask3, buyquant3))
                            BerriesPosition += buyquant3
        if currenttime >497000 and BerriesPosition > -250:
            sellquant = min(buys[best_bid], limit + BerriesPosition)
            orders.append(Order(product, best_bid, -sellquant))
            BerriesPosition -= sellquant
            if len(buyPrices)>=2:
                bid2 = buyPrices[1]
                if bid2 == best_bid - 1 and BerriesPosition > -limit:
                    sellquant2 = min(buys[bid2], limit + BerriesPosition)
                    orders.append(Order(product, bid2, -sellquant2))
                    BerriesPosition -= sellquant2
                    if len(buyPrices)>=3:
                        bid3 = buyPrices[2]
                        if bid3 == best_bid - 2 and BerriesPosition > -limit:
                            sellquant3 = min(buys[bid3], limit + BerriesPosition)
                            orders.append(Order(product, bid3, -sellquant3))
                            BerriesPosition -= sellquant3

        if orders:
            self.curOrders[product] = orders
            

    def berriesMM (self, state, limit=250, product='BERRIES'):
        ordersberries: list[Order] = []
        order_depth: OrderDepth = state.order_depths.get(product, 0)

        if order_depth == 0:
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
        if self.berriesPrevP and (theo - self.berriesPrevP is not None):
            bChange = theo-self.berriesPrevP
        else:
            bChange = 0
        self.berriesPrevP = theo

        bb_q = buys[best_bid]
        ba_q = -sells[best_ask]
        if bChange is not None and myPosition is not None:
            theo -= 0.05*myPosition-0.15*bChange
        


        if best_bid >= theo:
            for p in buyPrices[::-1]:
                # sell as much as possible above theo price
                if p < theo:
                    break
                sell_q = min(buys[p], limit + myPosition)
                if sell_q:
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


        #assert edge2 = -15/8*edge1


        if abs(edge1) >= edgeMax:
            edge1 = np.sign(edge1)*edgeMax
        if abs(edge2) >= edgeMax2:
            edge2 = np.sign(edge2)*edgeMax2

        product1_percent = edge1/edgeMax #position percent we want to maintain at this time t
        product2_percent = edge2/edgeMax2

        cur1_percent = myPosition1/lim1 #my current position percent
        cur2_percent = myPosition2/lim2


        trade_percent1 = product1_percent-cur1_percent #max trade percent I'm willing to take
        trade_percent2 = product2_percent-cur2_percent


        #max trades I'm willing to do
        trade_q1 = int(trade_percent1*lim1)
        trade_q2 = int(trade_percent2*lim2)


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
        sightings = int(state.observations['DOLPHIN_SIGHTINGS'])
        delta = sightings - self.prevSighting

        if self.prevSighting != 0:
            if delta >= 3:
                self.building.append("DIVING_GEAR")
                if "DIVING_GEAR" in self.shorting:
                    self.shorting.remove("DIVING_GEAR")
            elif delta <= -3:
                self.shorting.append("DIVING_GEAR")
                if "DIVING_GEAR" in self.building:
                    self.building.remove("DIVING_GEAR")

        self.prevSighting = sightings
            
        if self.building != []:
            
            for i in self.building:
              amt = state.position.get(i, 0) 
              order_depth: OrderDepth = state.order_depths[i]
              best_ask = min(order_depth.sell_orders.keys())
              vol = self.limits[i]

              if amt < vol:
                  orders: list[Order] = []
                  orders.append(Order(i, best_ask, vol-amt))
                  self.curOrders[i] = orders
              else:
                  self.building.remove(i)


        if self.shorting != []:
            for i in self.shorting:
              amt = state.position.get(i, 0) 
              order_depth: OrderDepth = state.order_depths[i]
              best_ask = max(order_depth.buy_orders.keys())
              vol = self.limits[i]

              if amt > -vol:
                  orders: list[Order] = []
                  orders.append(Order(i, best_ask, -vol-amt))
                  self.curOrders[i] = orders
              else:
                  self.shorting.remove(i)

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
                    
                    orders.append(Order(product, p, buy_q))
                    myPosition += buy_q
                if myPosition >= limit:
                    self.productLim[product] += 1
                    break

            #p = best_ask-1
            #if p != best_bid and myPosition < limit:
            #    orders.append(Order(product, p, limit-myPosition))





        if orders:
            self.curOrders[product] = orders
        return


    def pearlsStrat(self, state, theo=10000, limit=20):
        # theo is the theoretical price of pearls
        product = 'PEARLS'
        orders: list[Order] = []
        order_depth: OrderDepth = state.order_depths.get(product, 0)

        if order_depth == 0:
            
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
