#-*- coding:utf-8 -*-

u"""
yat.Library

This file contains the classes and functions needed for basic handling
of databases created with an old version of yat.

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

#-*- coding:utf-8 -*-

u"""
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

import yat.legacy as legacy
from yat.lib import Yat
from yatest import assert_raise, src, SQLTools as tools

class TestV0_1():
    @classmethod
    def setup_class(cls):
        cls.v0_1_path = src()+os.path.sep+'v0.1.db'
        cls.base_path = src()+os.path.sep+'base.db'
        tools.exec_sql([src()+os.path.sep+'v0.1.sql'], cls.v0_1_path)
        tools.exec_sql([src()+os.path.sep+'base.sql'], cls.base_path)
        cls.lib = Yat(config_file_path=src()+os.path.sep+'v0.1.yatrc',
                       db_path=cls.base_path)
        cls.leg = legacy.V0_1(cls.lib, cls.v0_1_path)

    @classmethod
    def teardown_class(cls):
        cls.leg.free_db()
        cls.lib.free_db()
        tools.restore_previous_db(cls.v0_1_path)
        tools.restore_previous_db(cls.base_path)

    def teardown_method(self, method):
        self.leg.free_db()
        tools.revert_db(self.v0_1_path)
        self.leg.load_db()

        self.lib.free_db()
        tools.revert_db(self.base_path)
        self.lib.load_db()

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

    def test_get_tasks(self):
        assert_raise(TypeError, self.leg.get_tasks, [], [], [], 'groups')
        tasks = self.leg.get_tasks()
        assert len(tasks) == 3
