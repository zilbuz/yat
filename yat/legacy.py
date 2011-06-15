#-*- coding:utf-8 -*-

u"""
yat.Library

This file contains the classes and functions needed for basic handling
of databases created with an old version of yat.

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

from yat import *
from exceptions import *

import re
import sqlite3

class V0_1(Yat):
    def __init__(self, current_lib, db):
        self.config = current_lib.config

        self._Yat__sql = sqlite3.connect(db)
        self._Yat__sql.row_factory = sqlite3.Row
        self._loaded_lists = {}
        self._loaded_tags = {}
        self._loaded_tasks = {}
        self._loaded_lists[1] = NoList(self)
        self._loaded_tags[1] = NoTag(self)
        methods_not_implemented = [
            '_add_task', '_edit_task', '_add_group', '_edit_group',
            '_add_note', '_edit_note', 'remove_tags', 'remove_tasks',
            'remove_lists', 'remove_notes'
        ]
        for m in methods_not_implemented: setattr(self, m, self.not_implemented)

    def delete_tables(self):
        with self.__sql:
            self.__sql.execute('drop table tasks')
            self.__sql.execute('drop table lists')
            self.__sql.execute('drop table tags')
            self.__sql.commit()

    # Limit the API to what is actually supported by the DB
    def get_tasks(self, ids=None, names=None, regexp=None):
        return super(V0_1, self).get_tasks(ids=ids, names=names, regexp=regexp)

    def get_tags(self, ids=None, names=None, regexp=None):
        return super(V0_1, self).get_tags(ids=ids, names=names, regexp=regexp)

    def not_implemented(self, *args):
        raise NotImplemented

    def get_notes(self, task=None, ids=None, names=None, regexp=None):
        return []
    # Reminder : an extract is a tuple of a list of loaded tasks
    # and a list of DB rows
    def _get_task_objects(self, extract):
        tasks = extract[0]
        task_rows = extract[1]
        for r in task_rows:
            tsk = Task(self)
            tsk.id = int(r['id'])
            tsk.content = r["task"]
            tsk.priority = int(r["priority"])
            tsk.due_date = float(r["due_date"])
            tsk.completed = r["completed"]
            tsk.created = float(r["created"])
            tsk.list = self.get_list(int(r["list"]))

            # We have to do the tags manually because get_tags(task)
            # relies on a DB scheme that doesn't exist yet
            tag_ids = [int(i) for i in r['tags'].split(',')]
            tsk.tags = set(self.get_tags(ids=tag_ids))
            tasks.append(tsk)
            self._loaded_tasks[tsk.id] = tsk
        return tasks

    def _get_group_objects(self, cls, loaded_objects, extract):
        groups = extract[0]
        rows = extract[1]
        for r in rows:
            g = cls(self)
            g.id = int(r["id"])
            g.content = r["name"]
            g.priority = r["priority"]
            g.created = r["created"]
            g.changed = False
            loaded_objects[g.id] = g
            groups.append(g)
        return groups

def analyze_db(filename=None, current_lib=None):
    u"""Check the version of the database pointed by filename, and return the
    appropriate library.
    
    Raises FileNotFound if "filename" doesn't exists.
    Raises UnknownDBVersion if the database is more recent than the program."""

    # If the file doesn't exist, raise an exception
    if not os.path.isfile(filename):
        raise FileNotFound

    # Connect to the database
    sql = sqlite3.connect(filename)
    sql.row_factory = sqlite3.Row
    
    # Get the version number of the database
    with sql:
        try:
            version = sql.execute(u"""select value from metadata where
                    key='version'""").fetchone()["value"]
        except sqlite3.OperationalError:
            # The metadata table doesn't exist yet, so it's a v0.1 db file
            version = "0.1"

    # Get the appropriate library
    if version == "0.1":
        lib = V0_1(current_lib, filename)
    elif version == "0.2":
        lib = Yat(db_path=filename)
    else:
        # Apparently, the database is more recent than the yat used
        raise UnknownDBVersion

    return lib
