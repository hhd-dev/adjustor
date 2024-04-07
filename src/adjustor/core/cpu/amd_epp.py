from .amd_cpu import get_online_cpus
import logging
import os

logger = logging.getLogger(__name__)

EPP_PATH = '/sys/devices/system/cpu/cpu{cpu_num}/cpufreq/energy_performance_preference'
EPP_OPTIONS_PATH = '/sys/devices/system/cpu/cpu{cpu_num}/cpufreq/energy_performance_available_preferences'

def get_available_epp_options(cpu_num):
    try:
        options_path = EPP_OPTIONS_PATH.format(cpu_num=cpu_num)
        if os.path.exists(options_path):
            with open(options_path, 'r') as file:
                available_options = file.read().strip().split(' ') or []
                file.close()
                return available_options
    except Exception as e:
        logger.error(f'{__name__} error getting epp options {e}')

    return []

def set_epp(cpu_num, epp_option):
    try:
        if epp_option not in get_available_epp_options(cpu_num):
            return False
        path = EPP_PATH.format(cpu_num=cpu_num)
        if os.path.exists(path):
            with open(path, 'wb') as file:
                file.write(epp_option)
                file.close()
                return True
    except Exception as e:
        logger.error(f'{__name__} error setting epp {e}')
    return False

def get_epp_paths():
    cpu_nums = get_online_cpus()

    epp_paths = list(map(
        lambda cpu_num: EPP_PATH.format(cpu_num=cpu_num),
        cpu_nums
    ))

    return epp_paths

def get_epp_option_paths():
    cpu_nums = get_online_cpus()

    epp_options_paths = list(map(
        lambda cpu_num: EPP_OPTIONS_PATH.format(cpu_num=cpu_num),
        cpu_nums
    ))

    return epp_options_paths