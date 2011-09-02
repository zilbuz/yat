#-*- coding:utf-8 -*-

u"""
This file contains the exceptions used by yat programs.


           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
                   Version 2, December 2004 

 Copyright (C) 2011
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
class IncoherentObject(Exception):
    u'''Exception raised when trying to save an object in the DB whose
    internal data are somehow incoherent — i.e. a Note with task == None.'''
    pass

class WrongId(Exception):
    u"""Exception raised when trying to extract a single object using an
    invalid ID."""
    pass
    
class WrongName(Exception):
    u"""Exception raised when trying to extract a single object using an
    invalid name."""
    pass

class ExistingLock(Exception):
    u"""Exception raised when a lock is already set."""
    pass

class WrongConfigFile(Exception):
    u"""Exception raised when the path passed to yat.) doesn't point to a valid
    file."""
    pass

class IncoherentDBState(Exception):
    u"""Exception raised when something doesn't add up and we don't know why,
    so we blame the DB"""
    pass

class FileNotFound(Exception):
    u"""Exception raised when trying to access a file that doesn't exist"""
    pass

class UnknownDBVersion(Exception):
    u"""Exception raised when trying to interact with an unknown version of a
    yat database"""
