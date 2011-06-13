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

import yatcli
from command import Command

class RemoveCommand (Command):
    u"""Remove a task, a list or a tag

usage: {name} remove [task | list | tag] [options] [<regexp>|id=<id_nb>]

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
    --force, -f
        Don't ask for a global confirmation, just delete.
    --interactive, -i
        Ask a confirmation for every deleted element.
"""

    alias = [u"remove", u"rm"]
    def __init__(self):
        self.options = ([
            ('f', 'force', 'force', None),
            ('i', 'interactive', 'interactive', None),
            ('r', 'recursive', 'recursive', None),
            ('n', 'no-recursive', 'no_recursive', None)
        ])

        self.ids_to_remove = []
        self.regexp = None
        self.select_type('task')
        self.arguments = (['type', 'id', 'regexp'], {
            'type'  :   ('^(?P<value>task|list|tag)$',
                         ['id', 'regexp'], self.select_type),
            'id'    :   ('^id=(?P<value>[0-9]+)$',
                         ['id', 'regexp', None], self.add_id_to_remove),
            'regexp':   ('^(?P<value>.*)$', ['id', 'regexp', None],
                         lambda x,y: setattr(self, 'regexp', self.regexp+' '+x) or True if self.regexp != None else setattr(self, 'regexp', x) or True)
        })
        super(RemoveCommand, self).__init__()

    def select_type(self, value, trail=None):
        u'''Select the internal methods to use to process the arguments.'''
        self.interactive_text = lambda x: ('Do you want to delete this {0}:\n'.format(value) +
                            '\n  {0.content}\n    priority: {0.priority}'.format(x))
        self.get_obj = getattr(yatcli.lib, 'get_{0}s'.format(value))
        if value == 'list':
            self.removal_function = lambda x: (
                yatcli.lib.remove_lists(x, (not self.no_recursive or
                                            self.recursive),
                                        (self.recursive and
                                         not self.no_recursive)))
        elif value == 'task':
            old_text = self.interactive_text
            self.interactive_text = (lambda x: old_text(x)+
                                     '\n    due date: {0}'
                                     .format(yatcli.parse_output_date(x.due_date)))

            self.removal_function = lambda x: (
                yatcli.lib.remove_tasks(x,
                                        not self.no_recursive or
                                        self.recursive))
        else:
            self.removal_function = getattr(yatcli.lib, 'remove_{0}s'.format(value))
        return False

    def add_id_to_remove(self, value, trail):
        if (self.interactive and not
            yatcli.yes_no_question(self.interactive_text(
                self.get_obj(ids=[int(value)])), default=True)):
            return True
        self.ids_to_remove.append(int(value))
        return True

    def process_regexp(self):
        if self.regexp == None:
            return
        if (self.regexp == '*' and not self.force and 
            not yatcli.yes_no_question(
                "This operation is potentially disastrous. Are you so desperate ?",
                default = True)):
            return
        objects = self.get_obj(regexp=self.regexp)
        if not self.force and self.interactive:
            for o in objects:
                if yatcli.yes_no_question(self.interactive_text(o)):
                    self.ids_to_remove.append(o.id)
            return
        self.ids_to_remove.extend([o.id for o in objects])
        return

    def execute(self, cmd, args):
        if not self.parse_arguments(self.parse_options(args)):
            print self.__doc__.split('\n',1)[0]," ",args
            return
        self.process_regexp()
        self.removal_function(self.ids_to_remove)
