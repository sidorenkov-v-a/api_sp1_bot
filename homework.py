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
    format=(
        '%(asctime)s,%(msecs)d %(levelname)-8s '
        '[%(filename)s:%(lineno)d] %(message)s'
    ),
    datefmt='%Y-%m-%d:%H:%M:%S',
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

RESPONSE_FIELDS = ('homework_name', 'status')

STATUS_VERDICTS = {
    'rejected1': 'К сожалению в работе нашлись ошибки.',
    'approved1': (
        'Ревьюеру всё понравилось, '
        'можно приступать к следующему уроку.'
    )
}


def is_response_valid(response):
    error_fields = []
    for field in RESPONSE_FIELDS:
        if response.get(field) is None:
            error_fields.append(field)

    if error_fields:
        error_dscr = (
            'Error!\n'
            f'Response = \n{response}\n'
            f'has no field(s): \n{error_fields}'
        )
        logging.error(error_dscr)
        return False, error_dscr

    return True


def parse_homework_status(homework):
    result = is_response_valid(homework)
    if result is True:
        homework_name = homework['homework_name']
        status = homework['status']

        verdict = STATUS_VERDICTS.get(status)
        if verdict:
            return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
        else:
            error_dscr = (
                f'Error!\n'
                f'Resposne = \n{homework}\n'
                f'Status field has unexpected value = {status}'
            )
            logging.error(error_dscr)
            return error_dscr
    else:
        return result[1]


def get_homework_statuses(current_timestamp):
    current_time = int(time.time())

    if isinstance(current_timestamp, int) is False:
        logging.error('Incorrect current_timestamp type')
        current_timestamp = current_time

    if current_time < current_timestamp < 0:
        logging.error('Incorrect current_timestamp value')
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
            'API request fail'
            f'Requests heades: \n {headers} \n '
            f'Requests params: \n {params} \n'
        )
        logging.exception(f'{info} \n {e}')
        return dict()

    return response.json()


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    # current_timestamp = int(time.time())  # начальное значение timestamp
    # while True:
    #     try:
    #         new_homework = get_homework_statuses(current_timestamp)
    #
    #         if new_homework.get('homeworks'):
    #             homework = new_homework.get('homeworks')[0]
    #             message = parse_homework_status(homework)
    #             send_message(message)
    #
    #         current_timestamp = new_homework.get('current_date')
    #         time.sleep(300)
    #
    #     except Exception as e:
    #         logging.exception(f'Бот упал с ошибкой: {e}')
    #         time.sleep(5)
    #         continue

    current_timestamp = int(time.time())  # начальное значение timestamp
    while True:
        try:
            new_homework = get_homework_statuses(0)

            if new_homework.get('homeworks'):
                homework = new_homework.get('homeworks')[0]
                message = parse_homework_status(homework) + "\nHello from HEROKU"
                send_message(message)

            time.sleep(10)

        except Exception as e:
            logging.exception(f'Бот упал с ошибкой: {e}')
            time.sleep(5)
            continue


if __name__ == '__main__':
    main()
