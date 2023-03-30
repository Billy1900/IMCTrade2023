from datamodel import Listing, OrderDepth, Trade, TradingState
from ga_program import Trader

timestamp = 1000

listings = {
	"PRODUCT1": Listing(
		symbol="PEARLS",
		product="PRODUCT1",
		denomination= "SEASHELLS"
	),
	"PRODUCT2": Listing(
		symbol="BANANAS",
		product="PRODUCT2",
		denomination= "SEASHELLS"
	),
}

order_depths = {
	"PEARLS": OrderDepth(
		#buy_orders={9999:5, 10001: 7, 10002: 5},
		#sell_orders={10003: -4, 10004: -8}
        buy_orders={9992:5, 9998: 7, 9999: 5},
		sell_orders={10003: -4, 10002:-2}
	),
	"BANANAS": OrderDepth(
		buy_orders={142: 3, 141: 5},
		sell_orders={144: -5, 145: -8}
	),
}

own_trades = {
	"PEARLS": [],
	"BANANAS": []
}

market_trades = {
	"PEARLS": [
		Trade(
			symbol="PEARLS",
			price=10000,
			quantity=4,
			buyer="",
			seller="",
			timestamp=900
		)
	],
	"BANANAS": []
}

position = {
	"PEARLS": 0,
	"BANANAS": -5
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

t = Trader()
t.run(state)
