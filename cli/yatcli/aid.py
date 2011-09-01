#-*- coding:utf-8 -*-

u"""
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
                   Version 2, December 2004 

 Copyright (C) 2010, 2011 
    Basile Desloges <basile.desloges@gmail.com>
    Simon Chopin <chopin.simon@gmail.com>

 Everyone is permitted to copy and distribute verbatim or modified 
 copies of this license document, and changing it is allowed as long 
 as the name is changed. 

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION 

  0. You just DO WHAT THE FUCK YOU WANT TO. 

This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
http://sam.zoy.org/wtfpl/COPYING for more details.
"""

from yatcli import write, aliases, name, commands
from yatcli.command import Command

class HelpCommand (Command):
    u"""Show this help or a command specific help if an argument is provided

usage: {name} help [command]

Without arguments, provide a short description of the differents commands. If
the name of a command is provided, show the specific help text for this command.
"""

    alias = [u"help"]
    def __init__(self):
        super(HelpCommand, self).__init__()
        self.cmd = self
        self.detailed = False
        self.arguments = (['command', None]), {
            'command':  ('^.*$', [None], self.__set_cmd)
        }

    def __set_cmd(self, value):
        u'''Load the command specified by value.'''
        self.cmd = aliases[value]
        self.detailed = True

    def execute(self, cmd):
        helptxt = self.cmd.__doc__.split('\n\n', 1)

        if self.detailed:
            write(helptxt[1].format(name = name))

        if self.cmd.alias[0] == u"help":
            if not self.detailed:
                write(
u"""{name} (Yet Another Todolist) is a very simple commandline todolist manager.

usage: {name} [options] [command] [arguments]

options:
    --help, -h
        Print this help and exit.
    --config-file FILE, -c FILE
        Use FILE as a configuration file.
    --version, -v
        Print the current version of yat and exit.

The different commands are:""".format(name = name))

            # Extract docstrings from command classes
            help_txts = []
            for cmd in commands.itervalues():
                txt = u"\t" + cmd.alias[0]
                txt += u"\t" + cmd.__doc__.split('\n', 1)[0]
                if len(cmd.alias) > 1:
                    txt += u" (alias: "
                    for i in range(1, len(cmd.alias)):
                        txt += cmd.alias[i]
                        if i < len(cmd.alias) - 1:
                            txt += u", "
                    txt += u")"
                help_txts.append(txt)

            # Sort the docstrings
            help_txts.sort()

            # Print them
            for txt in help_txts:
                write(txt)

            write()
            write(u"If no command are provided, \
                          the 'show' command is assumed.")
            write(u"Please type \"%s help [command]\" to have" %
                    name, linebreak = False)
            write(u" detailed informations on a specific command.")

        write()