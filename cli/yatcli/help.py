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

import yatcli
from command import Command

class HelpCommand (Command):
    u"""Show this help or a command specific help if an argument is provided

usage: {name} help [command]

Without arguments, provide a short description of the differents commands. If
the name of a command is provided, show the specific help text for this command.
"""

    alias = [u"help"]

    def execute(self, cmd, args):
        detailed = False
        cmd = self

        if len(args) > 0:
            if args[0] in yatcli.aliases:
                cmd = yatcli.aliases[args[0]]()
                detailed = True

        helptxt = cmd.__doc__.split('\n\n', 1)

        if detailed:
            yatcli.output(helptxt[1].format(name = yatcli.name))

        if cmd.alias[0] == u"help":
            if not detailed:
                yatcli.output(
                u"""{name} (Yet Another Todolist) is a very simple commandline todolist manager.

usage: {name} [options] [command] [arguments]

options:
    --help, -h
        Print this help and exit.
    --config-file FILE, -c FILE
        Use FILE as a configuration file.
    --version, -v
        Print the current version of yat and exit.

The different commands are:""".format(name = yatcli.name))

            # Extract docstrings from command classes
            help_txts = []
            for name, cmd in yatcli.commands.iteritems():
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
            for t in help_txts:
                yatcli.output(t)

            yatcli.output()
            yatcli.output(u"If no command are provided, the 'show' command is assumed.")
            yatcli.output(u"Please type \"%s help [command]\" to have" %
                    yatcli.name, linebreak = False)
            yatcli.output(u" detailed informations on a specific command.")

        yatcli.output()
        pass
    pass
