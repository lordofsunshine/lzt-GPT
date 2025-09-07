from datetime import datetime, time as dt_time
from config.settings import config

def is_sleep_time():
    now = datetime.now().time()
    sleep_start = dt_time(config["sleep_start_hour"], 0)
    sleep_end = dt_time(config["sleep_end_hour"], 0)
    return sleep_start <= now < sleep_end
