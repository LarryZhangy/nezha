from nezha import exception
from nezha import test


class NezhaExceptionTestCase(test.TestCase):
    def test_default_error_msg(self):
        class FakeNezhaException(exception.NezhaException):
            msg_fmt = "default message"

        exc = FakeNezhaException()
        self.assertEquals(unicode(exc), 'default message')

    def test_error_msg(self):
        self.assertEquals(unicode(exception.NezhaException('test')),
                          'test')

    def test_default_error_msg_with_kwargs(self):
        class FakeNezhaException(exception.NezhaException):
            msg_fmt = "default message: %(code)s"

        exc = FakeNezhaException(code=500)
        self.assertEquals(unicode(exc), 'default message: 500')
        self.assertEquals(exc.message, 'default message: 500')

    def test_error_msg_exception_with_kwargs(self):
        class FakeNezhaException(exception.NezhaException):
            msg_fmt = "default message: %(mispelled_code)s"

        exc = FakeNezhaException(code=500, mispelled_code='blah')
        self.assertEquals(unicode(exc), 'default message: blah')
        self.assertEquals(exc.message, 'default message: blah')

    def test_default_error_code(self):
        class FakeNezhaException(exception.NezhaException):
            code = 404

        exc = FakeNezhaException()
        self.assertEquals(exc.kwargs['code'], 404)

    def test_error_code_from_kwarg(self):
        class FakeNezhaException(exception.NezhaException):
            code = 500

        exc = FakeNezhaException(code=404)
        self.assertEquals(exc.kwargs['code'], 404)

    def test_cleanse_dict(self):
        kwargs = {'foo': 1, 'blah_pass': 2, 'zoo_password': 3, '_pass': 4}
        self.assertEquals(exception._cleanse_dict(kwargs), {'foo': 1})

        kwargs = {}
        self.assertEquals(exception._cleanse_dict(kwargs), {})

    def test_format_message_local(self):
        class FakeNezhaException(exception.NezhaException):
            msg_fmt = "some message"

        exc = FakeNezhaException()
        self.assertEquals(unicode(exc), exc.format_message())

    def test_format_message_remote(self):
        class FakeNezhaException_Remote(exception.NezhaException):
            msg_fmt = "some message"

            def __unicode__(self):
                return u"print the whole trace"

        exc = FakeNezhaException_Remote()
        self.assertEquals(unicode(exc), u"print the whole trace")
        self.assertEquals(exc.format_message(), "some message")
