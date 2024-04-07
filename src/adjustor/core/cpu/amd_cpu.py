from enum import Enum
import os
import re
import logging

logger = logging.getLogger(__name__)

AMD_PSTATE_PATH="/sys/devices/system/cpu/amd_pstate/status"
AMD_SMT_PATH="/sys/devices/system/cpu/smt/control"

BOOST_PATH="/sys/devices/system/cpu/cpufreq/boost"
PSTATE_BOOST_PATH="/sys/devices/system/cpu/amd_pstate/cpb_boost"

CPU_ONLINE_PATH='/sys/devices/system/cpu/cpu{cpu_id}/online'

def supports_smt():
    try:
        if os.path.exists(AMD_SMT_PATH):
            return True
    except Exception as e:
        logger.error(e)
        return False
    return False

def supports_cpu_boost():
    if os.path.exists(PSTATE_BOOST_PATH) or os.path.exists(BOOST_PATH):
        return True
    return False

def set_cpu_boost(enabled = True):
    try:
        if os.path.exists(PSTATE_BOOST_PATH):
            with open(PSTATE_BOOST_PATH, 'w') as file:
                if enabled:
                    file.write('1')
                else:
                    file.write('0')
                file.close()
                return True
        if os.path.exists(BOOST_PATH):
            with open(BOOST_PATH, 'w') as file:
                if enabled:
                    file.write('1')
                else:
                    file.write('0')
                file.close()
                return True
    except Exception as e:
        logger.error(e)
        return False
    return False

def set_smt(enabled = True):
    if not supports_smt():
        return False
    try:
        with open(AMD_SMT_PATH, 'w') as file:
            if enabled:
                file.write('on')
            else:
                file.write('off')
            file.close()
        return True
    except Exception as e:
        logging.error(e)
        return False

def check_cpu_online(cpu_id: int):
        cpu_path = CPU_ONLINE_PATH.format(cpu_id=cpu_id)
        if os.path.exists(cpu_path):
            with open(cpu_path, 'r') as f:
                status = f.read().strip()
                return status == '1'
        else:
            return False

def get_online_cpus():
    online_cpus = ['0']
    cpu_path = '/sys/devices/system/cpu/'
    cpu_pattern = re.compile(r'^cpu(\d+)$')

    for cpu_dir in os.listdir(cpu_path):
        match = cpu_pattern.match(cpu_dir)
        if match:
            cpu_id = match.group(1)
            if check_cpu_online(cpu_id):
                online_cpus.append(cpu_id)
    return online_cpus
