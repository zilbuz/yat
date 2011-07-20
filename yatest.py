#-*- coding:utf-8 -*-

u"""
yatest.py

This file contains a number of functions used to facilitate setting up unit tests.

 Copyright (C) 2010, 2011
    Basile Desloges <basile.desloges@gmail.com>
    Simon Chopin <chopin.simon@gmail.com>

           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
                   Version 2, December 2004 

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

import sqlite3
import os.path
import shutil
import inspect

def assert_raise(cls, function, *args):
    u'''Check that the function called with args as arguments raises
    an exception of type cls.'''
    try:
        function(*args)
        assert not 'The function {0}{1} didn\'t raise {3}'.format(function, args, cls)
    except cls:
        pass

def src():
    u'''Returns the absolute path to the directory containing the file calling
    this function.'''
    return os.path.dirname(inspect.getframeinfo(inspect.currentframe().f_back).filename)

class SQLTools(object):
    backup = {}

    @classmethod
    def exec_sql(cls, sql_files, db):
        u'''Executes the SQL code into the db file. Careful : there is no checking
        whatsoever. If the db file doesn't exist, it will be created, but the
        initialization has to be done inside the SQL code. If it exists, you'd
        better make sure the db file has the proper structure. The SQL statements
        will be executed in the order of the list.
        
        sql_files is a list of file names, and db a file name.
        All paths must be absolute, since it can be tricky to determine the
        location of the file with a relative path : relative to the calling
        module, to this module, or to the working directory... ?
        '''
        # We need to use a stack mechanism when facing several modification
        # because of the setup() and the actual test functions.
        if db not in cls.backup.iterkeys():
            cls.backup[db] = []
            if os.path.exists(db):
                cls.backup[db].append(db+'.bak0')
                shutil.copy(db, cls.backup[db][-1])
            else:
                cls.backup[db].append(None)

        db_object = sqlite3.connect(db)
        if isinstance(sql_files, str):
            db_object.executescript(open(sql_files).read())
        else:
            for f in sql_files:
                db_object.executescript(open(f).read())
        db_object.close()
        cls.backup[db].append(db+'.bak'+str(len(cls.backup[db])))
        shutil.copy(db, cls.backup[db][-1])

    @classmethod
    def restore_previous_db(cls, db):
        u'''Restore the given db (filename, absolute path) to its original
        state, assuming it was once modified by exec_sql or indirectly by
        load_yat (but in that case it might be best to use restore_yat instead,
        even though it shouldn't change anything)
        '''
        try:
            current = cls.backup[db].pop()
            bak = cls.backup[db][-1]
        except IndexError:
            return
        except KeyError:
            raise ValueError
        # If there is a backup but it is None, it means we created the file
        # once upon a time
        if bak == None:
            os.remove(db)
            return
        shutil.copy(bak, db)
        
        if current != None:
            os.remove(current)

    @classmethod
    def revert_db(cls, db):
        u'''Use this when you have fiddled with the DB using other tools than
        the one provided by this class.'''

        try:
            cls.backup[db].append(None)
        except KeyError:
            raise ValueError
        cls.restore_previous_db(db)
        
    @staticmethod
    def has_table(db, table):
        u'''Open a DB and check whether it has the specified table.'''
        try:
            db = sqlite3.connect(db)
            db.execute('select * from {0}'.format(table))
            db.close()
        except sqlite3.OperationalError:
            return False
        return True
