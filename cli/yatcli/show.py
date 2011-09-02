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

from yatcli import write, lib, parse_output_date
from yat.models import Group, NoList, NoTag, Task
from yat.tree import Tree
from yatcli.command import Command

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
        super(ShowCommand, self).__init__()
        if os.name == 'nt':
            self.width = 80
        else:
            self.width = int(os.popen('stty size', 'r').read().split()[1])
        self.textwidth = 0
        self.tagswidth = 0
        self.datewidth = \
                max(int(lib.config["cli.output_datetime_length"]), 8)
        self.options = [('a', 'show-completed', 'show_completed', None)]

    #pylint: disable=E1101,W0201
    def execute(self, cmd):
        self.check_contextual = True    # Until an option is implemented

        # Testing the alias used to call ListCommand
        if cmd in [u'show', u'ls', u'tasks']:
            # Width of the done column
            done_width = 0
            if self.show_completed:
                done_width = 2

            # 38 is an arbitrary value that seems to work well...
            if self.width < (38 + self.datewidth + done_width) :
                write("The terminal is too small \
                              to print the list correctly")
                return
            else:
                allowable = self.width - (20 + self.datewidth + done_width)
                self.tagswidth = allowable/4
                self.textwidth = allowable - self.tagswidth

            #Load all the tasks in memory
            lib.get_tasks()
            if lib.config["cli.display_group"] ==  u'list':
                to_display = [Tree(li) for li in
                              lib.get_loaded_lists()]
            else:
                to_display = [Tree(li) for li in
                              lib.get_loaded_tags()]
            criteria = []
            for criterium in lib.config['cli.task_ordering']:
                tmp = criterium.split(':')
                if len(tmp) == 2:
                    criteria.append((tmp[1], True))
                else:
                    criteria.append((tmp[0], False))
            Tree.sort_trees(to_display, criteria)

        elif cmd in [u'lists', u'tags'] :
            color_conf = lib.config["cli.color_group_name"]
            write(u"<" + cmd[0:-1] +
                  u" name> (id: <id>) - <tasks completed>/<tasks>:",
                  color = (color_conf[0], color_conf[1]), bold = color_conf[2])
            
            if cmd == u'lists':
                groups = set(lib.get_lists())
            else:
                groups = set(lib.get_tags())

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
        for word in tmp:
            length += len(word) + 1 # +1 to include spaces
            if length > width:
                index += 1
                splitted_text.append([])
                length = len(word) + 1
            splitted_text[index].append(word)
        for i in range(len(splitted_text)):
            splitted_text[i] = " ".join(splitted_text[i])
        return splitted_text

    #pylint: disable=W0613,R0912
    def __load_display(self, groups):
        u"""Load all the necessary methods in order to display correctly the
        objects."""
        done_column_top = ""
        done_column_middle = ""
        done_column_bottom = ""
        if self.show_completed:
            done_column_top = "__"
            done_column_middle = "| "
            done_column_bottom = "--"


        def group_header(group):
            u"""The header displayed before listing a groups content."""
            return u"{name} (Priority: {p}, id: {id})".format(name =
                    group.content, p = group.priority, id = group.id)

        def notag_header(group):
            u"""The header displayed before the tasks that are not tagged."""
            return u"Not tagged"

        def nolist_header(group):
            u"""The header displayed before the tasks that are not in a list.
            """
            return u"Not listed"

        def group_tree_display(group, recursion_arguments, contextual):
            u"""Print the tasks. The parameter tasks have to be complete rows of
            the tasks table."""
            write()
            text_group = group.group_header()
            color_conf = lib.config["cli.color_group_name"]
            write(text_group, color = (color_conf[0], color_conf[1]),
                  bold = color_conf[2])
            length = len(text_group)
            write(u"{s:*<{lgth}}".format(s = "*", lgth = length))

            # Print header, depending on show_completed
            color_conf = lib.config["cli.color_header"]
            write(u" {done}__________{t:_<{datewidth}}\
                  ______{t:_<{textwidth}}_{t:_<{tagswidth}} ".format( 
                done=done_column_top, t="_", textwidth=self.textwidth,
                tagswidth=self.tagswidth, datewidth=self.datewidth), 
                color = (color_conf[0], color_conf[1]), bold = color_conf[2])
            write(u"{done}|Priority |{date:^{datewidth}}| Id| \
                  {task:<{textwidth}}|{tags:<{tagswidth}}|".format(
                      done=done_column_middle, date = "Due date",
                      datewidth = self.datewidth, task = "Task",
                      textwidth = self.textwidth, tags = " Tags",
                      tagswidth = self.tagswidth),
                  color = (color_conf[0], color_conf[1]), bold = color_conf[2])
            write(u" {done}----------{t:-<{datewidth}}------\
                  {t:-<{textwidth}}-{t:-<{tagswidth}} ".format( 
                done=done_column_bottom, t="-", textwidth=self.textwidth,
                tagswidth=self.tagswidth, datewidth=self.datewidth),
                color = (color_conf[0], color_conf[1]), bold = color_conf[2])

        def group_display_callback(group, rec_arguments = None):
            u"""What should be displayed after a group_display."""
            pass

        def tree_print(tree, recursion_arguments = None):
            u"""The main recursion engine."""
            try:
                next_recursion = tree.parent.tree_display(recursion_arguments,
                                                          tree.context)
            except InterruptDisplay:
                return
            for child in tree.children:
                child.display(next_recursion)
            tree.parent.display_callback(next_recursion)

        def group_print(group):
            u"""When listing groups, this is how they are displayed."""
            tasks = lib.get_tasks(groups=[group])
            n_tasks = len(tasks)
            n_completed = 0
            for task in tasks:
                n_completed += task.completed
            write(u"\t- " + group.content + u" (id: " +
                        str(group.id) + u") - " +
                        str( n_completed) + u"/" + str(n_tasks))

        def task_display_callback(task, rec_arguments = None):
            u"""Called after a task's display."""
            if rec_arguments == None or rec_arguments["print_sep"]:
                # Print the separator
                write(u" {done}----------{t:-<{datewidth}}------\
                      {t:-<{textwidth}}-{t:-<{tagswidth}} ".format( 
                    done = done_column_bottom, t="-", textwidth=self.textwidth,
                    tagswidth=self.tagswidth, datewidth = self.datewidth))

        def task_tree_display(task, rec_arguments, contextual):
            u"""How a task is displayed when inside a Tree (see tree_print)"""
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
            string = self.__split_text(task.content, self.textwidth -
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
            date_column = parse_output_date(task.due_date)

            # Select color
            color_name = "cli.color_default"
            if self.check_contextual and contextual:
                color_name = "cli.color_contextual" 
            elif task.due_date < lib.get_time():
                color_name = "cli.color_tasks_late"
            else:
                color_name = "cli.color_priority" + str(task.priority)
            color_conf = lib.config[color_name]

            write(u"{done}|{p:^9}|{date:^{datewidth}}|{id:^3}| {pref:\
                  ^{pref_width}}{task:<{textwidth}}|{tags:{tagswidth}}|".format(
                      done = done_column, p = task.priority,
                      date = date_column, id = task.id,
                      pref = arguments['prefix'],
                      pref_width = len(arguments['prefix']),
                      task = string.pop(0),
                      textwidth = self.textwidth - len(arguments['prefix']),
                      tags = tags.pop(0), tagswidth = self.tagswidth,
                      datewidth = self.datewidth),
                  color = (color_conf[0], color_conf[1]), bold = color_conf[2])

            # Blanking the prefix
            blank_prefix = ""
            for i in range(len(arguments['prefix'])):
                blank_prefix = blank_prefix + " "

            # Print the rest of the current task
            for i in range(max(len(string), len(tags))):
                if i < len(string):
                    line_task = string[i]
                else:
                    line_task = u""
                if i < len(tags):
                    line_tag = tags[i]
                else:
                    line_tag = u""
                write(
                    u"{done}|         |{t: <{datewidth}}|   | {pref:^{\
                    pref_width}}{task:<{textwidth}}|{tags:{tagswidth}}|".format(
                        done = done_column_middle, task = line_task,
                        textwidth = self.textwidth - len(blank_prefix),
                        tags = line_tag, pref = blank_prefix,
                        pref_width = len(blank_prefix),
                        tagswidth = self.tagswidth, t = " ",
                        datewidth = self.datewidth),
                    color = (color_conf[0], color_conf[1]),
                    bold = color_conf[2])

            # Print the nodes of the root
            arguments['prefix'] = blank_prefix + "* "
            return arguments

        Task.tree_display = task_tree_display
        Task.display_callback = task_display_callback
        Group.tree_display = group_tree_display
        Group.display_callback = group_display_callback
        Group.group_header = group_header
        Group.display = group_print
        NoList.group_header = nolist_header
        NoTag.group_header = notag_header

        Tree.display = tree_print
    #pylint: enable=W0613,R0912
    #pylint: enable=E1101,W0201

class InterruptDisplay(Exception):
    u'''For internal use.'''
