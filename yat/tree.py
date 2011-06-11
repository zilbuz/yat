#-*- coding:utf-8 -*-

u"""
The Tree class

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
import models
import re

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

def Task_significant_value(self, tree, criterion):
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

def Task_direct_children(self):
    u'''Returns the list of all the loaded children of the given task.'''
    return self.lib.get_children(self)

def Task_child_policy(self, task):
    u'''Meant to be used in a Tree construction. Defines wether a task
should be part or not'''
    return Tree(task, self.child_policy)

def Task_child_callback(self, tree):
    return tree

def Group_direct_children(self):
    u'''Select every member of the group that would be at the root of a tree
in this group's context.'''
    return [c for c in self.lib.get_loaded_tasks()
            if (c != None and self.related_with(c) and
                not c.parents_in_group(self))]

def Group_child_callback(self, tree):
    u"""Appends the context tasks on top of the tree in the twisted cases :)"""
    if self.related_with(tree.parent) and (not tree.parent.parents_in_group(self)
                                     and tree.parent.parent != None):
        return stack_up_parents(tree)
    return tree

def Group_significant_value(self, tree, criterion):
    return getattr(tree.parent, criterion[0])

def List_related_with(self, task):
    u'''Returns True is <task> is affiliated with the list (used in 
the algorithms of Group.'''
    return task.list == self

def List_child_policy(self, task):
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

def Tag_child_policy(self, task):
    u"""The tags are considered inherited from the parent, so no discrimination whatsoever :)"""
    return Tree(task, self.child_policy)

def Tag_related_with(self, task):
    u'''Returns True is <task> is tagged with <self> (used in 
the algorithms of Group.'''
    return self in task.tags

def NoGroup_significant_value(self, tree, criterion):
    if criterion[1]:
        return float("-inf")
    return float('inf')

def NoTag_related_with(self, task):
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

global __all__
symbol_list = dir()
regexp = re.compile('^(?P<class>[A-Z][a-zA-Z]*)_(?P<function>[a-z_]+$)')
for s in symbol_list:
    res = regexp.match(s)
    if res != None:
        setattr(getattr(models, res.groupdict()['class']),
                res.groupdict()['function'], globals()[s])
    