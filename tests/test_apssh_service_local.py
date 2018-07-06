import util
from asynciojobs import Scheduler
from apssh import SshJob, LocalNode, Run
import glob
from time import sleep

def test_service_on_local_node(time):
    scheduler = Scheduler()
    local_node = LocalNode()
    command = Run("sleep {}".format(10*time), service=True)
    SshJob(node=local_node, scheduler=scheduler,
           forever=True, command=command)
    SshJob(node=local_node, scheduler=scheduler,
           command=Run("echo \"toto\"; sleep {}".format(time)))
    scheduler.run()
    scheduler.shutdown()
    sleep(1)
    file_list = glob.glob("./apssh_spid_*")
    if len(file_list) > 0:
        for file in file_list:
            pid = util.get_pid_from_apssh_file(file)
            if util.pid_is_alive(pid):
                print("ZOMBIEEEEEEEEEEEEEEEE")
                #break


test_service_on_local_node(4)
