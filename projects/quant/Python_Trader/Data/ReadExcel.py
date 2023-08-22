from Data.funcLib import *

# Load data for the symbol '000001' from the path 'D:/data'
#df = load_excel_data('D:/repos/quant/Python_Trader', '000001')

# Print the first 5 rows of the DataFrame
# print(df.head())

#names = loadFilesNames('D:/repos/quant/Python_Trader','xlsx')
names = load_symbols()

# iterate the names
if names:
    for name in names:
        print(name)


