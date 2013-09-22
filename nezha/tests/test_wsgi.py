"""Unit tests for `nezha.wsgi`."""

import os.path
import urllib2
import webob
import tempfile
import fixtures
import testtools

import eventlet

import nezha.wsgi
import nezha.exception
from nezha import test


class TestLoaderNothingExists(test.TestCase):
    """Loader tests where os.path.exists always returns False."""

    def setUp(self):
        super(TestLoaderNothingExists, self).setUp()
        self.useFixture(fixtures.MonkeyPatch('os.path.exists', lambda _: False))

    def test_config_not_found(self):
        self.assertRaises(
            nezha.exception.ConfigNotFound,
            nezha.wsgi.Loader,
        )


class TestLoaderNormalFilesystem(test.TestCase):
    """Loader tests with normal filesystem (unmodified os.path module)."""

    _paste_config = """
[app:test_app]
use = egg:Paste#static
document_root = /tmp
    """

    def setUp(self):
        super(TestLoaderNormalFilesystem, self).setUp()
        self.config = tempfile.NamedTemporaryFile(mode="w+t")
        self.config.write(self._paste_config.lstrip())
        self.config.seek(0)
        self.config.flush()
        self.loader = nezha.wsgi.Loader(self.config.name)

    def test_config_found(self):
        self.assertEquals(self.config.name, self.loader.config_path)

    def test_app_not_found(self):
        self.assertRaises(
            nezha.exception.PasteAppNotFound,
            self.loader.load_app,
            "nonexistent app",
        )

    def test_app_found(self):
        url_parser = self.loader.load_app("test_app")
        self.assertEquals("/tmp", url_parser.directory)

    def tearDown(self):
        self.config.close()
        super(TestLoaderNormalFilesystem, self).tearDown()

