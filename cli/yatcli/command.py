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

It must also contain a execute(self, cmd) function.

If you wish to parse options and arguments, you have to define an __init__()
function calling this class' __init__, and redefine if needed self.options,
self.arguments and self.breakdown. See the comments in the code.
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
    ([initial_arguments], {key: (regexp, next, process)})
with:
    - initial_arguments:
        the key values used as entry point. The properties and requirements
        are the same as for "next" below.

    - key:
        A hashable value...

    - regexp:
        a string containing a valid regular expression, which will be matched
        against the argument passed on the command line. If there's a match,
        the value used will be the whole argument, unless the "value"
        identifier is defined.

    - next:
        a list of keys, pointing to the potential next arguments. For instance,
        if you want to remove a list of yat, you type 'yat rm list id=$ID'. Here,
        the argument entry matching 'list' would return a list containing at
        least the key 'id'.

        next can be either a list or a function taking one argument (the
        value extracted from the regexp) and returning a list of keys.
        The keys have to be valid in the argument dictionary, or None. If the
        None key is present, it means that it is possible that this argument is
        the final argument.

    - process:
        process can be a list, a string or a function. If it is a list, the
        value extracted from the regexp will be appended to it. If it is a
        string, it represents the name of the 'self' attribute which will
        be affected by the extracted value.
        And last, if it is a callable, it has to take one argument: the 
        extracted value.
    u'''

        if not hasattr(self, 'breakdown'):
            self.breakdown = False
    u'''If self.breakdown is set to True, every argument will be divided into
    words, ignoring the quotation marks.'''

    def __call__(self, cmd, args):
        self.command = cmd
        self.parse_arguments(self.parse_options(args))
        self.execute(cmd)

    def parse_arguments(self, args):
        u'''Parse args using self.arguments. The arguments must have been
        stripped from all options. There is no return value, every modification
        takes place in self.'''
        # Regexp compilation
        for k, a in self.arguments[1].iteritems():
            self.arguments[1][k] = (re.compile(a[0]), a[1], a[2])

        # Breaking down the arguments into simple words
        if self.breakdown:
            args_cpy = []
            for a in args:
                args_cpy.extend(a.split(' '))
            args = args_cpy

        # Determine the first potential arguments
        if callable(self.arguments[0]):
            to_examine = self.arguments[0](self.command)
        else:
            to_examine = self.arguments[0]

        # Analyze the arguments
        for a in args:
            m = None

            # Match the argument against the potential entries
            for e in to_examine:
                # Indicates a possible end point. Irrelevant value.
                if e == None:
                    continue

                # Comparing the entry regexp against the argument
                p = self.arguments[1][e]
                m = p[0].match(a)
                if m == None:
                    continue

                # Extract the value
                try:
                    value = m.groupdict()['value']
                except KeyError:
                    value = a

                # Determine the next potential arguments
                if callable(p[1]):
                    to_examine = p[1](value)
                else:
                    to_examine = p[1]

                # Processing the value extracted from the regexp
                if callable(p[2]):
                    p[2](value)
                elif isinstance(p[2], str):
                    setattr(self, p[2], value)
                elif isinstance(p[2], list):
                    p[2].append(value)
                else:
                    raise TypeError("The last member of the argument tuple should \
                                    be a string, a list or a callable.")
                break

            # If there wasn't any match, the argument must be ill-formed
            if m == None:
                raise Exception('Unknown argument: {0}'.format(a))
            
        # A potential grammatical end of the command is signaled by the None key
        if None not in to_examine:
            raise yatcli.MIssingArgument('Argument missing !')

    def parse_options(self, args):
        u'''Parse the args provided using self.options. It modifies self and
        returns args stripped from every argument used.'''
        # Initialization of the attributes and shallow check of the option format
        for o in self.options:
            if len(o) != 4:
                raise ValueError('The options must be of the form \
                                 (short, long, attribute, type)')
            if o[3] == None:
                setattr(self, o[2], False)
            else:

                setattr(self, o[2], None)

        stripped_args = args[:]

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

        # We cannot use a for loop because we need to be able to make a
        # jump to reach the next argument inside of the loop
        it = iter(args)

        while(True):
            try:
                a = it.next()
            except StopIteration:
                break
            # Testing for a long option
            res = re_long.match(a)
            if res != None:
                option = long_dict[res.groupdict()['name']]
                
                # boolean option
                if option[1] == None:
                    setattr(self, option[0], True)
                else:
                    # The value is extracted directly from the regexp
                    value = res.groupdict()['value']
                    if value == None:
                        raise yatcli.MissingArgument
                    setattr(self, option[0], option[1]('value'))
                stripped_args.remove(a)
                continue

            # Checking if it is a cluster of short options
            res = re_short.match(a)
            if res != None:
                # Same reason as above : we need flexibility and complex
                # exception management
                it_l = iter([l for l in re.split('([a-zA-Z])',
                                               res.groupdict()['options'])
                           if len(l) == 1])

                #Bootstrapping the loop over the letters
                try:
                    l = it_l.next()
                except StopIteration:
                    stripped_args.remove(a)
                    continue
                while(True):
                    option = short_dict[l]

                    #Boolean option
                    if option[1] == None:
                        setattr(self, option[0], True)
                        try:
                            l = it_l.next()
                        except StopIteration:
                            break
                        continue

                    #Plain value option
                    try:
                        # If there is a next letter, there's a syntax error.
                        l = it_l.next()
                        raise yatcli.MissingArgument
                    except StopIteration:
                        value = it.next()
                        setattr(self, option[0], option[1](value))
                        stripped_args.remove(value)
                        break
                stripped_args.remove(a)
        return stripped_args

    def execute(self, cmd):
        u"""Method actually doing something
        Params:
            -cmd: alias used to invoke the command
            -args: the rest of the command line
        """
        raise NotImplementedError

    pass
