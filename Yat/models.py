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
    u'''This class describe a task in a OO perspective
    '''
    children_id = {} # id : (task, [c.id for c in children_of_task])
    class_lib = None    # The lib/db the tasks are gonna be pulled from

    @classmethod
    def get_task(cls, value = None, value_is_id = True):
        u'''The simplest interface possible to get a precise task. Note that it will
also load from the parent(s) from the DB if needed, as well as the lists and
tags coming alongside. 

If value_is_id is set to True, it will consider value as an ID, otherwise as an
exact name.

The return value is a Task.'''
        return cls.get_tasks([id])[0]

    @classmethod
    def get_tasks(cls, ids = None, names = None, regexp = None):
        u'''Get a series of tasks based on their ID, their content, and/or a regexp
matching their content. It will also pull the parents from the DB if needed, as
well as lists and tags.
The return value is a list of Task.'''
        tasks = []
        ids_to_fetch = []
        for i in ids:
            try:    # If the task is already loaded, take
                t = cls.children_id[i][0]
                if t == None:   # TODO: shift the unicity burden in
                                #       the library objects
                    raise Exception('internal')
                tasks.append(t)
            except:
                ids_to_fetch.append(int(i))
        tasks.extend(cls.class_lib._get_tasks(ids_to_fetch, names, regexp))
        return tasks

    # Every time an attribute is changed, the object memorizes it. This way,
    # the DB won't be updated at every call of self.save()
    def __setattr__(self, attr, value):
        super(Task, self).__setattr__('changed', True)
        super(Task, self).__setattr__(attr, value)

    def __init__(self, lib=None, sql_line=None, no_family=False):
        u"""Constructs a Task from an sql entry and an instance of Yat
        """
        self.lib = lib
        # Deal with what's there and fill the blanks for the lib.
        if Task.class_lib == None:
            Task.class_lib = self.lib
        elif self.lib == None:
            self.lib = Task.class_lib

        # Creation of a blank Task
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

        # Import from the SQL row
        self.id = int(sql_line["id"])
        try:
            parent_id = int(sql_line["parent"])
        except:
            parent_id = None

        # We have to handle all that stuff in a cleaner way.
        # For now, it is a bit too messy, even by my (Simon's) standards !
        # If the parent hasn't already an entry in the dict :
        if parent_id not in Task.children_id:
            Task.children_id[parent_id] = (None, [])
            # We assume it will be imported later on, which is kind of
            # dangerous and stupid, but hey, it has worked so far :)
        self.parent = Task.children_id[parent_id][0]

        # If the kid hasn't already been added to the list of the children
        # of the parent, add it. OTOH, who would have done that ?
        if self.id not in Task.children_id[parent_id][1]:
            Task.children_id[parent_id][1].append(self.id)

        # If the task hasn't already an entry (which would mean it has
        # children already created), create it
        if self.id not in Task.children_id:
            Task.children_id[self.id] = (self, [])
        else:
            # Else, update it, as well as its kids
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
        u'''Ensure that all the task's dependencies have been saved, and
then save itself into the lib.

Here, save can mean creation or update of an entry.'''
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
        u'''Returns the list of all the loaded children of the given task.'''
        try:    # Archaism. Should disappear once the new API is stabilized
            if search_parameters['no_family']:
                return []
        except:
            pass
        return [Task.children_id[i][0] for i in Task.children_id[self.id][1]]

    def child_policy(self, task, params):
        u'''Meant to be used in a Tree construction. Defines wether a task
should be part or not'''
        return Tree(task, self.child_policy, params)

    def child_callback(self, tree):
        return tree

class Group(object):
    class_lib = None
    def __setattr__(self, attr, value):
        super(Group, self).__setattr__('changed', True)
        super(Group, self).__setattr__(attr, value)

    def __init__(self, lib, sql_line):
        u"""Constructs a group from an sql row"""
        self.lib = lib
        if Group.class_lib == None:
            Group.class_lib = self.lib
        elif self.lib == None:
            self.lib = Group.class_lib
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

    @classmethod
    def get_groups(cls, loaded, fetch_function, ids=None, regexp=None):
        groups = []
        ids_to_fetch = None
        if ids != None:
            ids_to_fetch = []
            for i in ids:
                try:
                    groups.append(loaded[i])
                except:
                    ids_to_fetch.append(i)
        groups.extend(fetch_function(ids_to_fetch, regexp))
        return groups
    def direct_children(self, search_parameters):
        u'''Select every member of the group that would be at the root of a tree
in this group's context.'''
        try:    # As I said before, this thing is bound to disappear in a near future.
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
        u"""Check if the attributes of the group are valid."""
        if lib == None:
            lib = self.lib

        if self.priority == None:
            self.priority = lib.config["default_priority"]

        if self.created <= 0:
            self.created = self.lib.get_time()

    def save(self, lib = None):
        u'''Update or create the group into the lib/db'''
        if lib == None:
            lib = self.lib
        self.check_values(lib)
        if self.id == None:
            lib._add_group(self._table_name, self)
        elif self.changed:
            lib._edit_group(self._table_name, self)


class List(Group):
    u'''This class represent the "meta-data" of a list. It is NOT a container !'''
    list_id = {}
    _table_name = 'lists'

    @classmethod
    def get_list(cls, id):
        return cls.class_lib.get_list(id, True, False)

    @classmethod
    def get_lists(cls, ids=None, regexp=None):
        return cls.get_groups(cls.list_id, cls.class_lib.get_lists, ids, regexp)

    def __init__(self, lib, sql_line = None):
        u"""Constructs a List from an sql entry."""
        super(List, self).__init__(lib, sql_line)
        if self.id != None:
            List.list_id[self.id] = self

    def __str__(self):
        retour = "List " + str(self.id)
        return retour

    def related_with(self, task):
        u'''Returns True is <task> is affiliated with the list (used in 
the algorithms of Group.'''
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
    u'''This class represent the "meta-data" of a tag. It is NOT a container !'''
    tag_id = {}
    _table_name = 'tags'

    @classmethod
    def get_tag(cls, id):
        return cls.class_lib.get_tags(id, True, False)[0]

    @classmethod
    def get_tags(cls, ids=None, regexp=None):
        return cls.get_groups(cls.tag_id, cls.class_lib.get_tags_v2, ids, regexp)

    def __init__(self, lib, sql_line = None):
        u"""Constructs a Tag from an sql entry."""
        super(Tag, self).__init__(lib, sql_line)
        if self.id != None:
            Tag.tag_id[self.id] = self

    def child_policy(self, task, params):
        u"""The tags are considered inherited from the parent, so no discrimination whatsoever :)"""
        return Tree(task, self.child_policy, params)

    def related_with(self, task):
        u'''Returns True is <task> is tagged with <self> (used in 
the algorithms of Group.'''
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

