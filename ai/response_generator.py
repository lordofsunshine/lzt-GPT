import random
import re
import g4f
from loguru import logger
from config.settings import settings_gpt, config
from utils.text_processor import remove_markdown, expand_vocabulary, add_conversational_particles, add_typos

def ThabAIGen(text_lolz: str, is_mention: bool = False) -> str:
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
