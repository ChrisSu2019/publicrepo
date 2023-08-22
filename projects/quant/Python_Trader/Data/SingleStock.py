import akshare as ak
import matplotlib.pyplot as plt
import pandas as pd
import funcLib as mylib

# write a function to get any stock data
def get_stock_data(symbol, adjust):
    stock_hfq_df = ak.stock_zh_a_hist(symbol=symbol, adjust=adjust).iloc[:, :]
    stock_hfq_df = mylib.get_english_column_names(stock_hfq_df)
    return stock_hfq_df




