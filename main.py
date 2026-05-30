import time
from collections import deque
from loguru import logger
from config.settings import config
from utils.logger import setup_logger
from utils.time_utils import is_sleep_time
from api.forum_client import get_thread_ids, process_question, bump_threads

def remember_thread_id(seen_queue, seen_set, thread_id):
    if thread_id in seen_set:
        return
    if len(seen_queue) == seen_queue.maxlen:
        seen_set.discard(seen_queue[0])
    seen_queue.append(thread_id)
    seen_set.add(thread_id)

def main():
    setup_logger()
    
    first_start = True
    threads_ready = deque(maxlen=config["processed_threads_limit"])
    threads_ready_set = set()
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
                for thread_id in thread_ids_new:
                    remember_thread_id(threads_ready, threads_ready_set, thread_id)
                first_start = False
                logger.info("Первое вхождение")
            else:
                new_threads = [x for x in thread_ids_new if x not in threads_ready_set]
                threads_count = len(new_threads)
                logger.info(f"Количество новых тем: {threads_count}")

                if threads_count != 0:
                    time.sleep(2)
                    for thread_id in new_threads:
                        logger.info(f"Начинаю работать с темой: {thread_id}")
                        remember_thread_id(threads_ready, threads_ready_set, thread_id)
                        process_question(thread_id)

            time.sleep(config["thread_check_interval"])
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            time.sleep(config["error_delay"])

if __name__ == "__main__":
    main()
