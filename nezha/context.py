from nezha.openstack.common import local
from nezha.openstack.common import uuidutils as uuid


class RequestContext(object):
    def __init__(self, request_id=None, user=None, tenant=None):
        if not request_id:
            request_id = uuid.generate_uuid()
        self.request_id = request_id

        if not hasattr(local.store, 'context'):
            self.update_store()

        if not user:
            self.user = 'admin'
        if not tenant:
            self.tenant = 'admin'

    def update_store(self):
        local.store.context = self

    def to_dict(self):
        return {
                'request_id': self.request_id, 
                'user': self.user,
                'tenant': self.tenant
                }
