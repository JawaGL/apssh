import os
import asyncio

import apssh
import .util

def test_service_local(time):
    async def run_service(time, event):
        local_node = apssh.LocalNode()

        command = "echo \"$$\" > .apssh/apssh_spid_11;echo \"$$\" > .apssh/apssh_spid_1; sleep {}".format(10*time)
        print("Running service")
        await asyncio.wait([local_node.run(command, command_id="11")], timeout=time)
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
    loop.create_task(run_service(time, event))
    loop.run_until_complete(check_alive(event))

test_service_local(4)
