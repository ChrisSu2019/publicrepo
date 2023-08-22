import akshare as ak
import matplotlib.pyplot as plt
import pandas as pd
import MyModules as mylib

print("hello world, let's start to trade with python")

# This line of code is using the ak.stock_zh_a_hist function from the ak library
# to retrieve historical stock data for the company with the symbol "000001".
# The data is being adjusted using the "hfq" method,
# which is a method used in the Chinese stock market to adjust prices for corporate actions such as stock splits and dividends.
# The resulting data is stored in a pandas dataframe called stock_hfq_df.
#
# The .iloc method is part of the pandas library and is used for indexing and selecting data in a pandas DataFrame.
# The .iloc method is then used to select the first 6 columns of the dataframe.
stock_hfq_df = ak.stock_zh_a_hist(symbol="000001", adjust="hfq").iloc[:, :]


# rename all the column to match english input
stock_hfq_df = mylib.get_english_column_names(stock_hfq_df)


# The .head() method is part of the pandas library and is used to display the first 5 rows of a pandas DataFrame.
print(stock_hfq_df.head())


# The code does not draw a chart because the .plot method is not used to display the chart.
# It only generates the chart data and saves it to a file or to memory. To actually display the chart,
# you need to call a plotting library like matplotlib, seaborn, or plotly.
# draw the stock price chart with date on the x-axis and price on the y-axis
# stock_hfq_df.plot(x="date", y="close", title="000001 stock price")

# The .show() method is part of the matplotlib library and is used to display the chart.
# To display the chart using matplotlib, you can add the following code after the .plot method:
# plt.show()


# Create a strategy to buy the stock when it is underpriced and sell it when it is overpriced
# the type of data is DataFrame

def backtest_strategy(data : pd.DataFrame):
    canBuy = True
    canSell = False
    shares = 0
    cash = 100000
    portfolio = []
    transactions = []
    for index, row in data.iterrows():
        #df.shape returns a tuple (3, 2), where the first value is the number of rows, and the second value is the number of columns. 
        #By using df.shape[0], you can get the number of rows in the DataFrame.
        if row["close"] < row["open"] and canBuy and cash > 0 and index < data.shape[0]-1:
            # tomorrow buy with open price
            shares = cash / data.loc[index+1]["open"]
            cash = 0
            canSell = True
            transactions.append(
                {
                    "date": data.loc[index+1]["date"],
                    "action": "buy",
                    "price": data.loc[index+1]["open"],
                    "shares": shares,
                    "money": shares * data.loc[index+1]["open"] + cash,
                }
            )

        if row["close"] > row["open"] and canSell and shares > 0 and index < data.shape[0]-1:
            cash = shares * data.loc[index+1]["open"]
            shares = 0
            transactions.append(
                {
                    "date": data.loc[index+1]["date"],
                    "action": "sell",
                    "price": data.loc[index+1]["open"],
                    "shares": shares,
                    "money": shares * row["open"] + cash,
                }
            )
        portfolio.append({"date": data.loc[index]["date"], "cash": cash, "shares": shares})
    return pd.DataFrame(portfolio), pd.DataFrame(transactions)


# Evaluate the performance of the strategy
portfolio, transactions = backtest_strategy(stock_hfq_df)

print(portfolio)
print(transactions)


# plot chart with two y values
fig, ax1 = plt.subplots()
color = 'tab:red'
ax1.plot(
    portfolio["date"], portfolio["cash"] + portfolio["shares"] * stock_hfq_df["close"],color=color
)
ax1.set_xlabel("Date")
ax1.set_ylabel("Portfolio Value")
plt.title("Backtesting Results")

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color = 'tab:blue'
ax2.set_ylabel("Y2 Value", color=color)  # we already handled the x-label with ax1
ax2.plot("date", "close", data= stock_hfq_df )
ax2.tick_params(axis='y', labelcolor=color)
#fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()