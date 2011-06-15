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
import yatcli
import yatcli.command as command
import yatest
import yat.exceptions
from yatest import assert_raise
class TestBoolOptions():
    def setup_method(self, method):
        self.cmd = command.Command()
        self.cmd.options = [('b', 'bool', 'test', None), ('w', 'witness', 'test_witness', None)]
        self.func = self.cmd.parse_options

    def test_init(self):
        result = self.func([])
        assert self.cmd.test_witness == False
        assert result == []
        assert self.cmd.test == False

    def test_short(self):
        result = self.func(['-b'])
        assert self.cmd.test_witness == False
        assert result == []
        assert self.cmd.test == True

    def test_long(self):
        result = self.func(['--bool'])
        assert self.cmd.test_witness == False
        assert result == []
        assert self.cmd.test == True

    def test_multiple_short(self):
        self.cmd.options.append(('s', 'second', 'test2', None))
        result = self.func(['-sb'])
        assert result == []
        assert self.cmd.test_witness == False
        assert self.cmd.test == True
        assert self.cmd.test2 == True

class TestValueOptions():
    def setup_method(self, method):
        self.cmd = command.Command()
        self.cmd.options = [('v', 'value', 'test', str), ('w', 'witness', 'test_witness', str)]
        self.func = self.cmd.parse_options

    def test_init(self):
        result = self.func([])
        assert result == []
        assert self.cmd.test_witness == None
        assert self.cmd.test == None

    def test_short(self):
        result = self.func(['-v', 'test_value'])
        assert self.cmd.test_witness == None
        assert result == []
        assert self.cmd.test == 'test_value'

    def test_short_multiple_failure(self):
        self.cmd.options.append(('s', 'second', 'test2', str))
        assert_raise(yatcli.BadArgument, self.func , ['-vs', 'test_value'])

    def test_short_missing_failure(self):
        assert_raise(yatcli.MissingArgument, self.func , ['-v'])

    def test_long(self):
        result = self.func(['--value=test_value'])
        assert self.cmd.test_witness == None
        assert result == []
        assert self.cmd.test == 'test_value'

    def test_long_missing(self):
        assert_raise(yatcli.MissingArgument, self.func , ['--value'])
        assert_raise(yatcli.MissingArgument, self.func , ['--value='])

    def test_ill_formed_option(self):
        self.cmd.options.append(('a', 'aaa', 'name'))
        assert_raise(ValueError, self.func, [])

class TestArguments(object):
    def setup_method(self, method):
        self.cmd = command.Command()
        self.func = self.cmd.parse_arguments
        self.cmd.arguments = (['first'], {'first':('^.*$', [None], 'first')})

    def test_extra_argument(self):
        assert_raise(yatcli.MissingArgument, self.func, [])
        self.cmd.arguments[0][:] = [None]
        assert_raise(yatcli.BadArgument, self.func, ['test'])

    def test_initial_arguments(self):
        self.cmd.command = 'foo'
        self.func(['test'])
        assert self.cmd.first == 'test'
        self.cmd.first = None
        self.cmd.arguments = (lambda x:['first'], self.cmd.arguments[1])
        self.func(['test'])
        assert self.cmd.first == 'test'

    def test_regexp(self):
        #"Catch'em all" regexp
        self.func(['test'])
        assert self.cmd.first == 'test'
        self.cmd.first = None

        # More specific regexp with value extraction
        self.cmd.arguments[1]['first'] = ('^/(?P<value>.*)$', [None], 'first')
        # Feed with bad value
        assert_raise(yatcli.BadArgument, self.func, ['test'])

        # Feed with legit value
        self.func(['/test'])
        assert self.cmd.first == 'test'

    def test_next_arguments(self):
        self.cmd.arguments[1]['second'] = ('^.*$', [None], 'second')
        self.cmd.arguments[1]['third'] = ('^.*$', [None], 'third')

        self.cmd.arguments[1]['first'][1][:] = ['second']
        self.func(['foo', 'bar'])
        assert self.cmd.second == 'bar'

        self.cmd.arguments[1]['first'] = ('^.*$', lambda x: ['third'], 'first')
        self.func(['foo', 'bar'])
        assert self.cmd.third == 'bar'

    def test_value_processing(self):
        self.func(['test'])
        assert self.cmd.first == 'test'

        li = []
        self.cmd.arguments[1]['first'] = ('^.*$', [None], li)
        self.func(['test'])
        assert li[0] == 'test'

        self.foo = None
        self.cmd.arguments[1]['first'] = ('^.*$', [None], lambda x: setattr(self, 'foo', 'bar'))
        self.func(['test'])
        assert self.foo == 'bar'

        self.cmd.arguments[1]['first'] = ('^.*$', [None], 0)
        assert_raise(TypeError, self.func, ['test'])

    def test_breakdown(self):
        li = []
        self.cmd.arguments[1]['first'] = ('^.*$', ['first', None], li)
        self.func(['foo bar'])
        assert len(li) == 1

        li[:] = []
        self.cmd.breakdown = True
        self.func(['foo bar'])
        assert len(li) == 2

class TestCommand(object):
    def test_whole_command(self):
        cmd = command.Command()
        assert_raise(NotImplementedError, cmd, '', [])
