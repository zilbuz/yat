#!/usr/bin/env python
#-*- coding:utf-8 -*-

u"""
Very simple command line todolist manager
"""

import inspect
import locale
import os
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
    global enc, out
    enc = locale.getpreferredencoding()
    out = sys.stdout
    pass

def isCommand(obj):
    u"""Check if the parameter is a class derived from Command, without being
    Command"""

    if inspect.isclass(obj):
        return (issubclass(obj, Command) and not(obj is Command))
    else:
        return False

def output(str = u"", f = None, linebreak = True):
    global enc, out
    if f == None:
        f = out
    f.write(str.encode(enc))
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
