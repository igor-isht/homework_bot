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
TELEGRAM_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID'))

RETRY_TIME = 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Эта функция отправляет сообщения в чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        logging.error(error, exc_info=True)


def get_api_answer(current_timestamp) -> dict:
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


def check_response(response) -> list:
    """Принимает ответ от API практикума и возвращает список работ."""
    # Тут валятся тесты
    # if not isinstance(response, dict):
    #    raise Exception('ответ от API не является словарем')
    if not response['homeworks']:
        return False
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise Exception('при запросе д/з под ключом "homeworks" '
                        'значения не в виде списка')
    else:
        return homeworks


def parse_status(homework) -> str:
    """Извлекает статус д/з и подготавливает сообщение для отправки."""
    homework_name = homework.get('homework_name')
    if not homework.get('status'):
        raise Exception('при запросе статуса работы был возвращен '
                        'пустой ответ')
    status = homework.get('status')
    if status not in VERDICTS:
        raise KeyError('был возвращен незадокументированный статус '
                       'домашней работы')
    verdict = VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет наличие токенов."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
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
    previous_error_message = ''
    initial_homeworks = []

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks != initial_homeworks and homeworks:
                initial_homeworks = homeworks
                message = parse_status(homeworks[0])
                send_message(bot, message)
                logging.info(f'Бот отправил сообщение {message}')
            else:
                logging.debug('Новые статусы/работы отсутствуют')
            current_timestamp = int(time.time())

        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logging.error(error_message, exc_info=True)
            if error_message != previous_error_message:
                previous_error_message = error_message
                send_message(bot, error_message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':

    # Создание и настройка логгера
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    main()
