#!/usr/bin/env python
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
from distutils.core import setup
from distutils.command.build import build
from distutils.command.install import install
from distutils.cmd import Command
from docutils.core import publish_file
from docutils.writers import manpage

import os
import sys
import subprocess
#pylint: disable=W0201,R0904
class BuildDoc(Command):
    u'''Builds the documentation. Crazy, right ?'''
    description = "Build the documentation."
    user_options = [('build-dir=', 'b', 'directory for documentation')]

    def initialize_options(self):
        self.build_dir = None
        if os.name == 'nt':
            self.src_dir = sys.argv[0].split(os.path.sep)
        else:
            self.src_dir = (os.getcwd().split(os.path.sep) +
                            sys.argv[0].split(os.path.sep))
        self.src_dir.pop()

    def finalize_options(self):
        self.set_undefined_options('build', ('build_base', 'build_dir'))
        if isinstance(self.build_dir, str):
            self.build_dir = self.build_dir.split(os.path.sep)
        self.build_dir.append('doc')

    def run(self):
        try:
            os.makedirs(os.path.sep.join(self.build_dir))
        except OSError:
            pass
        # Make the man pages:
        # Analyze every file in man/ to know whether is is a source
        man_dir = '/'.join(self.src_dir + ['man'])
        man_src = [(n[0], int(n[1])) for n in [s.split('.')
                                               for s in os.listdir(man_dir)]
                   if (len(n) == 3 and int(n[1]) in range(1, 9) and
                       n[2] == 'rst')]

        # Create the directories
        mem = 0
        path = ''
        for i in man_src:
            if i[1] != mem:
                path = os.path.sep.join(self.build_dir +
                                        ['man/man{0}'.format(i[1])])
                try:
                    os.makedirs(path)
                except OSError:
                    pass
            mem = i[1]
            publish_file(source_path = '/'.join([man_dir,
                                                 '{0}.{1}.rst'.format(i[0],
                                                                      i[1])]),
                         destination_path = \
                            os.path.sep.join([path,
                                              '{0}.{1}'.format(i[0],i[1])]),
                         writer = manpage.Writer())

class InstallDoc(Command):
    u'''Install the documentation in the proper place, that is, if there's any.
    '''
    description = 'Install the documentation.'
    user_options = [('build-dir=', 'b', 'build directory for documentation'),
                    ('install-prefix=', 'i', 'installation prefix')]

    def initialize_options(self):
        self.build_dir = None
        self.install_prefix = None

    def finalize_options(self):
        self.set_undefined_options('build_doc', ('build_dir', 'build_dir'))
        self.set_undefined_options('install', ('install_data',
                                               'install_prefix'))
        if isinstance(self.build_dir, str):
            self.build_dir = self.build_dir.split(os.path.sep)
        if isinstance(self.install_prefix, str):
            self.install_prefix = self.install_prefix.split(os.path.sep)

    def run(self):
        self.run_command('build_doc')
        man_build_dir = os.path.sep.join(self.build_dir + ['man'])
        man_cat = set([int(s[3]) for s in os.listdir(man_build_dir)
                       if (len(s) == 4 and int(s[3]) in range(1, 9) and
                           s[0:3] == 'man')])
        for i in man_cat:
            if self.install_prefix[-1] != 'usr':
                man_install_dir = os.path.sep.join(self.install_prefix +
                                           ['man/man{0}'.format(i)])
            else:
                man_install_dir = os.path.sep.join(self.install_prefix +
                                           ['share/man/man{0}'.format(i)])
            man_origin_dir = os.path.sep.join([man_build_dir,
                                               'man{0}'.format(i)])
            self.copy_tree(man_origin_dir, man_install_dir)

class Test(Command):
    u'''Run the unit test suite.'''
    description = 'Run a bunch of tests'
    user_options = []

    def initialize_options(self):
        self.build_lib = None
        self.build_scripts = None
        if os.name == 'nt':
            self.source_dir = sys.argv[0].split(os.path.sep)
        else:
            self.source_dir = os.getcwd().split(os.path.sep) + \
                sys.argv[0].split(os.path.sep)
        self.source_dir.pop()
        if self.source_dir[-1] == '.':
            self.source_dir.pop()

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_lib', 'build_lib'),
                                   ('build_scripts', 'build_scripts')
                                  )
    def run(self):
        self.run_command('build')
        src = '/'.join(self.source_dir)
        if os.name == 'nt':
            paths_sep = ';'
            exec_name = 'py.test.exe'
        else:
            paths_sep = ':'
            exec_name = 'py.test'
        os.putenv('PYTHONPATH', paths_sep.join([self.build_lib, src]))
        subprocess.call([exec_name,
                         '--cov-report', 'term-missing',
                         '--cov-conf', src+'/coverage.rc',
                         '--cov', self.build_lib, src])

class Pylint(Command):
    u'''Run pylint on the sources for those of us that still use archaic
    dev tools like vim...'''
    description = 'Run PyLint on the sources.'
    user_options = []

    def initialize_options(self):
        self.source_dir = \
            os.getcwd().split(os.path.sep) + sys.argv[0].split(os.path.sep)
        self.source_dir.pop()
        if self.source_dir[-1] == '.':
            self.source_dir.pop()

    def finalize_options(self):
        pass

    def run(self):
        src = '/'.join(self.source_dir)
        sources = {
            src:                    ['yat'],
            src+os.path.sep+'cli':  ['yatcli']
                   }
        exec_name = 'pylint'
        paths_sep = ':'
        if os.name == 'nt':
            exec_name = 'pylint.bat'
            paths_sep = ';'
        os.putenv('PYTHONPATH', paths_sep.join(sources.keys()))
        working_dir = os.getcwd()
        for path, modules in sources.iteritems():
            print path
            os.chdir(path)
            for module in modules:
                subprocess.call([exec_name, module,
                                 '--ignore-docstrings=y', '--ignore-comments=y',
                                 '--include-ids=y', '--reports=n',
                                 '--disable=I0011', '--disable=R0801'])
        os.chdir(working_dir)

build.sub_commands.append(('build_doc', None))
install.sub_commands.append(('install_doc', None))

setup(name='yat',
      cmdclass={'build_doc':BuildDoc,
                'install_doc':InstallDoc,
                'test':Test,
                'pylint':Pylint
               },
      version='0.3',
      description='Todolist manager',
      author='yat Development Team',
      author_email='yat-devel@freelist.org',
      url='https://www.gitorious.org/yat/',
      license='WTFPL v2',
      packages=['yat', 'yatcli'],
      package_dir={'yat':'yat', 'yatcli':'cli/yatcli'},
      scripts=['cli/yat'],
      data_files=[('/etc/', ['etc/yat.yatrc'])]
     )
#pylint: enable=w0201,R0904
