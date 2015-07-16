#!/usr/bin/env python

# Author: Forest Bond <forest@alittletooquiet.net>
# This file is in the public domain.


from distutils.core import (
  setup,
  Extension,
  Command,
)


################################################################################


class test(Command):
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from tests import main
        main()


################################################################################


setup(
  cmdclass = {'test': test},
  name = 'inotifyx',
  version = '0.1.1',
  description = 'Simple Linux inotify bindings',
  author = 'Forest Bond',
  author_email = 'forest@alittletooquiet.net',
  url = 'http://www.alittletooquiet.net/software/inotifyx/',
  py_modules = ['inotifyx'],
  ext_modules = [Extension('_inotifyx', sources = ['inotifyxmodule.c'])],
)
