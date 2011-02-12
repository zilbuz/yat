#!/usr/bin/env python
#-*- coding:utf-8 -*-

u"""
Very simple command line todolist manager


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

import datetime
import inspect
import os
import re
import sys
import time

import yatlib

class Command:
    u"""Abstract class for instrospection
    
If you wish to add a command, you have to create a class that derive from this
one, and the docstring must have this format:
Short description

usage: %s cmd_name [options]

Long description
"""
    
    alias = []
    u"""Array containing the different aliases for this command"""

    def execute(self, cmd, args):
        u"""Method actually doing something
        Params:
            -cmd: alias used to invoke the command
            -args: the rest of the command line
        """
        raise NotImplementedError

    pass

class HelpCommand (Command):
    u"""Show this help or a command specific help if an argument is provided

usage: %s help [command]

Without arguments, provide a short description of the differents commands. If
the name of a command is provided, show the specific help text for this command.
"""

    alias = [u"help"]

    def execute(self, cmd, args):
        global progname, aliases, commands

        detailed = False
        cmd = self

        if len(args) > 0:
            if args[0] in aliases:
                cmd = aliases[args[0]]()
                detailed = True

        helptxt = cmd.__doc__.split('\n\n', 1)

        if detailed:
            output(helptxt[1] % progname)

        if cmd.alias[0] == u"help":
            if not detailed:
                output(st = (u"%s (Yet Another Todolist) is a very simple " %
                    progname), linebreak = False)
                output(u"commandline todolist manager.")
                output()
                output(u"usage: %s [command] [arguments]" % progname)
                output()

            output(u"The different commands are:")

            # Extract docstrings from command classes
            help_txts = []
            for name, cmd in commands.iteritems():
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
                output(t)

            output()
            output(u"If no command are provided, the 'show' command is assumed.")
            output(u"Please type \"%s help [command]\" to have" % progname, 
                    linebreak = False)
            output(u" detailed informations on a specific command.")

        output()
        pass
    pass

class AddCommand (Command):
    u"""Add a task, a list or a tag

usage: %s add [task | list | tag] "<informations>"

Add a task, a list or a tag to the todolist, depending of the first argument
after "add". If the first argument after "add" isn't one of these, then "task"
is assumed.

Adding a task:
    When adding a task, you must provide the task's text, and optionnally some
    symbols to set the priority, due date, tags or list. The symbols are '*',
    '^', '#' and '>'.

    '*' can be used to set the priority of the task, it must be followed by a number
    between 0 and 3. 
    Example: yat add "do the laundry *2".

    '^' can be used to set the due date of the task, it must be followed by a
    date of the form xx/xx/yyyy[:[h]h[:mm][am|pm]], where xx/xx is either dd/mm or
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

    Apart for the tags, if a symbol is used more than one time for a task, the
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
        global lib
        self.re_priority = re.compile(u"^\*({0})$".format(
            lib.config["re.priority"]))
        u"""Regex for the priorty"""

        self.re_tag = re.compile(u"^#({0})$".format(lib.config["re.tag_name"]))
        u"""Regex for the tags"""

        self.re_list = re.compile(u"^>({0})$".format(
            lib.config["re.list_name"]))
        u"""Regex for the list"""

        self.re_date = re.compile(u"^\^{0}$".format(lib.config["re.date"]))
        u"""Regex for the date"""

    def execute(self, cmd, args):
        global lib
        # Separate words
        args = (" ".join(args)).split(" ")

        cmd = ""
        if args[0] in ["task", "list", "tag"]:
            cmd = args[0]
            args = args[1:]

        # If there is no more arguments, return immediately
        if len(args) == 0:
            return

        # Process command
        if cmd in ["tag", "list"]:
            if len(args) > 1:
                # The second argument is the priority
                priority = int(args[1])
            else:
                priority = 0

            if cmd == "tag":
                lib.add_tag(args[0], priority)
            elif cmd == "list":
                lib.add_list(args[0], priority)
            pass
        else: # Adding a task
            # Init params
            priority = None
            tags = []
            list = None
            date = None
            text = []
            # Look for symbols
            for a in args:
                symbol = False
                # Priority
                res = self.re_priority.match(a)
                if res != None:
                    priority = int(res.group(1))
                    symbol = True
                # Tags
                res = self.re_tag.match(a)
                if res != None:
                    tags.append(res.group(1))
                    symbol = True
                # List
                res = self.re_list.match(a)
                if res != None:
                    list = res.group(1)
                    symbol = True
                # Date
                res = self.re_date.match(a)
                if res != None:
                    try:
                        date = parse_input_date(res)
                    except ValueError:
                        output("[ERR] The due date isn't well formed. See 'yat help add'.", 
                                f = sys.stderr)
                        return
                    symbol = True

                # Regular text
                if not symbol:
                    text.append(a)

            text = " ".join(text)

            # Add the task with the correct parameters
            lib.add_task(text.decode('utf-8'), priority, date, tags, list)
    pass
    

class RemoveCommand (Command):
    u"""Remove a task, a list or a tag

usage: %s remove [task | list | tag] [<regexp>|id=<id_nb>]

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
"""

    alias = [u"remove", u"rm"]

    def execute(self, cmd, args):
        global lib

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
        with lib.sql:
            if res is not None:
                a = res.group(1)
                operation = u"="
                identifier = u"id"
            else:
                operation = u" regexp "

                # Ask a confirmation for the * expression.
                if a == '*':
                    res = yes_no_question("This operation is potentially disastrous. Are you so desperate ?", default = True)
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
                with lib.sql:
                    temp = lib.sql.execute(u'select id from {0} where name regexp ?'.format(cmd+u's'), (a, )).fetchall()
                for t in temp:
                    ids.append(str(t[0]))

            # Removing the tasks belonging to the list
            if cmd == u'list':
                lib.remove_lists(ids)
            # Updating the tag list for the concerned tags.
            else:
                lib.remove_tags(ids)
        else: # removing a task
            ids = []
            with lib.sql:
                for t in lib.sql.execute(u'select id from {0} where {1}{2} ?'.format(cmd+u's', identifier, operation), (a,)):
                    ids.append(t["id"])
            lib.remove_tasks(ids)


class ListCommand (Command):
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
        self.datewidth = max(int(lib.config["cli.output_datetime_length"]), 8)
        self.show_completed = False

    def execute(self, cmd, args):
        global lib

        # Parse the options of the command
        copy_args = (" ".join(args)).split(" ")
        for a in copy_args:
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
                output("The terminal is too small to print the list correctly")
                return
            else:
                allowable = self.width - (19 + self.datewidth + done_width)
                self.tagswidth = allowable/4
                self.textwidth = allowable - self.tagswidth

            for group, tasks in lib.get_tasks(group_by =
                lib.config["cli.display_group"], order_by =
                lib.config["cli.task_ordering"]):
                # Print the tasks for each group
                text_group = u"{name} (Priority: {p}, id: {id})".format(name =
                        group["name"], p = group["priority"], id = group["id"])
                output(text_group)
                length = len(text_group)
                output(u"{s:*<{lgth}}".format(s = "*", 
                    lgth = length))
                self.__output_tasks(tasks)
                output()

        elif cmd in [u'lists', u'tags'] :
            grp_by = cmd[0:-1]

            output(u"<" + grp_by + u" name> (id: <id>) - <tasks completed>/<tasks>:")
            
            for group, tasks in lib.get_tasks(group_by = grp_by, order = False):
                n_tasks = len(tasks)
                n_completed = 0
                for t in tasks:
                    n_completed += t["completed"]
                output(u"\t- " + str(group["name"]) + u" (id: " + str(group["id"]) 
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
        for i in range(len(tags)):
            if tags[i] != "1":
                res = lib.sql.execute(u"select name from tags where id=?",
                        (tags[i],))
                tags_name.append( res.fetchone()["name"] )
        return ", ".join(tags_name)

    def __output_tasks(self, tasks):
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

        output(u" {done}__________{t:_<{datewidth}}_____{t:_<{textwidth}}_{t:_<{tagswidth}} ".format( 
            done=done_column_top, t="_", textwidth=self.textwidth,
            tagswidth=self.tagswidth, datewidth=self.datewidth))
        output(u"{done}|Priority |{date:^{datewidth}}| Id|{task:<{textwidth}}|{tags:<{tagswidth}}|".format(
            done=done_column_middle, date = "Due date", datewidth = self.datewidth, 
            task = " Task", textwidth = self.textwidth, tags = " Tags",
            tagswidth = self.tagswidth))
        output(u" {done}----------{t:-<{datewidth}}-----{t:-<{textwidth}}-{t:-<{tagswidth}} ".format( 
            done=done_column_bottom, t="-", textwidth=self.textwidth,
            tagswidth=self.tagswidth, datewidth=self.datewidth))

        for r in tasks:
            # Skip the task if it's completed
            if (not self.show_completed) and r["completed"] == 1:
                continue

            # Split task text
            st = self.__split_text(r["task"])

            # Prepare and split tags
            tags = self.__get_tags(r["tags"])
            tags = self.__split_text(tags, self.tagswidth)

            # Print the first line of the current task
            done_column = ""
            if self.show_completed:
                if r["completed"] == 1:
                    done_column = "|X"
                else:
                    done_column = "| "

            # Format the date column
            date_column = parse_output_date(r["due_date"])

            output(u"{done}|{p:^9}|{date:^{datewidth}}|{id:^3}|{task:<{textwidth}}|{tags:{tagswidth}}|".format(
                done = done_column, p = r["priority"], date = date_column, id = r["id"], 
                task = st.pop(0), textwidth = self.textwidth, 
                tags = tags.pop(0), tagswidth = self.tagswidth, 
                datewidth = self.datewidth))

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
                output(u"{done}|         |{t: <{datewidth}}|   |{task:<{textwidth}}|{tags:{tagswidth}}|".format(
                    done = done_column_middle, task = te, textwidth = self.textwidth, tags=ta,
                    tagswidth = self.tagswidth, t = " ", 
                    datewidth = self.datewidth))

            # Print the separator
            output(u" {done}----------{t:-<{datewidth}}-----{t:-<{textwidth}}-{t:-<{tagswidth}} ".format( 
                done = done_column_bottom, t="-", textwidth=self.textwidth,
                tagswidth=self.tagswidth, datewidth = self.datewidth))


class EditCommand(Command):
    u"""Edit the attributes of a task

usage: %s edit [task|list|tag] id=<id> [<attribute>=<value>]*

This command allows you to edit the attributes of an already entered task, list
or tag. You
must provide the id of the element to modify, and the attributes to modify. You can
edit multiple attributes at the same time. If the type of element to edit isn't
provided, "task" is assumed.

The possible attributes for a task are:
    task: the text of the task.
    due_date: the due date of the task, the value must have the same format than
        in the 'add' command: xx/xx/yyyy[:[h]h[:mm][am|pm]]
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
        global lib
        self.re_id = re.compile(u"^id=({0})$".format(lib.config["re.id"]))
        self.re_due_date = re.compile(u"^due_date={0}$".format(
            lib.config["re.date"]))
        self.re_priority = re.compile(u"^priority=({0})$".format(
            lib.config["re.priority"]))
        self.re_add_tags = re.compile(u"^add_tags=({0})$".format(
            lib.config["re.tags_list"]))
        self.re_remove_tags = re.compile(u"^remove_tags=({0})$".format(
            lib.config["re.tags_list"]))
        self.re_list = re.compile(u"list=({0})".format(
            lib.config["re.list_name"]))
        self.re_tol_priority = re.compile(u"^priority=(-?\d\d*)$")
        self.re_tol_name = re.compile(u"^name=({0}|{1})$".format(
            lib.config["re.list_name"], lib.config["re.tag_name"]))
        self.re_name = re.compile(u"^task=(.*)$")

    def execute(self, cmd, args):

        if len(args) == 0:
            output(st = u"[ERR] You must provide some arguments to edit an element. See 'yat help edit'.", 
                    f = sys.stderr)
            return

        if args[0] in [u"task", u"list", u"tag"]:
            element = args[0]
            args = args[1:]
        else:
            element = u"task"

        id = None
        task = None
        name = None
        due_date = None
        priority = None
        list = None
        add_tags = None
        remove_tags = None

        for a in args:
            res = self.re_id.match(a)
            if id == None and res != None:
                id = res.group(1)

            if element in [u"list", u"tag"]:
                res = self.re_tol_priority.match(a)
                if priority == None and res != None:
                    priority = int(res.group(1))

                res = self.re_tol_name.match(a)
                if name == None and res != None:
                    name = res.group(1)

            else:
                res = self.re_priority.match(a)
                if priority == None and res != None:
                    priority = int(res.group(1))
                    if priority > 3:
                        priority = 3
                
                res = self.re_due_date.match(a)
                if due_date == None and res != None:
                    try:
                        due_date = parse_input_date(res)
                    except ValueError:
                        output("[ERR] The due date isn't well formed. See 'yat help edit'.", 
                                f = sys.stderr)
                        return

                res = self.re_list.match(a)
                if list == None and res != None:
                    list = res.group(1)

                res = self.re_add_tags.match(a)
                if add_tags == None and res != None:
                    add_tags = res.group(1)

                res = self.re_remove_tags.match(a)
                if remove_tags == None and res != None:
                    remove_tags = res.group(1)

                res = self.re_name.match(a)
                if task == None and res != None:
                    task = res.group(1)
        
        if id == None:
            output(st = u"[ERR] You must provide an id to the edit command. See yat help edit.", 
                    f = sys.stderr)
            return

        if id == "1" and element in [u"tag", u"list"]:
            output(st = u"[ERR] You can't modify 'notag' or 'nolist'", f =
                    sys.stderr)
            return

        if element == u"list":
            try:
                lib.edit_list(id, name, priority)
            except yatlib.WrongListId:
                output(st = u"[ERR] {0} is not a valid list id.".format(id), 
                        f = sys.stderr)
        elif element == u"tag":
            try:
                lib.edit_tag(id, name, priority)
            except yatlib.WrongTagId:
                output(st = u"[ERR] {0} is not a valid tag id.".format(id), 
                        f = sys.stderr)
        else:
            # Process the tag names
            add_tags_ids = []
            if add_tags != None:
                for tag in lib.get_tags(add_tags.split(","), type_id = False,
                        can_create = True):
                    add_tags_ids.append(tag["id"])

            remove_tags_ids = []
            if remove_tags != None:
                for tag in lib.get_tags(remove_tags.split(","), type_id = False):
                    remove_tags_ids.append(tag["id"])

            # Process the list name
            if list != None:
                list_id = lib.get_list(list, type_id = False, 
                        can_create = True)["id"]
            else:
                list_id = None

            lib.edit_task(id, task, priority, due_date, list_id, add_tags_ids,
                    remove_tags_ids)
        pass

class DoneCommand(Command):
    u"""Set a task as completed.

usage: %s done (id=<id>|<regexp>)

This command allows you to mark a task as completed. A task completed won't be
deleted, but it won't be displayed by default with the 'show' command.

You have to provide either the id of the task (with 'id=<id>'), or the name of
the task. If you give the name of the task, you can use '*' and '?' as jokers.
But if you do so, be careful to surround your request with double quotes so that
the shell doesn't expand them.
"""

    alias = [u"done"]

    def __init__(self):
        global lib
        self.re_id = re.compile(u"^id=({0})$".format(lib.config["re.id"]))

    def execute(self, cmd, args):
        if len(args) == 0:
            output(st = u"[ERR] You must provide some informations to the command. See yat help done", 
                    f = sys.stderr)

        id = None
        regexp = []
        for a in args:
            res = self.re_id.match(a)
            if res != None:
                id = res.group(1)
                break
            regexp.append(a)

        regexp = " ".join(regexp)

        if id != None:
            tasks = lib.get_tasks(ids=[int(id)], group=False, order=False)
        else:
            tasks = lib.get_tasks(regexp = regexp, group=False, order = False)

        for task in tasks:
            lib.edit_task(task["id"], completed = True)

class CleanCommand(Command):
    u"""Delete all the completed tasks.

usage: %s clean [--force|-f|--interactive|-i]

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
        args = (" ".join(args)).split(" ")
        for a in args:
            res = self.re_force.match(a)
            if res != None:
                self.force = True
            res = self.re_interactive.match(a)
            if res != None:
                self.interactive = True

        if not self.force:
            if not yes_no_question(u"Are you sure you want to delete all your completed tasks ?"):
                return

        tasks = lib.get_tasks(order = False, group = False)
        tasks_ids = []
        for t in tasks:
            if t["completed"] == 1:
                if self.interactive:
                    txt = u"Do you want to delete this task:\n" + t["task"] 
                    txt += u" (priority: " + str(t["priority"])
                    txt += u", due date: " + parse_output_date(t["due_date"]) + u") ?"
                    if not yes_no_question(txt):
                        continue
                tasks_ids.append(t["id"])
        
        lib.remove_tasks(tasks_ids)


def isCommand(obj):
    u"""Check if the parameter is a class derived from Command, without being
    Command"""

    if inspect.isclass(obj):
        return (issubclass(obj, Command) and not(obj is Command))
    else:
        return False

def output(st = u"", f = None, linebreak = True):
    global lib
    if f == None:
        f = lib.output
    f.write(st.encode(lib.enc))
    if linebreak:
        f.write(os.linesep)

def input(f = None):
    global lib
    if f == None:
        f = lib.input
    return f.readline().encode(lib.enc)

def yes_no_question(txt, default = False, i = None, o = None):
    u"""Ask the user the 'txt' yes/no question (append ' (Y/n)' or (y/N)
    depending of the 'default' parameter) and return the answer with a boolean:
    True for yes and False for no. 'i' and 'o' are the input and output to use.
    If None, they use the ones defined in YatLib"""

    yn_txt = ""
    if default:
        yn_txt = "Y/n"
    else:
        yn_txt = "y/N"

    output(txt + " ("+ yn_txt + ")", f = o)
    rep = input(i).lower()
    while len(rep) == 0 or (rep[0] != "y" and rep[0] != "n" and rep[0] != "\n"):
        output(yn_txt + " :", f = o)
        rep = input().lower()

    if rep[0] == "\n":
        return default
    else:
        return rep[0] != "n"

def parse_input_date(regex_date):
    u"""This function transform the object returned by the date regexp in a
    timestamp. Raise a ValueError if there is an error in the date."""
    re_date = regex_date.groupdict()
    year = int(re_date["year"])
    if lib.config["cli.input_date"] == "dd/mm":
        month = int(re_date["x2"])
        day = int(re_date["x1"])
    else:
        month = int(re_date["x1"])
        day = int(re_date["x2"])

    hour = 0
    if re_date["hour"] != None: 
        hour = int(re_date["hour"])

    minute = 0
    if re_date["minute"] != None: 
        minute = int(re_date["minute"])

    apm = "am"
    if re_date["apm"] != None:
        apm = re_date["apm"]

    if lib.config["cli.input_time"] == "12" and apm == "pm":
        hour += 12

    d = datetime.datetime(year, month, day, hour, minute)
    return time.mktime(d.timetuple())

def parse_output_date(timestamp):
    u"""This function parse a timestamp into the format defined in the
    cli.output_datetime option. (empty string if the timestamp is infinite)"""
    date_string = ""
    if timestamp != float('+inf') and timestamp != float('-inf') and timestamp != float('+nan') and timestamp != float('-nan'):
        d = datetime.datetime.fromtimestamp(timestamp)
        date_string = u"{0:" + lib.config["cli.output_datetime"] + u"}"
        date_string = date_string.format(d)
    return date_string



def init():
    u"""Initialisation specific to this commandline program."""
    global lib

    lib.config["cli.task_ordering"] = lib.config.get("cli.task_ordering",
            "reverse:priority, due_date")
    lib.config["cli.display_group"] = lib.config.get("cli.display_group",
            "list")
    lib.config["cli.input_date"] = lib.config.get("cli.input_date",
            "dd/mm")
    lib.config["cli.input_time"] = lib.config.get("cli.input_time",
            "24")
    lib.config["cli.output_datetime"] = lib.config.get("cli.output_datetime",
            "%d/%m/%Y %H:%M")

    # Processing task_ordering option
    # Strip spaces and split on commas
    opt = "".join(lib.config["cli.task_ordering"].split(" ")).split(",")
    lib.config["cli.task_ordering"] = []
    for o in opt:
        order = o.split(":")
        if len(order) > 1 and order[0] == "reverse":
            reverse = True
            column = order[1]
        else:
            column = order[0]
        if column in ["priority", "due_date", "task", "id"]:
            lib.config["cli.task_ordering"].append(o)
        else:
            output(st=u"[ERR] Config file, option cli.task_ordering: '{0}' is not a valid ordering option. See the example config file for a valid option.".format(o), f = sys.stderr)

    # Default options
    if lib.config["cli.task_ordering"] == []:
        lib.config["cli.task_ordering"] = ["reverse:priority", "due_date"]

    if not lib.config["cli.display_group"] in ["list", "tag"]:
        output(u"[ERR] Config file, option cli.display_group: '{0}' is not a valid display group, it has to be \"list\" or \"tag\"".format(lib.config["cli.display_group"]), f = sys.stderr)
        lib.config["cli.display_group"] = "list"

    if not lib.config["cli.input_date"] in ["dd/mm", "mm/dd"]:
        output(u"[ERR] Config file, option cli.input_date: '{0}' is not a valid format, it has to be \"dd/mm\" or \"mm/dd\"".format(lib.config["cli.input_date"]), f = sys.stderr)
        lib.config["cli.input_date"] = "dd/mm"

    if not lib.config["cli.input_time"] in ["12", "24"]:
        output(u"[ERR] Config file, option cli.input_time: '{0}' is not a valid format, it has to be \"dd/mm\" or \"mm/dd\"".format(lib.config["cli.input_time"]), f = sys.stderr)
        lib.config["cli.input_time"] = "24"

    res = re.finditer("%(.)", lib.config["cli.output_datetime"])
    for g in res:
        if not g.group(1) in ["d", "m", "Y", "H", "I", "M", "p"]:
            output(u"[ERR] Config file, option cli.output_datetime: '{0}' is not a valid format, it has to be '%d', '%m', '%Y', '%H', '%I', '%M' or '%p'. See yatrc.sample for an example".format(g.group(0)), f = sys.stderr)
            lib.config["cli.output_datetime"] = "%d/%m/%Y %H:%M"
            break

    date_length = len(lib.config["cli.output_datetime"])
    if re.search("%Y", lib.config["cli.output_datetime"]):
        date_length += 2
    lib.config["cli.output_datetime_length"] = date_length


def main(argv):
    u"""
    Entry point of the program
    """
    global commands, aliases, progname, lib

    # Initialisation
    lib = yatlib.YatLib()
    init()

    # Getting the name of the program
    progname = argv[0]

    # Getting all the commands
    commands = dict(inspect.getmembers(sys.modules[__name__], isCommand))
    aliases = {}

    # Fill the aliases dictionnary
    for name, cmd in commands.iteritems():
        for a in cmd.alias:
            aliases[a] = cmd

    # Determining which command to use (default list)
    cmd = ListCommand()
    cmd_args = []
    cmd_alias = "tasks"
    if len(argv) > 1:
        if argv[1] in aliases:
            cmd = aliases[argv[1]]()
            cmd_alias = argv[1]
            cmd_args = argv[2:]
        else:
            cmd = ListCommand()
            cmd_args = argv[1:]

    # Executing command with the rest of the arguments
    cmd.execute(cmd_alias, cmd_args)

if __name__ == "__main__":
    main(sys.argv)

