#-*- coding:utf-8 -*-

u"""
The Task, List and Tag classes

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

from lib import *

import lib

class Task:
    children_id = {}

    def __init__(self, sql_line, lib):
        u"""Constructs a Task from an sql entry and an instance of Yat
        """
        self.id = sql_line["id"]
        self.parent_id = sql_line["parent"]

        if self.parent_id not in Task.children_id:
            Task.children_id[self.parent_id] = (None, [])
        self.parent = Task.children_id[self.parent_id]
        if self.id not in Task.children_id[self.parent_id][1]:
            Task.children_id[self.parent_id][1].append(self.id)
        if self.id not in Task.children_id:
            Task.children_id[self.id] = (self, [])
        else:
            Task.children_id[self.id] = (self, Task.children_id[self.id][1])
            for t in Task.children_id[self.id][1]:
                t.parent = self

        self.content = sql_line["task"]
        self.due_date = sql_line["due_date"]
        self.priority = sql_line["priority"]
        self.list = lib.get_list(sql_line["list"])
        self.tags = lib.get_tags([int(i) for i in sql_line[tags].split(",")])
        self.completed = sql_line["completed"]
        self.last_modified = sql_line["last_modified"]
        self.created = sql_line["created"]

class List:
    list_id = {}

    def __init__(self, sql_line):
        u"""Constructs a List from an sql entry."""
        self.id = sql_line["id"]
        self.content = sql_line["name"]
        self.priority = sql_line["priority"]
        self.last_modified = sql_line["last_modified"]
        self.created = sql_line["created"]
        list_id[self.id] = self

    def construction_tree(self, tasks = None) :
        if tasks == Non:
            return Tree(self, [])
        return_value = Tree(self, [])
        for t in tasks :
            task_tree = Tree(t, [])
class Tag:
    tag_id = {}

    def __init__(self, sql_line):
        u"""Constructs a Tag from an sql entry."""
        self.id = sql_line["id"]
        self.content = sql_line["name"]
        self.priority = sql_line["priority"]
        self.last_modified = sql_line["last_modified"]
        self.created = sql_line["created"]
        tag_id[self.id] = self

class Tree:
    def __init__(self, parent = None, children = []):
        self.parent = parent
        self.children = children

    def 
