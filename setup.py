#!/usr/bin/env python

from distutils.core import setup

setup(name='yat',
      version='0.3',
      description='Todolist manager',
      author='Basile Desloges',
      author_email='basile.desloges@gmail.com',
      maintainer='Simon Chopin',
      maintainer_email='chopin.simon@googlemail.com',
      url='https://www.gitorious.org/yat/'
      license='WTFPL v2'
      packages=['yat', 'yatcli.]
      package_dir={'yat':'yat', 'yatcli.:'yatcli.yatcli.}
      scripts=['yatcli.yat']
      data_files=[('/etc/', ['etc/*']),
                  ('doc/', ['doc/*'])]
     )

