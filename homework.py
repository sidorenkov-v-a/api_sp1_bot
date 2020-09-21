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
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

PRACTICUM_API_URL = (
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
)

proxy = telegram.utils.request.Request(
    proxy_url='socks5://185.151.243.37:1080')
bot = telegram.Bot(token=TELEGRAM_TOKEN, request=proxy)


def is_response_valid(response):
    check_fields = ['homework_name', 'status']
    error_fields = []
    for field in check_fields:
        if response.get(field) is None:
            error_fields.append(field)

    if error_fields:
        raise ValueError(
            f'Response = \n{response}\n'
            f'has no field(s): \n{error_fields}'
        )

    return True


def parse_homework_status(homework):
    if is_response_valid(homework):
        homework_name = homework.get('homework_name')
        status = homework.get('status')
        status_verdict = {
            'rejected': 'К сожалению в работе нашлись ошибки.',
            'approved': (
                'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.'
            )
        }
        verdict = status_verdict.get(status)
        if verdict:
            return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
        else:
            raise ValueError(
                f'Resposne status field has unexpected value = {status}'
            )


def get_homework_statuses(current_timestamp):
    if isinstance(current_timestamp, int) is False:
        raise TypeError('Current time should be int')

    current_time = int(time.time())
    if current_time < current_timestamp < 0:
        current_timestamp = current_time

    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    params = {'from_date': current_timestamp}

    try:
        response = requests.get(
            PRACTICUM_API_URL,
            params=params,
            headers=headers)
    except requests.exceptions.RequestException as e:
        info = (
            f'Response heades: \n {headers} \n '
            f'Response params: \n {params} \n'
        )
        logging.exception(f'{info} \n {e}')
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
                homework = new_homework.get('homeworks')[0]
                message = parse_homework_status(homework)
                send_message(message)

            current_timestamp = new_homework.get('current_date')
            time.sleep(300)

        except Exception as e:
            logging.exception(f'Бот упал с ошибкой: {e}')
            time.sleep(5)
            continue


if __name__ == '__main__':
    main()
