#!/usr/bin/env python
#-*- coding:utf-8 -*-

u"""
Very simple command line todolist manager
"""

import sys
import inspect

class Command:
    u"""Abstract class for instrospection
    
If you wish to add a command, you have to create a class that derive from this
one, and the docstring must have this format:
Short description

%s cmd_name [options]

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

%s help [command]

Without arguments, provide a short description of the differents commands. If
the name of a command is provided, show the specific help text for this command.
"""

    alias = ["help"]

    def execute(self,args):
        global progname
        # TODO
        print self.__doc__.split('\n\n',1)[1] % progname
        pass
    pass

class AddCommand (Command):
    u"""Add a task, a list or a tag

%s add [task | list | tag] <informations>
"""
    
    alias = ["add"]

    def execute(self,args):
        # TODO
        print self.__doc__.split('\n',1)[0]," ",args
        pass
    pass

class RemoveCommand (Command):
    u"""Remove a task, a list or a tag

%s remove [task | list | tag] <informations>
"""

    alias = ["remove", "rm"]

    def execute(self,args):
        # TODO
        print self.__doc__.split('\n',1)[0]," ",args
        pass
    pass

class ListCommand (Command):
    u"""List the current tasks

%s list
"""

    alias = ["list", "show"]

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
    # TODO
    pass

def isCommand(obj):
    u"""Check if the parameter is a class derived from Command, without being
    Command"""

    if inspect.isclass(obj):
        return (issubclass(obj, Command) and not(obj is Command))
    else:
        return False

def main(argv):
    u"""
    Entry point of the program
    """
    global commands, aliases, progname

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
