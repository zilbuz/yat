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

class RemoveCommand (Command):
    u"""Remove a task, a list or a tag

usage: %s remove [task | list | tag] [--interactive|-i] [<regexp>|id=<id_nb>]

The use is straightforward : every element matching the
informations gets deleted. 

The informations can be either a number or a regexp. The number
is compared to the id of the elements to delete (task, list or tag),
whereas the regexp is compared to the name or the title.

The symbols for the regexp are the same than the shell: * to match multiple
characters (will be expanded to the regexp ".*"), and ? to match a single
character (will be expanded to the regexp ".?"). Surround your regexp with
double quotes (") so that the shell doesn't expand them. If you want to search
for "*" or "?" you can escape them with "\\".

If "task", "list" or "tag" is not provided, "task" is assumed.

Options:
    --interactive, -i
        Ask a confirmation for every deleted element.
"""

    alias = [u"remove", u"rm"]

    def __init__(self):
        self.re_interactive = re.compile(r'^(--interactive|-i)$')
        self.interactive = False

    def execute(self, cmd, args):
        for a in args[:]:
            res = self.re_interactive.match(a)
            if res != None:
                self.interactive = True
                args.remove(a)

        if args == []:
            print self.__doc__.split('\n',1)[0]," ",args
            return
            
        cmd = ""
        if args[0] in [u"task", u"list", u"tag"]:
            cmd = args[0]
            args = args[1:]
        else:
            cmd = u"task"

        re_number = re.compile("^id=([0-9]+)$")

        operation = u""
        identifier = u""
       
        a = " ".join(args)
        res = re_number.match(a)
        if res is not None:
            a = res.group(1)
            operation = u"="
            identifier = u"id"
        else:
            operation = u" regexp "

            # Ask a confirmation for the * expression.
            if a == '*':
                res = cli.yes_no_question("This operation is potentially disastrous. Are you so desperate ?", default = True)
                if not res:
                    return

            if cmd == u"task":
                identifier = cmd
            else:
                identifier = u"name"

        if cmd in [u"list", u"tag"]:
            ids = []
            if operation == u'=':
                ids = [a, ]
            else:
                if cmd == "tag":
                    temp = cli.lib.get_tags_regex(a)
                else:
                    temp = cli.lib.get_lists_regex(a)

                for t in temp:
                    txt = u"Do you want to delete this " + cmd + u":\n" 
                    txt += t.content 
                    txt += u" (priority: " + str(t.priority) + u") ?"
                    if not cli.yes_no_question(txt):
                        continue
                    ids.append(str(t.id))

            # Removing the tasks belonging to the list
            if cmd == u'list':
                cli.lib.remove_lists(ids)
            # Updating the tag list for the concerned tags.
            else:
                cli.lib.remove_tags(ids)
        else: # removing a task
            ids = []
            if operation == u'=':
                temp = cli.lib.get_tasks(ids = [int(a)], group = False,
                                         order = False, fetch_children = False,
                                         fetch_parents = False)
            else:
                temp = cli.lib.get_tasks(regexp = a, group = False,
                                         order = False, fetch_parents = False,
                                         fetch_children = False)

            for t in temp:
                if self.interactive:
                    txt = u"Do you want to delete this task:\n" + t.parent.content
                    txt += u" (priority: " + str(t.parent.priority)
                    txt += u", due date: " + cli.parse_output_date(t.parent.due_date) + u") ?"
                    if not cli.yes_no_question(txt):
                        continue
                ids.append(t.parent.id)

            cli.lib.remove_tasks(ids)
