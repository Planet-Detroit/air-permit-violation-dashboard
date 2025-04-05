# Importing required libraries
import pygsheets
from pygsheets.datarange import DataRange
import pandas as pd
  
# Create the cietn and enter 
gc = pygsheets.authorize(service_account_env_var = 'pyg_sheets_auth')

# Grab the spreadsheet
sh = gc.open('EGLE-AQD-Violation-Notices-2018-2024')

# Grab the worksheet
wks = sh.worksheet_by_title("data")

# Define a dataframe
df = pd.read_csv('output/EGLE-AQD-Violation-Notices-2018-Present.csv')

# Assign the dataframe to the worksheet
wks.set_dataframe(df, start='A1', fit=True)

# Freeze the first row
wks.frozen_rows=1

# Bold the first row
model_cell = wks.cell('A1')

model_cell.set_text_format('bold', True)

drange = pygsheets.datarange.DataRange(start='A1', end='T1', worksheet=wks)

drange.apply_format(model_cell)
