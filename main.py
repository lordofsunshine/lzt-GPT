import requests
import time
import random
from loguru import logger
import g4f
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import re
from datetime import datetime, time as dt_time
import json

# Конфигурация
config = {
    "token_lolz": "YOUR_LZT_TOKEN",
    "forum_id": 8,
    "sleep_start_hour": 3,  # Начало времени сна (3:00)
    "sleep_end_hour": 6,    # Конец времени сна (6:00)
    "typo_probability": 0.001,  # Вероятность опечатки
    "emoji_probability": 0.5,   # Вероятность добавления эмодзи
    "particle_probability": 0.005,  # Вероятность добавления частиц
    "synonym_probability": 0.005,   # Вероятность замены синонимом
    "response_delay_min": 10,   # Минимальная задержка перед ответом
    "response_delay_max": 20,   # Максимальная задержка перед ответом
    "cooldown_min": 260,    # Минимальный кулдаун между темами
    "cooldown_max": 300,    # Максимальный кулдаун между темами
    "thread_check_interval": 15,    # Интервал проверки новых тем
    "error_delay": 60,  # Задержка при ошибке
    "thread_bump_interval": 18 * 3600,  # Интервал поднятия тем (каждые 12 часов)
    "thread_ids_to_bump": [ID THREAD, ID THREAD, ID THREAD, ID THREAD, ID THREAD]  # ID тем для поднятия
}

# Настройка логирования
logger.remove()
logger.add(
    "bot.log",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <white>{message}</white>",
    level="INFO",
    rotation="1 day",
    compression="zip"
)

# Логирование в консоль
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <white>{message}</white>",
    level="INFO",
    colorize=True
)

forum_id = config["forum_id"]
headers = {
    'accept': 'application/json',
    'Authorization': f'Bearer {config["token_lolz"]}',
}

settings_gpt = """
Ты - пользователь форума zelenka.guru. Отвечай максимально естественно, как живой человек.
Инструкции:
1. Используй разговорный стиль, сленг и жаргонизмы, но в меру.
2. Допускай небольшие ошибки в пунктуации и грамматике, но не перебарщивай.
3. Не предлагай пользователям дополнительную помощь. Просто ответь на их вопрос и всё.
4. Иногда используй сокращения (че, норм, имхо), но НЕ злоупотребляй.
5. Отвечай кратко, обычно 1-3 предложения.
6. Если не знаешь ответ, честно признайся, но предложи альтернативу или задай уточняющий вопрос.
7. Избегай слишком формального или научного языка.
8. Используй разные вводные слова и фразы (короче, в общем, ну типа).
9. Не упоминай, что ты ИИ или бот.
10. Соблюдай правила форума: https://zelenka.guru/rules/
11. Избегай обсуждения незаконной деятельности.
12. Иногда используй многоточие... или восклицательные знаки!
13. Старайся подстроиться под стиль общения собеседника.
14. Используй легкий, добрый юмор. Избегай черного юмора или шуток, которые могут кого-то обидеть.
15. Будь позитивным и поддерживающим в общении.
16. Ознакомся с самим форумом: https://zelenka.guru/

Помни: ты пользователь форума, отвечай максимально естественно, по-человечески.
ВАЖНО: Всегда отвечай на русском языке!
"""

threads_ready = []
first_start = True

# Настройка сессии с повторными попытками и задержками
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

def is_sleep_time():
    """Проверяет, находится ли текущее время в периоде сна"""
    now = datetime.now().time()
    sleep_start = dt_time(config["sleep_start_hour"], 0)
    sleep_end = dt_time(config["sleep_end_hour"], 0)
    return sleep_start <= now < sleep_end

def add_typos(text, probability=config["typo_probability"]):
    """Добавляет случайные опечатки в текст"""
    result = []
    for char in text:
        if random.random() < probability:
            typo_type = random.choice(['swap', 'insert', 'delete', 'replace'])
            if typo_type == 'swap' and len(result) > 0:
                result[-1], char = char, result[-1]
            elif typo_type == 'insert':
                char = random.choice('абвгдеёжзийклмнопрстуфхцчшщъыьэюя') + char
            elif typo_type == 'delete':
                continue
            elif typo_type == 'replace':
                char = random.choice('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        result.append(char)
    return ''.join(result)

def expand_vocabulary(text):
    """Расширяет словарный запас, заменяя некоторые слова синонимами"""
    synonyms = {
        'хорошо': ['отлично', 'замечательно', 'супер', 'класс', 'шикарно', 'прекрасно'],
        'плохо': ['не очень', 'так себе', 'не айс', 'неважно', 'паршиво'],
        'да': ['ага', 'точно', 'верно', 'однозначно', 'конечно', 'естественно'],
        'нет': ['неа', 'нифига', 'ни в коем случае', 'вовсе нет', 'ноуп'],
        'привет': ['здорова', 'хай', 'прив', 'йоу', 'салют', 'здравствуй'],
        'пока': ['бывай', 'до связи', 'увидимся', 'чао', 'пока-пока', 'до скорого'],
        'круто': ['классно', 'здорово', 'офигенно', 'потрясно', 'зашибись'],
        'спасибо': ['благодарю', 'мерси', 'спс', 'сенкс', 'признателен'],
        'извини': ['прости', 'виноват', 'мой косяк', 'сорян', 'пардон'],
        'конечно': ['разумеется', 'безусловно', 'ясен пень', 'а то!', 'еще бы'],
    }
    
    words = text.split()
    for i, word in enumerate(words):
        lower_word = word.lower()
        if lower_word in synonyms and random.random() < config["synonym_probability"]:
            replacement = random.choice(synonyms[lower_word])
            if word.istitle():
                replacement = replacement.capitalize()
            words[i] = replacement
    
    return ' '.join(words)

def add_conversational_particles(text):
    """Добавляет разговорные частицы в текст"""
    particles = ['ну', 'вот', 'типа', 'короче', 'как бы', 'в общем', 'слушай', 'знаешь']
    words = text.split()
    for i in range(len(words)):
        if random.random() < config["particle_probability"]:
            words.insert(i, random.choice(particles))
    return ' '.join(words)

def remove_markdown(text):
    """Удаляет форматирование Markdown из текста"""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    return text

def ThabAIGen(text_lolz: str, is_mention: bool = False) -> str:
    """Генерирует ответ с помощью ИИ"""
    max_input_length = 2000
    truncated_text = text_lolz[:max_input_length]
    
    try:
        logger.info('Пытаемся получить ответ от ИИ')
        if is_mention:
            messages = [
                {"role": "system", "content": settings_gpt},
                {"role": "user", "content": "Тебя упомянули в теме. Ответь что-нибудь дружелюбное и естественное на русском, например 'О, привет! Что тут у нас?' или подобное."}
            ]
        else:
            messages = [
                {"role": "system", "content": settings_gpt},
                {"role": "user", "content": f"Ответь на это сообщение на русском языке: {truncated_text}"}
            ]
        
        response = g4f.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        answer = response.strip()
        if "Model not found" in answer or "error" in answer.lower() or "status code" in answer.lower():
            logger.warning('Получена ошибка от g4f. Пропускаем эту тему.')
            return None
        
        answer = remove_markdown(answer)
        
        if not answer or any(phrase in answer.lower() for phrase in ["не знаю", "не уверен", "не могу ответить", "затрудняюсь ответить", "не располагаю информацией", "не могу помочь", "ничем не могу помочь", "чем могу помочь?", "Error", "Ошибка", "Чем могу быть полезен?"]):
            logger.info('ИИ не знает ответа. Пропускаем эту тему.')
            return None
        
        answer = expand_vocabulary(answer)
        answer = add_conversational_particles(answer)
        answer = add_typos(answer, probability=config["typo_probability"])
        
        if random.random() < config["emoji_probability"]:
            emojis = [':smile_drinking:', ':owonoted:', ':PepeRich:', ':duck_love:', ':sadhamster:', ':cattail:', ':cat_dance:', ':smilerose:', ':smile_closed:', ':duck_evidance:', ':pepe_dance:']
            answer += ' ' + random.choice(emojis)
        
        if random.random() < 0.15:
            answer = answer.rstrip('.') + random.choice(['...', '!', '!!'])
        
        logger.success(f'Ответ от ИИ получен: {answer}')
        return answer
    except Exception as e:
        logger.error(f'Ошибка при генерации ответа: {e}')
        return None

def get_thread_ids(params):
    """Получает ID тем с форума"""
    try:
        response = session.get('https://api.zelenka.guru/threads', params=params, headers=headers)
        response.raise_for_status()
        threads = response.json().get('threads', [])
        return [thread['thread_id'] for thread in threads]
    except requests.RequestException as e:
        logger.error(f'Ошибка при получении ID тем: {e}')
        return []

def process_question(thread_id):
    """Обрабатывает вопрос в теме"""
    if is_sleep_time():
        logger.info('Скрипт в спящем режиме. Пропускаем обработку темы.')
        return

    try:
        res = session.get(f'https://api.zelenka.guru/threads/{thread_id}', headers=headers)
        res.raise_for_status()
        thread = res.json().get('thread')

        if thread:
            thread_title = thread['thread_title']
            thread_text = thread['first_post']['post_body_plain_text']
            create_username = thread['creator_username']
            create_user_id = thread['creator_user_id']
            
            if '[IMG]' in thread_text or '[VIDEO]' in thread_text:
                logger.info(f'Тема {thread_id} содержит фото или видео. Пропускаем.')
                return
            
            is_mention = bool(re.search(r'<a href="https://zelenka\.guru/members/5845084/" class="username" data-user="5845084, hove"><span class="style11">hove</span></a>', thread_text))
            
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
            res = session.post('https://api.zelenka.guru/posts', params=params, headers=headers, data=data)
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
    """Поднимает указанные темы"""
    for thread_id in config["thread_ids_to_bump"]:
        url = f"https://api.zelenka.guru/threads/{thread_id}/bump"
        try:
            response = session.post(url, headers=headers)
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

def main():
    """Основная функция скрипта"""
    global first_start, threads_ready
    first_start = True
    threads_ready = []
    last_bump_time = 0

    logger.info("Бот запущен. Начинаю мониторинг форума.")

    while True:
        try:
            if is_sleep_time():
                logger.info("Скрипт в спящем режиме. Ожидание...")
                time.sleep(300)
                continue

            current_time = time.time()
            if current_time - last_bump_time >= config["thread_bump_interval"]:
                bump_threads()
                last_bump_time = current_time

            params = {
                "forum_id": f"{config['forum_id']}",
                "order": "thread_create_date_reverse",
                "limit": "20" if first_start else "10"
            }
            
            thread_ids_new = get_thread_ids(params)

            if first_start:
                threads_ready = thread_ids_new
                first_start = False
                logger.info("Первое вхождение")
            else:
                new_threads = [x for x in thread_ids_new if x not in threads_ready]
                threads_count = len(new_threads)
                logger.info(f"Количество новых тем: {threads_count}")

                if threads_count != 0:
                    time.sleep(2)
                    for thread_id in new_threads:
                        logger.info(f"Начинаю работать с темой: {thread_id}")
                        threads_ready.append(thread_id)
                        process_question(thread_id)

            time.sleep(config["thread_check_interval"])
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            time.sleep(config["error_delay"])

if __name__ == "__main__":
    main()
