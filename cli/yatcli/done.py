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

import re
import sys
from collections import deque

import yatcli
from command import Command

class DoneCommand(Command):
    u"""Change the completed status of a task.

usage: {name} (done|undone) (id=<id>|<regexp>)

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
        super(DoneCommand, self).__init__()
        self.ids_to_process = []
        self.regexp = []
        self.options = ([
            ('r', 'recursive', 'recursive', None),
            ('n', 'no-recursive', 'no_recursive', None)
        ])

        self.arguments = (['id', 'regexp'], {
            'id'    :   ('^id=(?P<value>[0-9]+)$', ['id', 'regexp', None],
                         self.ids_to_process),

            'regexp':   ('.*', ['regexp', None], self.regexp)
        })

    def execute(self, cmd):
        if self.regexp == []:
            regexp = None
        else:
            regexp = " ".join(self.regexp)

        done = cmd == u"done"
        tasks = deque(yatcli.lib.get_tasks(ids = self.ids_to_process,
                                           regexp = regexp))
        while True:
            try:
                t = tasks.popleft()
            except IndexError:
                break
            t.completed = done
            t.save()
            if self.recursive and not self.no_recursive:
                processed.add(t)
                tasks.extend([c for c in yatcli.lib.get_children(t)
                              if c not in processed])
