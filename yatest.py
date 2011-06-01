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

def load_sql(sql_files, db):
    u'''Executes the SQL code into the db file. Careful : there is no checking
    whatsoever. If the db file doesn't exist, it will be created, but the
    initialization has to be done inside the SQL code. If it exists, you'd
    better make sure the db file has the proper structure. The SQL statements
    will be executed in the order of the list.
    
    Note that db is a file name, and sql_files a list of file names'''

def load_yat(config_file, sql_files):
    u'''Loads a Yat object using the config file provided. If one or more SQL
    files come along, they will be executed into the db specified by the config
    file.

    Please note that both config_file and sql_file are file names (str objects).'''

