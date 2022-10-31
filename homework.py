import os
import sys
import telegram
from dotenv import load_dotenv
import time
import requests
import logging
from exceptions import SendMessageError, WrongApiAnswer, InvalidNameHomeWork
from http import HTTPStatus

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s'
)
handler.setFormatter(formatter)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в Телеграм."""
    try:
        logger.info('Отправляем сообщение в телеграм')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        raise SendMessageError(error)
    else:
        logger.info('Сообщение отправлено удачно')


def get_api_answer(current_timestamp):
    """Делаем запрос к эндпоинту."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    requests_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params,
    }
    logger.info('Делаем запрос к API')
    try:
        response = requests.get(**requests_params)
        if response.status_code != HTTPStatus.OK:
            raise WrongApiAnswer(
                f'Запрос к {ENDPOINT} вернул статус {response.status_code}, '
                'Мы ожидаем статус ответа - 200.'
            )
        else:
            logger.info('Запрос к API прошел успешно')
    except Exception as error:
        raise WrongApiAnswer(
            f'При запросе к {ENDPOINT} вернулась ошибка "{error}" '
            f'Параметры запроса: "{params}"'
        )
    return response.json()


def check_response(response):
    """Проверяем ответ от API."""
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            f'Ответ пришел не ввиде списка, а в виде {type(response)}'
        )
    if 'homeworks' not in response:
        raise KeyError('В ответ пришла ошибка')
    else:
        logger.info('Ответ API проверен')
    return response['homeworks']


def parse_status(homework):
    """Извлекает статус из конкретной домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(
            'Статус домашней работы не в списке статусов'
        )
    if not homework_name:
        raise InvalidNameHomeWork(
            'Имя домашней работы не в списке имен'
        )
    else:
        logger.info('Получаем статус домашней работы')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность токенов."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        raise SystemExit('Один из токенов не рабочий.')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homework = check_response(response)
            if len(homework) > 0:
                logger.info('Есть статус домашки')
                message = parse_status(homework[0])
                send_message(bot, message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            logger.error(f'Сообщение не было отправлено из-за: {error}')
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
