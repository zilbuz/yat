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

import yat
import sqlite3
import os.path
import os
import shutil

class Tools(object):
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
        emplacement of the file with a relative path : relative to the calling
        module, to this module, or to the working directory... ?
        '''
        # We need to use a stack mechanism when facing several modification
        # because of the setup() and the actual test functions.
        if os.path.exists(db):
            try:
                previous_backup = cls.backup[db][-1]
                num = len(cls.backup[db])
            except IndexError:
                previous_backup = None
            if previous_backup == None:
                # create the first backup
                bak = db+'.bak0'
            else:
                # increment the numbering
                bak = previous_backup[:len(previous_backup)-1]+str(num)
            shutil.copy(db, bak)
        else:
            bak = None
        try:
            cls.backup[db].append(bak)
        except IndexError:
            cls.backup[db] = [bak]
        
        db = sqlite3.connect(db)
        for f in sql_files:
            db.executescript(open(f).read())

        db.close()

    @classmethod
    def restore_db(cls, db):
        u'''Restore the given db (filename, absolute path) to its original
        state, assuming it was once modified by exec_sql or indirectly by
        load_yat (but in that case it might be best to use restore_yat instead,
        even though it shouldn't change anything)
        '''
        try:
            bak = cls.backup[db].pop()
        except IndexError:
            return
        # If there is a backup but it is None, it means we created the file
        # once upon a time
        if bak == None:
            os.remove(db)
            return
        shutil.move(bak, db)

