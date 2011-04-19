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
        self.parent = Task.children_id[self.parent_id][0]
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
        self.tags = lib.get_tags([int(i) for i in sql_line['tags'].split(",")])
        self.completed = sql_line["completed"]
        self.last_modified = sql_line["last_modified"]
        self.created = sql_line["created"]

    def __str__(self):
        retour = "Task "
        retour += str(self.id)
        return retour

    def parents_on_list(self, list):
        u"""Returns True if at least one parent of self is listed in list, False otherwise."""
        return self.parent != None and (list == self.parent.list or self.parent.parents_on_list(list))

    def tag_present_in_parents(self, tag):
        u"""Returns True if at least one parent of self is tagged with tag, False otherwise."""
        return self.parent != None and (tag in parent.tags or self.parent.tag_present_in_parents(tag))

    def get_list_parents(self):
        u"""Returns a list of all the parents of self, beginning with the root ancestor."""
        if self.parent == None:
            return []
        return self.parent.get_list_parents().append(self.parent)

    def stack_up_parents(tree):
        u"""Static function. Given a tree with a task as root, stacks up the ancestors of the said task
        on top of is, in a straight line to the task. The added nodes are tagged as contextual."""
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
        print self
        print Task.children_id
        print [Task.children_id[i][0] for i in Task.children_id[self.id][1]]
        return [Task.children_id[i][0] for i in Task.children_id[self.id][1]]

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
        List.list_id[self.id] = self

    def __str__(self):
        retour = "List " + str(self.id)
        return retour

    def child_policy(self, task):
        u"""This policy excludes all the tasks that aren't on the list, except for those who have a child
        on the list, and the immediate children of a member. The nodes with a task out of the list are 
        tagged contextual."""
        tree = Tree(task, self.child_policy)
        print tree
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
        return [c[0] for c in Task.children_id.itervalues() if (c[0] != None and c[0].list == self)]

class Tag:
    tag_id = {}

    def __init__(self, sql_line):
        u"""Constructs a Tag from an sql entry."""
        self.id = sql_line["id"]
        self.content = sql_line["name"]
        self.priority = sql_line["priority"]
        self.last_modified = sql_line["last_modified"]
        self.created = sql_line["created"]
        Tag.tag_id[self.id] = self

    def direct_children(self):
        return [c for h,c in Task.children_id if (c != None and self in c.tags and not c.tag_present_in_parents(self))]

    def child_policy(self, task):
        u"""The tags are considered inherited from the parent, so no discrimination whatsoever :)"""
        return Tree(task, self.child_policy)

    def child_callback(self, tree):
        if self in tree.parent.tags and tree.parent.parent != None and not tree.parent.tag_present_in_parents():
            return Task.stack_up_parents(tree)
        return tree

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
                print tree
                if policy == None:
                    tree = parent.child_callback(tree)  # In case additional actions are needed to finish the work. 
                self.children.append(tree)

    def __str__(self):
        retour = "Tree :"
        retour += str(self.parent) + ", " + str([str(c) for c in self.children])
        return retour

