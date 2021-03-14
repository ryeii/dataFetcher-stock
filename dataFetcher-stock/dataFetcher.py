import yfinance as yf
import pandas as pd
import PySimpleGUI as sg
import time
import os


def last_trade_date():
    t = time.time()
    while time.strftime("%w", time.localtime(t)) == "0" or time.strftime("%w", time.localtime(t)) == "6":
        t = t - 86400
    return time.strftime("%Y-%m-%d", time.localtime(t))


def handle_empty_file(code):
    file_name = "historical_data/" + code + ".csv"
    if len(pd.read_csv(file_name)) < 3:
        os.remove(file_name)
        return 'handled'
    else:
        return '0'


sg.theme('DarkAmber')
layout = [
    [sg.Text('Use this tool to fetch stock data, based on Yahoo finance.')],
    [sg.Text('Enter your stock code:'), sg.In(size=(10, 1))],
    [sg.Text('Fetch data from xxx to '), sg.In(default_text=last_trade_date(), size=(10, 1))],
    [sg.Button('Fetch'), sg.Button('Run self updates')],
    [sg.Text('Console output:')],
    [sg.Multiline(size=(60, 11), key='console', text_color='white')]
]
window = sg.Window('Data Fetcher: Stock', layout, font='Courier 16', finalize=True)
window['console'].print('console ready.\n')


def fetch_latest_data(code, latest_trade_day=last_trade_date()):
    code = code.upper()
    window['console'].print("fetching data for code: ", code)
    file = "historical_data/" + code + ".csv"
    try:
        pd.read_csv(file)
        existing_data = pd.read_csv(file)
        latest_date = existing_data.loc[len(existing_data) - 1, "Date"]
        window['console'].print("checking for vacuole...")
        if latest_date == latest_trade_day:
            window['console'].print("latest data already acquired:", latest_date, '\n\n\n')
        else:
            window['console'].print("data vacuole from ", latest_date, " to ", latest_trade_day, ', downloading...')
            yf.Ticker(code).history(start=latest_date,
                                    end=time.strftime("%Y-%m-%d", time.localtime(time.time()))).to_csv(
                "temporary_file.csv")
            if pd.read_csv("temporary_file.csv").loc[len(pd.read_csv("temporary_file.csv")) - 1, "Date"] == latest_date:
                window['console'].print("No further available data for this code, starting ", latest_date)
            else:
                window['console'].print("downloaded, writing files...")
                with open(file, "r", encoding="utf-8") as existing_file:
                    old_data = existing_file.readlines()
                with open("temporary_file.csv", "r", encoding="utf-8") as new_data_file:
                    new_data = new_data_file.readlines()
                with open(file, "w", encoding="utf-8") as existing_file:
                    for line in new_data[3:]:
                        old_data.append(line)
                    for line in old_data:
                        existing_file.write(line)
            window['console'].print("complete, rechecking...\n")
            fetch_latest_data(code, latest_trade_day)
    except FileNotFoundError:
        try:
            yf.Ticker(code).history(period="max").to_csv(file)
            if handle_empty_file(code) == 'handled':
                window['console'].print('- : No data found, code may be delisted\n\n')
            else:
                window['console'].print("data downloaded.\n\n")
        except TimeoutError:
            window['console'].print("request timeout.\n\n")


def data_self_update():
    lst = os.listdir('historical_data')
    log = open('logs/self_update_log' + str(time.localtime()), 'w')
    for file in lst:
        file_name = "historical_data/" + file
        if len(pd.read_csv(file_name)) < 3:
            os.remove(file_name)
            log.write('file removed: ' + file_name)
            window['console'].print('file removed: ' + file_name)
        else:
            fetch_latest_data(file.split('.csv')[0])
            log.write('file updated: ' + file)
            window['console'].print('file updated: ' + file)
    log.close()


while True:
    event, values = window.read()
    if event == 'Fetch':
        if values[0] != '':
            fetch_latest_data(values[0], values[1])
    if event == 'Run self updates':
        data_self_update()
    if event == sg.WIN_CLOSED:
        break

window.close()
