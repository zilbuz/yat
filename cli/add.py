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

class AddCommand (Command):
    u"""Add a task, a list or a tag

usage: %s add [task | list | tag] "<informations>"

Add a task, a list or a tag to the todolist, depending of the first argument
after "add". If the first argument after "add" isn't one of these, then "task"
is assumed.

Adding a task:
    When adding a task, you must provide the task's text, and optionnally some
    symbols to set the priority, due date, tags or list. The symbols are '*',
    '~', '^', '#' and '>'.

    '*' can be used to set the priority of the task, it must be followed by a number
    between 0 and 3. 
    Example: yat add "do the laundry *2".

    '~' would be used if you want to make a subtask for an already existing task. It 
    must be followed by the id number of the parent task. If no list/deadline/priority
    argument is provided, the default list/deadline/priority of the subtask will be the
    one(s) of the parent task.

    '^' can be used to set the due date of the task, it must be followed by a
    date of the form [x]x/xx/yyyy[:[h]h[:mm][am|pm]], where xx/xx is either dd/mm or
    mm/dd, depending of the cli.input_date option, and hh is the hour in 24 or
    12 hour format, depending of the cli.input_time option.
    Example: yat add "go to the cinema with Wendy ^12/02/2011:20".

    '#' can be used to set the tags of the task, it must be followed by the name
    of a tag. The tag name can be composed of anything but spaces. You can set 
    multiple tags for a task. If the tag doesn't exist, it will be created.
    Example: yat add "do my homework #work #important"

    '>' can be used to set the list of the task, it must be followed by the name
    of a list. The list name can be composed of anything but spaces. If the list
    doesn't exist, it will be created.
    Example: yad add "peanut butter >groceries"

    Apart from the tags, if a symbol is used more than one time for a task, the
    last one will be used.
    You can place the symbols anywhere in the task text.
    You can escape the symbols with \, for example: "the symbol \> won't be
    processed with this text". And of course, you also have to escape \ if you
    want to use it.
    If your task text uses none of the symbols that the shell can interpret, the
    double quotes are optionnal.

Adding a list:
    Just add a new list. The name can contain anything but spaces. The second
    argument can be the priority of the list. When the tasks will be displayed
    by lists, they will be ordered with this number. The default priority is 0
    and the "nolist" list has a priority of -1.
    Example: yat add list groceries 1

Adding a tag:
    Just add a new tag. The name can contain anything but spaces. The second
    argument can be the priority of the tag. When the tasks will be displayed by
    tags, they will be ordered with this number. The default priority is 0 and
    the "notag" tag has a priority of -1.
    Example: yat add tag work 5
"""
    
    alias = [u"add"]

    def __init__(self):
        self.re_priority = re.compile(u"^\*({0})$".format(
            cli.lib.config["re.priority"]))
        u"""Regex for the priorty"""

        self.re_tag = re.compile(u"^#({0})$".format(cli.lib.config["re.tag_name"]))
        u"""Regex for the tags"""

        self.re_parent = re.compile(u"^~({0})$".format(
            cli.lib.config["re.id"]))
        u"""Regex for the parent task"""

        self.re_list = re.compile(u"^>({0})$".format(
            cli.lib.config["re.list_name"]))
        u"""Regex for the list"""

        self.re_date = re.compile(u"^\^{0}$".format(cli.lib.config["re.date"]))
        u"""Regex for the date"""

    def execute(self, cmd, args):
        cmd = ""
        if args[0] in ["task", "list", "tag"]:
            cmd = args[0]
            args = args[1:]

        # If there is no more arguments, return immediately
        if len(args) == 0:
            return

        # Process command
        if cmd in ["tag", "list"]:
            if cmd == "tag":
                group = cli.Yat.Tag(cli.lib)
            elif cmd == "list":
                group = cli.Yat.List(cli.lib)
            group.content = args[0]
            if len(args) > 1:
                # The second argument is the priority
                group.priority = int(args[1])
            else:
                group.priority = 0

            group.save(cli.lib)

            pass
        else: # Adding a task
            # Init params
            new_task = cli.Yat.Task(None, cli.lib)
            tag_names = []
            text = []

            # Look for symbols
            for a in args:
                symbol = False
                # Priority
                res = self.re_priority.match(a)
                if res != None:
                    new_task.priority = int(res.group(1))
                    symbol = True
                # Tags
                res = self.re_tag.match(a)
                if res != None:
                    tag_names.append(res.group(1))
                    symbol = True
                # List
                res = self.re_list.match(a)
                if res != None:
                    new_task.list = cli.lib.get_list(res.group(1), type_id=False,
                                                 can_create=True)
                    symbol = True

                # Parent task
                res = self.re_parent.match(a)
                if res != None:
                    new_task.parent = cli.lib.get_tasks([res.group(1)],
                                                    group=False, order=False,
                                                    fetch_children=False,
                                                    fetch_parents=False,
                                                    regroup_family=False)[0].parent
                    symbol = True
                # Date
                res = self.re_date.match(a)
                if res != None:
                    try:
                        new_task.due_date = cli.parse_input_date(res)
                    except ValueError:
                        cli.output("[ERR] The due date isn't well formed. See 'yat help add'.", 
                                f = sys.stderr,
                                foreground = cli.colors.errf, background = 
                                cli.colors.errb, bold = cli.colors.errbold)
                        return
                    symbol = True

                # Regular text
                if not symbol:
                    text.append(a)

            new_task.content = " ".join(text)
            new_task.tags = cli.lib.get_tags(tag_names, type_id=False,
                                         can_create=True)
            new_task.save(cli.lib)

