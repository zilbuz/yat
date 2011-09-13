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

import locale
import os
import pickle
import re
import sqlite3
import sys
import time

from yat.models import Task, Note, List, Tag, NoList, NoTag
from yat.exceptions import WrongId, WrongName, WrongConfigFile, ExistingLock

# Current version of yat
# Is of the form "last_tag-development_state"
VERSION = u"0.2b-dev"
# Current version for the database.
DB_VERSION = u"0.2"

#pylint: disable=R0902,R0904,R0913
class Yat(object):
    u'''Driver to the yat database.'''

    @staticmethod
    def regexp(expr, item):
        u'''Compare an expression to a string and returns True if there
        is a match.
        '''
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
        self.config_file = config_file_path
        self.initialize(config_file_path, db_path)

    def initialize(self, config_file_path = None, db_path = None):
        u"""Constructor:
            * load the configuration file
            * open a connection with the database
            * initialize some variables
        """
        # Default encoding
        self.enc = locale.getpreferredencoding()

        # Default input : stdin
        self.input = sys.stdin

        # Default output : stdout
        self.output = sys.stdout

        # Config file
        if os.name == 'nt':
            default_config_file_path = \
                os.path.join(os.environ.get('appdata'), 'yat.rc')
            default_yatdir = \
                os.path.join(os.environ.get('appdata'), 'yat')
        else:
            default_config_file_path = \
                os.path.join(os.environ.get('HOME'), '.yatrc')
            default_yatdir = \
                os.path.join(os.environ.get('HOME'), '.yat')
        if config_file_path != None:
            self.config_file = config_file_path
        if self.config_file == None:
            self.config_file = default_config_file_path
        else:
            if not os.path.isfile(self.config_file):
                raise WrongConfigFile, self.config_file

        # Loading configuration
        self.config = {}
        try:
            with open(self.config_file, "r") as config_file:
                for line in config_file:
                    if not (re.match(r'^\s*#.*$', line) or
                            re.match(r'^\s*$', line)):
                        line = re.sub(r'\s*=\s*', "=", line, 1)
                        line = re.sub(r'\n$', r'', line)
                        opt = line.split('=', 1)
                        self.config[opt[0]] = opt[1]
            config_file.close()
        except IOError:
            # No .yatrc
            pass

        # For each option, loading default if it isn't defined
        self.config["yatdir"] = self.config.get("yatdir", default_yatdir)
        self.config["default_priority"] = \
            self.config.get("default_priority", "1")

        # Default timestamp: infinite
        self.config["default_date"] = float('+inf')

        # Create yat directory
        if self.config["yatdir"][0] == "~":
            self.config["yatdir"] = (os.environ.get("HOME") +
                                     self.config["yatdir"][1:])
        if not os.path.isdir(self.config["yatdir"]):
            os.makedirs(self.config["yatdir"], mode=0700)

        # Connect to sqlite db
        try:
            self.free_db()
        except AttributeError:
            pass
        if db_path == None:
            self._db_path = self.config['yatdir'] + os.path.sep +'yat.db'
        else:
            self._db_path = db_path
        self.__sql = sqlite3.connect(self._db_path)

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
        self.config["re.date"] = u"(?P<x1>\d?\d)/(?P<x2>\d\d)/(?P<year>\d{4})\
            (:(?P<hour>\d?\d)(:(?P<minute>\d\d))?(?P<apm>am|pm)?)?"
        self.config["re.tag_name"] = u".*"
        self.config["re.tags_list"] = u"{0}?(,{0}?)*".format(
                self.config["re.tag_name"])
        self.config["re.list_name"] = u".*"

        # Dictionaries used to avoid duplicating objects
        self._loaded_tasks = {}
        self._loaded_lists = {}
        self._loaded_tags = {}
        self._loaded_notes = {}

    def free_db(self):
        '''Unload the DB. It is especially useful for the tests.'''
        self.__sql.close()

    def load_db(self):
        u'''Open the database. Automatically executed on init.'''
        self.__sql = sqlite3.connect(self._db_path)
        self.__sql.row_factory = sqlite3.Row

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
                    last_modified real,
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

        # If the value isn't an ID, we assume it is a full name.
        try:
            return self.get_tasks(names=[value])[0]
        except IndexError:
            raise WrongName

    def get_loaded_tasks(self):
        u'''Returns a list of all the tasks that were already pulled from
        the DB. Complexity : O(n) = n'''
        return [t for t in self._loaded_tasks.itervalues()]

    def _extract_rows(self, table_name, loaded_objects,
                       ids, names, regexp, extra_criteria = None):
        u'''Extract the data out of the DB. It also checks whether it was
        already loaded, in which case it replaces it by the object.
        Arguments:
            table_name (str): 
                The name of the table from where the data will be extracted

            loaded_objects (dict):
                dict to check wether a row was already loaded or not.

            ids ([int]):
                A list of ids to load.

            names ([str]):
                A list of *exact* names to load.

            regexp (str):
                A regexp to compare with the content of the data.

            extra_criteria (str, [values]):
                The string is a SQL predicat such as 'parent=? and id=?' and
                "values" is a list containing the values to insert
                in the string.

        If ids, names and regexp are all None, the whole table will be fetched.

        It returns a tuple of list. The first list contains all the objects
        already loaded, the second the raw data to process.

        Complexity : Good question !'''

        loaded = []
        # Fetch'em all !
        if ids == None and names == None and regexp == None:
            if extra_criteria == None:
                rows = self.__sql.execute(u'select * from {0}'
                                          .format(table_name)).fetchall()
            else:
                rows = self.__sql.execute(u'select * from {0} where {1}'
                                          .format(table_name,
                                                  extra_criteria[0]),
                                          extra_criteria[1]).fetchall()
            copy = rows[:]
            for row in copy:
                try:
                    loaded.append(loaded_objects[int(row['id'])])
                except KeyError:
                    continue
                rows.remove(row)
        else:
            # To optimize the query, we have to create a new composed one
            # related to what is provided in argument. If there was no ID
            # provided, there's no need to test against the ids !
            # condition_string is what follows the 'where' statement.
            # condition_arguments is what will replace all the ?
            # in condition_string
            condition_string = ''
            condition_arguments = []

            if ids != None:
                # First, remove from the list what has already been loaded.
                ids_to_load = []
                for i in ids:
                    if i in loaded_objects:
                        loaded.append(loaded_objects[i])
                    else:
                        ids_to_load.append(i)

                # If everything has already been loaded, there's no need to
                # test against the ids.
                if ids_to_load != []:
                    condition_string = \
                        'id in ({0})'.format(', '.join(['?']*len(ids_to_load)))
                    condition_arguments.extend(ids_to_load)

            if names != None and names != []:
                # If there's already a condition
                if condition_string != '':
                    condition_string += ' or '
                condition_string += 'content in ({0})'
                condition_string = \
                    condition_string.format(', '.join(['?'] * len(names)))
                condition_arguments.extend(names)

            if regexp != None:
                if condition_string != '':
                    condition_string += ' or '
                condition_string += 'content regexp ?'
                condition_arguments.append(regexp)

            if extra_criteria != None and condition_string != '':
                extra_criteria = ('and ' + extra_criteria[0],
                                  list(extra_criteria[1]))
                condition_string = '(' + condition_string + ')'
            elif extra_criteria == None:
                extra_criteria = ('', [])
            # Don't forget the extra arguments !
            sql_arguments = condition_arguments + extra_criteria[1]

            # Prepare the request in advance
            request = (u'select * from {0} where {1} {2}'
                       .format(table_name, condition_string,
                               extra_criteria[0]))


            # Fetch the rows only if there's some conditions
            rows = []
            if extra_criteria[0] != '' or condition_string != '':
                try:
                    rows = self.__sql.execute(request, sql_arguments).fetchall()
                except sqlite3.InterfaceError as sql_exception:
                    raise sql_exception

                # Theoretically, it might be faster to remove an object from a
                # set if it is implemented as an unbalanced B-Tree : log(n)
                # complexity to reach the node, and 1 to delete the object
                set_rows = set(rows)
                for row in rows:
                    try:    # Try to fetch the loaded object.
                        loaded.append(loaded_objects[int(row['id'])])
                        set_rows.remove(row)
                        # If it is there, the row is useless
                    except KeyError:
                        pass
                rows = list(set_rows)
        return (loaded, rows)

    def get_tasks(self, ids=None, names=None, regexp=None, groups=None):
        u'''Returns a list of tasks matching the input data. If ids, names,
        regexp and group all equal None, every task will be fetched.
            ids: [int], ids to be loaded/fetched
            names: [str], the exact names of the tasks
            regexp: str, a valid regular expression to compare against the 
                    content attribute.
            groups: [Group], grab all the tasks associated with these
                    particular tags/lists. Note that it is possible to mix
                    them.
        '''
        loaded = []
        rows = []
        list_criterium = None
        lists = []
        tags = []

        if groups != None:
            if ids == None:
                ids = []    # Otherwise, it would pull everything
            for grp in groups:
                if issubclass(type(grp), List):
                    lists.append(grp.id)
                    continue
                if issubclass(type(grp), Tag):
                    tags.append(grp.id)
                    continue

            # For the lists, use the extra_criteria parameter in order to
            # benefit from the complex query optimizations.
            if lists != []:
                list_criterium = (
                    'list in ({0})'.format(', '.join(['?']*len(lists))),
                    lists)

            # For the tags, we have to do a separate query because of the
            # many-to-many relationship
            if tags != []:
                rows.extend(self.__sql.execute(
                    u''' select tasks.* from tasks, tagging
                    where tagging.tag in ({0}) and tasks.id=tagging.task'''
                    .format(', '.join(['?']*len(tags))), tags).fetchall())

                set_rows = set(rows)
                for row in rows:
                    try:
                        loaded.append(self._loaded_tasks[int(row['id'])])
                        set_rows.remove(row)
                    except KeyError:
                        pass
                loaded = self._get_task_objects((loaded, list(set_rows)))

        return loaded + self._get_task_objects(
            self._extract_rows("tasks", self._loaded_tasks,
                                ids, names, regexp, list_criterium))

    def get_children(self, task):
        u'''Returns all the direct subtasks of a given task.'''

        # Simply use the extra_criteria parameter to fetch the direct children
        return self._get_task_objects(
            self._extract_rows("tasks", self._loaded_tasks, None, None, None,
                                ('parent=?', [task.id])))

    def _get_task_objects(self, extract):
        u'''Take an extract and transforms the rows into fully fledged objects
        with a little functional voodoo :).

        extract ([Task], [SQLRow]):
            Usually, what is returned by a call to self._extract_rows()

        Return value: [Task]'''
        tasks = extract[0]
        rows = extract[1]
        id_to_row = {}  # id:row
        id_to_return = set()
        for row in rows:
            id_to_row[int(row["id"])] = row
            id_to_return.add(int(row['id']))

        while len(rows) > 0:
            parent_ids = []
            for row in rows:
                # Gather all the parents' ids.
                if (row['parent'] != None and
                    row['parent'] not in self._loaded_tasks.iterkeys()):
                    parent_ids.append(int(row['parent']))

            ids_to_fetch = []
            for i in parent_ids:
                # If we didn't already grabbed it
                if i not in id_to_row.iterkeys():
                    ids_to_fetch.append(i)

            parent_extract = self._extract_rows('tasks', self._loaded_tasks,
                                                 ids_to_fetch, None, None)
            # We discard the tasks already loaded.
            for row in parent_extract[1]:     # Don't care about redundancy,
                id_to_row[int(row["id"])] = row # overwrite if needed
            rows = parent_extract[1]

        # Sorry Basile, I needed this one.
        def distance(row):
            u'''The distance represents here the number of rows which have to
            be processed before this one.
            Careful, recursive !
            '''
            # If there's no parent or it is already loaded, then it can be
            # loaded right away
            if row['parent'] == None or (int(row['parent']) in
                                         self._loaded_tasks.iterkeys()):
                return 0
            return distance(id_to_row[int(row['parent'])])+1

        # Build a complete list of all rows to be transformed into tasks,
        # and then sort it out in order to meet every dependency.
        rows = [row for row in id_to_row.itervalues()]
        rows = sorted(rows, key=distance)

        # The actual transformation from rows to Tasks
        for row in rows:
            task = Task(self)
            task.id = int(row["id"])
            if row['parent'] == None:
                task.parent = None
            else:   # Thanks to the careful sorting, it has to be already loaded
                task.parent = self._loaded_tasks[int(row['parent'])]

            task.content = row["content"]

            task.due_date = (float(row["due_date"]) if row['due_date'] != None
                          else float('inf'))

            task.priority = int(row["priority"])
            task.list = self.get_list(row["list"])
            task.tags = set(self.get_tags(task=task))
            task.completed = row["completed"]
            task.last_modified = float(row["last_modified"])
            task.created = float(row["created"])

            # As usual, when pulling it from the DB we have to switch back
            # the changed flag to False.
            task.changed = False
            self._loaded_tasks[task.id] = task
            task.notes = sorted(self.get_notes(task), key = lambda x: x.id)

            # Return only the tasks explicitly requested, not the collateral
            if task.id in id_to_return:
                tasks.append(task)
        return tasks

    def get_notes(self, task=None, ids=None, contents=None, regexp=None):
        u'''Grab notes from the database and build the objects if needed.
        The arguments are pretty mutch the same as for the other get_* methods.
        As always, if ids, contents and regexp are all equal None, the method
        considers all notes, modulo the specified task (if specified)

        task (Task):
            If you just want to examin the notes of a given task.

        ids ([int]):
            A list of ids corresponding to notes to fetch.
            If the specified task is None, the ids are considered absolute. In
            any other case, they are local to the task.

        contents ([str]):
            A list of exact contents to match. In that particular case, it
            seems highly improbable that someone would reproduce the whole
            content of a note, but it has to be there for API consistency.

        regexp (str):
            A regular expression to compare against the contents.

        Return value: [Note]
        '''
        if task == None:
            extra_criteria = None
        else:
            extra_criteria = ('task=?', (task.id,))

        extract = self._extract_rows('notes', self._loaded_notes,
                                     self.__get_absolute_note_ids(task, ids),
                                     contents, regexp, extra_criteria)

        loaded = extract[0][:]
        for row in extract[1]:
            note = Note(self)
            note.id = int(row['id'])
            note.task = self.get_task(int(row['task']))
            note.content = row['content']
            note.hash = row['hash_id']
            note.created = row['created']

            # As usual, when pulling it from the DB we have to switch back
            # the changed flag to False.
            note.changed = False

            self._loaded_notes[note.id] = note
            loaded.append(note)

        return loaded

    @staticmethod
    def __get_absolute_note_ids(task, ids):
        '''When given a task and a list of local ids, return the absolute ids
        of the notes pointed by the local ones.'''
        if task == None or ids == None:
            return ids
        try:
            return [task.notes[i-1] for i in ids]
        except IndexError:
            raise WrongId

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
            task.id = \
                self.__sql.execute(u'''select id from tasks
                                    where created=? and content=?
                                    ''',
                                    (task.created, task.content)).fetchone()[0]
            for i in task.tags:
                self.__sql.execute('insert into tagging values(?,?)',
                                   (i.id, task.id))
            self.__sql.commit()

    def _edit_task(self, task):
        u'''Update the DB backup of a Task object.'''
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
            for tag in tags_to_rm:
                self.__sql.execute(u'''delete from tagging
                                  where tag=? and task=?''', (tag.id, task.id))
            for tag in tags_to_add:
                self.__sql.execute(u'''insert into tagging
                                  values(?, ?)''', (tag.id, task.id))
            self.__sql.commit()
        task.changed = False

    def remove_tasks(self, ids, recursive=False):
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
            query = '''
            replace into tasks (id, content, parent, priority, due_date,
                list, completed, last_modified, created, hash_id)
            select t1.id, t1.content, t2.parent, t1.priority, t1.due_date,
                t1.list, t1.completed, t1.last_modified, t1.created, t1.hash_id
            from tasks as t1, tasks as t2
            where t1.parent=t2.id and t2.id in ({0})
            '''.format(', '.join(['?']*len(ids)))

            with self.__sql:
                self.__sql.execute(query, ids)

        self._simple_removal(ids, 'tasks')

    def remove_notes(self, ids):
        u"""Remove notes by their ids.
        params:
            - ids (array<int>)
        """
        self._simple_removal(ids, 'notes')

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
        self._simple_removal(ids, 'lists')

    def remove_tags(self, ids):
        u"""Remove tags by their ids. Also update tasks which have these tags.
        param:
            - ids (array<string>)
        """
        # The cascade actions remove the appropriate relations in tagging
        self._simple_removal(ids, 'tags')

    def _simple_removal(self, ids, table):
        u'''Remove a list of items from a table. The items are selected by ids.
        '''
        with self.__sql:
            self.__sql.execute(u'delete from {table} where id in ({seq})'
                               .format(table=table, seq=', '.join(['?'] *
                                                                  len(ids))
                                      ), ids)
            self.__sql.commit()

    def _get_groups(self, cls, nocls, loaded_objects, ids, names, regexp):
        u'''Load groups from the DB.
        cls:            The final class of the objects.
        nocls:          Its negative (List => NoList)
        loaded_objects: A dictionary matching every loaded object to its ID.
        ids:            The IDs to load.
        names:          The exact names of the objects to load.
        regexp:         The regexp to compare against the content.
        '''
        if ids != None and None in ids and None not in loaded_objects:
            loaded_objects[None] = nocls(self)
        extract = self._extract_rows(cls.table_name, loaded_objects,
                                      ids, names, regexp)
        return self._get_group_objects(cls, loaded_objects, extract)
    
    def _get_group_objects(self, cls, loaded_objects, extract):
        u'''Transform rows into instances of cls.'''
        groups = extract[0]
        rows = extract[1]
        for row in rows:
            grp = cls(self)
            grp.id = int(row["id"])
            grp.content = row["content"]
            grp.priority = row["priority"]
            grp.last_modified = row["last_modified"]
            grp.created = row["created"]
            grp.changed = False
            loaded_objects[grp.id] = grp
            groups.append(grp)
        return groups

    def get_tags(self, ids=None, names=None, regexp=None, task=None):
        '''Standard getter for the tags. The first arguments are standard.
        Task allows to load the tags associated with the given task. It is
        used in the loading process of a task.
        '''
        loaded = []
        if task != None:
            ids = []    # Otherwise, the second step would fetch'em all
            query = u'''select tags.* from tags, tagging
            where tagging.task=? and tagging.tag=tags.id'''

            with self.__sql:
                rows = self.__sql.execute(query, [task.id]).fetchall()

            if rows == []:
                # We have to load NoTag here, since there wouldn't be any
                # request for the None id
                self._loaded_tags[None] = NoTag(self)
            set_rows = set(rows)
            for row in rows:
                try:
                    loaded.append(self._loaded_tags[int(row['id'])])
                    set_rows.remove(row)
                except KeyError:
                    pass
            loaded = self._get_group_objects(Tag, self._loaded_tags,
                                              (loaded, list(set_rows)))
        return loaded + self._get_groups(Tag, NoTag, self._loaded_tags,
                                           ids, names, regexp)

    def get_loaded_lists(self):
        u'''Self explanatory name.'''
        return [l for l in self._loaded_lists.itervalues()]

    def get_loaded_tags(self):
        u'''Self explanatory name.'''
        return [l for l in self._loaded_tags.itervalues()]

    def get_lists(self, ids=None, names=None, regexp=None):
        u'''Interface to get List objects from the DB. The arguments
        are the standard ones.
        '''
        return self._get_groups(List, NoList, self._loaded_lists, ids,
                                names, regexp)

    def get_list(self, value, value_is_id=True):
        u'''Get a single list'''
        if value == None:
            try:
                return self._loaded_lists[None]
            except KeyError:
                self._loaded_lists[None] = NoList(self)
                return self._loaded_lists[None]
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
        u'''Get a single tag.'''
        if value == None:
            try:
                return self._loaded_tags[None]
            except KeyError:
                self._loaded_tags[None] = NoTag(self)
                return self._loaded_tags[None]
        if value_is_id:
            try:
                return self.get_tags([int(value)])[0]
            except IndexError:
                raise WrongId
        try:
            return self.get_tags(names=[value])[0]
        except IndexError:
            raise WrongName 

    @staticmethod
    def get_time():
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
        u'''Add a new note to the DB from a Note object.'''
        note.check_values()
        with self.__sql:
            self.__sql.execute(u'''insert into notes
                               values(null, ?, ?, ?, ?, ?)''',
                               (note.content, note.task.id, self.get_time(),
                                note.created, note.hash))
            note_row = self.__sql.execute(u'''select * from notes
                                          where task=? and
                                          created=? and content=?''',
                                          (note.task.id, note.created,
                                           note.content)
                                         ).fetchone()
        note.id = int(note_row["id"])
        note.last_modified = int(note_row['last_modified'])
        note.changed = False

    def _edit_note(self, note):
        u'''Update the DB backup of a Note instance.'''
        note.check_values()
        if note.id == None:
            return
        now = self.get_time()
        query = u'''update notes set content=?, parent=?, last_modified=?
            where id=?'''
        arguments = (note.content, note.parent, now, note.id)
        with self.__sql:
            self.__sql.execute(query, arguments)
            note.last_modified = now
        note.changed = False

    def _add_group(self, group):
        u'''Save an instance of a child class of Group into the DB.'''
        group.check_values()
        self._add_tag_or_list(group.table_name, group.content,
                              group.priority, group.created)
        group_row = self.__sql.execute(u'''select * from %s
                                       where content=?
                                       ''' % group.table_name, (group.content,)
                                      ).fetchone()
        group.id = int(group_row['id'])
        group.priority = group_row['priority']
        group.created = group_row['created']
        group.last_modified = group_row['last_modified']
        group.changed = False

    def _edit_group(self, group):
        u'''Update the DB backup of an instance of a child class of Group.'''
        group.check_values()
        if group.id == None:
            return
        now = self.get_time()
        query = u'update %s set content=?, priority=?, \
                last_modified=? where id=?' % group.table_name
        with self.__sql:
            self.__sql.execute(query, (group.content, group.priority,
                                       now, group.id))
            group.last_modified = now
        group.changed = False

    def _add_tag_or_list(self, table, name, priority, created = 0):
        u"""Add an element "name" to the "table" if it doesn't exist. It is
        meant to be used with table="lists" or table="tags" """
        if created <= 0:
            creation_time = created
        else:
            creation_time = self.get_time()
        with self.__sql:
            count = self.__sql.execute('select count(*) as nb from %s \
                                    where content=?' % table, (name,))
            if count.fetchone()[0] == 0:
                self.__sql.execute('insert into %s \
                                    values(null, ?, ?, ?, ?, ?)' % table, 
                                    (name, priority, self.get_time(),
                                     creation_time, "nohash"))
                self.__sql.commit()

    @staticmethod
    def __compute_hash(obj):
        u'''Basile, knock yourself out !'''
        return "nohash"

#pylint: enable=R0902, R0904

if __name__ == "__main__":
    raise NotImplementedError
