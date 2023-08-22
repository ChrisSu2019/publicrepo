
import akshare as ak
import pandas as pd

# Get basic information for all A shares
all_stocks = ak.stock_zh_a_spot_em()

# Save the data as an Excel file
all_stocks.to_excel("all_stocks_em.xlsx")
print("all_stocks.xlsx saved successfully!")

# Get the stock list for A shares
stock_list = all_stocks["代码"].tolist()

# Loop through the stock list and save historical data as Excel files
for stock in stock_list:
    try:
        # Get historical data for the stock
        stock_data = ak.stock_zh_a_hist(symbol=stock,adjust="hfq")

        # Save the data as an Excel file with the file name as the stock symbol
        file_name = f"{stock}.xlsx"
        stock_data.to_excel(file_name)
        print(f"{file_name} saved successfully!")
    except:
        print(f"Failed to save {stock} data!")
