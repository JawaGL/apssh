#!/usr/bin/env python3


# for using the develop branch of asyncssh
#import sys
#sys.path.insert(0, "../../asyncssh/")

import os, os.path
import time
import argparse
import asyncio

from .config import default_time_name, default_timeout, default_username, default_private_key, default_remote_workdir
from .sshproxy import SshProxy
from .formatters import RawFormatter, ColonFormatter, SubdirFormatter
from .window import gather_window
from .util import print_stderr
from .version import version as apssh_version

class Apssh:
    """
    Main class for apssh utility
    """

    def __init__(self):
        self.proxies = []
        self.formatter = None

    def __repr__(self):
        return "".join([str(p) for p in self.proxies])

    def analyze_target(self, target, debug=False):
        """
        A target can be specified as either
        * a filename
          If the provided filename exists and could be parsed, returned object will be
            True, [ hostname1, ...]
        * a directory name
          This is for use together with the --mark option, so that one can easily select reachable nodes only, 
          or just as easily exclude failing nodes
          all the simple files that are found immediately under the specified directory are taken as hostnames
          XXX it would make sense to check there is at least one dot in their name, but I'm not sure about that yet
          Here again if things work out we return
            True, [ hostname1, ...]
        * otherwise
          the target is then expected a string passed to -t on the command line,
          so it is simply split according to white spaces before being returned as
            True, [ hostname1, ...]
        * If anything goes wrong, return code is 
            False, []
          e.g. the file exists but cannot be parsed
          not sure this truly is useful
        """
        names = []
        if os.path.exists(target):
            if os.path.isdir(target):
    # directory
                onlyfiles = [ f for f in os.listdir(target)
                              if os.path.isfile(os.path.join(target, f))]
                return True, onlyfiles
            else:
    # file
                try:
                    with open(target) as input:
                        for line in input:
                            line = line.strip()
                            if line.startswith('#'):
                                continue
                            line = line.split()
                            for token in line:
                                names += token.split()
                    return True, names
                except FileNotFoundError as e:
                    return False, None
                except Exception as e:
                    print_stderr("Unexpected exception when parsing file {}, {}".format(target, e))
                    if debug:
                        import traceback
                        traceback.print_exc()
                    return False, None
        else:
            # string
            return True, target.split()

    # create tuples username, hostname
    # use the username if already present in the target,
    # otherwise the one specified with --username
    def user_host(self, target):
        try:
            user, hostname = target.split('@')
            return user, hostname
        except:
            return self.parsed_args.username, target

    def create_proxies(self, gateway):
        # start with parsing excludes if any
        excludes = set()
        for exclude in self.parsed_args.excludes:
            parsed, cli_excludes = self.analyze_target(exclude)
            excludes.update(cli_excludes)
        if self.parsed_args.dry_run:
            print("========== {} excludes found:".format(len(excludes)))
            for exclude in excludes:
                  print(exclude)

        # gather targets as mentioned in -t -x args
        hostnames = []
        actually_excluded = 0
        # read input file(s)
        for target in self.parsed_args.targets:
            parsed, cli_targets = self.analyze_target(target)
            for target in cli_targets:
                if target not in excludes:
                    hostnames.append(target)
                else:
                    actually_excluded += 1
        if not hostnames:
            self.parser.print_help()
            exit(1)

        if self.parsed_args.dry_run:
            print("========== {} hostnames selected ({} excluded):"
                  .format(len(hostnames), actually_excluded))
            for hostname in hostnames:
                print(hostname)
            exit(0)

        # create proxies
        self.proxies = [ SshProxy(hostname, username=username,
                                  client_keys=self.parsed_args.private_keys,
                                  gateway = gateway,
                                  formatter = self.get_formatter(),
                                  timeout = self.parsed_args.timeout,
                                  debug = self.parsed_args.debug)
                         for username, hostname in  (self.user_host(target) for target in hostnames) ]
        return self.proxies

    def get_formatter(self):
        if self.formatter is None:
            if self.parsed_args.raw_output:
                self.formatter = RawFormatter(debug = self.parsed_args.debug)
            elif self.parsed_args.date_time:
                run_name = default_time_name
                self.formatter = SubdirFormatter(run_name)
            elif self.parsed_args.out_dir:
                self.formatter = SubdirFormatter(self.parsed_args.out_dir)
            else:
                self.formatter = ColonFormatter()
        return self.formatter
    
    def main(self):
        self.parser = parser = argparse.ArgumentParser()
        # scope - on what hosts
        parser.add_argument("-t", "--target", dest='targets', action='append', default=[],
                            help="""
                            specify targets (additive); each target can be either 
                              * a space-separated list of hostnames
                              * the name of a file containing hostnames
                              * the name of a directory containing files named after hostnames; 
                                see e.g. the --mark option
                            """)
        parser.add_argument("-x", "--exclude", dest='excludes', action='append', default=[],
                            help="""
                            like --target, but for specifying exclusions; 
                            for now there no wildcard mechanism is supported here;
                            also the order in which --target and --exclude options are mentioned does not matter;
                            use --dry-run to only check for the list of applicable hosts
                            """)
        # global settings
        parser.add_argument("-w", "--window", type=int, default=0,
                            help="specify how many connections can run simultaneously; default is no limit")
        parser.add_argument("-c", "--connect-timeout", dest='timeout',
                            type=float, default=default_timeout,
                            help="specify connection timeout, default is {}s".format(default_timeout))
        # ssh settings
        parser.add_argument("-u", "--username", default=default_username,
                            help="remote user name - default is {}".format(default_username))
        parser.add_argument("-i", "--private-keys",
                            default=[default_private_key], action='append', type=str,
                            help="specify private key file(s) - additive - default is to use {}"
                            .format(default_private_key))
        parser.add_argument("-g", "--gateway", default=None,
                            help="specify a gateway for 2-hops ssh - either hostname or username@hostname")
        # how to store results
        # xxx here xxx parser.add_argument()
        parser.add_argument("-o", "--out-dir", default=None,
                            help="specify directory where to store results")
        parser.add_argument("-d", "--date-time", default=None, action='store_true',
                            help="use date-based directory to store results")
        parser.add_argument("-r", "--raw-output", default=None, action='store_true',
                            help="produce raw result")
        parser.add_argument("-m", "--mark", default=False, action='store_true',
                            help="""
                            available with the -d and -o options only.

                            When specified, then for all nodes there will be a file created
                            in the output subdir, named either 0ok/<hostname> for successful nodes,
                            or 1failed/<hostname> for the other ones.
                            This mark file will contain a single line with the returned code, or 'None'
                            if the node was not reachable at all""")
        parser.add_argument("-s", "--script", action='store_true', default=False,
                            help="""If this flag is present, the first element of the remote command 
                            is assumed to be the name of a local script, that will be copied over
                            before being executed remotely.
                            In this case it should be executable.
                            On the remote boxes it will be installed and run in the {} directory.
                            """.format(default_remote_workdir))

        
        # turn on debugging
        parser.add_argument("-D", "--debug", action='store_true', default=False)
        parser.add_argument("-n", "--dry-run", default=False, action='store_true',
                            help="Only show details on selected hostnames")
        parser.add_argument("-V", "--version", action='store_true', default=False)

        # the commands to run
        parser.add_argument("commands", nargs=argparse.REMAINDER, type=str,
                            help="""
                            command to run remotely. If that command itself contains options,
                            it is a good practice to insert `--`
                            before the actual command.  

                            If the -s or --script option is provided, the first
                            argument here should denote a (typically script) file
                            **that must exist** on the local filesystem. This script is then copied
                            over remotely and serves as the command for the remote execution""")

        args = self.parsed_args = parser.parse_args()

        ### helpers
        if args.version:
            print("apssh version {}".format(apssh_version))
            exit(1)

        ### manual check for REMAINDER
        if not args.commands:
            print("You must provide a command to be run remotely")
            parser.print_help()
            exit(1)

        ### initialize a gateway proxy if --gateway is specified
        gateway = None
        if args.gateway:
            gwuser, gwhost = self.user_host(args.gateway)
            gateway = SshProxy(gwhost, username=gwuser,
                               client_keys = self.parsed_args.private_keys,
                               formatter = self.get_formatter(),
                               timeout = self.parsed_args.timeout,
                               debug = self.parsed_args.debug)

        proxies = self.create_proxies(gateway)

        if not args.script:
            command = " ".join(args.commands)
            tasks = [ proxy.connect_and_run(command) for proxy in proxies ]
        else:
            ### an executable is provided on the command line
            script, args = args.commands[0], args.commands[1:]
            if not os.path.exists(script):
                print("File not found {}".format(script))
                parser.print_help()
                exit(1)
            # xxx could also check it's executable
            
            # in this case a first pass is required to push the code
            tasks = [ proxy.connect_put_and_run(script, *args) for proxy in proxies ]


        loop = asyncio.get_event_loop()
        window = self.parsed_args.window
        if not window:
            if self.parsed_args.debug:
                print("No window limit")
            results = loop.run_until_complete(asyncio.gather(*tasks))
        else:
            if self.parsed_args.debug:
                print("Window limit={}".format(window))
            results = loop.run_until_complete(gather_window(*tasks, window=window,
                                                            debug=args.debug))

        ### print on stdout the name of the output directory
        # useful mostly with -d : 
        subdir = self.get_formatter().run_name \
                 if isinstance(self.get_formatter(), SubdirFormatter) \
                    else None
        if subdir:
            print(subdir)
        ### details on the individual retcods
        # raw
        if self.parsed_args.debug:
            for p, s in zip(proxies, results):
                print("PROXY {} -> {}".format(p.hostname, s))
        # marks
        names = { 0 : '0ok', None : '1failed'}
        if subdir and self.parsed_args.mark:
            # do we need to create the subdirs
            need_ok = [s for s in results if s==0]
            if need_ok:
                os.makedirs("{}/{}".format(subdir, names[0]), exist_ok=True)
            need_fail = [s for s in results if s!=0]
            if need_fail:
                os.makedirs("{}/{}".format(subdir, names[None]), exist_ok=True)
                                          
            for p, s in zip(proxies, results):
                prefix = names[0] if s == 0 else names[None]
                with open(os.path.join(subdir,"{}/{}".format(prefix, p.hostname)), "w") as mark:
                    mark.write("{}\n".format(s))

        # return 0 only if all hosts have returned 0
        # otherwise, return 1
        failures = [ r for r in results if r != 0 ]
        overall = 0 if len(failures) == 0 else 1
        return overall

