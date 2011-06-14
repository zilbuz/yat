#-*- coding:utf-8 -*-

u"""
The Task, List and Tag classes

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

from exceptions import *

class Task(object):
    u'''This class describe a task in a OO perspective
    '''
    class_lib = None    # The lib/db the tasks are gonna be pulled from

    # Every time an attribute is changed, the object memorizes it. This way,
    # the DB won't be updated at every call of self.save()
    def __setattr__(self, attr, value):
        super(Task, self).__setattr__('changed', True)
        super(Task, self).__setattr__(attr, value)

    def __init__(self, lib=None):
        u"""Constructs a Task from an sql entry and an instance of Yat
        """
        self.lib = lib
        # Deal with what's there and fill the blanks for the lib.
        if Task.class_lib == None:
            Task.class_lib = self.lib
        elif self.lib == None:
            self.lib = Task.class_lib

        # Creation of a blank Task
        self.id = None
        self.parent=None
        self.content=''
        self.due_date=None
        self.priority=None
        self.list = NoList(self.lib)
        self.tags = set()
        self.completed = 0
        self.last_modified = 0
        self.created = 0
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

Here, save can mean creation or update of an entry.
If lib isn't the lib specified at the creation of the object, it will
automatically create a new task.
The return value is always None.'''
        if lib == None:
            lib = self.lib
        elif lib != self.lib:
            self.id = None

        rv = self.list.save(lib)
        if rv != None:  # The list has been replaced in the new lib
            self.list = rv

        to_remove = set()
        to_add = set()
        for t in self.tags:
            rv = t.save(lib)
            if rv != None:  # The tag has been replaced in the new lib
                to_add.add(rv)
                to_remove.add(t)
        self.tags -= to_remove
        self.tags |= to_add

        if self.parent != None:
            rv = self.parent.save(lib)
            if rv != None:  # It shouldn't happen, but better safe than sorry
                self.parent = rv

        if self.id == None:
            save_function = lib._add_task
        else:
            save_function = lib._edit_task
        save_function(self)
        self.lib = lib
        return None

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

    @staticmethod
    def stack_up_parents(tree):
        u"""Static function. Given a tree with a task as root, stacks up the ancestors of the said task
        on top of is, in a straight line to the task. The added nodes are tagged as contextual."""
        parents = tree.parent.get_list_parents()
        def policy(t):
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

    def direct_children(self):
        u'''Returns the list of all the loaded children of the given task.'''
        return self.lib.get_children(self)

    def child_policy(self, task):
        u'''Meant to be used in a Tree construction. Defines wether a task
should be part or not'''
        return Tree(task, self.child_policy)

    def child_callback(self, tree):
        return tree

    @staticmethod
    def significant_value(tree, criterion):
        if tree.context:
            if criterion[1]:
                values = [float('-inf')]
            else:
                values = [float('inf')]
        else:
            values = [getattr(tree.parent, criterion[0])]
        values.extend([t.significant_value(criterion) for t in tree.children])
        if criterion[1]:
            reduce_function = lambda x,y: x if x > y else y
        else:
            reduce_function = lambda x,y: x if x < y else y
        return reduce(reduce_function, values)

class Note(object):
    class_lib = None

    def __setattr__(self, attr, value):
        super(Note, self).__setattr__('changed', True)
        super(Note, self).__setattr__(attr, value)

    def __init__(self, lib):
        self.lib = lib
        if Note.class_lib == None:
            Note.class_lib = self.lib
        elif self.lib == None:
            self.lib = Note.class_lib
        self.id = None
        self.content = None
        self.task = None
        self.created = 0 
        self.hash = None
        self.changed = False

    def save(self, lib):
        u'''Update or create the note into the lib/db'''
        if lib == None:
            lib = self.lib
        self.check_values(lib)
        if lib != self.lib:
            try:
                return lib.get_note(self.task, self.content, False)
            except WrongName:
                self.id == None
            except WrongId:
                raise IncoherentObject('A note must be associated to an existing task.')
        if self.id == None:
            lib._add_note(self)
        elif self.changed:
            lib._edit_note(self)
        self.lib = lib
        return None

    def check_values(self, lib = None):
        u"""Check if the attributes of the note are valid."""
        if self.task == None:
            raise IncoherentObject('A note must be associated to a task.')
        if lib == None:
            lib = self.lib

        if self.created <= 0:
            self.created = self.lib.get_time()

class Group(object):
    class_lib = None
    def __setattr__(self, attr, value):
        super(Group, self).__setattr__('changed', True)
        super(Group, self).__setattr__(attr, value)

    def __init__(self, lib):
        u"""Constructs a group from an sql row"""
        self.lib = lib
        if Group.class_lib == None:
            Group.class_lib = self.lib
        elif self.lib == None:
            self.lib = Group.class_lib
        self.id = None
        self.content = ''
        self.priority = None
        self.last_modified = 0
        self.created = 0
        self.changed = False

    def direct_children(self):
        u'''Select every member of the group that would be at the root of a tree
in this group's context.'''
        return [c for c in self.lib.get_loaded_tasks()
                if (c != None and self.related_with(c) and
                    not c.parents_in_group(self))]

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

    def _save(self, lib, getter):
        u'''Update or create the group into the lib/db'''
        if lib == None:
            lib = self.lib
        self.check_values(lib)
        if lib != self.lib:
            try:
                return getter(self.content, False)
            except WrongName:
                self.id == None
        if self.id == None:
            lib._add_group(self._table_name, self)
        elif self.changed:
            lib._edit_group(self._table_name, self)
        self.lib = lib
        return None

    @staticmethod
    def significant_value(tree, criterion):
        return getattr(tree.parent, criterion[0])


class List(Group):
    u'''This class represent the "meta-data" of a list. It is NOT a container !'''
    _table_name = 'lists'

    def __init__(self, lib):
        u"""Constructs a List from an sql entry."""
        super(List, self).__init__(lib)

    def __str__(self):
        retour = "List " + str(self.id)
        return retour

    def related_with(self, task):
        u'''Returns True is <task> is affiliated with the list (used in 
the algorithms of Group.'''
        return task.list == self

    def child_policy(self, task):
        u"""This policy excludes all the tasks that aren't on the list, except for those who have a child
        on the list, and the immediate children of a member. The nodes with a task out of the list are 
        tagged contextual."""
        tree = Tree(task, self.child_policy)
        if task.list == self:
            return tree
        if task.parent.list != self and tree.children == []:
            return None
        tree.context = True
        return tree

    def save(self, lib=None):
        if lib == None:
            lib = self.lib
        return self._save(lib, lib.get_list)

class Tag(Group):
    u'''This class represent the "meta-data" of a tag. It is NOT a container !'''
    _table_name = 'tags'

    def __init__(self, lib, sql_line = None):
        u"""Constructs a Tag from an sql entry."""
        super(Tag, self).__init__(lib)

    def child_policy(self, task):
        u"""The tags are considered inherited from the parent, so no discrimination whatsoever :)"""
        return Tree(task, self.child_policy)

    def related_with(self, task):
        u'''Returns True is <task> is tagged with <self> (used in 
the algorithms of Group.'''
        return self in task.tags

    def save(self, lib=None):
        if lib == None:
            lib = self.lib
        return self._save(lib, lib.get_tag)

class NoGroup(object):
    def __init__(self, lib):
        self.id = None
        self.lib = lib

    def save(self, lib = None):
        pass

    def check_values(self, lib = None):
        pass

    @staticmethod
    def significant_value(tree, criterion):
        if criterion[1]:
            return float("-inf")
        return float('inf')

class NoList(NoGroup, List):
    # List provides unique algorithms, but here we override its polymorphism abilities
    __mro__ = (NoGroup, Group, object, List)
    __instance = None
    def __new__(cls, lib):
        if cls.__instance == None:
            cls.__instance = super(NoList, cls).__new__(cls)
        return cls.__instance

    def __init__(self, lib):
        super(NoList, self).__init__(lib)

class NoTag(NoGroup, Tag):
    # Same as for NoList's MRO.
    __mro__ = (NoGroup, Group, object, Tag)
    __instance = None

    def __new__(cls, lib):
        if cls.__instance == None:
            cls.__instance = super(NoTag, cls).__new__(cls)
        return cls.__instance

    def __init__(self, lib):
        super(NoTag, self).__init__(lib)

    def related_with(self, task):
        return task.tags == [] or task.tags == set()

class Tree(object):
    def __init__(self, parent = None, policy = None):  # The policy is a function passed along to the make_children_tree method in order to help select the children
        self.parent = parent

        # Defines a cache used in sorting operations
        self.values = {}

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

    def __str__(self):
        retour = "Tree :"
        retour += str(self.parent) + ", " + str([str(c) for c in self.children])
        return retour

    def significant_value(self, criterion):
        try:
            return self.values[criterion]
        except KeyError as e:
            self.values[criterion] = self.parent.significant_value(self, criterion)
            return self.values[criterion]

    @staticmethod
    def sort_trees(trees, criteria):
        u'''Sort a list of trees according to several criteria.
Note : if a criterion cannot be applied to the root nodes,
the next one will be used.

A criterion is supposed to be of the form ("attribute", reverse)
with reverse either True or False.'''
        for t in trees:
            t.sort_trees(t.children, criteria)

        while criteria != []:
            try:
                trees.sort(key=lambda t: t.significant_value(criteria[0]),
                             reverse=criteria[0][1])
                break
            except AttributeError as e:
                criteria = criteria[1:]
        Tree.__subsort_trees(trees, criteria)


    @staticmethod
    def __subsort_trees(trees, criteria):
        u'''Static method used to make more passes on the list of trees
to sort the remaining cluster according to alternative criteria.

The first <criteria> ought to be the one used in the first pass.
Careful, the <trees> list will be modified on site.
'''
        if len(trees) <= 1 or len(criteria) <= 1:
            # It wouldn't make any sense to sort an empty list
            # Or without criterion
            return

        # We need something to compare to.
        reference = (trees[0].significant_value(criteria[0]), 0)
        for i in range(len(trees)):
            if trees[i].significant_value(criteria[0]) != reference[0]:
                # Cut out the unsorted part
                sublist = trees[reference[1]:i]
                # Sort it a first time
                criteria_copy = criteria[:]
                while len(criteria_copy) > 1:
                    try:
                        sublist.sort(key=(lambda t:
                                          t.significant_value(criteria_copy[1])
                                         ), reverse=criteria_copy[1][1])
                        break
                    except AttributeError as e:
                        criteria_copy = criteria_copy[1:]
                # And then lather, rince, repeat :)
                Tree.__subsort_trees(sublist, criteria[1:]) 
                # And after that, paste it back in
                trees[reference[1]:i] = sublist

                # Important, do not forget to update the reference
                reference = (trees[1].significant_value(criteria[0]), i)

        # Do the same for the last section of the list
        sublist = trees[reference[1]:]
        sublist.sort(key=lambda t: t.significant_value(criteria[1]),
                     reverse=criteria[1][1])
        Tree.__subsort_trees(sublist, criteria[1:])
        trees[reference[1]:] = sublist
