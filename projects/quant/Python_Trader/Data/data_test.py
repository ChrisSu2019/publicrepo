from SingleStock import *

import concurrent.futures

#股票市场总貌
#stock_sse_summary_df = ak.stock_sse_summary()
#print(stock_sse_summary_df)


#stock_szse_summary_df = ak.stock_szse_summary(date="20200619")
#print(stock_szse_summary_df)


##wirte codes to test the singleStock.py function
#new_varnew_var = get_stock_data("000001", "hfq")
#print(new_varnew_var.head())

#stock_szse_area_summary_df = ak.stock_szse_area_summary(date="202301")
#print(stock_szse_area_summary_df)

# use Akshare to collect all A stock history data and put them in each excel,naming as symbol.excel


# 获取所有指数
stock_zh_index_spot_df = ak.stock_zh_index_spot()
stock_zh_index_spot_df.to_excel("all_stocks_zhishu_em.xlsx")

stock_list = stock_zh_index_spot_df["代码"].tolist()

def process_item(stock):
    # do some processing on the item
    try:
        # Get historical data for the stock
        stock_data = ak.stock_zh_index_daily_tx(symbol=stock)

        # Save the data as an Excel file with the file name as the stock symbol
        file_name = f"{stock}.xlsx"
        stock_data.to_excel(file_name)
        print(f"{file_name} saved successfully!")
    except:
        print(f"Failed to save {stock} data!")
    return stock_data

items = stock_list  # a list of items to process

# create a ThreadPoolExecutor with a maximum of 4 worker threads
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    # submit each item to the executor for processing
    futures = [executor.submit(process_item, item) for item in items]

# wait for all futures to complete and get the processed items
processed_items = [future.result() for future in futures]

print("jobs all done")

# Loop through the stock list and save historical data as Excel files
#for stock in stock_list:
#    try:
#        # Get historical data for the stock
#        stock_data = ak.stock_zh_index_daily_tx(symbol=stock)

#        # Save the data as an Excel file with the file name as the stock symbol
#        file_name = f"{stock}.xlsx"
#        stock_data.to_excel(file_name)
#        print(f"{file_name} saved successfully!")
#    except:
#        print(f"Failed to save {stock} data!")



#print(stock_zh_index_spot_df)