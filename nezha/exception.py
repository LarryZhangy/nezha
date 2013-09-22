import sys

from nezha.openstack.common.gettextutils import _
from nezha.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class NezhaException(Exception):
    """Base Nezha Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.
    
    """
    msg_fmt = _("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs

            except Exception:
                exc_info = sys.exc_info()
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception(_('Exception in string format operation'))
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))

                message = self.msg_fmt

        super(NezhaException, self).__init__(message)

    def format_message(self):
        if self.__class__.__name__.endswith('_Remote'):
            return self.args[0]
        else:
            return unicode(self)


class Invalid(NezhaException):
    msg_fmt = _("Unacceptable parameters.")
    code = 400

class InvalidInput(Invalid):
    msg_fmt = _("Invalid input received") + ": %(reason)s"

class NotFound(NezhaException):
    msg_fmt = _("Resource could not be found.")
    code = 404

class ConfigNotFound(NotFound):
    msg_fmt = _("Could not find config at %(path)s")

class PasteAppNotFound(NotFound):
    msg_fmt = _("Could not load paste app '%(name)s' from %(path)s")

class ServerNotFound(NotFound):
    msg_fmt = _("Server '%(id)s' not find.")

class ServerExists(NezhaException):
    code = 409
    msg_fmt = _("Server '%(ip)s' had exists.")

class Forbidden(NezhaException):
    code = 403
    msg_fmt = _("You are not authorized to complite this action.")

def _cleanse_dict(original):
    """Strip all admin_password, new_pass, rescue_pass keys from a dict."""
    return dict((k, v) for k, v in original.iteritems() if not "_pass" in k)
