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

        # First, we want to follow Olivia.
        # follow_olivia_signal = False
        for trades in state.market_trades:
            for trade in state.market_trades[trades]:
                if trade.buyer == "Olivia":
                    self.followOlivia(trade)
                    follow_olivia_signal = True
                
                if trade.seller == "Olivia":
                    self.followOlivia(trade)
                    follow_olivia_signal = True
        
        # if follow_olivia_signal:
        #     logger.flush(state, self.curOrders)
        #     return self.curOrders

        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths.keys():
            if product == 'PEARLS':
                self.pearlsStrat(state)
            if product == 'BANANAS':
                self.bananaStrat(state)
            if product == 'BERRIES':
                self.berriesStrat(state)
            if product == 'DIVING_GEAR':
                self.DGstrat(state)
            if product == 'PICNIC_BASKET':
                #self.PBstrat(state)
                self.picnicBasket(state)

        self.pairCocoPinaStrat(state)
        self.picnicBasket(state)
        
        logger.flush(state, self.curOrders)
        return self.curOrders
    
    def followOlivia(self, particular_trade):
        orders: list[Order] = []
        orders.append(Order(particular_trade.symbol, particular_trade.price, particular_trade.quantity))
        if orders:
            self.curOrders[particular_trade.symbol] = orders
    
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