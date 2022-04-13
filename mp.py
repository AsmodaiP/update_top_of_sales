from datetime import datetime, timedelta

import logging

from xmlrpc.client import DateTime
from dotenv import load_dotenv
import os

import requests
from classes import *
from typing import List
from update_table import get_rows, update_table

load_dotenv()
TOKEN = os.environ.get('TOKEN')
print(TOKEN)
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', None)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
load_dotenv()
# TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
ID_FOR_NOTIFICATION = 295481377
# bot = telegram.Bot(token=TELEGRAM_TOKEN)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials_service.json')

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', None)


logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


def get_seller_items(date: DateTime, name, token=TOKEN, start_row=0) -> List[ArticleInfo]:
    
    date_for_params = (date.strftime('%Y-%m-%d'))
    headers = {
        'X-Mpstats-TOKEN': token
    }
    url = 'https://mpstats.io/api/wb/get/seller?d1=2020-07-13&d2=2020-08-11'
    params = {
        'path': name,
        'd1':date_for_params,
        'd2': date_for_params
    }
    data = {
        'startRow': start_row,
        'endRow': start_row+5000
    }

    response = requests.post(url, headers=headers, params=params, json=data)
    # print(response.json())
    data = response.json().get('data', [])
    return data




def update_row(date, sheetname, name: str, id: int):
    # print(get_seller_items('ООО АМА'))
    logger.info(f'Получение информации для {sheetname} {name} {id}')
    start_row = 0
    # items = get_seller_items(name, start_row=start_row)
    while True:
        # print(name, start_row)
        items = get_seller_items(date, name)
        # print(items)
        item = [item for item in items if item['id'] == id]
        if len(item) != 0:
            break
        if start_row > 5000 * 10 or len(items) == 0:
            return
        else:
            start_row += 5000
    item: ArticleInfo = item[0]
    info = ShortArticleInfo(
        id=item['id'],
        revenue=item['revenue'],
        price=item['client_price'],
        orders_count=item['sales']
    )
    print(info)
    update_table(sheetname, info, date.day)




if __name__ == '__main__':
    # update_row(sheetname='1', name='ООО АМА', id=61080921)
    date = datetime.now() - timedelta(1)
    # get_seller_items('ООО АМА')
    rows = get_rows()
    # print(rows)
    # date = 
    for row in rows:
        sheetname, name, id = row
        update_row(date,sheetname, name.strip(), int(id))
    # print(len((get_seller_items('ООО АМА'))))