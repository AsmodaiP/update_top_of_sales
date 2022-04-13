import json
from google.oauth2 import service_account
import os
from googleapiclient.discovery import build
import datetime as dt
from dotenv import load_dotenv
from marketplace import get_barcodes_with_full_info
import logging
from get_orders_of_day import clean_orders_from_user_status_1, get_all_orders, get_all_today_orders
import telegram

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
ID_FOR_NOTIFICATION = 295481377
bot = telegram.Bot(token=TELEGRAM_TOKEN)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials_service.json')
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
START_POSITION_FOR_PLACE = 14

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', None)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
load_dotenv('~/wb_fbs/.env ')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WEEKDAYS={
    0: 'Понедельник',
    1: 'Вторник',
    2: 'Среда',
    3: 'Четверг',
    4: 'Пятница',
    5: 'Суббота',
    6: 'Воскресенье'
}


def get_barcodes_with_orders_and_chartId(token, orders):
    barcodes_and_ids = {}
    logging.info('Сортировка информации по баркодам')
    for order in orders:
        barcode = order['barcodes'][0]
        id = int(order['orderId'])
        chrt_id = order['chrtId']
        if barcode not in barcodes_and_ids.keys():
            barcodes_and_ids[barcode] = {'orders': [id], 'chrtId': chrt_id}
        else:
            barcodes_and_ids[barcode]['orders'] += [id]

    logging.info(f'Получено {len(barcodes_and_ids)} баркодов')
    return barcodes_and_ids


def convert_to_column_letter(column_number):
    column_letter = ''
    while column_number != 0:
        c = ((column_number - 1) % 26)
        column_letter = chr(c + 65) + column_letter
        column_number = (column_number - c) // 26
    return column_letter


def get_count_or_0(data, article):
    if article in data.keys():
        count = data[article]['count']
        return count
    return 0


def get_total_price_or_0(data, article):
    if article in data.keys():
        count = str(data[article]['totalPrice'])[:-2]
        return count
    return 0

def custom_get_data_for_body(data, article, i, day, month, year=2022):
    position_for_place = START_POSITION_FOR_PLACE + (int(day) - 1) * 6 + 1
    range_name = f'{month}.{year}'
    letter_for_range = convert_to_column_letter(position_for_place)
    count = get_count_or_0(data, article)
    data_for_return =[{
                     'range': f'{range_name}!G{i}', 'values': [[data[article]['inside_article']]]}]
    if count != 0:
        total_price = get_total_price_or_0(data, article)
        data_for_return += [{'range': f'{range_name}!{letter_for_range}{i}', 'values': [[count]]}, {
                     'range': f'{range_name}!{convert_to_column_letter(position_for_place+2)}{i}', 'values': [[total_price]]},
                     
                     ]
        logging.info(data_for_return)
    return data_for_return


def get_data_about_today_nmid_and_count_of_orders(token):
    orders = get_all_today_orders(token)
    barcodes = get_barcodes_with_full_info(
        token=token, orders=orders)
    order_and_nmid_dict = {}
    for barcode in barcodes.keys():
        orders = barcodes[barcode]['orders']
        for order in orders:
            order_and_nmid_dict[order] = {
                'article': barcodes[barcode]['info']['nmId'],
                'totalPrice': barcodes[barcode]['totalPrice']}

    nmid_and_count = {}
    for order in order_and_nmid_dict.keys():
        article = str(order_and_nmid_dict[order]['article'])
        total_price = order_and_nmid_dict[order]['totalPrice']
        if not article in nmid_and_count:
            nmid_and_count[article] = {'count': 1, 'totalPrice': total_price}
        else:
            nmid_and_count[article]['count'] += 1
    return nmid_and_count


def get_nmid_and_count(barcodes):
    order_and_nmid_dict = {}
    for barcode in barcodes.keys():
        orders = barcodes[barcode]['orders']
        for order in orders:
            order_and_nmid_dict[order] = {
                'article': barcodes[barcode]['info']['nmId'],
                'totalPrice': barcodes[barcode]['totalPrice'],
                'inside_article': barcodes[barcode]['info']['article']
                }

    nmid_and_count = {}

    for order in order_and_nmid_dict.keys():
        article = str(order_and_nmid_dict[order]['article'])
        total_price = order_and_nmid_dict[order]['totalPrice']
        inside_article = order_and_nmid_dict[order]['inside_article']

        if not article in nmid_and_count:
            nmid_and_count[article] = {'count': 1, 'totalPrice': total_price, 'inside_article': inside_article}
        else:
            nmid_and_count[article]['count'] += 1
            nmid_and_count[article]['totalPrice'] += total_price

    return nmid_and_count


def get_end_begining(day, month, year=2022):
    current_day = day
    return (f'{year}-{month}-{current_day}T23:59:59+03:00',
            f'{year}-{month}-{current_day}T00:00:00.00+03:00')


def update_day(token, day, month, table_id):
    if day <= 9:
        day = f'0{day}'
    if month <= 9:
        month = f'0{month}'
    end, beginning = get_end_begining(day, month)
    logging.info((end, beginning))
    orders = get_all_orders(token=token, date_end=end, date_start=beginning)
    orders = clean_orders_from_user_status_1(orders)
    barcodes = get_barcodes_with_full_info(
        token=token, orders=orders)
    data = get_nmid_and_count(barcodes)
    return update_table(day, month, table_id, data)


def update_table(day, month, table_id, data, year=2022):
    range_name = f'{month}.{year}'
    position_for_place = START_POSITION_FOR_PLACE + (int(day) - 1) * 6

    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=table_id,
                                range=range_name, majorDimension='ROWS').execute()

    values = result.get('values', [])
    i = 3
    body_data = []
    if int(day) == dt.datetime.now().day:
        timestamp_for_table = str(dt.datetime.today().strftime('%d-%m-%Y %H:%M'))
        weekday = dt.datetime.today().weekday()
        body_data += [{'range': f'{range_name}!{convert_to_column_letter(position_for_place+5)}{i-1}',
                'values': [[WEEKDAYS[weekday]]]}]
    else:
        timestamp_for_table = f'{day}-{month}-{year} 23:59'
        
    body_data += [{'range': f'{range_name}!{convert_to_column_letter(position_for_place+1)}{i-1}',
                  'values': [[timestamp_for_table]]}]

    logging.info(body_data)
    result = ''
    if not values:
        logging.info('No data found.')
    else:
        for row in values[2:]:
            article = row[7].strip().upper()

            count = get_count_or_0(data, article)
            if count != 0:
                body_data += custom_get_data_for_body(
                    data, article, i, day, month)
                result += f'{article} — {count}\n'
            i += 1
            if article in data.keys():
                del data[article]
        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': body_data}

    sheet.values().batchUpdate(spreadsheetId=table_id, body=body).execute()
    result = ''
    return {'result': result, 'errors': data.keys()}


if __name__ == '__main__':
    cred_file = os.path.join(BASE_DIR, 'credentials.json')   
    with open(cred_file, 'r') as fp:
        cred = json.load(fp)
    for name, client_data in cred.items():
        token = client_data.get('token', None)
        table_id = client_data.get('table_id')
        if table_id is not None:
            day = dt.datetime.now().day 
            month = dt.datetime.now().month
            result = update_day(token, day, month, table_id)
            errors = result['errors']
            if len(errors) > 0 and name == 'БелотеловАГ':
                str_errors = '\n'.join(errors)
                bot.send_message(
                    ID_FOR_NOTIFICATION, f'Что-то не так с артикулами  у {name} \n{str_errors}')
