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

import yat.models

import re
import new

def stack_up_parents(tree):
    u"""Static function. Given a tree with a task as root, stacks up
    the ancestors of the said task on top of is, in a straight line to
    the task. The added nodes are tagged as contextual."""
    parents = tree.parent.get_list_parents()
    def policy(task):
        u'''Custom chil policy.'''
        if task == tree.parent:
            return tree
        if task in parents:
            l_tree = Tree(task, policy)
            l_tree.context = True
            return l_tree
        return None
    tree_return = Tree(parents[0], policy)
    tree_return.context = True
    return tree_return

#pylint: disable=C0103,W0613
def Task_significant_value(self, tree, criterion):
    u'''Walk down the entire tree in order to find the most meaningful value.
    '''
    if tree.context:
        if criterion[1]:
            values = [float('-inf')]
        else:
            values = [float('inf')]
    else:
        try:
            values = [getattr(tree.parent, criterion[0])]
        except AttributeError:
            raise ValueError
    values.extend([t.significant_value(criterion) for t in tree.children])
    if criterion[1]:
        reduce_function = lambda x, y: x if x > y else y
    else:
        reduce_function = lambda x, y: x if x < y else y
    return reduce(reduce_function, values)

def Task_direct_children(self):
    u'''Returns the list of all the loaded children of the given task.'''
    return self.lib.get_children(self)

def Task_child_policy(self, task):
    u'''Meant to be used in a Tree construction. Defines whether a task
should be part or not'''
    return Tree(task, self.child_policy)

def Task_child_callback(self, tree):
    u'''Simple identity function.'''
    return tree

def Group_direct_children(self):
    u'''Select every member of the group that would be at the root of a tree
in this group's context.'''
    return [task for task in self.lib.get_loaded_tasks()
            if (task != None and self.directly_related_with(task) and
                not task.parents_in_group(self))]

def Group_child_callback(self, tree):
    u"""Appends the context tasks on top of the tree in the twisted cases :)"""
    if (self.directly_related_with(tree.parent) and
        (not tree.parent.parents_in_group(self)
         and tree.parent.parent != None)):
        return stack_up_parents(tree)
    return tree

def Group_significant_value(self, tree, criterion):
    u'''The significant value of a Tree with a Group at the root is always
    the one found on the root Group.'''
    try:
        return getattr(tree.parent, criterion[0])
    except AttributeError:
        raise ValueError

def List_directly_related_with(self, task):
    u'''Returns True is <task> is affiliated with the list (used in 
the algorithms of Group.'''
    return task.list == self

def List_child_policy(self, task):
    u"""This policy excludes all the tasks that aren't on the list, except
    for those who have a child on the list, and the immediate children of a
    member. The nodes with a task out of the list are tagged contextual."""
    if not task.list == self and not task.parents_in_group(self):
        return None
    tree = Tree(task, self.child_policy)
    if task.list == self:
        return tree
    if task.parent.list != self and tree.children == []:
        return None
    tree.context = True
    return tree

def Tag_child_policy(self, task):
    u"""The tags are considered inherited from the parent, so no discrimination
    whatsoever :)"""
    if self.directly_related_with(task) or task.parents_in_group(self):
        return Tree(task, self.child_policy)
    return None

def Tag_directly_related_with(self, task):
    u'''Returns True is <task> is tagged with <self> (used in 
the algorithms of Group.'''
    return self in task.tags

def NoGroup_significant_value(self, tree, criterion):
    u'''Always return the value at the last extremity.'''
    if criterion[1]:
        return float("-inf")
    return float('inf')

def NoTag_directly_related_with(self, task):
    u'''True when the task has no tag.'''
    return len(task.tags) == 0
#pylint: enable=C0103,W0613

class Tree(object):
    u'''Generic tree structure.'''
    def __init__(self, parent = None, policy = None):
        u'''The policy is a function passed along to the make_children_tree
        method in order to help select the children'''
        self.parent = parent

        # Defines a cache used in sorting operations
        self.values = {}

        # The context flag might be used in display
        self.context = False

        # The parent is the best placed to determine who are her children ;-)
        direct_children = parent.direct_children()

        # If the Power That Be (the caller) didn't specify a policy, once again
        # ask the parent, she supposedly knows what's best for her children,
        # right ?
        if policy == None:
            child_policy = parent.child_policy
        else:
            child_policy = policy

        # Apply the policy to the children and filter the result to suppress
        # the invalid ones
        self.children = []
        for child in direct_children:
            tree = child_policy(child)
            if tree != None:
                if policy == None:
                    # In case additional actions are needed to finish the work.
                    tree = parent.child_callback(tree)
                self.children.append(tree)

    def significant_value(self, criterion):
        u'''Determin the significant value of the tree according the criterion.
        WARNING: Since it can be quite heavy calculation, the values are only
        calculated once and then stored as a cache.'''
        try:
            return self.values[criterion]
        except KeyError:
            self.values[criterion] = \
                self.parent.significant_value(self, criterion)
            return self.values[criterion]

    @staticmethod
    def sort_trees(trees, criteria):
        u'''Sort a list of trees according to several criteria.
Note : if a criterion cannot be applied to the root nodes, the next one
will be used.

A criterion is supposed to be of the form ("attribute", reverse)
with reverse either True or False.'''
        for tree in trees:
            tree.sort_trees(tree.children, criteria)

        while criteria != []:
            try:
                trees.sort(key=lambda t: t.significant_value(criteria[0]),
                             reverse=criteria[0][1])
                break
            except ValueError:
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
                        sublist.sort(
                            key=(lambda t: 
                                 t.significant_value(criteria_copy[1])),
                            reverse=criteria_copy[1][1])
                        break
                    except ValueError:
                        criteria_copy = criteria_copy[1:]
                # And then lather, rince, repeat :)
                Tree.__subsort_trees(sublist, criteria[1:]) 
                # And after that, paste it back in
                trees[reference[1]:i] = sublist

                # Important, do not forget to update the reference
                reference = (trees[1].significant_value(criteria[0]), i)

        # Do the same for the last section of the list
        sublist = trees[reference[1]:]
        # Sort it a first time
        criteria_copy = criteria[:]
        while len(criteria_copy) > 1:
            try:
                sublist.sort(key=(lambda t:
                                  t.significant_value(criteria_copy[1])
                                 ), reverse=criteria_copy[1][1])
                break
            except ValueError:
                criteria_copy = criteria_copy[1:]
        Tree.__subsort_trees(sublist, criteria[1:])
        trees[reference[1]:] = sublist

#pylint: disable=W0604,C0103
global __all__
symbol_list = dir()
regexp = re.compile('^(?P<class>[A-Z][a-zA-Z]*)_(?P<function>[a-z_]+$)')
#pylint: enable=W0604,C0103
for s in symbol_list:
    res = regexp.match(s)
    if res != None:
        class_ = getattr(yat.models, res.groupdict()['class'])
        setattr(class_, res.groupdict()['function'],
                new.instancemethod(globals()[s], None, class_))

