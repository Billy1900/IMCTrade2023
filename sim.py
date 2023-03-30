from datamodel import Listing, OrderDepth, Trade, TradingState
from program import Trader

timestamp = 1000

listings = {
	"PRODUCT1": Listing(
		symbol="PEARLS",
		product="PRODUCT1",
		denomination= "SEASHELLS"
	),
	"PRODUCT2": Listing(
		symbol="PRODUCT2",
		product="PRODUCT2",
		denomination= "SEASHELLS"
	),
}

order_depths = {
	"PEARLS": OrderDepth(
		#buy_orders={9999:5, 10001: 7, 10002: 5},
		#sell_orders={10003: -4, 10004: -8}
        buy_orders={9992:5, 9998: 7, 9999: 5},
		sell_orders={10003: -4, 10001:-2}
	),
	"PRODUCT2": OrderDepth(
		buy_orders={142: 3, 141: 5},
		sell_orders={144: -5, 145: -8}
	),
}

own_trades = {
	"PEARLS": [Trade(
		symbol="PEARLS",
		price=10001,
		quantity=4,
		buyer="",
		seller="SUBMISSION",
		timestamp=900
	), Trade(
		symbol="PEARLS",
		price=9999,
		quantity=4,
		buyer="SUBMISSION",
		seller="",
		timestamp=900
	), Trade(
		symbol="PEARLS",
		price=9998,
		quantity=2,
		buyer="SUBMISSION",
		seller="",
		timestamp=800
	)],
	"PRODUCT2": []
}

own_trades2 = {
	"PEARLS": [Trade(
		symbol="PEARLS",
		price=10001,
		quantity=4,
		buyer="",
		seller="SUBMISSION",
		timestamp=900
	), Trade(
		symbol="PEARLS",
		price=9999,
		quantity=4,
		buyer="SUBMISSION",
		seller="",
		timestamp=900
	), Trade(
		symbol="PEARLS",
		price=9998,
		quantity=2,
		buyer="SUBMISSION",
		seller="",
		timestamp=800
	)],
	"PRODUCT2": []
}

market_trades = {
	"PEARLS": [
		Trade(
			symbol="PEARLS",
			price=10000,
			quantity=4,
			buyer="xxx",
			seller="yyy",
			timestamp=900
		)
	],
	"PRODUCT2": [
		Trade(
			symbol="PEARLS",
			price=10000,
			quantity=4,
			buyer="aaa",
			seller="bbb",
			timestamp=900
		)
	]
}

position = {
	"PEARLS": 2,
	"PRODUCT2": 0
}

observations = {}

state = TradingState(
    timestamp=timestamp,
    listings=listings,
	order_depths=order_depths,
    own_trades=own_trades,
    market_trades=market_trades,
    position=position,
    observations=observations

)
state2 = TradingState(
    timestamp=timestamp,
    listings=listings,
	order_depths=order_depths,
    own_trades=own_trades2,
    market_trades=market_trades,
    position=position,
    observations=observations

)
# t = Trader()
# t.run(state)
# t.run(state2)
for trades in state2.market_trades:
    # print(trades)
    # print(state2.market_trades[trades])
    # print(state2.market_trades[trades][0].buyer)
    for trade in state2.market_trades[trades]:
        print(trade.buyer)
            