#!/usr/bin/env python3

import os, os.path
import time
from argparse import ArgumentParser
import asyncio

from sshproxy import SshProxy
from formatters import RawFormatter, ColonFormatter, SubdirFormatter

default_username = os.getlogin()
default_private_key = os.path.expanduser("~/.ssh/id_rsa")

class Apssh:
    """
    Main class for apssh utility
    """

    def __init__(self):
        self.proxies = []
        self.formatter = None

    def __repr__(self):
        return "".join([str(p) for p in self.proxies])

    def create_proxies(self):
        # gather targets as mentioned in files and on the command line
        # always assume they can be comma-separated
        targets = []
        # read input file(s)
        if self.parsed_args.targets_files:
            for targets_file in self.parsed_args.targets_files:
                try:
                    with open(targets_file) as input:
                        for line in input:
                            line = line.strip()
                            if line.startswith('#'): continue
                            line = line.split()
                            for token in line:
                                targets += token.split(',')
                except IOError as e:
                    print("Could not open file {} - aborting".format(self.targets_files))
        # add command line targets
        for target in self.parsed_args.targets:
            targets += target.split(',')

        # create tuples username, hostname
        # use the username if already present in the target,
        # otherwise the one specified with --username
        def user_host(target):
            try:
                user, hostname = target.split('@')
                return user, hostname
            except:
                return self.parsed_args.username, target

        # create proxies
        self.proxies = [ SshProxy(hostname, username=username,
                                  client_keys=self.parsed_args.private_keys,
                                  formatter = self.get_formatter())
                         for username, hostname in  (user_host(target) for target in targets) ]
        return self.proxies

    def get_formatter(self):
        if self.formatter is None:
            if self.parsed_args.raw_output:
                self.formatter = RawFormatter()
            elif self.parsed_args.date_time:
                default_run_name = time.strftime("%Y-%m-%d@%H:%M")
                self.formatter = SubdirFormatter(default_run_name)
            elif self.parsed_args.out_dir:
                self.formatter = SubdirFormatter(self.parsed_args.out_dir)
            else:
                self.formatter = ColonFormatter()
        return self.formatter
    
    def main(self):
        parser = ArgumentParser()
        # scope - on what hosts
        parser.add_argument("-f", "--targets-file", dest='targets_files',
                            default=[], action='append', type=str,
                            help="Specify files that contain a list of target hosts - additive")
        parser.add_argument("-t", "--target", dest='targets',
                            default=[], action='append', type=str,
                            help="comma-separated list of target hosts - additive")
        # ssh settings
        parser.add_argument("-u", "--username", default=default_username,
                            help="remote user name - default is {}".format(default_username))
        parser.add_argument("-i", "--private-keys",
                            default=[default_private_key], action='append', type=str,
                            help="specify private key file(s) - additive - default is to use {}"
                            .format(default_private_key))
        # how to store results
        # xxx here xxx parser.add_argument()
        parser.add_argument("-o", "--out-dir", default=None,
                            help="specify directory where to store results")
        parser.add_argument("-d", "--date-time", default=None, action='store_true',
                            help="use date-based directory to store results")
        parser.add_argument("-r", "--raw-output", default=None, action='store_true',
                            help="produce raw result")
        
        # the commands to run
        parser.add_argument("commands", nargs='+', type=str,
                            help="command to run remotely")

        args = self.parsed_args = parser.parse_args()
        proxies = self.create_proxies()
#        print(self)
        command = " ".join(args.commands)
        tasks = [ proxy.connect_and_run(command) for proxy in proxies ]

        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(asyncio.gather(*tasks))

        # xxx how can we return something more useful
        return 0

if __name__ == '__main__':
    exit(Apssh().main())
