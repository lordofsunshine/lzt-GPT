import requests
import time
import random
import re
from loguru import logger
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from config.settings import config, headers
from ai.response_generator import ThabAIGen
from utils.time_utils import is_sleep_time

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

def request_with_timeout(method, url, **kwargs):
    kwargs.setdefault("timeout", config["request_timeout"])
    return getattr(session, method)(url, **kwargs)

def is_bot_mention(thread_text):
    user_id = str(config.get("bot_user_id") or "").strip()
    username = str(config.get("bot_username") or "").strip()
    if not user_id or not username:
        return False
    patterns = [
        rf'data-user="{re.escape(user_id)},\s*{re.escape(username)}"',
        rf'/members/{re.escape(user_id)}/',
    ]
    return any(re.search(pattern, thread_text or "") for pattern in patterns)

def get_thread_ids(params):
    try:
        response = request_with_timeout('get', 'https://api.zelenka.guru/threads', params=params, headers=headers)
        response.raise_for_status()
        threads = response.json().get('threads', [])
        return [thread.get('thread_id') for thread in threads if thread.get('thread_id') is not None]
    except requests.RequestException as e:
        logger.error(f'Ошибка при получении ID тем: {e}')
        return []

def process_question(thread_id):
    if is_sleep_time():
        logger.info('Скрипт в спящем режиме. Пропускаем обработку темы.')
        return

    try:
        res = request_with_timeout('get', f'https://api.zelenka.guru/threads/{thread_id}', headers=headers)
        res.raise_for_status()
        thread = res.json().get('thread') or {}

        if thread:
            first_post = thread.get('first_post') or {}
            thread_title = thread.get('thread_title') or ''
            thread_text = first_post.get('post_body_plain_text') or first_post.get('post_body') or ''
            create_username = thread.get('creator_username') or 'unknown'
            create_user_id = thread.get('creator_user_id')
            
            if '[IMG]' in thread_text or '[VIDEO]' in thread_text:
                logger.info(f'Тема {thread_id} содержит фото или видео. Пропускаем.')
                return
            
            is_mention = is_bot_mention(thread_text)
            
            text_lolz = f'{thread_title} {thread_text}'
            logger.info(f'Заголовок темы: {thread_title} от {create_username}')
            
            answer_bot = ThabAIGen(text_lolz, is_mention)
            if answer_bot is None:
                logger.info(f'Пропускаем тему {thread_id} из-за отсутствия ответа или незнания')
                return

            delay = random.randint(config["response_delay_min"], config["response_delay_max"])
            logger.info(f'Ожидание перед ответом: {delay} секунд')
            time.sleep(delay)

            params = {'thread_id': thread_id}
            data = {'post_body': f'{answer_bot}'}

            logger.info(f'Отправка ответа: {data["post_body"]}')
            res = request_with_timeout('post', 'https://api.zelenka.guru/posts', params=params, headers=headers, data=data)
            res.raise_for_status()
            response_json = res.json()
            logger.info(f'Ответ API: {response_json}')
            status = response_json.get('post')
            if status is not None:
                logger.success('Ответ на вопрос успешно отправлен')
                delay = random.randint(config["cooldown_min"], config["cooldown_max"])
                logger.info(f'Кулдаун перед следующей темой: {delay} секунд')
                time.sleep(delay)
            else:
                logger.error(f'Ответ на вопрос не был отправлен. Ответ API: {response_json}')
    except requests.RequestException as e:
        logger.error(f'Ошибка при обработке вопроса: {e}')
    except Exception as e:
        logger.error(f'Неожиданная ошибка при обработке вопроса: {e}')

def bump_threads():
    for thread_id in config["thread_ids_to_bump"]:
        url = f"https://api.zelenka.guru/threads/{thread_id}/bump"
        try:
            response = request_with_timeout('post', url, headers=headers)
            response.raise_for_status()
            info = response.json()
            if "errors" in info:
                logger.warning(f"Не удалось поднять тему {thread_id}. Причина: {str(info['errors']).strip('[]')}")
            else:
                logger.success(f"Успешно поднял тему с id {thread_id}")
            time.sleep(6)
        except Exception as err:
            logger.error(f"Произошла ошибка при поднятии темы {thread_id}: {err}")
    logger.info(f"Прошел {len(config['thread_ids_to_bump'])} тем. Ожидаю {config['thread_bump_interval'] // 3600} часов")
