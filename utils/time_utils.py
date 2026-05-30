from datetime import datetime, time as dt_time
from config.settings import config

def is_sleep_time_at(current_time, sleep_start_hour, sleep_end_hour):
    sleep_start = dt_time(sleep_start_hour, 0)
    sleep_end = dt_time(sleep_end_hour, 0)
    if sleep_start == sleep_end:
        return False
    if sleep_start < sleep_end:
        return sleep_start <= current_time < sleep_end
    return current_time >= sleep_start or current_time < sleep_end

def is_sleep_time():
    now = datetime.now().time()
    return is_sleep_time_at(now, config["sleep_start_hour"], config["sleep_end_hour"])
