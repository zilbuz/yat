#!/usr/bin/env python

from Yat import *

import re
import sqlite3

class V0_1:
    def __init__(self, current_lib, db):
        self.enc = current_lib.config 
        self.current_lib = current_lib

        self.config = current_lib.config

        self.__sql = sqlite3.connect(db)
        self.__sql.row_factory = sqlite3.Row
        self.__list_ids = {}
        self.__tag_ids = {}
        self.__task_ids = {}

    def delete_tables(self):
        with self.__sql:
            self.__sql.execute('drop tasks')
            self.__sql.execute('drop lists')
            self.__sql.execute('drop tags')
            self.__sql.commit()

    def get_tasks(self, ids=None, regexp=None):
        if ids == None and regexp == None:
            task_rows = self.__sql.execute('select * from tasks').fetchall()
        else:
            task_rows = set()
            if ids != None:
                for i in ids:
                    with self.__sql:
                        task_rows.add(self.__sql.execute(u'''select * from tasks
                                                        where id=?
                                                        ''', (i,)).fetchone())
            if regexp != None:
                with self.__sql:
                    task_rows |= self.__sql.execute(u'''select * from tasks
                                                    where regexp task ?
                                                    ''', (regexp,)).fetchall()

        tasks =set() 
        self.__list_ids[1] = NoList()
        self.__tag_ids[1] = NoTag()
        for r in task_rows:
            try:
                t = task_ids[int(r["id"])]
            except:
                t = Task(self.current_lib)
                t.content = r["task"]
                t.priority = int(r["priority"])
                t.due_date = r["due_date"]
                t.completed = r["completed"]
                t.created = r["created"]
                try:
                    t.list = self.__list_ids[int(r["list"])]
                except:
                    with self.__sql:
                        list_row = self.__sql.execute(u'''select * from lists
                                                    where id=?
                                                    ''', (int(r["list"]),)).fetchone()
                    # Get the list from the up-to-date DB if it exists
                    list_ = self.current_lib.get_list(list_row["name"], False)
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
                        with self.__sql:
                            tag_row = self.__sql.execute(u'''select * from tags
                                                        where id=?''', (i,)).fetchone()
                        tag_ = self.current_lib.get_tag(tag_row['name'], False)
                        if tag_.id == None:
                            tag_.content = tag_row['name']
                            tag_.priority = tag_row['priority']
                            tag_.created = tag_row['created']
                        self.__tag_ids[i] = tag_
                        t.tags.append(tag_)
                tasks.add(t)
                self.__task_ids[int(r["id"])] = t

        return tasks

    def _get_groups(self, group_ids, get_group, table, ids = None, regexp = None):
        if ids == None and regexp == None:
            with self.__sql:
                group_rows = self.__sql.execute('select * from %s' % table).fetchall()
        else:
            if ids != None:
                for i in ids:
                    with self.__sql:
                        group_rows.append(self.__sql.execute(u'''
                                                            select * from %s 
                                                            where id=?
                                                            ''' % table,
                                                            (i,)).fetchone())
            if regexp != None:
                with self.__sql:
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

    def get_lists(self, ids = None, regexp = None):
        return self._get_groups(self.__list_ids, self.current_lib.get_list, 'lists',
                                ids, regexp)

    def get_tags(self, ids = None, regexp = None):
        return self._get_groups(self.__tag_ids,
                                lambda tag, b1, b2: self.current_lib.get_tags([tag],
                                                                         b1,
                                                                         b2)[0],
                                'tags', ids, regexp)

def analyze_db(filename=None, current_lib=None):
    return V0_1(current_lib, filename)
