import logging
import os
import time
from datetime import datetime

import requests
import telegram
from dotenv import load_dotenv

log_time = datetime.today()
logging.basicConfig(
    filename=f'app-{log_time}.log', filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

PRACTICUM_API_URL = \
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

proxy = telegram.utils.request.Request(
    proxy_url='socks5://185.151.243.37:1080')
bot = telegram.Bot(token=TELEGRAM_TOKEN, request=proxy)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, ' \
                  'можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if isinstance(current_timestamp, int) is False:
        raise TypeError('Current time should be int')

    current_time = int(time.time())
    if current_timestamp < 0 or current_timestamp > current_time:
        raise ValueError(
            f'current_timestamp should be grater than 0 '
            f'and lower than current time = {current_time}'
        )

    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    params = {'from_date': current_timestamp}

    try:
        response = requests.get(
            PRACTICUM_API_URL,
            params=params,
            headers=headers)
    except requests.exceptions.RequestException as e:
        logging.exception(e)
        return dict()

    return response.json()


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())  # начальное значение timestamp
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)

            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]))
            current_timestamp = new_homework.get(
                'current_date')  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            logging.exception(f'Бот упал с ошибкой: {e}')
            time.sleep(5)
            continue


if __name__ == '__main__':
    main()
