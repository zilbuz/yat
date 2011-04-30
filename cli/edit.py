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

import cli
from command import Command

class EditCommand(Command):
    u"""Edit the attributes of a task

usage: {name} edit [task|list|tag] id=<id> [<attribute>=<value>]*

This command allows you to edit the attributes of an already entered task, list
or tag. You
must provide the id of the element to modify, and the attributes to modify. You can
edit multiple attributes at the same time. If the type of element to edit isn't
provided, "task" is assumed.

The possible attributes for a task are:
    task: the text of the task.
    due_date: the due date of the task, the value must have the same format than
        in the 'add' command: [x]x/xx/yyyy[:[h]h[:mm][am|pm]]
    priority: the priority of the task, must be an integer from 0 (lowest
        priority) to 3 (highest priority)
    list: the task will be deleted from its current list and added to the one
        provided.
    add_tags: you have to provide a comma separated list of tags (they don't
        have to exist yet). The task will be added to them.
    remove_tags: you also have to provide a comma separated list of tags, and
        the task will be deleted from them. If there are no more tags in the
        tasks, the 'notag' tag will be added.

The possible attributes for a list or a tag are:
    name: the name of the element
    priority: the priority of the element, it have to be an integer, and it's
        used to alter the order in which they are displayed.
"""

    alias = [u"edit"]

    def __init__(self):
        self.re_id = re.compile(u"^id=({0})$".format(cli.lib.config["re.id"]))
        self.re_due_date = re.compile(u"^due_date={0}$".format(
            cli.lib.config["re.date"]))
        self.re_parent = re.compile(u"^parent=({0})$".format(
            cli.lib.config["re.id"]))
        self.re_priority = re.compile(u"^priority=({0})$".format(
            cli.lib.config["re.priority"]))
        self.re_add_tags = re.compile(u"^add_tags=({0})$".format(
            cli.lib.config["re.tags_list"]))
        self.re_remove_tags = re.compile(u"^remove_tags=({0})$".format(
            cli.lib.config["re.tags_list"]))
        self.re_list = re.compile(u"list=({0})".format(
            cli.lib.config["re.list_name"]))
        self.re_tol_priority = re.compile(u"^priority=(-?\d\d*)$")
        self.re_tol_name = re.compile(u"^name=({0}|{1})$".format(
            cli.lib.config["re.list_name"], cli.lib.config["re.tag_name"]))
        self.re_name = re.compile(u"^task=(.*)$")

    def execute(self, cmd, args):

        if len(args) == 0:
            cli.output(st = u"[ERR] You must provide some arguments to edit an element. See 'yat help edit'.", 
                    f = sys.stderr,
                    foreground = cli.colors.errf, background = cli.colors.errb,
                    bold = cli.colors.errbold)
            return

        if args[0] in [u"task", u"list", u"tag"]:
            element = args[0]
            args = args[1:]
        else:
            element = u"task"

        to_edit = None

        task = None
        cli.Yat.Task.class_lib = cli.lib
        for a in args:
            res = self.re_id.match(a)
            if to_edit == None and res != None:
                if element == u'task':
                    to_edit = cli.lib.get_task(res.group(1))
                elif element == u'tag':
                    to_edit = cli.lib.get_tag(res.group(1))
                elif element == u'list':
                    to_edit = cli.lib.get_list(res.group(1))
                continue

            if element in [u"list", u"tag"]:
                res = self.re_tol_priority.match(a)
            else:
                res = self.re_priority.match(a)
            if res != None:
                to_edit.priority = int(res.group(1))
                continue

            if element in [u"list", u"tag"]:
                res = self.re_tol_name.match(a)
                if res != None:
                    to_edit.content = res.group(1)
                    continue

            res = self.re_due_date.match(a)
            if res != None:
                try:
                    to_edit.due_date = cli.parse_input_date(res)
                except ValueError:
                    cli.output("[ERR] The due date isn't well formed. See 'yat help edit'.", 
                            f = sys.stderr,
                            foreground = cli.colors.errf, background =
                            cli.colors.errb, bold = cli.colors.errbold)
                    return
                continue

            res = self.re_parent.match(a)
            if res != None:
                to_edit.parent = cli.Yat.Task.get_task(res.group(1))
                continue

            res = self.re_list.match(a)
            if res != None:
                try:
                    to_edit.list = cli.lib.get_list(res.group(1), False) 
                except:
                    to_edit.list = cli.Yat.List(cli.lib)
                    to_edit.list.content = res.group(1)
                continue

            res = self.re_add_tags.match(a)
            if res != None:
                tag_names = res.group(1).split(',')
                for n in tag_names:
                    try:
                        to_edit.tags.add(cli.lib.get_tag(n, False))
                    except:
                        tag = cli.Yat.Tag(cli.lib)
                        tag.content = n
                        to_edit.tags.add(tag)
                continue

            res = self.re_remove_tags.match(a)
            if res != None:
                to_edit.tags -= set(cli.lib.get_tags(names=res.group(1).split(',')))
                continue

            res = self.re_name.match(a)
            if task == None and res != None:
                task = [res.group(1)]
                continue

            if task != None:
                task.append(a)

        if task != None:
            task = " ".join(task)
            if element == 'task': 
                to_edit.content = task
        to_edit.save()
