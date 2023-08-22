import pandas as pd
import os


column_name_mapping = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "change_percent",
    "涨跌额": "change_amount",
    "换手率": "turnover_rate",
    # not sure whether this would be useful or not
    "复权因子": "adjust_factor",
    "后复权收盘价": "adj_close",
}


def get_english_column_names(df):
    return df.rename(columns=column_name_mapping)


def load_excel_data(path, symbol):
    # Construct the filename from the path and symbol
    filename = f"{symbol}.xlsx"
    filepath = f"{path}/{filename}"

    # Load data from the Excel file using pandas
    df = pd.read_excel(filepath, engine='openpyxl').iloc[:, 1:7]
    dataframe = get_english_column_names(df)
    dataframe.index = pd.to_datetime(dataframe['date'])
    
    # Return the DataFrame
    return dataframe

def load_symbols():
    filename = f"D:/repos/quant/Python_Trader/all_stocks_em.xlsx"
    # Load data from the Excel file using pandas
    df = pd.read_excel(filename, engine='openpyxl', dtype={'代码': str})
    return df["代码"].tolist()

   

#folder_path = "/path/to/folder"
#file_extension = ".txt"
def loadFilesNames(folder_path, file_extension):
    file_names = [f for f in os.listdir(folder_path) if f.endswith(file_extension)]
    print(file_names)



