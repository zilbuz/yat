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

class MigrateCommand(Command):
    u"""Change the completed status of a task.

usage : {name} import <file.db>
        {name} migrate

The import version will import all the tasks contained in <file.db> into the
database currently specified n your .yatrc file. The beauty is, it will work
with old versions of the database !

The migrate version is useful when you are upgrading yat. It will convert your
database into a format suited for the new version of yat.
"""

    alias = [u"import", u"migrate"]

    def __cmd_switch(self, alias):
        '''Analyzes the alias used and initialize the environment accordingly.
        It returns the list of the possible following arguments.'''
        if alias == 'import':
            self.files = []
            self.migration = False
            return ['filename']
        elif alias == 'migrate':
            self.files = [yatcli.lib.config['yatdir'] + '/yat.db']
            return [None]

    def __init__(self):
        self.arguments = (self.__cmd_switch, {
            'filename': ('^.*$', ['filename', None],
                         lambda x,y: self.files.append(x))
        })
        super(MigrateCommand, self).__init__()

    def execute(self, cmd, args):
        self.command = cmd
        self.parse_arguments(args)

        for f in self.files:
            # leg is the library associated with the DB to import.
            leg = yatcli.yat.legacy.analyze_db(filename = f,
                                            current_lib = yatcli.lib)

            objects = leg.get_tasks() + leg.get_lists() + leg.get_tags()
            if self.migration:
                # When migrating, once we have all the old data, we don't want
                # the old layout sticking around :)
                leg.delete_tables()
                yatcli.lib.create_tables()
            for o in objects:
                o.save(yatcli.lib)

