import os
import glob
import time
import asyncio

from asynciojobs import Scheduler
from apssh import SshJob, LocalNode, Run

import tests.util as util

import unittest

class Tests(unittest.TestCase):

    # formerly in test_zombie_local.py
    def test_zombie_local(self, timeout=2):
        async def run_service(timeout, event):
            local_node = LocalNode()

            command = "echo \"$$\" > .apssh/apssh_spid_11;echo \"$$\" > .apssh/apssh_spid_1; sleep {}".format(10*timeout)
            print("Running service")
            await asyncio.wait([local_node.run(command, command_id="11")], timeout=timeout)
            print("Shutdown service")
            await local_node.shutdown("11")
            await asyncio.sleep(1)
            event.set()

        async def check_alive(event):
            await event.wait()
            pid = util.get_pid_from_apssh_file(".apssh/apssh_spid_1")
            alive = util.pid_is_alive(pid)
            os.remove(".apssh/apssh_spid_1")
            if not alive:
                print("OK service dead")
            else:
                print("NOK service running")

        loop = asyncio.get_event_loop()
        event = asyncio.Event()
        loop.create_task(run_service(timeout, event))
        loop.run_until_complete(check_alive(event))


    # formerly in test_apssh_service_local.py
    def test_service_local(self, timeout=2):
        scheduler = Scheduler()
        local_node = LocalNode()
        command = Run("sleep {}".format(10*timeout), service=True)
        SshJob(node=local_node, scheduler=scheduler,
               forever=True, command=command)
        SshJob(node=local_node, scheduler=scheduler,
               command=Run("echo \"toto\"; sleep {}".format(timeout)))
        scheduler.run()
        scheduler.shutdown()
        time.sleep(1)
        file_list = glob.glob("./apssh_spid_*")
        if len(file_list) > 0:
            for file in file_list:
                pid = util.get_pid_from_apssh_file(file)
                if util.pid_is_alive(pid):
                    print("ZOMBIEEEEEEEEEEEEEEEE")
                #break


if __name__ == '__main__':
    test_service_local(4)
