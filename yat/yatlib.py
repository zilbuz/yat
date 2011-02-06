#!/usr/bin/env python
#-*- coding:utf-8 -*-

u"""
Yat Library

Minimalistic library to manipulate the data of yat: the configuration file and
the sqlite database.


           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
                   Version 2, December 2004 

 Copyright (C) 2010 
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
import re
import sqlite3
import sys
import time

class YatLib:

    def __init__(self):
        u"""Constructor:
            * load the configuration file
            * open a connection with the database
            * initialise some variables
        """
        # Default encoding
        self.enc = locale.getpreferredencoding()

        # Default output : stdout
        self.out = sys.stdout

        # Loading configuration
        self.config = {}
        try:
            with open(os.environ.get("HOME") + "/.yatrc", "r") as config_file:
                for line in config_file:
                    if not (re.match(r'^\s*#.*$', line) or re.match(r'^\s*$', line)):
                        line = re.sub(r'\s*=\s*', "=", line, 1)
                        line = re.sub(r'\n$', r'', line)
                        opt = line.split('=', 1)
                        config[opt[0]] = opt[1]
            config_file.close()
        except IOError:
            # No .yatrc
            pass

        # For each option, loading default if it isn't defined
        self.config["yatdir"] = self.config.get("yatdir", "~/.yat")
        self.config["default_list"] = self.config.get("default_list", "nolist")
        self.config["default_tag"] = self.config.get("default_tag", "notag")
        self.config["default_priority"] = self.config.get("default_priority", "1")

        # Create yat directory
        if self.config["yatdir"][0] == "~":
            self.config["yatdir"] = os.environ.get("HOME") + self.config["yatdir"][1:]
        if not os.path.isdir(self.config["yatdir"]):
            os.makedirs(self.config["yatdir"], mode=0700)

        # Connect to sqlite db
        self.sql = sqlite3.connect(self.config["yatdir"] + "/yat.db")

        # Use Row as row_factory to add access by column name and other things
        self.sql.row_factory = sqlite3.Row

        # Add a function to support the REGEXP() operator
        def regexp(expr, item):
            r = re.findall(expr,item)
            return len(r) == 1 and r[0] == item
        self.sql.create_function("regexp", 2, regexp)
    
        # Verify the existence of the database and create it if it doesn't exist
        # (very basic)
        try:
            with self.sql:
                self.sql.execute("select * from tags")
        except sqlite3.OperationalError:
            # Create tables
            with self.sql:
                self.sql.execute("""
                    create table tasks (
                        id integer primary key,
                        task text,
                        priority int,
                        due_date text,
                        tags text,
                        list text,
                        completed integer,
                        last_modified real
                    )""")
                self.sql.execute("""
                    create table tags (
                        id integer primary key,
                        name text,
                        priority integer,
                        last_modified real
                        )""")
                self.sql.execute("""
                    create table lists (
                        id integer primary key,
                        name text,
                        priority integer,
                        last_modified real
                        )""")
                self.sql.execute("""insert into tags values (null, "notag", -1,
                        ?)""", (time.time(),))
                self.sql.execute("""insert into lists values (null, "nolist",
                        -1, ?)""", (time.time(),))
                self.sql.commit()
        pass

    def get_tasks(self, ids=None, regexp=None, order=True, group_by="list",
    order_by=["priority", "due_date"]):
        u"""Method to get the tasks from the database and ordering them
        according to the parameters. 
        
        The ordering is done only if the "order" parameter is set to True. 
        
        If no ids and no regexp are provided, assume regexp=".*"

        The group-by arg can only contain "list" or "tag"

        The order-by contains an array with column names. The tasks will be
        ordered by the first element, then the second...

        params:
            - ids (array<int>)
            - regexp (string)
            - order (boolean)
            - group-by ("list" or "tag")
            - order-by (array<string>)
        """
        # TODO: a fonction to get the tasks from their ids or a regexp, and
        # order them depending on a parameter. Return a table, or maybe a map 
        # {listname -> tasks_table} or {tagname -> tasks_table}, also depending
        # on a parameter

        tasks = []
        # Extract tasks from the database
        if ids != None:
            with self.sql:
                for i in ids:
                    tasks.extend(self.sql.execute(
                        u"select * from tasks where id=?", (i,)).fetchall())
        if regexp != None:
            with self.sql:
                tasks.extend(self.sql.execute(
                    u"select * from tasks where task regexp ?", 
                    (regexp,)).fetchall())
        if ids == None and regexp == None:
            with self.sql:
                tasks.extend(self.sql.execute(
                    u"select * from tasks").fetchall())


        # Grouping tasks
        grouped_tasks = []
        if group_by == "list":
            lists = self.sql.execute(u"select * from lists").fetchall()
            for l in lists:
                index = len(grouped_tasks)
                grouped_tasks.append((l,[]))
                for t in tasks[:]:
                    if t["list"] == str(l["id"]):
                        grouped_tasks[index][1].append(t)
                        tasks.remove(t) # A task is in one list only
        elif group_by == "tag":
            lists = self.sql.execute(u"select * from tags").fetchall()
            for tag in tags:
                index = len(grouped_tasks)
                grouped_tasks.append((tag,[]))
                for t in tasks:
                    task_tags = t["tags"].split(",")
                    if str(tag["id"]) in task_tags:
                        grouped_tasks[index][1].append(t)
                        # A task can be in different tags

        # Ordering them
        if order:
            #TODO: tasks ordering
            ordered_tasks = grouped_tasks
        else:
            ordered_tasks = grouped_tasks

        return ordered_tasks

    def add_task(self, text, priority=None, due_date=None, tags=None, list=None, completed=False):
        u"""Add a task to the database with the informations provided. Use
        default informations if None is provided
        params:
            - text (string)
            - priority (int)
            - due_date (string)
            - tags (array<string>)
            - list (string)
            - completed (bool)
        """

        # Set the priority
        if priority == None:
            priority = self.config["default_priority"]
        elif priority > 3:
            priority = 3

        # Set the due date
        if due_date == None:
            due_date = u""

        # Get the ids of the tags
        if tags == None or tags == []:
            tags.append(self.config["default_tag"])
        tags_copy = []
        for t in tags:
            self.__add_tag_or_list("tags", t, 0)
            tags_copy.append(self.__get_id("tags", t))
        tags = ",".join(tags_copy)

        # Get the id of the list
        if list == None or list == u"":
            list = self.config["default_list"]
        self.__add_tag_or_list("lists", list, 0)
        list = self.__get_id("lists", list)

        # Set completed
        if completed:
            completed = 1
        else:
            completed = 0
        
        # Add the task to the bdd
        with self.sql:
            self.sql.execute('insert into tasks values(null, ?, ?, ?, ?, ?, ?, ?)',
                    (text, priority, due_date, tags, list, completed,
                        self.get_time()))
            self.sql.commit()
        pass

    def edit_task():
        #TODO : edit task
        pass

    def remove_tasks(self, ids):
        u"""Remove tasks by their ids
        params:
            - ids (array<int>)
        """
        with self.sql:
            for i in ids:
                self.sql.execute(u'delete from tasks where id=?', (i,))
            self.sql.commit()
        pass

    def add_tag(self, name, priority=0):
        u"""Add a tag to the database with a certain priority, and create it if
        it doesn't exist
        params:
            - name (string)
            - priority=0 (int)
        """
        self.__add_tag_or_list("tags", name, priority)
        pass

    def edit_tag():
        pass

    def remove_tags(self, ids):
        u"""Remove tags by their ids. Also update tasks which have these tags.
        param:
            - ids (array<string>)
        """
        with self.sql:
            # Remove tags
            for i in ids:
                if i != "1": # it's not possible to remove the "notag" tag
                    self.sql.execute(u'delete from tags where id=?', (i,))

            # Update tasks
            for t in self.sql.execute(u'select * from tasks'):
                tags = t["tags"].split(",")
                tags_copy = tags[:]
                for i in range(len(tags_copy)):
                    if tags_copy[i] in ids:
                        tags.pop(i)
                if len(tags) == 0:
                    tags.append("1")
                self.sql.execute(u'update tasks set tags=? where id=?',
                        (",".join(tags), t["id"]))
            self.sql.commit()
        pass

    def add_list(self, name, priority=0):
        u"""Add a list to the database with a certain priority and create it if 
        it doesn't exist.
        params:
            - name (string)
            - priority=0 (int)
        """
        self.__add_tag_or_list("lists", name, priority)
        pass

    def edit_list():
        pass
    
    def remove_lists(self, ids):
        u"""Remove lists by their ids. Be careful, when deleting a list, every
        task that it contains will be deleted too.
        param:
            - ids (array<string>)
        """
        with self.sql:
            for i in ids:
                if i != "1": # It's not possible to remove the "nolist" list
                    # Delete list
                    self.sql.execute(u'delete from lists where id=?', (i,))
                    # Delete tasks
                    self.sql.execute(u'delete from tasks where list=?', (i,))
            self.sql.commit()
        pass

    def get_time(self):
        return time.time()

    def __add_tag_or_list(self, table, name, priority):
        u"""Add an element "name" to the "table" if it doesn't exist. It is
        meant to be used with table="lists" or table="tags" """
        with self.sql:
            c = self.sql.execute('select count(*) as nb from %s where name=?' %
                    table, (name,))
            if c.fetchone()[0] == 0:
                self.sql.execute('insert into %s values(null, ?, ?, ?)' % table,
                    (name, priority, self.get_time()))
                self.sql.commit()

    def __get_id(self, table, name):
        u"""Get the id of the element "name" in "table". It's meant to be used
        with table = "lists" or "tags" """
        with self.sql:
            res = self.sql.execute('select id from %s where name=?' % table, (name,))
            return str(res.fetchone()[0])
    

if __name__ == "__main__":
    raise NotImplementedError
