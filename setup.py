#!/usr/bin/env python

from distutils.core import setup
from distutils.command.build import build
from distutils.command.install import install
from distutils.cmd import Command
from docutils.core import publish_file
from docutils.writers import manpage

import os
import sys

class BuildDoc(Command):
    description = "Build the documentation."
    user_options = [('build-dir=', 'b', 'directory for documentation')]

    def initialize_options(self):
        self.build_dir = None
        self.src_dir = sys.argv[0].split(os.path.sep)
        self.src_dir.pop()

    def finalize_options(self):
        self.set_undefined_options('build', ('build_base', 'build_dir'))
        if isinstance(self.build_dir, str):
            self.build_dir = self.build_dir.split(os.path.sep)
        self.build_dir.append('doc')

    def run(self):
        try:
            os.makedirs('/'.join(self.build_dir))
        except OSError:
            pass
        # Make the man pages:
        # Analyze every file in man/ to know wether is is a source
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
                path = '/'.join(self.build_dir + ['man/man{0}'.format(i[1])])
                try:
                    os.makedirs(path)
                except OSError:
                    pass
            mem = i[1]
            publish_file(source_path='/'.join([man_dir,
                                               '{0}.{1}.rst'.format(i[0],
                                                                    i[1])
                                              ]),
                         destination_path='/'.join([path,
                                                    '{0}.{1}'.format(i[0],
                                                                     i[1])
                                                   ]),
                         writer=manpage.Writer())

class InstallDoc(Command):
    description = 'Install the documentation.'
    user_options = [('build-dir=', 'b', 'build directory for documentation'),
                    ('install-prefix=', 'i', 'installation prefix')]

    def initialize_options(self):
        self.build_dir = None
        self.install_prefix = None

    def finalize_options(self):
        self.set_undefined_options('build_doc', ('build_dir', 'build_dir'))
        self.set_undefined_options('install', ('install_data', 'install_prefix'))
        if isinstance(self.build_dir, str):
            self.build_dir = self.build_dir.split(os.path.sep)
        if isinstance(self.install_prefix, str):
            self.install_prefix = self.install_prefix.split(os.path.sep)

    def run(self):
        self.run_command('build_doc')
        man_build_dir = '/'.join(self.build_dir + ['man'])
        man_cat = set([int(s[3]) for s in os.listdir(man_build_dir)
                       if (len(s) == 4 and int(s[3]) in range(1, 9) and
                           s[0:3] == 'man')])
        for i in man_cat:
            if self.install_prefix[-1] != 'usr':
                man_install_dir = '/'.join(self.install_prefix +
                                           ['man/man{0}'.format(i)])
            else:
                man_install_dir = '/'.join(self.install_prefix +
                                           ['share/man/man{0}'.format(i)])
            man_origin_dir = '/'.join([man_build_dir, 'man{0}'.format(i)])
            self.copy_tree(man_origin_dir, man_install_dir)

build.sub_commands.append(('build_doc', None))
install.sub_commands.append(('install_doc', None))

setup(name='yat',
      cmdclass={'build_doc':BuildDoc, 'install_doc':InstallDoc},
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

