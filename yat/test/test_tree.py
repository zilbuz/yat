#-*- coding:utf-8 -*-

u"""
yat core module

This file contains the unit tests for the yat.tree module.

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

import os.path

from yatest import assert_raise, src, SQLTools as tools
from yat.lib import Yat
import yat.tree as tree

lib = None

def setup_module():
    global lib
    tools.exec_sql(src()+os.path.sep+'tree.sql',
                   src()+os.path.sep+'tree.db')
    lib = Yat(config_file_path=src()+os.path.sep+'tree.yatrc',
              db_path=src()+os.path.sep+'tree.db')

def teardown_module():
    global lib
    lib.free_db()
    tools.restore_previous_db(src()+os.path.sep+'tree.db')

def test_Task_significant_value():
    global lib
    t1 = lib.get_task(1)
    t3 = lib.get_task(3)
    tree1 = tree.Tree(t1)
    tree3 = tree.stack_up_parents(tree.Tree(t3))
    assert tree.Task_significant_value(t1, tree1, ('priority', True)) == 3
    assert tree.Task_significant_value(t1, tree1, ('priority', False)) == 1
    assert tree.Task_significant_value(t3, tree3, ('priority', True)) == 2
    assert tree.Task_significant_value(t3, tree3, ('priority', False)) == 2

    assert_raise(ValueError, tree.Task_significant_value,
                 t1, tree1, ('foo', True))

def test_Task_direct_children():
    global lib
    assert len(tree.Task_direct_children(lib.get_task(1))) == 2
    assert len(tree.Task_direct_children(lib.get_task(3))) == 0

def test_Task_child_policy():
    global lib
    assert tree.Task_child_policy(lib.get_task(2),
                                  lib.get_task(3)
                                  ).parent.id == 3

def test_Task_child_callback():
    global lib
    t1 = lib.get_task(1)
    tr = tree.Tree(lib.get_task(2))
    assert tree.Task_child_callback(t1, tr) == tr

def test_Group_direct_children():
    global lib
    l1 = lib.get_list(1)
    children = tree.Group_direct_children(l1)
    assert len(children) == 1
    assert children[0] == lib.get_task(4)

def test_Group_child_callback():
    global lib
    l1 = lib.get_list(1)
    tr1 = tree.Tree(lib.get_task(1))
    tr4 = tree.Tree(lib.get_task(4))
    assert tree.Group_child_callback(l1, tr1) == tr1
    assert tree.Group_child_callback(l1, tr4).parent.id == 1

def test_Group_significant_value():
    global lib
    l1 = lib.get_list(1)
    tr1 = tree.Tree(l1)
    assert tree.Group_significant_value(l1, tr1, ('priority', True)) == -5
    assert tree.Group_significant_value(l1, tr1, ('priority', False)) == -5
    assert_raise(ValueError,
                 tree.Group_significant_value, l1, tr1, ('foo', False))

def test_List_directly_related_with():
    global lib
    l1 = lib.get_list(1)
    assert tree.List_directly_related_with(l1, lib.get_task(4))
    assert not tree.List_directly_related_with(l1, lib.get_task(2))

def test_List_child_policy():
    global lib
    l2 = lib.get_list(2)
    tr7 = tree.List_child_policy(l2, lib.get_task(7))
    assert tr7 != None
    assert not tr7.context
    tr9 = tree.List_child_policy(l2, lib.get_task(9))
    assert tr9 != None
    assert tr9.context
    tr12 = tree.List_child_policy(l2, lib.get_task(9))
    assert tr12 != None
    assert tr12.context
    assert tree.List_child_policy(l2, lib.get_task(2)) == None
    assert tree.List_child_policy(l2, lib.get_task(1)) == None

def test_Tag_child_policy():
    global lib
    t1 = lib.get_tag(1)
    assert tree.Tag_child_policy(t1, lib.get_task(1)) == None
    assert tree.Tag_child_policy(t1, lib.get_task(6)) == None
    tr2 = tree.Tag_child_policy(t1, lib.get_task(2))
    assert tr2 != None
    assert not tr2.context
    tr3 = tree.Tag_child_policy(t1, lib.get_task(3))
    assert tr3 != None
    assert not tr3.context

def test_Tag_directly_related_with():
    global lib
    t1 = lib.get_tag(1)
    assert not tree.Tag_directly_related_with(t1, lib.get_task(1))
    assert tree.Tag_directly_related_with(t1, lib.get_task(2))
    assert not tree.Tag_directly_related_with(t1, lib.get_task(3))

def test_NoTag_directy_related_with():
    global lib
    nt = lib.get_tags([None])[0]
    assert tree.NoTag_directly_related_with(nt, lib.get_task(1))
    assert not tree.NoTag_directly_related_with(nt, lib.get_task(2))

def test_NoGroup_significant_value():
    global lib
    nt = lib.get_tags([None])[0]
    tr = tree.Tree(nt)
    assert tree.NoGroup_significant_value(nt, tr, ('foo', True)) == float('-inf')
    assert tree.NoGroup_significant_value(nt, tr, ('foo', False)) == float('inf')

def test_stackup_parents():
    global lib
    task = lib.get_task(3)
    tr = tree.Tree(task)
    stack = tree.stack_up_parents(tr)
    assert stack.parent.id == 1
    assert len(stack.children) == 1
    assert stack.children[0].parent.id == 2

class TestTree():
    def test_significant_value(self):
        global lib
        tr2 = tree.Tree(lib.get_task(2))
        assert tr2.significant_value(('priority', True)) == 3
        assert tr2.significant_value(('priority', True)) == 3
        assert tr2.significant_value(('priority', False)) == 2

    def test_sort_trees(self):
        global lib
        criteria = [('foo', True), ('priority', True),
                    ('content', False), ('bar',False)]
        sorted = tree.Tree(lib.get_task(1))
        tree.Tree.sort_trees([sorted], criteria)
        assert sorted.children[0].parent.id == 2
        assert sorted.children[1].parent.id == 4

        sorted = [tree.Tree(lib.get_task(13)), tree.Tree(lib.get_task(11))]
        tree.Tree.sort_trees(sorted, criteria)
        assert sorted[0].parent.id == 13