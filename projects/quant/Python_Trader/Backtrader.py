from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from ast import Import
from datetime import datetime
import warnings

from Data.funcLib import get_english_column_names, load_excel_data
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.dates")
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import backtrader as bt
import pandas as pd
import itertools

from stragies.ThreeLowerCloses import ThreeLowerCloses
from stragies.SimpleMovingAverage import *
from stragies.VolumnPrice import VolumnPrice


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(VolumnPrice, maperiod = 5)
    #cerebro.addstrategy(ThreeLowerCloses, exitbars = 7)
    
    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath("D:\repos\backtrader\datas"))
    datapath = os.path.join("D:/repos/backtrader/datas", 'orcl-1995-2014.txt')

    # Create a Data Feed
    #data = bt.feeds.YahooFinanceCSVData(
    #    dataname=datapath,
    #    # Do not pass values before this date
    #    fromdate=datetime.datetime(2000, 1, 1),
    #    # Do not pass values before this date
    #    todate=datetime.datetime(2000, 12, 31),
    #    # Do not pass values after this date
    #    reverse=False)

    # Pandas data source for excel
    dataframe =  load_excel_data('D:/repos/quant/Python_Trader', '000001')
    start_date = datetime(2022, 1, 10)  # 回测开始时间
    end_date = datetime(2023,1, 10)  # 回测结束时间
    data = bt.feeds.PandasData(dataname=dataframe, fromdate=start_date, todate=end_date)  # 规范化数据格式

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Add a FixedSize sizer according to the stake
    # cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    cerebro.addsizer(bt.sizers.AllInSizerInt)
    
    # 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.dates")

    cerebro.plot()



