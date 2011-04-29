#-*- coding:utf-8 -*-

u"""
Yat Library

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

# Current version of yat
# Is of the form "last_tag-development_state"
VERSION = u"0.1b-dev"

class Yat:

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

    def __init__(self, config_file_path = None):
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
        self.__sql = sqlite3.connect(self.config["yatdir"] + "/yat.db")

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
            # Create tables
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
                        ?)""", (VERSION,))
                self.__sql.commit()

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

        # Dictionary matching an task id to a tuple of the matching Task and a list of
        # its children's ids.
        Task.children_id = { 0:(None, [])}
        self.__tag_id = {}
        self.__list_id = {}
        pass

    def _get_tasks(self, ids=None, names=None, regexp=None):
        return [t.parent for t in self.get_tasks(ids, regexp, False, False,
                                                 '', [], False, True,
                                                 False)
               if ((ids != None and t.parent.id in ids) or
                   (regexp != None and self.regexp(regexp,
                                                  t.parent.content)) or
                   (regexp == None and ids == None))]

    def get_tasks(self, ids=None, regexp=None, group=True, order=True, group_by="list",
                  order_by=["reverse:priority", "due_date"], fetch_children=True,
                  fetch_parents=True, regroup_family=True):
        u"""Method to get the tasks from the database, group them by list or
        tag, and order them according to the parameters. This function return an
        array of trees if group is False, and an array of tuple (group,
        list_of_trees) if group is True, where group is a list or a tag, and
        list_of_trees, well... a list of trees...

        The grouping is done only if "group" is set to True
        
        The ordering is done only if "order" and "group" are set to True. 
        
        If no ids and no regexp are provided, assume regexp="*"

        The group_by arg can only contain "list" or "tag"

        The order_by contains an array with column names. The tasks will be
        ordered by the first element, then the second... To reverse the sorting
        order, use something like "reverse:column_name" (see default parameters
        for an example)

        If select_children is set to True, the function will fetch the children
        and parents of the tasks matching the pattern specified by the other
        parameters.

        params:
            - ids (array<int>)
            - regexp (string)
            - group (boolean)
            - order (boolean)
            - group-by ("list" or "tag")
            - order-by (array<string>)
            - select_children (boolean)
        """

        tasks = []
        # Extract tasks from the database
        if ids != None:
            with self.__sql:
                for i in ids:
                    tasks.extend(self.__sql.execute(
                        u"select * from tasks where id=?", (i,)).fetchall())
        if regexp != None:
            with self.__sql:
                tasks.extend(self.__sql.execute(
                    u"select * from tasks where content regexp ?", 
                    (regexp,)).fetchall())
        if ids == None and regexp == None:
            with self.__sql:
                tasks.extend(self.__sql.execute(
                    u"select * from tasks").fetchall())

        # Pulls in the children of the selected tasks
        if fetch_children:
            to_examine = tasks

            while to_examine != []:
                new_children = []
                for i in to_examine:
                    tmp = self.__sql.execute(u'''select * from tasks
                                                      where parent=?''', (i['id'],)).fetchall()
                    new_children.extend([c for c in tmp if c not in tasks])
                to_examine = new_children
                tasks.extend(new_children)
        if fetch_parents:
            to_fetch = (set([t['parent'] for t in tasks]) -
                        set([t['id'] for t in tasks]) -
                        set([None]))
            tasks.extend([
                self.__sql.execute(u'''select * from tasks where id=?''',
                                   (i,)).fetchone() for i in to_fetch])

        tasks = [Task(self, t) for t in tasks]

        # Grouping tasks
        tree_parameters = {'no_family': not regroup_family}
        if group:
            grouped_tasks = []
            tree_construction = None
            if group_by == "list":
                nogroup = Tree(NoList(), None, tree_parameters)
                grouped_tasks = [Tree(l, None, tree_parameters)
                                 for l in List.list_id.itervalues()
                                 if l.id != None]

            elif group_by == "tag":
                grouped_tasks = [Tree(t, None, tree_parameters) for t in Tag.tag_id.itervalues()]
                nogroup = Tree(NoTag(), None, tree_parameters)

        else:
            # Takes an id and returns the list associated
            grouped_tasks = [Tree(t[0], None, tree_parameters)
                             for t in Task.children_id.itervalues()
                             if t[0] != None]

        # Ordering tasks (you can't order tasks if they aren't grouped
        if order and group:
            # Ordering groups
            ordered_tasks = self.__quicksort(list = grouped_tasks, column =
                "priority", group = True)

            # And then make a reinsertion at the end of the sorted list.
            if nogroup.children != []:
                ordered_tasks.append(nogroup)

            # Ordering tasks according to the first criterion
            for t in ordered_tasks:
                group = t.parent
                tasks = t.children
                tmp = order_by[0].split(":")
                if tmp[0] == "reverse":
                    comparison = ">"
                    attribute = tmp[1]
                else:
                    comparison = "<"
                    attribute = tmp[0]

                # Reset the internal dictionary
                self.__dict = {}

                self.__quicksort(list = tasks, column = attribute, order =
                        comparison, depth = True)

                # Ordering tasks according to the rest of the criterion
                tasks = self.__secondary_sort(tasks, order_by[1:], (comparison, attribute))

        else:
            ordered_tasks = grouped_tasks

        return ordered_tasks

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
        tags = set(self.get_tags_from_task(task.id))
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

    def remove_tasks(self, ids):
        u"""Remove tasks by their ids
        params:
            - ids (array<int>)
        """
        with self.__sql:
            for i in ids:
                children = self.__sql.execute(u'select id from tasks where parent=?', (i,)).fetchall()
                children = [tmp[0] for tmp in children]
                self.remove_tasks(children)
                self.__sql.execute(u'delete from tasks where id=?', (i,))
            self.__sql.commit()
        pass

    def get_tags(self, tags, type_id = True, can_create = False):
        u"""Extract the tags from the database. The parameter tags have to be an
        array with tag names or tag ids. 
        
        If tag names are provided, type_id have to be set to False. 
        
        If type_id is set to False and can_create is set to True, then if a tag
        doesn't exist, it will be created.
        """
        res = []
        for t in tags:
            with self.__sql:
                tag_row = None
                if type_id:
                    if int(t) in Tag.tag_id:
                        res.append(Tag.tag_id[int(t)])
                    else:
                        tag_row = self.__sql.execute(u'select * from tags where id=?',
                                (t,)).fetchone()
                else:
                    tag_row = self.__sql.execute(u'select * from tags where content=?', 
                            (t,)).fetchone()
                    if can_create and tag_row == None:
                        self._add_tag_or_list("tags", t, 0)
                        tag_row = self.__sql.execute(u'select * from tags where content=?', 
                            (t,)).fetchone()
                    elif tag_row != None and int(tag_row["id"]) in Tag.tag_id:
                        res.append(Tag.tag_id[int(tag_row["id"])])
                        tag_row = None
                res.append(Tag(self, tag_row))
        return res

    def get_tags_regex(self, regex):
        u"""Extract from the database all the tags that match regex, where regex
        is an expression with * and ? jokers"""
        with self.__sql:
            raw_tags = self.__sql.execute(u'select * from tags where content regexp ?',
                    (regex,)).fetchall()
            return [Tag(self, t) for t in raw_tags]

    def get_tags_from_task(self, task_id):
        u"""Extract from the DB all the tags associated with the id provided"""
        with self.__sql:
            tag_id = [l[0] for l in self.__sql.execute('select tag from tagging where task=?', (task_id,))]
            return_list = []
            for i in tag_id:
                try:
                    return_list.append(Tag.tag_id[i])
                except:
                    return_list.append(Tag(self, self.__sql.execute('select * from tags where id=?', (i,)).fetchone()))
            return return_list

    def _edit_group(self, table_name, group):
        group.check_values()
        if group.id == None:
            return
        with self.__sql:
            self.__sql.execute(u'update %s set content=?, priority=?, last_modified=? where id=?' % table_name,
                    (group.content, group.priority, self.get_time(), group.id))
        group.changed = False

    def remove_tags(self, ids):
        u"""Remove tags by their ids. Also update tasks which have these tags.
        param:
            - ids (array<string>)
        """
        with self.__sql:
            # Update tasks
            for t in ids:
                # Remove tags
                self.__sql.execute(u'delete from tags where id=?', (t,))
            self.__sql.commit()
        pass

    def __get_group_rows(self, table, ids=None, regexp=None):
        if ids == None and regexp == None:
            sql_rows = set(self.__sql.execute(u'select * from lists'))
        else:
            sql_rows = set()
            if ids != None:
                for i in ids:
                    sql_rows.add(self.__sql.execute(u'''
                                                    select * from %s
                                                    where id=?''' % table,
                                                    (i,)).fetchone())
            if regexp != None:
                sql_rows |= set(self.__sql.execute(u'''
                                                   select * from %s 
                                                   where content regexp ?
                                                   ''' % table,
                                                   (regexp)).fetchall())
        return sql_rows

    #Only temporary until complete redesign
    def _get_lists(self, ids = None, regexp = None):
        return [List(self, r) for r in self.__get_group_rows('lists',
                                                             ids, regexp)]

    # Same as _get_lists
    def _get_tags_v2(self, ids = None, regexp = None):
        return [Tag(self, r) for r in self.__get_group_rows('tags',
                                                            ids, regexp)]

    def get_list(self, list, type_id = True, can_create = False):
        u"""Extract a list from the database. The parameter list has to be a
        list name or a list id. 
        
        If a list name is provided, then type_id has to be set to False.

        If type_id is set to False and can_create is set to True, then if the
        list name provided doesn't exist, it will be created.
        """
        res = None
        if (list == None and type_id) or (list == '' and not type_id):
            if None in List.list_id:
                return List.list_id[None]
            return NoList()
        with self.__sql:
            if type_id:
                if int(list) in List.list_id:
                    return List.list_id[int(list)]
                res = self.__sql.execute(u'select * from lists where id=?',
                        (list,)).fetchone()
            else:
                res = self.__sql.execute(u'select * from lists where content=?',
                        (list,)).fetchone()
                if res == None and can_create:
                    self._add_tag_or_list("lists", list, 0)
                    res = self.__sql.execute(u'select * from lists where content=?',
                            (list,)).fetchone()
                elif res != None and int(res["id"]) in List.list_id:
                    return List.list_id[int(res["id"])]
            return List(self, res)

    def get_lists_regex(self, regex):
        u"""Extract from the database the lists that match regex, where regex is
        an expression with * and ? jokers."""
        with self.__sql:
            raw_lists = self.__sql.execute('select * from lists where content regexp ?',
                    (regex,)).fetchall()
            lists = []
            for l in raw_lists:
                if l["id"] in List.list_id:
                    lists.append(List.list_id[l["id"]])
                else:
                    lists.append(List(self, l))
            return lists

    def remove_lists(self, ids):
        u"""Remove lists by their ids. Be careful, when deleting a list, every
        task that it contains will be deleted too.
        param:
            - ids (array<string>)
        """
        with self.__sql:
            for i in ids:
                self.__sql.execute(u'delete from lists where id=?', (i,))
            self.__sql.commit()
        pass

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

    # Also very temporary
    def _add_group(self, table_name, group):
        group.check_values()
        self._add_tag_or_list(table_name, group.content,
                              group.priority, group.created)
        group_row = self.__sql.execute(u'''select * from %s
                                       where priority = ? and content=?
                                       ''' % table_name, (group.priority,
                                                          group.content)
                                      ).fetchone()
        group.id = group_row['id']
        group.created = group_row['created']
        group.last_modified = group_row['last_modified']
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

    def __get_id(self, table, name):
        u"""Get the id of the element "name" in "table". It's meant to be used
        with table = "lists" or "tags" """
        with self.__sql:
            res = self.__sql.execute('select id from %s where content=?' % table, (name,))
            return str(res.fetchone()[0])

    def __quicksort(self, list, column, left=None, right=None, order=">=",
            group=False, depth = False):
        u"""Implementation of the quicksort of database rows. 
        
        The parameter "list" contains database rows or tuples of database rows.
        If a tuple is provided, the ordering will be made on the first element,
        and group has to be set to True.

        The parameters "left" and "right" contain the limits for the sorting
        algorithm.

        The parameter "order" contains the comparison that will be made between
        the elements. It has to be in [">", "<", ">=", "<="].
        """
        if depth and not group:
            for e in list:
                if e != []:
                    self.__quicksort(e.children, column, left, right, order, group, True)

        # If left and right are not provided, assuming sorting on all the list
        if left == None:
            left = 0
        if right == None:
            right = len(list) - 1

        if right > left:
            pivot = left + (right - left)/2
            pivot = self.__partition(list, column, left, right, pivot, order,
                    group)
            self.__quicksort(list, column, left, pivot - 1, order, group)
            self.__quicksort(list, column, pivot + 1, right, order, group)
        return list

    def __partition(self, list, column, left, right, pivot, order, group):
        u"""Partioning of a list according to a "pivot" and a sorting "order",
        within the "left" and "right" limits. This function is a part of the
        quicksort algorithm.
        """
        pivotValue = list[pivot]
        list[pivot], list[right] = list[right], list[pivot]
        storeIndex = left
        for i in range(left, right):
            swap = False

            if group:
                if self.__compare(column, order, list[i].parent,
                        pivotValue.parent ,depth = False):
                    swap = True
            else:
                if self.__compare(column, order, list[i],
                        pivotValue):
                    swap = True

            if swap:
                list[i], list[storeIndex] = list[storeIndex], list[i]
                storeIndex += 1
        list[storeIndex], list[right] = list[right], list[storeIndex]
        return storeIndex

    def __tree_extrem_value(self, tree, column, comparison):
        u"""Returns the most significant value for the given comparison,
        column and task tree. For instance, if the column is priority and the
        comparison is ">=" or ">", it will return the higher priority amongst
        amongst all the leafs of the tree.
        """
        # We assume the dictionary is up-to-date
        if tree.parent in self.__dict:
            return self.__dict[tree.parent]
        if comparison not in self.__operators:
            raise AttributeError, 'order argument should be in {0}'.format(self.__operators.keys())
        return_value = tree.parent.__dict__[column]
        if tree.children != []:
            subvalues = map(lambda x: self.__tree_extrem_value(x, column, comparison), tree.children)
            extrem_subvalue = reduce((lambda x,y: x if self.__operators[comparison](x, y) else y), subvalues)
            return_value = return_value if self.__operators[comparison](return_value, extrem_subvalue) else extrem_subvalue
        return return_value
            


    def __compare(self, column, comparison, val1, val2, depth = True):
        u"""Compare two values of "column" with "comparison". The attribute
        "column" has to be provided to handle correctly the comparison of the
        "due_date" column. This method is a part of the quicksort algorithm.
        
        If depth isn't True, it will only compare the first member of the val[12]
        tuples. This is mostly designed for non-tree values such as the (group, [tasks])
        type tuples. If depth IS True, it will consider the most significant value
        of each tree in the comparison.
        """
        if comparison not in self.__operators:
            raise AttributeError, 'order argument should be in {0}'.format(self.__operators.keys())
        if not depth:
            return self.__operators[comparison](val1.__dict__[column], val2.__dict__[column])

        return self.__operators[comparison](self.__tree_extrem_value(val1, column, comparison),
                                            self.__tree_extrem_value(val2, column, comparison))

    def __secondary_sort(self, list, remaining, primary_tuple):

        u""" Takes a list of trees, the remaining sort arguments, and the main
        sort argument (the main sorting task is supposed to be already done via
        __quicksort & co), and sorts the trees until it runs out of sorting arguments
        """
        for t in list:
            t = (t.parent, self.__secondary_sort(t.children, remaining, primary_tuple))
        ordered_by = [primary_tuple]
        for c in remaining:
            l = 0
            r = 0

            # Extract attribute and sorting order
            tmp = c.split(":")
            if tmp[0] == "reverse":
                comp = ">"
                attr = tmp[1]
            else:
                comp = "<"
                attr = tmp[0]

            # Sort tasks
            for i in range(len(list) - 1):
                compare = True
                for o in ordered_by:
                    if (self.__tree_extrem_value(list[i], o[1], o[0]) !=
                        self.__tree_extrem_value(list[i+1], o[1], o[0])):
                        compare = False
                if compare:
                    r = i + 1
                else:
                    self.__quicksort(list, left = l, right = r,
                            column = attr, order = comp)
                    l = i + 1
            self.__quicksort(list, left = l, right = r, column =
                    attr, order = comp)
            ordered_by.append((attr,comp))
        return list


class WrongTagId(Exception):
    u"""Exception raised when trying to extract a tag that doesn't exist"""
    pass
    
class WrongListId(Exception):
    u"""Exception raised when trying to extract a list that doesn't exist"""
    pass

class WrongTaskId(Exception):
    u"""Exception raised when trying to extract a task that doesn't exist"""
    pass

class ExistingLock(Exception):
    u"""Exception raised when a lock is already set."""
    pass

class WrongConfigFile(Exception):
    u"""Exception raised when the path passed to Yat() doesn't point to a valid
    file."""
    pass

class IncoherentDBState(Exception):
    u"""Exception raised when something doesn't add up and we don't know why, so we blame the DB"""
    pass

if __name__ == "__main__":
    raise NotImplementedError
