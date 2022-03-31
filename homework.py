import requests
import time
import os
import telegram
import logging
from dotenv import load_dotenv


# Подгрузка токенов
load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = 1057292278

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

# Создание и настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)


def send_message(bot, message):
    """Эта функция отправляет сообщения в чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Функция делает запрос к API практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
        code = homework_statuses.status_code
        if code == 200:
            homework_statuses = homework_statuses.json()
            return homework_statuses
        else:
            raise Exception(f'эндпоинт {ENDPOINT} недоступен. '
                            f'Код ответа API: {code}')
    except Exception:
        raise Exception('прочие ошибки при запросе к эндпойту')


def check_response(response):
    """Принимает ответ от API практикума и возвращает список работ."""
    if response == {}:
        raise Exception('ответ от API содержит пустой словарь')
    if not response['homeworks']:
        raise Exception('ответ от API не содержит ключа "homeworks"')
    homeworks = response['homeworks']
    if type(homeworks) != list:
        raise Exception('при запросе д/з под ключом "homeworks" '
                        'значения не в виде списка')
    else:
        return homeworks


def parse_status(homework):
    """Извлекает статус д/з и подготавливает сообщение для отправки."""
    homework_name = homework.get('homework_name')
    if not homework.get('status'):
        raise Exception('при запросе статуса работы был возвращен '
                        'пустой ответ')
    status = homework.get('status')
    if status not in HOMEWORK_STATUSES:
        raise KeyError('был возвращен незадокументированный статус '
                       'домашней работы')
    verdict = HOMEWORK_STATUSES.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет наличие токенов"""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = ('отсутствует одна или несколько обязательных переменных '
                   'окружения. Программа принудительно остановлена.')
        logging.critical(message)
        if TELEGRAM_CHAT_ID:
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
            send_message(bot, message)
        exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previous_response = ''
    previous_error_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if response != previous_response:
                previous_response = response
                homeworks = check_response(response)
                message = parse_status(homeworks[0])
                send_message(bot, message)
                logging.info(f'Бот отправил сообщение {message}')
            else:
                logging.debug('Новые статусы/работы отсутствуют')
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time())

        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logging.error(error_message, exc_info=True)
            if error_message != previous_error_message:
                previous_error_message = error_message
                send_message(bot, error_message)
            time.sleep(RETRY_TIME)
        else:

            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
