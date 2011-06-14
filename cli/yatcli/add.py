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

import yatcli
from command import Command

class AddCommand (Command):
    u"""Add a task, a list or a tag

usage: {name} add [task | list | tag] "<informations>"

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
    mm/dd, depending of the yatcli.input_date option, and hh is the hour in 24 or
    12 hour format, depending of the yatcli.input_time option.
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
        super(AddCommand, self).__init__()

        self.breakdown = True
        self.cmd = 'task'
        self.content = []
        self.tags_to_add = []
        whole_task = ['tag', 'list', 'parent', 'date', 'priority', 'word', None]
        self.arguments = (['type', 'tag', 'list', 'parent', 'date', 'priority', 'word'], {
            # The first argument, 'tag', 'task' or 'list'
            'type':     ('^(?P<value>task|list|tag)$',
                         lambda x: whole_task if x == 'task' else (
                             ['list_name'] if x == 'list' else ['tag_name']),
                         lambda x,y: setattr(self, 'cmd', x)),

            # A tag element of a task definition
            'tag':      ('^#(?P<value>{0})$'.format(yatcli.lib.config["re.tag_name"]),
                         whole_task, lambda x,y: self.tags_to_add.append(x)),

            # The list element of a task definition
            'list':     ('^>(?P<value>{0})$'.format(yatcli.lib.config['re.list_name']),
                         whole_task, lambda x,y: setattr(self, 'list', x)),
            
            'parent':   ('^~(?P<value>{0})$'.format(yatcli.lib.config['re.id']),
                         whole_task, lambda x,y: setattr(self, 'parent', x)),

            # The priority for a task only !
            'priority': ('^\*(?P<value>{0})$'.format(yatcli.lib.config['re.priority']),
                         whole_task, lambda x,y: setattr(self, 'priority', int(x))),

            'date':     ('^\^(?P<value>{0})$'.format(yatcli.lib.config['re.date']),
                         whole_task, lambda x,y: setattr(self, 'date', x)),

            # Will be added to the content.
            'word':     ('^.*$', whole_task,
                         lambda x,y: self.content.append(x)),

            'tag_name': ('^(?P<value>{0})$'.format(yatcli.lib.config['re.tag_name']),
                         ['group_priority', None], lambda x,y: self.content.append(x)),

            'list_name':('^(?P<value>{0})$'.format(yatcli.lib.config['re.list_name']),
                         ['group_priority', None], lambda x,y: self.content.append(x)),

            'group_priority': ('^-?\d\d*$', [None],
                               lambda x,y: setattr(self, 'priority', int(x)))
        })


    def edit_content(self, obj):
        if self.content == []:
            yatcli.output("[ERR] There is no actual content !.", 
                    f = sys.stderr,
                    foreground = yatcli.colors.errf, background = 
                    yatcli.colors.errb, bold = yatcli.colors.errbold)
            return
        obj.content = ' '.join(self.content)

    def get_object(self):
        if self.cmd == 'list':
            return yatcli.yat.List(yatcli.lib)
        elif self.cmd == 'tag':
            return yatcli.yat.Tag(yatcli.lib)
        elif self.cmd == 'task':
            return yatcli.yat.Task(yatcli.lib)

    def edit_tags(self, obj):
        new_tags = set()
        for n in self.tags_to_add:
            try:
                new_tags.add(yatcli.lib.get_tag(n, False))
            except:
                #If the tags don't exist, create them
                new_tag = yatcli.yat.Tag(yatcli.lib)
                new_tag.content = n
                new_tags.add(new_tag)
        obj.tags |= new_tags

    def execute(self, cmd, args):
        self.parse_arguments(self.parse_options(args))
        obj = self.get_object()
        if self.cmd == 'task':
            # Set the tags
            self.edit_tags(obj)

            #Set the list
            try:
                obj.list = yatcli.lib.get_list(self.list, False)
            except yatcli.yat.WrongName:
                obj.list = yatcli.yat.List(yatcli.lib)
                obj.list.content = self.list
            except AttributeError:
                # It means the list hasn't been specified
                pass

            # Set the parent
            try:
                obj.parent = yatcli.lib.get_task(int(self.parent))
            except yatcli.yat.WrongId:
                yatcli.output("[ERR] The specified parent task doesn't exist.", 
                        f = sys.stderr,
                        foreground = yatcli.colors.errf, background = 
                        yatcli.colors.errb, bold = yatcli.colors.errbold)
                return
            except AttributeError:
                # The parent hasn't been specified
                pass

            # Set the due_date
            try:
                obj.due_date = yatcli.parse_input_date(self.due_date)
            except ValueError:
                yatcli.output("[ERR] The due date isn't well formed. See 'yat help add'.", 
                        f = sys.stderr,
                        foreground = yatcli.colors.errf, background = 
                        yatcli.colors.errb, bold = yatcli.colors.errbold)
                return
            except AttributeError:
                pass

        # Common attributes
        self.edit_content(obj)
        try:
            obj.priority = self.priority
        except AttributeError:
            pass
        obj.save(yatcli.lib)
