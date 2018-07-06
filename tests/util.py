# pylint: disable=c0111

import asyncio

from pathlib import Path

from asynciojobs import Watch, Job, Scheduler

import subprocess

import os

def produce_png(scheduler, name):
    dot = scheduler.graph()
    dot.format = 'png'

    tests_dir = Path('tests')
    if tests_dir.exists():
        actual_name = str(tests_dir / name)
    else:
        actual_name = name
    dot.render(actual_name)
    print(f"png file produced in {actual_name}{{,.png}}")

def check_pid_alive(pid):
    with open(os.devnull, 'w') as devnull:
        ret = subprocess.run(["kill", "-0", "{}".format(pid)], stdout=devnull,
                             stderr=devnull).returncode
        return ret

def get_pid_from_apssh_file(filename):
    with Path(filename).open() as file:
        data = file.readline()
        try:
            ret = int(data)
        except ValueError:
            ret = -1
        return ret

def rm_file(filepath):
    os.remove(filepath)
