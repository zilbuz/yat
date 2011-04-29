#-*- coding:utf-8 -*-

u"""
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
                   Version 2, December 2004 

 Copyright (C) 2010 
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

import re
import sys

import cli
from command import Command

class DoneCommand(Command):
    u"""Change the completed status of a task.

usage: %s (done|undone) (id=<id>|<regexp>)

By using the 'done' alias, this command allows you to mark a task as completed.
A task completed won't be deleted, but it won't be displayed by default with the
'show' command.

If you use 'undone' instead, the 'completed' flag will be set to False for this
task.

You have to provide either the id of the task (with 'id=<id>'), or the name of
the task. If you give the name of the task, you can use '*' and '?' as jokers.
But if you do so, be careful to surround your request with double quotes so that
the shell doesn't expand them.
"""

    alias = [u"done", u"undone"]

    def __init__(self):
        self.re_id = re.compile(u"^id=({0})$".format(cli.lib.config["re.id"]))

    def execute(self, cmd, args):
        if len(args) == 0:
            cli.output(st = u"[ERR] You must provide some informations to the command. See 'yat help done'", 
                    f = sys.stderr,
                    foreground = cli.colors.errf, background = cli.colors.errb,
                    bold = cli.colors.errbold)

        id = None
        regexp = []
        for a in args:
            res = self.re_id.match(a)
            if res != None:
                id = res.group(1)
                break
            regexp.append(a)

        regexp = " ".join(regexp)

        cli.Yat.Task.class_lib = cli.lib
        if id != None:
            tasks = cli.Yat.Task.get_tasks(ids=[int(id)])
        else:
            tasks = cli.Yat.Task.get_tasks(regexp=regexp)

        done = cmd == u"done"
        for task in tasks:
            task.completed = done
            task.save()
