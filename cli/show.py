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

import os
import re

import cli
from command import Command

class ShowCommand (Command):
    u"""List the current tasks, lists or tags

usage: %s [show|ls|tasks|lists|tags] [--show-completed|-a]

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
        self.datewidth = max(int(cli.lib.config["cli.output_datetime_length"]), 8)
        self.show_completed = False

    def execute(self, cmd, args):

        # Parse the options of the command
        for a in args:
            res = re.match("^(--show-completed|-a)$", a)
            if res != None:
                self.show_completed = True

        # Testing the alias used to call ListCommand
        if cmd in [u'show', u'ls', u'tasks']:
            # Width of the done column
            done_width = 0
            if self.show_completed:
                done_width = 2

            # 38 is an arbitrary value that seems to work well...
            if self.width < (38 + self.datewidth + done_width) :
                cli.output("The terminal is too small to print the list correctly")
                return
            else:
                allowable = self.width - (19 + self.datewidth + done_width)
                self.tagswidth = allowable/4
                self.textwidth = allowable - self.tagswidth

            for group, tasks in cli.lib.get_tasks(group_by =
                cli.lib.config["cli.display_group"], order_by =
                cli.lib.config["cli.task_ordering"]):
                # Print the tasks for each group
                text_group = u"{name} (Priority: {p}, id: {id})".format(name =
                        group["name"], p = group["priority"], id = group["id"])
                c = cli.lib.config["cli.color_group_name"]
                cli.output(text_group, foreground = c[0], background = c[1], bold =
                        c[2])
                length = len(text_group)
                cli.output(u"{s:*<{lgth}}".format(s = "*", 
                    lgth = length))
                if cli.lib.config["cli.display_group"] == "list":
                    self.__output_tasks(tasks, list=group);
                elif cli.lib.config["cli.display_group"] == "tag":
                    self.__output_tasks(tasks, tag=group);
                cli.output()

        elif cmd in [u'lists', u'tags'] :
            grp_by = cmd[0:-1]

            c = cli.lib.config["cli.color_group_name"]
            cli.output(u"<" + grp_by + u" name> (id: <id>) - <tasks completed>/<tasks>:", 
                    foreground = c[0], background = c[1], bold = c[2])
            
            for group, tasks in cli.lib.get_tasks(group_by = grp_by, order = False):
                n_tasks = len(tasks)
                n_completed = 0
                for t in tasks:
                    n_completed += t["completed"]
                cli.output(u"\t- " + str(group["name"]) + u" (id: " + str(group["id"]) 
                        + u") - " + str( n_completed) + u"/" + str(n_tasks))

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

    def __get_tags(self, tags_nb):
        u"""From a comma-separated list of tags ids, get the tags name and
        return a comma separated list of tags name"""
        tags = tags_nb.split(",")
        tags_name = []
        tags_rows = cli.lib.get_tags(tags)
        for t in tags_rows:
            if t["id"] != 1:
                tags_name.append(t["name"])
        return ", ".join(tags_name)

    def __output_tasks(self, tasks, list=None, tag=None):
        u"""Print the tasks. The parameter tasks have to be complete rows of
        the tasks table."""
        # Print header, depending on show_completed
        done_column_top = ""
        done_column_middle = ""
        done_column_bottom = ""
        if self.show_completed:
            done_column_top = "__"
            done_column_middle = "| "
            done_column_bottom = "--"

        c = cli.lib.config["cli.color_header"]
        cli.output(u" {done}__________{t:_<{datewidth}}_____{t:_<{textwidth}}_{t:_<{tagswidth}} ".format( 
            done=done_column_top, t="_", textwidth=self.textwidth,
            tagswidth=self.tagswidth, datewidth=self.datewidth), 
            foreground = c[0], background = c[1], bold = c[2])
        cli.output(u"{done}|Priority |{date:^{datewidth}}| Id|{task:<{textwidth}}|{tags:<{tagswidth}}|".format(
            done=done_column_middle, date = "Due date", datewidth = self.datewidth, 
            task = " Task", textwidth = self.textwidth, tags = " Tags",
            tagswidth = self.tagswidth),
            foreground = c[0], background = c[1], bold = c[2])
        cli.output(u" {done}----------{t:-<{datewidth}}-----{t:-<{textwidth}}-{t:-<{tagswidth}} ".format( 
            done=done_column_bottom, t="-", textwidth=self.textwidth,
            tagswidth=self.tagswidth, datewidth=self.datewidth),
            foreground = c[0], background = c[1], bold = c[2])

        for r in tasks:
            self.__print_tree(r, "", done_column_middle, list=list, tag=tag, check_contextual=True)

            # Print the separator
            cli.output(u" {done}----------{t:-<{datewidth}}-----{t:-<{textwidth}}-{t:-<{tagswidth}} ".format( 
                done = done_column_bottom, t="-", textwidth=self.textwidth,
                tagswidth=self.tagswidth, datewidth = self.datewidth))

    def __print_tree(self, root, prefix="", done_column_middle="", list=None, tag=None, check_contextual=True):
        # Skip the task if it's completed
        if (not self.show_completed) and root[0]["completed"] == 1:
            return

        # Split task text
        st = self.__split_text(root[0]["task"], self.textwidth - len(prefix))

        # Prepare and split tags
        tags = self.__get_tags(root[0]["tags"])
        tags = self.__split_text(tags, self.tagswidth)

        # Print the first line of the current task
        done_column = ""
        if self.show_completed:
            if root[0]["completed"] == 1:
                done_column = "|X"
            else:
                done_column = "| "

        # Format the date column
        date_column = cli.parse_output_date(root[0]["due_date"])

        # Select color
        contextual = (list != None and int(root[0]["list"]) != list['id']) or (
            tag != None and (str(tag["id"]) not in root[0]["tags"].split(",")))
        color_name = "cli.color_default"
        if check_contextual and contextual:
            color_name = "cli.color_contextual" 
        elif root[0]["due_date"] < cli.lib.get_time():
            color_name = "cli.color_tasks_late"
        else:
            color_name = "cli.color_priority" + str(root[0]["priority"])
        c = cli.lib.config[color_name]

        cli.output(u"{done}|{p:^9}|{date:^{datewidth}}|{id:^3}| {pref:^{pref_width}}{task:<{textwidth}}|{tags:{tagswidth}}|".format(
            done = done_column, p = root[0]["priority"], date = date_column, id = root[0]["id"], 
            pref = prefix, pref_width = len(prefix),
            task = st.pop(0), textwidth = self.textwidth - len(prefix), 
            tags = tags.pop(0), tagswidth = self.tagswidth, 
            datewidth = self.datewidth),
            foreground = c[0], background = c[1], bold = c[2])

        # Blanking the prefix
        blank_prefix = ""
        for i in range(len(prefix)):
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
            cli.output(u"{done}|         |{t: <{datewidth}}|   | {pref:^{pref_width}}{task:<{textwidth}}|{tags:{tagswidth}}|".format(
                done = done_column_middle, task = te, textwidth = self.textwidth - len(blank_prefix),
                tags=ta, pref = blank_prefix, pref_width = len(blank_prefix),
                tagswidth = self.tagswidth, t = " ", 
                datewidth = self.datewidth),
                foreground = c[0], background = c[1], bold = c[2])

        # Print the nodes of the root
        prefix = blank_prefix + "* "
        for node in root[1]:
            self.__print_tree(node, prefix, list = list, tag = tag, check_contextual = check_contextual and (list != None or (tag != None and contextual)))
