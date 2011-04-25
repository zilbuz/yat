#!/usr/bin/env python

from Yat import *

import datetime
import locale
import os
import pickle
import re
import sqlite3
import sys
import time

current_lib = Yat()
List.class_lib = current_lib
Tag.class_lib = current_lib
Task.class_lib = current_lib

class V0_1:
    def __init__(self, current_lib, db):
        self.enc = current_lib.config 

        self.config = current_lib.config

        self.__sql = sqlite3.connect(db)
        self.__sql.row_factory = sqlite3.Row
        self.__list_ids = {}
        self.__tag_ids = {}
        self.__task_ids = {}

    def _get_tasks(self, ids=None, regexp=None):
        if ids == None and regexp == None:
            task_rows = self.__sql.execute('select * from tasks').fetchall()
        else:
            task_rows = set()
            if ids != None:
                for i in ids:
                    task_rows.add(self.__sql.execute(u'''select * from tasks
                                                     where id=?
                                                     ''', (i,)).fetchone())
            if regexp != None:
                task_rows |= self.__sql.execute(u'''select * from tasks
                                                where regexp task ?
                                                ''', (regexp,)).fetchall()

        tasks = []
        self.__list_ids[1] = NoList()
        self.__tag_ids[1] = NoTag()
        for r in task_rows:
            try:
                t = task_ids[int(r["id"])]
            except:
                t = Task(current_lib)
                t.content = r["task"]
                t.priority = int(r["priority"])
                t.due_date = r["due_date"]
                t.completed = r["completed"]
                t.created = r["created"]
                try:
                    t.list = self.__list_ids[int(r["list"])]
                except:
                    list_row = self.__sql.execute(u'''select * from lists
                                                  where id=?
                                                  ''', (int(r["list"]),)).fetchone()
                    # Get the list from the up-to-date DB if it exists
                    list_ = current_lib.get_list(list_row["name"], False, False)
                    if list_.id == None:
                        list_.content = list_row["name"]
                        list_.priority = list_row["priority"]
                        list_.created = list_row["created"]
                    self.__list_ids[int(r["list"])] = list_
                    t.list = list_

                tag_ids = [int(i) for i in r['tags'].split(',')]
                t.tags = []
                for i in tag_ids:
                    try:
                        t.tags.append(self.__tag_ids[i])
                    except:
                        tag_row = self.__sql.execute(u'''select * from tags
                                                     where id=?''', (i,))
                        tag_ = current_lib.get_tags([tag_row['name']], False, False)[0]
                        if tag_.id == None:
                            tag_.content = tag_row['name']
                            tag_.priority = tag_row['priority']
                            tag_.created = tag_row['created']
                        self.__tag_ids[i] = tag_
                        t.tags.append(tag_)
                tasks.append(t)
                self.__task_ids[int(r["id"])] = t

        return tasks

    def _get_groups(self, group_ids, get_group, table, ids = None, regexp = None):
        if ids == None and regexp == None:
            group_rows = self.__sql.execute('select * from %s' % table).fetchall()
        else:
            if ids != None:
                for i in ids:
                    group_rows.append(self.__sql.execute(u'''
                                                        select * from %s 
                                                        where id=?
                                                        ''' % table,
                                                        (i,)).fetchone())
            if regexp != None:
                group_rows.extend(self.__sql.execute(u'''select * from %s
                                                    where regexp name ?
                                                    ''' % table,
                                                    (regexp,)).fetchall())

        groups = set()
        for r in group_rows:
            try:
                groups.add(group_ids[int(r["id"])])
            except:
                group_ = get_group(r["name"], False, False)
                if group_.id == None:
                    group_.content = r["name"]
                    group_.priority = r["priority"]
                    group_.created = r["created"]
                group_ids[int(r["id"])] = group_
                groups.add(group_)

        return groups

    def _get_lists(self, ids = None, regexp = None):
        return self._get_groups(self.__list_ids, current_lib.get_list, 'lists',
                                ids, regexp)

    def _get_tags(self, ids = None, regexp = None):
        return self._get_groups(self.__tag_ids,
                                lambda tag, b1, b2: current_lib.get_tags([tag],
                                                                         b1,
                                                                         b2)[0],
                                'tags', ids, regexp)

def analyze_db(db_file):
    return V0_1(current_lib, db_file)
ex_lib = analyze_db(sys.argv[1])
for t in ex_lib._get_tasks():
    t.save(current_lib)
for l in ex_lib._get_lists():
    l.save(current_lib)
for t in ex_lib._get_tags():
    t.save(current_lib)
