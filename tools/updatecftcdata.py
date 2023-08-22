import os
import requests, zipfile, io
from datetime import datetime
import pandas as pd

basedir = os.path.join(os.path.dirname(__file__), 'data','futures','cftc')
year = datetime.today().year
url_dir_file = [
         (f"https://www.cftc.gov/files/dea/history/dea_fut_xls_{year}.zip", "legacy", "annual.xls"),
         (f"https://www.cftc.gov/files/dea/history/dea_com_xls_{year}.zip", "legacy_option_combined", "annualof.xls"),
         #(f"https://www.cftc.gov/files/dea/history/dea_cit_xls_{year}.zip", "index_trader_supplement", "deacit.xls"),
         (f"https://www.cftc.gov/files/dea/history/fut_disagg_xls_{year}.zip", "disaggregated", "f_year.xls"),
         (f"https://www.cftc.gov/files/dea/history/com_disagg_xls_{year}.zip", "disaggregated_option_combined", "c_year.xls"),
         (f"https://www.cftc.gov/files/dea/history/fut_fin_xls_{year}.zip","financial_futures", "FinFutYY.xls"),
         (f"https://www.cftc.gov/files/dea/history/com_fin_xls_{year}.zip", "financial_futures_option_combined", 'FinComYY.xls')
]

for url, dir, file in url_dir_file:
   print(f"Update CFTC data: {dir}")
   dirname = os.path.join(basedir, dir)
   r = requests.get(url)
   z = zipfile.ZipFile(io.BytesIO(r.content))
   df = pd.read_excel(z.read(file))
   df['Report_Date_as_MM_DD_YYYY'] = df['Report_Date_as_MM_DD_YYYY'].dt.strftime('%Y-%m-%d')
   for name, group in df.groupby('Market_and_Exchange_Names'):
      name = name.replace('/','-').replace('<','-')
      filename = os.path.join(dirname,f"{name}.csv")
      group.sort_values(by='As_of_Date_In_Form_YYMMDD', inplace=True)
      if not os.path.exists(filename):
            group.to_csv(filename, mode='w', index=False)
      else:
            old = pd.read_csv(filename)
            #old = old.drop('Report_Date_as_MM_DD_YYYY', axis=1)
            #old = old.rename(columns = {'Report_Date_as_MM_DD_YYYY.1':'Report_Date_as_MM_DD_YYYY'})
            df = pd.concat([old, group])
            df.drop_duplicates('As_of_Date_In_Form_YYMMDD', inplace=True)
            df.to_csv(filename, mode='w', index=False)