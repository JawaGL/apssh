from apssh import SshNode, SshJob, Run, CaptureFormatter, TerminalFormatter

from asynciojobs import Scheduler

import unittest

class Tests(unittest.TestCase):

    def test_capture(self):

        s = Scheduler()
        f = CaptureFormatter()
        n = SshNode('faraday.inria.fr', username='root', formatter=f)
        s.add(
            SshJob(
                node=n,
                commands=[
                    Run("echo LINE1"),
                    Run("echo LINE2"),
                    ])
        )

        f.start_capture()
        s.run()
        captured = f.get_capture()

        expected = "LINE1\nLINE2\n"
        self.assertEqual(captured, expected)

    # for visual test for now
    def test_format(self):
        s = Scheduler()
        f = TerminalFormatter("%Y:%H:%S - @host@:@line@",
                              verbose=True)
        n = SshNode('faraday.inria.fr', username='root', formatter=f)
        s.add(SshJob(node=n, commands=[ Run("echo LINE1"), Run("echo LINE2")]))
        s.run()