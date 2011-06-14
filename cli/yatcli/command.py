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

import re
import yatcli

class Command(object):
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

    def __init__(self):
        if not hasattr(self, 'options'):
            self.options = []
        u"""An option is defined this way:
    (short, long, attribute, default)
with:
    - short: a single letter or None
    - long: a single word or None. In the word can be used lower-case letters,
            hyphens and digits
    - attribute: a valid python name
    - constructor: a function building an object out of a string
While short, long and attribute ought to be of the str type, default can be
any python object. The values of self.attribute is initialized with False if
constructor is None, None otherwise, when creating the Command object."""

        if not hasattr(self, 'arguments'):
            self.arguments = ([None], {})
        u'''Of the form:
    ([names], {name: (regexp, next, process)}
with:
    - names: the key values used as entry point
    - name: a simple string
    - regexp: a string containing a valid regular expression, and an identifier 'value'
    - next: a list of names, all entries of the very same arguments dictionary
    - process: a function taking 2 arguments : the content of the 'value' match and the return value
      of the last argument' process function.
    u'''

        if not hasattr(self, 'breakdown'):
            self.breakdown = False

    def __call__(self, cmd, args):
        self.command = cmd
        self.execute(cmd, self.parse_arguments(self.parse_options(args)))

    def parse_arguments(self, args):
        for k, a in self.arguments[1].iteritems():
            self.arguments[1][k] = (re.compile(a[0]), a[1], a[2])

        if self.breakdown:
            args_cpy = []
            for a in args:
                args_cpy.extend(a.split(' '))
            args = args_cpy
        if callable(self.arguments[0]):
            to_examine = self.arguments[0](self.command)
        else:
            to_examine = self.arguments[0]
        to_pass = None
        for a in args:
            m = None
            for e in to_examine:
                if e == None:
                    continue
                p = self.arguments[1][e]
                m = p[0].match(a)
                if m == None:
                    continue
                try:
                    value = m.groupdict()['value']
                except KeyError:
                    value = a
                if callable(p[1]):
                    to_examine = p[1](value)
                else:
                    to_examine = p[1]
                to_pass = p[2](value, to_pass)
                break
            if m == None:
                raise Exception('Unknown argument {0}'.format(a.__repr__()))
            
        if None not in to_examine:
            raise Exception('Argument missing')

        return to_pass

    def parse_options(self, args):
        for o in self.options:
            if len(o) != 4:
                raise ValueError('The options must be of the form \
                                 (short, long, attribute, type)')
            if o[3] == None:
                setattr(self, o[2], False)
            else:

                setattr(self, o[2], None)

        stripped_args = args[:]

        # We cannot use a for loop because we need to be able to make a
        # jump to reach the next argument inside of the loop
        it = iter(args)

        # We load the options into dictionaries in order not to have to go
        # through the list at every element of args
        short_dict = {}
        long_dict = {}
        for o in self.options:
            if o[0] != None:
                short_dict[o[0]] = (o[2], o[3])
            if o[1] != None:
                long_dict[o[1]] = (o[2], o[3])

        re_long = re.compile('^--(?P<name>([a-z][-a-z0-9]+))(=(?P<value>.*))?$')
        re_short= re.compile('^-(?P<options>[a-zA-Z]+)$')

        try:
            while(True):
                a = it.next()
                res = re_long.match(a)
                if res != None:
                    option = long_dict[res.groupdict()['name']]
                    if option[1] == None:
                        setattr(self, option[0], True)
                    else:
                        value = res.groupdict()['value']
                        if value == None:
                            raise yatcli.MissingArgument
                        setattr(self, option[0], option[1]('value'))
                    stripped_args.remove(a)
                    continue

                res = re_short.match(a)
                if res != None:
                    # Same reason as above : we need flexibility and complex
                    # exception management
                    it_l = iter([l for l in re.split('([a-zA-Z])',
                                                   res.groupdict()['options'])
                               if len(l) == 1])
                    try:
                        l = it_l.next()
                        while(True):
                            option = short_dict[l]
                            if option[1] == None:
                                setattr(self, option[0], True)
                                l = it_l.next()
                                continue
                            # If it doesn't raise an exception,
                            # there is another short option : Error
                            try:
                                l = it_l.next()
                                raise yatcli.MissingArgument
                            except StopIteration:
                                value = it.next()
                                setattr(self, option[0], option[1](value))
                                stripped_args.remove(value)
                                break
                    except StopIteration:   # for the loop over the letters
                        pass
                    stripped_args.remove(a)
        except StopIteration:   # for the loop over the arguments
            pass
        return stripped_args

    def execute(self, cmd, args):
        u"""Method actually doing something
        Params:
            -cmd: alias used to invoke the command
            -args: the rest of the command line
        """
        raise NotImplementedError

    pass
