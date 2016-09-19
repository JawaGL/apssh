#!/usr/bin/env python3

import unittest

#import asyncio

from apssh.keys import *

class Tests(unittest.TestCase):

    def test_import(self):

        test_names = [ 'id_rsa', 'id-pass' ]

        for test_name in test_names:
            path = os.path.expanduser("~/.ssh/{}".format(test_name))
            print("========== importing key from {}".format(path))
            sshkey = import_private_key(path)
            print("-> got {}".format(sshkey))

    def test_agent(self):
#        loop = asyncio.get_event_loop()
        
        for key in load_agent_keys():
            print("Found in agent: {}".format(key))


unittest.main()            
