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

class Task(object):
    children_id = {}
    class_lib

    @classmethod
    def get_task(cls, id):
        return cls.get_tasks([id])[0]

    @classmethod
    def get_tasks(cls, ids):
        tasks = []
        ids_to_fetch = []
        for i in ids:
            try:
                t = cls.children_id[i][0]
                if t == None:
                    raise Exception('internal')
                tasks.append(t)
            except:
                ids_to_fetch.append(i)
        tasks.extend([tree.parent for tree in
                     cls.class_lib.get_tasks(ids, group=False, order=False,
                                             fetch_children=False,
                                             fetch_parents=True,
                                             regroup_family=False)])
        return tasks

    def __setattr__(self, attr, value):
        super(Task, self).__setattr__('changed', True)
        super(Task, self).__setattr__(attr, value)

    def __init__(self, sql_line=None, lib=None, no_family=False):
        u"""Constructs a Task from an sql entry and an instance of Yat
        """
        self.lib = lib
        if Task.class_lib == None:
            Task.class_lib = self.lib
        elif self.lib == None:
            self.lib = Task.class_lib
        if sql_line == None:
            self.id = None
            self.parent=None
            self.content=''
            self.due_date=None
            self.priority=None
            self.list = NoList()
            self.tags = set()
            self.completed = 0
            self.last_modified = 0
            self.created = 0
            self.changed = False
            return
        self.id = sql_line["id"]
        parent_id = sql_line["parent"]

        if parent_id not in Task.children_id:
            Task.children_id[parent_id] = (None, [])
        self.parent = Task.children_id[parent_id][0]
        if self.id not in Task.children_id[parent_id][1]:
            Task.children_id[parent_id][1].append(self.id)
        if self.id not in Task.children_id:
            Task.children_id[self.id] = (self, [])
        else:
            Task.children_id[self.id] = (self, Task.children_id[self.id][1])
            for t in Task.children_id[self.id][1]:
                t_changed = Task.children_id[t][0].changed
                Task.children_id[t][0].parent = self
                Task.children_id[t][0].changed = t_changed

        self.content = sql_line["content"]
        self.due_date = sql_line["due_date"]
        self.priority = sql_line["priority"]
        self.list = lib.get_list(sql_line["list"])
        self.tags = set(lib.get_tags_from_task(self.id))
        self.completed = sql_line["completed"]
        self.last_modified = sql_line["last_modified"]
        self.created = sql_line["created"]

        self.changed = False

    def check_values(self, lib = None):
        u'''Checks the values of the object, and correct them
        if needed by using the default values provided by lib.
        '''
        if lib == None:
            lib = self.lib
        if self.priority == None:
            if self.parent != None:
                self.priority = self.parent.priority
            else:
                self.priority = lib.config["default_priority"]
        elif self.priority > 3:
            self.priority = 3

        for t in self.tags:
            t.check_values(lib)

        self.list.check_values(lib)

        if self.due_date == None:
            if self.parent == None:
                self.due_date = lib.config["default_date"]
            else:
                self.due_date = self.parent.due_date

        if self.created <= 0:
            self.created = lib.get_time()

        if self.completed == True or self.completed == 1:
            self.completed = 1
        else:
            self.completed = 0

    def save(self, lib = None):
        if lib == None:
            lib = self.lib
        self.list.save(lib)
        for t in self.tags:
            t.save(lib)
        if self.parent != None:
            self.parent.save(lib)

        if self.id == None:
            save_function = lib._add_task
        else:
            save_function = lib._edit_task
        save_function(self)

    def __str__(self):
        retour = "Task "
        retour += str(self.id)
        return retour

    def parents_in_group(self, group):
        u"""Returns True if at least one parent of self is in the group, False otherwise."""
        return self.parent != None and (group.related_with(self.parent) or
                                        self.parent.parents_in_group(group))

    def get_list_parents(self):
        u"""Returns a list of all the parents of self, beginning with the root ancestor."""
        if self.parent == None:
            return []
        list = self.parent.get_list_parents()
        list.append(self.parent)
        return list

    def stack_up_parents(tree):
        u"""Static function. Given a tree with a task as root, stacks up the ancestors of the said task
        on top of is, in a straight line to the task. The added nodes are tagged as contextual."""
        parents = tree.parent.get_list_parents()
        def policy(t, p):
            if t == tree.parent:
                return tree
            if t in parents:
                l_tree = Tree(t, policy, p)
                l_tree.context = True
                return l_tree
            return None
        tree_return = Tree(parents[0], policy)
        tree_return.context = True
        return tree_return
    stack_up_parents = staticmethod(stack_up_parents)

    def direct_children(self, search_parameters):
        try:
            if search_parameters['no_family']:
                return []
        except:
            pass
        return [Task.children_id[i][0] for i in Task.children_id[self.id][1]]

    def child_policy(self, task, params):
        return Tree(task, self.child_policy, params)

    def child_callback(self, tree):
        return tree

class Group(object):
    def __setattr__(self, attr, value):
        super(Group, self).__setattr__('changed', True)
        super(Group, self).__setattr__(attr, value)

    def __init__(self, lib, sql_line):
        u"""Constructs a group from an sql row"""
        self.lib = lib
        if sql_line == None:
            self.id = None
            self.content = ''
            self.priority = None
            self.last_modified = 0
            self.created = 0
            self.changed = False
            return
        self.id = int(sql_line["id"])
        self.content = sql_line["content"]
        self.priority = sql_line["priority"]
        self.last_modified = sql_line["last_modified"]
        self.created = sql_line["created"]
        self.changed = False

    def direct_children(self, search_parameters):
        try:
            no_family = search_parameters['no_family']
        except:
            no_family = False
        return [c[0] for c in Task.children_id.itervalues()
                if (c[0] != None and self.related_with(c[0]) and
                    (not c[0].parents_in_group(self) or no_family))]

    def child_callback(self, tree):
        u"""Appends the context tasks on top of the tree in the twisted cases :)"""
        if self.related_with(tree.parent) and (not tree.parent.parents_in_group(self)
                                         and tree.parent.parent != None):
            return Task.stack_up_parents(tree)
        return tree

    def check_values(self, lib = None):
        if lib == None:
            lib = self.lib

        if self.priority == None:
            self.priority = lib.config["default_priority"]

        if self.created <= 0:
            self.created = self.lib.get_time()

    def save(self, lib = None):
        if lib == None:
            lib = self.lib
        self.check_values(lib)
        if self.id == None:
            lib._add_tag_or_list(self._table_name, self.content, self.priority)
        elif self.changed:
            lib._edit_group(self._table_name, self)


class List(Group):
    list_id = {}
    _table_name = 'lists'

    def __init__(self, lib, sql_line = None):
        u"""Constructs a List from an sql entry."""
        super(List, self).__init__(lib, sql_line)
        if self.id != None:
            List.list_id[self.id] = self

    def __str__(self):
        retour = "List " + str(self.id)
        return retour

    def related_with(self, task):
        return task.list == self

    def child_policy(self, task, params):
        u"""This policy excludes all the tasks that aren't on the list, except for those who have a child
        on the list, and the immediate children of a member. The nodes with a task out of the list are 
        tagged contextual."""
        tree = Tree(task, self.child_policy, params)
        if task.list == self:
            return tree
        if task.parent.list != self and tree.children == []:
            return None
        tree.context = True
        return tree

class Tag(Group):
    tag_id = {}
    _table_name = 'tags'

    def __init__(self, lib, sql_line = None):
        u"""Constructs a Tag from an sql entry."""
        super(Tag, self).__init__(lib, sql_line)
        if self.id != None:
            Tag.tag_id[self.id] = self

    def child_policy(self, task, params):
        u"""The tags are considered inherited from the parent, so no discrimination whatsoever :)"""
        return Tree(task, self.child_policy, params)

    def related_with(self, task):
        return self in task.tags

class NoGroup(object):
    def __init__(self):
        self.id = None

    def save(self, lib = None):
        pass

    def check_values(self, lib = None):
        pass

class NoList(NoGroup, List):
    # List provides unique algorithms, but here we override its polymorphism abilities
    __mro__ = (NoGroup, Group, object, List)
    def __new__(cls):
        try:
            return List.list_id[None]
        except:
            return super(NoList, cls).__new__(cls)

    def __init__(self):
        super(NoList, self).__init__()
        List.list_id[None] = self

class NoTag(NoGroup, Tag):
    # Same as for NoList's MRO.
    __mro__ = (NoGroup, Group, Tag, object)

    def __init__(self):
        super(NoTag, self).__init__()

    def related_with(self, task):
        return task.tags == []

class Tree:
    def __init__(self, parent = None, policy = None, search_parameters = None):  # The policy is a function passed along to the make_children_tree method in order to help select the children
        self.parent = parent

        # The context flag might be used in display
        self.context = False

        # The parent is the best placed to determine who are her children ;-)
        direct_children = parent.direct_children(search_parameters)

        # If the Power That Be (the caller) didn't specify a policy, once again ask the parent,
        # she supposedly knows what's best for her children, right ?
        if policy == None:
            child_policy = parent.child_policy
        else:
            child_policy = policy

        # Apply the policy to the children and filter the result to suppress the invalid ones
        self.children = []
        for c in direct_children:
            tree = child_policy(c, search_parameters)
            if tree != None:
                if policy == None:
                    tree = parent.child_callback(tree)  # In case additional actions are needed to finish the work. 
                self.children.append(tree)

    def __str__(self):
        retour = "Tree :"
        retour += str(self.parent) + ", " + str([str(c) for c in self.children])
        return retour

