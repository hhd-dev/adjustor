from .amd_cpu import get_online_cpus
import os
import logging

logger = logging.getLogger(__name__)

POWER_GOVERNOR_PATH='/sys/devices/system/cpu/cpu{cpu_num}/cpufreq/scaling_governor'
POWER_GOVERNOR_OPTIONS_PATH='/sys/devices/system/cpu/cpu{cpu_num}/cpufreq/scaling_available_governors'

def set_power_governor(cpu_num, option):
    try:
        path = POWER_GOVERNOR_PATH.format(cpu_num=cpu_num)
        if os.path.exists(path):
            with open(path, 'wb') as file:
                file.write(option)
                file.close()
                return True
    except Exception as e:
        logger.error(f'{__name__} error setting power governor {e}')
    return False

def get_available_governor_options(cpu_num):
    try:
        path = POWER_GOVERNOR_OPTIONS_PATH.format(cpu_num=cpu_num)
        if os.path.exists(path):
            with open(path, 'r') as file:
                available_options = file.read().strip().split(' ') or []
                file.close()
                return available_options
    except Exception as e:
        logger.error(f'{__name__} error getting power governor options {e}')

    return []

def get_power_governor_option_paths():
    cpu_nums = get_online_cpus()

    power_governor_option_paths = list(map(
        lambda cpu_num: POWER_GOVERNOR_OPTIONS_PATH.format(cpu_num=cpu_num),
        cpu_nums
    ))

    return power_governor_option_paths

def get_power_governor_paths():
    cpu_nums = get_online_cpus()

    power_governor_paths = list(map(
        lambda cpu_num: POWER_GOVERNOR_PATH.format(cpu_num=cpu_num),
        cpu_nums
    ))

    return power_governor_paths