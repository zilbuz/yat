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

    def parents_on_list(self, list):
        return self.parent != None and (list == self.parent.list or self.parent.parents_on_list(list))

    def tag_present_in_parents(self, tag):
        return self.parent != None and (tag in parent.tags or self.parent.tag_present_in_parents(tag))

    def get_list_parents(self):
        if self.parent == None:
            return []
        return self.parent.get_list_parents().append(self.parent)

    def stack_up_parents(tree):
        parents = tree.parent.get_list_parents()
        def policy(t):
            if t == tree.parent:
                return tree
            if t in parents:
                l_tree = Tree(t, policy)
                l_tree.context = True
                return l_tree
            return None
        return Tree(parents[0], policy)
    stack_up_parents = staticmethod(stack_up_parents)

    def direct_children(self):
        return children_id[self.id]

    def child_policy(self, task):
        return Tree(task, self.child_policy)

    def child_callback(self, tree):
        return tree

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

    def child_policy(self, task):
        tree = Tree(task, self.child_policy)
        if task.list == self:
            return tree
        if task.parent.list != self and tree.children == []:
            return None
        tree.context = True
        return tree

    def child_callback(self, tree):
        u"""Appends the context tasks on top of the tree in the twisted cases :)"""
        if tree.parent.list == list and (not tree.parent.parents_on_list(self)
                                         and tree.parent.parent != None):
            return Task.stack_up_parents(tree)
        return tree

    def direct_children(self):
        return [c for h,c in Task.children_id if (c != None and c.list == self and not c.parents_on_list(self))]

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
    def __init__(self, parent = None, policy = None):  # The policy is a function passed along to the make_children_tree method in order to help select the children
        self.parent = parent

        # The context flag might be used in display
        self.context = False

        # The parent is the best placed to determine who are her children ;-)
        direct_children = parent.direct_children()

        # If the Power That Be (the caller) didn't specify a policy, once again ask the parent,
        # she supposedly knows what's best for her children, right ?
        if policy == None:
            child_policy = parent.child_policy
        else:
            child_policy = policy

        # Apply the policy to the children and filter the result to suppress the invalid ones
        self.children = []
        for c in direct_children:
            tree = child_policy(c)
            if tree != None:
                if policy == None:
                    tree = parent.child_callback(tree)  # In case additional actions are needed to finish the work. 
                self.children.append(tree)

