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


class Command:
    u"""Abstract class for instrospection
    
If you wish to add a command, you have to create a class that derive from this
one, and the docstring must have this format (use {name} wherever you want the
program's name to appear):
Short description

usage: {name} cmd_name [options]

Long description
"""
    
    alias = []
    u"""Array containing the different aliases for this command"""

    def execute(self, cmd, args):
        u"""Method actually doing something
        Params:
            -cmd: alias used to invoke the command
            -args: the rest of the command line
        """
        raise NotImplementedError

    pass
