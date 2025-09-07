import random
import re
from config.settings import config

def add_typos(text, probability=config["typo_probability"]):
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
    particles = ['ну', 'вот', 'типа', 'короче', 'как бы', 'в общем', 'слушай', 'знаешь']
    words = text.split()
    for i in range(len(words)):
        if random.random() < config["particle_probability"]:
            words.insert(i, random.choice(particles))
    return ' '.join(words)

def remove_markdown(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    return text
