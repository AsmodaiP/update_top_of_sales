import json
from typing import final
from google.oauth2 import service_account
import os
from googleapiclient.discovery import build
import datetime as dt
from dotenv import load_dotenv
import logging
import telegram
from classes import ShortArticleInfo

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

load_dotenv()

# TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
ID_FOR_NOTIFICATION = 295481377
# bot = telegram.Bot(token=TELEGRAM_TOKEN)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials_service.json')
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', None)


def convert_to_column_letter(column_number):
    column_letter = ''
    while column_number != 0:
        c = ((column_number - 1) % 26)
        column_letter = chr(c + 65) + column_letter
        column_number = (column_number - c) // 26
    return column_letter

def update_table(sheetname, info: ShortArticleInfo, day, table_id=SPREADSHEET_ID):
    range_name = sheetname
    position_for_place = 2 + (int(day) - 1) * 5 - 24
    print(position_for_place)

    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=table_id,
                                range=f'{range_name}!A:N', majorDimension='ROWS').execute()

    values = result.get('values', [])
    body_data = []
    i = 1
    for row in values:
        print(row)
        try:
            if row[1] == str(info['id']):
                body_data += [
                    
                    {'range': f'{range_name}!{convert_to_column_letter(position_for_place)}{i}','values': [[info['price']]]},
                    {'range': f'{range_name}!{convert_to_column_letter(position_for_place+1)}{i}','values': [[  info['revenue']  ]]},
                    {'range': f'{range_name}!{convert_to_column_letter(position_for_place+2)}{i}','values': [[  info['orders_count']  ]]}
                ]
        except:
            pass
        finally:
            i += 1
    logging.info(body_data)
    result = ''
    body = {
            'valueInputOption': 'USER_ENTERED',
            'data': body_data}

    sheet.values().batchUpdate(spreadsheetId=table_id, body=body).execute()
    result = ''
    # return {'result': result, 'errors': data.keys()}



def get_sheetnames(spreadsheet_id=SPREADSHEET_ID):
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    sheets = sheet.get(spreadsheetId=spreadsheet_id).execute().get('sheets')
    sheetnames = []
    for sheet in sheets:
        sheetnames.append(sheet.get("properties", {}).get("title", "Sheet1"))
    return sheetnames

def get_rows(spreadsheet_id=SPREADSHEET_ID):
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    sheetnames = get_sheetnames(spreadsheet_id)
    rows = []
    for sheetname in  sheetnames:
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=f'{sheetname}!A:B', majorDimension='ROWS').execute()
        values = result.get('values', [])
        for row in values:
            try:
                name = row[0]
                article = row[1]
                if isinstance(name, str) and len(name)>3 and article.isdigit() and len(article)==8:
                    rows.append((sheetname, name, row[1]))
            except:
                pass
    return rows

        
# get_rows()