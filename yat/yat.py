#!/usr/bin/env python
#-*- coding:utf-8 -*-

u"""
Very simple command line todolist manager
"""

import inspect
import locale
import os
import re
import sys

class Command:
    u"""Abstract class for instrospection
    
If you wish to add a command, you have to create a class that derive from this
one, and the docstring must have this format:
Short description

usage: %s cmd_name [options]

Long description
"""
    
    alias = []
    u"""Array containing the different aliases for this command"""

    def execute(self,args):
        u"""Method actually doing something"""
        raise NotImplementedError

    pass

class HelpCommand (Command):
    u"""Show this help or a command specific help if an argument is provided

usage: %s help [command]

Without arguments, provide a short description of the differents commands. If
the name of a command is provided, show the specific help text for this command.
"""

    alias = [u"help"]

    def execute(self,args):
        global progname, aliases, commands

        detailed = False
        cmd = self

        if len(args) > 0:
            if args[0] in aliases:
                cmd = aliases[args[0]]()
                detailed = True

        helptxt = cmd.__doc__.split('\n\n', 1)

        if detailed:
            output(helptxt[1] % progname)

        if cmd.alias[0] == u"help":
            if not detailed:
                output(str = (u"%s (Yet Another Todolist) is a very simple " %
                    progname), linebreak = False)
                output(u"commandline todolist manager.")
                output()
                output(u"usage: %s [command] [arguments]" % progname)
                output()

            output(u"The different commands are:")
            for name, cmd in commands.iteritems():
                output(u"\t", linebreak = False)
                output(cmd.alias[0], linebreak = False)
                output(u"\t", linebreak = False)
                output(cmd.__doc__.split('\n',1)[0], linebreak = False)
                if len(cmd.alias) > 1:
                    output(u" (alias: ", linebreak = False)
                    for i in range(1, len(cmd.alias)):
                        output(cmd.alias[i], linebreak = False)
                        if i < len(cmd.alias) - 1: 
                            output(u",", linebreak = False)
                    output(u")", linebreak = False)
                output()
            output()
            output(u"Please type \"%s help [command]\" to have" % progname, 
                    linebreak = False)
            output(u" detailed informations on a specific command")

        output()
        pass
    pass

class AddCommand (Command):
    u"""Add a task, a list or a tag

usage: %s add [task | list | tag] <informations>
"""
    
    alias = [u"add"]

    def execute(self,args):
        # TODO
        print self.__doc__.split('\n',1)[0]," ",args
        pass
    pass

class RemoveCommand (Command):
    u"""Remove a task, a list or a tag

usage: %s remove [task | list | tag] <informations>
"""

    alias = [u"remove", u"rm"]

    def execute(self,args):
        # TODO
        print self.__doc__.split('\n',1)[0]," ",args
        pass
    pass

class ListCommand (Command):
    u"""List the current tasks

usage: %s list
"""

    alias = [u"list", u"show"]

    def execute(self,args):
        # TODO
        print self.__doc__.split('\n',1)[0]," ",args
        pass
    pass


def init():
    u"""Initialisation of the program
    - loading user preferences
    - initialising database access
    - initializing some global vars
    """
    global enc, out, config

    # Default encoding
    enc = locale.getpreferredencoding()

    # Default output : stdout
    out = sys.stdout

    # Loading configuration
    config = {}
    try:
        with open(os.environ.get("HOME") + "/.yatrc", "r") as config_file:
            for line in config_file:
                if not (re.match(r'^\s*#.*$', line) or re.match(r'^\s*$', line)):
                    line = re.sub(r'\s*=\s*', "=", line, 1)
                    line = re.sub(r'\n$', r'', line)
                    opt = line.split('=', 1)
                    config[opt[0]] = opt[1]
        config_file.close()
    except IOError:
        # No .yatrc
        pass

    # For each option, loading default if it isn't defined
    config["yatdir"] = config.get("yatdir", "~/.yat")
    config["default_list"] = config.get("default_list", "nolist")
    config["default_tag"] = config.get("default_tag", "notag")

    # Create yat directory
    if config["yatdir"][0] == "~":
        config["yatdir"] = os.environ.get("HOME") + config["yatdir"][1:]
    if not os.path.isdir(config["yatdir"]):
        os.makedirs(config["yatdir"], mode=0700)
    print config
    pass

def isCommand(obj):
    u"""Check if the parameter is a class derived from Command, without being
    Command"""

    if inspect.isclass(obj):
        return (issubclass(obj, Command) and not(obj is Command))
    else:
        return False

def output(st = u"", f = None, linebreak = True):
    global enc, out
    if f == None:
        f = out
    f.write(st.encode(enc))
    if linebreak:
        f.write(os.linesep)

def main(argv):
    u"""
    Entry point of the program
    """
    global commands, aliases, progname

    # Initialisation
    init()

    # Getting the name of the program
    progname = argv[0]

    # Getting all the commands
    commands = dict(inspect.getmembers(sys.modules[__name__], isCommand))
    aliases = {}

    # Fill the aliases dictionnary
    for name, cmd in commands.iteritems():
        for a in cmd.alias:
            aliases[a] = cmd

    # Determining which command to use (default list)
    cmd = ListCommand()
    cmd_args = []
    if len(argv) > 1:
        if argv[1] in aliases:
            cmd = aliases[argv[1]]()
            cmd_args = argv[2:]
        else:
            cmd = AddCommand()
            cmd_args = argv[1:]

    # Executing command with the rest of the arguments
    cmd.execute(cmd_args)

if __name__ == "__main__":
    main(sys.argv)
