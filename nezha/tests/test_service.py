"""
Unit Tests for remote procedure calls using queue
"""

import sys
import mock
import fixtures
import testtools

from oslo.config import cfg

from nezha import context
from nezha import db
from nezha import exception
from nezha import manager
from nezha import service
from nezha import test
from nezha import wsgi

test_service_opts = [
    cfg.StrOpt("test_service_listen",
               default='127.0.0.1',
               help="Host to bind test service to"),
    cfg.IntOpt("test_service_listen_port",
               default=0,
               help="Port number to bind test service to"),
    ]

CONF = cfg.CONF
CONF.register_opts(test_service_opts)


class TestWSGIService(test.TestCase):

    def setUp(self):
        super(TestWSGIService, self).setUp()
        self.useFixture(fixtures.MonkeyPatch('nezha.wsgi.Loader.load_app', mock.MagicMock))

    def test_service_random_port(self):
        test_service = service.WSGIService("test_service")
        test_service.start()
        self.assertNotEqual(0, test_service.port)
        test_service.stop()


class TestLauncher(test.TestCase):

    def setUp(self):
        super(TestLauncher, self).setUp()
        self.useFixture(fixtures.MonkeyPatch('nezha.wsgi.Loader.load_app', mock.MagicMock))
        self.service = service.WSGIService("test_service")

    def test_launch_app(self):
        service.serve(self.service)
        self.assertNotEquals(0, self.service.port)

