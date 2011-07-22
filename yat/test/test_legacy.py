#-*- coding:utf-8 -*-

u"""
yat core module

This file contains the unit tests for the yat.legacy module.

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

import yat.legacy as legacy
from yat.lib import Yat
from yat.models import NoList, NoTag
from yat.exceptions import UnknownDBVersion, FileNotFound
from yatest import assert_raise, src, SQLTools as tools

def setup_module():
    TestV0_1.v0_1_path = src()+os.path.sep+'v0.1.db'
    TestV0_1.base_path = src()+os.path.sep+'base.db'
    tools.exec_sql([src()+os.path.sep+'v0.1.sql'], TestV0_1.v0_1_path)
    tools.exec_sql([src()+os.path.sep+'base.sql'], TestV0_1.base_path)
    TestV0_1.lib = Yat(config_file_path=src()+os.path.sep+'v0.1.yatrc',
                   db_path=TestV0_1.base_path)
    TestV0_1.leg = legacy.V0_1(TestV0_1.lib, TestV0_1.v0_1_path)

def teardown_module():
    TestV0_1.leg.free_db()
    TestV0_1.lib.free_db()
    tools.restore_previous_db(TestV0_1.v0_1_path)
    tools.restore_previous_db(TestV0_1.base_path)

class TestV0_1():
    @classmethod
    def reset(cls):
        cls.leg.free_db()
        tools.revert_db(cls.v0_1_path)
        cls.leg.load_db()
        cls.lib.free_db()
        tools.revert_db(cls.base_path)
        cls.lib.load_db()

    def test_init(self):
        assert self.lib.config == self.leg.config
        assert len(self.leg._loaded_lists) == 1
        assert len(self.leg._loaded_tags) == 1
        assert self.leg._loaded_tasks == {}

    def test_delete_tables(self):
        self.leg.delete_tables()
        assert not tools.has_table(self.v0_1_path, 'tasks')
        assert not tools.has_table(self.v0_1_path, 'tags')
        assert not tools.has_table(self.v0_1_path, 'lists')
        self.reset()

    def test_get_tasks(self):
        assert_raise(TypeError, self.leg.get_tasks, [], [], [], 'groups')
        tasks = self.leg.get_tasks()
        assert len(tasks) == 3

        t1 = self.leg.get_task(1)
        assert t1.parent == None
        assert t1.content == 'task1'
        assert t1.list.content == 'list1'
        assert iter(t1.tags).next().content == 'tag1'
        assert t1.due_date == float('inf')

        t2 = self.leg.get_task(2)
        assert t2.parent == None
        assert t2.content == 'task2'
        assert type(t2.list) == NoList
        assert len(t2.tags) == 0
        assert t2.due_date == 1297537200.0

        t3 = self.leg.get_task(3)
        assert t3.parent == None
        assert t3.content == 'task3'
        assert t3.list == t2.list
        assert len(t3.tags) == 2
        for tag in t1.tags:
            assert tag in t3.tags
        assert t3.due_date == float('inf')

    def test_get_lists(self):
        lists = self.leg.get_lists()
        assert len(lists) == 3
        assert NoList(self.leg) in lists

        assert type(self.leg.get_list(1)) == NoList

        l1 = self.leg.get_list(2)
        assert l1.content == 'list1'
        assert l1.priority == 0

        l2 = self.leg.get_list(3)
        assert l2.content == 'list2'
        assert l2.priority == -2

    def test_get_tags(self):
        tags = self.leg.get_tags()
        assert len(tags) == 3
        assert NoTag(self.leg) not in tags

        t1 = self.leg.get_tag(2)
        assert t1.content == 'tag1'
        assert t1.priority == 0

        t3 = self.leg.get_tag(4)
        assert t3.content == 'tag3'
        assert t3.priority == 4

    def test_misc(self):
        assert_raise(NotImplementedError, self.leg.not_implemented, "foo", 1)
        assert self.leg.get_notes() == []

def test_analyze_db():
    TestV0_1.reset()
    future_path = src()+os.path.sep+'future.db'
    tools.exec_sql([src()+os.path.sep+'future.sql'], future_path)


    assert_raise(UnknownDBVersion, legacy.analyze_db,
                 future_path, TestV0_1.lib)
    assert_raise(FileNotFound, legacy.analyze_db,
                 'bogus_path_to_nowhere', TestV0_1.lib)

    leg = legacy.analyze_db(TestV0_1.v0_1_path,
                            TestV0_1.lib)
    assert type(leg) == legacy.V0_1
    leg.free_db()

    leg = legacy.analyze_db(TestV0_1.base_path, TestV0_1.lib)
    assert type(leg) == Yat
    leg.free_db()

    tools.restore_previous_db(future_path)