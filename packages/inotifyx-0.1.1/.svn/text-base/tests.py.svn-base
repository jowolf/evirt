import os, sys, unittest
from unittest import TestCase

import inotifyx


WORKING_DIR = os.getcwd()
PROJECT_DIR = os.path.dirname(__file__)


class TestInotifyx(TestCase):
    fd = None
    test_dir = os.path.join(PROJECT_DIR, 'test')

    def setUp(self):
        os.mkdir(self.test_dir)
        os.chdir(self.test_dir)
        self.fd = inotifyx.init()

    def tearDown(self):
        os.close(self.fd)
        os.chdir(WORKING_DIR)
        os.rmdir(self.test_dir)

    def _create_file(self, path, content = ''):
        f = open(path, 'w')
        try:
            f.write(content)
        finally:
            f.close()

    def test_file_create(self):
        inotifyx.add_watch(self.fd, self.test_dir, inotifyx.IN_CREATE)
        self._create_file('foo')
        try:
            events = inotifyx.get_events(self.fd)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].mask, inotifyx.IN_CREATE)
            self.assertEqual(events[0].name, 'foo')
        finally:
            os.unlink('foo')

    def test_file_remove(self):
        self._create_file('foo')
        try:
            inotifyx.add_watch(self.fd, self.test_dir, inotifyx.IN_DELETE)
        except:
            os.unlink('foo')
            raise
        os.unlink('foo')
        events = inotifyx.get_events(self.fd)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].mask, inotifyx.IN_DELETE)
        self.assertEqual(events[0].name, 'foo')


def main(argv = None):
    if argv is None:
        argv = [__name__, '--verbose']
    unittest.main(module = __name__, argv = argv)
