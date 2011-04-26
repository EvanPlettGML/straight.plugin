#!/usr/bin/env python

import sys
import os
import unittest

from straight.plugin import loaders


class LoaderTestCaseMixin(object):

    paths = []

    def setUp(self):
        for path in self.paths:
            if isinstance(path, tuple):
                path = os.path.join(*path)
            sys.path.append(path)

        super(LoaderTestCaseMixin, self).setUp()

    def tearDown(self):
        for path in self.paths:
            del sys.path[-1]
        for modname in list(sys.modules):
            if modname.startswith('testplugin'):
                del sys.modules[modname]


class ModuleLoaderTestCase(LoaderTestCaseMixin, unittest.TestCase):

    paths = (
        os.path.join(os.path.dirname(__file__), 'test-packages', 'more-test-plugins'),
        os.path.join(os.path.dirname(__file__), 'test-packages', 'some-test-plugins'),
    )
    
    def setUp(self):
        self.loader = loaders.ModuleLoader()
        super(ModuleLoaderTestCase, self).setUp()
    
    def test_load(self):
        modules = list(self.loader.load('testplugin'))
        assert len(modules) == 2, modules

    def test_plugin(self):
        assert self.loader.load('testplugin')[0].do(1) == 2


class ModuleLoaderHooksTestCase(LoaderTestCaseMixin, unittest.TestCase):

    paths = (
        os.path.join(os.path.dirname(__file__), 'test-packages', 'module-hook-test-plugins'),
    )
    
    def setUp(self):
        self.loader = loaders.ModuleLoader()
        super(ModuleLoaderHooksTestCase, self).setUp()

    def test_hook_used(self):
        result = list(self.loader.load('testplugin'))
        self.assertEqual(result[0], "returned from hook")


class ObjectLoaderTestCase(LoaderTestCaseMixin, unittest.TestCase):

    paths = (
        os.path.join(os.path.dirname(__file__), 'test-packages', 'more-test-plugins'),
        os.path.join(os.path.dirname(__file__), 'test-packages', 'some-test-plugins'),
    )

    def setUp(self):
        self.loader = loaders.ObjectLoader()
        super(ObjectLoaderTestCase, self).setUp()

    def test_load_all(self):
        objects = list(self.loader.load('testplugin'))
        self.assertEqual(len(objects), 2, str(objects)[:100] + ' ...')


class ClassLoaderTestCase(LoaderTestCaseMixin, unittest.TestCase):

    paths = (
        os.path.join(os.path.dirname(__file__), 'test-packages', 'class-test-plugins'),
    )

    def setUp(self):
        self.loader = loaders.ClassLoader()
        super(ClassLoaderTestCase, self).setUp()

    def test_all_classes(self):
        classes = list(self.loader.load('testplugin'))

        self.assertEqual(len(classes), 3)

    def test_subclasses(self):
        from testplugin import testclasses
        classes = list(self.loader.load('testplugin', subclasses=testclasses.A))

        self.assertEqual(len(classes), 1)
        self.assertTrue(classes[0] is testclasses.A1)


if __name__ == '__main__':
    unittest.main()
