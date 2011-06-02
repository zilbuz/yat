#-*- coding:utf-8 -*-

u"""
yat.Library

Minimalistic library to manipulate the data of yat: the configuration file and
the sqlite database.

This file also contain the exceptions used by yat programs.


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

import datetime
import locale
import os
import pickle
import re
import sqlite3
import sys
import time
from models import *
from exceptions import *

# Current version of yat
# Is of the form "last_tag-development_state"
VERSION = u"0.2b-dev"
# Current version for the database.
DB_VERSION = u"0.2"

class Yat:

    @staticmethod
    def regexp(expr, item):
        u'''Compare an expression to a string and returns True if there
        is a match.
        '''
        if expr == None:
            return False
        # Replace all * and ? with .* and .? (but not \* and \?)
        regex = re.sub(r'([^\\]?)\*', r'\1.*', expr)
        regex = re.sub(r'([^\\])\?', r'\1.?', regex)
        # Replace other \ with \\
        regex = re.sub(r'\\([^*?])', r'\\\\\1', regex)
        # Replace ^ and $ by \^ and \$
        regex = re.sub(r'\^', r'\^', regex)
        regex = re.sub(r'\$', r'\$', regex)
        # Add ^ and $ to the regexp
        regex = r'^' + regex + r'$'
        return len(re.findall(regex, item)) > 0

    def __init__(self, config_file_path = None, db_path = None):
        u"""Constructor:
            * load the configuration file
            * open a connection with the database
            * initialise some variables
        """
        # Default encoding
        self.enc = locale.getpreferredencoding()

        # Default input : stdin
        self.input = sys.stdin

        # Default output : stdout
        self.output = sys.stdout

        # Config file
        if config_file_path == None:
            config_file_path = os.environ.get("HOME") + "/.yatrc"
        else:
            if not os.path.isfile(config_file_path):
                raise WrongConfigFile, config_file_path

        # Loading configuration
        self.config = {}
        try:
            with open(config_file_path, "r") as config_file:
                for line in config_file:
                    if not (re.match(r'^\s*#.*$', line) or re.match(r'^\s*$', line)):
                        line = re.sub(r'\s*=\s*', "=", line, 1)
                        line = re.sub(r'\n$', r'', line)
                        opt = line.split('=', 1)
                        self.config[opt[0]] = opt[1]
            config_file.close()
        except IOError:
            # No .yatrc
            pass

        # For each option, loading default if it isn't defined
        self.config["yatdir"] = self.config.get("yatdir", "~/.yat")
        self.config["default_priority"] = self.config.get("default_priority", "1")

        # Default timestamp: infinite
        self.config["default_date"] = float('+inf')

        # Create yat directory
        if self.config["yatdir"][0] == "~":
            self.config["yatdir"] = os.environ.get("HOME") + self.config["yatdir"][1:]
        if not os.path.isdir(self.config["yatdir"]):
            os.makedirs(self.config["yatdir"], mode=0700)

        # Connect to sqlite db
        if db_path == None:
            self.__sql = sqlite3.connect(self.config["yatdir"] + "/yat.db")
        else:
            self.__sql = sqlite3.connect(db_path)

        # Use Row as row_factory to add access by column name and other things
        self.__sql.row_factory = sqlite3.Row

        # Add a function to support the REGEXP() operator
        self.__sql.create_function("regexp", 2, Yat.regexp)

        # Verify the existence of the database and create it if it doesn't exist
        # (very basic)
        try:
            with self.__sql:
                self.__sql.execute("PRAGMA foreign_keys=ON")
                self.__sql.execute("select * from tags")
        except sqlite3.OperationalError:
            self.create_tables()

        # Get application pid
        self.__pid = os.getpid()

        # Hidden config (regexp)
        self.config["re.id"] = u"\d*?"
        self.config["re.priority"] = u"\d"
        self.config["re.date"] = u"(?P<x1>\d?\d)/(?P<x2>\d\d)/(?P<year>\d{4})(:(?P<hour>\d?\d)(:(?P<minute>\d\d))?(?P<apm>am|pm)?)?"
        self.config["re.tag_name"] = u".*"
        self.config["re.tags_list"] = u"{0}?(,{0}?)*".format(
                self.config["re.tag_name"])
        self.config["re.list_name"] = u".*"

        # Dictionary used in the sorting of the tasks

        self.__operators = {}
        self.__operators["<"] = lambda x, y: x < y
        self.__operators[">"] = lambda x, y: x > y
        self.__operators[">="] = lambda x, y: x >= y
        self.__operators["<="] = lambda x, y: x <= y

        self.__loaded_tasks = {}
        self.__loaded_lists = {}
        self.__loaded_tags = {}
        self.__loaded_notes = {}
        pass

    def delete_tables(self):
        u'''Delete all the tables created by yat from the DB.
        This operation CANNOT be reverted !
        '''
        with self.__sql:
            self.__sql.execute('drop table if exists tasks')
            self.__sql.execute('drop table if exists lists')
            self.__sql.execute('drop table if exists tags')
            self.__sql.execute('drop table if exists tagging')
            self.__sql.execute('drop table if exists notes')
            self.__sql.execute('drop table if exists metadata')
            self.__sql.commit()

    def create_tables(self):
        u''' Create the necessary tables in the DB. This might overwrite
        data, please proceed with caution.
        '''
        self.delete_tables()
        with self.__sql:
            self.__sql.execute("""
                create table lists (
                    id integer primary key,
                    content text,
                    priority integer,
                    last_modified real,
                    created real,
                    hash_id varchar(64)
                    )""")
            self.__sql.execute("""
                create table tags (
                    id integer primary key,
                    content text,
                    priority integer,
                    last_modified real,
                    created real,
                    hash_id varchar(64)
                    )""")
            self.__sql.execute("""
                create table tasks (
                    id integer primary key,
                    content text,
                    parent integer references tasks(id) on delete cascade,
                    priority int,
                    due_date real,
                    list integer references lists(id) on delete cascade,
                    completed integer,
                    last_modified real,
                    created real,
                    hash_id varchar(64)
                )""")
            self.__sql.execute("""
                create table notes (
                    id integer primary key,
                    content text,
                    task integer references tasks(id) on delete cascade,
                    created real,
                    hash_id varchar(64)
                )""")
            self.__sql.execute("""
                create table tagging (
                    tag integer references tags(id) on delete cascade,
                    task integer references tasks(id) on delete cascade
                    )""")
            self.__sql.execute("""
                create table metadata (
                    key varchar(30),
                    value varchar(128)
                    )""")
            self.__sql.execute("""insert into metadata values ("version",
                    ?)""", (DB_VERSION,))
            self.__sql.commit()

    def get_task(self, value, value_is_id = True):
        u'''Get one task. Value can be either an ID or a name. It is
        treated as indicated by the value of value_is_id : True for ID
        and False for a name.'''
        if value_is_id:
            try:
                return self.get_tasks([int(value)])[0]
            except IndexError:
                raise WrongId
        try:
            return self.get_tasks(names=[value])[0]
        except IndexError:
            raise WrongName

    def get_loaded_tasks(self):
        u'''Returns a list of all the tasks that were already pulled from
        the DB.'''
        return [t for t in self.__loaded_tasks.itervalues()]

    def __extract_rows(self, table_name, loaded_objects,
                       ids, names, regexp, extra_criteria = None):
        u'''Extract the data out of the DB. It also checks wether it was already
        loaded, in which case it replaces it by the object.
        Arguments:
            str:table_name : The name of the table from where the data will be
                             extracted
            dict:loaded_objects: dict to check wether a row was already loaded
                                 or not.
            list(int):ids:  A list of ids to load.
            list(str):names:    A list of *exact* names to load.
            str:regexp:     A regexp to compare with the content of the data.
            (string, (values)):extra_criteria:  The string is a SQL predicat
                such as 'parent=? and id=?' and "values" is a tuple containing
                the values to insert in the string.

        If ids, names and regexp are all None, the whole table will be fetched.

        It returns a tuple of list. The first list contains all the objects
        already loaded, the second the raw data to process.'''
        loaded = []
        if ids == None and names == None and regexp == None:
            if extra_criteria == None:
                rows = self.__sql.execute(u'select * from {0}'
                                          .format(table_name)).fetchall()
            else:
                rows = self.__sql.execute(u'select * from {0} where {1}'
                                          .format(table_name,
                                                  extra_criteria[0]),
                                          extra_criteria[1]).fetchall()
        else:
            if extra_criteria == None:
                extra_criteria = ('', [])
            else:
                extra_criteria = ('and ' + extra_criteria[0], list(extra_criteria[1]))
            if ids == None:
                ids = []
            if names == None:
                names = []
            rows = self.__sql.execute(u'''select * from {0}
                                           where (id in ({1}) or 
                                           content in ({2}) or
                                           content regexp ?) {3}'''
                                               .format(table_name,
                                                       ', '.join('?'*len(ids)),
                                                       ', '.join('?'*len(names)),
                                                       extra_criteria[0]),
                                               (ids + names + [regexp] +
                                                extra_criteria[1])).fetchall()
        set_rows = set(rows)
        for r in rows:
            try:    # Try to fetch the loaded object.
                loaded.append(loaded_objects[int(r['id'])])
                set_rows.remove(r)  # If it is there, the row is useless
            except KeyError as e:
                pass
        return (loaded, list(set_rows))

    def get_tasks(self, ids=None, names=None, regexp=None, group=None):
        u'''Returns a list of tasks matching the input data. If ids, names,
        regexp and group all equal None, every task will be fetched.'''
        loaded = []
        if group != None:
            if ids == None: ids = []    # Otherwise, it would pull everything
            if issubclass(type(group), List):
                rows = self.__sql.execute(u'''select * from tasks
                                          where list=?''', (group.id,)
                                         ).fetchall()
            elif issubclass(type(group), Tag):
                rows = self.__sql.execute(u'''select tasks.*
                                          from tasks, tagging
                                          where tagging.tag=? and
                                          tasks.id=tagging.task''', (group.id,)
                                         ).fetchall()
            else: rows=[]
            set_rows = set(rows)
            for r in rows:
                try:
                    loaded.append(self.__loaded_tasks[int(r['id'])])
                    set_rows.remove(r)
                except KeyError as e:
                    pass
            loaded = self.__get_task_objects((loaded, list(set_rows)))
        return loaded + self.__get_task_objects(
            self.__extract_rows("tasks", self.__loaded_tasks,
                                ids, names, regexp))

    def get_children(self, task):
        u'''Returns all the direct subtasks of a given task.'''
        rows = self.__sql.execute(u'''select * from tasks where parent=?''',
                                  (task.id,)).fetchall()
        loaded = []
        set_rows = set(rows)
        for r in rows:
            try:
                loaded.append(self.__loaded_tasks[int(r['id'])])
                set_rows.remove(r)
            except KeyError as e:
                pass
        return self.__get_task_objects((loaded, list(set_rows)))

    def __get_task_objects(self, extract):
        u'''Take an extract: ([Task], [SQLRow]) ; and transforms the rows
        into fully fledged objects with a little functional voodoo :).

        Return value: [Task]'''
        tasks = extract[0]
        rows = extract[1]
        parent_ids = []
        id_to_row = {}  # id:row
        for r in rows:
            id_to_row[int(r["id"])] = r

            # Gather all the parents' ids.
            if (r['parent'] != None and
                r['parent'] not in self.__loaded_tasks.iterkeys()):
                parent_ids.append(int(r['parent']))

        ids_to_fetch = []
        for i in parent_ids:
            # If we didn't already grabbed it
            if i not in id_to_row.iterkeys():
                ids_to_fetch.append(i)

        parent_extract = self.__extract_rows('tasks', self.__loaded_tasks,
                                             ids_to_fetch, None, None)
        # We discard the tasks already loaded.
        for r in parent_extract[1]:     # Don't care about redundancy, overwrite if needed
            id_to_row[int(r["id"])] = r

        # Sorry Basile, I needed this one.
        def distance(row):
            u'''The distance represents here the number of rows which have to
            be processed before this one.'''
            # If there's no parent or it is already loaded, then it can be
            # loaded right away
            if row['parent'] == None or (int(row['parent']) in
                                         self.__loaded_tasks.iterkeys()):
                return 0
            return distance(id_to_row[int(row['parent'])])+1

        rows = [r for r in id_to_row.itervalues()]
        rows = sorted(rows, key=distance)
        for r in rows:
            t = Task(self)
            t.id = int(r["id"])
            if r['parent'] == None:
                t.parent = None
            else:   # If everything go as planned, it is already loaded
                t.parent = self.__loaded_tasks[int(r['parent'])]

            t.content = r["content"]
            t.due_date = r["due_date"]
            t.priority = r["priority"]
            t.list = self.get_list(r["list"])
            t.tags = set(self.get_tags(task=t))
            t.completed = r["completed"]
            t.last_modified = r["last_modified"]
            t.created = r["created"]

            t.changed = False
            self.__loaded_tasks[t.id] = t
            t.notes = self.get_notes(t)

            # Return only the tasks explicitly requested, not the collateral
            if t.id not in ids_to_fetch:
                tasks.append(t)
        return tasks

    def get_notes(self, task=None, ids=None, contents=None, regexp=None):
        if task == None:
            extra_criteria = None
            extract = self.__extract_rows('notes', self.__loaded_notes,
                                             ids, contents, regexp)
        else:
            extra_criteria = ('task=?', (task.id,))
        extract = self.__extract_rows('notes', self.__loaded_notes,
                                      ids, contents, regexp, extra_criteria)

        loaded = extract[0][:]
        for n in extract[1]:
            note = Note(self)
            note.id = int(n['id'])
            note.task = self.get_task(int(n['task']))
            note.content = n['content']
            note.hash = n['hash_id']
            note.created = n['created']
            note.changed = False
            self.__loaded_notes[note.id] = note
            loaded.append(note)

        return loaded
    def _add_task(self, task):
        u'''Adds a task to the DB.
        '''
        task.check_values(self)
        if task.parent == None:
            parent_id = None
        else:
            parent_id = task.parent.id

        with self.__sql:
            self.__sql.execute(u'''insert into tasks
                               values(null, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                               ''',
                               (task.content, parent_id, task.priority,
                                task.due_date, task.list.id, task.completed,
                                self.get_time(), task.created, "nohash"))
            self.__sql.commit()
            if parent_id == None:
                parent_id = "null"
            task.id = self.__sql.execute('select id from tasks where created=? and content=?', (task.created, task.content)).fetchone()[0]
            for i in task.tags:
                self.__sql.execute('insert into tagging values(?,?)', (i.id, task.id))
            self.__sql.commit()

    def _edit_task(self, task):
        if task.id == None:
            return
        task.check_values()
        if task.parent == None:
            parent_id = None
        else:
            parent_id = task.parent.id

        # Process add_tags and remove_tags
        tags = set(self.get_tags(task=task))
        tags_to_add = task.tags - tags
        tags_to_rm = tags - task.tags

        with self.__sql:
            self.__sql.execute(u'''update tasks set
                               content=?, parent=?, priority=?, due_date=?,
                               list=?, completed=?, last_modified=?
                               where id=?''', (task.content, parent_id,
                                               task.priority, task.due_date,
                                               task.list.id, task.completed,
                                               self.get_time(), task.id))
            for t in tags_to_rm:
                self.__sql.execute(u'''delete from tagging
                                  where tag=? and task=?''', (t.id,task.id))
            for t in tags_to_add:
                self.__sql.execute(u'''insert into tagging
                                  values(?, ?)''', (t.id, task.id))
            self.__sql.commit()
        task.changed = False

    def remove_tasks(self, ids, recursive=True):
        u"""Remove tasks by their ids
        params:
            - ids (array<int>)
            - recursive (bool)
        If recursive is True, it will also destroy all the children tasks.
        """
        # The cascade property ensure the deletion of the children
        # If we are to change this policy punctually, we can change the
        # children's parents here before the removal
        if not recursive:
            with self.__sql:
                self.__sql.execute('''replace into tasks
                                   (id, content,parent, priority, due_date,
                                    list, completed, last_modified,
                                    created, hash_id
                                   )
                                   select t1.id, t1.content, t2.parent,
                                   t1.priority, t1.due_date, t1.list,
                                   t1.completed, t1.last_modified,
                                   t1.created, t1.hash_id
                                   from tasks as t1, tasks as t2
                                   where t1.parent=t2.id
                                   and t2.id in ({seq})
                                   '''.format(seq=', '.join(['?']*len(ids))),
                                   ids)
        self.__simple_removal(ids, 'tasks')

    def remove_notes(self, ids):
        u"""Remove notes by their ids.
        params:
            - ids (array<int>)
        """
        self.__simple_removal(ids, 'notes')

    def remove_lists(self, ids, list_recursion=True, task_recursion=False):
        u"""Remove lists by their ids. Be careful, when deleting a list, every
        task that it contains will be deleted too.
        param:
            - ids (array<string>)
            - list_recursion (bool)
            - task_recursion (bool)
        If list_recursion is True, it will also destroy all the tasks belonging
        to the lists. If task_recursion is True, those tasks' children are
        destroyed alongside.
        """
        # Same remark as for the task : cascade effect.
        if list_recursion and not task_recursion:
            with self.__sql:
                task_ids = [int(i[0]) for i in
                            self.__sql.execute('''
                                               select id from tasks
                                               where list in ({seq})
                                               '''.format(seq=', '
                                                          .join(['?'] *
                                                                len(ids))
                                                         ),
                                               ids).fetchall()]
            self.remove_tasks(task_ids, False)
        elif not list_recursion:
            with self.__sql:
                self.__sql.execute('''update tasks set list=null
                                   where list in ({seq})
                                   '''.format(seq=', '.join(['?'] * len(ids))),
                                   ids)
        self.__simple_removal(ids, 'lists')

    def remove_tags(self, ids):
        u"""Remove tags by their ids. Also update tasks which have these tags.
        param:
            - ids (array<string>)
        """
        # The cascade actions remove the appropriate relations in tagging
        self.__simple_removal(ids, 'tags')

    def __simple_removal(self, ids, table):
        with self.__sql:
            self.__sql.execute(u'delete from {table} where id in ({seq})'
                               .format(table=table, seq=', '.join(['?'] *
                                                                  len(ids))
                                      ), ids)
            self.__sql.commit()

    def __get_groups(self, cls, nocls, loaded_objects, ids, names, regexp):
        if ids != None and None in ids and None not in loaded_objects:
            loaded_objects[None] = nocls(self)
        extract = self.__extract_rows(cls._table_name, loaded_objects,
                                      ids, names, regexp)
        return self.__get_group_objects(cls, loaded_objects, extract)
    
    def __get_group_objects(self, cls, loaded_objects, extract):
        groups = extract[0]
        rows = extract[1]
        for r in rows:
            g = cls(self)
            g.id = int(r["id"])
            g.content = r["content"]
            g.priority = r["priority"]
            g.last_modified = r["last_modified"]
            g.created = r["created"]
            g.changed = False
            loaded_objects[g.id] = g
            groups.append(g)
        return groups

    def get_tags(self, ids=None, names=None, regexp=None, task=None):
        loaded = []
        if task != None:
            ids = []    # Otherwise, the second step would fetch'em all
            with self.__sql:
                rows = self.__sql.execute(u'''select tags.* from tags, tagging
                                          where tagging.task=? and
                                          tagging.tag=tags.id''', (task.id,)
                                         ).fetchall()
            if rows == []:
                # We have to load NoTag here, since there wouldn't be any request
                # for the None id
                self.__loaded_tags[None]= NoTag(self)
            set_rows = set(rows)
            for r in rows:
                try:
                    loaded.append(self.__loaded_tags[int(r['id'])])
                    set_rows.remove(r)
                except KeyError:
                    pass
            loaded = self.__get_group_objects(Tag, self.__loaded_tags,
                                              (loaded, list(set_rows)))
        return loaded + self.__get_groups(Tag, NoTag, self.__loaded_tags,
                                           ids, names, regexp)

    def get_loaded_lists(self):
        return [l for l in self.__loaded_lists.itervalues()]

    def get_loaded_tags(self):
        return [l for l in self.__loaded_tags.itervalues()]

    def get_lists(self, ids=None, names=None, regexp=None):
        return self.__get_groups(List, NoList, self.__loaded_lists, ids, names, regexp)

    def get_list(self, value, value_is_id=True):
        if value == None:
            try:
                return self.__loaded_lists[None]
            except KeyError as e:
                self.__loaded_lists[None] = NoList(self)
                return self.__loaded_lists[None]
        if value_is_id:
            try:
                return self.get_lists([int(value)])[0]
            except IndexError:
                raise WrongId
        try:
            return self.get_lists(names=[value])[0]
        except IndexError:
            raise WrongName 

    def get_tag(self, value, value_is_id=True):
        if value == None:
            try:
                return self.__loaded_tags[None]
            except KeyError as e:
                self.__loaded_tags[None] = NoTag(self)
                return self.__loaded_tags[None]
        if value_is_id:
            try:
                return self.get_tags([int(value)])[0]
            except IndexError:
                raise WrongId
        try:
            return self.get_tags(names=[value])[0]
        except IndexError:
            raise WrongName 

    def get_time(self):
        u"""Return the current timestamp"""
        return time.time()

    def get_lock(self, force = False):
        u"""Acquire the lock for the database. If the lock is already active
        with someone other than us, raise an exception"""
        locked_pid = 0
        try:
            with open(self.config["yatdir"] + "/lock") as lock_file:
                locked_pid = pickle.load(lock_file)
        except IOError:
            locked_pid = self.__pid

        if locked_pid == self.__pid or force:
            with open(self.config["yatdir"] + "/lock", 'w') as lock_file:
                pickle.dump(self.__pid, lock_file)
        else:
            raise ExistingLock, locked_pid
        
        return self.__pid

    def release_lock(self):
        u"""Release the lock for the database then return true. If the lock was
        set up by another program, then do nothing and return false."""
        delete = False
        try:
            with open(self.config["yatdir"] + "/lock") as lock_file:
                if pickle.load(lock_file) == self.__pid:
                    delete = True
        except IOError:
            pass

        if delete:
            os.remove(self.config["yatdir"] + "/lock")

        return delete

    def _add_note(self, note):
        note.check_values()
        with self.__sql:
            self.__sql.execute(u'''insert into notes
                               values(null, ?, ?, ?, ?)''',
                               (note.content, note.task.id, note.created,
                                note.hash))
            note_row = self.__sql.execute(u'''select * from notes
                                          where task=? and
                                          created=? and content=?''',
                                          (note.task.id, note.created, note.content)
                                         ).fetchone()
        note.id = note_row["id"]

    def _edit_note(self, note):
        note.check_values()
        if note.id == None:
            return
        with self.__sql:
            self.__sql.execute(u'''update notes
                               set content=?, parent=? where id=?''',
                               (note.content, note.parent, note.id))
        note.changed = False

    def _add_group(self, table_name, group):
        group.check_values()
        self._add_tag_or_list(table_name, group.content,
                              group.priority, group.created)
        group_row = self.__sql.execute(u'''select * from %s
                                       where content=?
                                       ''' % table_name, (group.content,)
                                      ).fetchone()
        group.id = group_row['id']
        group.priority = group_row['priority']
        group.created = group_row['created']
        group.last_modified = group_row['last_modified']
        group.changed = False

    def _edit_group(self, table_name, group):
        group.check_values()
        if group.id == None:
            return
        with self.__sql:
            self.__sql.execute(u'update %s set content=?, priority=?, last_modified=? where id=?' % table_name,
                    (group.content, group.priority, self.get_time(), group.id))
        group.changed = False

    def _add_tag_or_list(self, table, name, priority, created = 0):
        u"""Add an element "name" to the "table" if it doesn't exist. It is
        meant to be used with table="lists" or table="tags" """
        if created <= 0:
            creation_time = created
        else:
            creation_time = self.get_time()
        with self.__sql:
            c = self.__sql.execute('select count(*) as nb from %s where content=?' %
                    table, (name,))
            if c.fetchone()[0] == 0:
                self.__sql.execute('insert into %s values(null, ?, ?, ?, ?, ?)' % table,
                    (name, priority, self.get_time(), creation_time, "nohash"))
                self.__sql.commit()

    @staticmethod
    def __compute_hash(obj):
        u'''Basile, knock yourself out !'''
        return "nohash"

if __name__ == "__main__":
    raise NotImplementedError
