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

class ImportCommand(Command):
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

    def __init__(self):
        self.re_id = re.compile(u"^id=({0})$".format(cli.lib.config["re.id"]))

    def execute(self, cmd, args):
        if cmd == u"migrate":
            # When migrating, the only DB to import is the default one.
            files = [cli.lib.config['yatdir'] + '/yat.db']
        elif len(args) == 0:
            cli.output(st = u"[ERR] You must provide some informations to the command. See 'yat help import'", 
                    f = sys.stderr,
                    foreground = cli.colors.errf, background = cli.colors.errb,
                    bold = cli.colors.errbold)
            return
        else:
            files = args

        for f in files:
            # leg is the library associated with the DB to import.
            migration = (cmd == u'migrate' and
                         f == cli.lib.config['yatdir'] + '/yat.db')
            leg = cli.Yat.legacy.analyze_db(filename = f,
                                            current_lib = cli.lib,
                                            migration = migration)
            # So far, we get the objects as sets (hence the strange operator).
            # It might change.
            objects = leg.get_tasks() + leg.get_lists() + leg.get_tags()
            if migration:
                # When migrating, once we have all the old data, we don't want
                # the old layout sticking around :)
                leg.delete_tables()
                cli.lib.create_tables()
            for o in objects:
                o.save(cli.lib)

