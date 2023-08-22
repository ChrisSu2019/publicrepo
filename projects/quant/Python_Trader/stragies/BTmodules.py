import backtrader as bt
import itertools

class VWMA(bt.Indicator):
    lines = ('vwma',)
    params = (('period', 20),)
    
    def __init__(self):
        self.addminperiod(self.params.period)
        
    def next(self):
        price = self.data.close
        volume = self.data.volume
        self.lines.vwma = bt.indicators.WeightedMovingAverage(price, period=self.params.period, 
                                                             volume=volume)

class MovingAverage(bt.Indicator):
    lines = ('ma',)
    params = (('period', 5),)

    def __init__(self):
        self.lines.ma = bt.indicators.SMA(self.data, period=self.params.period)

class BuySignal(bt.Signal):
    params = (('period', 5),)

    def __init__(self):
        self.addindicator(MovingAverage, period=self.params.period)

    def next(self):

        # 5 days any 3 days up
         if any(all(self.data[i] > self.data[i-1] for i in indices) for indices in itertools.combinations(range(-1, -self.params.period, -1), 3)):
       # if self.data[0] > self.data[-1] and all(self.data[i] > self.data[i-1] for i in range(-1, -self.params.period, -1)):
            self.buy()