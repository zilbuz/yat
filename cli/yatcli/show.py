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

import os
import re

import yatcli
from command import Command

class ShowCommand (Command):
    u"""List the current tasks, lists or tags

usage: {name} [show|ls|tasks|lists|tags] [--show-completed|-a]

List the content of the todolist. Depending of the alias used, it will display
the tasks list, the lists list or the tags list. The aliases "show" and "ls"
display the tasks. If no command is provided, "tasks" is assumed.

Options:
    --show-completed, -a
        Display all the tasks, even if they are marked as completed.
"""

    alias = [u"show", u"ls", u"lists", u"tasks", u"tags"]

    def __init__(self):
        self.width = int(os.popen('stty size', 'r').read().split()[1])
        self.textwidth = 0
        self.tagswidth = 0
        self.datewidth = max(int(yatcli.lib.config["cli.output_datetime_length"]), 8)
        self.show_completed = False

    def execute(self, cmd, args):

        # Parse the options of the command
        for a in args:
            res = re.match("^(--show-completed|-a)$", a)
            if res != None:
                self.show_completed = True
        self.check_contextual = True    # Until an option is implemented

        # Testing the alias used to call ListCommand
        if cmd in [u'show', u'ls', u'tasks']:
            # Width of the done column
            done_width = 0
            if self.show_completed:
                done_width = 2

            # 38 is an arbitrary value that seems to work well...
            if self.width < (38 + self.datewidth + done_width) :
                yatcli.output("The terminal is too small to print the list correctly")
                return
            else:
                allowable = self.width - (20 + self.datewidth + done_width)
                self.tagswidth = allowable/4
                self.textwidth = allowable - self.tagswidth

            tasks = yatcli.lib.get_tasks()
            if yatcli.lib.config["cli.display_group"] ==  u'list':
                to_display = [yatcli.yat.Tree(li) for li in yatcli.lib.get_loaded_lists()]
            else:
                to_display = [yatcli.yat.Tree(li) for li in yatcli.lib.get_loaded_tags()]
            criteria = []
            for o in yatcli.lib.config['cli.task_ordering']:
                tmp = o.split(':')
                if len(tmp) == 2:
                    criteria.append((tmp[1], True))
                else:
                    criteria.append((tmp[0], False))
            yatcli.yat.Tree.sort_trees(to_display, criteria)

        elif cmd in [u'lists', u'tags'] :
            c = yatcli.lib.config["cli.color_group_name"]
            yatcli.output(u"<" + cmd[0:-1] + u" name> (id: <id>) - <tasks completed>/<tasks>:", 
                    foreground = c[0], background = c[1], bold = c[2])
            
            if cmd == u'lists':
                groups = set(yatcli.lib.get_lists())
            else:
                groups = set(yatcli.lib.get_tags())

            to_display = groups

        self.__load_display(cmd in [u'lists', u'tags'])
        for item in to_display:
            item.display()

    def __split_text(self, text, width=None):
        u"""Split the text so each chunk isn't longer than the textwidth
        attribute"""
        if width == None:
            width = self.textwidth
        tmp = text.split(" ")
        length = 0
        index = 0
        splitted_text = [[]]
        for t in tmp:
            length += len(t) + 1 # +1 to include spaces
            if length > width:
                index += 1
                splitted_text.append([])
                length = len(t) + 1
            splitted_text[index].append(t)
        for i in range(len(splitted_text)):
            splitted_text[i] = " ".join(splitted_text[i])
        return splitted_text

    def __load_display(self, groups):
        done_column_top = ""
        done_column_middle = ""
        done_column_bottom = ""
        if self.show_completed:
            done_column_top = "__"
            done_column_middle = "| "
            done_column_bottom = "--"


        def group_header(group):
            return u"{name} (Priority: {p}, id: {id})".format(name =
                    group.content, p = group.priority, id = group.id)

        def notag_header(group):
            return u"Not tagged"

        def nolist_header(group):
            return u"Not listed"

        def group_tree_display(group, recursion_arguments, contextual):
            u"""Print the tasks. The parameter tasks have to be complete rows of
            the tasks table."""
            yatcli.output()
            text_group = group.group_header()
            c = yatcli.lib.config["cli.color_group_name"]
            yatcli.output(text_group, foreground = c[0], background = c[1], bold =
                    c[2])
            length = len(text_group)
            yatcli.output(u"{s:*<{lgth}}".format(s = "*", 
                lgth = length))

            # Print header, depending on show_completed
            c = yatcli.lib.config["cli.color_header"]
            yatcli.output(u" {done}__________{t:_<{datewidth}}______{t:_<{textwidth}}_{t:_<{tagswidth}} ".format( 
                done=done_column_top, t="_", textwidth=self.textwidth,
                tagswidth=self.tagswidth, datewidth=self.datewidth), 
                foreground = c[0], background = c[1], bold = c[2])
            yatcli.output(u"{done}|Priority |{date:^{datewidth}}| Id| {task:<{textwidth}}|{tags:<{tagswidth}}|".format(
                done=done_column_middle, date = "Due date", datewidth = self.datewidth, 
                task = "Task", textwidth = self.textwidth, tags = " Tags",
                tagswidth = self.tagswidth),
                foreground = c[0], background = c[1], bold = c[2])
            yatcli.output(u" {done}----------{t:-<{datewidth}}------{t:-<{textwidth}}-{t:-<{tagswidth}} ".format( 
                done=done_column_bottom, t="-", textwidth=self.textwidth,
                tagswidth=self.tagswidth, datewidth=self.datewidth),
                foreground = c[0], background = c[1], bold = c[2])

        def group_display_callback(group, rec_arguments = None):
            pass

        def tree_print(tree, recursion_arguments = None):
            try:
                next_recursion = tree.parent.tree_display(recursion_arguments, tree.context)
            except InterruptDisplay:
                return
            for t in tree.children:
                t.display(next_recursion)
            tree.parent.display_callback(next_recursion)

        def group_print(group):
            tasks = yatcli.lib.get_tasks(groups=[group])
            n_tasks = len(tasks)
            n_completed = 0
            for t in tasks:
                n_completed += t.completed
            yatcli.output(u"\t- " + group.content + u" (id: " +
                        str(group.id) + u") - " +
                        str( n_completed) + u"/" + str(n_tasks))

        def task_display_callback(task, rec_arguments = None):
            if rec_arguments == None or rec_arguments["print_sep"]:
                # Print the separator
                yatcli.output(u" {done}----------{t:-<{datewidth}}------{t:-<{textwidth}}-{t:-<{tagswidth}} ".format( 
                    done = done_column_bottom, t="-", textwidth=self.textwidth,
                    tagswidth=self.tagswidth, datewidth = self.datewidth))

        def task_tree_display(task, rec_arguments, contextual):
            if (not self.show_completed) and task.completed == 1:
                raise InterruptDisplay()

            if rec_arguments == None:
                arguments = {
                        'prefix':'',
                        'print_sep': True,
                        }
            else:
                arguments = rec_arguments.copy()
                arguments['print_sep'] = False

            # Split task text
            st = self.__split_text(task.content, self.textwidth -
                                   len(arguments['prefix']))

            # Prepare and split tags
            tags = sorted(task.tags, key = lambda t: len(t.content))
            tags = ", ".join([t.content for t in tags])
            tags = self.__split_text(tags, self.tagswidth)

            # Print the first line of the current task
            done_column = ""
            if self.show_completed:
                if task.completed == 1:
                    done_column = "|X"
                else:
                    done_column = "| "

            # Format the date column
            date_column = yatcli.parse_output_date(task.due_date)

            # Select color
            color_name = "cli.color_default"
            if self.check_contextual and contextual:
                color_name = "cli.color_contextual" 
            elif task.due_date < yatcli.lib.get_time():
                color_name = "cli.color_tasks_late"
            else:
                color_name = "cli.color_priority" + str(task.priority)
            c = yatcli.lib.config[color_name]

            yatcli.output(u"{done}|{p:^9}|{date:^{datewidth}}|{id:^3}| {pref:^{pref_width}}{task:<{textwidth}}|{tags:{tagswidth}}|".format(
                done = done_column, p = task.priority, date = date_column, id = task.id, 
                pref = arguments['prefix'], pref_width = len(arguments['prefix']),
                task = st.pop(0), textwidth = self.textwidth - len(arguments['prefix']), 
                tags = tags.pop(0), tagswidth = self.tagswidth, 
                datewidth = self.datewidth),
                foreground = c[0], background = c[1], bold = c[2])

            # Blanking the prefix
            blank_prefix = ""
            for i in range(len(arguments['prefix'])):
                blank_prefix = blank_prefix + " "

            # Print the rest of the current task
            for i in range(max(len(st),len(tags))):
                if i < len(st):
                    te = st[i]
                else:
                    te = u""
                if i < len(tags):
                    ta = tags[i]
                else:
                    ta = u""
                yatcli.output(u"{done}|         |{t: <{datewidth}}|   | {pref:^{pref_width}}{task:<{textwidth}}|{tags:{tagswidth}}|".format(
                    done = done_column_middle, task = te, textwidth = self.textwidth - len(blank_prefix),
                    tags=ta, pref = blank_prefix, pref_width = len(blank_prefix),
                    tagswidth = self.tagswidth, t = " ", 
                    datewidth = self.datewidth),
                    foreground = c[0], background = c[1], bold = c[2])

            # Print the nodes of the root
            arguments['prefix'] = blank_prefix + "* "
            return arguments

        yatcli.yat.Task.tree_display = task_tree_display
        yatcli.yat.Task.display_callback = task_display_callback
        yatcli.yat.Group.tree_display = group_tree_display
        yatcli.yat.Group.display_callback = group_display_callback
        yatcli.yat.Group.group_header = group_header
        yatcli.yat.Group.display = group_print
        yatcli.yat.NoList.group_header = nolist_header
        yatcli.yat.NoTag.group_header = notag_header
        yatcli.yat.Tree.display = tree_print

class InterruptDisplay(Exception):
    u'''For internal use.'''
