"""
Implemented by Artavazd Mnatsakanyan

Description:

    Script gets exchange rates from given api.
    COnvert rates to given cuurency.
    Adds all rates to local DB as list.
    Gets last 7 days data from DB.

Dependencies & Supported versions:

    Python 3.6.x

Libraries:

    sys, requests, urllib3, akamai.edgeauth

Revision:
	v0.1 alpha (25/02/2020)
            Initial version
"""
try:
    import os
    import re
    import sys
    import json
    import telebot
    import pymysql
    import logging
    import requests
    import datetime
    from enum import Enum
    import pymysql.cursors
    import matplotlib.pyplot as plt
except ImportError as exception:
    print ('%s - Please install the necessary libraries.' % exception)
    sys.exit(1)

Log = Enum('Log', (('INFO'), ('WARNING'), ('ERROR'), ('CRITICAL'), ('DEBUG')), start=0)
# Logger name
logger = logging.getLogger('telegram_exchange_bot')


def print_log_msg(msg, level):
    """
    Print and add the message into the log file.
    """
    # Check the log level
    {
        Log.INFO.value: lambda msg: logger.info(msg),
        Log.DEBUG.value: lambda msg: logger.debug(msg),
        Log.WARNING.value: lambda msg: logger.warning(msg),
        Log.ERROR.value: lambda msg: logger.error(msg),
        Log.CRITICAL.value: lambda msg: logger.critical(msg)
    }[level](msg)

    print(msg)


def get_exchange_rates():
    """
    Get exchange rates from https://exchangeratesapi.io/ api.
    Args:
        ----.
    Returns:
        all_rates - dict with all rates from api.
    """
    all_rates = {}
    print_log_msg('Open url for getting rates', Log.DEBUG.value)
    url = 'https://api.exchangeratesapi.io/latest?base=USD'
    try:
        response = requests.get(url)
    except HTTPError as httperr:
        print_log_msg('Can\'t connect to api: %s' % url, Log.ERROR.value)

    all_rates = create_rates_dict(response.json())

    return all_rates


def create_rates_dict(all_rates):
    """
    Get all rates and filter necessary rates.
    Args:
        all_rates - rates with all currencies.
    Returns:
        current_currency - dict with current currency.
    """
    print_log_msg('Create dictionary with all currencies and rates', Log.DEBUG.value)
    current_currency = {}
    for currencies in all_rates['rates']:
        current_currency.setdefault(all_rates['base'], [])
        if all_rates['rates'][currencies] != all_rates['base']:
            current_currency[all_rates['base']].append({currencies : round(float(all_rates['rates'][currencies]), 2)})

    return current_currency


def compare_rates(all_rates, previus_date):
    """
    Compare two dictionaries.
    If there are differneces return new one, in another case return nothing.
    Args:
        all_rates - current rates from api request.
        previus_date - last run date and time.
    Returns:
        all_rates/---
    """
    minutes_passed = True
    if os.path.isfile('last_run_date'):
        with open('last_run_date', 'r') as date:
            last_run_date = date.readline()
        if datetime.datetime.strptime(last_run_date, '%Y/%m/%d %H:%M:%S:%f') + \
                datetime.timedelta(minutes=10) > previus_date:
            with open('rates_' + next(iter(all_rates))) as result:
                previus_rates = json.load(result)
            if previus_rates == all_rates:
                minutes_passed = False
                return None, minutes_passed
            else:
                with open('rates_' + next(iter(all_rates)), "w") as result:
                    json.dump(all_rates, result)
                return all_rates, minutes_passed
        else:
            with open('last_run_date', 'w') as date_f:
                date_f.write(previus_date.strftime('%Y/%m/%d %H:%M:%S:%f'))
            print_log_msg('10 minutes in not left', Log.INFO.value)
            with open('rates_' + next(iter(all_rates))) as result:
                previus_rates = json.load(result)
            minutes_passed = False
            return previus_rates, minutes_passed
    else:
        with open('last_run_date', 'w') as date_f:
            date_f.write(previus_date.strftime('%Y/%m/%d %H:%M:%S:%f'))
        with open('rates_' + next(iter(all_rates)), "w") as result:
            json.dump(all_rates, result)
        return all_rates, minutes_passed


#def add_to_db(result):
#    """
#    Dump all currencies and rates to DB.
#    Args:
#        result - dictionary with currency and rates.
#    Returns:
#        ---
#    """
#    host = 'localhost'
#    username = 'root'
#    password = 'root'
#    dbname = 'telegram_exchange_db'
#    port = 3306
#    """
#    Connect to MySQL Database.
#    """
#    try:
#        connection = pymysql.connect(host=host, user=username, password=password,
#                db=dbname, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
#    except pymysql.MySQLError as pymysql_err:
#        print_log_msg(pymysql_err, Log.ERROR.name)
#        sys.exit(0)
#    finally:
#        print_log_msg('Connection opened successfully.', Log.INFO.value)
#    """
#    Execute SQL query.
#    Args:
#        result - final dictionary with team names and scores.
#    Returns:
#        ---
#    """
#    try:
#        with connection.cursor() as cursor:
#            for currency, rates in result.items():
#                for rate in rates:
#                    for rate_name, rate_value in rate.items():
#                        # Create a new record
#                        teams_info_path = ("INSERT INTO `telegram_exchange` (`Base`,`Currency`, `Value`) VALUES (%s, %s, %s)")
#                        cursor.execute(teams_info_path, (currency, rate_name, rate_value))
#            # Connection is not autocommit by default.
#            # So you must to save your changes.
#            connection.commit()
#
#    except pymysql.MySQLError as pymysql_err:
#        print_log_msg(pymysql_err, Log.ERROR.value)
#        print_log_msg("Can't append scores to the db:", Log.ERROR.value)
#
#    finally:
#        connection.close()
#        connection = None
#        print_log_msg('Data has already appended in to DB successfully', Log.INFO.value)
#        print_log_msg('Database connection closed.', Log.INFO.value)
#

def convert_rates(s_convert, multiplier):
    """
    Convert rates
    Args:
        s_convert - second converter type
        multiplier - number for multipy
    Returns:
        new_converted_rate
    """
    url = 'https://api.exchangeratesapi.io/latest?symbols=USD,%s' % (s_convert.upper())
    response = requests.get(url).json()
    print (response)
    for rate in response['rates']:
        if rate == 'USD':
            f_value = response['rates'][rate]
        if rate == s_convert.upper():
            s_value = response['rates'][rate]
    return round(float(s_value)/float(f_value)*float(multiplier), 2)


def show_last_seven_days_rates(f_convert, s_convert):
    """
    Show last 7 days rate
    Args:
        f_convert - first converter type
        s_convert - second converter type
    Returns:
        plot
    """
    values = []
    date_list = []

    current_date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
    last_week_date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days=7), '%Y-%m-%d')
    url = 'https://api.exchangeratesapi.io/history?start_at=%s&end_at=%s&base=%s&symbols=%s' % \
            (last_week_date, current_date, f_convert.upper(), s_convert.upper())
    response = requests.get(url).json()

    for date, rates in response['rates'].items():
        date_list.append(date)
        for rate_name, rate_value in rates.items():
            if rate_value not in values:
                values.append(rate_value)

    plt.plot(date_list, values)
    plt.savefig('analys.png')


def create_tel_bot():
    """
    Create telegram bot for getting exchange rates.
    Args:
        ---
    Returns:
        ---
    """
    patt = r'\d+'
    # For logging debug, warning, error and info messages into log file
    logFile = './telegram_exchange_bot.log'
    level = 'DEBUG'
    logging.basicConfig(filename=logFile, level=level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filemode='w')

    tel_bot = telebot.TeleBot('1121274019:AAHKIIwcQ0NWpRgu_X_LdfZssWw1i0j5_O8')
    @tel_bot.message_handler(commands=['start'])
    def start_message(message):
        tel_bot.send_message(message.chat.id, 'Hi')

    @tel_bot.message_handler(commands=['list', 'lst'])
    def send_text(message):
        # Get current currency date
        result = get_exchange_rates()
        for currency, rates in result.items():
            output = ''
            tel_bot.send_message(message.chat.id, currency)
            for rate in rates:
                for rate_name, rate_value in rate.items():
                    output += """%s: %s\n""" % (rate_name, rate_value)
        tel_bot.send_message(message.chat.id, output)

        # Get current runing time.
        current_date = datetime.datetime.now()

        all_rates, flag = compare_rates(all_rates, current_date)
        if not:
            print_log_msg('There is no update with the previus run', Log.INFO.value)


    @tel_bot.message_handler(commands=['exchange'])
    def send_text(message):
        tel_bot.send_message(message.chat.id, 'Please enter convert parameters')
        @tel_bot.message_handler(content_types=['text'])
        def send_result(output):
            if re.search(patt, output.text):
                convert_size = re.search(patt,output.text).group(0)
                second_converter = output.text.split('to')[-1].strip()
                res = convert_rates(second_converter, convert_size)
                tel_bot.send_message(output.chat.id, res)
            else:
                tel_bot.send_message(output.chat.id, 'Please write between currencies \' to \' ')


    @tel_bot.message_handler(commands=['history'])
    def send_text(message):
        tel_bot.send_message(message.chat.id, 'For displaying last 7 days currencies, please enter corresponding parametrs')
        @tel_bot.message_handler(content_types=['text'])
        def send_result(output):
            first_converter = output.text.split('/')[0]
            second_converter = output.text.split('/')[-1]
            show_last_seven_days_rates(first_converter, second_converter)
            if not os.path.isfile('analys.png'):
                tel_bot.send_message(output.chat.id, 'Please enter currencies with the following type: USD/CAD')
            else:
                tel_bot.send_photo(output.chat.id, photo=open('./analys.png', 'rb'))
    tel_bot.polling()


if __name__ == '__main__':
    create_tel_bot()
