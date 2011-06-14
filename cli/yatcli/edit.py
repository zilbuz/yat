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
from add import AddCommand

class EditCommand(AddCommand):
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
        # We skip the AddCommand __init__()
        super(AddCommand, self).__init__()

        self.breakdown = False
        self.cmd = 'task'
        self.content = []
        self.tags_to_add = []
        self.tags_to_rm = []
        whole_task = ['tags', 'list', 'rm_tags', 'parent', 'date', 'priority', 'task_name', None]
        self.arguments = (['type', 'id'], {
            # The first argument, 'tag', 'task' or 'list'
            'type':     ('^(?P<value>task|list|tag)$', ['id'],
                         lambda x,y: setattr(self, 'cmd', x)),

            'id':       ('^id=(?P<value>{0})$'.format(yatcli.lib.config["re.id"]),
                         lambda x: (
                             ['rm_tags', 'tags', 'list', 'parent',
                              'date', 'priority', 'task_name']
                             if self.cmd == 'task' else 
                             ['list_name', 'group_priority'] if self.cmd == 'list' else
                             ['tag_name', 'group_priority']),
                         lambda x,y: setattr(self, 'id', int(x))),

            # A tag element of a task definition
            'tags':      ('^add_tags=(?P<value>{0}(,{0})*)$'.format(yatcli.lib.config["re.tag_name"]),
                         whole_task, lambda x,y: self.tags_to_add.extend(x.split(','))),

            'rm_tags':      ('^remove_tags=(?P<value>{0}(,{0})*)$'.format(yatcli.lib.config["re.tag_name"]),
                         whole_task, lambda x,y: self.tags_to_rm.extend(x.split(','))),

            # The list element of a task definition
            'list':     ('^list=(?P<value>{0})$'.format(yatcli.lib.config['re.list_name']),
                         whole_task, lambda x,y: setattr(self, 'list', x)),
            
            'parent':   ('^parent=(?P<value>{0})$'.format(yatcli.lib.config['re.id']),
                         whole_task, lambda x,y: setattr(self, 'parent', x)),

            # The priority for a task only !
            'priority': ('^priority=(?P<value>{0})$'.format(yatcli.lib.config['re.priority']),
                         whole_task, lambda x,y: setattr(self, 'priority', x)),

            'date':     ('^due_date=(?P<value>{0})$'.format(yatcli.lib.config['re.date']),
                         whole_task, lambda x,y: setattr(self, 'date', x)),

            # Will be added to the content.
            'task_name':('^task=(?P<value>.*)$', whole_task,
                         lambda x,y: setattr(self, 'content', [x])),

            'tag_name': ('^name=(?P<value>{0})$'.format(yatcli.lib.config['re.tag_name']),
                         ['group_priority', None], lambda x,y: setattr(self, 'content', [x])),

            'list_name':('^name=(?P<value>{0})$'.format(yatcli.lib.config['re.list_name']),
                         ['group_priority', None], lambda x,y: setattr(self, 'content', [x])),

            'group_priority': ('^priority=(?P<value>-?\d\d*)$',
                               lambda x: ['tag_name', None] if self.cmd == 'tag'
                               else ['list_name', None],
                               lambda x,y: setattr(self, 'priority', x))
        })

    def edit_content(self, obj):
        if self.content == []:
            return
        obj.content = " ".join(self.content)

    def edit_tags(self, obj):
        super(EditCommand, self).edit_tags(obj)
        obj.tags -= set(yatcli.lib.get_tags(names=self.tags_to_rm))

    def get_object(self):
        return getattr(yatcli.lib, 'get_{0}'.format(self.cmd))(self.id)
