import backtrader as bt
import itertools

# Create a Stratey
class VolumnPrice(bt.Strategy):
    params = (
        ('maperiod', 2),
        ('threshold', 2),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        
        self.datavolumn = self.datas[0].volume

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma =  bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)
        
        self.sma_volume = bt.indicators.MovingAverageSimple(self.data.volume, period=self.params.maperiod)
        
        # Indicators for the plotting show
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=self.params.maperiod)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=self.params.maperiod,
                                            subplot=True)
        bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0], plot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            # if self.dataclose[0] > self.sma[0] and self.datavolumn[0] > self.sma_volume[0]:
            if self.dataclose[0] > self.dataclose[-1] and any(all(self.sma[i] > self.sma[i-1] for i in indices) for indices in itertools.combinations(range(-1, -self.params.maperiod, -1), self.params.threshold)):
                if self.datavolumn[0] > self.datavolumn[-1] and any(all(self.datavolumn[i] > self.datavolumn[i-1] for i in indices) for indices in itertools.combinations(range(-1, -self.params.maperiod, -1), self.params.threshold)):
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    
                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:

             if len(self) >= (self.bar_executed + self.params.maperiod*2):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()





