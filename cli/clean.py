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

import cli
from command import Command

class CleanCommand(Command):
    u"""Delete all the completed tasks.

usage: {name} clean [options]

This command deletes all the completed tasks from the database. Be careful, this
is definitive.

Options:
    --force, -f
        Don't ask for a global confirmation, just delete.
    --interactive, -i
        Ask a confirmation for each completed task.
"""
    
    alias = [u"clean"]

    def __init__(self):
        self.re_force = re.compile(r'^(--force|-f)$')
        self.re_interactive = re.compile(r'^(--interactive|-i)$')
        self.force = False
        self.interactive = False

    def execute(self, cmd, args):
        # Parse args
        for a in args:
            res = self.re_force.match(a)
            if res != None:
                self.force = True
            res = self.re_interactive.match(a)
            if res != None:
                self.interactive = True

        if not self.force:
            if not cli.yes_no_question(u"Are you sure you want to delete all your completed tasks ?"):
                return

        tasks = cli.lib.get_tasks()
        tasks_ids = []
        for t in tasks:
            if t.completed == 1:
                if self.interactive:
                    txt = u"Do you want to delete this task:\n" + t.content 
                    txt += u" (priority: " + str(t.priority)
                    txt += u", due date: " + cli.parse_output_date(t.due_date) + u") ?"
                    if not cli.yes_no_question(txt):
                        continue
                tasks_ids.append(t.id)
        
        cli.lib.remove_tasks(tasks_ids)
